#!/usr/bin/env python3
# /// script
# dependencies = ["google-cloud-bigquery[bqstorage]", "duckdb", "pyarrow", "google-cloud-secret-manager"]
# ///
"""
Historical Ethereum Data Backfill (2020-2025)

Loads 5 years of Ethereum blocks from BigQuery → MotherDuck

Usage:
    uv run historical_backfill.py [--start-year YEAR] [--end-year YEAR] [--dry-run]

Options:
    --start-year YEAR    Start year (default: 2020)
    --end-year YEAR      End year (default: 2025)
    --dry-run            Show query without executing

Secrets (Google Secret Manager):
    motherduck-token: MotherDuck authentication token (fetched via get_secret())

Environment Variables:
    GCP_PROJECT: GCP project ID (default: eonlabs-ethereum-bq)
"""

import os
import sys
from datetime import datetime, timezone
from google.cloud import bigquery
from google.cloud import secretmanager
import duckdb
import pyarrow as pa

# Configuration
GCP_PROJECT = os.environ.get('GCP_PROJECT', 'eonlabs-ethereum-bq')
BQ_DATASET = "bigquery-public-data.crypto_ethereum"
BQ_TABLE = "blocks"
MD_DATABASE = os.environ.get('MD_DATABASE', 'ethereum_mainnet')
MD_TABLE = os.environ.get('MD_TABLE', 'blocks')
START_YEAR = int(os.environ.get('START_YEAR', '2020'))
END_YEAR = int(os.environ.get('END_YEAR', '2025'))


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


def estimate_blocks(start_year, end_year):
    """Estimate number of blocks for time range."""
    # Ethereum averages ~300 blocks/hour, ~7,200/day, ~2,628,000/year
    years = end_year - start_year
    estimated = years * 2_628_000
    return estimated

def fetch_from_bigquery(start_year, end_year, dry_run=False):
    """Fetch blocks from BigQuery for date range."""
    print(f"\n[1/3] Fetching from BigQuery...")
    print(f"   Date range: {start_year}-01-01 to {end_year}-01-01")
    print(f"   Estimated blocks: ~{estimate_blocks(start_year, end_year):,}")

    # Query for blocks in date range
    query = f"""
    SELECT
        TIMESTAMP(timestamp) as timestamp,
        number,
        gas_limit,
        gas_used,
        base_fee_per_gas,
        transaction_count,
        difficulty,
        total_difficulty,
        size,
        blob_gas_used,
        excess_blob_gas
    FROM `{BQ_DATASET}.{BQ_TABLE}`
    WHERE timestamp >= TIMESTAMP('{start_year}-01-01 00:00:00')
      AND timestamp < TIMESTAMP('{end_year}-01-01 00:00:00')
    ORDER BY number ASC
    """

    if dry_run:
        print("\n📋 DRY RUN - Query to be executed:")
        print(query)
        return None

    # Execute query
    client = bigquery.Client(project=GCP_PROJECT)
    print(f"   Executing query...")

    start_time = datetime.now(timezone.utc)
    query_job = client.query(query)

    # Get results as PyArrow table (zero-copy)
    pa_table = query_job.to_arrow()

    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    print(f"   ✅ Fetched {len(pa_table):,} blocks in {elapsed:.1f}s")
    print(f"   Block range: {pa_table['number'][0]} - {pa_table['number'][-1]}")

    return pa_table

def load_to_motherduck(pa_table):
    """Load PyArrow table to MotherDuck."""
    print(f"\n[2/3] Loading to MotherDuck...")

    # Fetch token from Secret Manager
    print(f"   Fetching secret from Secret Manager...")
    token = get_secret('motherduck-token')

    os.environ['motherduck_token'] = token

    # Connect
    print(f"   Connecting to MotherDuck...")
    conn = duckdb.connect('md:')

    # Create database if needed
    conn.execute(f"CREATE DATABASE IF NOT EXISTS {MD_DATABASE}")
    conn.execute(f"USE {MD_DATABASE}")

    # Create table if needed
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

    # Insert data (INSERT OR REPLACE for idempotency)
    print(f"   Inserting {len(pa_table):,} blocks...")
    start_time = datetime.now(timezone.utc)

    # Register PyArrow table as temporary view
    conn.register('temp_blocks', pa_table)

    # Batch insert with INSERT OR REPLACE
    conn.execute(f"""
        INSERT OR REPLACE INTO {MD_TABLE}
        SELECT * FROM temp_blocks
    """)

    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    blocks_per_sec = len(pa_table) / elapsed if elapsed > 0 else 0

    print(f"   ✅ Inserted {len(pa_table):,} blocks in {elapsed:.1f}s ({blocks_per_sec:,.0f} blocks/sec)")

    # Verify
    result = conn.execute(f"SELECT COUNT(*) FROM {MD_TABLE}").fetchone()
    total_blocks = result[0]

    result = conn.execute(f"SELECT MIN(number), MAX(number) FROM {MD_TABLE}").fetchone()
    min_block, max_block = result

    print(f"   ✅ Total blocks in MotherDuck: {total_blocks:,}")
    print(f"   ✅ Block range: {min_block:,} - {max_block:,}")

    conn.close()

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Historical Ethereum backfill')
    parser.add_argument('--start-year', type=int, default=START_YEAR, help='Start year')
    parser.add_argument('--end-year', type=int, default=END_YEAR, help='End year')
    parser.add_argument('--dry-run', action='store_true', help='Show query without executing')
    args = parser.parse_args()

    print("=" * 80)
    print("Historical Ethereum Data Backfill")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}")
    print(f"BigQuery Dataset: {BQ_DATASET}.{BQ_TABLE}")
    print(f"MotherDuck: {MD_DATABASE}.{MD_TABLE}")
    print(f"GCP Project: {GCP_PROJECT}")
    print("=" * 80)

    try:
        # Fetch from BigQuery
        pa_table = fetch_from_bigquery(args.start_year, args.end_year, dry_run=args.dry_run)

        if args.dry_run:
            print("\n✅ DRY RUN COMPLETE")
            return 0

        if pa_table is None or len(pa_table) == 0:
            print("\n❌ No data fetched from BigQuery")
            return 1

        # Load to MotherDuck
        load_to_motherduck(pa_table)

        print("\n" + "=" * 80)
        print("✅ BACKFILL COMPLETE")
        print("=" * 80)
        print()

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
