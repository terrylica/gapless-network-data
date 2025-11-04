#!/bin/bash
# Test Dune Analytics and Flipside Crypto APIs

echo "=== 1. Dune Analytics API ==="
echo "Documentation: https://dune.com/docs/api/"
echo "Note: Free tier requires API key (30 requests/min)"
echo ""

# Check if Dune public queries are accessible
echo "Testing public query access..."
DUNE_QUERY_ID="3238251"  # Example public Uniswap V3 query
curl -s "https://api.dune.com/api/v1/query/${DUNE_QUERY_ID}/results" | head -50

echo -e "\n\n=== 2. Flipside Crypto API ==="
echo "Documentation: https://flipsidecrypto.xyz/api"
echo "Note: Free tier available with API key"
echo ""

# Test public endpoint
curl -s "https://api-v2.flipsidecrypto.xyz/json-rpc" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "getServerStats",
    "params": [],
    "id": 1
  }' | jq . 2>&1 | head -30

echo -e "\n\n=== 3. Footprint Analytics ==="
echo "Free tier with API key required"
curl -s "https://api.footprint.network/api/v1/public/card/query" | head -20

echo -e "\n\n=== 4. Covalent API (Chain Data) ==="
echo "Free tier: 100k credits/month"
# Test without API key to see response
curl -s "https://api.covalenthq.com/v1/1/address/0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984/transactions_v2/" | jq .error_message 2>&1

echo -e "\n\n=== 5. Transpose (Stream) ==="
echo "SQL queries on blockchain data, free tier available"
curl -s "https://api.transpose.io/api-status" | jq . 2>&1
