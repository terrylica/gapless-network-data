# DEX/DeFi On-Chain Data Research

**Research Date**: 2025-11-04
**Researcher**: Claude (Sonnet 4.5)
**Objective**: Identify free high-frequency DEX data sources with M15+ frequency and 2022+ historical depth

---

## Quick Links

📊 **[FINDINGS_SUMMARY.md](FINDINGS_SUMMARY.md)** - Complete research findings and recommendations

📚 **[API_ENDPOINTS_REFERENCE.md](API_ENDPOINTS_REFERENCE.md)** - Detailed API documentation and code examples

🧪 **[test_recommended_sources.sh](test_recommended_sources.sh)** - Quick validation script

---

## Executive Summary

### Key Finding

**No truly free DEX data source provides both M15+ frequency AND 2022+ historical depth without API key.**

### Recommended Solutions

#### ✅ For Production ML Pipelines (2022+ data, M15 frequency)

**Primary**: Dune Analytics (free API key required)

- SQL queries on indexed blockchain data
- Full historical depth (back to 2021 for Uniswap V3)
- 30 requests/min free tier
- Custom aggregations (M1, M5, M15, etc.)

**Fallback**: CryptoCompare (free API key required)

- Hourly data back to 2021
- 100k calls/month free tier
- Not DEX-specific (mixed CEX/DEX)

#### ⚠️ For Recent Data Only (No API Key)

**GeckoTerminal** - Best for recent high-frequency

- M1 OHLCV candles
- ~6 months historical depth
- 30 calls/min
- No authentication

**DEX Screener** - Best for real-time monitoring

- M5 volume/price snapshots
- Real-time only (no historical)
- No authentication

---

## Research Artifacts

### Documentation

- **FINDINGS_SUMMARY.md** - 12KB - Complete analysis with comparison matrix
- **API_ENDPOINTS_REFERENCE.md** - 11KB - API specs, endpoints, code examples
- **README.md** - This file

### Test Scripts

- **test_recommended_sources.sh** - Quick test of top 4 sources
- **geckoterminal_api.sh** - GeckoTerminal comprehensive testing
- **dexscreener_detailed.sh** - DEX Screener feature analysis
- **blockchain_indexers.sh** - Alchemy, QuickNode, Moralis tests
- **dex_aggregators.sh** - 1inch, 0x, ParaSwap tests
- **historical_providers.sh** - Dune, Flipside, Goldsky research
- **market_data_apis.sh** - CryptoCompare, CoinCap, Messari tests
- **test_dune_flipside.sh** - Analytics platform testing
- **test_thegraph_decentralized.sh** - Graph network migration check
- **test_dex_apis.sh** - Initial broad API survey
- **uniswap_v3_test.sh** - Uniswap subgraph testing

---

## Data Sources Evaluated

### ✅ Viable (with constraints)

1. **GeckoTerminal** - M1 OHLCV, 6 months, no auth
2. **DEX Screener** - M5 snapshots, real-time, no auth
3. **Dune Analytics** - Custom SQL, full history, free API key
4. **CryptoCompare** - H1 OHLCV, 3+ years, free API key

### 🔑 Viable (requires paid/registration)

5. **Covalent** - 100k credits/month free
6. **Bitquery** - 10k points/month free
7. **Defined.fi** - Free tier available
8. **Flipside Crypto** - Free tier available

### ❌ Not Viable

9. **The Graph Hosted Service** - Deprecated (301 redirects)
10. **Uniswap Subgraph** - Migrated to decentralized (requires key)
11. **DEX Aggregators** (1inch, 0x, ParaSwap) - No historical data
12. **Blockchain Node Providers** (Alchemy, QuickNode) - No DEX indexing

---

## Comparison Matrix

| Source             | Frequency         | Historical Depth | Free Access  | Rate Limits  | OHLCV  | Auth   |
| ------------------ | ----------------- | ---------------- | ------------ | ------------ | ------ | ------ |
| **GeckoTerminal**  | M1, H1, D1        | ~6 months        | ✅ Yes       | 30/min       | ✅ Yes | ❌ No  |
| **DEX Screener**   | M5, H1, H24       | Real-time only   | ✅ Yes       | Undocumented | ❌ No  | ❌ No  |
| **CryptoCompare**  | M1 (7d), H1 (3y+) | Mixed            | 🔑 Free tier | 100k/mo      | ✅ Yes | ✅ Yes |
| **Dune Analytics** | Custom SQL        | Full history     | 🔑 Free tier | 30/min       | ⚠️ DIY | ✅ Yes |

---

## Quick Start

### 1. Test Available Sources (No Auth)

```bash
cd /tmp/defi-research
./test_recommended_sources.sh
```

### 2. Test GeckoTerminal (M1 OHLCV)

```bash
# Get last 100 minute candles for WETH/USDC
curl "https://api.geckoterminal.com/api/v2/networks/eth/pools/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640/ohlcv/minute?limit=100" | jq .
```

### 3. Test DEX Screener (M5 Snapshots)

```bash
# Get current M5 volume and price change
curl "https://api.dexscreener.com/latest/dex/pairs/ethereum/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640" | jq '.pair.volume, .pair.priceChange'
```

### 4. Test CryptoCompare (H1 Historical)

```bash
# Get last 100 hourly candles for ETH/USDC
curl "https://min-api.cryptocompare.com/data/v2/histohour?fsym=ETH&tsym=USDC&limit=100" | jq .
```

---

## Implementation Recommendations

### Hybrid Data Collection Strategy

**For ML pipelines requiring M15 data from 2022-2025:**

```
Phase 1: Historical Backfill (2022-2024)
├─ Source: Dune Analytics (free API key)
├─ Method: SQL query on Uniswap V3 Swap events
├─ Aggregation: GROUP BY 15-minute intervals
└─ Output: ~105k candles (3 years × 365 days × 96 intervals/day)

Phase 2: Recent Data (Last 6 months)
├─ Source: GeckoTerminal (no auth)
├─ Method: Fetch M1 candles, resample to M15
├─ Rate: 30 calls/min (sufficient for backfill)
└─ Merge with Phase 1 data

Phase 3: Live Updates (Ongoing)
├─ Source: GeckoTerminal or DEX Screener
├─ Frequency: Poll every 5-15 minutes
└─ Append to existing dataset
```

### Python Example

```python
import requests
import pandas as pd

# Fetch M1 from GeckoTerminal
url = "https://api.geckoterminal.com/api/v2/networks/eth/pools/{pool}/ohlcv/minute"
response = requests.get(url, params={"limit": 1000})
candles = response.json()["data"]["attributes"]["ohlcv_list"]

# Convert to DataFrame and resample to M15
df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
df.set_index("timestamp", inplace=True)

df_m15 = df.resample("15min").agg({
    "open": "first",
    "high": "max",
    "low": "min",
    "close": "last",
    "volume": "sum"
})
```

---

## Cost Analysis

### Truly Free (No Registration)

- **GeckoTerminal**: 30/min, unlimited monthly
- **DEX Screener**: Undocumented limits

### Free Tier (Registration Required)

- **CryptoCompare**: 100k calls/month
- **Dune Analytics**: 30 queries/min
- **Covalent**: 100k credits/month
- **Bitquery**: 10k points/month

### Cost for 2022-2025 M15 Data (105k candles)

| Source           | API Calls | Free Tier | Feasible?      |
| ---------------- | --------- | --------- | -------------- |
| GeckoTerminal M1 | ~105      | ✅ Yes    | ❌ Only 6mo    |
| CryptoCompare M1 | ~105      | ✅ Yes    | ❌ Only 7d     |
| CryptoCompare H1 | ~263      | ✅ Yes    | ✅ 3y+ data    |
| Dune Analytics   | 1-10      | ✅ Yes    | ✅ Best option |

---

## Unanswered Questions

1. Does DEX Screener have undocumented historical endpoint?
2. Can GeckoTerminal fetch older than 6 months via pagination?
3. What are Defined.fi's exact free tier limits?
4. What is Goldsky's subgraph deployment quota?

---

## Next Steps

### For Immediate Use

1. Start with GeckoTerminal for recent data (no auth)
2. Use DEX Screener for real-time monitoring

### For Production Pipeline

1. **Sign up** for Dune Analytics free API key
2. **Test** SQL query for Uniswap V3 swap event aggregation
3. **Validate** data quality and gap detection
4. **Consider** CryptoCompare as H1 fallback

### For Research

1. Investigate Defined.fi free tier capabilities
2. Test Goldsky subgraph hosting
3. Explore Subsquid as Graph alternative

---

## Additional Resources

- **GeckoTerminal API Docs**: https://www.geckoterminal.com/dex-api
- **Dune Analytics Docs**: https://dune.com/docs/api/
- **CryptoCompare API Docs**: https://min-api.cryptocompare.com/documentation
- **Uniswap V3 Subgraph**: https://github.com/Uniswap/v3-subgraph
- **The Graph Docs**: https://thegraph.com/docs/en/

---

## Research Methodology

**Approach**: Dynamic TODO-driven exploration

1. Started with Uniswap V3 subgraph (discovered sunset)
2. Tested DEX aggregator APIs (found real-time only)
3. Evaluated analytics platforms (Dune, Flipside, Bitquery)
4. Checked market data APIs (CryptoCompare, CoinGecko)
5. Validated GeckoTerminal and DEX Screener (viable)

**Tools Used**:

- `curl` for API testing
- `jq` for JSON parsing
- Bash scripts for repeatability
- Empirical validation over documentation

**Total APIs Tested**: 20+
**Viable Sources Found**: 4 (2 no-auth, 2 free-tier)

---

**Repository**: /tmp/defi-research/
**Last Updated**: 2025-11-04 04:51 UTC
