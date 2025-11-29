#!/usr/bin/env python3
# /// script
# dependencies = ["google-cloud-bigquery[bqstorage]", "pyarrow", "google-cloud-secret-manager", "requests", "clickhouse-connect"]
# ///
"""
BigQuery → ClickHouse Ethereum Block Updater

Fetches latest Ethereum blocks from BigQuery public dataset and loads them into
ClickHouse Cloud. Designed to run as a Cloud Run Job on an hourly schedule.

Environment Variables:
    GCP_PROJECT: GCP project ID
    DATASET_ID: BigQuery dataset ID (default: crypto_ethereum)
    TABLE_ID: BigQuery table ID (default: blocks)
    LOOKBACK_HOURS: Hours to look back for new blocks (default: 2)
    CLICKHOUSE_HOST: ClickHouse Cloud hostname (required)
    CLICKHOUSE_PORT: ClickHouse port (default: 8443)
    CLICKHOUSE_USER: ClickHouse username (default: default)
    CLICKHOUSE_PASSWORD: ClickHouse password (required)

Error Policy: Fail-fast. If ClickHouse write fails, raise exception immediately.
"""

import os
import sys
from datetime import datetime, timedelta, timezone

import clickhouse_connect
import requests
from google.cloud import bigquery

# Configuration
GCP_PROJECT = os.environ.get('GCP_PROJECT', 'eonlabs-ethereum-bq')
DATASET_ID = os.environ.get('DATASET_ID', 'crypto_ethereum')
TABLE_ID = os.environ.get('TABLE_ID', 'blocks')
LOOKBACK_HOURS = int(os.environ.get('LOOKBACK_HOURS', '2'))

# ClickHouse configuration
CLICKHOUSE_HOST = os.environ.get('CLICKHOUSE_HOST')
CLICKHOUSE_PORT = int(os.environ.get('CLICKHOUSE_PORT', '8443'))
CLICKHOUSE_USER = os.environ.get('CLICKHOUSE_USER', 'default')
CLICKHOUSE_PASSWORD = os.environ.get('CLICKHOUSE_PASSWORD')
CLICKHOUSE_DATABASE = 'ethereum_mainnet'
CLICKHOUSE_TABLE = 'blocks'

# Monitoring
HEALTHCHECK_URL = 'https://hc-ping.com/616d5e4b-9e5b-470f-bd85-7870c2329ba3'

# ML-optimized columns (11 columns for feature engineering)
COLUMNS = [
    'timestamp',
    'number',
    'gas_limit',
    'gas_used',
    'base_fee_per_gas',
    'transaction_count',
    'difficulty',
    'total_difficulty',
    'size',
    'blob_gas_used',
    'excess_blob_gas'
]


def fetch_latest_blocks(lookback_hours: int = 2):
    """Fetch latest Ethereum blocks from BigQuery.

    Args:
        lookback_hours: Hours to look back from current time

    Returns:
        PyArrow table with block data
    """
    print(f"[1/3] Fetching blocks from last {lookback_hours} hours...")

    # Calculate time range
    end_time = datetime.now(timezone.utc).replace(tzinfo=None)
    start_time = end_time - timedelta(hours=lookback_hours)

    # Build query
    columns_str = ', '.join(COLUMNS)
    query = f"""
    SELECT {columns_str}
    FROM `bigquery-public-data.{DATASET_ID}.{TABLE_ID}`
    WHERE timestamp >= TIMESTAMP('{start_time.isoformat()}')
      AND timestamp < TIMESTAMP('{end_time.isoformat()}')
    ORDER BY number DESC
    """

    print(f"   Time range: {start_time.isoformat()} to {end_time.isoformat()}")

    # Execute query
    client = bigquery.Client(project=GCP_PROJECT)
    query_job = client.query(query)
    pa_table = query_job.to_arrow()

    row_count = len(pa_table)
    print(f"[1/3] Fetched {row_count} blocks ({len(COLUMNS)} columns)")

    if row_count == 0:
        print("   No new blocks found in time range")
        return None

    # Show block range
    block_numbers = pa_table.column('number').to_pylist()
    print(f"   Block range: {min(block_numbers)} - {max(block_numbers)}")

    return pa_table


def load_to_clickhouse(pa_table):
    """Load PyArrow table to ClickHouse Cloud (fail-fast on error).

    Args:
        pa_table: PyArrow table with block data

    Raises:
        ValueError: If ClickHouse credentials are missing
        Exception: If connection or insert fails (fail-fast policy)
    """
    print(f"\n[2/3] Loading {len(pa_table)} blocks to ClickHouse...")

    if not CLICKHOUSE_HOST or not CLICKHOUSE_PASSWORD:
        raise ValueError(
            "Missing CLICKHOUSE_HOST or CLICKHOUSE_PASSWORD. "
            "Set via environment variables or Doppler."
        )

    # Connect to ClickHouse
    print(f"   Connecting to {CLICKHOUSE_HOST}...")
    client = clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        secure=True,
        connect_timeout=30,
    )
    print(f"   Connected to ClickHouse (server {client.server_version})")

    # Convert PyArrow table to pandas, handling large integers
    df = pa_table.to_pandas()

    # Handle nullable columns and type conversions
    df['timestamp'] = df['timestamp'].dt.tz_localize(None)

    # Ensure numeric types for standard columns
    small_int_cols = ['number', 'gas_limit', 'gas_used', 'base_fee_per_gas',
                      'transaction_count', 'size']
    for col in small_int_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype('int64')

    # Handle very large integers (difficulty, total_difficulty) - convert to string
    # ClickHouse UInt256 accepts string representation of large numbers
    for col in ['difficulty', 'total_difficulty']:
        if col in df.columns:
            df[col] = df[col].fillna(0).apply(lambda x: str(int(x)) if x else '0')

    # Insert to ClickHouse
    column_names = [
        'timestamp', 'number', 'gas_limit', 'gas_used', 'base_fee_per_gas',
        'transaction_count', 'difficulty', 'total_difficulty', 'size',
        'blob_gas_used', 'excess_blob_gas'
    ]

    client.insert_df(
        f'{CLICKHOUSE_DATABASE}.{CLICKHOUSE_TABLE}',
        df,
        column_names=column_names,
    )

    # Verify
    result = client.query(f"SELECT COUNT(*) FROM {CLICKHOUSE_DATABASE}.{CLICKHOUSE_TABLE}")
    total_rows = result.result_rows[0][0]

    print(f"[2/3] ClickHouse load complete")
    print(f"   Total blocks in ClickHouse: {total_rows:,}")


def ping_healthcheck(success: bool = True):
    """Ping Healthchecks.io to signal job completion.

    Args:
        success: True for success ping, False for failure ping
    """
    try:
        url = HEALTHCHECK_URL if success else f"{HEALTHCHECK_URL}/fail"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        status = "success" if success else "failure"
        print(f"[3/3] Healthchecks.io pinged ({status})")
    except Exception as e:
        # Don't fail the job if healthcheck ping fails
        print(f"[3/3] Failed to ping Healthchecks.io: {e}")


def main():
    """Main execution flow."""
    print("=" * 80)
    print("BigQuery -> ClickHouse Ethereum Block Updater")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}")
    print(f"GCP Project: {GCP_PROJECT}")
    print(f"BigQuery Dataset: {DATASET_ID}.{TABLE_ID}")
    print(f"ClickHouse: {CLICKHOUSE_DATABASE}.{CLICKHOUSE_TABLE}")
    print("=" * 80)
    print()

    try:
        # Fetch latest blocks
        pa_table = fetch_latest_blocks(lookback_hours=LOOKBACK_HOURS)

        if pa_table is None:
            print("\n" + "=" * 80)
            print("UPDATE COMPLETE (no new blocks)")
            print("=" * 80)

            # Ping Healthchecks.io on success (no new blocks is OK)
            ping_healthcheck(success=True)

            return 0

        # Load to ClickHouse
        load_to_clickhouse(pa_table)

        print("\n" + "=" * 80)
        print("UPDATE COMPLETE")
        print("=" * 80)
        print(f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}")

        # Ping Healthchecks.io on success
        ping_healthcheck(success=True)

        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

        # Ping Healthchecks.io on failure
        ping_healthcheck(success=False)

        return 1


if __name__ == "__main__":
    sys.exit(main())
