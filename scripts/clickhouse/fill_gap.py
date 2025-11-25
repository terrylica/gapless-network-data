# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "clickhouse-connect>=0.7.0",
#     "google-cloud-bigquery>=3.20.0",
# ]
# ///
"""
Targeted gap fill: blocks 23,865,017 - 23,875,000

Fills the gap between BigQuery historical migration and dual-write start.
Uses block-number based filtering (not year-based).

Usage:
    doppler run --project aws-credentials --config prd -- uv run scripts/clickhouse/fill_gap.py
"""

import os
import sys
import clickhouse_connect
from google.cloud import bigquery


def main():
    # ClickHouse connection
    ch_client = clickhouse_connect.get_client(
        host=os.environ['CLICKHOUSE_HOST'],
        port=8443,
        username='default',
        password=os.environ['CLICKHOUSE_PASSWORD'],
        secure=True
    )

    # BigQuery client (use public dataset project)
    bq_client = bigquery.Client(project="eonlabs-ethereum-bq")

    # Gap range
    gap_start = 23865017
    gap_end = 23875000  # Slightly higher to catch any new blocks

    print(f"Fetching blocks {gap_start:,} - {gap_end:,} from BigQuery...")

    query = f"""
    SELECT
        number,
        `hash`,
        parent_hash,
        nonce,
        miner,
        difficulty,
        total_difficulty,
        size,
        gas_limit,
        gas_used,
        timestamp,
        transaction_count,
        base_fee_per_gas
    FROM `bigquery-public-data.crypto_ethereum.blocks`
    WHERE number >= {gap_start} AND number <= {gap_end}
    ORDER BY number
    """

    result = bq_client.query(query).result()
    rows = list(result)
    print(f"Fetched {len(rows):,} rows from BigQuery")

    if len(rows) == 0:
        print("No rows to insert - BigQuery may not have these blocks yet")
        return 1

    # Convert to list for insertion
    data = []
    for row in rows:
        data.append([
            row.number,
            row.hash,
            row.parent_hash,
            row.nonce or '',
            row.miner,
            int(row.difficulty) if row.difficulty else 0,
            int(row.total_difficulty) if row.total_difficulty else 0,
            row.size,
            row.gas_limit,
            row.gas_used,
            row.timestamp,
            row.transaction_count,
            int(row.base_fee_per_gas) if row.base_fee_per_gas else 0
        ])

    print(f"Inserting {len(data):,} rows to ClickHouse...")

    ch_client.insert(
        'ethereum_mainnet.blocks',
        data,
        column_names=[
            'number', 'hash', 'parent_hash', 'nonce', 'miner',
            'difficulty', 'total_difficulty', 'size', 'gas_limit',
            'gas_used', 'timestamp', 'transaction_count', 'base_fee_per_gas'
        ]
    )

    print(f"✅ Inserted {len(data):,} blocks to ClickHouse")

    # Verify
    result = ch_client.query(f'''
        SELECT COUNT(*)
        FROM ethereum_mainnet.blocks FINAL
        WHERE number >= {gap_start} AND number <= {gap_end}
    ''')
    count = result.result_rows[0][0]
    print(f"✅ Verified: {count:,} blocks in range {gap_start:,} - {gap_end:,}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
