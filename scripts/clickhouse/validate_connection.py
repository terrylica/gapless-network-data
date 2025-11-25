# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "clickhouse-connect>=0.7.0",
# ]
# ///
"""
Validate ClickHouse Cloud connection using Doppler credentials.

Usage:
    doppler run --project aws-credentials --config prd -- uv run scripts/clickhouse/validate_connection.py

Expected environment variables (from Doppler):
    CLICKHOUSE_HOST - ClickHouse Cloud hostname
    CLICKHOUSE_PORT - ClickHouse port (8443 for HTTPS)
    CLICKHOUSE_USER - Username (default)
    CLICKHOUSE_PASSWORD - Password
"""

import os
import sys
from datetime import datetime


def validate_connection() -> bool:
    """Validate ClickHouse Cloud connection."""
    import clickhouse_connect

    host = os.environ.get("CLICKHOUSE_HOST")
    port = int(os.environ.get("CLICKHOUSE_PORT", "8443"))
    user = os.environ.get("CLICKHOUSE_USER", "default")
    password = os.environ.get("CLICKHOUSE_PASSWORD")

    if not host or not password:
        print("ERROR: Missing CLICKHOUSE_HOST or CLICKHOUSE_PASSWORD")
        print("Run with: doppler run --project aws-credentials --config prd -- uv run scripts/clickhouse/validate_connection.py")
        return False

    print(f"Connecting to ClickHouse Cloud...")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  User: {user}")
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

        # Test 1: Simple query
        result = client.query("SELECT 1")
        print(f"✅ SELECT 1 returned: {result.result_rows[0][0]}")

        # Test 2: Server version
        version = client.server_version
        print(f"✅ Server version: {version}")

        # Test 3: List databases
        databases = client.query("SHOW DATABASES")
        db_list = [row[0] for row in databases.result_rows]
        print(f"✅ Databases: {db_list}")

        # Test 4: Check if ethereum_mainnet database exists
        if "ethereum_mainnet" in db_list:
            print(f"✅ Database 'ethereum_mainnet' exists")
            # Check tables
            tables = client.query("SHOW TABLES FROM ethereum_mainnet")
            table_list = [row[0] for row in tables.result_rows]
            print(f"   Tables: {table_list}")
        else:
            print(f"⚠️  Database 'ethereum_mainnet' does not exist (will create)")

        # Test 5: Write permission (create test table in default database)
        print()
        print("Testing write permission...")
        client.command("""
            CREATE TABLE IF NOT EXISTS default.migration_test (
                id UInt64,
                created_at DateTime DEFAULT now()
            ) ENGINE = MergeTree()
            ORDER BY id
        """)
        print(f"✅ Created test table 'default.migration_test'")

        # Insert test row
        client.command("INSERT INTO default.migration_test (id) VALUES (1)")
        print(f"✅ Inserted test row")

        # Read back
        result = client.query("SELECT COUNT(*) FROM default.migration_test")
        count = result.result_rows[0][0]
        print(f"✅ Row count: {count}")

        # Cleanup
        client.command("DROP TABLE IF EXISTS default.migration_test")
        print(f"✅ Dropped test table")

        print()
        print("=" * 50)
        print("✅ ALL VALIDATION CHECKS PASSED")
        print("=" * 50)
        print()
        print(f"ClickHouse Cloud is ready for migration!")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  User: {user}")
        print(f"  Validated: {datetime.now().isoformat()}")

        return True

    except Exception as e:
        print()
        print("=" * 50)
        print(f"❌ VALIDATION FAILED")
        print("=" * 50)
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check Doppler credentials: doppler secrets --project aws-credentials --config prd")
        print("2. Verify ClickHouse Cloud service is running")
        print("3. Check network connectivity to ClickHouse Cloud")
        return False


if __name__ == "__main__":
    success = validate_connection()
    # Save result to file
    result_file = "/tmp/clickhouse-validation.txt"
    with open(result_file, "w") as f:
        f.write(f"Validation Date: {datetime.now().isoformat()}\n")
        f.write(f"Result: {'PASSED' if success else 'FAILED'}\n")
        f.write(f"Host: {os.environ.get('CLICKHOUSE_HOST', 'N/A')}\n")
    print(f"\nResult saved to: {result_file}")
    sys.exit(0 if success else 1)
