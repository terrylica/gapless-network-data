# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "google-cloud-bigquery[bqstorage]",
#     "clickhouse-connect>=0.7.0",
#     "pyarrow",
#     "pandas",
# ]
# ///
"""
Historical Ethereum Data Migration: BigQuery → ClickHouse

Loads Ethereum blocks from BigQuery public dataset directly to ClickHouse.
Processes in yearly chunks to prevent OOM.

Usage:
    doppler run --project aws-credentials --config prd -- uv run scripts/clickhouse/migrate_from_bigquery.py

Options (environment variables):
    START_YEAR: Start year (default: 2015 - Ethereum genesis)
    END_YEAR: End year (default: 2026)
    BATCH_SIZE: Rows per insert batch (default: 100000)
    DRY_RUN: Set to "true" to show queries without executing

Progress logging every 30 seconds for long-running operations.
"""

import os
import sys
import time
from datetime import datetime

# Configuration
GCP_PROJECT = os.environ.get('GCP_PROJECT', 'eonlabs-ethereum-bq')
BQ_DATASET = "bigquery-public-data.crypto_ethereum"
BQ_TABLE = "blocks"
START_YEAR = int(os.environ.get('START_YEAR', '2015'))
END_YEAR = int(os.environ.get('END_YEAR', '2026'))
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', '100000'))
DRY_RUN = os.environ.get('DRY_RUN', 'false').lower() == 'true'


def get_clickhouse_client():
    """Create ClickHouse client from Doppler credentials."""
    import clickhouse_connect

    host = os.environ.get("CLICKHOUSE_HOST")
    port = int(os.environ.get("CLICKHOUSE_PORT", "8443"))
    user = os.environ.get("CLICKHOUSE_USER", "default")
    password = os.environ.get("CLICKHOUSE_PASSWORD")

    if not host or not password:
        raise ValueError("Missing CLICKHOUSE_HOST or CLICKHOUSE_PASSWORD")

    return clickhouse_connect.get_client(
        host=host,
        port=port,
        username=user,
        password=password,
        secure=True,
        connect_timeout=60,
    )


def fetch_year_from_bigquery(year: int) -> "pyarrow.Table":
    """Fetch one year of blocks from BigQuery."""
    from google.cloud import bigquery

    query = f"""
    SELECT
        TIMESTAMP(timestamp) as timestamp,
        number,
        gas_limit,
        gas_used,
        COALESCE(base_fee_per_gas, 0) as base_fee_per_gas,
        transaction_count,
        COALESCE(difficulty, 0) as difficulty,
        COALESCE(total_difficulty, 0) as total_difficulty,
        size,
        blob_gas_used,
        excess_blob_gas
    FROM `{BQ_DATASET}.{BQ_TABLE}`
    WHERE timestamp >= TIMESTAMP('{year}-01-01 00:00:00')
      AND timestamp < TIMESTAMP('{year + 1}-01-01 00:00:00')
    ORDER BY number ASC
    """

    client = bigquery.Client(project=GCP_PROJECT)
    print(f"  Executing BigQuery query for year {year}...")

    # Use BigQuery Storage API for faster reads
    job = client.query(query)
    arrow_table = job.to_arrow()

    return arrow_table


def insert_to_clickhouse(client, arrow_table: "pyarrow.Table", year: int) -> int:
    """Insert Arrow table to ClickHouse in batches."""
    import pyarrow as pa

    total_rows = arrow_table.num_rows
    if total_rows == 0:
        print(f"  No rows for year {year}")
        return 0

    print(f"  Inserting {total_rows:,} rows to ClickHouse...")

    # Convert Arrow table to pandas for clickhouse-connect
    df = arrow_table.to_pandas()

    # Handle nullable columns and type conversions
    # Convert timestamp to datetime64 with ms precision
    df['timestamp'] = df['timestamp'].dt.tz_localize(None)

    # Ensure numeric types - use object dtype for very large integers (difficulty)
    small_int_cols = ['number', 'gas_limit', 'gas_used', 'base_fee_per_gas',
                      'transaction_count', 'size']
    for col in small_int_cols:
        df[col] = df[col].fillna(0).astype('int64')

    # Handle very large integers (difficulty, total_difficulty) - convert to string
    # ClickHouse UInt256 accepts string representation of large numbers
    for col in ['difficulty', 'total_difficulty']:
        df[col] = df[col].fillna(0).apply(lambda x: str(int(x)) if x else '0')

    # Insert in batches
    inserted = 0
    start_time = time.time()
    last_log_time = start_time

    for i in range(0, total_rows, BATCH_SIZE):
        batch_df = df.iloc[i:i + BATCH_SIZE]

        client.insert_df(
            'ethereum_mainnet.blocks',
            batch_df,
            column_names=[
                'timestamp', 'number', 'gas_limit', 'gas_used', 'base_fee_per_gas',
                'transaction_count', 'difficulty', 'total_difficulty', 'size',
                'blob_gas_used', 'excess_blob_gas'
            ]
        )

        inserted += len(batch_df)

        # Progress logging every 30 seconds
        current_time = time.time()
        if current_time - last_log_time >= 30:
            elapsed = current_time - start_time
            rate = inserted / elapsed if elapsed > 0 else 0
            remaining = (total_rows - inserted) / rate if rate > 0 else 0
            print(f"    Progress: {inserted:,}/{total_rows:,} rows ({inserted/total_rows*100:.1f}%) "
                  f"- {rate:.0f} rows/sec - ETA: {remaining:.0f}s")
            last_log_time = current_time

    elapsed = time.time() - start_time
    rate = total_rows / elapsed if elapsed > 0 else 0
    print(f"  ✅ Inserted {total_rows:,} rows in {elapsed:.1f}s ({rate:.0f} rows/sec)")

    return total_rows


def verify_row_count(client, year: int, expected: int) -> bool:
    """Verify row count for year matches expected."""
    result = client.query(f"""
        SELECT COUNT(*) FROM ethereum_mainnet.blocks
        WHERE toYear(timestamp) = {year}
    """)
    actual = result.result_rows[0][0]

    if actual == expected:
        print(f"  ✅ Row count verified: {actual:,} rows")
        return True
    else:
        print(f"  ⚠️  Row count mismatch: expected {expected:,}, got {actual:,}")
        return False


def migrate():
    """Run full migration from BigQuery to ClickHouse."""
    print("=" * 60)
    print("BigQuery → ClickHouse Migration")
    print("=" * 60)
    print()
    print(f"Configuration:")
    print(f"  Source: {BQ_DATASET}.{BQ_TABLE}")
    print(f"  Target: ClickHouse ethereum_mainnet.blocks")
    print(f"  Years: {START_YEAR} - {END_YEAR - 1}")
    print(f"  Batch size: {BATCH_SIZE:,} rows")
    print(f"  Dry run: {DRY_RUN}")
    print()

    if DRY_RUN:
        print("DRY RUN - No data will be migrated")
        return True

    # Connect to ClickHouse
    print("Connecting to ClickHouse...")
    ch_client = get_clickhouse_client()
    version = ch_client.server_version
    print(f"✅ Connected to ClickHouse {version}")
    print()

    # Get current row count
    result = ch_client.query("SELECT COUNT(*) FROM ethereum_mainnet.blocks")
    existing_rows = result.result_rows[0][0]
    print(f"Existing rows in ClickHouse: {existing_rows:,}")
    print()

    # Migration stats
    total_migrated = 0
    start_time = time.time()
    failed_years = []

    # Process each year
    for year in range(START_YEAR, END_YEAR):
        print()
        print(f"[Year {year}] Starting migration...")

        try:
            # Fetch from BigQuery
            arrow_table = fetch_year_from_bigquery(year)
            rows_fetched = arrow_table.num_rows
            print(f"  Fetched {rows_fetched:,} rows from BigQuery")

            if rows_fetched == 0:
                print(f"  Skipping year {year} (no data)")
                continue

            # Insert to ClickHouse
            rows_inserted = insert_to_clickhouse(ch_client, arrow_table, year)
            total_migrated += rows_inserted

            # Verify
            verify_row_count(ch_client, year, rows_fetched)

        except Exception as e:
            print(f"  ❌ Error migrating year {year}: {e}")
            failed_years.append(year)
            # Continue with next year instead of failing completely
            continue

    # Final summary
    elapsed = time.time() - start_time
    print()
    print("=" * 60)
    print("Migration Complete")
    print("=" * 60)
    print()
    print(f"Total rows migrated: {total_migrated:,}")
    print(f"Total time: {elapsed/60:.1f} minutes ({elapsed:.0f} seconds)")
    print(f"Average rate: {total_migrated/elapsed:.0f} rows/sec")
    print()

    # Final verification
    result = ch_client.query("SELECT COUNT(*) FROM ethereum_mainnet.blocks FINAL")
    final_count = result.result_rows[0][0]
    print(f"Final row count (deduplicated): {final_count:,}")

    if failed_years:
        print()
        print(f"⚠️  Failed years: {failed_years}")
        print("   Re-run migration for failed years individually")
        return False

    print()
    print("✅ Migration successful!")
    return True


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
