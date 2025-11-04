#!/bin/bash

echo "=== Testing blockchain.info API ==="
echo ""

echo "1. Charts available:"
curl -s "https://api.blockchain.info/charts/market-price?timespan=5weeks&format=json&cors=true" | jq 'if .values then (.values | length, .[0:3]) else . end'
echo ""

echo "2. Test different charts:"
for chart in "market-price" "transactions-per-second" "mempool-size" "avg-block-size" "n-transactions" "hash-rate"; do
    echo "Chart: $chart"
    curl -s "https://api.blockchain.info/charts/$chart?timespan=1year&sampled=false&format=json&cors=true" 2>/dev/null | jq 'if .values then "Points: \(.values | length), Latest: \(.values[-1])" else . end' 2>/dev/null || echo "  Failed"
    echo ""
done
