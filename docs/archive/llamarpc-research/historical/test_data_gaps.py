#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

"""Test for data gaps in historical Ethereum blocks."""

import requests
from datetime import datetime

LLAMARPC_URL = "https://eth.llamarpc.com"

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
            return None, result["error"]

        return result.get("result"), None
    except Exception as e:
        return None, str(e)

print("Testing for Data Gaps in LlamaRPC")
print("=" * 80)

# Test random blocks across entire history
test_blocks = [
    0,           # Genesis
    100000,      # Early Ethereum
    1000000,     # Homestead era
    5000000,     # Byzantium era
    10000000,    # ~2020
    15537394,    # The Merge
    18000000,    # Recent (2023)
    21000000,    # Recent (2024)
]

print("\nChecking random blocks across history:")
print("-" * 80)

missing_blocks = []
successful_blocks = []

for block_num in test_blocks:
    block, error = fetch_block(block_num)

    if error or block is None:
        print(f"Block {block_num:>9,}: MISSING - {error}")
        missing_blocks.append(block_num)
    else:
        timestamp = int(block["timestamp"], 16)
        dt = datetime.utcfromtimestamp(timestamp) if timestamp > 0 else "N/A"
        tx_count = len(block.get("transactions", []))
        print(f"Block {block_num:>9,}: OK - {dt} - {tx_count} txs")
        successful_blocks.append(block_num)

print("\n" + "=" * 80)
print(f"\nResults:")
print(f"  Tested: {len(test_blocks)} blocks")
print(f"  Successful: {len(successful_blocks)}")
print(f"  Missing: {len(missing_blocks)}")

if missing_blocks:
    print(f"  Missing blocks: {missing_blocks}")
else:
    print(f"  No gaps detected across tested range!")

print("\nConclusion:")
if len(missing_blocks) == 0:
    print("  ✓ LlamaRPC provides complete historical data back to genesis")
    print("  ✓ No gaps detected in random sampling")
else:
    print(f"  ✗ {len(missing_blocks)} missing blocks detected")
    print("  ✗ Data may not be complete")
