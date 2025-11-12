#!/usr/bin/env python3
"""
Simple example: Fetching historical Ethereum block data using web3.py with LlamaRPC.
"""
# /// script
# dependencies = ["web3>=7.0.0"]
# ///

from web3 import Web3
from datetime import datetime

# LlamaRPC endpoint (free Ethereum mainnet RPC)
LLAMARPC_ENDPOINT = "https://eth.llamarpc.com"

def main():
    """Demonstrate historical data collection."""
    w3 = Web3(Web3.HTTPProvider(LLAMARPC_ENDPOINT))

    print(f"Connecting to {LLAMARPC_ENDPOINT}...")

    # Get latest block number
    latest_block = w3.eth.block_number
    print(f"✓ Latest block: {latest_block}")

    # Fetch 10 historical blocks
    print("\nFetching historical blocks...")
    start_block = 15000000

    for block_num in range(start_block, start_block + 10):
        block = w3.eth.get_block(block_num)
        timestamp = datetime.fromtimestamp(block['timestamp'])
        tx_count = len(block['transactions'])
        gas_used = block['gasUsed']
        gas_limit = block['gasLimit']
        gas_utilization = (gas_used / gas_limit) * 100

        print(f"Block {block_num}: {timestamp} | {tx_count} txs | Gas: {gas_utilization:.1f}%")

    print("\n✓ Historical data collection complete!")

if __name__ == "__main__":
    main()
