#!/usr/bin/env python3
# /// script
# dependencies = ["google-cloud-bigquery[bqstorage]", "duckdb", "pyarrow", "google-cloud-secret-manager"]
# ///
"""
BigQuery → MotherDuck Ethereum Block Updater

Fetches latest Ethereum blocks from BigQuery public dataset and loads them into MotherDuck.
Designed to run as a Cloud Run Job on an hourly schedule.

Environment Variables:
    GCP_PROJECT: GCP project ID
    DATASET_ID: BigQuery dataset ID (default: crypto_ethereum)
    TABLE_ID: BigQuery table ID (default: blocks)
    motherduck_token: MotherDuck authentication token (read/write)
    MD_DATABASE: MotherDuck database name (default: ethereum_mainnet)
    MD_TABLE: MotherDuck table name (default: blocks)
    LOOKBACK_HOURS: Hours to look back for new blocks (default: 2)
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from google.cloud import bigquery
from google.cloud import secretmanager
import duckdb

# Configuration
GCP_PROJECT = os.environ.get('GCP_PROJECT', 'eonlabs-ethereum-bq')
DATASET_ID = os.environ.get('DATASET_ID', 'crypto_ethereum')
TABLE_ID = os.environ.get('TABLE_ID', 'blocks')
MD_DATABASE = os.environ.get('MD_DATABASE', 'ethereum_mainnet')
MD_TABLE = os.environ.get('MD_TABLE', 'blocks')
LOOKBACK_HOURS = int(os.environ.get('LOOKBACK_HOURS', '2'))

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
    conn = duckdb.connect('md:')
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


def main():
    """Main execution flow."""
    print("=" * 80)
    print("BigQuery → MotherDuck Ethereum Block Updater")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}")
    print(f"GCP Project: {GCP_PROJECT}")
    print(f"BigQuery Dataset: {DATASET_ID}.{TABLE_ID}")
    print(f"MotherDuck: {MD_DATABASE}.{MD_TABLE}")
    print("=" * 80)
    print()

    try:
        # Fetch latest blocks
        pa_table = fetch_latest_blocks(lookback_hours=LOOKBACK_HOURS)

        if pa_table is None:
            print("\n" + "=" * 80)
            print("✅ UPDATE COMPLETE (no new blocks)")
            print("=" * 80)
            return 0

        # Load to MotherDuck
        load_to_motherduck(pa_table)

        print("\n" + "=" * 80)
        print("✅ UPDATE COMPLETE")
        print("=" * 80)
        print(f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}")

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
