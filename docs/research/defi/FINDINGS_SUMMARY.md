# DEX/DeFi On-Chain Data Research - Free High-Frequency Sources

**Research Date**: 2025-11-04
**Objective**: Find free APIs/datasets with M1/M5/M15+ frequency, historical depth to 2022 (3+ years)
**Data Types**: DEX trades, liquidity pools, TVL, swap volumes, OHLCV

---

## Executive Summary

**Key Finding**: No truly free DEX data source provides both high-frequency (M15+) AND historical depth back to 2022.

**Best Available Options**:

1. **GeckoTerminal** - Minute-level OHLCV, but only 6 months history
2. **DEX Screener** - 5-minute aggregates (real-time), historical depth unknown
3. **CryptoCompare** - Minute data (7 days only), Hourly data (back to 2021)

---

## Detailed Findings

### 1. GeckoTerminal (CoinGecko) ⭐ Best for Recent High-Frequency

**URL**: `https://api.geckoterminal.com/api/v2`
**Authentication**: None required
**Rate Limits**: 30 calls/min (documented)

**Frequency Available**:

- ✅ M1 (minute candles)
- ✅ H1 (hour candles)
- ✅ D1 (day candles)

**Historical Depth**:

- Minute data: ~17 hours only (1,000 candles max)
- Hour data: Limited testing
- Day data: **184 days (~6 months)** (tested on WETH/USDC)

**Data Types**:

- OHLCV candles (Open, High, Low, Close, Volume)
- Pool info (TVL, 24h volume, reserves)
- Recent trades/swaps
- Pool metadata

**Pools/Pairs Covered**:

- All major DEXs: Uniswap V2/V3, SushiSwap, PancakeSwap, etc.
- Multi-chain: Ethereum, BSC, Polygon, Arbitrum, Optimism, etc.
- Thousands of pairs

**Example Query - M1 OHLCV**:

```bash
curl "https://api.geckoterminal.com/api/v2/networks/eth/pools/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640/ohlcv/minute?aggregate=1&limit=1000"
```

**Response Format**:

```json
{
  "data": {
    "attributes": {
      "ohlcv_list": [
        [1762231500, 3637.54, 3637.54, 3637.54, 3637.54, 300.71]
        // [timestamp, open, high, low, close, volume]
      ]
    }
  }
}
```

**Limitations**:

- ❌ Historical depth only ~6 months (does NOT reach 2022)
- ❌ No documented way to paginate through older data
- ⚠️ Free tier rate limits (30/min) may be restrictive for bulk downloads

---

### 2. DEX Screener ⭐ Best for Real-Time Monitoring

**URL**: `https://api.dexscreener.com/latest`
**Authentication**: None required
**Rate Limits**: Undocumented (free tier)

**Frequency Available**:

- ✅ M5 (5-minute volume/price change)
- ✅ H1 (1-hour aggregates)
- ✅ H6 (6-hour aggregates)
- ✅ H24 (24-hour aggregates)

**Historical Depth**:

- ❓ Unknown - No OHLCV endpoint available
- Only real-time snapshots tested
- Historical endpoint existence: NOT FOUND

**Data Types**:

- Current price USD
- Volume (5m, 1h, 6h, 24h)
- Price change % (5m, 1h, 6h, 24h)
- Liquidity USD
- FDV (Fully Diluted Valuation)

**Example Query - Latest Pair Data**:

```bash
curl "https://api.dexscreener.com/latest/dex/pairs/ethereum/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
```

**Response Format**:

```json
{
  "pair": {
    "baseToken": { "symbol": "WETH" },
    "quoteToken": { "symbol": "USDC" },
    "priceUsd": "3628.75",
    "volume": {
      "m5": 60453.21,
      "h1": 970084.04,
      "h6": 13034624.23,
      "h24": 91609210.05
    },
    "priceChange": {
      "m5": -0.06,
      "h1": -0.54,
      "h6": 1.25,
      "h24": -2.76
    }
  }
}
```

**Limitations**:

- ❌ No OHLCV historical endpoint
- ❌ Cannot retrieve historical data for feature engineering
- ⚠️ Only useful for real-time monitoring
- ⚠️ Rate limits not documented

---

### 3. CryptoCompare 🔸 Mixed Results

**URL**: `https://min-api.cryptocompare.com/data/v2`
**Authentication**: API key required (free tier: 100k calls/month)
**Rate Limits**: 100k calls/month, 50 calls/sec

**Frequency Available**:

- ✅ M1 (minute) - **7 days only**
- ✅ H1 (hour) - **Back to 2021** ⭐
- ✅ D1 (day) - Multi-year history

**Historical Depth**:

- Minute: **7 days only** (ETH/USDC tested)
- Hour: **Back to October 2021** (3+ years) ✅
- Day: Multi-year

**Data Types**:

- OHLCV (time, open, high, low, close, volumefrom, volumeto)
- Aggregated from CEX and some DEX sources

**Example Query - Hourly OHLCV**:

```bash
curl "https://min-api.cryptocompare.com/data/v2/histohour?fsym=ETH&tsym=USDC&limit=2000&toTs=1640995200"
```

**Response Format**:

```json
{
  "Response": "Success",
  "Data": {
    "Data": [
      {
        "time": 1633795200,
        "high": 3631.4,
        "low": 3628.81,
        "open": 3631.13,
        "volumefrom": 56.43,
        "volumeto": 204865.54,
        "close": 3630.74
      }
    ]
  }
}
```

**Limitations**:

- ❌ Minute data only 7 days (not suitable for 2022 backfill)
- ⚠️ Data is aggregated (CEX + some DEX), not pure DEX
- ⚠️ API key required (free tier available)
- ✅ Hourly data has 3+ year history (suitable for H1+ timeframes)

---

### 4. The Graph Network ❌ Sunset

**Status**: Hosted service deprecated
**Migration**: Decentralized network requires API keys

**Findings**:

- Uniswap V3 subgraph on hosted service: **301 Moved Permanently**
- Graph Studio endpoints: **404 Not Found**
- Messari/Odos alternative subgraphs: **301 redirects**

**Recommendation**: Not viable for free access anymore

---

### 5. Dune Analytics 🔑 Requires API Key

**URL**: `https://api.dune.com/api/v1`
**Authentication**: API key required
**Free Tier**: 30 requests/min

**Capabilities**:

- SQL queries on indexed blockchain data
- Historical DEX swap events
- Custom aggregations (M1, M5, M15 possible via SQL)
- Data back to genesis blocks (full history)

**Limitations**:

- ❌ Requires free API key signup
- ⚠️ Query execution can be slow
- ⚠️ Free tier rate limits (30/min)

**Verdict**: Powerful but requires registration

---

### 6. Other Services Evaluated

#### Bitquery ❌

- Requires API key (no free unauthenticated access)
- Free tier: 10k points/month
- GraphQL endpoint: Returns "Unauthorized" without key

#### Flipside Crypto ❌

- Requires API key (`x-api-key` header)
- Free tier available after signup
- SQL-based queries

#### Covalent 🔑

- Free tier: 100k credits/month
- API key required
- DEX endpoints: `/xy=k/uniswap_v2/tokens/address/`

#### Defined.fi 🔑

- GraphQL API with historical OHLCV
- Requires API key (free tier available)
- Introspection disabled (need docs)

#### Goldsky 🔑

- Successor to The Graph hosted service
- Free tier available
- Requires signup

#### Santiment 🔑

- On-chain metrics
- Free tier: 5 API calls/min
- Requires API key

#### DEX Aggregators (1inch, 0x, ParaSwap, KyberSwap)

- ❌ No historical data
- ❌ Only real-time quotes/routing
- Not suitable for feature engineering

#### Blockchain Node Providers (Alchemy, QuickNode, Moralis, Ankr)

- ❌ No pre-indexed DEX data
- Would require manual Swap event parsing
- Requires API keys

---

## Comparison Matrix

| Source             | Frequency         | Historical Depth | Free Access  | Rate Limits   | OHLCV  | API Key |
| ------------------ | ----------------- | ---------------- | ------------ | ------------- | ------ | ------- |
| **GeckoTerminal**  | M1, H1, D1        | ~6 months        | ✅ Yes       | 30/min        | ✅ Yes | ❌ No   |
| **DEX Screener**   | M5, H1, H6, H24   | ❓ Unknown       | ✅ Yes       | Undocumented  | ❌ No  | ❌ No   |
| **CryptoCompare**  | M1 (7d), H1 (3y+) | Mixed            | 🔑 Free tier | 100k/mo, 50/s | ✅ Yes | ✅ Yes  |
| **Dune Analytics** | Custom SQL        | Full history     | 🔑 Free tier | 30/min        | ⚠️ DIY | ✅ Yes  |
| **The Graph**      | N/A               | N/A              | ❌ Sunset    | N/A           | N/A    | N/A     |
| **Bitquery**       | Custom GraphQL    | Full history     | 🔑 Free tier | 10k pts/mo    | ⚠️ DIY | ✅ Yes  |
| **Defined.fi**     | OHLCV available   | Full history     | 🔑 Free tier | TBD           | ✅ Yes | ✅ Yes  |
| **Covalent**       | DEX endpoints     | Full history     | 🔑 Free tier | 100k/mo       | ❌ No  | ✅ Yes  |

---

## Recommendations by Use Case

### Use Case 1: Short-term live trading (recent M1/M5 data)

**Best Option**: GeckoTerminal + DEX Screener

- GeckoTerminal for OHLCV candles (M1, limited history)
- DEX Screener for M5 volume/price snapshots

### Use Case 2: Feature engineering with 2022+ historical data

**Best Option**: Dune Analytics (with free API key)

- Custom SQL queries to fetch Uniswap V3 Swap events
- Aggregate into M1/M5/M15 candles via SQL
- Historical depth: Back to genesis block (May 2021 for Uni V3)

**Alternative**: CryptoCompare (H1 only)

- Hourly data back to 2021 (free tier with key)
- Not DEX-specific (mixed CEX/DEX), but covers major pairs

### Use Case 3: Real-time monitoring

**Best Option**: DEX Screener

- M5 volume/price change metrics
- No authentication required
- Good for live dashboards

### Use Case 4: Research/academic (no API key constraints)

**Options**:

1. GeckoTerminal (6 months history)
2. Manual event parsing via free RPC (Infura/Alchemy free tier)

---

## Technical Implementation Notes

### Recommended Data Collection Strategy

For a production ML pipeline requiring 2022+ historical data:

1. **Primary Source: Dune Analytics** (requires free API key)
   - Query Uniswap V3 swap events from `uniswap_v3_ethereum.Swap`
   - Aggregate into M1/M5/M15 buckets via SQL
   - Paginate results (API returns max ~100k rows per query)

2. **Fallback: CryptoCompare** (hourly only)
   - Use for H1 timeframe if M15 not critical
   - 3+ years history available
   - Requires free API key

3. **Real-time Updates: GeckoTerminal or DEX Screener**
   - Backfill recent data (last 6 months) from GeckoTerminal
   - Live updates from DEX Screener M5 snapshots

### Example: Dune Analytics Query for M15 OHLCV

```sql
SELECT
  date_trunc('minute', 15) AS timestamp,
  MIN(price_usd) AS open,
  MAX(price_usd) AS high,
  MIN(price_usd) AS low,
  MAX(price_usd) AS close,
  SUM(amount_usd) AS volume
FROM (
  SELECT
    block_time,
    amount0 * pool.token0_price_usd AS amount_usd,
    pool.token0_price_usd AS price_usd
  FROM uniswap_v3_ethereum.Swap
  WHERE pool = '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'
    AND block_time >= '2022-01-01'
)
GROUP BY 1
ORDER BY 1
```

_(Note: Actual schema may vary, requires Dune docs)_

---

## Cost Analysis

### Truly Free (No API Key)

- **GeckoTerminal**: 30 calls/min, unlimited (rate-limited)
- **DEX Screener**: Unknown limits, appears unlimited for reasonable use

### Free Tier (Requires Signup)

- **CryptoCompare**: 100k calls/month (~33k candles/day if fetching M1)
- **Dune Analytics**: 30 queries/min, ~1.3M queries/month
- **Covalent**: 100k credits/month
- **Bitquery**: 10k points/month

### Cost Estimate for 2022-2025 M15 Data

Assuming 3 years × 365 days × 96 intervals/day = **105,120 candles**

| Source           | API Calls Needed       | Free Tier Status | Feasibility      |
| ---------------- | ---------------------- | ---------------- | ---------------- |
| GeckoTerminal    | ~105 calls (1000/call) | ✅ Within limits | ❌ Only 6mo data |
| CryptoCompare M1 | ~105 calls (1000/call) | ✅ Within limits | ❌ Only 7d data  |
| CryptoCompare H1 | ~263 calls (2000/call) | ✅ Within limits | ✅ H1 feasible   |
| Dune Analytics   | 1-10 queries (SQL agg) | ✅ Within limits | ✅ Best option   |

---

## Unanswered Questions

1. **DEX Screener historical API**: Does it exist? Undocumented.
2. **GeckoTerminal pagination**: Can we fetch older than 6 months?
3. **Defined.fi free tier limits**: What are exact API quotas?
4. **Goldsky free tier**: Subgraph deployment limits?

---

## Conclusion

**For M15+ frequency with 2022+ history (free)**:

✅ **Recommended**: Dune Analytics (free API key required)
⚠️ **Alternative**: CryptoCompare (H1 only, free API key)
❌ **Not Viable**: GeckoTerminal (only 6 months), DEX Screener (no historical), The Graph (sunset)

**For no-API-key constraint**:

- Limited to recent data (6 months max via GeckoTerminal)
- Or real-time monitoring only (DEX Screener)

**Action Items**:

1. Sign up for Dune Analytics free API key
2. Test Dune query for Uniswap V3 swap event aggregation
3. Validate data quality and gaps
4. Consider CryptoCompare H1 as fallback for hourly timeframe
