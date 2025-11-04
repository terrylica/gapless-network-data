#!/bin/bash

echo "=== CoinGecko API Test ==="
echo ""

# Test 1: Check granularity with different days parameter
echo "Test 1: Daily granularity (365 days)"
curl -s "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=365" | jq 'length'

echo ""
echo "Test 2: Granularity with 90 days (should be 4-hourly per docs)"
curl -s "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=90" | jq 'length'

echo ""
echo "Test 3: Granularity with 7 days (should be hourly)"
curl -s "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=7" | jq 'length'

echo ""
echo "Test 4: Granularity with 1 day (should be 30-minute)"
curl -s "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=1" | jq 'length'

echo ""
echo "Test 5: Check available coins list (first 5)"
curl -s "https://api.coingecko.com/api/v3/coins/list" | jq '.[0:5]'

echo ""
echo "Test 6: Check supported chains"
curl -s "https://api.coingecko.com/api/v3/asset_platforms" | jq '[.[] | select(.id != null) | {id: .id, name: .name, chain_identifier: .chain_identifier}] | .[0:10]'
