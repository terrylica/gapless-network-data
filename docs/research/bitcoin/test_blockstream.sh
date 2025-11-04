#!/bin/bash

echo "=== Testing Blockstream Esplora API ==="
echo ""

echo "1. Get latest block:"
curl -s "https://blockstream.info/api/blocks/tip/height"
echo ""

echo "2. Get recent blocks:"
curl -s "https://blockstream.info/api/blocks/0" | jq '.[0:3] | .[] | {height, timestamp, tx_count, size, weight}'
echo ""

echo "3. Fee estimates:"
curl -s "https://blockstream.info/api/fee-estimates" | jq '.'
echo ""

echo "4. Mempool info:"
curl -s "https://blockstream.info/api/mempool" | jq '.'
echo ""

echo "5. Test historical block (Jan 2022 - height ~718000):"
curl -s "https://blockstream.info/api/block-height/718000"
echo ""
