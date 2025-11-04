# Bitcoin High-Frequency Data Sources - Quick Reference

## Top 2 Sources (Meet ALL Criteria)

### 1. blockchain.info - M15 Frequency ⭐⭐⭐⭐⭐

```bash
# M15 mempool size (105,016 points, Nov 2022 - Nov 2025)
curl -s "https://api.blockchain.info/charts/mempool-size?timespan=3years&sampled=false&format=json"

# M15 transactions per second (105,016 points)
curl -s "https://api.blockchain.info/charts/transactions-per-second?timespan=3years&sampled=false&format=json"

# Available timespans: 1weeks, 1months, 1years, 3years, all
```

**Data**: 15-minute intervals, back to 2009  
**Free**: Yes, no authentication  
**Rate Limits**: Not documented, generous

---

### 2. mempool.space - M5 Frequency ⭐⭐⭐⭐⭐

```bash
# M5 statistics - 1 week (2,017 points)
curl -s "https://mempool.space/api/v1/statistics/1w"

# M30 statistics - 1 month (1,489 points)
curl -s "https://mempool.space/api/v1/statistics/1m"

# H12 statistics - 3 years (2,193 points, Nov 2022 - Nov 2025)
curl -s "https://mempool.space/api/v1/statistics/3y"

# Current mempool state (real-time)
curl -s "https://mempool.space/api/mempool"

# Fee recommendations
curl -s "https://mempool.space/api/v1/fees/recommended"
```

**Data**: 5-minute to 12-hour intervals, back to Nov 2022  
**Free**: Yes, no authentication  
**Rate Limits**: 10 req/sec

---

## Quick Comparison

| Feature          | blockchain.info | mempool.space |
| ---------------- | --------------- | ------------- |
| Best Frequency   | M15 (15 min)    | M5 (5 min)    |
| Historical Depth | 2009+           | Nov 2022+     |
| Mempool Size     | ✅ M15          | ✅ M5         |
| Transaction Rate | ✅ M15          | ✅ M5         |
| Fee Rates        | ❌ (Daily only) | ✅ Real-time  |
| Block Data       | ❌              | ✅            |
| Mining Stats     | ❌              | ✅            |

---

## Python Integration Examples

### blockchain.info

```python
import requests
import pandas as pd

url = "https://api.blockchain.info/charts/mempool-size"
params = {"timespan": "3years", "sampled": "false", "format": "json"}
resp = requests.get(url, params=params)
data = resp.json()

df = pd.DataFrame(data['values'])
df['timestamp'] = pd.to_datetime(df['x'], unit='s')
df = df.set_index('timestamp').rename(columns={'y': 'mempool_size_bytes'})
# 105,016 rows × 1 column (M15 frequency)
```

### mempool.space

```python
import requests
import pandas as pd

url = "https://mempool.space/api/v1/statistics/1w"
resp = requests.get(url)
data = resp.json()

df = pd.DataFrame(data)
df['timestamp'] = pd.to_datetime(df['added'], unit='s')
df = df.set_index('timestamp')
# 2,017 rows × 4 columns (M5 frequency)
# Columns: count, vbytes_per_second, min_fee, vsizes
```

---

## Data Fields

### blockchain.info M15 Data

- `mempool-size`: Mempool size in bytes
- `transactions-per-second`: Network TPS

### mempool.space M5 Data

- `count`: Transaction count in mempool
- `vbytes_per_second`: Mempool growth rate
- `min_fee`: Minimum fee rate (sat/vB)
- `vsizes`: Array of mempool size buckets by fee tier

---

## For OHLCV Price Data

Bitcoin ecosystem APIs do NOT provide OHLCV candles.

Use exchange APIs instead:

- **Binance**: `GET /api/v3/klines` (M1/M5/M15, free)
- **Kraken**: `GET /0/public/OHLC` (M1/M5/M15, free)
- **Coinbase**: `GET /products/{id}/candles` (M1/M5/M15, free)

---

## Files in /tmp/bitcoin-research/

- `COMPREHENSIVE_FINDINGS.md` - Full research report
- `mempool_space_findings.md` - mempool.space details
- `blockchain_info_findings.md` - blockchain.info details
- `blockstream_findings.md` - Blockstream analysis
- `test_*.sh` - Bash test scripts
- `analyze_*.py` - Python analysis scripts
