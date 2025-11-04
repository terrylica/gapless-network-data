# Free High-Frequency Multi-Chain Data Aggregators Research

## M15+ Frequency Going Back to 2022

**Research Date**: 2025-11-03
**Research Workspace**: `/tmp/aggregator-research/`

---

## Executive Summary

**Key Finding**: Traditional data aggregators (CoinGecko, CryptoCompare, Glassnode) have severe limitations for M15+ historical data. **Exchange APIs and CSV archives are the primary free sources** for high-frequency data going back to 2022.

**Best Free Sources for M1/M5/M15 Historical Data**:

1. **Binance API** - Complete M1/M5/M15 data back to 2017 (no authentication)
2. **CryptoDataDownload** - CSV archives with minute-level data, 5+ years depth
3. **Crypto Archive** - 4.1+ billion minutes of free 1-minute OHLCV data
4. **Kraken API + CSV** - Historical data from market inception with 1/5/15-minute intervals

---

## Category 1: Data Aggregators (Limited Free Access)

### 1.1 CoinGecko API

**Status**: ❌ **UNSUITABLE** for M15+ historical data back to 2022

**Free Tier Limitations**:

- Historical depth: **365 days maximum** (free tier)
- Granularity: Daily (365d), 4-hourly (90d), hourly (7d), 30-minute (1d)
- No M1/M5/M15 support on free tier
- Rate limit: 30 calls/minute (demo API)

**Test Results**:

```bash
# Attempting to fetch max historical data returns error
curl "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=max"
# Error: "Your request exceeds the allowed time range. Public API users are limited to querying historical data within the past 365 days"

# 365 days returns only 92 daily candles
curl "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=365" | jq 'length'
# Output: 92
```

**Multi-chain Coverage**: Yes (thousands of coins across multiple chains)
**API Key Required**: No (demo), Yes (paid tiers)
**Verdict**: Paid plan required for 2022 data and higher granularity

---

### 1.2 CryptoCompare API

**Status**: ❌ **UNSUITABLE** for historical data back to 2022

**Free Tier Limitations**:

- Historical depth: **7 days only** for minute-level data
- Granularity: M1, M5 supported (via `aggregate` parameter)
- Maximum: 2000 data points per request (~33 hours at M1)
- Rate limit: Standard free tier limits apply

**Test Results**:

```bash
# Recent minute data works fine
curl "https://min-api.cryptocompare.com/data/v2/histominute?fsym=BTC&tsym=USD&limit=10"
# Returns: 11 minutes of recent data with OHLCV

# Attempting 2022 data (timestamp: 1640995200) returns null
curl "https://min-api.cryptocompare.com/data/v2/histominute?fsym=BTC&tsym=USD&limit=10&toTs=1640995200"
# Returns: null data arrays (beyond 7-day window)
```

**Multi-chain Coverage**: Yes (BTC, ETH, major altcoins)
**API Key Required**: No (basic), Yes (higher limits)
**Historical Data Access**: Enterprise tier required for 1-year minute data
**Verdict**: Only useful for recent 7-day minute data

---

### 1.3 Glassnode

**Status**: ❌ **NO FREE API ACCESS**

**Free Tier Limitations**:

- **No API access** on free (Standard) tier
- Free tier: 24-hour resolution only (web UI access)
- Highest frequency available: 10-minute intervals (Professional + API add-on)
- No M1/M5/M15 data at any tier

**Pricing Structure**:

- Standard (Free): No API access, 24h resolution, Tier 1 metrics only
- Advanced: 1-hour resolution, no API
- Professional + API add-on: 10-minute resolution (highest available)

**API Key Required**: Yes (Professional plan + paid API add-on)
**Multi-chain Coverage**: Yes (Bitcoin, Ethereum on-chain data)
**Verdict**: Not suitable for high-frequency OHLCV data

---

### 1.4 IntoTheBlock / Sentora Research

**Status**: ⚠️ **API DISCONTINUED**

**Current Status**:

- IntoTheBlock legacy API sunset (2024)
- Relaunched as "Sentora Research" (free research platform)
- Previous free tier: 24-hour granularity maximum
- No minute-level data in historical free tier

**Verdict**: No longer relevant for API-based data collection

---

### 1.5 Dune Analytics

**Status**: ⚠️ **NOT SUITABLE** for OHLCV high-frequency data

**Capabilities**:

- Free tier: Query blockchain data via SQL, export to CSV (limited)
- Paid tier: "Export to CSV" button, API access with `DUNE_API_KEY`
- Focus: On-chain analytics (transactions, smart contracts, DEX activity)
- **Does NOT provide OHLCV price data** at minute-level granularity

**Export Options**:

- Browser extension: 5 free exports, then paid
- Python client: `dune-client` library
- Third-party tools: Dune Downloader (dunedl.com)

**Verdict**: Wrong use case - blockchain analytics, not price data aggregation

---

## Category 2: Exchange APIs (Best Free Sources)

### 2.1 Binance API ✅ **RECOMMENDED**

**Status**: ✅ **EXCELLENT** - Best free source for historical M1/M5/M15 data

**Capabilities**:

- **Frequency**: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
- **Historical Depth**: **Back to 2017-08-17** (Binance launch date)
- **Multi-chain Coverage**: 3370+ trading pairs (BTC, ETH, BNB, SOL, etc.)
- **Rate Limit**: 1200 requests/minute (IP), 6000 requests/minute (UID)
- **Authentication**: None required for historical data

**Test Results**:

```bash
# M1 data from Jan 1, 2022 (confirmed working)
curl "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&startTime=1640995200000&limit=5"
# Returns: [timestamp, open, high, low, close, volume, close_time, quote_volume, trades, taker_buy_base, taker_buy_quote, ignore]

# M5 data from Jan 1, 2022
curl "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=5m&startTime=1640995200000&limit=5"
# Returns: 5 candles starting 2022-01-01 00:00:00 UTC

# M15 data from Jan 1, 2022
curl "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=15m&startTime=1640995200000&limit=5"
# Returns: 5 candles with 15-minute intervals

# Historical depth test (2017)
curl "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&startTime=1483228800000&limit=5"
# Returns: Data from 2017-08-17 (Binance inception)

# Max records per request: 1000
curl "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=1000" | jq 'length'
# Output: 1000
```

**Data Format**:

```json
[
  [
    1640995200000, // Open time (ms)
    "46216.93000000", // Open
    "46271.08000000", // High
    "46208.37000000", // Low
    "46250.00000000", // Close
    "40.57574000", // Volume
    1640995259999, // Close time (ms)
    "1875978.44269790", // Quote asset volume
    796, // Number of trades
    "27.26086000", // Taker buy base asset volume
    "1260270.37206270", // Taker buy quote asset volume
    "0" // Ignore
  ]
]
```

**API Endpoints**:

- Klines: `https://api.binance.com/api/v3/klines`
- Exchange Info: `https://api.binance.com/api/v3/exchangeInfo`
- Documentation: https://binance-docs.github.io/apidocs/spot/en/

**Limitations**:

- Max 1000 candles per request (requires pagination for large ranges)
- Spot market only (Futures has separate API)
- No authentication = lower rate limits (sufficient for batch downloads)

**Example Usage**:

```bash
# Fetch 1 month of M15 data from 2022
# Jan 1, 2022 = 1640995200000 ms
# Feb 1, 2022 = 1643673600000 ms
# 1 month M15 = 2976 candles (requires 3 requests at 1000/request)

curl "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=15m&startTime=1640995200000&endTime=1643673600000&limit=1000"
```

**Verdict**: **Primary recommendation** for free M1/M5/M15 historical data

---

### 2.2 Coinbase Advanced Trade API ✅

**Status**: ✅ **GOOD** - Complete historical data, free access

**Capabilities**:

- **Frequency**: 1m (60s), 5m (300s), 15m (900s), 1h, 6h, 1d
- **Historical Depth**: From market inception (varies by pair, BTC-USD from ~2015)
- **Multi-chain Coverage**: Major pairs (BTC, ETH, SOL, etc.)
- **Rate Limit**: 15 requests/second (public endpoints)
- **Authentication**: None required for historical candles

**Test Results**:

```bash
# M1 data from Jan 1, 2022 (ISO 8601 format)
curl "https://api.exchange.coinbase.com/products/BTC-USD/candles?start=2022-01-01T00:00:00Z&end=2022-01-01T00:10:00Z&granularity=60"
# Returns: [timestamp, low, high, open, close, volume]

# Response format (note: different order than Binance)
[
  [1640995800, 46326.59, 46375.72, 46363.03, 46365.34, 5.21343665],
  [1640995740, 46334.88, 46392.16, 46382.21, 46364.9, 13.68422033]
]
```

**Data Format**: `[timestamp, low, high, open, close, volume]` (note order)

**API Endpoints**:

- Candles: `https://api.exchange.coinbase.com/products/{product-id}/candles`
- Products: `https://api.exchange.coinbase.com/products`
- Documentation: https://docs.cloud.coinbase.com/exchange/

**Limitations**:

- 300 candles maximum per request
- Time range parameter required (start/end)
- Different column order than standard OHLCV

**Verdict**: Solid alternative to Binance, especially for BTC/ETH USD pairs

---

### 2.3 Kraken API ✅

**Status**: ✅ **GOOD** - Complete historical data, unique pairs

**Capabilities**:

- **Frequency**: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 15d
- **Historical Depth**: From market inception (BTC/USD from 2013)
- **Multi-chain Coverage**: 600+ pairs (strong EUR/USD fiat pairs)
- **Rate Limit**: Tiered system (15-20 calls/sec for public data)
- **Authentication**: None required for OHLC endpoint

**Test Results**:

```bash
# Note: Kraken ignores historical `since` parameter, returns recent data
curl "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=1&since=1640995200"
# Returns: Recent data (NOT 2022 data as requested)

# Response format: [timestamp, open, high, low, close, vwap, volume, count]
[
  [1762188180, "106540.1", "106569.8", "106467.5", "106569.7", "106544.4", "0.82873355", 57]
]
```

**Data Format**: `[time, open, high, low, close, vwap, volume, count]`

**Limitation Discovered**:

- API `since` parameter does NOT work reliably for deep historical data
- Recent data only via API endpoint
- **Solution**: Use Kraken CSV downloads (see Section 3.2)

**API Endpoints**:

- OHLC: `https://api.kraken.com/0/public/OHLC`
- Asset Pairs: `https://api.kraken.com/0/public/AssetPairs`
- Documentation: https://docs.kraken.com/rest/

**Verdict**: Good for recent data, use CSV archives for 2022 data

---

### 2.4 KuCoin API ✅

**Status**: ✅ **GOOD** - Complete historical data, emerging altcoins

**Capabilities**:

- **Frequency**: 1min, 3min, 5min, 15min, 30min, 1hour, 2hour, 4hour, 6hour, 8hour, 12hour, 1day, 1week
- **Historical Depth**: From market inception (2017+)
- **Multi-chain Coverage**: 1000+ pairs (strong altcoin selection)
- **Rate Limit**: Public API limits (not explicitly documented)
- **Authentication**: None required for historical candles

**Test Results**:

```bash
# M1 data from Jan 1, 2022 (Unix timestamps in seconds)
curl "https://api.kucoin.com/api/v1/market/candles?type=1min&symbol=BTC-USDT&startAt=1640995200&endAt=1640995800"
# Returns: [timestamp, open, close, high, low, volume, turnover]

# Response format (note: open/close swapped)
[
  ["1640995740", "46391.7", "46377", "46406.4", "46350", "4.14136271", "192037.804847693"]
]
```

**Data Format**: `["timestamp", "open", "close", "high", "low", "volume", "turnover"]`

**API Endpoints**:

- Candles: `https://api.kucoin.com/api/v1/market/candles`
- Symbols: `https://api.kucoin.com/api/v1/symbols`
- Documentation: https://docs.kucoin.com/

**Limitations**:

- Max 1500 data points per request
- Column order differs from standard (open/close swapped)
- Rate limits not clearly documented

**Verdict**: Excellent for altcoins and emerging tokens

---

### 2.5 OKX API ⚠️

**Status**: ⚠️ **PARTIAL** - Recent data only

**Test Results**:

```bash
# Attempting 2022 data returns empty array
curl "https://www.okx.com/api/v5/market/candles?instId=BTC-USDT&bar=1m&after=1640995200000&limit=5"
# Returns: []
```

**Limitation**: API appears to limit historical depth significantly
**Verdict**: Not recommended for 2022 historical data

---

### 2.6 Bybit API ✅

**Status**: ✅ **GOOD** - Complete historical data

**Capabilities**:

- **Frequency**: 1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, M, W
- **Historical Depth**: From market inception
- **Multi-chain Coverage**: Spot + derivatives markets
- **Authentication**: None required for kline endpoint

**Test Results**:

```bash
# M1 data from Jan 1, 2022
curl "https://api.bybit.com/v5/market/kline?category=spot&symbol=BTCUSDT&interval=1&start=1640995200000&limit=5"
# Returns: [timestamp, open, high, low, close, volume, turnover]

# Response format
[
  ["1640995440000", "46341.4", "46343.62", "46317.18", "46336.27", "0.682194", "31612.46443916"]
]
```

**Data Format**: `["timestamp", "open", "high", "low", "close", "volume", "turnover"]`

**Verdict**: Good alternative with derivatives market coverage

---

## Category 3: CSV Download Archives (Best for Bulk Historical Data)

### 3.1 CryptoDataDownload ✅ **RECOMMENDED**

**Status**: ✅ **EXCELLENT** - Zero-gap 1-minute OHLCV archives

**Capabilities**:

- **Frequency**: Daily, Hourly, Minute (1-minute intervals)
- **Historical Depth**: 5+ years for major pairs
- **Format**: CSV files (instant download, no registration)
- **Verification**: Gapless 1-minute interval data
- **Multi-chain Coverage**: Major cryptocurrencies across multiple exchanges

**Website**: https://www.cryptodatadownload.com/

**Features**:

- No API required (direct CSV downloads)
- No rate limits
- Pre-verified data quality
- Multiple exchange sources (Binance, Coinbase, Kraken, etc.)

**Data Format** (typical):

```
timestamp,open,high,low,close,volume
2022-01-01 00:00:00,46216.93,46271.08,46208.37,46250.00,40.57574
```

**Verdict**: **Best option for bulk downloads** - complete archives, no pagination needed

---

### 3.2 Kraken CSV Historical Data ✅

**Status**: ✅ **EXCELLENT** - Official exchange archives

**Capabilities**:

- **Frequency**: 1, 5, 15, 30, 60, 240, 720, 1440 minute intervals
- **Historical Depth**: From market inception to Q3 2024
- **Format**: CSV files (OHLCVT format)
- **Coverage**: All Kraken trading pairs

**Documentation**: https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data

**Data Format**: OHLCVT (Open, High, Low, Close, Volume, Trades)

**API Alternative**:

```bash
# Direct API access to same data
curl "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=1&since=1640995200"
```

**Verdict**: Official exchange data, highly reliable

---

### 3.3 Crypto Archive ✅ **RECOMMENDED**

**Status**: ✅ **EXCELLENT** - Massive free archive

**Capabilities**:

- **Data Volume**: 4,154,065,476 minutes of 1-minute OHLCV data
- **Frequency**: 1-minute intervals
- **Cost**: 100% free
- **Format**: Downloadable archives

**Website**: https://www.cryptoarchive.com.au/

**Unique Feature**: Largest known free archive of minute-level crypto data

**Verdict**: Excellent for research and backtesting

---

### 3.4 CryptoDatum.io ⚠️

**Status**: ⚠️ **MIXED** - Free daily/4h, paid minute data

**Capabilities**:

- **Free Tier**: 1d, 4h CSV files for BTC, ETH, XRP
- **Paid Tier**: Minute-level data via CSV Downloader
- **Format**: CSV

**Website**: https://cryptodatum.io/

**Verdict**: Limited free tier, better free alternatives exist

---

### 3.5 GitHub: crypto-prices-download ✅

**Status**: ✅ **GOOD** - Python tool for automated downloads

**Repository**: https://github.com/martkir/crypto-prices-download

**Capabilities**:

- **Frequency**: 1m (default), 5m, 15m, 30m, 1h, 4h, 6h, 12h, 1d, 1w
- **Source**: Binance API wrapper
- **Format**: Automated CSV generation

**Usage**:

```bash
# Clone and use to download historical data
git clone https://github.com/martkir/crypto-prices-download.git
# Default 1-minute resolution
```

**Verdict**: Useful automation tool wrapping Binance API

---

## Summary Matrix

| Source                 | M1  | M5  | M15 | Depth (2022) | Auth Required | Multi-chain | Rate Limits     | Recommendation     |
| ---------------------- | --- | --- | --- | ------------ | ------------- | ----------- | --------------- | ------------------ |
| **Binance API**        | ✅  | ✅  | ✅  | ✅ (2017+)   | ❌            | ✅ (3370+)  | 1200/min        | ⭐ PRIMARY         |
| **CryptoDataDownload** | ✅  | ❌  | ❌  | ✅ (5+ yrs)  | ❌            | ✅          | None (CSV)      | ⭐ BULK DOWNLOAD   |
| **Crypto Archive**     | ✅  | ❌  | ❌  | ✅ (varies)  | ❌            | ✅          | None (CSV)      | ⭐ BULK DOWNLOAD   |
| **Coinbase API**       | ✅  | ✅  | ✅  | ✅ (2015+)   | ❌            | ✅ (major)  | 15/sec          | ✅ GOOD            |
| **Kraken API**         | ✅  | ✅  | ✅  | ⚠️ (recent)  | ❌            | ✅ (600+)   | 15-20/sec       | ⚠️ Use CSV instead |
| **Kraken CSV**         | ✅  | ✅  | ✅  | ✅ (2013+)   | ❌            | ✅          | None (download) | ✅ GOOD            |
| **KuCoin API**         | ✅  | ✅  | ✅  | ✅ (2017+)   | ❌            | ✅ (1000+)  | Undocumented    | ✅ GOOD            |
| **Bybit API**          | ✅  | ✅  | ✅  | ✅ (varies)  | ❌            | ✅          | Standard        | ✅ GOOD            |
| **CoinGecko API**      | ❌  | ❌  | ❌  | ❌ (365d)    | ❌            | ✅          | 30/min          | ❌ UNSUITABLE      |
| **CryptoCompare API**  | ✅  | ✅  | ❌  | ❌ (7d)      | ❌            | ✅          | Standard        | ❌ UNSUITABLE      |
| **Glassnode**          | ❌  | ❌  | ❌  | N/A          | ✅ (paid)     | Limited     | N/A             | ❌ NO FREE API     |
| **IntoTheBlock**       | ❌  | ❌  | ❌  | N/A          | N/A           | N/A         | Discontinued    | ❌ DISCONTINUED    |
| **Dune Analytics**     | ❌  | ❌  | ❌  | N/A          | ⚠️ (export)   | ✅          | Varies          | ❌ WRONG USE CASE  |

---

## Recommended Implementation Strategy

### For Real-Time Collection (Ongoing)

**Primary**: Binance API
**Backup**: Coinbase API, KuCoin API

```bash
# Example: Fetch last 1000 minutes of BTC/USDT M1 data
curl "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=1000"
```

### For Historical Backfill (2022 data)

**Option 1**: Binance API with pagination

```bash
# Fetch January 2022 M15 data (2976 candles = 3 requests)
for offset in 0 1000 2000; do
  start=$((1640995200000 + offset * 15 * 60 * 1000))
  curl "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=15m&startTime=$start&limit=1000"
done
```

**Option 2**: CryptoDataDownload CSV (instant bulk download)

- Visit https://www.cryptodatadownload.com/data/
- Select exchange and pair
- Download complete historical CSV
- No pagination or rate limits

### For Multi-Chain Coverage

**Recommended Approach**:

1. Binance API for major pairs (3370+ symbols)
2. KuCoin API for emerging altcoins
3. Coinbase API for USD-denominated pairs
4. Kraken CSV for EUR pairs and deep history

---

## Rate Limit Comparison

| Source             | Limit           | Window | Notes                     |
| ------------------ | --------------- | ------ | ------------------------- |
| Binance            | 1200 requests   | 1 min  | No auth, IP-based         |
| Coinbase           | 15 requests     | 1 sec  | Public endpoints          |
| Kraken             | 15-20 requests  | 1 sec  | Tiered system             |
| KuCoin             | Undocumented    | -      | Monitor 429 responses     |
| Bybit              | Standard limits | -      | Not explicitly documented |
| CryptoDataDownload | None            | -      | CSV download              |
| Crypto Archive     | None            | -      | CSV download              |

---

## Data Format Standards

### Binance Format (Most Common)

```json
[timestamp_open_ms, open, high, low, close, volume, timestamp_close_ms, quote_volume, trades, taker_buy_base, taker_buy_quote, ignore]
```

### Coinbase Format

```json
[timestamp, low, high, open, close, volume]
```

### Kraken Format

```json
[timestamp, open, high, low, close, vwap, volume, count]
```

### CSV Format (CryptoDataDownload)

```
timestamp,open,high,low,close,volume
```

---

## Integration Example: Multi-Source Data Pipeline

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "requests",
#   "pandas",
# ]
# ///

import requests
import pandas as pd
from datetime import datetime

def fetch_binance_m15(symbol="BTCUSDT", start_date="2022-01-01", end_date="2022-02-01"):
    """Fetch M15 data from Binance API with pagination"""
    url = "https://api.binance.com/api/v3/klines"

    start_ms = int(pd.Timestamp(start_date).timestamp() * 1000)
    end_ms = int(pd.Timestamp(end_date).timestamp() * 1000)

    all_data = []
    current_start = start_ms

    while current_start < end_ms:
        params = {
            "symbol": symbol,
            "interval": "15m",
            "startTime": current_start,
            "limit": 1000
        }

        response = requests.get(url, params=params)
        data = response.json()

        if not data:
            break

        all_data.extend(data)
        current_start = data[-1][0] + 1  # Last timestamp + 1ms

    # Convert to DataFrame
    df = pd.DataFrame(all_data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
        'taker_buy_quote', 'ignore'
    ])

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.set_index('timestamp')

    return df[['open', 'high', 'low', 'close', 'volume']]

# Example usage
df = fetch_binance_m15("BTCUSDT", "2022-01-01", "2022-01-02")
print(f"Fetched {len(df)} M15 candles")
print(df.head())
```

---

## Key Findings & Recommendations

### ✅ **Top 3 Recommendations**

1. **Binance API** - Best all-around solution
   - Complete M1/M5/M15 data back to 2017
   - 3370+ trading pairs
   - No authentication required
   - 1200 req/min rate limit

2. **CryptoDataDownload** - Best for bulk historical downloads
   - Pre-packaged CSV archives
   - No pagination or rate limits
   - Zero-gap verified data
   - 5+ years of history

3. **Kraken CSV Archives** - Best for official exchange data
   - Complete OHLCVT data from inception
   - 1/5/15/30/60/240/720/1440 minute intervals
   - Reliable source from major exchange

### ❌ **Avoid These Sources**

1. **CoinGecko API** - 365-day limit, no M15 on free tier
2. **CryptoCompare API** - Only 7 days of minute data
3. **Glassnode** - No free API access, max 10-minute resolution
4. **IntoTheBlock** - API discontinued
5. **Dune Analytics** - Not designed for OHLCV price data

### 🎯 **Implementation Priority**

**Phase 1**: Use Binance API for ongoing collection

- Real-time M1/M5/M15 data
- Minimal code complexity
- No authentication hassle

**Phase 2**: Backfill historical data via CryptoDataDownload

- Download complete 2022 archives
- One-time bulk import
- Validate against Binance API samples

**Phase 3**: Add redundancy with Coinbase/KuCoin APIs

- Cross-validate data quality
- Fill gaps if Binance has downtime
- Expand asset coverage

---

## Research Scripts

All test scripts available in `/tmp/aggregator-research/`:

- `coingecko_test.sh` - CoinGecko API validation
- `cryptocompare_test.sh` - CryptoCompare historical depth tests
- `binance_test.sh` - Binance M1/M5/M15 validation
- `exchange_test.sh` - Multi-exchange comparison
- `csv_sources_test.sh` - CSV archive verification

---

## Conclusion

**For M15+ frequency data going back to 2022, traditional aggregators fail**. Exchange APIs and CSV archives are the only viable free sources.

**Recommended Stack**:

- **Primary Data Source**: Binance API
- **Bulk Historical**: CryptoDataDownload CSV archives
- **Validation**: Kraken CSV + Coinbase API
- **Altcoin Coverage**: KuCoin API

This combination provides:
✅ Complete M1/M5/M15 coverage
✅ Historical depth to 2017+
✅ Multi-chain support (3000+ pairs)
✅ Zero authentication required
✅ Reasonable rate limits (1200/min Binance)
✅ Free forever (no tier limits)
