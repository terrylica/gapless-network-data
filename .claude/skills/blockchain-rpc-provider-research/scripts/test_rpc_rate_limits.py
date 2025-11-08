#!/usr/bin/env python3
"""
RPC Rate Limit Testing Template

Template for empirically validating RPC provider rate limits.
Customize RPC_ENDPOINT and test different REQUESTS_PER_SECOND values.

Based on validated pattern from ethereum-collector-poc/05_ultra_conservative.py

Usage:
    1. Set RPC_ENDPOINT (replace YOUR_API_KEY if needed)
    2. Set REQUESTS_PER_SECOND to test
    3. Run: uv run test_rpc_rate_limits.py
    4. Success criteria: 100% success rate, zero 429 errors
    5. If failed: reduce RPS and retry
    6. If passed: try slightly higher RPS to find limit

Example test progression:
    - Test 10 RPS (likely fail) → baseline understanding
    - Test 5 RPS (may work) → find working range
    - Test 2 RPS (should work) → ultra-conservative
    - Actual sustainable: 5.79 RPS (Alchemy case study)
"""

import time
from datetime import datetime
from statistics import mean
from web3 import Web3

# ============================================================================
# CONFIGURATION - CUSTOMIZE THESE VALUES
# ============================================================================

# RPC endpoint to test
RPC_ENDPOINT = "https://eth.llamarpc.com"  # or "https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY"

# Rate limit to test (start high, reduce until 100% success)
REQUESTS_PER_SECOND = 2.0  # Adjust this value

# Number of blocks to test (minimum 50, ideally 100+)
NUM_BLOCKS = 50

# ============================================================================
# IMPLEMENTATION - Usually no changes needed below
# ============================================================================

DELAY_BETWEEN_REQUESTS = 1.0 / REQUESTS_PER_SECOND


def fetch_block(w3: Web3, block_num: int) -> tuple[dict | None, float, bool]:
    """Fetch block with timing and error detection.

    Returns:
        (block_data, fetch_time_ms, rate_limited)
    """
    start_time = time.time()
    try:
        block = w3.eth.get_block(block_num)
        fetch_time = (time.time() - start_time) * 1000

        # Extract 6-field schema (adjust for your needs)
        block_data = {
            'block_number': block['number'],
            'timestamp': datetime.fromtimestamp(block['timestamp']),
            'baseFeePerGas': block.get('baseFeePerGas'),
            'gasUsed': block['gasUsed'],
            'gasLimit': block['gasLimit'],
            'transactions_count': len(block['transactions']),
        }
        return (block_data, fetch_time, False)
    except Exception as e:
        fetch_time = (time.time() - start_time) * 1000
        rate_limited = "429" in str(e)
        return (None, fetch_time, rate_limited)


def test_rate_limits():
    """Run rate limit test."""
    print("=" * 70)
    print("RPC Rate Limit Testing")
    print("=" * 70)
    print(f"\nEndpoint: {RPC_ENDPOINT}")
    print(f"Target: {REQUESTS_PER_SECOND} RPS "
          f"({REQUESTS_PER_SECOND / 50 * 100:.0f}% of 50 RPS max)")
    print(f"Delay: {DELAY_BETWEEN_REQUESTS * 1000:.0f}ms between requests")
    print(f"Test size: {NUM_BLOCKS} blocks\n")

    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))
    latest_block = w3.eth.block_number
    start_block = latest_block - NUM_BLOCKS - 100  # Offset to avoid reorgs

    print(f"Fetching {NUM_BLOCKS} blocks from {start_block:,}...\n")

    blocks = []
    fetch_times = []
    rate_limited_count = 0

    start_time = time.time()

    for i in range(NUM_BLOCKS):
        block_num = start_block + i

        block_data, fetch_time, rate_limited = fetch_block(w3, block_num)
        fetch_times.append(fetch_time)

        if rate_limited:
            rate_limited_count += 1
            print(f"  ⚠️  RATE LIMITED at block {block_num}")
        elif block_data:
            blocks.append(block_data)

        # Progress indicator every 10 blocks
        if (i + 1) % 10 == 0:
            elapsed = time.time() - start_time
            actual_rps = (i + 1) / elapsed
            print(f"  Progress: {i+1}/{NUM_BLOCKS} | "
                  f"Rate: {actual_rps:.2f} RPS | "
                  f"Fetch: {mean(fetch_times[-10:]):.0f}ms | "
                  f"Errors: {rate_limited_count}")

        # Rate limiting delay
        time.sleep(DELAY_BETWEEN_REQUESTS)

    total_time = time.time() - start_time

    # Results
    print(f"\n{'=' * 70}")
    print("Results:")
    print(f"{'=' * 70}")
    print(f"  Successful: {len(blocks)}/{NUM_BLOCKS} "
          f"({len(blocks) / NUM_BLOCKS * 100:.0f}%)")
    print(f"  Rate limited: {rate_limited_count}")
    print(f"  Actual rate: {NUM_BLOCKS / total_time:.2f} RPS")
    print(f"  Total time: {total_time:.1f}s")

    # Success criteria
    success_rate = len(blocks) / NUM_BLOCKS
    no_rate_limiting = rate_limited_count == 0

    print(f"\n{'=' * 70}")
    print("Verdict:")
    print(f"{'=' * 70}")

    if success_rate >= 0.99 and no_rate_limiting:
        print(f"✅ PASS: {REQUESTS_PER_SECOND} RPS is sustainable")
        print(f"   - Success rate: {success_rate * 100:.1f}%")
        print(f"   - Zero rate limiting errors")
        print(f"   - Actual throughput: {NUM_BLOCKS / total_time:.2f} RPS")

        # Timeline projection
        print(f"\nTimeline projection (13M blocks at {NUM_BLOCKS / total_time:.2f} RPS):")
        seconds = 13_000_000 / (NUM_BLOCKS / total_time)
        print(f"  - {seconds / 86400:.1f} days")
        print(f"  - {seconds / 3600:.0f} hours")
    else:
        print(f"❌ FAIL: Rate limiting detected")
        if rate_limited_count > 0:
            print(f"   - {rate_limited_count} rate limit errors (429)")
        if success_rate < 0.99:
            print(f"   - Success rate: {success_rate * 100:.1f}% (below 99%)")
        print(f"\nRecommendation: Reduce to {REQUESTS_PER_SECOND / 2:.1f} RPS and retry")

    print("=" * 70)

    return {
        "rps_target": REQUESTS_PER_SECOND,
        "rps_actual": NUM_BLOCKS / total_time,
        "success_rate": success_rate,
        "rate_limited": rate_limited_count,
        "passed": success_rate >= 0.99 and no_rate_limiting,
    }


if __name__ == "__main__":
    result = test_rate_limits()

    # Exit code for automation
    exit(0 if result["passed"] else 1)
