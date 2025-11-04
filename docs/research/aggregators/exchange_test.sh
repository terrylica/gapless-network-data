#!/bin/bash

echo "=== Multi-Exchange API Test ==="
echo ""

# Coinbase Advanced Trade API
echo "Test 1: Coinbase Advanced Trade - BTC-USD candles (1-minute)"
# Coinbase uses ISO 8601 timestamps
curl -s "https://api.exchange.coinbase.com/products/BTC-USD/candles?start=2022-01-01T00:00:00Z&end=2022-01-01T00:10:00Z&granularity=60" | jq '.[0:3]'

echo ""
echo "Test 2: Kraken OHLC - BTC/USD (1-minute)"
# Kraken interval: 1 = 1 minute, since parameter in Unix timestamp
curl -s "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=1&since=1640995200" | jq '.result.XXBTZUSD[0:3]'

echo ""
echo "Test 3: KuCoin - BTC-USDT klines (1-minute)"
# KuCoin uses seconds for timestamps, type can be 1min, 5min, 15min
curl -s "https://api.kucoin.com/api/v1/market/candles?type=1min&symbol=BTC-USDT&startAt=1640995200&endAt=1640995800" | jq '.data[0:3]'

echo ""
echo "Test 4: OKX - BTC-USDT candles (1m bar)"
# OKX uses millisecond timestamps
curl -s "https://www.okx.com/api/v5/market/candles?instId=BTC-USDT&bar=1m&after=1640995200000&limit=5" | jq '.data[0:3]'

echo ""
echo "Test 5: Bybit - BTC/USDT kline (1 minute)"
curl -s "https://api.bybit.com/v5/market/kline?category=spot&symbol=BTCUSDT&interval=1&start=1640995200000&limit=5" | jq '.result.list[0:3]'
