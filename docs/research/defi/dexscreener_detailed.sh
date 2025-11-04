#!/bin/bash
# Deep dive into DEX Screener API capabilities

echo "=== DEX Screener API Analysis ==="
echo ""

# 1. Get latest data for WETH/USDC on Uniswap V3
echo "1. Latest WETH/USDC pair data:"
curl -s "https://api.dexscreener.com/latest/dex/pairs/ethereum/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640" | jq '{
  pairAddress: .pair.pairAddress,
  baseToken: .pair.baseToken.symbol,
  quoteToken: .pair.quoteToken.symbol,
  priceUsd: .pair.priceUsd,
  volume: {
    h24: .pair.volume.h24,
    h6: .pair.volume.h6,
    h1: .pair.volume.h1,
    m5: .pair.volume.m5
  },
  priceChange: {
    h24: .pair.priceChange.h24,
    h6: .pair.priceChange.h6,
    h1: .pair.priceChange.h1,
    m5: .pair.priceChange.m5
  },
  liquidity: .pair.liquidity.usd,
  fdv: .pair.fdv
}'

echo -e "\n2. Search for top Uniswap pairs:"
curl -s "https://api.dexscreener.com/latest/dex/search?q=WBTC%20USDC" | jq '.pairs[0:3] | .[] | {
  chainId: .chainId,
  dexId: .dexId,
  baseToken: .baseToken.symbol,
  quoteToken: .quoteToken.symbol,
  priceUsd: .priceUsd,
  volume24h: .volume.h24
}'

echo -e "\n3. Get tokens by address (WETH):"
curl -s "https://api.dexscreener.com/latest/dex/tokens/0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2" | jq '.pairs[0:2] | .[] | {
  dexId: .dexId,
  quoteToken: .quoteToken.symbol,
  priceUsd: .priceUsd,
  volume24h: .volume.h24
}'

echo -e "\n=== Key Observations ==="
echo "✓ Real-time data available"
echo "✓ Volume metrics: 24h, 6h, 1h, 5min"
echo "✓ Price change metrics: 24h, 6h, 1h, 5min"
echo "✓ Liquidity and FDV data"
echo "? Historical data availability: UNKNOWN"
echo "? Data back to 2022: UNKNOWN"
echo "? Rate limits: NOT DOCUMENTED in free tier"
