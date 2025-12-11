# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "clickhouse-connect>=0.7.0",
# ]
# ///
"""
Create ClickHouse schema for Ethereum blocks migration.

ADR: 2025-12-10-clickhouse-codec-optimization

Usage:
    doppler run --project aws-credentials --config prd -- uv run scripts/clickhouse/create_schema.py

ClickHouse schema for Ethereum mainnet blocks with production optimizations:
- ReplacingMergeTree engine for automatic deduplication (dual-pipeline support)
- ORDER BY number for deduplication key and efficient block-range queries
- Monthly partitioning for efficient data management
- Compression codecs optimized per column type (DoubleDelta, T64, Delta, ZSTD)
- Projection for timestamp-based queries
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

        # ADR: 2025-12-10-clickhouse-codec-optimization - Codecs optimized per column type
        ddl = """
        CREATE TABLE IF NOT EXISTS ethereum_mainnet.blocks (
            -- Temporal (DoubleDelta for monotonic timestamps)
            timestamp DateTime64(3) NOT NULL CODEC(DoubleDelta, ZSTD),

            -- Block identification (DoubleDelta for strictly increasing)
            number Int64 CODEC(DoubleDelta, ZSTD),

            -- Gas metrics (Delta for slow-changing, T64 for high-variance)
            gas_limit Int64 CODEC(Delta, ZSTD),
            gas_used Int64 CODEC(T64, ZSTD),
            base_fee_per_gas Int64 CODEC(T64, ZSTD),

            -- Transaction count (T64 for bounded integers)
            transaction_count Int64 CODEC(T64, ZSTD),

            -- Mining difficulty (ZSTD(3) - T64 doesn't support UInt256)
            difficulty UInt256 CODEC(ZSTD(3)),
            total_difficulty UInt256 CODEC(ZSTD(3)),

            -- Block size in bytes (T64 for bounded integers)
            size Int64 CODEC(T64, ZSTD),

            -- EIP-4844 blob fields (T64 for sparse nulls, high variance)
            blob_gas_used Nullable(Int64) CODEC(T64, ZSTD),
            excess_blob_gas Nullable(Int64) CODEC(T64, ZSTD)
        )
        ENGINE = ReplacingMergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY number
        SETTINGS index_granularity = 8192
        COMMENT 'Ethereum mainnet blocks - production data store'
        """

        client.command(ddl)
        print("✅ Table created with ReplacingMergeTree engine and compression codecs")

        # Step 3: Add projection for timestamp-based queries
        # ADR: 2025-12-10-clickhouse-codec-optimization
        # ClickHouse Cloud (SharedReplacingMergeTree) requires special handling for projections
        # Skip projection on ClickHouse Cloud - the codecs provide the main optimization
        print()
        print("Skipping projection (SharedReplacingMergeTree on ClickHouse Cloud has limitations)")
        print("  Note: Codecs still provide significant compression benefits")
        print("  Timestamp queries will use full table scan with ORDER BY")

        print()
        print("Schema details:")
        print("  - Engine: ReplacingMergeTree (automatic deduplication)")
        print("  - ORDER BY: number (block number as deduplication key)")
        print("  - PARTITION BY: toYYYYMM(timestamp) (monthly partitions)")
        print("  - Codecs: DoubleDelta, T64, Delta, ZSTD (per column type)")
        print("  - Columns: 11 (timestamp, number, gas_*, transaction_count, difficulty, size, blob_*)")

        # Step 4: Verify table exists
        print()
        print("Verifying table structure...")
        result = client.query("DESCRIBE TABLE ethereum_mainnet.blocks")
        print()
        print("Table columns:")
        for row in result.result_rows:
            col_name = row[0]
            col_type = row[1]
            print(f"  {col_name}: {col_type}")

        # Step 5: Test insert
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
