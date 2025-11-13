#!/usr/bin/env python3
"""
Verify MotherDuck database state for Ethereum blockchain data.

Usage:
    python3 verify_motherduck.py

Requires:
    - MOTHERDUCK_TOKEN environment variable or Doppler access
    - duckdb Python package
"""

# /// script
# dependencies = ["duckdb"]
# ///

import duckdb
import os
import sys
from subprocess import run, PIPE


def get_motherduck_token():
    """Get MotherDuck token from environment or Doppler."""
    token = os.environ.get('MOTHERDUCK_TOKEN')

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
        print("❌ Error: MOTHERDUCK_TOKEN not found in environment or Doppler")
        sys.exit(1)

    return token


def verify_database():
    """Verify MotherDuck ethereum_mainnet database state."""
    token = get_motherduck_token()

    try:
        conn = duckdb.connect(
            f'md:?motherduck_token={token}',
            config={'connect_timeout': 30000}  # 30 seconds
        )

        # Query database state
        result = conn.execute("""
            SELECT
                COUNT(*) as total_blocks,
                MIN(number) as min_block,
                MAX(number) as max_block,
                MIN(timestamp) as earliest_timestamp,
                MAX(timestamp) as latest_timestamp
            FROM ethereum_mainnet.blocks
        """).fetchone()

        print(f"\n📊 MotherDuck Database Status:")
        print(f"   Database: ethereum_mainnet")
        print(f"   Table: blocks")
        print(f"   Total blocks: {result[0]:,}")
        print(f"   Block range: {result[1]:,} → {result[2]:,}")
        print(f"   Time range: {result[3]} → {result[4]}")

        # Yearly breakdown (optional, only if >1M blocks)
        if result[0] > 1000000:
            yearly = conn.execute("""
                SELECT
                    YEAR(timestamp) as year,
                    COUNT(*) as blocks,
                    MIN(number) as min_block,
                    MAX(number) as max_block
                FROM ethereum_mainnet.blocks
                GROUP BY YEAR(timestamp)
                ORDER BY year
            """).fetchall()

            print(f"\n📅 Yearly Breakdown:")
            for row in yearly:
                print(f"   {row[0]}: {row[1]:,} blocks (#{row[2]:,} → #{row[3]:,})")

        # Expected: ~14.5M blocks for 2020-2025 historical backfill
        expected_min = 13000000
        expected_max = 15000000

        if expected_min <= result[0] <= expected_max:
            print(f"\n✅ Database state looks healthy!")
            print(f"   Expected range: {expected_min/1e6:.1f}M-{expected_max/1e6:.1f}M blocks")
        else:
            print(f"\n⚠️  Warning: Block count outside expected range!")
            print(f"   Expected: {expected_min/1e6:.1f}M-{expected_max/1e6:.1f}M blocks")
            print(f"   Actual: {result[0]/1e6:.1f}M blocks")

        conn.close()

    except Exception as e:
        print(f"❌ Error verifying database: {e}")
        sys.exit(1)


if __name__ == '__main__':
    verify_database()
