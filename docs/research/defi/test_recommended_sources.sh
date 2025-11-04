#!/bin/bash
# Quick test script for recommended DEX data sources

echo "==================================================================="
echo "DEX Data Sources - Quick Test"
echo "==================================================================="
echo ""

# 1. GeckoTerminal - Best for recent high-frequency
echo "1️⃣  GeckoTerminal (M1 OHLCV - Recent 6 months)"
echo "-------------------------------------------------------------------"
POOL="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"  # WETH/USDC
curl -s "https://api.geckoterminal.com/api/v2/networks/eth/pools/${POOL}/ohlcv/minute?limit=5" | jq '{
  candles: (.data.attributes.ohlcv_list | length),
  latest: .data.attributes.ohlcv_list[0] | {
    timestamp: .[0],
    open: .[1],
    high: .[2],
    low: .[3],
    close: .[4],
    volume: .[5]
  }
}'
echo ""

# 2. DEX Screener - Best for real-time M5 snapshots
echo "2️⃣  DEX Screener (M5 aggregates - Real-time)"
echo "-------------------------------------------------------------------"
curl -s "https://api.dexscreener.com/latest/dex/pairs/ethereum/${POOL}" | jq '{
  pair: .pair.baseToken.symbol + "/" + .pair.quoteToken.symbol,
  priceUsd: .pair.priceUsd,
  volume_m5: .pair.volume.m5,
  volume_h1: .pair.volume.h1,
  priceChange_m5: .pair.priceChange.m5,
  priceChange_h1: .pair.priceChange.h1
}'
echo ""

# 3. CryptoCompare - Best for historical H1 (requires API key)
echo "3️⃣  CryptoCompare (H1 OHLCV - Back to 2021)"
echo "-------------------------------------------------------------------"
echo "Testing without API key (limited functionality):"
curl -s "https://min-api.cryptocompare.com/data/v2/histohour?fsym=ETH&tsym=USDC&limit=5" | jq '{
  Response: .Response,
  Message: .Message,
  candles: (.Data.Data | length),
  latest: .Data.Data[-1] | {
    time: .time,
    open: .open,
    high: .high,
    low: .low,
    close: .close,
    volume: .volumefrom
  }
}'
echo ""

# 4. Dune Analytics - Best for historical data (requires API key)
echo "4️⃣  Dune Analytics (Custom SQL - Full history)"
echo "-------------------------------------------------------------------"
echo "❌ Requires API key - Sign up at https://dune.com/settings/api"
echo "Free tier: 30 requests/min, SQL queries for Swap events"
echo ""

# 5. Summary
echo "==================================================================="
echo "📊 SUMMARY"
echo "==================================================================="
echo ""
echo "✅ No API Key Required:"
echo "   - GeckoTerminal: M1 OHLCV, ~6 months history"
echo "   - DEX Screener: M5 snapshots, real-time only"
echo ""
echo "🔑 Free API Key Required:"
echo "   - CryptoCompare: M1 (7d), H1 (3y+), 100k calls/month"
echo "   - Dune Analytics: Custom SQL, full history, 30 req/min"
echo ""
echo "🎯 Recommendation for 2022+ M15 data:"
echo "   Sign up for Dune Analytics free tier"
echo "   Query: uniswap_v3_ethereum.Swap events"
echo "   Aggregate: GROUP BY date_trunc('minute', 15)"
echo ""
