# DEX Data API Endpoints - Quick Reference

## 1. GeckoTerminal (Recommended - No Auth)

### Base URL

```
https://api.geckoterminal.com/api/v2
```

### Rate Limits

- 30 calls/minute (documented)
- No authentication required

### Endpoints

#### Get OHLCV Candles (Minute)

```bash
GET /networks/{network}/pools/{pool_address}/ohlcv/minute?aggregate=1&limit=1000

# Example: WETH/USDC on Uniswap V3
curl "https://api.geckoterminal.com/api/v2/networks/eth/pools/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640/ohlcv/minute?limit=100"
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

#### Get OHLCV Candles (Hour)

```bash
GET /networks/{network}/pools/{pool_address}/ohlcv/hour?aggregate=1&limit=1000
```

#### Get Pool Info

```bash
GET /networks/{network}/pools/{pool_address}

# Example
curl "https://api.geckoterminal.com/api/v2/networks/eth/pools/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
```

#### Get Recent Trades

```bash
GET /networks/{network}/pools/{pool_address}/trades?limit=100
```

#### Search Pools

```bash
GET /search/pools?query={token_symbol}

# Example: Find WBTC pools
curl "https://api.geckoterminal.com/api/v2/search/pools?query=WBTC"
```

### Historical Depth

- Minute: ~17 hours (1,000 candle limit)
- Hour: ~41 days (1,000 candle limit)
- Day: ~6 months (184 days tested)

### Supported Networks

- `eth` - Ethereum
- `bsc` - Binance Smart Chain
- `polygon` - Polygon
- `arbitrum` - Arbitrum
- `optimism` - Optimism
- Many more...

---

## 2. DEX Screener (Real-time - No Auth)

### Base URL

```
https://api.dexscreener.com/latest
```

### Rate Limits

- Undocumented (appears generous)
- No authentication required

### Endpoints

#### Get Pair by Address

```bash
GET /dex/pairs/{chain}/{pair_address}

# Example: WETH/USDC on Uniswap V3
curl "https://api.dexscreener.com/latest/dex/pairs/ethereum/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
```

**Response Format**:

```json
{
  "pair": {
    "chainId": "ethereum",
    "dexId": "uniswap",
    "pairAddress": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
    "baseToken": { "symbol": "WETH", "address": "0xc02..." },
    "quoteToken": { "symbol": "USDC", "address": "0xa0b..." },
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
    },
    "liquidity": { "usd": 74108188.56 }
  }
}
```

#### Search Pairs

```bash
GET /dex/search?q={query}

# Example: Search for WBTC pairs
curl "https://api.dexscreener.com/latest/dex/search?q=WBTC"
```

#### Get Pairs by Token Address

```bash
GET /dex/tokens/{token_address}

# Example: All pairs for WETH
curl "https://api.dexscreener.com/latest/dex/tokens/0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
```

### Available Metrics

- Price USD (current)
- Volume: M5, H1, H6, H24
- Price Change %: M5, H1, H6, H24
- Liquidity USD
- FDV

### Limitations

- No OHLCV candles
- No historical endpoint (real-time only)
- Good for monitoring, not backtesting

---

## 3. CryptoCompare (Free Tier - Requires API Key)

### Base URL

```
https://min-api.cryptocompare.com/data/v2
```

### Authentication

```bash
# Add to headers or query param
?api_key=YOUR_API_KEY
```

### Free Tier Limits

- 100,000 calls/month
- 50 calls/second

### Sign Up

- https://www.cryptocompare.com/cryptopian/api-keys

### Endpoints

#### Get Minute OHLCV (7 days only)

```bash
GET /histominute?fsym={FROM}&tsym={TO}&limit={LIMIT}&toTs={TIMESTAMP}

# Example: ETH/USDC last 100 minutes
curl "https://min-api.cryptocompare.com/data/v2/histominute?fsym=ETH&tsym=USDC&limit=100"
```

#### Get Hourly OHLCV (3+ years)

```bash
GET /histohour?fsym={FROM}&tsym={TO}&limit={LIMIT}&toTs={TIMESTAMP}

# Example: ETH/USDC back to 2022
curl "https://min-api.cryptocompare.com/data/v2/histohour?fsym=ETH&tsym=USDC&limit=2000&toTs=1640995200"
```

#### Get Daily OHLCV

```bash
GET /histoday?fsym={FROM}&tsym={TO}&limit={LIMIT}

# Example: ETH/USDC daily
curl "https://min-api.cryptocompare.com/data/v2/histoday?fsym=ETH&tsym=USDC&limit=365"
```

**Response Format**:

```json
{
  "Response": "Success",
  "Data": {
    "Data": [
      {
        "time": 1762228800,
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

### Historical Depth

- Minute: **7 days only**
- Hour: **Back to October 2021** (3+ years)
- Day: Multi-year

### Limitations

- Not DEX-specific (aggregates CEX + DEX data)
- Minute data limited to 7 days
- Requires API key (free tier available)

---

## 4. Dune Analytics (Free Tier - Requires API Key)

### Base URL

```
https://api.dune.com/api/v1
```

### Authentication

```bash
# Add to headers
-H "X-Dune-API-Key: YOUR_API_KEY"
```

### Free Tier Limits

- 30 requests/minute
- Unlimited queries/month

### Sign Up

- https://dune.com/settings/api

### Workflow

#### 1. Execute Query

```bash
POST /query/{query_id}/execute

# Example: Execute Uniswap V3 swap query
curl -X POST "https://api.dune.com/api/v1/query/3238251/execute" \
  -H "X-Dune-API-Key: YOUR_API_KEY"
```

#### 2. Get Execution Status

```bash
GET /execution/{execution_id}/status

curl "https://api.dune.com/api/v1/execution/01HN7QWFD1A2ZJK3WZG9RHJX5Y/status" \
  -H "X-Dune-API-Key: YOUR_API_KEY"
```

#### 3. Get Results

```bash
GET /execution/{execution_id}/results

curl "https://api.dune.com/api/v1/execution/01HN7QWFD1A2ZJK3WZG9RHJX5Y/results" \
  -H "X-Dune-API-Key: YOUR_API_KEY"
```

### Example SQL Query for M15 OHLCV

```sql
WITH swaps AS (
  SELECT
    block_time,
    token0_amount,
    token1_amount,
    amount_usd
  FROM uniswap_v3_ethereum.Swap
  WHERE contract_address = 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640 -- WETH/USDC pool
    AND block_time >= TIMESTAMP '2022-01-01'
),
candles AS (
  SELECT
    DATE_TRUNC('minute', block_time) +
      INTERVAL '15 minute' * FLOOR(EXTRACT(MINUTE FROM block_time) / 15) AS candle_time,
    FIRST_VALUE(amount_usd) OVER (PARTITION BY DATE_TRUNC('minute', block_time) +
      INTERVAL '15 minute' * FLOOR(EXTRACT(MINUTE FROM block_time) / 15) ORDER BY block_time) AS open,
    MAX(amount_usd) OVER (PARTITION BY DATE_TRUNC('minute', block_time) +
      INTERVAL '15 minute' * FLOOR(EXTRACT(MINUTE FROM block_time) / 15)) AS high,
    MIN(amount_usd) OVER (PARTITION BY DATE_TRUNC('minute', block_time) +
      INTERVAL '15 minute' * FLOOR(EXTRACT(MINUTE FROM block_time) / 15)) AS low,
    LAST_VALUE(amount_usd) OVER (PARTITION BY DATE_TRUNC('minute', block_time) +
      INTERVAL '15 minute' * FLOOR(EXTRACT(MINUTE FROM block_time) / 15) ORDER BY block_time) AS close,
    SUM(amount_usd) OVER (PARTITION BY DATE_TRUNC('minute', block_time) +
      INTERVAL '15 minute' * FLOOR(EXTRACT(MINUTE FROM block_time) / 15)) AS volume
  FROM swaps
)
SELECT DISTINCT
  candle_time,
  open,
  high,
  low,
  close,
  volume
FROM candles
ORDER BY candle_time
```

### Historical Depth

- **Full blockchain history** (Uniswap V3: May 2021 onwards)
- Customizable aggregation (M1, M5, M15, H1, etc.)

### Advantages

- SQL flexibility for custom aggregations
- Full historical data
- Multiple DEXs and chains

### Limitations

- Requires API key (free tier available)
- Query execution can be slow (minutes for large ranges)
- Need to learn Dune's SQL dialect

---

## 5. Other Options (Require API Keys)

### Covalent

- **URL**: `https://api.covalenthq.com/v1`
- **Free Tier**: 100k credits/month
- **Endpoints**: `/1/xy=k/uniswap_v2/tokens/{address}/`
- **Sign Up**: https://www.covalenthq.com/platform/

### Bitquery

- **URL**: `https://graphql.bitquery.io`
- **Free Tier**: 10k points/month
- **Type**: GraphQL
- **Sign Up**: https://bitquery.io/

### Defined.fi

- **URL**: `https://api.defined.fi/graphql`
- **Type**: GraphQL with OHLCV endpoints
- **Sign Up**: https://www.defined.fi/

### Flipside Crypto

- **URL**: `https://api-v2.flipsidecrypto.xyz`
- **Type**: SQL-based queries
- **Sign Up**: https://flipsidecrypto.xyz/

---

## Comparison Summary

| Feature           | GeckoTerminal | DEX Screener  | CryptoCompare  | Dune Analytics    |
| ----------------- | ------------- | ------------- | -------------- | ----------------- |
| **Auth**          | None          | None          | API Key (free) | API Key (free)    |
| **M1 Data**       | ✅ 17h        | ❌            | ✅ 7d          | ✅ Custom SQL     |
| **M5 Data**       | ❌            | ✅ Snapshots  | ❌             | ✅ Custom SQL     |
| **M15 Data**      | ❌            | ❌            | ❌             | ✅ Custom SQL     |
| **H1 Data**       | ✅ ~41d       | ✅ Aggregated | ✅ 3y+         | ✅ Custom SQL     |
| **2022+ History** | ❌            | ❌            | ✅ H1 only     | ✅ Full           |
| **Rate Limit**    | 30/min        | Unknown       | 100k/mo        | 30/min            |
| **OHLCV**         | ✅            | ❌            | ✅             | ⚠️ DIY via SQL    |
| **Best For**      | Recent M1     | Real-time M5  | Hourly 2022+   | Custom historical |

---

## Recommended Approach

### For Feature Engineering with 2022+ Data at M15 Frequency

**Strategy**: Hybrid approach

1. **Historical Backfill (2022-2024)**: Dune Analytics
   - Sign up for free API key
   - Query Uniswap V3 swap events
   - Aggregate to M15 candles via SQL
   - Export to Parquet/CSV

2. **Recent Data (Last 6 months)**: GeckoTerminal
   - Fetch M1 candles (no auth)
   - Resample to M15 locally
   - Merge with Dune data

3. **Live Updates**: DEX Screener or GeckoTerminal
   - Poll every 5-15 minutes
   - Append new candles to dataset

### Python Example

```python
import requests
import pandas as pd
from datetime import datetime, timedelta

# 1. Fetch from GeckoTerminal (last 6 months, M1)
def fetch_geckoterminal_ohlcv(pool_address, network="eth", limit=1000):
    url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/minute"
    params = {"aggregate": 1, "limit": limit}
    response = requests.get(url, params=params)
    data = response.json()

    candles = data["data"]["attributes"]["ohlcv_list"]
    df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df.set_index("timestamp", inplace=True)
    return df

# 2. Resample to M15
pool = "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
df_m1 = fetch_geckoterminal_ohlcv(pool)
df_m15 = df_m1.resample("15min").agg({
    "open": "first",
    "high": "max",
    "low": "min",
    "close": "last",
    "volume": "sum"
})

print(df_m15.head())
```

---

## Key Takeaways

1. **No truly free source** provides both M15+ frequency AND 2022+ history without API key
2. **Best free option**: Dune Analytics (requires signup, but generous free tier)
3. **No-auth option**: GeckoTerminal (limited to ~6 months history)
4. **For production ML pipelines**: Sign up for Dune + CryptoCompare free tiers
5. **For quick prototyping**: GeckoTerminal M1 → resample to M15 locally

---

## Additional Resources

- **GeckoTerminal Docs**: https://www.geckoterminal.com/dex-api
- **Dune Docs**: https://dune.com/docs/api/
- **CryptoCompare API**: https://min-api.cryptocompare.com/documentation
- **The Graph Decentralized Network**: https://thegraph.com/docs/en/querying/querying-the-graph/
- **Uniswap V3 Subgraph Schema**: https://github.com/Uniswap/v3-subgraph

---

**Last Updated**: 2025-11-04
