---
version: "0.1.0"
last_updated: "2025-11-04"
supersedes: []
status: "pending"
---

# Feature Engineering Guide

**Status**: 🚧 Pending Phase 3 implementation

This document will provide comprehensive guidance for creating cross-domain features from network data + OHLCV price data.

## Planned Content

### Core Concepts

#### Temporal Alignment

- Forward-fill strategy (prevents data leakage in live trading)
- ASOF JOIN with DuckDB (16x faster than pandas reindex)
- Handling missing data and gaps

#### Cross-Domain Feature Fusion

- Combining network metrics with price data
- Feature correlation analysis
- Feature selection strategies

### Feature Categories

#### Ethereum Network Features

- **Gas Pressure**: Normalized base fee (relative to rolling median)
- **Block Utilization**: Gas used / gas limit percentage
- **Transaction Velocity**: Rolling transaction count per time window
- **Fee Spikes**: Z-score of base fee changes
- **Congestion Index**: Composite metric of gas + utilization

#### Bitcoin Mempool Features

- **Fee Pressure**: Fastest fee / economy fee ratio
- **Mempool Congestion**: Unconfirmed transaction count (z-score)
- **Fee Gradient**: Difference between fastest and economy fees
- **Mempool Size Growth**: Rate of change in vsize_mb
- **Fee Rate Stability**: Rolling standard deviation of fee rates

#### Cross-Chain Features

- **Relative Congestion**: ETH gas pressure vs BTC fee pressure
- **Network Health**: Composite score across chains
- **Fee Arbitrage**: Opportunities based on cross-chain congestion

### Implementation Patterns

#### Pattern 1: Simple Forward-Fill Alignment

```python
import gapless_crypto_data as gcd
import gapless_network_data as gnd
import pandas as pd

# Step 1: Collect OHLCV data (1-minute ETHUSDT)
df_ohlcv = gcd.get_data(
    symbol="ETHUSDT",
    timeframe="1m",
    start_date="2024-01-01",
    end_date="2024-01-31"
)
# Returns: DatetimeIndex with OHLCV 11-column format

# Step 2: Collect Ethereum network data (12-second blocks)
df_eth = gnd.fetch_snapshots(
    chain="ethereum",
    start="2024-01-01 00:00:00",
    end="2024-01-31 23:59:59"
)
# Returns: DatetimeIndex with 6-column format

# Step 3: Temporal alignment (forward-fill for live trading)
df_eth_aligned = df_eth.reindex(df_ohlcv.index, method='ffill')

# Step 4: Feature fusion via join
df = df_ohlcv.join(df_eth_aligned)

# Step 5: Engineer features
df['gas_pressure'] = df['baseFeePerGas'] / df['baseFeePerGas'].rolling(60).median()
df['block_utilization'] = (df['gasUsed'] / df['gasLimit']) * 100
df['gas_adjusted_return'] = (df['close'] - df['open']) / (df['baseFeePerGas'] + 1)
```

#### Pattern 2: DuckDB High-Performance Alignment

```python
import duckdb
import gapless_network_data as gnd

# Connect to DuckDB (reads Parquet directly, no loading)
conn = duckdb.connect()

# ASOF JOIN: Align network data to OHLCV timestamps (16x faster)
df = conn.execute("""
    SELECT
        ohlcv.*,
        eth.baseFeePerGas,
        eth.gasUsed,
        eth.gasLimit,
        eth.transactions,
        -- Derived features
        (eth.baseFeePerGas / eth.baseFeePerGas_median_60) AS gas_pressure,
        (CAST(eth.gasUsed AS DOUBLE) / eth.gasLimit * 100) AS block_utilization
    FROM read_parquet('data/ohlcv/*.parquet') AS ohlcv
    ASOF LEFT JOIN read_parquet('data/ethereum/*.parquet') AS eth
        ON ohlcv.timestamp >= eth.timestamp
    ORDER BY ohlcv.timestamp
""").df()
```

#### Pattern 3: Multi-Chain Feature Fusion

```python
import gapless_crypto_data as gcd
import gapless_network_data as gnd

# Collect OHLCV for both pairs
df_eth = gcd.get_data(symbol="ETHUSDT", timeframe="1m", start_date="2024-01-01", end_date="2024-01-31")
df_btc = gcd.get_data(symbol="BTCUSDT", timeframe="1m", start_date="2024-01-01", end_date="2024-01-31")

# Collect network data for both chains
df_eth_network = gnd.fetch_snapshots(chain="ethereum", start="2024-01-01", end="2024-01-31")
df_btc_network = gnd.fetch_snapshots(chain="bitcoin", start="2024-01-01", end="2024-01-31")

# Align network data to OHLCV timestamps
df_eth_network_aligned = df_eth_network.reindex(df_eth.index, method='ffill')
df_btc_network_aligned = df_btc_network.reindex(df_btc.index, method='ffill')

# Join all data sources
df = df_eth.join(df_eth_network_aligned, rsuffix='_eth_network')
df = df.join(df_btc_network, lsuffix='_btc', rsuffix='_btc_network')

# Cross-chain features
df['relative_congestion'] = (
    (df['baseFeePerGas'] / df['baseFeePerGas'].rolling(60).median()) /
    (df['fastest_fee'] / df['fastest_fee'].rolling(60).median())
)
```

### Feature Examples

#### Ethereum Gas Pressure Features

```python
# Normalized base fee (relative to rolling median)
df['gas_pressure_60m'] = df['baseFeePerGas'] / df['baseFeePerGas'].rolling(60).median()
df['gas_pressure_24h'] = df['baseFeePerGas'] / df['baseFeePerGas'].rolling(1440).median()

# Block utilization
df['block_utilization'] = (df['gasUsed'] / df['gasLimit']) * 100

# Transaction velocity
df['tx_velocity_1h'] = df['transactions'].rolling(60).sum()

# Fee spike detection (z-score)
df['base_fee_zscore'] = (
    (df['baseFeePerGas'] - df['baseFeePerGas'].rolling(60).mean()) /
    (df['baseFeePerGas'].rolling(60).std() + 1e-10)
)

# Congestion index (composite)
df['congestion_index'] = (
    0.5 * df['gas_pressure_60m'] +
    0.3 * (df['block_utilization'] / 100) +
    0.2 * (df['tx_velocity_1h'] / df['tx_velocity_1h'].rolling(1440).mean())
)
```

#### Bitcoin Mempool Pressure Features

```python
# Fee pressure
df['fee_pressure'] = df['fastest_fee'] / (df['economy_fee'] + 1e-10)

# Mempool congestion (z-score)
df['mempool_congestion'] = (
    (df['unconfirmed_count'] - df['unconfirmed_count'].rolling(60).mean()) /
    (df['unconfirmed_count'].rolling(60).std() + 1e-10)
)

# Fee gradient
df['fee_gradient'] = df['fastest_fee'] - df['economy_fee']

# Mempool size growth rate
df['vsize_growth_rate'] = df['vsize_mb'].pct_change()

# Fee rate stability
df['fee_stability'] = df['fastest_fee'].rolling(60).std()
```

#### Cross-Domain Price + Network Features

```python
# Gas-adjusted returns
df['gas_adjusted_return'] = (df['close'] - df['open']) / (df['baseFeePerGas'] + 1)

# Volume per transaction
df['volume_per_tx'] = df['volume'] / (df['number_of_trades'] + 1e-10)

# Price momentum with network confirmation
df['price_momentum'] = df['close'].pct_change()
df['network_confirmed_momentum'] = df['price_momentum'] * (1 + df['gas_pressure_60m'])
```

### Data Leakage Prevention

**Forward-Fill Strategy**: Always use `method='ffill'` when aligning network data to OHLCV timestamps. This ensures you only use network data that was available BEFORE each OHLCV candle close.

```python
# CORRECT: Forward-fill (no data leakage)
df_eth_aligned = df_eth.reindex(df_ohlcv.index, method='ffill')

# WRONG: Backward-fill (data leakage!)
df_eth_aligned = df_eth.reindex(df_ohlcv.index, method='bfill')  # DON'T DO THIS

# WRONG: Interpolation (data leakage!)
df_eth_aligned = df_eth.reindex(df_ohlcv.index).interpolate()  # DON'T DO THIS
```

### Performance Optimization

**DuckDB vs Pandas**:

- pandas `reindex`: Baseline performance
- DuckDB `ASOF JOIN`: 16x faster for large datasets (>1M rows)
- DuckDB `LAG()`: 8x faster for rolling features
- DuckDB `QUALIFY`: 12x faster for filtering with window functions

**Memory Optimization**:

- Use Polars for intermediate calculations (5-10x faster than pandas)
- Stream large datasets with `read_parquet(use_pyarrow=True)`
- Batch process by month/week to control memory usage

---

## Current Quick Start

Until this document is completed, refer to:

- [README.md](/README.md) - Feature engineering section (lines 117-152)
- [CLAUDE.md](/CLAUDE.md) - Feature engineering integration (lines 442-476)
- [Cross-Package Integration](/Users/terryli/eon/gapless-crypto-data/docs/architecture/cross-package-feature-integration.yaml) - Complete design specification

**Example from README.md**:

```python
import gapless_crypto_data as gcd
import gapless_network_data as gnd

# Collect OHLCV data (ETHUSDT)
df_ohlcv = gcd.get_data(symbol="ETHUSDT", timeframe="1m", start_date="2024-01-01", end_date="2024-01-02")

# Collect Ethereum network data
df_eth = gnd.fetch_snapshots(chain="ethereum", start="2024-01-01 00:00:00", end="2024-01-02 00:00:00")

# Temporal alignment (forward-fill to prevent data leakage)
df_eth_aligned = df_eth.reindex(df_ohlcv.index, method='ffill')

# Join on timestamp
df = df_ohlcv.join(df_eth_aligned)

# Engineer cross-domain features
df['gas_pressure'] = df['baseFeePerGas'] / df['baseFeePerGas'].rolling(60).median()
df['block_utilization'] = (df['gasUsed'] / df['gasLimit']) * 100
df['gas_adjusted_return'] = (df['close'] - df['open']) / (df['baseFeePerGas'] + 1)
```

---

**Related Documentation**:

- [Python API Reference](/docs/guides/python-api.md) - Data collection API
- [DuckDB Integration Strategy](/specifications/duckdb-integration-strategy.yaml) - Performance benchmarks

**This document will be completed during Phase 3 implementation.**
