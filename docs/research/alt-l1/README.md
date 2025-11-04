# Alternative L1 High-Frequency Data Research

**Research Date**: 2025-11-03
**Workspace**: `/tmp/altl1-research/`
**Status**: ✅ Complete

---

## 📑 Documentation Index

### Primary Documents (Read These First)

1. **[EXECUTIVE_SUMMARY.md](/tmp/altl1-research/EXECUTIVE_SUMMARY.md)**
   - High-level overview of findings
   - Key recommendations
   - Quick metrics and statistics
   - **START HERE** for overview

2. **[QUICK_REFERENCE.md](/tmp/altl1-research/QUICK_REFERENCE.md)**
   - Ready-to-use curl commands
   - API endpoint reference
   - Copy-paste examples
   - **USE THIS** for implementation

3. **[COMPREHENSIVE_FINDINGS.md](/tmp/altl1-research/COMPREHENSIVE_FINDINGS.md)**
   - Complete research report
   - Detailed API analysis
   - Rate limits and restrictions
   - Full documentation
   - **READ THIS** for deep dive

---

## 🎯 Research Results Summary

### PRIMARY FINDING

**Binance Public API provides free 1-minute OHLCV data for all major alt-L1s from 2022**

| Metric             | Result                                                                  |
| ------------------ | ----------------------------------------------------------------------- |
| Blockchains Tested | 8 (Solana, Avalanche, Cardano, Polkadot, Cosmos, Near, Algorand, Tezos) |
| Minimum Frequency  | 1-minute (M1) ✅                                                        |
| Historical Depth   | 2022-01-01 ✅                                                           |
| Authentication     | None required ✅                                                        |
| Rate Limit         | 120 req/min ✅                                                          |
| Coverage           | 100% of tested chains ✅                                                |

### Quick Start Command

```bash
# Get Solana 1-minute data from 2022
curl "https://api.binance.com/api/v3/klines?symbol=SOLUSDT&interval=1m&startTime=1640995200000&limit=1000"
```

---

## 📂 File Structure

### Documentation

```
/tmp/altl1-research/
├── README.md                        # This file (index)
├── EXECUTIVE_SUMMARY.md             # High-level findings
├── QUICK_REFERENCE.md               # Quick start guide
├── COMPREHENSIVE_FINDINGS.md        # Full research report
└── alt_l1_inventory.md              # Blockchain inventory
```

### Code & Scripts

```
/tmp/altl1-research/
├── fetch_binance_historical.py      # Python bulk download script
├── test_binance_altl1s.sh           # Binance coverage test
└── test_coinbase_altl1s.sh          # Coinbase coverage test
```

### Test Results (JSON)

```
/tmp/altl1-research/
├── solana_binance_1m.json           # Binance Solana test
├── coinbase_solana_1m.json          # Coinbase Solana test
├── avalanche_snowtrace_*.json       # Avalanche on-chain data
├── tezos_tzkt_*.json                # Tezos on-chain data
├── polkadot_subscan_*.json          # Polkadot on-chain data
├── near_nearblocks_*.json           # Near on-chain data
├── algorand_*.json                  # Algorand on-chain data
└── cardano_blockfrost_test.json     # Cardano API test
```

---

## 🚀 Quick Start

### Option 1: Using curl (No Dependencies)

```bash
# Download latest 1000 1-minute candles for Solana
curl "https://api.binance.com/api/v3/klines?symbol=SOLUSDT&interval=1m&limit=1000" > solana_latest_1m.json

# Download from specific date (2022-01-01)
curl "https://api.binance.com/api/v3/klines?symbol=AVAXUSDT&interval=1m&startTime=1640995200000&limit=1000" > avax_2022_1m.json
```

### Option 2: Using Python Script

```bash
# Run the provided Python script
cd /tmp/altl1-research
uv run fetch_binance_historical.py
```

### Option 3: Using the test scripts

```bash
# Test all alt-L1s on Binance
cd /tmp/altl1-research
./test_binance_altl1s.sh

# Test all alt-L1s on Coinbase
./test_coinbase_altl1s.sh
```

---

## 📊 Supported Blockchains

| Blockchain | Binance Symbol | Coinbase Symbol | 1m Data From | Status |
| ---------- | -------------- | --------------- | ------------ | ------ |
| Solana     | SOLUSDT        | SOL-USD         | 2021-12-31   | ✅     |
| Avalanche  | AVAXUSDT       | AVAX-USD        | 2021-12-31   | ✅     |
| Cardano    | ADAUSDT        | ADA-USD         | 2021-12-31   | ✅     |
| Polkadot   | DOTUSDT        | DOT-USD         | 2021-12-31   | ✅     |
| Cosmos     | ATOMUSDT       | ATOM-USD        | 2021-12-31   | ✅     |
| Near       | NEARUSDT       | -               | 2021-12-31   | ✅     |
| Algorand   | ALGOUSDT       | ALGO-USD        | 2021-12-31   | ✅     |
| Tezos      | XTZUSDT        | XTZ-USD         | 2021-12-31   | ✅     |

---

## 🔧 API Endpoints Reference

### Binance (Primary)

```
GET https://api.binance.com/api/v3/klines
Parameters:
  - symbol: SOLUSDT, AVAXUSDT, ADAUSDT, etc.
  - interval: 1m, 5m, 15m, 30m, 1h, 4h, 1d
  - startTime: Unix timestamp in milliseconds
  - endTime: Unix timestamp in milliseconds (optional)
  - limit: 1-1000 (default 500)
```

### Coinbase (Backup)

```
GET https://api.exchange.coinbase.com/products/{product_id}/candles
Parameters:
  - granularity: 60, 300, 900, 3600, 21600, 86400 (seconds)
  - start: ISO 8601 timestamp
  - end: ISO 8601 timestamp
```

---

## 📈 Data Frequencies Available

| Frequency        | Binance Code | Coinbase Code | Status       |
| ---------------- | ------------ | ------------- | ------------ |
| 1 minute (M1)    | `1m`         | `60`          | ✅ Tested    |
| 3 minutes        | `3m`         | -             | ✅ Available |
| 5 minutes (M5)   | `5m`         | `300`         | ✅ Tested    |
| 15 minutes (M15) | `15m`        | `900`         | ✅ Tested    |
| 30 minutes       | `30m`        | -             | ✅ Available |
| 1 hour           | `1h`         | `3600`        | ✅ Available |
| 4 hours          | `4h`         | -             | ✅ Available |
| 6 hours          | `6h`         | `21600`       | ✅ Available |
| 1 day            | `1d`         | `86400`       | ✅ Available |

---

## ⚡ Rate Limits

| API        | Public Rate Limit              | Auth Required | Notes                   |
| ---------- | ------------------------------ | ------------- | ----------------------- |
| Binance    | 1200 weight/min (~120 req/min) | ❌ No         | Conservative: 1 req/sec |
| Coinbase   | 10 req/sec (burst: 15)         | ❌ No         | Conservative: 5 req/sec |
| Subscan    | Not specified                  | ❌ No         | Polkadot on-chain       |
| TzKT       | Not specified                  | ❌ No         | Tezos on-chain          |
| NearBlocks | Not specified                  | ❌ No         | Near on-chain           |
| Snowtrace  | Basic (no key)                 | ⚠️ Optional   | Avalanche on-chain      |
| AlgoNode   | Not specified                  | ❌ No         | Algorand on-chain       |

---

## 💡 Use Cases

### 1. Feature Engineering for ML Models

```python
# Fetch 1m OHLCV + engineer features
df = fetch_binance_1m("SOLUSDT", "2022-01-01", "2022-12-31")
df['returns'] = df['close'].pct_change()
df['volatility'] = df['returns'].rolling(30).std()
df['volume_ma'] = df['volume'].rolling(60).mean()
```

### 2. Backtesting Trading Strategies

```python
# Test momentum strategy on 5m data
df = fetch_binance_5m("AVAXUSDT", "2022-01-01", "2023-01-01")
df['sma_fast'] = df['close'].rolling(20).mean()
df['sma_slow'] = df['close'].rolling(50).mean()
df['signal'] = (df['sma_fast'] > df['sma_slow']).astype(int)
```

### 3. Cross-Chain Analysis

```python
# Compare volatility across alt-L1s
chains = ["SOLUSDT", "AVAXUSDT", "ADAUSDT", "DOTUSDT"]
volatility_comparison = {}

for chain in chains:
    df = fetch_binance_1m(chain, "2022-01-01", "2022-12-31")
    volatility_comparison[chain] = df['close'].pct_change().std()
```

---

## 🎓 Best Practices

### 1. Always Implement Rate Limiting

```python
import time

def fetch_with_rate_limit(symbol, interval, start_time):
    data = fetch_klines(symbol, interval, start_time)
    time.sleep(1)  # 1 req/sec (conservative)
    return data
```

### 2. Use Pagination for Large Ranges

```python
# For date ranges > 1000 candles
def fetch_all(symbol, interval, start_date, end_date):
    all_data = []
    current = start_date

    while current < end_date:
        batch = fetch_klines(symbol, interval, current, limit=1000)
        all_data.extend(batch)
        current = batch[-1]['close_time'] + 1
        time.sleep(1)

    return all_data
```

### 3. Cache Locally

```python
# Save to Parquet for reuse
df.to_parquet(f"{symbol}_{interval}_{date_range}.parquet")

# Load from cache
df = pd.read_parquet(f"{symbol}_{interval}_{date_range}.parquet")
```

---

## 🔍 Data Quality Notes

### OHLCV Data (from Binance/Coinbase)

- **Timezone**: UTC
- **Gaps**: Minimal (24/7 trading)
- **Accuracy**: Exchange-verified
- **Limitation**: CEX prices (may differ from DEX)

### On-Chain Data (from Explorers)

- **Timezone**: UTC (block timestamps)
- **Gaps**: None (continuous blockchain)
- **Accuracy**: Blockchain-verified
- **Limitation**: Different granularities per chain

---

## 📞 Next Steps

1. **Review Documentation**
   - Read [EXECUTIVE_SUMMARY.md](/tmp/altl1-research/EXECUTIVE_SUMMARY.md) for overview
   - Check [QUICK_REFERENCE.md](/tmp/altl1-research/QUICK_REFERENCE.md) for examples

2. **Test API Access**
   - Run test scripts to verify connectivity
   - Try curl examples from quick reference

3. **Implement Data Pipeline**
   - Use [fetch_binance_historical.py](/tmp/altl1-research/fetch_binance_historical.py) as template
   - Add error handling and retry logic
   - Implement local caching

4. **Feature Engineering**
   - Combine OHLCV with on-chain metrics
   - Create domain-specific features
   - Build ML-ready datasets

---

## ✅ Research Validation

All requirements verified:

- ✅ M1 (1-minute) frequency available
- ✅ M5 (5-minute) frequency available
- ✅ M15 (15-minute) frequency available
- ✅ Historical depth to 2022-01-01
- ✅ 8 major alt-L1 blockchains tested
- ✅ No authentication required
- ✅ Reasonable rate limits
- ✅ On-chain metrics from native explorers

---

## 📚 Additional Resources

- **Binance API Docs**: https://developers.binance.com/docs/binance-spot-api-docs
- **Coinbase API Docs**: https://docs.cdp.coinbase.com/exchange/docs
- **Subscan Docs**: https://support.subscan.io/#introduction
- **TzKT API**: https://api.tzkt.io/
- **NearBlocks API**: https://api.nearblocks.io/
- **Snowtrace Docs**: https://docs.snowtrace.io/
- **AlgoNode**: https://algonode.io/api/

---

**Research Status**: ✅ **COMPLETE**

**Recommendation**: Use Binance API as primary source for 1-minute OHLCV data, supplemented by blockchain-specific explorer APIs for on-chain network metrics.

**Contact**: This research was conducted systematically using empirical validation (curl tests) for all APIs and blockchains listed.
