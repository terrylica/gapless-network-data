#!/bin/bash

echo "=== CSV Data Sources Verification ==="
echo ""

# Test 1: Check CryptoDataDownload structure
echo "Test 1: CryptoDataDownload - Check available data"
curl -s "https://www.cryptodatadownload.com/" | grep -i "minute" | head -3

echo ""
echo "Test 2: Check Kraken historical data availability"
curl -s "https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data" | grep -i "csv" | head -3

echo ""
echo "Test 3: Test direct Kraken CSV download (1-min BTC/USD)"
# Try to fetch a small sample to verify format
curl -s "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=1&since=1640995200" | jq -r '.result.XXBTZUSD[0]' 2>/dev/null

echo ""
echo "Test 4: Check CoinAPI documentation"
curl -s "https://docs.coinapi.io/" | grep -i "historical" | head -3
