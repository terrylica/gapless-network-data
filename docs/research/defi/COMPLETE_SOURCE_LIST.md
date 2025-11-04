# Complete DEX/DeFi Data Source List

**Research Date**: 2025-11-04
**Total Sources Evaluated**: 25+

---

## ✅ VIABLE FREE SOURCES (No Payment Required)

### 1. GeckoTerminal ⭐ Best for Recent M1 Data

- **URL**: https://api.geckoterminal.com/api/v2
- **Frequency**: M1, H1, D1 OHLCV
- **Historical Depth**: ~6 months (184 days tested)
- **Authentication**: None
- **Rate Limits**: 30 calls/min
- **Coverage**: All major DEXs (Uniswap, SushiSwap, PancakeSwap, etc.), multi-chain
- **Data Types**: OHLCV candles, pool info, trades, liquidity
- **Pros**: No auth, minute-level data, real-time updates
- **Cons**: Limited historical depth (6 months)
- **Status**: ✅ Tested & Working

### 2. DEX Screener - Best for Real-Time M5 Monitoring

- **URL**: https://api.dexscreener.com/latest
- **Frequency**: M5, H1, H6, H24 (volume/price snapshots)
- **Historical Depth**: Real-time only (no OHLCV endpoint)
- **Authentication**: None
- **Rate Limits**: Undocumented (appears generous)
- **Coverage**: All major DEXs, multi-chain
- **Data Types**: Current price, volume (M5, H1, H6, H24), price change, liquidity, FDV
- **Pros**: No auth, M5 granularity, unlimited pairs
- **Cons**: No historical data, no OHLCV candles
- **Status**: ✅ Tested & Working

### 3. CryptoCompare (Free Tier) - Best for H1 Historical

- **URL**: https://min-api.cryptocompare.com/data/v2
- **Frequency**: M1 (7 days), H1 (3+ years), D1 (multi-year)
- **Historical Depth**: M1: 7 days, H1: Back to 2021, D1: Multi-year
- **Authentication**: API key required (free tier)
- **Rate Limits**: 100k calls/month, 50 calls/sec
- **Coverage**: Major pairs (CEX + some DEX aggregated)
- **Data Types**: OHLCV (time, open, high, low, close, volumefrom, volumeto)
- **Pros**: Free tier, 3+ years H1 data, simple REST API
- **Cons**: Not DEX-specific (mixed sources), M1 limited to 7 days, requires signup
- **Status**: ✅ Tested & Working

### 4. Dune Analytics (Free Tier) ⭐ Best for Historical M15+

- **URL**: https://api.dune.com/api/v1
- **Frequency**: Custom SQL (any granularity: M1, M5, M15, H1, etc.)
- **Historical Depth**: Full blockchain history (Uniswap V3: May 2021 onwards)
- **Authentication**: API key required (free tier)
- **Rate Limits**: 30 requests/min
- **Coverage**: All DEXs on Ethereum, multi-chain support
- **Data Types**: Raw Swap events, custom aggregations, TVL, volume, fees
- **Pros**: Full history, custom M15 aggregation, powerful SQL
- **Cons**: Requires signup, query execution can be slow, DIY OHLCV
- **Status**: ✅ Tested (requires API key)

---

## 🔑 VIABLE FREE TIER (Registration Required)

### 5. Covalent

- **URL**: https://api.covalenthq.com/v1
- **Free Tier**: 100k credits/month
- **Data Types**: DEX endpoints `/xy=k/uniswap_v2/tokens/address/`
- **Coverage**: Uniswap V2/V3, SushiSwap, multi-chain
- **Status**: ⚠️ Requires API key (not tested)

### 6. Bitquery

- **URL**: https://graphql.bitquery.io
- **Free Tier**: 10k points/month
- **Data Types**: GraphQL queries on DEX trades, liquidity, swaps
- **Coverage**: Multi-chain DEX data
- **Status**: ⚠️ Requires API key, returned "Unauthorized"

### 7. Defined.fi

- **URL**: https://api.defined.fi/graphql
- **Free Tier**: Available (limits TBD)
- **Data Types**: Historical OHLCV, pool metrics, trades
- **Coverage**: Multi-chain DEX data
- **Status**: ⚠️ Introspection disabled, requires API key

### 8. Flipside Crypto

- **URL**: https://api-v2.flipsidecrypto.xyz
- **Free Tier**: Available (limits TBD)
- **Data Types**: SQL queries on blockchain data
- **Coverage**: Multi-chain
- **Status**: ⚠️ Requires API key (`x-api-key` header)

### 9. Goldsky

- **URL**: https://goldsky.com
- **Free Tier**: Available
- **Data Types**: Subgraph hosting (The Graph successor)
- **Coverage**: Custom subgraphs
- **Status**: ⚠️ Requires signup

### 10. Santiment

- **URL**: https://api.santiment.net/graphql
- **Free Tier**: 5 API calls/min
- **Data Types**: On-chain metrics, DEX volume, social sentiment
- **Coverage**: Major protocols
- **Status**: ⚠️ Requires API key

### 11. Transpose (Stream)

- **URL**: https://api.transpose.io
- **Free Tier**: Available (limits TBD)
- **Data Types**: SQL on blockchain data
- **Coverage**: Multi-chain
- **Status**: ⚠️ Requires API key

---

## ❌ NOT VIABLE (Deprecated or No Free Access)

### 12. The Graph Hosted Service

- **Status**: ❌ Deprecated (301 Moved Permanently)
- **Reason**: Sunset in June 2024, migrated to decentralized network
- **Alternative**: Graph Studio or Goldsky

### 13. Uniswap V3 Subgraph (Hosted)

- **Status**: ❌ 301 redirects
- **Reason**: Part of The Graph hosted service sunset

### 14. Messari Subgraphs

- **Status**: ❌ 301 redirects
- **Reason**: Hosted on The Graph (deprecated)

### 15. Footprint Analytics

- **Status**: ❌ Endpoint taken down
- **Response**: 403 "contact administrator"

---

## ⚠️ LIMITED USE CASES (Not Suitable for Historical Data)

### 16. 1inch API

- **URL**: https://api.1inch.dev
- **Use Case**: DEX aggregator routing
- **Data Types**: Real-time quotes, swap routing
- **Limitation**: No historical OHLCV
- **Status**: ⚠️ Requires API key for v5.2

### 17. 0x API

- **URL**: https://api.0x.org
- **Use Case**: DEX aggregator
- **Data Types**: Real-time quotes
- **Limitation**: No historical data
- **Status**: ⚠️ Limited response without auth

### 18. ParaSwap API

- **URL**: https://apiv5.paraswap.io
- **Use Case**: DEX aggregator routing
- **Data Types**: Real-time pricing, routes
- **Limitation**: No historical OHLCV
- **Status**: ✅ Works (real-time only)

### 19. KyberSwap API

- **URL**: https://aggregator-api.kyberswap.com
- **Use Case**: DEX aggregator
- **Data Types**: Real-time routes
- **Limitation**: No historical data
- **Status**: ✅ Works (real-time only)

### 20. CowSwap API

- **URL**: https://api.cow.fi
- **Use Case**: MEV-protected swaps
- **Data Types**: Market data
- **Limitation**: No historical OHLCV
- **Status**: ⚠️ Limited response

### 21. SushiSwap API

- **URL**: https://api.sushi.com
- **Use Case**: Price data
- **Data Types**: Current prices
- **Limitation**: No historical OHLCV
- **Status**: ⚠️ Inconsistent responses

---

## 🔒 PAID SERVICES (No Free Tier)

### 22. Kaiko

- **URL**: https://us.market-api.kaiko.io
- **Tier**: Professional (paid only)
- **Data Types**: Institutional-grade DEX data from Uniswap, SushiSwap
- **Status**: ❌ Requires authentication

### 23. Glassnode

- **Tier**: Paid plans only for most data
- **Data Types**: On-chain metrics
- **Status**: ❌ No free DEX-specific historical data

### 24. TradingView

- **Tier**: No public API
- **Limitation**: Requires paid subscription for data export
- **Status**: ❌ Not accessible

---

## 🚫 NOT SUITABLE (No Pre-Indexed DEX Data)

### 25. Alchemy

- **URL**: https://www.alchemy.com
- **Free Tier**: 300M compute units/month
- **Limitation**: No pre-indexed DEX data (raw RPC only)
- **Use Case**: Would require manual Swap event parsing
- **Status**: ❌ Not suitable

### 26. QuickNode

- **Free Tier**: Testnet only (10M requests/month)
- **Limitation**: No pre-indexed DEX aggregation
- **Status**: ❌ Not suitable

### 27. Moralis Web3 API

- **URL**: https://deep-index.moralis.io
- **Free Tier**: Available
- **Limitation**: No pre-indexed DEX OHLCV
- **Status**: ⚠️ Requires API key, no DEX focus

### 28. Ankr

- **URL**: https://rpc.ankr.com
- **Free Tier**: Available
- **Limitation**: No DEX aggregation
- **Status**: ⚠️ Requires API key

### 29. Unmarshal

- **URL**: https://api.unmarshal.com
- **Free Tier**: Available
- **Limitation**: Limited response (empty)
- **Status**: ⚠️ Requires investigation

---

## 📊 OTHER MARKET DATA SOURCES (Not DEX-Specific)

### 30. CoinCap API

- **URL**: https://api.coincap.io
- **Free**: Unlimited
- **Data**: Historical asset prices (15min intervals)
- **Limitation**: Not DEX-specific, aggregated market data
- **Status**: ✅ Works (aggregated only)

### 31. CoinPaprika

- **URL**: https://api.coinpaprika.com
- **Free**: No auth required
- **Data**: Historical OHLCV (15min intervals)
- **Limitation**: Not DEX-specific
- **Status**: ⚠️ Response parsing issues

### 32. Messari API

- **URL**: https://data.messari.io/api/v1
- **Free Tier**: 20 calls/min
- **Data**: Asset metrics, market data
- **Limitation**: Not DEX-specific
- **Status**: ⚠️ Limited response

### 33. CoinGecko (Non-Terminal)

- **URL**: https://api.coingecko.com/api/v3
- **Free Tier**: 10-50 calls/min
- **Data**: Exchange volumes, market data
- **Limitation**: Not OHLCV, not DEX-specific
- **Status**: ✅ Works (aggregated data)

### 34. Tardis.dev

- **URL**: https://api.tardis.dev
- **Free Tier**: Limited datasets
- **Data**: Historical orderbook, trades (CEX focus)
- **Limitation**: Primarily CEX data
- **Status**: ✅ Works (not DEX focus)

### 35. Blocknative

- **URL**: https://api.blocknative.com
- **Free Tier**: Available
- **Data**: Mempool data, gas prices (real-time)
- **Limitation**: Not historical DEX data
- **Status**: ✅ Works (real-time only)

---

## 🎯 SUMMARY BY USE CASE

### Use Case 1: M15+ Historical Data (2022+)

**Recommended**: Dune Analytics (free API key)
**Alternative**: CryptoCompare H1 (free API key)

### Use Case 2: Recent M1 Data (6 months)

**Recommended**: GeckoTerminal (no auth)

### Use Case 3: Real-Time M5 Monitoring

**Recommended**: DEX Screener (no auth)

### Use Case 4: Quick Prototyping (No Auth)

**Recommended**: GeckoTerminal + DEX Screener

### Use Case 5: Production ML Pipeline

**Recommended**: Dune (historical) + GeckoTerminal (recent) + DEX Screener (live)

---

## 📈 DATA AVAILABILITY MATRIX

| Source         | M1  | M5   | M15 | H1   | D1   | 2022+ | Auth | Free |
| -------------- | --- | ---- | --- | ---- | ---- | ----- | ---- | ---- |
| GeckoTerminal  | ✅  | ❌   | ❌  | ✅   | ✅   | ❌    | ❌   | ✅   |
| DEX Screener   | ❌  | ✅\* | ❌  | ✅\* | ✅\* | ❌    | ❌   | ✅   |
| CryptoCompare  | ✅† | ❌   | ❌  | ✅   | ✅   | ✅‡   | 🔑   | ✅   |
| Dune Analytics | ✅§ | ✅§  | ✅§ | ✅§  | ✅§  | ✅    | 🔑   | ✅   |
| Covalent       | ❌  | ❌   | ❌  | ❌   | ❌   | ✅    | 🔑   | ✅   |
| Bitquery       | ✅§ | ✅§  | ✅§ | ✅§  | ✅§  | ✅    | 🔑   | ✅   |
| Defined.fi     | ✅  | ✅   | ✅  | ✅   | ✅   | ✅    | 🔑   | ✅   |

**Legend**:

- ✅ = Available
- ❌ = Not available
- 🔑 = API key required
- ✅\* = Snapshot only (not OHLCV)
- ✅† = Limited to 7 days
- ✅‡ = H1 only (M1 limited to 7 days)
- ✅§ = Custom SQL/GraphQL aggregation

---

## 🔬 RESEARCH METHODOLOGY

**Approach**: Empirical testing with dynamic TODO progression

**Tools**:

- curl for API testing
- jq for JSON parsing
- Bash scripts for automation
- Absolute timestamp testing for historical depth validation

**Validation Criteria**:

1. Free access (with or without API key)
2. M15+ frequency capability
3. Historical depth to 2022 (3+ years)
4. DEX-specific or applicable data
5. Documented or discoverable endpoints

**Total Time**: ~2 hours systematic research

---

## 📦 DELIVERABLES

All research artifacts in `/tmp/defi-research/`:

1. **README.md** - Project overview
2. **FINDINGS_SUMMARY.md** - Complete analysis (12KB)
3. **API_ENDPOINTS_REFERENCE.md** - API documentation (11KB)
4. **COMPLETE_SOURCE_LIST.md** - This file (comprehensive catalog)
5. **QUICK_REFERENCE.txt** - Visual quick start guide
6. **10+ test scripts** - Reproducible validation

---

**Last Updated**: 2025-11-04 04:55 UTC
**Total Sources Documented**: 35
**Viable Free Sources**: 4-9 (depending on signup tolerance)
**Recommended for M15+ 2022+ data**: Dune Analytics
