#!/bin/bash
# Test GeckoTerminal API (CoinGecko's DEX data product)

BASE_URL="https://api.geckoterminal.com/api/v2"

echo "=== GeckoTerminal API Testing ==="
echo "Documentation: https://www.geckoterminal.com/dex-api"
echo ""

# 1. Get trending pools
echo "1. Trending pools on Ethereum:"
curl -s "${BASE_URL}/networks/eth/trending_pools" | jq '.data[0:3] | .[] | {
  name: .attributes.name,
  address: .attributes.address,
  base_token: .attributes.base_token_price_usd,
  volume_24h: .attributes.volume_usd.h24,
  price_change_24h: .attributes.price_change_percentage.h24
}' 2>&1

echo -e "\n2. Get specific pool info (WETH/USDC on Uniswap V3):"
POOL_ADDRESS="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
curl -s "${BASE_URL}/networks/eth/pools/${POOL_ADDRESS}" | jq '.data.attributes | {
  name: .name,
  address: .address,
  pool_created_at: .pool_created_at,
  price_usd: .base_token_price_usd,
  volume_24h: .volume_usd.h24,
  reserve_usd: .reserve_in_usd
}' 2>&1

echo -e "\n3. Get OHLCV data (most important for our use case):"
# Check available timeframes: 1m, 5m, 15m, 1h, 4h, 12h, 1d
TIMEFRAME="minute"  # Can be: minute, hour, day
curl -s "${BASE_URL}/networks/eth/pools/${POOL_ADDRESS}/ohlcv/${TIMEFRAME}?aggregate=1&limit=100" | jq '{
  meta: .meta,
  sample_candles: .data.attributes.ohlcv_list[0:3]
}' 2>&1

echo -e "\n4. Test different timeframes:"
for tf in "minute" "hour" "day"; do
  echo "  Timeframe: ${tf}"
  curl -s "${BASE_URL}/networks/eth/pools/${POOL_ADDRESS}/ohlcv/${tf}?limit=5" | jq '.data.attributes.ohlcv_list[0] // "No data"' 2>&1
done

echo -e "\n5. Get pool trades (recent swaps):"
curl -s "${BASE_URL}/networks/eth/pools/${POOL_ADDRESS}/trades?limit=3" | jq '.data[0:3] | .[] | {
  block_timestamp: .attributes.block_timestamp,
  kind: .attributes.kind,
  volume_usd: .attributes.volume_in_usd,
  from_token: .attributes.from_token_amount,
  to_token: .attributes.to_token_amount
}' 2>&1

echo -e "\n6. Search for pools:"
curl -s "${BASE_URL}/search/pools?query=WBTC" | jq '.data[0:2] | .[] | {
  name: .attributes.name,
  network: .relationships.network.data.id,
  address: .attributes.address
}' 2>&1

echo -e "\n=== Key Findings ==="
echo "✓ OHLCV data available (minute, hour, day)"
echo "✓ Recent trades/swaps available"
echo "✓ Pool info with volume and liquidity"
echo "? Historical depth: Testing..."
echo "? Rate limits: 30 calls/min per API docs"
