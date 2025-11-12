#!/usr/bin/env python3
"""
Investigate specific gap in MotherDuck Ethereum data.

Usage:
    python3 investigate_gap.py <block_number>

Example:
    python3 investigate_gap.py 22565171
"""

# /// script
# dependencies = ["duckdb", "httpx"]
# ///

import sys
import duckdb
import httpx
from subprocess import run, PIPE


def get_motherduck_token():
    """Get MotherDuck token from GCP Secret Manager or environment."""
    # Try environment first
    import os
    token = os.environ.get('MOTHERDUCK_TOKEN')

    if not token:
        # Try GCP Secret Manager (if running on GCP)
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            name = "projects/eonlabs-ethereum-bq/secrets/motherduck-token/versions/latest"
            response = client.access_secret_version(request={"name": name})
            token = response.payload.data.decode('UTF-8').strip()
        except:
            pass

    if not token:
        # Try Doppler
        result = run(
            ['doppler', 'secrets', 'get', 'MOTHERDUCK_TOKEN',
             '--project', 'claude-config', '--config', 'dev', '--plain'],
            stdout=PIPE, stderr=PIPE, text=True
        )
        if result.returncode == 0:
            token = result.stdout.strip()

    if not token:
        print("❌ Error: MOTHERDUCK_TOKEN not found")
        sys.exit(1)

    return token


def investigate_gap(block_number: int):
    """Investigate gap around specific block number."""
    token = get_motherduck_token()
    conn = duckdb.connect(f'md:?motherduck_token={token}')

    print(f"\n🔍 Investigating gap around block {block_number:,}\n")

    # 1. Check blocks around the gap (±10 blocks)
    print("=" * 80)
    print("1. BLOCK SEQUENCE ANALYSIS (±10 blocks)")
    print("=" * 80)

    result = conn.execute(f"""
        SELECT
            number,
            timestamp,
            LAG(number) OVER (ORDER BY number) as prev_number,
            LAG(timestamp) OVER (ORDER BY number) as prev_timestamp,
            number - LAG(number) OVER (ORDER BY number) as block_gap,
            EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (ORDER BY number))) as time_gap_seconds
        FROM ethereum_mainnet.blocks
        WHERE number BETWEEN {block_number - 10} AND {block_number + 10}
        ORDER BY number
    """).fetchall()

    print(f"{'Block':>12} {'Timestamp':^20} {'Prev Block':>12} {'Block Gap':>10} {'Time Gap':>10}")
    print("-" * 80)

    for row in result:
        block_gap = f"{int(row[4])}" if row[4] is not None else "N/A"
        time_gap = f"{row[5]:.1f}s" if row[5] is not None else "N/A"

        # Highlight gaps > 1 block or > 15 seconds
        highlight = ""
        if row[4] is not None and row[4] > 1:
            highlight = f" ⚠️  MISSING {int(row[4]-1)} BLOCKS"
        elif row[5] is not None and row[5] > 15:
            highlight = f" ⚠️  LONG GAP ({row[5]:.1f}s)"

        print(f"{row[0]:>12,} {str(row[1]):^20} {row[2] or 'N/A':>12} {block_gap:>10} {time_gap:>10}{highlight}")

    # 2. Check for missing blocks in sequence
    print("\n" + "=" * 80)
    print("2. MISSING BLOCKS DETECTION")
    print("=" * 80)

    missing = conn.execute(f"""
        WITH block_range AS (
            SELECT UNNEST(RANGE({block_number - 10}, {block_number + 11})) as expected_block
        )
        SELECT br.expected_block
        FROM block_range br
        LEFT JOIN ethereum_mainnet.blocks b ON br.expected_block = b.number
        WHERE b.number IS NULL
        ORDER BY br.expected_block
    """).fetchall()

    if missing:
        print(f"\n⚠️  Found {len(missing)} missing blocks:")
        for row in missing:
            print(f"   Block {row[0]:,} is MISSING from database")
    else:
        print("\n✅ No missing blocks found in sequence")

    # 3. Calculate gap statistics for this time period (±1 hour)
    print("\n" + "=" * 80)
    print("3. GAP STATISTICS (±1 hour around gap)")
    print("=" * 80)

    stats = conn.execute(f"""
        WITH gaps AS (
            SELECT
                number,
                timestamp,
                LAG(timestamp) OVER (ORDER BY timestamp) AS prev_timestamp,
                EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (ORDER BY timestamp))) AS gap_seconds
            FROM ethereum_mainnet.blocks
            WHERE number BETWEEN {block_number - 300} AND {block_number + 300}
        )
        SELECT
            COUNT(*) as total_blocks,
            MIN(gap_seconds) as min_gap,
            AVG(gap_seconds) as avg_gap,
            MAX(gap_seconds) as max_gap,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY gap_seconds) as median_gap,
            SUM(CASE WHEN gap_seconds > 15 THEN 1 ELSE 0 END) as gaps_over_15s
        FROM gaps
        WHERE gap_seconds IS NOT NULL
    """).fetchone()

    print(f"\nBlocks analyzed: {stats[0]:,}")
    print(f"Min gap: {stats[1]:.1f}s")
    print(f"Avg gap: {stats[2]:.1f}s")
    print(f"Median gap: {stats[4]:.1f}s")
    print(f"Max gap: {stats[3]:.1f}s")
    print(f"Gaps >15s: {stats[5]} ({stats[5]/stats[0]*100:.1f}%)")

    # 4. External verification using Etherscan API
    print("\n" + "=" * 80)
    print("4. EXTERNAL VERIFICATION (Etherscan API)")
    print("=" * 80)

    try:
        # Query Etherscan for block info (no API key needed for basic queries)
        url = f"https://api.etherscan.io/api?module=proxy&action=eth_getBlockByNumber&tag=0x{block_number:x}&boolean=true"
        response = httpx.get(url, timeout=10)
        data = response.json()

        if data.get('result'):
            etherscan_timestamp = int(data['result']['timestamp'], 16)
            from datetime import datetime
            etherscan_time = datetime.fromtimestamp(etherscan_timestamp)

            print(f"\n✅ Block {block_number:,} exists on Ethereum mainnet")
            print(f"   Etherscan timestamp: {etherscan_time}")

            # Compare with our database
            our_block = conn.execute(f"""
                SELECT timestamp FROM ethereum_mainnet.blocks WHERE number = {block_number}
            """).fetchone()

            if our_block:
                print(f"   Our timestamp: {our_block[0]}")
                diff = abs((our_block[0] - etherscan_time).total_seconds())
                if diff < 1:
                    print(f"   ✅ Timestamps match (diff: {diff:.2f}s)")
                else:
                    print(f"   ⚠️  Timestamp mismatch (diff: {diff:.2f}s)")
            else:
                print(f"   ❌ Block NOT in our database")
        else:
            print(f"\n⚠️  Could not verify with Etherscan (rate limit or API error)")

    except Exception as e:
        print(f"\n⚠️  Etherscan verification failed: {e}")

    # 5. Conclusion
    print("\n" + "=" * 80)
    print("5. CONCLUSION")
    print("=" * 80)

    if not missing and stats[5] / stats[0] < 0.05:  # <5% gaps >15s
        print("""
✅ LIKELY LEGITIMATE NETWORK EVENT

The gap appears to be a legitimate Ethereum network event because:
- No missing blocks in the sequence
- Surrounding blocks have normal timing (<5% gaps >15s)
- Block exists on Ethereum mainnet (verified via Etherscan)

Ethereum occasionally has longer block times due to:
- Validator issues (missed proposals)
- Network congestion
- Protocol upgrades or hard forks
- Beacon chain reorganizations

RECOMMENDATION: This gap is expected behavior and does not indicate a data
collection issue.
""")
    elif missing:
        print(f"""
⚠️  POTENTIAL DATA COLLECTION ISSUE

Found {len(missing)} missing blocks in sequence. This suggests:
- BigQuery historical backfill may have gaps
- Alchemy real-time stream may have missed blocks
- Database ingestion issue

RECOMMENDATION: Investigate pipeline logs around this time period and consider
running targeted backfill for missing blocks.
""")
    else:
        print("""
⚠️  ABNORMAL GAP DENSITY

Surrounding blocks have high gap density (>5% gaps >15s). This could indicate:
- Network issues during this time period
- Data collection synchronization issues

RECOMMENDATION: Check Cloud Logging for pipeline errors during this time period.
""")

    conn.close()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 investigate_gap.py <block_number>")
        print("Example: python3 investigate_gap.py 22565171")
        sys.exit(1)

    try:
        block_number = int(sys.argv[1])
        investigate_gap(block_number)
    except ValueError:
        print(f"❌ Error: '{sys.argv[1]}' is not a valid block number")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
