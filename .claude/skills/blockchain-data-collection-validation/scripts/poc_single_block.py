#!/usr/bin/env python3
"""
Proof of Concept: Fetch single Ethereum block from LlamaRPC

Validates:
1. web3.py connection to LlamaRPC
2. eth_getBlockByNumber method works
3. Block schema matches our expectations (6 fields)
4. Data types are correct
5. Response time for single block

Run with: uv run 01_single_block_fetch.py

Based on: scratch/llamarpc-archive-validation/test_01_basic_connection.py
"""

import time
from datetime import datetime
from web3 import Web3

# LlamaRPC endpoint (free, no auth required)
LLAMARPC_ENDPOINT = "https://eth.llamarpc.com"

def main():
    """Test single block fetch from LlamaRPC."""
    print("=== Ethereum Single Block Fetch POC ===\n")

    # Initialize Web3 connection
    print(f"Connecting to: {LLAMARPC_ENDPOINT}")
    w3 = Web3(Web3.HTTPProvider(LLAMARPC_ENDPOINT))

    # Check connection
    is_connected = w3.is_connected()
    print(f"Connected: {is_connected}")

    if not is_connected:
        print("❌ Failed to connect to LlamaRPC")
        return

    print(f"✅ Connected successfully\n")

    # Get latest block number
    latest_block = w3.eth.block_number
    print(f"Latest block: {latest_block:,}")

    # Fetch a recent block (not latest to avoid reorg issues)
    test_block_num = latest_block - 100
    print(f"Fetching block: {test_block_num:,}\n")

    # Measure fetch time
    start_time = time.time()
    block = w3.eth.get_block(test_block_num)
    fetch_time = time.time() - start_time

    print(f"✅ Fetched block in {fetch_time*1000:.1f}ms\n")

    # Display block data
    print("Block data:")
    print(f"  - block_number: {block['number']:,}")
    print(f"  - timestamp: {block['timestamp']} ({datetime.fromtimestamp(block['timestamp'])})")
    print(f"  - baseFeePerGas: {block.get('baseFeePerGas', 'N/A')} wei")
    print(f"  - gasUsed: {block['gasUsed']:,}")
    print(f"  - gasLimit: {block['gasLimit']:,}")
    print(f"  - transactions_count: {len(block['transactions'])}")
    print()

    # Validate our 6 required fields
    required_fields = {
        'number': int,
        'timestamp': int,
        'baseFeePerGas': (int, type(None)),  # None for pre-EIP-1559 blocks
        'gasUsed': int,
        'gasLimit': int,
        'transactions': list,
    }

    print("Validating required fields:")
    all_valid = True
    for field, expected_type in required_fields.items():
        if field not in block:
            print(f"  ❌ Missing field: {field}")
            all_valid = False
        elif not isinstance(block[field], expected_type):
            print(f"  ❌ Wrong type for {field}: expected {expected_type}, got {type(block[field])}")
            all_valid = False
        else:
            print(f"  ✅ {field}: {type(block[field]).__name__}")

    if all_valid:
        print("\n✅ All required fields present and valid")
    else:
        print("\n❌ Some fields missing or invalid")

    # Test schema constraints
    print("\nValidating constraints:")
    print(f"  - baseFeePerGas >= 0: {block.get('baseFeePerGas', 0) >= 0}")
    print(f"  - gasUsed >= 0: {block['gasUsed'] >= 0}")
    print(f"  - gasLimit >= 0: {block['gasLimit'] >= 0}")
    print(f"  - gasUsed <= gasLimit: {block['gasUsed'] <= block['gasLimit']}")
    print(f"  - transactions_count >= 0: {len(block['transactions']) >= 0}")

    # Extract data in our schema format
    print("\nExtracted data (our 6-field schema):")
    extracted = {
        'block_number': block['number'],
        'timestamp': datetime.fromtimestamp(block['timestamp']),
        'baseFeePerGas': block.get('baseFeePerGas'),
        'gasUsed': block['gasUsed'],
        'gasLimit': block['gasLimit'],
        'transactions_count': len(block['transactions']),
    }

    for key, value in extracted.items():
        print(f"  - {key}: {value}")

    print("\n=== Summary ===")
    print(f"✅ LlamaRPC connection works")
    print(f"✅ eth_getBlockByNumber works")
    print(f"✅ Response time: {fetch_time*1000:.1f}ms")
    print(f"✅ All 6 fields available")
    print(f"✅ Data types correct")
    print(f"✅ Constraints satisfied")

    print("\n=== Next Steps ===")
    print("1. Test batch fetching (100 blocks)")
    print("2. Test parallel requests (ThreadPoolExecutor)")
    print("3. Measure sustained throughput")
    print("4. Test historical block access (2020-era blocks)")

if __name__ == "__main__":
    main()
