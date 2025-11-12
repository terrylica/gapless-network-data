#!/usr/bin/env python3
"""
Simple Ethereum Metrics Calculator (No external dependencies)
Uses only Python standard library
"""

import json
import urllib.request
from datetime import datetime, timezone


def rpc_call(method, params):
    """Make JSON-RPC call using urllib"""
    url = "https://eth.llamarpc.com"
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        return data["result"]


def main():
    print("=== Ethereum Network Metrics Demo ===\n")

    # Get latest block
    print("Fetching latest block...")
    block = rpc_call("eth_getBlockByNumber", ["latest", False])

    block_num = int(block["number"], 16)
    timestamp = int(block["timestamp"], 16)
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)

    print(f"\n📦 Block #{block_num:,}")
    print(f"   Timestamp: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"   Hash: {block['hash']}")

    # Gas metrics
    gas_limit = int(block["gasLimit"], 16)
    gas_used = int(block["gasUsed"], 16)
    base_fee_gwei = int(block["baseFeePerGas"], 16) / 1e9

    print(f"\n⛽ Gas Metrics:")
    print(f"   Utilization: {(gas_used/gas_limit)*100:.2f}%")
    print(f"   Base Fee: {base_fee_gwei:.3f} gwei")
    print(f"   Gas Used: {gas_used:,} / {gas_limit:,}")

    # Transaction metrics
    tx_count = len(block["transactions"])
    block_size_kb = int(block["size"], 16) / 1024

    print(f"\n📝 Transactions:")
    print(f"   Count: {tx_count}")
    print(f"   Avg Gas/Tx: {gas_used/tx_count:,.0f}")
    print(f"   Block Size: {block_size_kb:.2f} KB")

    # Blob metrics (EIP-4844)
    blob_gas_used = int(block.get("blobGasUsed", "0x0"), 16)
    max_blob_gas = 6 * 131072
    blob_utilization = (blob_gas_used / max_blob_gas) * 100 if max_blob_gas > 0 else 0

    print(f"\n🫧 Blob Data (EIP-4844):")
    print(f"   Utilization: {blob_utilization:.2f}%")
    print(f"   Blobs: ~{blob_gas_used // 131072}")

    # Withdrawals
    withdrawals = block.get("withdrawals", [])
    withdrawal_count = len(withdrawals)
    total_gwei = sum(int(w["amount"], 16) for w in withdrawals)
    total_eth = total_gwei / 1e9

    print(f"\n💰 Withdrawals:")
    print(f"   Count: {withdrawal_count}")
    print(f"   Total: {total_eth:.6f} ETH")

    # Builder info
    extra_hex = block["extraData"][2:]
    try:
        builder_tag = bytes.fromhex(extra_hex).decode('utf-8', errors='ignore').strip()
    except:
        builder_tag = ""

    print(f"\n🏗️  Builder:")
    print(f"   Address: {block['miner']}")
    print(f"   Tag: {builder_tag}")

    # Fee history
    print("\n\nFetching fee market data...")
    fee_history = rpc_call("eth_feeHistory", ["0x14", "latest", [25, 50, 75]])

    base_fees = [int(f, 16) / 1e9 for f in fee_history["baseFeePerGas"]]
    current_base = base_fees[-1]
    oldest_base = base_fees[0]
    change_pct = ((current_base - oldest_base) / oldest_base) * 100

    print(f"\n📈 Base Fee Trends (20 blocks):")
    print(f"   Current: {current_base:.3f} gwei")
    print(f"   Range: {min(base_fees):.3f} - {max(base_fees):.3f} gwei")
    print(f"   Change: {change_pct:+.2f}%")

    # Priority fees from latest block
    latest_rewards = fee_history["reward"][-1]
    p25 = int(latest_rewards[0], 16) / 1e9
    p50 = int(latest_rewards[1], 16) / 1e9
    p75 = int(latest_rewards[2], 16) / 1e9

    print(f"\n💎 Priority Fees (Latest Block):")
    print(f"   25th percentile: {p25:.3f} gwei")
    print(f"   50th percentile: {p50:.3f} gwei")
    print(f"   75th percentile: {p75:.3f} gwei")

    # Congestion
    gas_ratios = fee_history["gasUsedRatio"]
    avg_utilization = sum(gas_ratios) / len(gas_ratios)

    if avg_utilization < 0.5:
        level = "LOW"
    elif avg_utilization < 0.8:
        level = "MODERATE"
    else:
        level = "HIGH"

    print(f"\n🚦 Network Congestion:")
    print(f"   Level: {level}")
    print(f"   Avg Utilization: {avg_utilization*100:.2f}%")

    # Recommended gas prices
    print(f"\n⚡ Recommended Gas Prices:")
    print(f"   🐢 Slow:     {current_base + p25:.3f} gwei")
    print(f"   🚶 Standard: {current_base + p50:.3f} gwei")
    print(f"   🚀 Fast:     {current_base + p75:.3f} gwei")

    print("\n✅ Demo completed!")


if __name__ == "__main__":
    main()
