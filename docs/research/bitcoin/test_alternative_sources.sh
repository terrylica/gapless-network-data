#!/bin/bash

echo "=== Testing Alternative Bitcoin Data Sources ==="
echo ""

echo "1. Testing Bitcoin.com API:"
curl -s "https://rest.bitcoin.com/v2/blockchain/getBlockchainInfo" 2>&1 | head -c 200
echo "..."
echo ""

echo "2. Testing Blockchair API (supports historical):"
curl -s "https://api.blockchair.com/bitcoin/stats" | jq 'if .data then .data else . end' | head -20
echo "..."
echo ""

echo "3. Testing BlockCypher API:"
curl -s "https://api.blockcypher.com/v1/btc/main" | jq 'if . then . else empty end' | head -20
echo "..."
echo ""

echo "4. Testing btc.com API:"
curl -s "https://chain.api.btc.com/v3/block/latest" 2>&1 | jq 'if .data then .data else . end' | head -20
echo "..."
echo ""
