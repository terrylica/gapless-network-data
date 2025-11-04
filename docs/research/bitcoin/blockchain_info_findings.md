# blockchain.info (Blockchain.com) API Analysis

## Summary

Free Bitcoin charts API with EXCELLENT M15 historical data going back to 2009.

## Base URL

`https://api.blockchain.info/charts/{chart_name}`

## Parameters

- `timespan`: 1weeks, 1months, 1years, 3years, all
- `sampled`: true/false (false = full resolution)
- `format`: json
- `cors`: true

## High-Frequency Charts (M15 = 15-minute intervals)

### 1. Mempool Size

- **URL**: `https://api.blockchain.info/charts/mempool-size?timespan=all&sampled=false&format=json`
- **Frequency**: M15 (15 minutes)
- **Historical Depth**: 329,108 points back to ~2009
- **Unit**: Bytes
- **3-year data**: 105,016 points (Nov 2022 - Nov 2025)

### 2. Transactions Per Second

- **URL**: `https://api.blockchain.info/charts/transactions-per-second?timespan=all&sampled=false&format=json`
- **Frequency**: M15 (15 minutes)
- **Historical Depth**: Complete history
- **Unit**: Transactions/second
- **3-year data**: 104,386 points

## Daily Charts (D1 = Daily intervals)

### Market Data

- `market-price`: Bitcoin USD price (daily)
- `trade-volume`: Trading volume in USD (daily)

### Network Statistics

- `hash-rate`: Network hash rate in TH/s (daily)
- `difficulty`: Mining difficulty (daily)
- `n-transactions`: Total transactions (daily)
- `n-unique-addresses`: Unique addresses used (daily)
- `avg-block-size`: Average block size in MB (daily)

### Economic Metrics

- `miners-revenue`: Miner revenue in USD (daily)
- `transaction-fees`: Transaction fees in BTC (daily)
- `cost-per-transaction`: Cost per tx in USD (daily)
- `output-volume`: Total output volume in BTC (daily)
- `estimated-transaction-volume`: Estimated volume (daily)

## Data Format

```json
{
  "status": "ok",
  "name": "Mempool Size",
  "unit": "Bytes",
  "period": "day",
  "description": "...",
  "values": [
    {"x": 1762219800, "y": 934284.5},
    ...
  ]
}
```

## Example Commands

```bash
# M15 mempool size (3 years)
curl -s "https://api.blockchain.info/charts/mempool-size?timespan=3years&sampled=false&format=json" | jq '.values | length'

# M15 transactions per second (1 year)
curl -s "https://api.blockchain.info/charts/transactions-per-second?timespan=1years&sampled=false&format=json" | jq '.values[0:5]'

# Daily hash rate (all time)
curl -s "https://api.blockchain.info/charts/hash-rate?timespan=all&format=json" | jq '.values | length'

# Daily market price (3 years back to 2022)
curl -s "https://api.blockchain.info/charts/market-price?timespan=3years&format=json" | jq '.values[0:5]'
```

## Rate Limits

- **Not documented**, appears to be generous
- **Authentication**: None required

## Data Types

- ✅ M15 mempool size (15-minute intervals)
- ✅ M15 transactions per second
- ✅ Daily market price (NOT OHLCV, just closing price)
- ✅ Daily network metrics (hash rate, difficulty, etc)
- ✅ Historical depth back to Nov 2022 (3+ years)
- ❌ OHLCV candles (only daily closing price available)

## Frequency Assessment

- **M15 (15-minute)**: ✅ Available for mempool-size, transactions-per-second
- **D1 (Daily)**: ✅ Available for most other metrics
- **Historical depth**: ✅ 3+ years (back to Nov 2022), some metrics to 2009

## Verdict

**EXCELLENT** for M15 mempool and transaction data. Daily price available but NOT full OHLCV.
