# mempool.space API Analysis

## Summary

Free Bitcoin data API with excellent historical depth and high frequency capabilities.

## Endpoints

### 1. Real-time Mempool Data

- **URL**: `https://mempool.space/api/mempool`
- **Frequency**: Real-time (on-demand)
- **Fields**:
  - `count`: Unconfirmed transaction count
  - `vsize`: Mempool size in virtual bytes
  - `total_fee`: Total fees in satoshis
  - `fee_histogram`: Array of [fee_rate, vsize] pairs

### 2. Fee Recommendations

- **URL**: `https://mempool.space/api/v1/fees/recommended`
- **Frequency**: Real-time (on-demand)
- **Fields**: `fastestFee`, `halfHourFee`, `hourFee`, `economyFee`, `minimumFee` (sat/vB)

### 3. Historical Statistics (HIGH FREQUENCY!)

- **Base URL**: `https://mempool.space/api/v1/statistics/{period}`
- **Periods Available**:
  - `1w`: 2017 points, ~5 min intervals (M5 frequency)
  - `1m`: 1489 points, ~30 min intervals (M30 frequency)
  - `3m`: 1105 points, ~2 hour intervals (H2 frequency)
  - `6m`: 1457 points, ~3 hour intervals (H3 frequency)
  - `1y`: 1096 points, ~8 hour intervals (H8 frequency)
  - `2y`: 2194 points, ~8 hour intervals (H8 frequency)
  - `3y`: 2193 points, ~12 hour intervals (H12 frequency)

**Historical Depth**: Back to November 2022 (3+ years) ✅

**Fields Available**:

- `added`: Unix timestamp
- `count`: Transaction count in mempool
- `vbytes_per_second`: Mempool growth rate
- `min_fee`: Minimum fee rate
- `vsizes`: Array of mempool size buckets by fee rate

### 4. Block Data

- **URL**: `https://mempool.space/api/v1/blocks/{start_height}`
- **Returns**: 10 blocks per request
- **Fields**: height, timestamp, tx_count, size, weight, miner, fees
- **Historical Depth**: Genesis block (2009) to present

### 5. Mining Statistics

- **URL**: `https://mempool.space/api/v1/mining/hashrate/pools/{period}`
- **Periods**: 1m, 3m, 6m, 1y, 2y, 3y
- **Fields**: timestamp, avgHashrate, share, poolName

## Example Commands

```bash
# Current mempool state
curl -s "https://mempool.space/api/mempool" | jq .

# Fee recommendations
curl -s "https://mempool.space/api/v1/fees/recommended" | jq .

# 1-week high-frequency stats (M5 granularity)
curl -s "https://mempool.space/api/v1/statistics/1w" | jq '.[0:5]'

# 3-year historical stats (back to 2022)
curl -s "https://mempool.space/api/v1/statistics/3y" | jq '.[0:5]'

# Latest blocks
curl -s "https://mempool.space/api/v1/blocks/0" | jq '.[0:3]'

# Mining pool hashrate (1 month)
curl -s "https://mempool.space/api/v1/mining/hashrate/pools/1m" | jq '.[0:5]'
```

## Rate Limits

- **Documented**: 10 requests/second
- **Authentication**: None required (public API)

## Data Types

- ✅ Mempool statistics (count, size, fees)
- ✅ Fee rates (multiple time horizons)
- ✅ Block data (height, timestamp, transactions)
- ✅ Mining statistics (hashrate, pool distribution)
- ❌ OHLCV price data (NOT available - use crypto exchanges)

## Frequency Assessment

- **M5 (5-minute)**: ✅ Available (1w endpoint)
- **M15 (15-minute)**: ✅ Can aggregate from M5
- **Historical depth**: ✅ 3+ years (back to Nov 2022)

## Verdict

**EXCELLENT** for mempool/blockchain data. Does NOT provide OHLCV price data.
