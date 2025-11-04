#!/usr/bin/env python3
"""
Test LlamaRPC for fetching Ethereum M1 gas price data
Block 14000000 = Jan 13, 2022
"""
import requests
from datetime import datetime
import json

RPC_URL = "https://eth.llamarpc.com"

def rpc_call(method: str, params: list) -> dict:
    """Make JSON-RPC call"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    response = requests.post(RPC_URL, json=payload)
    return response.json()

# Test 1: Get latest block number
print("=" * 80)
print("TEST 1: Get Latest Block Number")
print("=" * 80)
result = rpc_call("eth_blockNumber", [])
latest_block = int(result["result"], 16)
print(f"Latest block: {latest_block:,}")
print()

# Test 2: Get historical block (Jan 13, 2022)
print("=" * 80)
print("TEST 2: Get Historical Block 14000000 (Jan 13, 2022)")
print("=" * 80)
result = rpc_call("eth_getBlockByNumber", ["0xD59F80", False])
block = result["result"]

# Parse block data
block_number = int(block["number"], 16)
timestamp = int(block["timestamp"], 16)
gas_used = int(block["gasUsed"], 16)
gas_limit = int(block["gasLimit"], 16)
base_fee = int(block["baseFeePerGas"], 16)

dt = datetime.fromtimestamp(timestamp)
base_fee_gwei = base_fee / 1e9
utilization = gas_used / gas_limit

print(f"Block Number: {block_number:,}")
print(f"Timestamp: {dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")
print(f"Base Fee: {base_fee_gwei:.2f} Gwei")
print(f"Gas Used: {gas_used:,} ({utilization:.1%} utilization)")
print(f"Gas Limit: {gas_limit:,}")
print()

# Test 3: Get fee history (last 10 blocks)
print("=" * 80)
print("TEST 3: Get Fee History (Last 10 Blocks)")
print("=" * 80)
result = rpc_call("eth_feeHistory", ["0xa", "latest", [25, 50, 75]])
fee_history = result["result"]

oldest_block = int(fee_history["oldestBlock"], 16)
base_fees = [int(fee, 16) / 1e9 for fee in fee_history["baseFeePerGas"]]
gas_used_ratios = fee_history["gasUsedRatio"]

print(f"Oldest Block: {oldest_block:,}")
print(f"\nBase Fees (Gwei):")
for i, fee in enumerate(base_fees):
    ratio = gas_used_ratios[i] if i < len(gas_used_ratios) else None
    if ratio is not None:
        print(f"  Block {oldest_block + i}: {fee:.2f} Gwei (utilization: {ratio:.1%})")
    else:
        print(f"  Next block prediction: {fee:.2f} Gwei")
print()

# Test 4: Fetch 5 consecutive blocks for M1 aggregation demo
print("=" * 80)
print("TEST 4: Fetch 5 Consecutive Blocks (M1 Aggregation Demo)")
print("=" * 80)
blocks = []
start_block = 14000000

for i in range(5):
    block_num = start_block + i
    result = rpc_call("eth_getBlockByNumber", [hex(block_num), False])
    block = result["result"]

    blocks.append({
        "number": int(block["number"], 16),
        "timestamp": int(block["timestamp"], 16),
        "baseFeePerGas": int(block["baseFeePerGas"], 16) / 1e9,
        "gasUsed": int(block["gasUsed"], 16),
        "gasLimit": int(block["gasLimit"], 16)
    })

print(f"Fetched {len(blocks)} blocks\n")

# Calculate OHLC for this ~1-minute interval
base_fees = [b["baseFeePerGas"] for b in blocks]
total_gas_used = sum(b["gasUsed"] for b in blocks)
avg_gas_limit = sum(b["gasLimit"] for b in blocks) / len(blocks)

print("M1 Aggregation Results:")
print(f"  Open:  {base_fees[0]:.2f} Gwei")
print(f"  High:  {max(base_fees):.2f} Gwei")
print(f"  Low:   {min(base_fees):.2f} Gwei")
print(f"  Close: {base_fees[-1]:.2f} Gwei")
print(f"  Total Gas Used: {total_gas_used:,}")
print(f"  Avg Utilization: {total_gas_used / (avg_gas_limit * len(blocks)):.1%}")
print()

# Time span
start_time = datetime.fromtimestamp(blocks[0]["timestamp"])
end_time = datetime.fromtimestamp(blocks[-1]["timestamp"])
duration = (end_time - start_time).total_seconds()
print(f"Time Span: {duration:.0f} seconds ({duration/60:.2f} minutes)")
print(f"Average Block Time: {duration / (len(blocks) - 1):.1f} seconds")
print()

print("=" * 80)
print("✅ All tests completed successfully!")
print("=" * 80)
print("\nNEXT STEPS:")
print("1. Use pandas to aggregate blocks to M1/M5/M15 intervals")
print("2. Save to Parquet format for efficient storage")
print("3. Implement rate limiting and retry logic for production")
print("4. Consider using Alchemy/Infura for more reliable production access")
