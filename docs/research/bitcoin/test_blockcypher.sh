#!/bin/bash

echo "=== BlockCypher API Analysis ==="
echo ""

echo "1. Main chain info:"
curl -s "https://api.blockcypher.com/v1/btc/main" | jq '{height, time, unconfirmed_count, high_fee_per_kb, medium_fee_per_kb, low_fee_per_kb}'
echo ""

echo "2. Get block by height (recent):"
curl -s "https://api.blockcypher.com/v1/btc/main/blocks/922000" | jq '{height, time, n_tx, total, fees}'
echo ""

echo "3. Get historical block (Jan 2022 - ~718000):"
curl -s "https://api.blockcypher.com/v1/btc/main/blocks/718000" | jq '{height, time, n_tx, total, fees}'
echo ""

echo "4. Test block range endpoint:"
curl -s "https://api.blockcypher.com/v1/btc/main/blocks/922000?limit=3" | jq 'if type == "array" then length else . end'
echo ""
