# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "clickhouse-connect>=0.7.0",
# ]
# ///
"""
Sync production data from ClickHouse Cloud to local ClickHouse.

Usage:
    # Sync latest 10,000 blocks
    doppler run --project aws-credentials --config prd -- \
        uv run scripts/clickhouse/sync_to_local.py --limit 10000

    # Sync specific date range
    doppler run --project aws-credentials --config prd -- \
        uv run scripts/clickhouse/sync_to_local.py --start 2024-01-01 --end 2024-01-31

Requires:
    - Local ClickHouse running with ethereum_mainnet.blocks table
    - Doppler credentials for production ClickHouse Cloud
"""

import argparse
import os
import sys


def sync_to_local(limit: int | None, start: str | None, end: str | None) -> bool:
    """Sync data from production ClickHouse Cloud to local."""
    import clickhouse_connect

    # Production credentials (from Doppler)
    prod_host = os.environ.get("CLICKHOUSE_HOST")
    prod_password = os.environ.get("CLICKHOUSE_PASSWORD")

    if not prod_host or not prod_password:
        print("ERROR: Missing production credentials")
        print("Run with Doppler:")
        print("  doppler run --project aws-credentials --config prd -- \\")
        print("    uv run scripts/clickhouse/sync_to_local.py --limit 10000")
        return False

    # Local ClickHouse (no auth)
    local_host = "localhost"
    local_port = 8123

    print("Syncing from ClickHouse Cloud to local...")
    print(f"  Production: {prod_host}")
    print(f"  Local: {local_host}:{local_port}")
    print()

    try:
        # Connect to production
        print("Connecting to production...")
        prod_client = clickhouse_connect.get_client(
            host=prod_host,
            port=8443,
            username="default",
            password=prod_password,
            secure=True,
            connect_timeout=30,
        )
        print("✅ Production connected")

        # Connect to local
        print("Connecting to local...")
        local_client = clickhouse_connect.get_client(
            host=local_host,
            port=local_port,
            connect_timeout=10,
        )
        print("✅ Local connected")

        # Build query
        query = """
            SELECT
                timestamp, number, gas_limit, gas_used, base_fee_per_gas,
                transaction_count, difficulty, total_difficulty, size,
                blob_gas_used, excess_blob_gas
            FROM ethereum_mainnet.blocks
        """

        conditions = []
        if start:
            conditions.append(f"timestamp >= '{start}'")
        if end:
            conditions.append(f"timestamp <= '{end} 23:59:59'")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY number DESC"

        if limit:
            query += f" LIMIT {limit}"

        print()
        print(f"Query: {query[:100]}...")

        # Fetch from production
        print()
        print("Fetching from production...")
        result = prod_client.query(query)
        rows = result.result_rows

        if not rows:
            print("⚠️  No data found matching criteria")
            return True

        print(f"✅ Fetched {len(rows):,} rows")

        # Get block range
        block_numbers = [row[1] for row in rows]
        min_block = min(block_numbers)
        max_block = max(block_numbers)
        print(f"   Block range: {min_block:,} - {max_block:,}")

        # Insert into local
        print()
        print("Inserting into local...")

        column_names = [
            "timestamp",
            "number",
            "gas_limit",
            "gas_used",
            "base_fee_per_gas",
            "transaction_count",
            "difficulty",
            "total_difficulty",
            "size",
            "blob_gas_used",
            "excess_blob_gas",
        ]

        # Insert in batches of 10,000 for progress feedback
        batch_size = 10_000
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            local_client.insert(
                "ethereum_mainnet.blocks",
                batch,
                column_names=column_names,
            )
            print(f"   Inserted {min(i + batch_size, len(rows)):,}/{len(rows):,} rows")

        print(f"✅ All {len(rows):,} rows inserted")

        # Verify
        result = local_client.query("SELECT COUNT(*) FROM ethereum_mainnet.blocks")
        total_count = result.result_rows[0][0]
        print(f"✅ Total rows in local table: {total_count:,}")

        print()
        print("=" * 60)
        print("✅ SYNC COMPLETE")
        print("=" * 60)
        print()
        print("Test with SDK:")
        print("  export CLICKHOUSE_HOST_READONLY=localhost")
        print("  export CLICKHOUSE_USER_READONLY=default")
        print("  export CLICKHOUSE_PASSWORD_READONLY=''")
        print("  python -c 'import gapless_network_data as gmd; print(gmd.fetch_blocks(limit=5))'")

        return True

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ SYNC FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync production data to local ClickHouse"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10000,
        help="Number of blocks to sync (default: 10000)",
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End date (YYYY-MM-DD)",
    )

    args = parser.parse_args()

    success = sync_to_local(args.limit, args.start, args.end)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
