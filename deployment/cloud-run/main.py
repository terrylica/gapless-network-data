#!/usr/bin/env python3
# /// script
# dependencies = ["google-cloud-bigquery[bqstorage]", "duckdb", "pyarrow", "google-cloud-secret-manager", "requests", "clickhouse-connect"]
# ///
"""
BigQuery → MotherDuck + ClickHouse Ethereum Block Updater (Dual-Write)

Fetches latest Ethereum blocks from BigQuery public dataset and loads them into
both MotherDuck AND ClickHouse (dual-write for migration).
Designed to run as a Cloud Run Job on an hourly schedule.

Environment Variables:
    GCP_PROJECT: GCP project ID
    DATASET_ID: BigQuery dataset ID (default: crypto_ethereum)
    TABLE_ID: BigQuery table ID (default: blocks)
    MD_DATABASE: MotherDuck database name (default: ethereum_mainnet)
    MD_TABLE: MotherDuck table name (default: blocks)
    LOOKBACK_HOURS: Hours to look back for new blocks (default: 2)
    CLICKHOUSE_HOST: ClickHouse Cloud hostname (required for dual-write)
    CLICKHOUSE_PORT: ClickHouse port (default: 8443)
    CLICKHOUSE_USER: ClickHouse username (default: default)
    CLICKHOUSE_PASSWORD: ClickHouse password (required for dual-write)
    DUAL_WRITE_ENABLED: Enable writes to ClickHouse (default: true)
    MOTHERDUCK_WRITE_ENABLED: Enable writes to MotherDuck (default: true)
                              Set to 'false' during Phase 4 cutover to stop MotherDuck writes

Secrets (Google Secret Manager):
    motherduck-token: MotherDuck authentication token (fetched via get_secret())

Error Policy: Fail-fast. If ClickHouse write fails, raise exception immediately.
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from google.cloud import bigquery
from google.cloud import secretmanager
import duckdb
import requests

# Configuration
GCP_PROJECT = os.environ.get('GCP_PROJECT', 'eonlabs-ethereum-bq')
DATASET_ID = os.environ.get('DATASET_ID', 'crypto_ethereum')
TABLE_ID = os.environ.get('TABLE_ID', 'blocks')
MD_DATABASE = os.environ.get('MD_DATABASE', 'ethereum_mainnet')
MD_TABLE = os.environ.get('MD_TABLE', 'blocks')
LOOKBACK_HOURS = int(os.environ.get('LOOKBACK_HOURS', '2'))

# ClickHouse dual-write configuration
DUAL_WRITE_ENABLED = os.environ.get('DUAL_WRITE_ENABLED', 'true').lower() == 'true'
CLICKHOUSE_HOST = os.environ.get('CLICKHOUSE_HOST')
CLICKHOUSE_PORT = int(os.environ.get('CLICKHOUSE_PORT', '8443'))
CLICKHOUSE_USER = os.environ.get('CLICKHOUSE_USER', 'default')
CLICKHOUSE_PASSWORD = os.environ.get('CLICKHOUSE_PASSWORD')
CLICKHOUSE_DATABASE = 'ethereum_mainnet'
CLICKHOUSE_TABLE = 'blocks'

# Cutover control: Set to 'false' to disable MotherDuck writes (Phase 4)
MOTHERDUCK_WRITE_ENABLED = os.environ.get('MOTHERDUCK_WRITE_ENABLED', 'true').lower() == 'true'

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


def get_secret(secret_id: str, project_id: str = GCP_PROJECT) -> str:
    """Fetch secret from Google Secret Manager.

    Args:
        secret_id: Secret name (e.g., 'motherduck-token')
        project_id: GCP project ID

    Returns:
        Secret value as string
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8').strip()


def fetch_latest_blocks(lookback_hours: int = 2):
    """Fetch latest Ethereum blocks from BigQuery.

    Args:
        lookback_hours: Hours to look back from current time

    Returns:
        PyArrow table with block data
    """
    print(f"[1/4] Fetching blocks from last {lookback_hours} hours...")

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
    print(f"✅ Fetched {row_count} blocks ({len(COLUMNS)} columns)")

    if row_count == 0:
        print("⚠️  No new blocks found in time range")
        return None

    # Show block range
    block_numbers = pa_table.column('number').to_pylist()
    print(f"   Block range: {min(block_numbers)} - {max(block_numbers)}")

    return pa_table


def load_to_motherduck(pa_table):
    """Load PyArrow table to MotherDuck.

    Args:
        pa_table: PyArrow table with block data
    """
    print(f"\n[2/4] Connecting to MotherDuck...")

    # Fetch MotherDuck token from Secret Manager
    print(f"   Fetching secret from Secret Manager...")
    token = get_secret('motherduck-token')

    # Set motherduck_token for DuckDB connection
    os.environ['motherduck_token'] = token

    # Connect
    conn = duckdb.connect('md:', config={'connect_timeout': 30000})  # 30 seconds
    print(f"✅ Connected to MotherDuck")

    # Create database and use it
    print(f"\n[3/4] Preparing database '{MD_DATABASE}'...")
    conn.execute(f"CREATE DATABASE IF NOT EXISTS {MD_DATABASE}")
    conn.execute(f"USE {MD_DATABASE}")
    print(f"✅ Database ready")

    # Create or replace table with new data
    print(f"\n[4/4] Loading {len(pa_table)} blocks to '{MD_TABLE}'...")

    # Use INSERT OR REPLACE for upsert behavior (keyed by block number)
    # First ensure table exists with correct schema
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {MD_TABLE} (
            timestamp TIMESTAMP NOT NULL,
            number BIGINT PRIMARY KEY,
            gas_limit BIGINT,
            gas_used BIGINT,
            base_fee_per_gas BIGINT,
            transaction_count BIGINT,
            difficulty HUGEINT,
            total_difficulty HUGEINT,
            size BIGINT,
            blob_gas_used BIGINT,
            excess_blob_gas BIGINT
        )
    """)

    # Insert new data (will replace duplicates based on PRIMARY KEY)
    conn.execute(f"INSERT OR REPLACE INTO {MD_TABLE} SELECT * FROM pa_table")

    # Verify
    result = conn.execute(f"SELECT COUNT(*) FROM {MD_TABLE}").fetchone()
    total_rows = result[0]

    print(f"✅ Load complete")
    print(f"   Total blocks in MotherDuck: {total_rows:,}")

    conn.close()


def load_to_clickhouse(pa_table):
    """Load PyArrow table to ClickHouse Cloud (fail-fast on error).

    Args:
        pa_table: PyArrow table with block data

    Raises:
        ValueError: If ClickHouse credentials are missing
        Exception: If connection or insert fails (fail-fast policy)
    """
    import clickhouse_connect

    print(f"\n[DUAL-WRITE] Loading {len(pa_table)} blocks to ClickHouse...")

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
    print(f"✅ Connected to ClickHouse (server {client.server_version})")

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

    print(f"✅ ClickHouse load complete")
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
        status = "✅" if success else "❌"
        print(f"   {status} Healthchecks.io pinged")
    except Exception as e:
        # Don't fail the job if healthcheck ping fails
        print(f"   ⚠️  Failed to ping Healthchecks.io: {e}")


def main():
    """Main execution flow."""
    print("=" * 80)
    print("BigQuery → MotherDuck + ClickHouse Ethereum Block Updater (Dual-Write)")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}")
    print(f"GCP Project: {GCP_PROJECT}")
    print(f"BigQuery Dataset: {DATASET_ID}.{TABLE_ID}")
    print(f"MotherDuck: {MD_DATABASE}.{MD_TABLE} ({'ENABLED' if MOTHERDUCK_WRITE_ENABLED else 'DISABLED'})")
    print(f"ClickHouse: {CLICKHOUSE_DATABASE}.{CLICKHOUSE_TABLE} ({'ENABLED' if DUAL_WRITE_ENABLED else 'DISABLED'})")
    write_mode = 'Dual-Write' if DUAL_WRITE_ENABLED and MOTHERDUCK_WRITE_ENABLED else 'ClickHouse-Only' if DUAL_WRITE_ENABLED else 'MotherDuck-Only'
    print(f"Write Mode: {write_mode}")
    print("=" * 80)
    print()

    try:
        # Fetch latest blocks
        pa_table = fetch_latest_blocks(lookback_hours=LOOKBACK_HOURS)

        if pa_table is None:
            print("\n" + "=" * 80)
            print("✅ UPDATE COMPLETE (no new blocks)")
            print("=" * 80)

            # Ping Healthchecks.io on success (no new blocks is OK)
            ping_healthcheck(success=True)

            return 0

        # DUAL-WRITE: ClickHouse FIRST (fail-fast)
        if DUAL_WRITE_ENABLED:
            load_to_clickhouse(pa_table)

        # Then load to MotherDuck (if enabled)
        if MOTHERDUCK_WRITE_ENABLED:
            load_to_motherduck(pa_table)
        else:
            print("\n[CUTOVER] ⏭️  MotherDuck write SKIPPED (cutover mode)")

        print("\n" + "=" * 80)
        print("✅ UPDATE COMPLETE")
        print("=" * 80)
        print(f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}")

        # Ping Healthchecks.io on success
        ping_healthcheck(success=True)

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

        # Ping Healthchecks.io on failure
        ping_healthcheck(success=False)

        return 1


if __name__ == "__main__":
    sys.exit(main())
