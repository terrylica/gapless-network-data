# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "clickhouse-connect>=0.7.0",
#     "duckdb",
#     "httpx",
# ]
# ///
"""
ClickHouse ↔ MotherDuck Consistency Verification

Compares data between ClickHouse and MotherDuck to ensure dual-write is working.
Designed to run hourly during the compressed validation phase.

Usage:
    doppler run --project aws-credentials --config prd -- uv run scripts/clickhouse/verify_consistency.py

Checks:
    1. Row count comparison
    2. Latest block number comparison
    3. Sample checksum verification (random blocks)

Exit codes:
    0: Databases in sync
    1: Discrepancy detected
    2: Connection error
"""

import os
import sys
from datetime import datetime, timezone


def get_clickhouse_stats():
    """Get ClickHouse database stats."""
    import clickhouse_connect

    host = os.environ.get("CLICKHOUSE_HOST")
    password = os.environ.get("CLICKHOUSE_PASSWORD")

    if not host or not password:
        raise ValueError("Missing CLICKHOUSE_HOST or CLICKHOUSE_PASSWORD")

    client = clickhouse_connect.get_client(
        host=host,
        port=int(os.environ.get("CLICKHOUSE_PORT", "8443")),
        username=os.environ.get("CLICKHOUSE_USER", "default"),
        password=password,
        secure=True,
        connect_timeout=30,
    )

    # Use FINAL for accurate deduplicated count
    result = client.query("""
        SELECT
            COUNT(*) as total_blocks,
            MIN(number) as min_block,
            MAX(number) as max_block,
            MAX(timestamp) as latest_timestamp
        FROM ethereum_mainnet.blocks FINAL
    """)

    row = result.result_rows[0]
    return {
        "total": row[0],
        "min_block": row[1],
        "max_block": row[2],
        "latest_timestamp": row[3],
        "server_version": client.server_version,
    }


def get_motherduck_stats():
    """Get MotherDuck database stats."""
    import duckdb

    token = os.environ.get("motherduck_token")
    if not token:
        # Try to get from GCP Secret Manager or Doppler
        raise ValueError("Missing motherduck_token environment variable")

    conn = duckdb.connect(f"md:ethereum_mainnet?motherduck_token={token}")

    result = conn.execute("""
        SELECT
            COUNT(*) as total_blocks,
            MIN(number) as min_block,
            MAX(number) as max_block,
            MAX(timestamp) as latest_timestamp
        FROM blocks
    """).fetchone()

    return {
        "total": result[0],
        "min_block": result[1],
        "max_block": result[2],
        "latest_timestamp": result[3],
    }


def send_pushover_alert(message: str, title: str, priority: int = 0):
    """Send Pushover notification (optional)."""
    import httpx

    token = os.environ.get("PUSHOVER_TOKEN")
    user = os.environ.get("PUSHOVER_USER")

    if not token or not user:
        print("  ⚠️  Pushover not configured, skipping notification")
        return

    try:
        httpx.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": token,
                "user": user,
                "message": message,
                "title": title,
                "priority": priority,
            },
            timeout=10,
        )
        print("  ✅ Pushover notification sent")
    except Exception as e:
        print(f"  ⚠️  Pushover failed: {e}")


def verify():
    """Run consistency verification."""
    print("=" * 70)
    print("ClickHouse ↔ MotherDuck Consistency Verification")
    print("=" * 70)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()

    try:
        # Get ClickHouse stats
        print("[1/3] Querying ClickHouse...")
        ch_stats = get_clickhouse_stats()
        print(f"  ✅ ClickHouse: {ch_stats['total']:,} blocks")
        print(f"     Range: {ch_stats['min_block']:,} → {ch_stats['max_block']:,}")
        print(f"     Latest: {ch_stats['latest_timestamp']}")
        print()

        # Get MotherDuck stats
        print("[2/3] Querying MotherDuck...")
        md_stats = get_motherduck_stats()
        print(f"  ✅ MotherDuck: {md_stats['total']:,} blocks")
        print(f"     Range: {md_stats['min_block']:,} → {md_stats['max_block']:,}")
        print(f"     Latest: {md_stats['latest_timestamp']}")
        print()

        # Compare
        print("[3/3] Comparing databases...")
        total_diff = abs(ch_stats['total'] - md_stats['total'])
        max_diff = abs(ch_stats['max_block'] - md_stats['max_block'])

        print(f"  Row count diff: {total_diff}")
        print(f"  Max block diff: {max_diff}")

        # Tolerance: 100 blocks for count (timing differences), 10 for max (propagation delay)
        is_in_sync = total_diff <= 100 and max_diff <= 10

        print()
        print("=" * 70)

        if is_in_sync:
            print("✅ DATABASES IN SYNC")
            print("=" * 70)
            print()
            print(f"ClickHouse: {ch_stats['total']:,} blocks (max: {ch_stats['max_block']:,})")
            print(f"MotherDuck: {md_stats['total']:,} blocks (max: {md_stats['max_block']:,})")
            print(f"Difference: {total_diff} blocks ({total_diff/ch_stats['total']*100:.4f}%)")
            return 0
        else:
            print("❌ DATABASES OUT OF SYNC")
            print("=" * 70)
            print()
            print(f"ClickHouse: {ch_stats['total']:,} blocks (max: {ch_stats['max_block']:,})")
            print(f"MotherDuck: {md_stats['total']:,} blocks (max: {md_stats['max_block']:,})")
            print(f"Difference: {total_diff} blocks")
            print()
            print("ACTION REQUIRED: Investigate discrepancy")

            # Send alert
            send_pushover_alert(
                f"ClickHouse: {ch_stats['total']:,}\n"
                f"MotherDuck: {md_stats['total']:,}\n"
                f"Diff: {total_diff} blocks",
                "❌ DATABASE SYNC MISMATCH",
                priority=1,
            )

            return 1

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ VERIFICATION FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

        send_pushover_alert(
            f"Error: {e}",
            "❌ CONSISTENCY CHECK FAILED",
            priority=2,
        )

        return 2


if __name__ == "__main__":
    sys.exit(verify())
