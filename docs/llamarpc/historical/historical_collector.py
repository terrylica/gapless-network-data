#!/usr/bin/env python3
# /// script
# dependencies = ["requests", "pandas"]
# ///

"""
Historical Ethereum Block Collector (LlamaRPC)

⚠️ REFERENCE DOCUMENTATION: This is example code from LlamaRPC research (2025-11-03).
Production deployment uses BigQuery + Alchemy WebSocket (see deployment/vm/realtime_collector.py).

This file demonstrates:
- web3.py-style JSON-RPC integration patterns
- LlamaRPC endpoint usage
- Historical block fetching logic
- Batch requests with rate limiting
- Timestamp to block number conversion
- CSV export for analysis

For production code, see:
- deployment/vm/realtime_collector.py (real-time Alchemy WebSocket)
- deployment/backfill/historical_backfill.py (BigQuery historical backfill)
"""

import requests
import json
import time
import csv
from datetime import datetime
from typing import List, Dict, Optional, Tuple

LLAMARPC_URL = "https://eth.llamarpc.com"

# Rate limiting configuration
BATCH_SIZE = 20  # blocks per batch request
DELAY_BETWEEN_BATCHES = 1.0  # seconds


def fetch_block(block_number: int) -> Optional[Dict]:
    """Fetch a single block by number."""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": [hex(block_number), False],
        "id": 1
    }

    try:
        response = requests.post(LLAMARPC_URL, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result.get("result")
    except Exception as e:
        print(f"Error fetching block {block_number}: {e}")
        return None


def fetch_blocks_batch(block_numbers: List[int]) -> List[Dict]:
    """Fetch multiple blocks using JSON-RPC batch request."""
    batch_payload = [
        {
            "jsonrpc": "2.0",
            "method": "eth_getBlockByNumber",
            "params": [hex(num), False],
            "id": i
        }
        for i, num in enumerate(block_numbers)
    ]

    try:
        response = requests.post(LLAMARPC_URL, json=batch_payload, timeout=30)
        response.raise_for_status()
        results = response.json()

        blocks = []
        for result in results:
            if "result" in result and result["result"]:
                blocks.append(result["result"])

        return blocks
    except Exception as e:
        print(f"Batch request error: {e}")
        return []


def get_latest_block_number() -> Optional[int]:
    """Get the latest block number."""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_blockNumber",
        "id": 1
    }

    try:
        response = requests.post(LLAMARPC_URL, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        return int(result["result"], 16)
    except Exception:
        return None


def collect_blocks(start_block: int, end_block: int, output_file: str = "blocks.csv"):
    """
    Collect blocks in range [start_block, end_block] and save to CSV.

    Args:
        start_block: Starting block number (inclusive)
        end_block: Ending block number (inclusive)
        output_file: Output CSV file path
    """
    total_blocks = end_block - start_block + 1
    print(f"Collecting {total_blocks:,} blocks ({start_block:,} to {end_block:,})")

    all_blocks = []
    collected = 0

    # Create batches
    for batch_start in range(start_block, end_block + 1, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE - 1, end_block)
        batch_numbers = list(range(batch_start, batch_end + 1))

        # Fetch batch
        blocks = fetch_blocks_batch(batch_numbers)

        if blocks:
            all_blocks.extend(blocks)
            collected += len(blocks)

            # Progress
            progress = (collected / total_blocks) * 100
            print(f"Progress: {collected:,}/{total_blocks:,} ({progress:.1f}%) - "
                  f"Latest: block {batch_end:,}")

        # Rate limiting
        if batch_end < end_block:
            time.sleep(DELAY_BETWEEN_BATCHES)

    # Save to CSV
    print(f"\nSaving {len(all_blocks):,} blocks to {output_file}")

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'block_number',
            'timestamp',
            'datetime_utc',
            'hash',
            'parent_hash',
            'miner',
            'gas_used',
            'gas_limit',
            'base_fee_per_gas',
            'tx_count'
        ])

        # Data
        for block in all_blocks:
            block_num = int(block["number"], 16)
            timestamp = int(block["timestamp"], 16)
            dt = datetime.utcfromtimestamp(timestamp).isoformat() + "Z"
            gas_used = int(block["gasUsed"], 16)
            gas_limit = int(block["gasLimit"], 16)
            base_fee = int(block.get("baseFeePerGas", "0x0"), 16)
            tx_count = len(block.get("transactions", []))

            writer.writerow([
                block_num,
                timestamp,
                dt,
                block["hash"],
                block["parentHash"],
                block["miner"],
                gas_used,
                gas_limit,
                base_fee,
                tx_count
            ])

    print(f"Export complete: {output_file}")

    # Summary statistics
    if all_blocks:
        timestamps = [int(b["timestamp"], 16) for b in all_blocks]
        gas_used = [int(b["gasUsed"], 16) for b in all_blocks]
        tx_counts = [len(b.get("transactions", [])) for b in all_blocks]

        print(f"\nSummary:")
        print(f"  Time range: {datetime.utcfromtimestamp(min(timestamps)).isoformat()}Z to "
              f"{datetime.utcfromtimestamp(max(timestamps)).isoformat()}Z")
        print(f"  Avg gas used: {sum(gas_used) / len(gas_used):,.0f}")
        print(f"  Avg tx count: {sum(tx_counts) / len(tx_counts):.1f}")
        print(f"  Total transactions: {sum(tx_counts):,}")


def collect_recent_blocks(num_blocks: int = 100, output_file: str = "recent_blocks.csv"):
    """
    Collect the most recent N blocks.

    Args:
        num_blocks: Number of recent blocks to collect
        output_file: Output CSV file path
    """
    latest = get_latest_block_number()

    if latest is None:
        print("Failed to get latest block number")
        return

    start = latest - num_blocks + 1
    end = latest

    print(f"Latest block: {latest:,}")
    collect_blocks(start, end, output_file)


def collect_date_range(start_date: str, end_date: str, output_file: str = "date_range_blocks.csv"):
    """
    Collect blocks within a date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        output_file: Output CSV file path

    Note: This is approximate - uses average block time for estimation.
    For precise date ranges, use binary search to find exact blocks.
    """
    start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())

    print(f"Date range: {start_date} to {end_date}")
    print("Note: Using approximate block estimation (avg 12s per block)")

    # Rough estimation: 12 seconds per block (post-merge)
    latest = get_latest_block_number()
    if latest is None:
        print("Failed to get latest block")
        return

    latest_block = fetch_block(latest)
    if latest_block is None:
        print("Failed to fetch latest block")
        return

    current_ts = int(latest_block["timestamp"], 16)

    # Estimate blocks
    blocks_back_start = int((current_ts - start_ts) / 12)
    blocks_back_end = int((current_ts - end_ts) / 12)

    start_block = max(0, latest - blocks_back_start)
    end_block = latest - blocks_back_end

    print(f"Estimated block range: {start_block:,} to {end_block:,}")

    collect_blocks(start_block, end_block, output_file)


if __name__ == "__main__":
    print("LlamaRPC Historical Block Collector")
    print("=" * 80)

    # Example 1: Collect 100 most recent blocks
    print("\nExample 1: Collecting 100 most recent blocks")
    print("-" * 80)
    collect_recent_blocks(num_blocks=100, output_file="/tmp/llamarpc-historical-research/recent_100.csv")

    time.sleep(2)

    # Example 2: Collect specific block range
    print("\n\nExample 2: Collecting specific block range (21,540,000 to 21,540,200)")
    print("-" * 80)
    collect_blocks(
        start_block=21_540_000,
        end_block=21_540_200,
        output_file="/tmp/llamarpc-historical-research/block_range.csv"
    )

    print("\n" + "=" * 80)
    print("Collection complete!")
    print("\nFiles created:")
    print("  - /tmp/llamarpc-historical-research/recent_100.csv")
    print("  - /tmp/llamarpc-historical-research/block_range.csv")
