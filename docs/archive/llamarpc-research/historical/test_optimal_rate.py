#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

"""Find optimal batch size and rate limiting for LlamaRPC."""

import requests
import json
import time

LLAMARPC_URL = "https://eth.llamarpc.com"

def fetch_blocks_batch_with_delay(start_block, count, delay=0):
    """Fetch blocks using JSON-RPC batch request with optional delay."""
    batch_payload = []

    for i in range(count):
        block_num = start_block + i
        batch_payload.append({
            "jsonrpc": "2.0",
            "method": "eth_getBlockByNumber",
            "params": [hex(block_num), False],
            "id": i
        })

    if delay > 0:
        time.sleep(delay)

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
        return blocks, elapsed, None

    except Exception as e:
        elapsed = time.time() - start_time
        return [], elapsed, str(e)

print("Finding Optimal Rate Limiting Strategy for LlamaRPC")
print("=" * 80)

# Test small batch sizes (should work)
start_block = 21540000

print("\nPhase 1: Testing small batch sizes (no delay)")
print("-" * 80)

for batch_size in [5, 10, 20]:
    blocks, elapsed, error = fetch_blocks_batch_with_delay(start_block, batch_size)

    if error:
        print(f"Batch size {batch_size}: FAILED - {error}")
    else:
        rate = len(blocks) / elapsed if elapsed > 0 else 0
        print(f"Batch size {batch_size}: {len(blocks)} blocks in {elapsed:.2f}s ({rate:.1f} blocks/sec)")

    time.sleep(1)  # Brief pause between tests

# Test with delays
print("\nPhase 2: Testing batch size 20 with varying delays")
print("-" * 80)

for delay in [0.5, 1.0, 2.0]:
    blocks, elapsed, error = fetch_blocks_batch_with_delay(start_block, 20, delay)

    if error:
        print(f"Delay {delay}s: FAILED - {error}")
    else:
        rate = len(blocks) / (elapsed + delay) if (elapsed + delay) > 0 else 0
        print(f"Delay {delay}s: {len(blocks)} blocks in {elapsed:.2f}s (total: {elapsed + delay:.2f}s, {rate:.1f} blocks/sec)")

    time.sleep(1)

# Test sustained fetching with optimal strategy
print("\nPhase 3: Sustained fetching test (20 blocks x 10 batches with 1s delay)")
print("-" * 80)

total_blocks = 0
total_time = 0
errors = 0

for i in range(10):
    blocks, elapsed, error = fetch_blocks_batch_with_delay(start_block + (i * 20), 20, 1.0)

    if error:
        print(f"Batch {i+1}: FAILED - {error}")
        errors += 1
    else:
        total_blocks += len(blocks)
        total_time += elapsed + 1.0
        print(f"Batch {i+1}: {len(blocks)} blocks in {elapsed:.2f}s")

    time.sleep(1)

if total_time > 0:
    overall_rate = total_blocks / total_time
    print(f"\nSummary: {total_blocks} blocks in {total_time:.2f}s ({overall_rate:.2f} blocks/sec, {errors} errors)")

print("\n" + "=" * 80)
print("\nRecommendations:")
print("- Batch size: 10-20 blocks per request")
print("- Delay: 1-2 seconds between batches")
print("- Expected rate: 10-20 blocks/sec")
print("- Avoid: Batch sizes > 50 (400 Bad Request)")
print("- Avoid: Rapid sequential requests (429 Too Many Requests)")
