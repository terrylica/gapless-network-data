# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "clickhouse-connect>=0.7.0",
# ]
# ///
"""
Create ClickHouse schema for Ethereum blocks migration.

Usage:
    doppler run --project aws-credentials --config prd -- uv run scripts/clickhouse/create_schema.py

Schema mirrors MotherDuck ethereum_mainnet.blocks table with ClickHouse-specific optimizations:
- ReplacingMergeTree engine for automatic deduplication (dual-pipeline support)
- ORDER BY number for deduplication key and efficient block-range queries
- Monthly partitioning for efficient data management
"""

import os
import sys
from datetime import datetime


def create_schema() -> bool:
    """Create ClickHouse database and table schema."""
    import clickhouse_connect

    host = os.environ.get("CLICKHOUSE_HOST")
    port = int(os.environ.get("CLICKHOUSE_PORT", "8443"))
    user = os.environ.get("CLICKHOUSE_USER", "default")
    password = os.environ.get("CLICKHOUSE_PASSWORD")

    if not host or not password:
        print("ERROR: Missing CLICKHOUSE_HOST or CLICKHOUSE_PASSWORD")
        return False

    print(f"Connecting to ClickHouse Cloud...")
    print(f"  Host: {host}")
    print()

    try:
        client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=user,
            password=password,
            secure=True,
            connect_timeout=30,
        )

        # Step 1: Create database
        print("Creating database 'ethereum_mainnet'...")
        client.command("CREATE DATABASE IF NOT EXISTS ethereum_mainnet")
        print("✅ Database created")

        # Step 2: Create table with ReplacingMergeTree
        # ReplacingMergeTree automatically deduplicates rows with same ORDER BY key
        # during background merges. For immediate deduplication, use FINAL modifier in queries.
        print()
        print("Creating table 'ethereum_mainnet.blocks'...")

        ddl = """
        CREATE TABLE IF NOT EXISTS ethereum_mainnet.blocks (
            -- Temporal
            timestamp DateTime64(3) NOT NULL,

            -- Block identification (deduplication key)
            number Int64,

            -- Gas metrics
            gas_limit Int64,
            gas_used Int64,
            base_fee_per_gas Int64,

            -- Transaction count
            transaction_count Int64,

            -- Mining difficulty (use UInt256 for Ethereum's large values)
            difficulty UInt256,
            total_difficulty UInt256,

            -- Block size in bytes
            size Int64,

            -- EIP-4844 blob fields (nullable for pre-Dencun blocks)
            blob_gas_used Nullable(Int64),
            excess_blob_gas Nullable(Int64)
        )
        ENGINE = ReplacingMergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY number
        SETTINGS index_granularity = 8192
        COMMENT 'Ethereum mainnet blocks - migrated from MotherDuck 2025-11-24'
        """

        client.command(ddl)
        print("✅ Table created with ReplacingMergeTree engine")
        print()
        print("Schema details:")
        print("  - Engine: ReplacingMergeTree (automatic deduplication)")
        print("  - ORDER BY: number (block number as deduplication key)")
        print("  - PARTITION BY: toYYYYMM(timestamp) (monthly partitions)")
        print("  - Columns: 12 (timestamp, number, gas_*, transaction_count, difficulty, size, blob_*)")

        # Step 3: Verify table exists
        print()
        print("Verifying table structure...")
        result = client.query("DESCRIBE TABLE ethereum_mainnet.blocks")
        print()
        print("Table columns:")
        for row in result.result_rows:
            col_name = row[0]
            col_type = row[1]
            print(f"  {col_name}: {col_type}")

        # Step 4: Test insert
        print()
        print("Testing insert...")
        client.command("""
            INSERT INTO ethereum_mainnet.blocks (
                timestamp, number, gas_limit, gas_used, base_fee_per_gas,
                transaction_count, difficulty, total_difficulty, size,
                blob_gas_used, excess_blob_gas
            ) VALUES (
                now64(3), 0, 0, 0, 0, 0, 0, 0, 0, NULL, NULL
            )
        """)
        print("✅ Test insert succeeded")

        # Verify insert
        result = client.query("SELECT COUNT(*) FROM ethereum_mainnet.blocks")
        count = result.result_rows[0][0]
        print(f"✅ Row count: {count}")

        # Cleanup test row (block 0 will be overwritten during migration anyway)
        # Note: We leave the test row since it will be replaced during actual migration

        print()
        print("=" * 50)
        print("✅ SCHEMA CREATION COMPLETE")
        print("=" * 50)
        print()
        print("Ready for historical data migration!")
        print("  Database: ethereum_mainnet")
        print("  Table: blocks")
        print("  Engine: ReplacingMergeTree")
        print(f"  Created: {datetime.now().isoformat()}")

        return True

    except Exception as e:
        print()
        print("=" * 50)
        print(f"❌ SCHEMA CREATION FAILED")
        print("=" * 50)
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    success = create_schema()
    sys.exit(0 if success else 1)
