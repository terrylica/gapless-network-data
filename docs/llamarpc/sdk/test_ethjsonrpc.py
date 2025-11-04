#!/usr/bin/env python3
"""Test ethjsonrpc with LlamaRPC endpoint."""
# /// script
# dependencies = ["ethjsonrpc>=0.3.0"]
# ///

from ethjsonrpc import EthJsonRpc

# LlamaRPC endpoint (free Ethereum mainnet RPC)
LLAMARPC_ENDPOINT = "eth.llamarpc.com"

def test_basic_connection():
    """Test basic RPC connection."""
    print(f"Testing ethjsonrpc with {LLAMARPC_ENDPOINT}...")

    # Initialize client (note: ethjsonrpc expects host without https://)
    eth = EthJsonRpc(LLAMARPC_ENDPOINT, 443, tls=True)

    # Get latest block number
    latest_block = eth.eth_blockNumber()
    print(f"✓ Latest block: {latest_block}")

    # Get client version
    try:
        client_version = eth.web3_clientVersion()
        print(f"✓ Client version: {client_version}")
    except Exception as e:
        print(f"  Note: client version not available: {e}")

    return True

def test_historical_block():
    """Test fetching historical block data."""
    print("\nTesting historical block fetching...")

    eth = EthJsonRpc(LLAMARPC_ENDPOINT, 443, tls=True)

    # Fetch a historical block
    block_number = 15000000
    block = eth.eth_getBlockByNumber(block_number)

    print(f"✓ Block {block_number}:")
    print(f"  Hash: {block['hash']}")
    print(f"  Timestamp: {int(block['timestamp'], 16)}")
    print(f"  Transactions: {len(block['transactions'])}")
    print(f"  Gas used: {int(block['gasUsed'], 16)}")

    return True

def test_transaction_data():
    """Test fetching transaction data."""
    print("\nTesting transaction fetching...")

    eth = EthJsonRpc(LLAMARPC_ENDPOINT, 443, tls=True)

    # Get a block with full transaction details
    block = eth.eth_getBlockByNumber(15000000, tx_objects=True)

    if block['transactions']:
        tx = block['transactions'][0]
        print(f"✓ Transaction sample:")
        print(f"  Hash: {tx['hash']}")
        print(f"  From: {tx['from']}")
        print(f"  To: {tx.get('to', 'Contract creation')}")
        value_eth = int(tx['value'], 16) / 1e18
        gas_gwei = int(tx['gasPrice'], 16) / 1e9
        print(f"  Value: {value_eth} ETH")
        print(f"  Gas price: {gas_gwei} Gwei")

    return True

if __name__ == "__main__":
    try:
        test_basic_connection()
        test_historical_block()
        test_transaction_data()
        print("\n✓ All ethjsonrpc tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
