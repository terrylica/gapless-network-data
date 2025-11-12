#!/usr/bin/env python3
# /// script
# dependencies = ["requests"]
# ///

"""Test fetching Ethereum blocks from different time periods."""

import requests
import json
from datetime import datetime

LLAMARPC_URL = "https://eth.llamarpc.com"

def fetch_block(block_number):
    """Fetch a block by number."""
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": [hex(block_number), False],  # False = don't fetch full tx objects
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

def analyze_block(block, label):
    """Analyze and print block information."""
    if block is None:
        print(f"\n{label}: FAILED")
        return

    block_num = int(block["number"], 16)
    timestamp = int(block["timestamp"], 16)
    dt = datetime.utcfromtimestamp(timestamp)
    tx_count = len(block.get("transactions", []))

    print(f"\n{label}:")
    print(f"  Block Number: {block_num:,}")
    print(f"  Timestamp: {timestamp} ({dt.isoformat()}Z)")
    print(f"  Hash: {block['hash']}")
    print(f"  Transactions: {tx_count}")
    print(f"  Gas Used: {int(block['gasUsed'], 16):,}")

# Test blocks at different time periods
test_blocks = [
    (21548000, "Recent block (~Nov 2024)"),
    (18500000, "~1 year ago (Oct 2023)"),
    (15537394, "The Merge (Sep 15, 2022)"),
    (12965000, "~3 years ago (May 2021)"),
    (10000000, "~5 years ago (Jun 2020)"),
    (7280000, "Byzantium fork (Oct 2018)"),
    (4370000, "Homestead (Mar 2017)"),
    (1, "Block 1 (near genesis)"),
    (0, "Genesis block"),
]

print("Testing LlamaRPC Historical Data Access")
print("=" * 60)

for block_num, label in test_blocks:
    block, error = fetch_block(block_num)

    if error:
        print(f"\n{label}:")
        print(f"  Block Number: {block_num:,}")
        print(f"  ERROR: {error}")
    else:
        analyze_block(block, label)

print("\n" + "=" * 60)
print("Test Complete")
