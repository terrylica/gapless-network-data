#!/bin/bash

echo "=== CryptoCompare API Test ==="
echo ""

# Test 1: Check how far back minute data goes (try 2022-01-01)
echo "Test 1: Historical depth - Try Jan 1, 2022 (timestamp: 1640995200)"
curl -s "https://min-api.cryptocompare.com/data/v2/histominute?fsym=BTC&tsym=USD&limit=10&toTs=1640995200" | jq '.Data.TimeFrom, .Data.TimeTo, .Data.Data[0]'

echo ""
echo "Test 2: Check 5-minute data endpoint"
curl -s "https://min-api.cryptocompare.com/data/v2/histominute?fsym=BTC&tsym=USD&limit=5&aggregate=5" | jq '.Data.Data[0:2]'

echo ""
echo "Test 3: Check available exchanges"
curl -s "https://min-api.cryptocompare.com/data/v4/all/exchanges" | jq 'keys | .[0:10]'

echo ""
echo "Test 4: Check Ethereum minute data"
curl -s "https://min-api.cryptocompare.com/data/v2/histominute?fsym=ETH&tsym=USD&limit=5" | jq '.Data.Data[0:2]'

echo ""
echo "Test 5: Check available blockchain list"
curl -s "https://min-api.cryptocompare.com/data/blockchain/list" | jq 'keys | .[0:10]'

echo ""
echo "Test 6: Test max limit per request"
curl -s "https://min-api.cryptocompare.com/data/v2/histominute?fsym=BTC&tsym=USD&limit=2000&toTs=1640995200" | jq '.Data.Data | length'
