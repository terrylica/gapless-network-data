# Gapless Network Data

Multi-chain blockchain network metrics collection with zero-gap guarantee for feature engineering in cryptocurrency trading and ML pipelines.

## Overview

Gapless Network Data provides high-frequency blockchain network data with complete historical backfill support. Collect network congestion metrics (gas prices, mempool pressure, block data) from multiple blockchains with validated gap detection and automated recovery.

**Primary Data Source**: Ethereum via LlamaRPC (block-level, ~12 second intervals)

**Secondary Data Source**: Bitcoin via mempool.space (mempool snapshots, 5-minute intervals)

**Key Features**:

- Multi-chain support (Ethereum PRIMARY, Bitcoin, extensible to Solana/Avalanche/Polygon)
- Zero-gap data collection with automated backfill
- DuckDB-based validation storage for quality assurance
- Parquet output format with snappy compression
- Temporal alignment utilities for feature engineering
- Complete type safety (PEP 561 compliant)
- web3.py integration for Ethereum RPC calls

## Installation

```bash
pip install gapless-network-data
```

## Quick Start

### Python API - Ethereum (Primary)

```python
import gapless_network_data as gnd

# Fetch Ethereum block data (12-second intervals)
df_eth = gnd.fetch_snapshots(
    chain="ethereum",
    start="2024-01-01 00:00:00",
    end="2024-01-01 06:00:00"
)

# Get latest Ethereum block
block = gnd.get_latest_snapshot(chain="ethereum")
print(f"Block number: {block['number']}")
print(f"Base fee: {block['baseFeePerGas']} wei")
print(f"Gas used: {block['gasUsed']:,}")
```

### Python API - Bitcoin (Secondary)

```python
# Fetch Bitcoin mempool snapshots (5-minute intervals)
df_btc = gnd.fetch_snapshots(
    chain="bitcoin",
    start="2024-01-01 00:00:00",
    end="2024-01-01 06:00:00"
)

# Get latest Bitcoin mempool snapshot
snapshot = gnd.get_latest_snapshot(chain="bitcoin")
print(f"Unconfirmed txs: {snapshot['unconfirmed_count']}")
print(f"Fastest fee: {snapshot['fastest_fee']} sat/vB")
```

### CLI

```bash
# Collect Ethereum block data
gapless-network-data collect \
    --chain ethereum \
    --start 2024-01-01 \
    --end 2024-01-02 \
    --output-dir ./data

# Stream live Ethereum blocks
gapless-network-data stream \
    --chain ethereum \
    --output-dir ./data

# Collect Bitcoin mempool data
gapless-network-data collect \
    --chain bitcoin \
    --start 2024-01-01 \
    --end 2024-01-02 \
    --output-dir ./data
```

## Data Schemas

### Ethereum Block Data (12-second intervals)

| Field             | Type     | Description                          |
| ----------------- | -------- | ------------------------------------ |
| `number`          | int      | Block number                         |
| `timestamp`       | datetime | UTC timestamp (ISO 8601)             |
| `baseFeePerGas`   | int      | Base fee per gas (wei)               |
| `gasUsed`         | int      | Total gas used in block              |
| `gasLimit`        | int      | Block gas limit                      |
| `transactions`    | int      | Number of transactions in block      |

### Bitcoin Mempool Data (5-minute intervals)

| Field               | Type     | Description                               |
| ------------------- | -------- | ----------------------------------------- |
| `timestamp`         | datetime | UTC timestamp (ISO 8601)                  |
| `unconfirmed_count` | int      | Number of unconfirmed transactions        |
| `vsize_mb`          | float    | Total mempool virtual size (MB)           |
| `total_fee_btc`     | float    | Total fees in mempool (BTC)               |
| `fastest_fee`       | float    | Fee rate for next block (sat/vB)          |
| `half_hour_fee`     | float    | Fee rate for ~30min confirmation (sat/vB) |
| `hour_fee`          | float    | Fee rate for ~1hr confirmation (sat/vB)   |
| `economy_fee`       | float    | Fee rate for low-priority tx (sat/vB)     |
| `minimum_fee`       | float    | Minimum relay fee (sat/vB)                |

## Feature Engineering

Gapless Network Data integrates with [gapless-crypto-data](https://github.com/terrylica/gapless-crypto-data) for cross-domain feature engineering:

```python
import gapless_crypto_data as gcd
import gapless_network_data as gnd
import pandas as pd

# Collect OHLCV data (ETHUSDT)
df_ohlcv = gcd.get_data(
    symbol="ETHUSDT",
    timeframe="1m",
    start_date="2024-01-01",
    end_date="2024-01-02"
)

# Collect Ethereum network data
df_eth = gnd.fetch_snapshots(
    chain="ethereum",
    start="2024-01-01 00:00:00",
    end="2024-01-02 00:00:00"
)

# Temporal alignment (forward-fill to prevent data leakage)
df_eth_aligned = df_eth.reindex(df_ohlcv.index, method='ffill')

# Join on timestamp
df = df_ohlcv.join(df_eth_aligned)

# Engineer cross-domain features
df['gas_pressure'] = df['baseFeePerGas'] / df['baseFeePerGas'].rolling(60).median()
df['block_utilization'] = (df['gasUsed'] / df['gasLimit']) * 100
df['gas_adjusted_return'] = (df['close'] - df['open']) / (df['baseFeePerGas'] + 1)
```

See [examples/feature_integration.py](examples/feature_integration.py) for complete workflow.

## Architecture

- **Collectors**:
  - Ethereum: web3.py with LlamaRPC endpoint
  - Bitcoin: mempool.space REST API client with ETag caching
- **Validation**: 5-layer pipeline (HTTP/RPC, schema, sanity, gap detection, anomaly detection)
- **Storage**: DuckDB for validation reports, Parquet for raw data
- **Resilience**: Exponential backoff retry, automatic gap recovery

## Documentation

- [API Reference](docs/guides/python-api.md)
- [Data Collection Guide](docs/guides/DATA_COLLECTION.md)
- [Validation System](docs/validation/OVERVIEW.md)
- [Architecture Overview](docs/architecture/OVERVIEW.md)
- [LlamaRPC Research](docs/llamarpc/INDEX.md) - Comprehensive Ethereum RPC analysis

## Requirements

- Python 3.9+
- Dependencies: httpx, polars, pandas, duckdb, pydantic, web3, tenacity

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Projects

- [gapless-crypto-data](https://github.com/terrylica/gapless-crypto-data) - OHLCV data collection
- [mempool.space](https://mempool.space) - Bitcoin data source
- [LlamaRPC](https://llamarpc.com) - Ethereum data source

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
