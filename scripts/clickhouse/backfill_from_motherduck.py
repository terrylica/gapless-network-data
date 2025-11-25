# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "clickhouse-connect>=0.7.0",
#     "duckdb",
#     "google-cloud-secret-manager>=2.21.0",
# ]
# ///
"""
Backfill ClickHouse gap from MotherDuck.

The real-time VM collector has been writing to MotherDuck every ~12 seconds.
This script copies the missing blocks from MotherDuck to ClickHouse.

Usage:
    doppler run --project aws-credentials --config prd -- uv run scripts/clickhouse/backfill_from_motherduck.py
"""

import os
import sys
import time
import clickhouse_connect
import duckdb


def get_secret(secret_id: str, project_id: str = "eonlabs-ethereum-bq") -> str:
    """Fetch secret from Google Secret Manager."""
    from google.cloud import secretmanager
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8').strip()


def main():
    print("=" * 70)
    print("MotherDuck → ClickHouse Gap Backfill")
    print("=" * 70)
    print()

    # Connect to ClickHouse
    print("[1/5] Connecting to ClickHouse...")
    ch_client = clickhouse_connect.get_client(
        host=os.environ['CLICKHOUSE_HOST'],
        port=8443,
        username='default',
        password=os.environ['CLICKHOUSE_PASSWORD'],
        secure=True
    )
    print(f"  ✅ Connected to ClickHouse {ch_client.server_version}")

    # Connect to MotherDuck
    print("[2/5] Connecting to MotherDuck...")
    token = os.environ.get("motherduck_token")
    if not token:
        token = get_secret("motherduck-token")
    md_conn = duckdb.connect(f"md:ethereum_mainnet?motherduck_token={token}")
    print("  ✅ Connected to MotherDuck")

    # Find the gap
    print("[3/5] Analyzing gap...")

    # Get ClickHouse block numbers
    ch_result = ch_client.query('''
        SELECT MIN(number), MAX(number), COUNT(*)
        FROM ethereum_mainnet.blocks FINAL
    ''')
    ch_min, ch_max, ch_count = ch_result.result_rows[0]
    print(f"  ClickHouse: {ch_count:,} blocks (range {ch_min:,} - {ch_max:,})")

    # Get MotherDuck block numbers
    md_result = md_conn.execute('''
        SELECT MIN(number), MAX(number), COUNT(*)
        FROM blocks
    ''').fetchone()
    md_min, md_max, md_count = md_result
    print(f"  MotherDuck: {md_count:,} blocks (range {md_min:,} - {md_max:,})")

    gap_size = md_count - ch_count
    print(f"  Gap: {gap_size:,} blocks to backfill")

    if gap_size <= 0:
        print()
        print("✅ No gap to backfill - databases are in sync!")
        return 0

    # Find specific missing blocks using anti-join pattern
    print("[4/5] Fetching missing blocks from MotherDuck...")

    # Get list of block numbers in ClickHouse (for the gap range)
    # We'll query in batches to avoid memory issues
    batch_size = 50000
    total_inserted = 0

    # Find the actual gap range by checking where ClickHouse is missing blocks
    # Query MotherDuck for blocks NOT in ClickHouse
    # Since we can't do cross-database joins, we'll use block number ranges

    # Get ClickHouse gaps using window function
    gap_query = ch_client.query('''
        WITH numbered AS (
            SELECT
                number,
                number - lagInFrame(number) OVER (ORDER BY number) as gap
            FROM ethereum_mainnet.blocks FINAL
        )
        SELECT number - gap + 1 as gap_start, number - 1 as gap_end
        FROM numbered
        WHERE gap > 1
        ORDER BY number
    ''')

    gaps = [(row[0], row[1]) for row in gap_query.result_rows if row[1] >= row[0]]

    if not gaps:
        # Check if gap is at the end (MotherDuck has newer blocks)
        if md_max > ch_max:
            gaps = [(ch_max + 1, md_max)]
        else:
            print("  No gaps found in block sequence")
            return 0

    print(f"  Found {len(gaps)} gap range(s):")
    for gap_start, gap_end in gaps[:5]:  # Show first 5
        print(f"    Blocks {gap_start:,} - {gap_end:,} ({gap_end - gap_start + 1:,} missing)")
    if len(gaps) > 5:
        print(f"    ... and {len(gaps) - 5} more ranges")

    print()
    print("[5/5] Backfilling gaps...")

    for gap_start, gap_end in gaps:
        gap_count = gap_end - gap_start + 1
        if gap_count > 1000000:
            print(f"  Skipping large gap {gap_start:,} - {gap_end:,} (too large)")
            continue

        print(f"  Fetching blocks {gap_start:,} - {gap_end:,} ({gap_count:,} blocks)...")
        start_time = time.time()

        # Fetch from MotherDuck (matching ClickHouse schema)
        md_rows = md_conn.execute(f'''
            SELECT
                timestamp,
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
            FROM blocks
            WHERE number >= {gap_start} AND number <= {gap_end}
            ORDER BY number
        ''').fetchall()

        if not md_rows:
            print(f"    ⚠️  No rows found in MotherDuck for this range")
            continue

        # Convert to list for ClickHouse insertion
        data = []
        for row in md_rows:
            data.append([
                row[0],  # timestamp
                row[1],  # number
                row[2],  # gas_limit
                row[3],  # gas_used
                row[4] if row[4] else 0,  # base_fee_per_gas
                row[5],  # transaction_count
                int(row[6]) if row[6] else 0,  # difficulty
                int(row[7]) if row[7] else 0,  # total_difficulty
                row[8],  # size
                row[9],  # blob_gas_used
                row[10],  # excess_blob_gas
            ])

        # Insert to ClickHouse
        ch_client.insert(
            'ethereum_mainnet.blocks',
            data,
            column_names=[
                'timestamp', 'number', 'gas_limit', 'gas_used',
                'base_fee_per_gas', 'transaction_count', 'difficulty',
                'total_difficulty', 'size', 'blob_gas_used', 'excess_blob_gas'
            ]
        )

        elapsed = time.time() - start_time
        rate = len(data) / elapsed if elapsed > 0 else 0
        print(f"    ✅ Inserted {len(data):,} blocks in {elapsed:.1f}s ({rate:.0f} rows/sec)")
        total_inserted += len(data)

    print()
    print("=" * 70)
    print(f"✅ BACKFILL COMPLETE")
    print("=" * 70)
    print(f"Total blocks inserted: {total_inserted:,}")

    # Verify final counts
    ch_final = ch_client.query('SELECT COUNT(*) FROM ethereum_mainnet.blocks FINAL')
    md_final = md_conn.execute('SELECT COUNT(*) FROM blocks').fetchone()

    print(f"ClickHouse final: {ch_final.result_rows[0][0]:,} blocks")
    print(f"MotherDuck final: {md_final[0]:,} blocks")
    print(f"Remaining diff: {md_final[0] - ch_final.result_rows[0][0]:,}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
