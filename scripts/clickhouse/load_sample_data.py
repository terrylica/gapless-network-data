# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "clickhouse-connect>=0.7.0",
# ]
# ///
"""
Load sample data into local ClickHouse for development/testing.

Usage:
    uv run scripts/clickhouse/load_sample_data.py

This creates ~100 realistic Ethereum blocks for local development.
For production data, use sync_to_local.py instead.
"""

import sys
from datetime import datetime, timedelta, timezone


def load_sample_data() -> bool:
    """Load sample Ethereum blocks into local ClickHouse."""
    import clickhouse_connect

    host = "localhost"
    port = 8123

    print("Loading sample data into local ClickHouse...")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print()

    try:
        client = clickhouse_connect.get_client(
            host=host,
            port=port,
            connect_timeout=10,
        )

        # Verify table exists
        result = client.query("SELECT COUNT(*) FROM ethereum_mainnet.blocks")
        existing_count = result.result_rows[0][0]
        print(f"Existing rows: {existing_count}")

        # Generate realistic sample data
        # Based on actual Ethereum mainnet patterns post-EIP-1559
        print()
        print("Generating sample blocks...")

        # Start from a realistic recent block
        start_block = 19_000_000  # ~Feb 2024
        start_time = datetime(2024, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
        num_blocks = 100

        rows = []
        for i in range(num_blocks):
            block_num = start_block + i
            # ~12 second block time (post-Merge)
            timestamp = start_time + timedelta(seconds=i * 12)

            # Realistic values based on actual Ethereum data
            gas_limit = 30_000_000  # Standard post-London
            # Gas used varies 40-95% utilization
            utilization = 0.4 + (i % 10) * 0.055
            gas_used = int(gas_limit * utilization)

            # Base fee varies with utilization (EIP-1559 mechanics)
            # ~20-100 Gwei range
            base_fee_gwei = 20 + int(utilization * 80)
            base_fee_per_gas = base_fee_gwei * 10**9  # Convert to wei

            # Transaction count correlates with gas used
            transaction_count = 100 + int(utilization * 200)

            # Post-Merge: difficulty is always 0
            difficulty = 0
            total_difficulty = 58_750_003_716_598_352_816_469  # Frozen at Merge

            # Block size varies with transaction count
            size = 50_000 + transaction_count * 200

            # EIP-4844 blob fields (post-Dencun, block 19,426,587+)
            # For our sample range, these should be present
            if block_num >= 19_426_587:
                blob_gas_used = 131072 * (i % 3)  # 0, 1, or 2 blobs
                excess_blob_gas = 0
            else:
                blob_gas_used = None
                excess_blob_gas = None

            rows.append([
                timestamp,
                block_num,
                gas_limit,
                gas_used,
                base_fee_per_gas,
                transaction_count,
                difficulty,
                total_difficulty,
                size,
                blob_gas_used,
                excess_blob_gas,
            ])

        print(f"Generated {len(rows)} sample blocks")
        print(f"  Block range: {start_block} - {start_block + num_blocks - 1}")
        print(f"  Time range: {start_time.date()} to {(start_time + timedelta(seconds=num_blocks*12)).date()}")

        # Insert data
        print()
        print("Inserting into ethereum_mainnet.blocks...")

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

        client.insert(
            "ethereum_mainnet.blocks",
            rows,
            column_names=column_names,
        )

        print(f"✅ Inserted {len(rows)} blocks")

        # Verify
        result = client.query("SELECT COUNT(*) FROM ethereum_mainnet.blocks")
        total_count = result.result_rows[0][0]
        print(f"✅ Total rows in table: {total_count}")

        # Show sample
        print()
        print("Sample data (first 5 rows):")
        result = client.query("""
            SELECT number, timestamp, gas_used, base_fee_per_gas, transaction_count
            FROM ethereum_mainnet.blocks
            ORDER BY number
            LIMIT 5
        """)

        print(f"  {'Block':<12} {'Timestamp':<22} {'Gas Used':<12} {'Base Fee (Gwei)':<16} {'Tx Count'}")
        print("  " + "-" * 75)
        for row in result.result_rows:
            block_num, ts, gas, fee, txs = row
            fee_gwei = fee / 10**9
            print(f"  {block_num:<12} {str(ts):<22} {gas:<12,} {fee_gwei:<16.1f} {txs}")

        print()
        print("=" * 60)
        print("✅ SAMPLE DATA LOADED")
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
        print("❌ SAMPLE DATA LOAD FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Did you run setup first?")
        print("  uv run scripts/clickhouse/setup_local.py")
        return False


if __name__ == "__main__":
    success = load_sample_data()
    sys.exit(0 if success else 1)
