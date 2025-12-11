# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "clickhouse-connect>=0.7.0",
# ]
# ///
"""
Set up local ClickHouse database for development.

Usage:
    uv run scripts/clickhouse/setup_local.py

This script creates the ethereum_mainnet database and blocks table
on a local ClickHouse server (no authentication, no TLS).

Prerequisites:
    - ClickHouse installed: mise install clickhouse
    - Server running: clickhouse server (in background)
"""

import sys


def setup_local() -> bool:
    """Create local ClickHouse schema for development."""
    import clickhouse_connect

    # Local ClickHouse defaults (no auth, HTTP interface)
    host = "localhost"
    port = 8123  # HTTP interface (not 9000 native)

    print("Setting up local ClickHouse for development...")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print()

    try:
        client = clickhouse_connect.get_client(
            host=host,
            port=port,
            # No username/password for local development
            connect_timeout=10,
        )

        # Test connection
        result = client.query("SELECT 1")
        print(f"✅ Connection successful (SELECT 1 = {result.result_rows[0][0]})")

        # Step 1: Create database
        print()
        print("Creating database 'ethereum_mainnet'...")
        client.command("CREATE DATABASE IF NOT EXISTS ethereum_mainnet")
        print("✅ Database created")

        # Step 2: Create table with same schema as production
        # ADR: 2025-12-10-clickhouse-codec-optimization
        print()
        print("Creating table 'ethereum_mainnet.blocks'...")

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
        COMMENT 'Ethereum mainnet blocks - local development'
        """

        client.command(ddl)
        print("✅ Table created with ReplacingMergeTree engine")

        # Step 3: Verify schema
        print()
        print("Verifying table structure...")
        result = client.query("DESCRIBE TABLE ethereum_mainnet.blocks")

        print()
        print("Table columns:")
        for row in result.result_rows:
            col_name = row[0]
            col_type = row[1]
            print(f"  {col_name}: {col_type}")

        # Step 4: Insert test row
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

        # Verify
        result = client.query("SELECT COUNT(*) FROM ethereum_mainnet.blocks")
        count = result.result_rows[0][0]
        print(f"✅ Row count: {count}")

        print()
        print("=" * 60)
        print("✅ LOCAL SETUP COMPLETE")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Load sample data:")
        print("     uv run scripts/clickhouse/load_sample_data.py")
        print()
        print("  2. Or sync from production (requires Doppler):")
        print("     uv run scripts/clickhouse/sync_to_local.py --limit 10000")
        print()
        print("  3. Test SDK locally:")
        print("     export CLICKHOUSE_HOST_READONLY=localhost")
        print("     export CLICKHOUSE_USER_READONLY=default")
        print("     export CLICKHOUSE_PASSWORD_READONLY=")
        print("     python -c 'import gapless_network_data as gmd; print(gmd.fetch_blocks(limit=10))'")

        return True

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ LOCAL SETUP FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Ensure ClickHouse server is running:")
        print("     clickhouse server  # Run in separate terminal")
        print()
        print("  2. Check if port 8123 is available:")
        print("     lsof -i :8123")
        print()
        print("  3. Install ClickHouse if needed:")
        print("     mise install clickhouse")
        return False


if __name__ == "__main__":
    success = setup_local()
    sys.exit(0 if success else 1)
