#!/usr/bin/env python3
"""Test pythereum (async) with LlamaRPC endpoint - requires WebSocket support."""
# /// script
# dependencies = ["pythereum>=1.2.0"]
# ///

import asyncio
from pythereum import EthRPC

# Note: LlamaRPC HTTP endpoint, but pythereum requires WebSocket
# This will likely fail as LlamaRPC may not expose WS on same endpoint
LLAMARPC_WS = "wss://eth.llamarpc.com"
LLAMARPC_HTTP = "https://eth.llamarpc.com"

async def test_websocket():
    """Test WebSocket connection (if supported)."""
    print(f"Testing pythereum with WebSocket: {LLAMARPC_WS}...")

    try:
        async with EthRPC(LLAMARPC_WS, pool_size=1) as erpc:
            # Get latest block number
            latest_block = await erpc.get_block_number()
            print(f"✓ Latest block: {latest_block}")

            # Get chain ID
            chain_id = await erpc.chain_id()
            print(f"✓ Chain ID: {chain_id}")

            return True
    except Exception as e:
        print(f"✗ WebSocket test failed: {e}")
        return False

async def test_http_endpoint():
    """Test HTTP endpoint (pythereum may not support this)."""
    print(f"\nTesting pythereum with HTTP: {LLAMARPC_HTTP}...")

    try:
        async with EthRPC(LLAMARPC_HTTP, pool_size=1) as erpc:
            latest_block = await erpc.get_block_number()
            print(f"✓ Latest block: {latest_block}")
            return True
    except Exception as e:
        print(f"✗ HTTP test failed: {e}")
        return False

async def main():
    """Run tests."""
    ws_result = await test_websocket()
    http_result = await test_http_endpoint()

    if ws_result or http_result:
        print("\n✓ At least one pythereum test passed!")
    else:
        print("\n✗ All pythereum tests failed!")
        print("\nNote: pythereum requires WebSocket, LlamaRPC may only support HTTP")

if __name__ == "__main__":
    asyncio.run(main())
