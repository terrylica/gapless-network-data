#!/usr/bin/env python3
"""
Basic usage example for gapless-network-data.

Demonstrates:
1. Getting the latest mempool snapshot
2. Collecting snapshots for a time range
3. Basic data inspection
"""

import gapless_network_data as gmd


def main():
    print("=" * 80)
    print("Gapless Mempool Data - Basic Usage Example")
    print("=" * 80)
    print()

    # Example 1: Get latest snapshot
    print("Example 1: Get Latest Snapshot")
    print("-" * 80)
    snapshot = gmd.get_latest_snapshot()
    print(f"Timestamp: {snapshot['timestamp']}")
    print(f"Unconfirmed transactions: {snapshot['unconfirmed_count']:,}")
    print(f"Mempool size: {snapshot['vsize_mb']:.2f} MB")
    print(f"Total fees: {snapshot['total_fee_btc']:.4f} BTC")
    print(f"Fastest fee: {snapshot['fastest_fee']} sat/vB")
    print(f"Half-hour fee: {snapshot['half_hour_fee']} sat/vB")
    print(f"Hour fee: {snapshot['hour_fee']} sat/vB")
    print(f"Economy fee: {snapshot['economy_fee']} sat/vB")
    print()

    # Example 2: Collect forward snapshots (real-time)
    print("Example 2: Collect Forward Snapshots (Real-Time)")
    print("-" * 80)
    print("NOTE: This tool only supports forward collection (real-time).")
    print("Historical data collection is not supported as mempool.space does not")
    print("provide historical snapshot APIs. Run this tool continuously as a daemon")
    print("to build historical datasets.")
    print()

    # Collect 5 snapshots at 60-second intervals starting from now
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    df = gmd.fetch_snapshots(
        start=now.isoformat(),
        end=(now + timedelta(minutes=5)).isoformat(),
        interval=60,
    )

    print(f"Collected {len(df)} snapshots")
    print()
    print("Sample data:")
    print(df.head())
    print()

    # Basic statistics
    print("Summary statistics:")
    print(f"  Avg unconfirmed count: {df['unconfirmed_count'].mean():,.0f}")
    print(f"  Avg mempool size: {df['vsize_mb'].mean():.2f} MB")
    print(f"  Avg fastest fee: {df['fastest_fee'].mean():.2f} sat/vB")
    print()

    print("=" * 80)
    print("Example complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
