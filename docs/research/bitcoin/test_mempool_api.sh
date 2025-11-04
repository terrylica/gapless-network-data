#!/bin/bash

echo "=== Testing mempool.space API endpoints ==="
echo ""

echo "1. Current fees:"
curl -s "https://mempool.space/api/v1/fees/recommended" | jq .
echo ""

echo "2. Current mempool stats:"
curl -s "https://mempool.space/api/mempool" | jq 'del(.fee_histogram)'
echo ""

echo "3. Recent blocks (check timestamps):"
curl -s "https://mempool.space/api/v1/blocks/tip/height" 
echo ""
BLOCK_HEIGHT=$(curl -s "https://mempool.space/api/v1/blocks/tip/height")
echo "Current block height: $BLOCK_HEIGHT"
echo ""

echo "4. Get latest blocks with timestamps:"
curl -s "https://mempool.space/api/v1/blocks/0" | jq '.[0:3] | .[] | {height, timestamp, tx_count, size, weight}'
echo ""

echo "5. Check historical block (Jan 2022 - height ~718000):"
curl -s "https://mempool.space/api/v1/block-height/718000" | head -c 100
echo "..."
echo ""

echo "6. Mining stats (30d, 1y):"
curl -s "https://mempool.space/api/v1/mining/hashrate/pools/1m" | jq 'if type == "array" then .[0:2] else . end'
echo ""

