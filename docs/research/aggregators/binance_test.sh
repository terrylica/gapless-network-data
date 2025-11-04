#!/bin/bash

echo "=== Binance Public API Test ==="
echo ""

# Test 1: Get current time to calculate historical timestamp
echo "Test 1: Check M1 (1-minute) data from Jan 1, 2022"
# Jan 1, 2022 00:00:00 UTC = 1640995200000 ms
curl -s "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&startTime=1640995200000&limit=5" | jq '.'

echo ""
echo "Test 2: Check M5 (5-minute) data from Jan 1, 2022"
curl -s "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=5m&startTime=1640995200000&limit=5" | jq '.'

echo ""
echo "Test 3: Check M15 (15-minute) data from Jan 1, 2022"
curl -s "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=15m&startTime=1640995200000&limit=5" | jq '.'

echo ""
echo "Test 4: Check how far back data goes (try 2017)"
# Jan 1, 2017 00:00:00 UTC = 1483228800000 ms
curl -s "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&startTime=1483228800000&limit=5" | jq '.'

echo ""
echo "Test 5: Check max limit per request"
curl -s "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=1000" | jq 'length'

echo ""
echo "Test 6: Check Ethereum data"
curl -s "https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1m&startTime=1640995200000&limit=3" | jq '.'

echo ""
echo "Test 7: Check exchange info for available symbols"
curl -s "https://api.binance.com/api/v3/exchangeInfo" | jq '.symbols | length'
