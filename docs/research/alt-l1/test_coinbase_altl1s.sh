#!/bin/bash

symbols=("AVAX-USD" "ADA-USD" "DOT-USD" "ATOM-USD" "NEAR-USD" "ALGO-USD" "XTZ-USD")

for symbol in "${symbols[@]}"; do
    echo "=== Testing $symbol ==="
    result=$(curl -s "https://api.exchange.coinbase.com/products/$symbol/candles?granularity=60&start=2022-01-01T00:00:00Z&end=2022-01-01T00:05:00Z")
    
    if echo "$result" | jq -e '.[0]' > /dev/null 2>&1; then
        count=$(echo "$result" | jq 'length')
        first_time=$(echo "$result" | jq -r '.[-1][0]')
        first_price=$(echo "$result" | jq -r '.[-1][3]')
        echo "✓ Available - $count candles, First: $(date -r $first_time '+%Y-%m-%d %H:%M:%S'), Price: $first_price"
    else
        echo "✗ Not available: $result"
    fi
    echo ""
    sleep 0.5
done
