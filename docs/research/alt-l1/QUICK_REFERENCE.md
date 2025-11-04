# Alternative L1 Free High-Frequency Data - Quick Reference

**Last Updated**: 2025-11-03

---

## 🚀 Quick Start: Get 1-Minute OHLCV Data (No Auth Required)

### Binance API (Recommended)

```bash
# Solana - Latest 100 1-minute candles
curl "https://api.binance.com/api/v3/klines?symbol=SOLUSDT&interval=1m&limit=100"

# Avalanche - Historical from 2022-01-01
curl "https://api.binance.com/api/v3/klines?symbol=AVAXUSDT&interval=1m&startTime=1640995200000&limit=1000"

# Cardano - 5-minute candles
curl "https://api.binance.com/api/v3/klines?symbol=ADAUSDT&interval=5m&limit=500"

# Polkadot - 15-minute candles
curl "https://api.binance.com/api/v3/klines?symbol=DOTUSDT&interval=15m&limit=500"
```

### Coinbase API (Alternative)

```bash
# Solana - 1-minute candles
curl "https://api.exchange.coinbase.com/products/SOL-USD/candles?granularity=60&start=2022-01-01T00:00:00Z&end=2022-01-01T05:00:00Z"

# Avalanche - 5-minute candles
curl "https://api.exchange.coinbase.com/products/AVAX-USD/candles?granularity=300"

# Cardano - 15-minute candles
curl "https://api.exchange.coinbase.com/products/ADA-USD/candles?granularity=900"
```

---

## 📊 Supported Blockchains & Symbols

| Blockchain | Binance Symbol | Coinbase Symbol | 2022 Data | Status       |
| ---------- | -------------- | --------------- | --------- | ------------ |
| Solana     | SOLUSDT        | SOL-USD         | ✅        | Available    |
| Avalanche  | AVAXUSDT       | AVAX-USD        | ✅        | Available    |
| Cardano    | ADAUSDT        | ADA-USD         | ✅        | Available    |
| Polkadot   | DOTUSDT        | DOT-USD         | ✅        | Available    |
| Cosmos     | ATOMUSDT       | ATOM-USD        | ✅        | Available    |
| Near       | NEARUSDT       | ❌              | ✅        | Binance only |
| Algorand   | ALGOUSDT       | ALGO-USD        | ✅        | Available    |
| Tezos      | XTZUSDT        | XTZ-USD         | ✅        | Available    |

---

## ⏱️ Frequency Options

### Binance Intervals

| Interval   | Code  | Example        |
| ---------- | ----- | -------------- |
| 1 minute   | `1m`  | `interval=1m`  |
| 3 minutes  | `3m`  | `interval=3m`  |
| 5 minutes  | `5m`  | `interval=5m`  |
| 15 minutes | `15m` | `interval=15m` |
| 30 minutes | `30m` | `interval=30m` |
| 1 hour     | `1h`  | `interval=1h`  |
| 2 hours    | `2h`  | `interval=2h`  |
| 4 hours    | `4h`  | `interval=4h`  |
| 6 hours    | `6h`  | `interval=6h`  |
| 12 hours   | `12h` | `interval=12h` |
| 1 day      | `1d`  | `interval=1d`  |

### Coinbase Granularity (in seconds)

| Interval   | Seconds | Example             |
| ---------- | ------- | ------------------- |
| 1 minute   | `60`    | `granularity=60`    |
| 5 minutes  | `300`   | `granularity=300`   |
| 15 minutes | `900`   | `granularity=900`   |
| 1 hour     | `3600`  | `granularity=3600`  |
| 6 hours    | `21600` | `granularity=21600` |
| 1 day      | `86400` | `granularity=86400` |

---

## 🔄 Date/Time Conversion

### Convert Date to Unix Timestamp (milliseconds for Binance)

```bash
# macOS
date -j -f "%Y-%m-%d %H:%M:%S" "2022-01-01 00:00:00" "+%s000"

# Linux
date -d "2022-01-01 00:00:00" "+%s000"

# Output: 1640995200000
```

### Convert Unix Timestamp to Date

```bash
# macOS
date -r 1640995200

# Linux
date -d @1640995200

# Output: Fri Dec 31 16:00:00 PST 2021
```

---

## 📈 On-Chain Network Metrics

### Polkadot (Subscan)

```bash
# Network metadata
curl -X POST "https://polkadot.api.subscan.io/api/scan/metadata" \
  -H "Content-Type: application/json" \
  -d '{}'

# Recent blocks
curl -X POST "https://polkadot.api.subscan.io/api/v2/scan/blocks" \
  -H "Content-Type: application/json" \
  -d '{"row": 10, "page": 0}'
```

**Frequency**: Block-level (~6 seconds)
**Historical**: From genesis (May 2020)
**Auth**: None required

---

### Tezos (TzKT)

```bash
# Latest block
curl "https://api.tzkt.io/v1/head"

# Daily statistics
curl "https://api.tzkt.io/v1/statistics/daily?limit=100&sort.desc=date"

# Blocks from 2022
curl "https://api.tzkt.io/v1/blocks?timestamp.ge=2022-01-01&limit=100"
```

**Frequency**: Block-level (~30-60 seconds)
**Historical**: From genesis (June 2018)
**Auth**: None required

---

### NEAR (NearBlocks)

```bash
# Network stats
curl "https://api.nearblocks.io/v1/stats"

# Historical charts (daily)
curl "https://api.nearblocks.io/v1/charts?start_date=2022-01-01&end_date=2022-12-31"
```

**Frequency**: Daily aggregates
**Historical**: From launch (July 2020)
**Auth**: None required

---

### Avalanche (Snowtrace)

```bash
# Current AVAX price
curl "https://api.snowtrace.io/api?module=stats&action=ethprice"

# Daily transaction counts
curl "https://api.snowtrace.io/api?module=stats&action=dailytx&startdate=2022-01-01&enddate=2022-12-31&sort=asc"
```

**Frequency**: Daily aggregates
**Historical**: From C-Chain launch (Sep 2020)
**Auth**: None required (optional key for higher limits)

---

### Algorand (AlgoNode)

```bash
# Indexer health
curl "https://mainnet-idx.algonode.cloud/health"

# Specific block
curl "https://mainnet-idx.algonode.cloud/v2/blocks/19000000"
```

**Frequency**: Block-level (~4.5 seconds)
**Historical**: From mainnet (June 2019)
**Auth**: None required

---

## ⚡ Rate Limits

| API        | Limit                                     | Auth Required |
| ---------- | ----------------------------------------- | ------------- |
| Binance    | 1200 weight/min (~120 req/min for klines) | ❌ No         |
| Coinbase   | 10 req/sec (burst: 15 req/sec)            | ❌ No         |
| Subscan    | Not specified                             | ❌ No         |
| TzKT       | Not specified                             | ❌ No         |
| NearBlocks | Not specified                             | ❌ No         |
| Snowtrace  | Basic (no key), Higher (with key)         | ⚠️ Optional   |
| AlgoNode   | Not specified                             | ❌ No         |

---

## 📦 Data Format Examples

### Binance Response

```json
[
  [
    1640995200000, // Open time (Unix ms)
    "170.01000000", // Open
    "170.22000000", // High
    "169.93000000", // Low
    "170.14000000", // Close
    "810.27000000", // Volume (base)
    1640995259999, // Close time
    "137785.37510000", // Quote volume
    174, // Number of trades
    "459.80000000", // Taker buy base
    "78194.16870000", // Taker buy quote
    "0" // Ignore
  ]
]
```

### Coinbase Response

```json
[
  [
    1640998800, // Timestamp (Unix seconds)
    172.28, // Low
    172.44, // High
    172.4, // Open
    172.28, // Close
    483.46 // Volume
  ]
]
```

---

## 🐍 Python One-Liner

```python
# Fetch Solana 1m data for 2022-01-01
import requests, pandas as pd

df = pd.DataFrame(
    requests.get("https://api.binance.com/api/v3/klines",
                 params={"symbol": "SOLUSDT", "interval": "1m",
                         "startTime": 1640995200000, "limit": 1000}).json(),
    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
             'close_time', 'quote_volume', 'trades', 'taker_buy_base',
             'taker_buy_quote', 'ignore']
)

df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)

print(df[['open', 'high', 'low', 'close', 'volume']].head())
```

---

## 💡 Pro Tips

### 1. Batch Download with Pagination

```bash
#!/bin/bash
# Download full 2022 Solana data in batches

symbol="SOLUSDT"
interval="1m"
start=1640995200000  # 2022-01-01
end=1672531199000    # 2022-12-31 23:59:59

current=$start
output_file="solana_2022_1m.json"
echo "[" > $output_file

while [ $current -lt $end ]; do
    echo "Fetching from $(date -r $((current/1000)))"

    data=$(curl -s "https://api.binance.com/api/v3/klines?symbol=$symbol&interval=$interval&startTime=$current&limit=1000")

    # Append to file (remove outer brackets)
    echo "$data" | jq '.[]' >> $output_file

    # Get last timestamp and increment
    last_close=$(echo "$data" | jq -r '.[-1][6]')
    current=$((last_close + 1))

    # Rate limit: 1 req/sec
    sleep 1
done

echo "]" >> $output_file
echo "Download complete: $output_file"
```

### 2. Multi-Chain Parallel Download

```bash
#!/bin/bash
# Download multiple chains in parallel

symbols=("SOLUSDT" "AVAXUSDT" "ADAUSDT" "DOTUSDT")

for symbol in "${symbols[@]}"; do
    (
        echo "Starting $symbol"
        curl -s "https://api.binance.com/api/v3/klines?symbol=$symbol&interval=1m&startTime=1640995200000&limit=1000" \
          | jq '.' > "${symbol}_2022.json"
        echo "Completed $symbol"
    ) &
done

wait
echo "All downloads complete"
```

### 3. CSV Export

```bash
# Download and convert to CSV
curl -s "https://api.binance.com/api/v3/klines?symbol=SOLUSDT&interval=1m&limit=100" \
  | jq -r '.[] | [.[0], .[1], .[2], .[3], .[4], .[5]] | @csv' \
  | (echo "timestamp,open,high,low,close,volume"; cat) \
  > solana_1m.csv
```

---

## 📚 Full Documentation

- **Comprehensive Findings**: `/tmp/altl1-research/COMPREHENSIVE_FINDINGS.md`
- **Python Script**: `/tmp/altl1-research/fetch_binance_historical.py`
- **Binance API Docs**: https://developers.binance.com/docs/binance-spot-api-docs
- **Coinbase API Docs**: https://docs.cdp.coinbase.com/exchange/docs

---

## ✅ Verification Checklist

- [x] M1 (1-minute) frequency available
- [x] M5 (5-minute) frequency available
- [x] M15 (15-minute) frequency available
- [x] Historical data from 2022-01-01
- [x] No authentication required
- [x] 8 major alt-L1 blockchains tested
- [x] On-chain metrics from native explorers
- [x] Rate limits documented
- [x] Example scripts provided

---

**Status**: ✅ All requirements met

**Best Source**: Binance API (`https://api.binance.com/api/v3/klines`)

**Backup Source**: Coinbase Exchange API (`https://api.exchange.coinbase.com`)
