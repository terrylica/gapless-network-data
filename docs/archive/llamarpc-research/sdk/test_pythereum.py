#!/usr/bin/env python3
"""Test pythereum with LlamaRPC endpoint."""
# /// script
# dependencies = ["pythereum>=0.1.0"]
# ///

from pythereum import Ethereum

# LlamaRPC endpoint (free Ethereum mainnet RPC)
LLAMARPC_ENDPOINT = "https://eth.llamarpc.com"

def test_basic_connection():
    """Test basic RPC connection."""
    print(f"Testing pythereum with {LLAMARPC_ENDPOINT}...")

    # Initialize Ethereum client
    eth = Ethereum(LLAMARPC_ENDPOINT)

    # Get latest block number
    latest_block = eth.get_block_number()
    print(f"✓ Latest block: {latest_block}")

    # Get chain ID
    chain_id = eth.chain_id()
    print(f"✓ Chain ID: {chain_id}")

    return True

def test_historical_block():
    """Test fetching historical block data."""
    print("\nTesting historical block fetching...")

    eth = Ethereum(LLAMARPC_ENDPOINT)

    # Fetch a historical block
    block_number = 15000000
    block = eth.get_block_by_number(block_number)

    print(f"✓ Block {block_number}:")
    print(f"  Hash: {block['hash']}")
    print(f"  Timestamp: {block['timestamp']}")
    print(f"  Transactions: {len(block['transactions'])}")
    print(f"  Gas used: {block['gasUsed']}")

    return True

def test_transaction_data():
    """Test fetching transaction data."""
    print("\nTesting transaction fetching...")

    eth = Ethereum(LLAMARPC_ENDPOINT)

    # Get a block with full transaction details
    block = eth.get_block_by_number(15000000, full_transactions=True)

    if block['transactions']:
        tx = block['transactions'][0]
        print(f"✓ Transaction sample:")
        print(f"  Hash: {tx['hash']}")
        print(f"  From: {tx['from']}")
        print(f"  To: {tx.get('to', 'Contract creation')}")
        print(f"  Value: {int(tx['value'], 16) / 1e18} ETH")
        print(f"  Gas price: {int(tx['gasPrice'], 16) / 1e9} Gwei")

    return True

if __name__ == "__main__":
    try:
        test_basic_connection()
        test_historical_block()
        test_transaction_data()
        print("\n✓ All pythereum tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
