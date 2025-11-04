#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

"""Timestamp to block number mapping using binary search."""

import requests
import time
from datetime import datetime

LLAMARPC_URL = "https://eth.llamarpc.com"

# Known Ethereum constants
GENESIS_TIMESTAMP = 1438269973  # July 30, 2015
MERGE_BLOCK = 15537394  # The Merge (Sep 15, 2022)
MERGE_TIMESTAMP = 1663224179

# Average block times
PRE_MERGE_BLOCK_TIME = 13.3  # seconds (PoW)
POST_MERGE_BLOCK_TIME = 12.0  # seconds (PoS)

def fetch_block(block_number):
    """Fetch a block by number."""
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

        if "error" in result:
            return None

        return result.get("result")
    except Exception:
        return None

def get_latest_block():
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

        if "result" in result:
            return int(result["result"], 16)
    except Exception:
        pass

    return None

def estimate_block_from_timestamp(target_timestamp):
    """Estimate block number from timestamp using known constants."""
    latest_block = get_latest_block()

    if latest_block is None:
        return None

    # Fetch latest block to get current timestamp
    latest_block_data = fetch_block(latest_block)
    if latest_block_data is None:
        return None

    current_timestamp = int(latest_block_data["timestamp"], 16)

    # If target is after merge, use post-merge block time
    if target_timestamp >= MERGE_TIMESTAMP:
        blocks_from_merge = int((target_timestamp - MERGE_TIMESTAMP) / POST_MERGE_BLOCK_TIME)
        estimated_block = MERGE_BLOCK + blocks_from_merge
    else:
        # Pre-merge: use genesis as reference
        blocks_from_genesis = int((target_timestamp - GENESIS_TIMESTAMP) / PRE_MERGE_BLOCK_TIME)
        estimated_block = blocks_from_genesis

    # Clamp to valid range
    estimated_block = max(0, min(estimated_block, latest_block))

    return estimated_block

def find_block_by_timestamp(target_timestamp, tolerance=60):
    """
    Find block closest to target timestamp using binary search.

    Args:
        target_timestamp: Unix timestamp
        tolerance: Acceptable difference in seconds (default 60s = ~5 blocks)

    Returns:
        (block_number, block_timestamp) or (None, None)
    """
    # Get initial estimate
    estimated_block = estimate_block_from_timestamp(target_timestamp)

    if estimated_block is None:
        print("Could not estimate starting block")
        return None, None

    print(f"Estimated block: {estimated_block:,}")

    # Binary search
    left = max(0, estimated_block - 10000)  # Search window: +/- 10k blocks (~1.5 days)
    right = estimated_block + 10000

    latest = get_latest_block()
    if latest:
        right = min(right, latest)

    best_block = None
    best_diff = float('inf')
    iterations = 0
    max_iterations = 20

    while left <= right and iterations < max_iterations:
        mid = (left + right) // 2
        block = fetch_block(mid)

        if block is None:
            print(f"Failed to fetch block {mid}")
            break

        block_timestamp = int(block["timestamp"], 16)
        diff = abs(block_timestamp - target_timestamp)

        print(f"Iteration {iterations + 1}: Block {mid:,}, timestamp {block_timestamp}, diff {diff}s")

        if diff < best_diff:
            best_diff = diff
            best_block = mid

        if diff <= tolerance:
            print(f"Found block within tolerance: {mid:,} (diff: {diff}s)")
            return mid, block_timestamp

        if block_timestamp < target_timestamp:
            left = mid + 1
        else:
            right = mid - 1

        iterations += 1
        time.sleep(0.5)  # Rate limiting

    if best_block is not None:
        block = fetch_block(best_block)
        if block:
            return best_block, int(block["timestamp"], 16)

    return None, None

# Test cases
print("Testing Timestamp to Block Number Mapping")
print("=" * 80)

test_timestamps = [
    ("2024-01-01 00:00:00 UTC", int(datetime(2024, 1, 1, 0, 0, 0).timestamp())),
    ("2023-01-01 00:00:00 UTC", int(datetime(2023, 1, 1, 0, 0, 0).timestamp())),
    ("2022-09-15 06:42:42 UTC (The Merge)", MERGE_TIMESTAMP),
    ("2021-01-01 00:00:00 UTC", int(datetime(2021, 1, 1, 0, 0, 0).timestamp())),
]

for label, target_ts in test_timestamps:
    print(f"\n{label}")
    print(f"Target timestamp: {target_ts}")

    block_num, block_ts = find_block_by_timestamp(target_ts)

    if block_num:
        dt = datetime.utcfromtimestamp(block_ts)
        diff = abs(block_ts - target_ts)
        print(f"Result: Block {block_num:,}")
        print(f"Block timestamp: {block_ts} ({dt.isoformat()}Z)")
        print(f"Difference: {diff}s (~{diff/12:.1f} blocks)")
    else:
        print("FAILED to find block")

    print("-" * 80)
    time.sleep(1)

print("\nMapping Strategy:")
print("1. Use estimate_block_from_timestamp() for initial guess")
print("2. Binary search within +/- 10k block window")
print("3. Typical accuracy: Within 60 seconds of target")
print("4. Average search iterations: 10-15")
