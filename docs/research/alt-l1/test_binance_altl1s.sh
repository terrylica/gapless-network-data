#!/bin/bash

symbols=("AVAXUSDT" "ADAUSDT" "DOTUSDT" "ATOMUSDT" "NEARUSDT" "ALGOUSDT" "XTZUSDT")
start_2022=1640995200000  # 2022-01-01 00:00:00 UTC

for symbol in "${symbols[@]}"; do
    echo "=== Testing $symbol ==="
    result=$(curl -s "https://api.binance.com/api/v3/klines?symbol=$symbol&interval=1m&startTime=$start_2022&limit=1")
    
    if echo "$result" | jq -e '.[0]' > /dev/null 2>&1; then
        open_time=$(echo "$result" | jq -r '.[0][0]')
        open_price=$(echo "$result" | jq -r '.[0][1]')
        echo "✓ Available - First candle: $(date -r $((open_time/1000)) '+%Y-%m-%d %H:%M:%S'), Open: $open_price"
    else
        echo "✗ Not available or error: $result"
    fi
    echo ""
    sleep 0.5
done
