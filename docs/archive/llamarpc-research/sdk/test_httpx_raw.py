#!/usr/bin/env python3
"""Test raw httpx JSON-RPC with LlamaRPC endpoint - minimal dependencies."""
# /// script
# dependencies = ["httpx>=0.27.0"]
# ///

import httpx

# LlamaRPC endpoint (free Ethereum mainnet RPC)
LLAMARPC_ENDPOINT = "https://eth.llamarpc.com"

def rpc_call(method: str, params: list = None) -> dict:
    """Make a JSON-RPC call."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or [],
        "id": 1
    }

    response = httpx.post(LLAMARPC_ENDPOINT, json=payload, timeout=30.0)
    response.raise_for_status()
    result = response.json()

    if "error" in result:
        raise Exception(f"RPC error: {result['error']}")

    return result["result"]

def test_basic_connection():
    """Test basic RPC connection."""
    print(f"Testing raw httpx JSON-RPC with {LLAMARPC_ENDPOINT}...")

    # Get latest block number
    latest_block_hex = rpc_call("eth_blockNumber")
    latest_block = int(latest_block_hex, 16)
    print(f"✓ Latest block: {latest_block}")

    # Get chain ID
    chain_id_hex = rpc_call("eth_chainId")
    chain_id = int(chain_id_hex, 16)
    print(f"✓ Chain ID: {chain_id} (1 = Ethereum mainnet)")

    # Get client version
    client_version = rpc_call("web3_clientVersion")
    print(f"✓ Client version: {client_version}")

    return True

def test_historical_block():
    """Test fetching historical block data."""
    print("\nTesting historical block fetching...")

    # Fetch a historical block
    block_number = 15000000
    block_number_hex = hex(block_number)

    block = rpc_call("eth_getBlockByNumber", [block_number_hex, False])

    print(f"✓ Block {block_number}:")
    print(f"  Hash: {block['hash']}")
    print(f"  Timestamp: {int(block['timestamp'], 16)}")
    print(f"  Transactions: {len(block['transactions'])}")
    print(f"  Gas used: {int(block['gasUsed'], 16)}")

    return True

def test_transaction_data():
    """Test fetching transaction data."""
    print("\nTesting transaction fetching...")

    # Get a block with full transaction details
    block_number = 15000000
    block_number_hex = hex(block_number)

    block = rpc_call("eth_getBlockByNumber", [block_number_hex, True])

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

def test_batch_requests():
    """Test batch JSON-RPC requests."""
    print("\nTesting batch requests...")

    # Batch request for multiple blocks
    batch_payload = [
        {"jsonrpc": "2.0", "method": "eth_getBlockByNumber", "params": [hex(15000000 + i), False], "id": i}
        for i in range(5)
    ]

    response = httpx.post(LLAMARPC_ENDPOINT, json=batch_payload, timeout=30.0)
    response.raise_for_status()
    results = response.json()

    print(f"✓ Fetched {len(results)} blocks in batch:")
    for i, result in enumerate(results):
        if "error" in result:
            print(f"  Block {i}: Error - {result['error']}")
        else:
            block_num = int(result["result"]["number"], 16)
            tx_count = len(result["result"]["transactions"])
            print(f"  Block {block_num}: {tx_count} transactions")

    return True

if __name__ == "__main__":
    try:
        test_basic_connection()
        test_historical_block()
        test_transaction_data()
        test_batch_requests()
        print("\n✓ All raw httpx JSON-RPC tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
