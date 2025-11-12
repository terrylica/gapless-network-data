#!/usr/bin/env python3
"""Test web3.py with LlamaRPC endpoint."""
# /// script
# dependencies = ["web3>=7.0.0"]
# ///

from web3 import Web3

# LlamaRPC endpoint (free Ethereum mainnet RPC)
LLAMARPC_ENDPOINT = "https://eth.llamarpc.com"

def test_basic_connection():
    """Test basic RPC connection."""
    print(f"Testing connection to {LLAMARPC_ENDPOINT}...")

    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(LLAMARPC_ENDPOINT))

    # Test connection
    if w3.is_connected():
        print("✓ Connection successful!")
    else:
        print("✗ Connection failed!")
        return False

    # Get latest block number
    latest_block = w3.eth.block_number
    print(f"✓ Latest block: {latest_block}")

    # Get chain ID
    chain_id = w3.eth.chain_id
    print(f"✓ Chain ID: {chain_id} (1 = Ethereum mainnet)")

    # Get client version
    client_version = w3.client_version
    print(f"✓ Client version: {client_version}")

    return True

def test_historical_block():
    """Test fetching historical block data."""
    print("\nTesting historical block fetching...")

    w3 = Web3(Web3.HTTPProvider(LLAMARPC_ENDPOINT))

    # Fetch a historical block (block 15000000)
    block_number = 15000000
    block = w3.eth.get_block(block_number)

    print(f"✓ Block {block_number}:")
    print(f"  Hash: {block['hash'].hex()}")
    print(f"  Timestamp: {block['timestamp']}")
    print(f"  Transactions: {len(block['transactions'])}")
    print(f"  Gas used: {block['gasUsed']}")

    return True

def test_transaction_data():
    """Test fetching transaction data."""
    print("\nTesting transaction fetching...")

    w3 = Web3(Web3.HTTPProvider(LLAMARPC_ENDPOINT))

    # Get a block with transactions
    block = w3.eth.get_block(15000000, full_transactions=True)

    if block['transactions']:
        tx = block['transactions'][0]
        print(f"✓ Transaction sample:")
        print(f"  Hash: {tx['hash'].hex()}")
        print(f"  From: {tx['from']}")
        print(f"  To: {tx.get('to', 'Contract creation')}")
        print(f"  Value: {Web3.from_wei(tx['value'], 'ether')} ETH")
        print(f"  Gas price: {Web3.from_wei(tx['gasPrice'], 'gwei')} Gwei")

    return True

if __name__ == "__main__":
    try:
        test_basic_connection()
        test_historical_block()
        test_transaction_data()
        print("\n✓ All web3.py tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
