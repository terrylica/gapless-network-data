#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

"""Test JSON-RPC batch requests for bulk block fetching."""

import requests
import json
import time

LLAMARPC_URL = "https://eth.llamarpc.com"

def fetch_blocks_sequential(start_block, count):
    """Fetch blocks one by one."""
    blocks = []
    start_time = time.time()

    for i in range(count):
        block_num = start_block + i
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getBlockByNumber",
            "params": [hex(block_num), False],
            "id": i
        }

        try:
            response = requests.post(LLAMARPC_URL, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()

            if "result" in result and result["result"]:
                blocks.append(result["result"])
        except Exception as e:
            print(f"Error fetching block {block_num}: {e}")

    elapsed = time.time() - start_time
    return blocks, elapsed

def fetch_blocks_batch(start_block, count):
    """Fetch blocks using JSON-RPC batch request."""
    batch_payload = []

    for i in range(count):
        block_num = start_block + i
        batch_payload.append({
            "jsonrpc": "2.0",
            "method": "eth_getBlockByNumber",
            "params": [hex(block_num), False],
            "id": i
        })

    start_time = time.time()

    try:
        response = requests.post(LLAMARPC_URL, json=batch_payload, timeout=30)
        response.raise_for_status()
        results = response.json()

        blocks = []
        for result in results:
            if "result" in result and result["result"]:
                blocks.append(result["result"])

        elapsed = time.time() - start_time
        return blocks, elapsed

    except Exception as e:
        print(f"Batch request error: {e}")
        return [], 0

# Test different batch sizes
print("Testing JSON-RPC Batch Requests")
print("=" * 80)

test_cases = [
    (10, "Small batch"),
    (50, "Medium batch"),
    (100, "Large batch"),
    (500, "Extra large batch"),
]

start_block = 21540000  # Recent blocks for consistent timing

print(f"\nStarting from block {start_block:,}\n")

for batch_size, label in test_cases:
    print(f"{label} ({batch_size} blocks):")

    # Sequential fetching
    blocks_seq, time_seq = fetch_blocks_sequential(start_block, batch_size)
    rate_seq = batch_size / time_seq if time_seq > 0 else 0

    print(f"  Sequential: {time_seq:.2f}s ({rate_seq:.1f} blocks/sec)")

    # Batch fetching
    time.sleep(0.5)  # Brief pause between tests
    blocks_batch, time_batch = fetch_blocks_batch(start_block, batch_size)
    rate_batch = batch_size / time_batch if time_batch > 0 else 0

    print(f"  Batch:      {time_batch:.2f}s ({rate_batch:.1f} blocks/sec)")

    if time_seq > 0 and time_batch > 0:
        speedup = time_seq / time_batch
        print(f"  Speedup:    {speedup:.1f}x faster")
    print()

print("=" * 80)

# Test very large batch to find limits
print("\nTesting batch size limits...")
large_batch_sizes = [1000, 2000, 5000]

for size in large_batch_sizes:
    print(f"\nBatch size: {size}")
    blocks, elapsed = fetch_blocks_batch(start_block, size)

    if elapsed > 0:
        rate = len(blocks) / elapsed
        print(f"  Success: {len(blocks)} blocks in {elapsed:.2f}s ({rate:.1f} blocks/sec)")
    else:
        print(f"  Failed")
