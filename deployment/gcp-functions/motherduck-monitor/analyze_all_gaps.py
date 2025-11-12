#!/usr/bin/env python3
"""
Analyze all gaps in MotherDuck Ethereum data.

Usage:
    python3 analyze_all_gaps.py
"""

# /// script
# dependencies = ["duckdb"]
# ///

import duckdb
from subprocess import run, PIPE


def get_motherduck_token():
    """Get MotherDuck token from GCP Secret Manager or environment."""
    import os
    token = os.environ.get('MOTHERDUCK_TOKEN')

    if not token:
        # Try GCP Secret Manager
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
        import sys
        sys.exit(1)

    return token


def analyze_all_gaps():
    """Analyze all gaps in the 1-year window."""
    token = get_motherduck_token()
    conn = duckdb.connect(f'md:?motherduck_token={token}')

    print("\n" + "=" * 80)
    print("ANALYZING ALL GAPS (1 YEAR WINDOW)")
    print("=" * 80)
    print()

    # Query all gaps
    query = """
    WITH gaps AS (
        SELECT
            number AS block_number,
            timestamp,
            LAG(timestamp) OVER (ORDER BY timestamp) AS prev_timestamp,
            EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (ORDER BY timestamp))) AS gap_seconds
        FROM ethereum_mainnet.blocks
        WHERE timestamp BETWEEN (CURRENT_TIMESTAMP - INTERVAL '365 days')
                            AND (CURRENT_TIMESTAMP - INTERVAL '3 minutes')
    )
    SELECT
        block_number,
        timestamp,
        prev_timestamp,
        gap_seconds,
        ROUND(gap_seconds / 60.0, 2) AS gap_minutes
    FROM gaps
    WHERE gap_seconds > 15
    ORDER BY gap_seconds DESC
    LIMIT 100
    """

    result = conn.execute(query).fetchall()

    print(f"Found {len(result)} gaps > 15 seconds\n")
    print("=" * 80)

    # Analyze each gap
    gaps_by_severity = {
        'critical': [],  # >60s
        'high': [],      # 30-60s
        'medium': [],    # 20-30s
        'low': [],       # 15-20s
    }

    for row in result:
        block_number = row[0]
        timestamp = row[1]
        prev_timestamp = row[2]
        gap_seconds = row[3]
        gap_minutes = row[4]

        # Categorize by severity
        if gap_seconds > 60:
            severity = 'critical'
        elif gap_seconds > 30:
            severity = 'high'
        elif gap_seconds > 20:
            severity = 'medium'
        else:
            severity = 'low'

        gaps_by_severity[severity].append({
            'block_number': block_number,
            'timestamp': timestamp,
            'prev_timestamp': prev_timestamp,
            'gap_seconds': gap_seconds,
            'gap_minutes': gap_minutes,
        })

    # Report by severity
    print(f"\n📊 GAPS BY SEVERITY\n")
    print(f"{'Severity':<10} {'Count':<8} {'Range':<20}")
    print("-" * 80)
    print(f"{'CRITICAL':<10} {len(gaps_by_severity['critical']):<8} >60 seconds")
    print(f"{'HIGH':<10} {len(gaps_by_severity['high']):<8} 30-60 seconds")
    print(f"{'MEDIUM':<10} {len(gaps_by_severity['medium']):<8} 20-30 seconds")
    print(f"{'LOW':<10} {len(gaps_by_severity['low']):<8} 15-20 seconds")
    print()

    # Show top 20 largest gaps
    print("=" * 80)
    print("TOP 20 LARGEST GAPS")
    print("=" * 80)
    print()
    print(f"{'Rank':<6} {'Block':>12} {'Gap':>8} {'Date':^20} {'Time Range'}")
    print("-" * 80)

    for i, row in enumerate(result[:20], 1):
        block_number = row[0]
        timestamp = row[1]
        prev_timestamp = row[2]
        gap_seconds = row[3]
        gap_minutes = row[4]

        date_str = timestamp.strftime('%Y-%m-%d')
        time_range = f"{prev_timestamp.strftime('%H:%M:%S')} → {timestamp.strftime('%H:%M:%S')}"

        print(f"{i:<6} {block_number:>12,} {gap_seconds:>6.0f}s  {date_str:^20} {time_range}")

    # Check for patterns
    print("\n" + "=" * 80)
    print("PATTERN ANALYSIS")
    print("=" * 80)
    print()

    # Check if gaps cluster around specific dates
    from collections import Counter
    gap_dates = [row[1].date() for row in result]
    date_counts = Counter(gap_dates)

    print("📅 GAPS BY DATE (top 10 dates with most gaps):\n")
    for date, count in date_counts.most_common(10):
        print(f"   {date}: {count} gaps")

    # Check missing blocks
    print("\n" + "=" * 80)
    print("MISSING BLOCKS CHECK")
    print("=" * 80)
    print()

    # Check for gaps >1 block difference
    missing_blocks_query = """
    WITH gaps AS (
        SELECT
            number AS block_number,
            LAG(number) OVER (ORDER BY number) AS prev_block,
            number - LAG(number) OVER (ORDER BY number) AS block_gap
        FROM ethereum_mainnet.blocks
        WHERE timestamp BETWEEN (CURRENT_TIMESTAMP - INTERVAL '365 days')
                            AND (CURRENT_TIMESTAMP - INTERVAL '3 minutes')
    )
    SELECT block_number, prev_block, block_gap
    FROM gaps
    WHERE block_gap > 1
    ORDER BY block_gap DESC
    LIMIT 20
    """

    missing_result = conn.execute(missing_blocks_query).fetchall()

    if missing_result:
        print(f"⚠️  Found {len(missing_result)} locations with missing blocks:\n")
        print(f"{'Block Number':>15} {'Previous Block':>15} {'Missing Blocks':>15}")
        print("-" * 80)
        for row in missing_result[:10]:
            block_number = row[0]
            prev_block = row[1]
            block_gap = row[2]
            missing_count = block_gap - 1
            print(f"{block_number:>15,} {prev_block:>15,} {missing_count:>15,}")
    else:
        print("✅ No missing blocks in sequence")

    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()

    critical_count = len(gaps_by_severity['critical'])
    high_count = len(gaps_by_severity['high'])

    if critical_count > 0 or high_count > 5:
        print("""
⚠️  SIGNIFICANT GAPS DETECTED

Found {} critical gaps (>60s) and {} high-severity gaps (30-60s).

RECOMMENDED ACTIONS:
1. Investigate top 10 largest gaps individually with investigate_gap.py
2. Check if gaps cluster around specific time periods
3. Review pipeline logs for those time periods
4. Consider adding more gaps to KNOWN_LEGITIMATE_GAPS if validated

NEXT STEPS:
- Run: python3 investigate_gap.py <block_number>
- For each of the top 10 largest gaps
- Verify with external sources (Etherscan, Beaconcha.in)
""".format(critical_count, high_count))
    else:
        print("""
✅ GAPS APPEAR NORMAL

Most gaps are <30 seconds, which is typical for Ethereum due to:
- Occasional missed validator proposals
- Network congestion
- Protocol events

RECOMMENDATION: These gaps are likely legitimate network behavior and can be
added to KNOWN_LEGITIMATE_GAPS after individual verification.
""")

    conn.close()


if __name__ == '__main__':
    analyze_all_gaps()
