#!/bin/bash
# Test market data APIs that might include DEX data

echo "=== Market Data APIs ==="
echo ""

echo "1. CryptoCompare (Free tier: 100k calls/month):"
# Check if they have Uniswap or DEX-specific data
curl -s "https://min-api.cryptocompare.com/data/v2/histominute?fsym=ETH&tsym=USDC&limit=10" | jq '{
  Response: .Response,
  Type: .Type,
  Message: .Message,
  sample_data: .Data.Data[0:2]
}' 2>&1

echo -e "\n2. CoinCap API (Free, unlimited):"
# Real-time and historical asset data
curl -s "https://api.coincap.io/v2/assets/ethereum/history?interval=m15" | jq '{
  timestamp: .data[0].time,
  price: .data[0].priceUsd,
  date: .data[0].date
}' 2>&1

echo -e "\n3. CoinPaprika (Free, no auth):"
# Historical OHLCV
curl -s "https://api.coinpaprika.com/v1/tickers/eth-ethereum/historical?start=2024-11-01&interval=15m&limit=10" | jq '.[0:2] | .[] | {
  timestamp: .timestamp,
  price: .price,
  volume_24h: .volume_24h
}' 2>&1

echo -e "\n4. Messari API (Free tier: 20 calls/min):"
# Comprehensive crypto data
curl -s "https://data.messari.io/api/v1/assets/ethereum/metrics" | jq '{
  name: .data.name,
  symbol: .data.symbol,
  market_data: .data.market_data.price_usd
}' 2>&1

echo -e "\n5. Kaiko (Professional data, free trial available):"
echo "   - Institutional-grade data"
echo "   - Includes DEX data from Uniswap, SushiSwap, etc."
echo "   - Free tier: Limited"
curl -s "https://us.market-api.kaiko.io/v2/data/trades.v1/exchanges/cbse/spot/btc-usd/trades" | head -20

echo -e "\n6. Tardis.dev (Market data replay):"
echo "   - Historical orderbook, trades, derivatives"
echo "   - Free tier: Limited datasets"
curl -s "https://api.tardis.dev/v1/exchanges" | jq '.[0:5] | .[] | {id: .id, name: .name}' 2>&1

echo -e "\n7. TradingView (No free API):"
echo "   - Popular charting platform"
echo "   - No public API for historical data"
echo "   - Requires paid subscription for data export"
