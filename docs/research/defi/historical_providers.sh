#!/bin/bash
# Research historical DEX data providers

echo "=== Specialized Historical Data Providers ==="
echo ""

echo "1. Defined.fi (GraphQL API):"
echo "   - Free tier: Available with API key"
echo "   - Historical OHLCV data for DEX pairs"
echo "   - Test with proper query..."

# Defined.fi requires API key, but let's check documentation endpoint
curl -s "https://docs.defined.fi" | grep -i "ohlcv\|candle\|historical" | head -5

echo -e "\n2. Goldsky (Subgraph hosting & real-time indexing):"
echo "   - Successor to The Graph hosted service"
echo "   - Free tier available"
echo "   - Check main site..."
curl -s "https://goldsky.com" | grep -i "pricing\|free" | head -3

echo -e "\n3. SubQuery Network:"
echo "   - Multi-chain indexing"
echo "   - Check if they have Ethereum DEX data"
curl -s "https://api.subquery.network/sq/subquery/eth-dictionary" | head -20

echo -e "\n4. Subsquid (The Graph alternative):"
echo "   - Open-source indexing framework"
echo "   - Check for Uniswap squids..."
curl -s "https://squid.subsquid.io/gs-explorer-uniswap/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ swapsConnection(first: 1) { totalCount } }"}' | jq . 2>&1

echo -e "\n5. Blocknative Mempool Platform:"
echo "   - Real-time mempool data (not historical)"
curl -s "https://api.blocknative.com/gasprices/blockprices" | jq .blockPrices[0] 2>&1

echo -e "\n6. Santiment API:"
echo "   - On-chain metrics including DEX volume"
echo "   - Free tier: 5 API calls/min"
curl -s "https://api.santiment.net/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ getMetric(metric: \"dev_activity\") { metadata { metric } } }"}' | jq . 2>&1 | head -20

echo -e "\n7. Glassnode:"
echo "   - On-chain metrics (requires paid plan for most data)"
echo "   - No free DEX-specific historical data"

echo -e "\n8. IntoTheBlock:"
echo "   - On-chain intelligence"
curl -s "https://api.intotheblock.com/market/markets" | head -20
