# Alternative L1 Blockchain Free High-Frequency Data Research

**Research Date**: 2025-11-03
**Research Goal**: Find free APIs/datasets with M1/M5/M15 frequency going back to 2022 for alternative L1 blockchains

---

## Executive Summary

**PRIMARY FINDING**: Binance and Coinbase provide free, high-frequency (1-minute) OHLCV data for major alt-L1 tokens going back to 2022 **with no authentication required**.

**Coverage**:

- ✅ 1-minute (M1) granularity
- ✅ 5-minute (M5) granularity
- ✅ 15-minute (M15) granularity
- ✅ Historical depth to 2022-01-01 (3+ years)
- ✅ 7 major alt-L1 blockchains tested and verified

---

## Part 1: OHLCV Price Data (Trading Data)

### 🏆 Top Recommendation: Binance Public API

**Base URL**: `https://api.binance.com/api/v3`

**Authentication**: ❌ None required for public market data

**Rate Limits**:

- Weight-based system: 1200 weight per minute
- Klines endpoint weight: 10 (for limit=1000)
- Effective rate: ~120 requests/minute (2/second)

**Supported Alt-L1 Tokens** (all verified with 2022 data):

| Blockchain | Symbol   | First Data Point    | Status       |
| ---------- | -------- | ------------------- | ------------ |
| Solana     | SOLUSDT  | 2021-12-31 16:00:00 | ✅ Available |
| Avalanche  | AVAXUSDT | 2021-12-31 16:00:00 | ✅ Available |
| Cardano    | ADAUSDT  | 2021-12-31 16:00:00 | ✅ Available |
| Polkadot   | DOTUSDT  | 2021-12-31 16:00:00 | ✅ Available |
| Cosmos     | ATOMUSDT | 2021-12-31 16:00:00 | ✅ Available |
| Near       | NEARUSDT | 2021-12-31 16:00:00 | ✅ Available |
| Algorand   | ALGOUSDT | 2021-12-31 16:00:00 | ✅ Available |
| Tezos      | XTZUSDT  | 2021-12-31 16:00:00 | ✅ Available |

**Intervals Supported**:

- `1m` - 1 minute (tested ✅)
- `3m` - 3 minutes
- `5m` - 5 minutes (tested ✅)
- `15m` - 15 minutes (tested ✅)
- `30m` - 30 minutes
- `1h` - 1 hour
- `2h`, `4h`, `6h`, `8h`, `12h` - Multi-hour
- `1d`, `3d`, `1w`, `1M` - Daily/Weekly/Monthly

**Data Format**: JSON array of OHLCV candles

```json
[
  [
    1640995200000, // Open time (Unix timestamp ms)
    "170.01000000", // Open price
    "170.22000000", // High price
    "169.93000000", // Low price
    "170.14000000", // Close price
    "810.27000000", // Volume (base asset)
    1640995259999, // Close time
    "137785.37510000", // Volume (quote asset)
    174, // Number of trades
    "459.80000000", // Taker buy base volume
    "78194.16870000", // Taker buy quote volume
    "0" // Ignore
  ]
]
```

**Example curl Commands**:

```bash
# Get latest 1-minute candles for Solana
curl "https://api.binance.com/api/v3/klines?symbol=SOLUSDT&interval=1m&limit=100"

# Get historical data from specific date (2022-01-01)
curl "https://api.binance.com/api/v3/klines?symbol=AVAXUSDT&interval=1m&startTime=1640995200000&limit=1000"

# Get 5-minute candles
curl "https://api.binance.com/api/v3/klines?symbol=DOTUSDT&interval=5m&limit=500"

# Get 15-minute candles with date range
curl "https://api.binance.com/api/v3/klines?symbol=ATOMUSDT&interval=15m&startTime=1640995200000&endTime=1641081600000"
```

**Limitations**:

- Max 1000 candles per request (use pagination for larger ranges)
- No sub-minute granularity
- Rate limiting on excessive requests

---

### 🥈 Alternative: Coinbase Exchange API

**Base URL**: `https://api.exchange.coinbase.com`

**Authentication**: ❌ None required for public market data

**Rate Limits**:

- Public endpoints: 10 requests/second per IP
- Burst capacity: up to 15 requests/second
- Max 300 candles per request

**Supported Alt-L1 Tokens** (verified with 2022 data):

| Blockchain | Symbol   | First Data Point    | Status       |
| ---------- | -------- | ------------------- | ------------ |
| Solana     | SOL-USD  | 2021-12-31 16:00:00 | ✅ Available |
| Avalanche  | AVAX-USD | 2021-12-31 16:00:00 | ✅ Available |
| Cardano    | ADA-USD  | 2021-12-31 16:00:00 | ✅ Available |
| Polkadot   | DOT-USD  | 2021-12-31 16:00:00 | ✅ Available |
| Cosmos     | ATOM-USD | 2021-12-31 16:00:00 | ✅ Available |
| Algorand   | ALGO-USD | 2021-12-31 16:00:00 | ✅ Available |
| Tezos      | XTZ-USD  | 2021-12-31 16:00:00 | ✅ Available |
| Near       | NEAR-USD | ❌ Not available    | Not listed   |

**Granularity Options** (in seconds):

- `60` - 1 minute (M1) ✅
- `300` - 5 minutes (M5) ✅
- `900` - 15 minutes (M15) ✅
- `3600` - 1 hour
- `21600` - 6 hours
- `86400` - 1 day

**Data Format**: JSON array `[timestamp, low, high, open, close, volume]`

```json
[
  [
    1640998800, // Unix timestamp (seconds)
    172.28, // Low
    172.44, // High
    172.4, // Open
    172.28, // Close
    483.46 // Volume
  ]
]
```

**Example curl Commands**:

```bash
# Get 1-minute candles for Solana
curl "https://api.exchange.coinbase.com/products/SOL-USD/candles?granularity=60&start=2022-01-01T00:00:00Z&end=2022-01-01T05:00:00Z"

# Get 5-minute candles for Avalanche
curl "https://api.exchange.coinbase.com/products/AVAX-USD/candles?granularity=300&start=2022-01-01T00:00:00Z&end=2022-01-02T00:00:00Z"

# Get 15-minute candles for Cardano
curl "https://api.exchange.coinbase.com/products/ADA-USD/candles?granularity=900"
```

**Limitations**:

- Max 300 candles per request (smaller than Binance)
- Slightly fewer alt-L1 tokens than Binance
- Start/end time required for historical data

---

### 🥉 Honorable Mention: CryptoCompare API

**Base URL**: `https://min-api.cryptocompare.com`

**Authentication**: ⚠️ API key required (free tier available)

**Rate Limits**:

- Free tier: Limited total calls
- Max 2000 data points per request

**Coverage**: Wide range of alt-L1s including all major ones

**Intervals**: `histominute` endpoint provides minute-level data

**Limitation**: Free tier may be restrictive for bulk historical downloads

---

## Part 2: On-Chain Network Metrics (Block/Transaction Data)

### Polkadot - Subscan API

**Base URL**: `https://polkadot.api.subscan.io`

**Authentication**: ❌ None required for basic queries

**Data Available**:

- Block-level data (every ~6 seconds)
- Transaction counts per block
- Network metadata
- Historical data back to genesis (2020)

**Example curl**:

```bash
# Get network metadata
curl -X POST "https://polkadot.api.subscan.io/api/scan/metadata" \
  -H "Content-Type: application/json" \
  -d '{}'

# Get recent blocks
curl -X POST "https://polkadot.api.subscan.io/api/v2/scan/blocks" \
  -H "Content-Type: application/json" \
  -d '{"row": 10, "page": 0}'
```

**Data Frequency**: Block-level (~6 second granularity)

**Historical Depth**: From network genesis (May 2020)

---

### Tezos - TzKT API

**Base URL**: `https://api.tzkt.io`

**Authentication**: ❌ None required

**Data Available**:

- Block-level data (every ~30-60 seconds)
- Daily statistics (supply, fees, etc.)
- Account operations
- Historical data back to genesis

**Example curl**:

```bash
# Get latest block
curl "https://api.tzkt.io/v1/head"

# Get daily statistics from 2022
curl "https://api.tzkt.io/v1/statistics/daily?limit=100&sort.desc=date"

# Get specific blocks from 2022
curl "https://api.tzkt.io/v1/blocks?timestamp.ge=2022-01-01&limit=100"
```

**Data Frequency**: Block-level (~30-60 second granularity)

**Historical Depth**: From network genesis (June 2018), verified 2022-01-01 ✅

---

### NEAR - NearBlocks API

**Base URL**: `https://api.nearblocks.io`

**Authentication**: ❌ None required

**Data Available**:

- Daily transaction counts
- Daily price data
- Block counts
- Network statistics

**Example curl**:

```bash
# Get network stats
curl "https://api.nearblocks.io/v1/stats"

# Get historical charts (daily granularity)
curl "https://api.nearblocks.io/v1/charts?start_date=2022-01-01&end_date=2022-12-31"
```

**Data Frequency**: Daily aggregates

**Historical Depth**: From network launch (July 2020), verified 2022-01-01 ✅

---

### Avalanche - Snowtrace API

**Base URL**: `https://api.snowtrace.io`

**Authentication**: ❌ None required for basic queries (optional API key for higher limits)

**Data Available**:

- Daily transaction counts
- Network statistics
- Block data
- Account data

**Example curl**:

```bash
# Get AVAX price
curl "https://api.snowtrace.io/api?module=stats&action=ethprice"

# Get daily transaction counts from 2022
curl "https://api.snowtrace.io/api?module=stats&action=dailytx&startdate=2022-01-01&enddate=2022-12-31&sort=asc"
```

**Data Frequency**: Daily aggregates

**Historical Depth**: From C-Chain launch (Sep 2020), verified 2022-01-01 ✅

---

### Algorand - AlgoNode Indexer

**Base URL**: `https://mainnet-idx.algonode.cloud`

**Authentication**: ❌ None required

**Data Available**:

- Block-level data
- Transaction data
- Account information
- Application state

**Example curl**:

```bash
# Get indexer health
curl "https://mainnet-idx.algonode.cloud/health"

# Get specific block
curl "https://mainnet-idx.algonode.cloud/v2/blocks/19000000"

# Get account transactions
curl "https://mainnet-idx.algonode.cloud/v2/accounts/[ADDRESS]/transactions"
```

**Data Frequency**: Block-level (~4.5 second granularity)

**Historical Depth**: From mainnet launch (June 2019)

---

## Part 3: API Comparison Matrix

| Blockchain | OHLCV Source     | Min Freq | On-Chain Source | Min Freq      | 2022 Data |
| ---------- | ---------------- | -------- | --------------- | ------------- | --------- |
| Solana     | Binance/Coinbase | 1m       | -               | -             | ✅        |
| Avalanche  | Binance/Coinbase | 1m       | Snowtrace       | Daily         | ✅        |
| Cardano    | Binance/Coinbase | 1m       | Blockfrost\*    | Block         | ✅        |
| Polkadot   | Binance/Coinbase | 1m       | Subscan         | Block (~6s)   | ✅        |
| Cosmos     | Binance/Coinbase | 1m       | LCD API         | Block (~6s)   | ✅        |
| Near       | Binance          | 1m       | NearBlocks      | Daily         | ✅        |
| Algorand   | Binance/Coinbase | 1m       | AlgoNode        | Block (~4.5s) | ✅        |
| Tezos      | Binance/Coinbase | 1m       | TzKT            | Block (~30s)  | ✅        |

\*Blockfrost requires free API key

---

## Part 4: Recommended Data Collection Strategy

### For Feature Engineering (ML/Trading)

**Primary Pipeline**:

1. **Price/Volume Data**: Use Binance API
   - 1-minute granularity
   - No authentication required
   - Wide coverage of alt-L1s
   - Reliable uptime

2. **On-Chain Metrics**: Use blockchain-specific explorers
   - Polkadot: Subscan (block-level, ~6s)
   - Tezos: TzKT (block-level, ~30s)
   - Avalanche: Snowtrace (daily aggregates)
   - Near: NearBlocks (daily aggregates)
   - Algorand: AlgoNode (block-level, ~4.5s)

**Data Fusion Approach**:

```python
# Example: Combine 1m OHLCV with hourly on-chain metrics
import pandas as pd

# Step 1: Fetch OHLCV from Binance (1m)
df_ohlcv = fetch_binance_klines("AVAXUSDT", "1m", start="2022-01-01")

# Step 2: Fetch on-chain data from Snowtrace (daily)
df_onchain = fetch_snowtrace_daily_tx("2022-01-01", "2022-12-31")

# Step 3: Resample on-chain to hourly (interpolate or forward-fill)
df_onchain_hourly = df_onchain.resample('1H').ffill()

# Step 4: Align and merge
df_merged = df_ohlcv.join(df_onchain_hourly.resample('1T').ffill())
```

---

## Part 5: Rate Limit Management

### Binance API

**Strategy**:

```python
import time

# Conservative approach: 1 request per second
def fetch_with_rate_limit(symbol, interval, start_time, end_time):
    current_time = start_time
    all_data = []

    while current_time < end_time:
        # Fetch 1000 candles (max per request)
        data = fetch_klines(symbol, interval, current_time, limit=1000)
        all_data.extend(data)

        # Update start time for next batch
        if len(data) == 1000:
            current_time = data[-1][0] + 60000  # Move to next minute
        else:
            break

        # Rate limit: 1 request/second
        time.sleep(1)

    return all_data
```

### Coinbase API

**Strategy**:

```python
# Coinbase allows 10 req/s, but conservative 5 req/s
def fetch_coinbase_candles(product, granularity, start, end):
    # Max 300 candles per request
    # For 1m granularity: 300 minutes = 5 hours per request

    chunks = split_date_range(start, end, hours=5)
    all_data = []

    for chunk_start, chunk_end in chunks:
        data = fetch_candles(product, granularity, chunk_start, chunk_end)
        all_data.extend(data)
        time.sleep(0.2)  # 5 req/s

    return all_data
```

---

## Part 6: Sample Implementation Scripts

### Test Script: Binance Historical Download

```bash
#!/bin/bash
# File: /tmp/altl1-research/download_binance_historical.sh

SYMBOL="AVAXUSDT"
INTERVAL="1m"
START_TIME=1640995200000  # 2022-01-01 00:00:00 UTC
OUTPUT_FILE="avax_1m_historical.json"

echo "Downloading $SYMBOL $INTERVAL data from $(date -r $((START_TIME/1000)))"

curl -s "https://api.binance.com/api/v3/klines?symbol=$SYMBOL&interval=$INTERVAL&startTime=$START_TIME&limit=1000" \
  | jq '.' > "$OUTPUT_FILE"

echo "Downloaded $(jq 'length' $OUTPUT_FILE) candles to $OUTPUT_FILE"
```

### Python Script: Multi-Chain Data Collection

```python
#!/usr/bin/env python3
# /// script
# dependencies = ["requests", "pandas"]
# ///

import requests
import pandas as pd
from datetime import datetime

def fetch_binance_klines(symbol, interval, start_time_ms, limit=1000):
    """Fetch OHLCV data from Binance."""
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time_ms,
        "limit": limit
    }

    response = requests.get(url, params=params)
    data = response.json()

    # Convert to DataFrame
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    # Convert to numeric
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col])

    return df

# Example usage
if __name__ == "__main__":
    symbols = ["SOLUSDT", "AVAXUSDT", "ADAUSDT", "DOTUSDT"]
    start_time = int(datetime(2022, 1, 1).timestamp() * 1000)

    for symbol in symbols:
        print(f"Fetching {symbol}...")
        df = fetch_binance_klines(symbol, "1m", start_time, limit=100)
        print(f"  Retrieved {len(df)} rows")
        print(f"  First timestamp: {df.index[0]}")
        print(f"  Last timestamp: {df.index[-1]}")
        print()
```

---

## Part 7: Key Findings Summary

### ✅ CONFIRMED CAPABILITIES

1. **M1 (1-minute) Frequency**: Available for all major alt-L1s via Binance/Coinbase
2. **M5 (5-minute) Frequency**: Available for all major alt-L1s via Binance/Coinbase
3. **M15 (15-minute) Frequency**: Available for all major alt-L1s via Binance/Coinbase
4. **Historical Depth**: Data goes back to 2022-01-01 (verified for 8 blockchains)
5. **No Authentication**: Binance and Coinbase public APIs require no API keys
6. **Rate Limits**: Reasonable limits (Binance: 120 req/min, Coinbase: 600 req/min)

### 🎯 BEST PRACTICES

1. **Use Binance as primary source** for OHLCV data (better limits, more tokens)
2. **Use Coinbase as backup** or for tokens not on Binance
3. **Supplement with on-chain data** from blockchain-specific explorers
4. **Implement retry logic** and exponential backoff for production systems
5. **Cache data locally** to avoid redundant API calls
6. **Respect rate limits** to avoid IP bans

### ⚠️ LIMITATIONS

1. **No sub-minute data**: Finest granularity is 1-minute
2. **Pagination required**: For large historical ranges (>1000 candles)
3. **Price data only**: OHLCV reflects exchange trading, not blockchain state
4. **Exchange-specific**: Data from CEX may differ slightly from DEX prices
5. **Coverage gaps**: Some alt-L1s may have listing date after 2022-01-01

---

## Part 8: Validation Test Results

All test results stored in `/tmp/altl1-research/`

### Files Created:

- `alt_l1_inventory.md` - Initial blockchain inventory
- `solana_binance_1m.json` - Binance Solana 1m test
- `solana_coinbase_1m.json` - Coinbase Solana 1m test
- `avalanche_snowtrace_test.json` - Snowtrace API test
- `tezos_tzkt_test.json` - TzKT API test
- `near_nearblocks_test.json` - NearBlocks API test
- `polkadot_subscan_test.json` - Subscan API test

### Test Scripts:

- `test_binance_altl1s.sh` - Multi-token Binance verification
- `test_coinbase_altl1s.sh` - Multi-token Coinbase verification

---

## Conclusion

**FREE HIGH-FREQUENCY DATA IS READILY AVAILABLE** for all major alternative L1 blockchains with:

- ✅ M1/M5/M15 granularity via Binance/Coinbase
- ✅ Historical depth back to 2022 (3+ years)
- ✅ No authentication required
- ✅ Reasonable rate limits for research/development
- ✅ Block-level on-chain metrics from native explorers

**PRIMARY RECOMMENDATION**: Use Binance API as the main data source for OHLCV with 1-minute frequency, supplemented by blockchain-specific explorer APIs for on-chain network metrics.
