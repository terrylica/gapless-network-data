#!/bin/bash
# Test The Graph decentralized network for Uniswap v3

# The Graph Gateway endpoint (free queries with rate limits)
GATEWAY="https://gateway.thegraph.com/api/[api-key]/subgraphs/id/"

# Uniswap v3 subgraph ID on decentralized network
# Try the public query node first
PUBLIC_NODE="https://api.studio.thegraph.com/query/48211/uniswap-v3-mainnet/version/latest"

echo "=== Testing Uniswap v3 on Graph Studio ==="
echo "Endpoint: $PUBLIC_NODE"
echo ""

# Simple query for recent swaps
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"query": "{ swaps(first: 2, orderBy: timestamp, orderDirection: desc) { timestamp } }"}' \
  "$PUBLIC_NODE"

echo -e "\n\n=== Checking alternative Uniswap endpoints ==="

# Try Messari's subgraph
MESSARI="https://api.thegraph.com/subgraphs/name/messari/uniswap-v3-ethereum"
echo "Testing Messari endpoint..."
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"query": "{ protocols(first: 1) { name } }"}' \
  "$MESSARI"

echo -e "\n\n=== Checking Odos Uniswap V3 ==="
ODOS="https://api.thegraph.com/subgraphs/name/odos-xyz/uniswap-v3"
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"query": "{ swaps(first: 1) { timestamp } }"}' \
  "$ODOS"
