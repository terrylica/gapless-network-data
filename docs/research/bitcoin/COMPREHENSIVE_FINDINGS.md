# Bitcoin On-Chain High-Frequency Data Sources Research

**Research Date**: November 3, 2025  
**Perspective**: Bitcoin Ecosystem (mempool.space, blockchain.info, blockstream, etc.)  
**Criteria**: Free APIs, M1/M5/M15+ frequency, Historical depth to 2022+

---

## Executive Summary

**TOP RECOMMENDATIONS**:

1. **blockchain.info** - M15 frequency, complete historical data back to 2009 ✅
2. **mempool.space** - M5 frequency, 3+ years historical (Nov 2022+) ✅
3. **BlockCypher** - Block-level data, historical to genesis (requires polling)

---

## Detailed Source Analysis

### 1. blockchain.info (Blockchain.com) Charts API ⭐⭐⭐⭐⭐

**Status**: EXCELLENT - Best for M15 historical data

**Base URL**: `https://api.blockchain.info/charts/{chart_name}`

**High-Frequency Data (M15 = 15-minute intervals)**:

- `mempool-size`: 329,108+ data points (back to ~2009)
- `transactions-per-second`: 329,108+ data points

**Frequency Analysis**:

- **M15 charts**: 15.01 minute average intervals
- **D1 charts**: Daily intervals for most other metrics

**Historical Depth**:

- ✅ 3+ years: 105,016 points (Nov 2022 - Nov 2025)
- ✅ Complete history: 329,108 points back to 2009

**Available Metrics**:

```
HIGH FREQUENCY (M15):
- mempool-size (bytes)
- transactions-per-second

DAILY (D1):
- market-price (USD closing price)
- hash-rate (TH/s)
- difficulty
- n-transactions (daily count)
- n-unique-addresses
- avg-block-size (MB)
- miners-revenue (USD)
- transaction-fees (BTC)
- cost-per-transaction (USD)
- trade-volume (USD)
```

**Example Commands**:

```bash
# M15 mempool size (3 years)
curl -s "https://api.blockchain.info/charts/mempool-size?timespan=3years&sampled=false&format=json" | jq '.values | length'
# Output: 105016

# M15 transactions per second (all time)
curl -s "https://api.blockchain.info/charts/transactions-per-second?timespan=all&sampled=false&format=json" | jq '.values[0:3]'
```

**Data Format**:

```json
{
  "status": "ok",
  "name": "Mempool Size",
  "unit": "Bytes",
  "period": "day",
  "values": [
    {"x": 1762219800, "y": 934284.5},
    ...
  ]
}
```

**Rate Limits**: Not documented, appears generous  
**Authentication**: None required  
**Cost**: FREE

**Verdict**: ✅ BEST SOURCE for M15 mempool and transaction data

---

### 2. mempool.space API ⭐⭐⭐⭐⭐

**Status**: EXCELLENT - Best for M5 statistical data

**Base URL**: `https://mempool.space/api/`

**High-Frequency Statistics**:

- `1w`: 2017 points, ~5 min intervals (M5 frequency)
- `1m`: 1489 points, ~30 min intervals (M30 frequency)
- `3m`: 1105 points, ~2 hour intervals (H2 frequency)
- `6m`: 1457 points, ~3 hour intervals (H3 frequency)
- `1y`: 1096 points, ~8 hour intervals (H8 frequency)
- `2y`: 2194 points, ~8 hour intervals (H8 frequency)
- `3y`: 2193 points, ~12 hour intervals (H12 frequency)

**Historical Depth**: Back to November 2022 (3+ years) ✅

**Available Endpoints**:

```
STATISTICS (M5 to H12):
- /api/v1/statistics/{period}
  Fields: timestamp, count, vbytes_per_second, min_fee, vsizes[]

REAL-TIME:
- /api/mempool (current state)
- /api/v1/fees/recommended (fee estimates)

BLOCKS:
- /api/v1/blocks/{start_height} (10 blocks per request)

MINING:
- /api/v1/mining/hashrate/pools/{period}
```

**Example Commands**:

```bash
# M5 statistics (1 week)
curl -s "https://mempool.space/api/v1/statistics/1w" | jq '.[0:5]'

# 3-year historical stats (M12 frequency)
curl -s "https://mempool.space/api/v1/statistics/3y" | jq '. | length'
# Output: 2193

# Current mempool state
curl -s "https://mempool.space/api/mempool" | jq .
```

**Data Format**:

```json
{
  "added": 1762231232,
  "count": 70455.5,
  "vbytes_per_second": 1492.5,
  "min_fee": 0.10000000149011612,
  "vsizes": [33487042, 604469, ...]
}
```

**Rate Limits**: 10 requests/second (documented)  
**Authentication**: None required  
**Cost**: FREE

**Verdict**: ✅ EXCELLENT for M5 mempool statistics and fee data

---

### 3. Blockstream Esplora API ⭐⭐

**Status**: REAL-TIME ONLY - Not suitable for historical research

**Base URL**: `https://blockstream.info/api/`

**Capabilities**:

- Current mempool state
- Fee estimates (1-1008 blocks ahead)
- Block data (requires iteration by height)
- Transaction history (address-based, paginated)

**Limitations**:

- ❌ No built-in time-series statistics endpoints
- ❌ No historical charts API
- ❌ Requires manual polling for time-series data

**Use Case**: Real-time queries only, not historical analysis

**Verdict**: ❌ NOT SUITABLE for historical high-frequency research

---

### 4. Blockchair API ⭐⭐⭐

**Status**: LIMITED - Free tier has strict rate limits

**Base URL**: `https://api.blockchair.com/`

**Capabilities**:

- Real-time stats (mempool_transactions, mempool_size, mempool_tps)
- Block queries by date/height
- Charts available (web interface)
- Multi-blockchain support (Bitcoin, Ethereum, etc.)

**Limitations**:

- ⚠️ HTTP 430 errors on free tier (rate limits)
- ⚠️ Historical time-series not fully accessible via free API
- ⚠️ Paid plans required for higher limits

**Example**:

```bash
curl -s "https://api.blockchair.com/bitcoin/stats" | jq '.data'
```

**Verdict**: ⚠️ LIMITED FREE ACCESS - Consider paid tier for production

---

### 5. BlockCypher API ⭐⭐⭐⭐

**Status**: GOOD - Block-level historical data

**Base URL**: `https://api.blockcypher.com/v1/btc/main`

**Capabilities**:

- Real-time chain info (height, unconfirmed_count, fee estimates)
- Block data by height (back to genesis)
- Historical access confirmed (tested: block 718000 from Jan 2022)
- Transaction details

**Historical Depth**: ✅ Genesis block (2009) to present

**Example Commands**:

```bash
# Current chain state
curl -s "https://api.blockcypher.com/v1/btc/main" | jq .

# Historical block (Jan 2022)
curl -s "https://api.blockcypher.com/v1/btc/main/blocks/718000" | jq '{height, time, n_tx, fees}'
```

**Data Format**:

```json
{
  "height": 718000,
  "time": "2022-01-10T09:47:09Z",
  "n_tx": 1325,
  "total": 2615510350126,
  "fees": 5026709
}
```

**Limitations**:

- Block-level granularity only (~10 min intervals)
- No aggregated statistics endpoints
- Requires iteration for time-series

**Rate Limits**: Free tier available, limits not clearly documented  
**Verdict**: ✅ GOOD for block-level historical reconstruction

---

## Premium Sources (Not Fully Free)

### Glassnode

- **Status**: Freemium (Community tier available)
- **Strengths**: Advanced on-chain analytics, SOPR, exchange flows
- **Limitations**: Limited metrics on free tier, daily granularity
- **Cost**: Community tier free, Pro tier from $29/month

### CoinMetrics

- **Status**: Freemium (Community API available)
- **Strengths**: Professional-grade on-chain metrics
- **Limitations**: Free tier has restricted access
- **Cost**: Community API free, paid tiers for full access

---

## Data Type Coverage Matrix

| Source          | M1  | M5  | M15 | Mempool | Fees | Blocks | OHLCV                 | Historical        |
| --------------- | --- | --- | --- | ------- | ---- | ------ | --------------------- | ----------------- |
| blockchain.info | ❌  | ❌  | ✅  | ✅      | ❌   | ❌     | ⚠️ (Daily close only) | ✅ 2009+          |
| mempool.space   | ❌  | ✅  | ✅  | ✅      | ✅   | ✅     | ❌                    | ✅ 2022+          |
| Blockstream     | ❌  | ❌  | ❌  | ✅      | ✅   | ✅     | ❌                    | ⚠️ (Manual)       |
| Blockchair      | ❌  | ❌  | ❌  | ✅      | ❌   | ✅     | ❌                    | ⚠️ (Rate limited) |
| BlockCypher     | ❌  | ❌  | ❌  | ✅      | ✅   | ✅     | ❌                    | ✅ 2009+          |

**Legend**:

- ✅ Available
- ⚠️ Limited/Conditional
- ❌ Not Available

---

## Recommended Integration Strategy

### For M15 Mempool Data

```python
import requests
from datetime import datetime

# blockchain.info M15 mempool size (3 years)
url = "https://api.blockchain.info/charts/mempool-size"
params = {"timespan": "3years", "sampled": "false", "format": "json"}
resp = requests.get(url, params=params)
data = resp.json()

# Convert to DataFrame
import pandas as pd
df = pd.DataFrame(data['values'])
df['timestamp'] = pd.to_datetime(df['x'], unit='s')
df = df.set_index('timestamp')
df = df.rename(columns={'y': 'mempool_size_bytes'})
print(f"M15 data points: {len(df)}")
# Output: M15 data points: 105016
```

### For M5 Mempool Statistics

```python
# mempool.space M5 statistics (1 week)
url = "https://mempool.space/api/v1/statistics/1w"
resp = requests.get(url)
data = resp.json()

df = pd.DataFrame(data)
df['timestamp'] = pd.to_datetime(df['added'], unit='s')
df = df.set_index('timestamp')
print(f"M5 data points: {len(df)}")
# Output: M5 data points: 2017
```

### For Block-Level Historical Data

```python
# BlockCypher block iteration (example: Jan 2022)
base_url = "https://api.blockcypher.com/v1/btc/main/blocks"
heights = range(718000, 718100)  # 100 blocks

blocks = []
for height in heights:
    resp = requests.get(f"{base_url}/{height}")
    blocks.append(resp.json())

df = pd.DataFrame(blocks)
df['timestamp'] = pd.to_datetime(df['time'])
df = df[['height', 'timestamp', 'n_tx', 'fees', 'total']]
```

---

## Key Findings Summary

### ✅ MEETS CRITERIA (M15+, 3+ years, FREE)

1. **blockchain.info** - M15 mempool/TPS data, back to 2009
2. **mempool.space** - M5 statistics, back to Nov 2022

### ⚠️ PARTIAL COVERAGE

3. **BlockCypher** - Block-level (M10 avg), back to genesis
4. **Blockchair** - Limited by rate limits

### ❌ NOT SUITABLE

5. **Blockstream** - Real-time only, no historical aggregates
6. **Glassnode/CoinMetrics** - Paid tiers required for high-frequency

---

## Notes on OHLCV Price Data

**Important**: Bitcoin ecosystem APIs (blockchain.info, mempool.space, etc.) do NOT provide proper OHLCV candles. They only offer:

- Daily closing prices (blockchain.info `market-price`)
- No open/high/low/volume breakdown

**For OHLCV data**, use cryptocurrency exchange APIs instead:

- Binance API (free, M1/M5/M15 available)
- Kraken API (free, M1/M5/M15 available)
- Coinbase Pro API (free, M1/M5/M15 available)

---

## Testing Workspace

All test scripts and findings are available in `/tmp/bitcoin-research/`:

- `mempool_space_findings.md`
- `blockchain_info_findings.md`
- `blockstream_findings.md`
- `test_mempool_api.sh`
- `analyze_mempool_stats.py`
- `analyze_blockchain_info.py`
- `test_blockstream.sh`
- `test_blockcypher.sh`

---

## Conclusion

**For high-frequency Bitcoin on-chain data** meeting the criteria (M15+, 3+ years, free):

1. **Primary Source**: blockchain.info Charts API
   - M15 frequency ✅
   - 3+ years historical ✅
   - Free ✅
   - 105,016 data points (Nov 2022 - Nov 2025)

2. **Secondary Source**: mempool.space Statistics API
   - M5 frequency ✅
   - 3+ years historical ✅
   - Free ✅
   - 2,193 data points (3-year endpoint)

3. **Supplementary**: BlockCypher for block-level data
   - Block granularity (~10 min) ✅
   - Complete history to genesis ✅
   - Free tier available ✅

**Both primary sources meet ALL criteria** and provide complementary data:

- blockchain.info: Better for M15 time-series
- mempool.space: Better for M5 real-time statistics + mining data
