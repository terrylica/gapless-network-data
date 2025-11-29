# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "clickhouse-connect>=0.7.0",
# ]
# ///
"""
Verify Ethereum blocks in ClickHouse Cloud.

Checks:
1. Total block count
2. Block range (min/max)
3. Latest block timestamp (freshness)
4. Gap detection (missing blocks)

Usage:
    doppler run --project aws-credentials --config prd -- uv run scripts/clickhouse/verify_blocks.py

Expected environment variables (from Doppler):
    CLICKHOUSE_HOST - ClickHouse Cloud hostname
    CLICKHOUSE_PASSWORD - Password
"""

import os
import sys
from datetime import datetime, timezone


def verify_blocks() -> bool:
    """Verify Ethereum blocks in ClickHouse Cloud."""
    import clickhouse_connect

    host = os.environ.get("CLICKHOUSE_HOST")
    password = os.environ.get("CLICKHOUSE_PASSWORD")

    if not host or not password:
        print("ERROR: Missing CLICKHOUSE_HOST or CLICKHOUSE_PASSWORD")
        print("Run with: doppler run --project aws-credentials --config prd -- uv run scripts/clickhouse/verify_blocks.py")
        return False

    print("Connecting to ClickHouse Cloud...")
    print(f"  Host: {host}")
    print()

    try:
        client = clickhouse_connect.get_client(
            host=host,
            port=8443,
            username="default",
            password=password,
            secure=True,
            connect_timeout=30,
        )

        # Check 1: Total block count
        result = client.query("SELECT COUNT(*) FROM ethereum_mainnet.blocks FINAL")
        total_blocks = result.result_rows[0][0]
        print(f"Total blocks: {total_blocks:,}")

        # Check 2: Block range
        result = client.query("SELECT MIN(number), MAX(number) FROM ethereum_mainnet.blocks FINAL")
        min_block, max_block = result.result_rows[0]
        print(f"Block range: {min_block:,} to {max_block:,}")

        # Check 3: Latest block timestamp (freshness)
        result = client.query("SELECT MAX(timestamp) FROM ethereum_mainnet.blocks FINAL")
        latest_timestamp = result.result_rows[0][0]

        # Handle timezone-aware comparison
        now = datetime.now(timezone.utc)
        if latest_timestamp.tzinfo is None:
            latest_timestamp = latest_timestamp.replace(tzinfo=timezone.utc)

        age_seconds = (now - latest_timestamp).total_seconds()
        print(f"Latest block: {latest_timestamp.isoformat()} ({age_seconds:.0f}s ago)")

        # Check 4: Expected vs actual blocks
        expected_blocks = max_block - min_block + 1
        missing_blocks = expected_blocks - total_blocks

        print()
        if missing_blocks == 0:
            print(f"Status: HEALTHY (zero gaps)")
        else:
            print(f"Status: GAPS DETECTED ({missing_blocks:,} missing blocks)")
            print(f"  Expected: {expected_blocks:,}")
            print(f"  Actual: {total_blocks:,}")
            print(f"  Missing: {missing_blocks:,}")

        # Check 5: Freshness assessment
        print()
        if age_seconds < 60:
            print(f"Freshness: GOOD (within 1 minute)")
        elif age_seconds < 300:
            print(f"Freshness: OK (within 5 minutes)")
        else:
            print(f"Freshness: STALE (over 5 minutes old)")
            print(f"  Check real-time collector: .claude/skills/vm-infrastructure-ops/scripts/check_vm_status.sh")

        # Summary
        print()
        print("=" * 50)
        if missing_blocks == 0 and age_seconds < 300:
            print("VERIFICATION PASSED")
            return True
        else:
            print("VERIFICATION WARNING")
            if missing_blocks > 0:
                print(f"  - {missing_blocks:,} gaps detected")
            if age_seconds >= 300:
                print(f"  - Data is {age_seconds/60:.1f} minutes stale")
            return False

    except Exception as e:
        print()
        print("=" * 50)
        print(f"VERIFICATION FAILED")
        print("=" * 50)
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check Doppler credentials: doppler secrets --project aws-credentials --config prd")
        print("2. Verify ClickHouse Cloud service is running")
        print("3. Run: doppler run -- uv run scripts/clickhouse/validate_connection.py")
        return False


if __name__ == "__main__":
    success = verify_blocks()
    sys.exit(0 if success else 1)
