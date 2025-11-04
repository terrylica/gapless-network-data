#!/bin/bash
# Test Uniswap v3 subgraph on The Graph

# Uniswap v3 Ethereum mainnet subgraph endpoint
ENDPOINT="https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"

# Query to check oldest swap data and schema
QUERY='{"query": "{ swaps(first: 1, orderBy: timestamp, orderDirection: asc) { timestamp id token0 { symbol } token1 { symbol } amount0 amount1 amountUSD } }"}'

echo "=== Testing Uniswap v3 Subgraph ==="
echo "Endpoint: $ENDPOINT"
echo ""
echo "Fetching oldest swap record..."
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "$QUERY" \
  "$ENDPOINT" | jq .

# Query for recent swaps to check data freshness
RECENT_QUERY='{"query": "{ swaps(first: 5, orderBy: timestamp, orderDirection: desc) { timestamp id pool { token0 { symbol } token1 { symbol } } amount0 amount1 amountUSD } }"}'

echo ""
echo "=== Fetching 5 most recent swaps ==="
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "$RECENT_QUERY" \
  "$ENDPOINT" | jq .

# Query pool data
POOL_QUERY='{"query": "{ pools(first: 5, orderBy: totalValueLockedUSD, orderDirection: desc) { id token0 { symbol } token1 { symbol } totalValueLockedUSD volumeUSD } }"}'

echo ""
echo "=== Top 5 Pools by TVL ==="
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "$POOL_QUERY" \
  "$ENDPOINT" | jq .
