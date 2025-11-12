#!/bin/bash
# Curl-based examples for LlamaRPC Ethereum data fetching

LLAMARPC_URL="https://eth.llamarpc.com"

echo "LlamaRPC Curl Examples"
echo "======================================================================"

# Example 1: Get latest block number
echo -e "\n1. Get latest block number:"
echo "   Command: eth_blockNumber"
curl -s -X POST $LLAMARPC_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "eth_blockNumber",
    "params": [],
    "id": 1
  }' | jq -r '.result' | xargs printf "   Latest block: %d\n"

sleep 1

# Example 2: Get specific block
echo -e "\n2. Get block 21,540,000 (without full transactions):"
echo "   Command: eth_getBlockByNumber"
curl -s -X POST $LLAMARPC_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "eth_getBlockByNumber",
    "params": ["0x148a1e0", false],
    "id": 1
  }' | jq '{
    number: .result.number,
    timestamp: .result.timestamp,
    hash: .result.hash,
    transactions: (.result.transactions | length),
    gasUsed: .result.gasUsed
  }'

sleep 1

# Example 3: Get genesis block
echo -e "\n3. Get genesis block (block 0):"
curl -s -X POST $LLAMARPC_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "eth_getBlockByNumber",
    "params": ["0x0", false],
    "id": 1
  }' | jq '{
    number: .result.number,
    timestamp: .result.timestamp,
    hash: .result.hash
  }'

sleep 1

# Example 4: Batch request (10 blocks)
echo -e "\n4. Batch request for blocks 21,540,000 to 21,540,009:"
echo "   Command: JSON-RPC batch (10 requests in one HTTP call)"
curl -s -X POST $LLAMARPC_URL \
  -H "Content-Type: application/json" \
  -d '[
    {"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x148a1e0",false],"id":0},
    {"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x148a1e1",false],"id":1},
    {"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x148a1e2",false],"id":2},
    {"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x148a1e3",false],"id":3},
    {"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x148a1e4",false],"id":4},
    {"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x148a1e5",false],"id":5},
    {"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x148a1e6",false],"id":6},
    {"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x148a1e7",false],"id":7},
    {"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x148a1e8",false],"id":8},
    {"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x148a1e9",false],"id":9}
  ]' | jq 'map({
    id: .id,
    block: .result.number,
    timestamp: .result.timestamp,
    tx_count: (.result.transactions | length)
  })'

sleep 1

# Example 5: Historical block from 2020
echo -e "\n5. Get historical block 10,000,000 (~May 2020):"
curl -s -X POST $LLAMARPC_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "eth_getBlockByNumber",
    "params": ["0x989680", false],
    "id": 1
  }' | jq '{
    number: .result.number,
    timestamp: .result.timestamp,
    datetime: (.result.timestamp | tonumber | todate),
    hash: .result.hash
  }'

sleep 1

# Example 6: The Merge block
echo -e "\n6. Get The Merge block (15,537,394 - Sep 15, 2022):"
curl -s -X POST $LLAMARPC_URL \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "eth_getBlockByNumber",
    "params": ["0xed29f2", false],
    "id": 1
  }' | jq '{
    number: .result.number,
    timestamp: .result.timestamp,
    datetime: (.result.timestamp | tonumber | todate),
    hash: .result.hash,
    difficulty: .result.difficulty
  }'

echo -e "\n======================================================================"
echo "Examples complete!"
echo ""
echo "Key findings:"
echo "- Historical depth: Full access back to genesis (July 2015)"
echo "- Batch requests: Supported (tested up to 20 blocks per batch)"
echo "- Rate limits: Strict - use 1-2s delay between batches"
echo "- Block format: Standard Ethereum JSON-RPC response"
