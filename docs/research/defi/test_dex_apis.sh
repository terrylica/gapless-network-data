#!/bin/bash
# Test various DEX data APIs

echo "=== 1. DEX Screener API (Free, no auth) ==="
# Get Uniswap V3 WETH/USDC pool data
curl -s "https://api.dexscreener.com/latest/dex/pairs/ethereum/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640" | jq '{pair: .pair.baseToken.symbol, priceUsd: .pair.priceUsd, volume24h: .pair.volume.h24, liquidity: .pair.liquidity.usd}'

echo -e "\n\n=== 2. Defined.fi API (Free tier available) ==="
# Test endpoint availability
curl -s "https://api.defined.fi/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { queryType { name } } }"}' | head -20

echo -e "\n\n=== 3. DeFi Llama API (Free, no auth) ==="
# Get Uniswap protocol data
curl -s "https://api.llama.fi/protocol/uniswap" | jq '{name: .name, chainTvls: .chainTvls | keys}'

echo -e "\n\n=== 4. CoinGecko DEX Volume (Free tier) ==="
curl -s "https://api.coingecko.com/api/v3/exchanges/uniswap_v3/volume_chart?days=1" | jq 'length'

echo -e "\n\n=== 5. Bitquery API (Free tier: 10k points/month) ==="
# Test Ethereum DEX trades
BITQUERY_ENDPOINT="https://graphql.bitquery.io"
curl -s -X POST "$BITQUERY_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ ethereum { dexTrades(options: {limit: 1, desc: \"block.timestamp.time\"}) { block { timestamp { time } } exchange { fullName } } } }"
  }' | jq .

echo -e "\n\n=== 6. Uniswap Labs API (Direct) ==="
# Check if direct API exists
curl -s "https://interface.gateway.uniswap.org/v1/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}' | head -20
