# Gapless Network Data

Ethereum blockchain network metrics for financial time series forecasting.

## Quick Start

```python
import gapless_network_data as gmd

# Fetch latest blocks (recommended for live trading)
df = gmd.fetch_blocks(limit=1000)

# Compute block utilization (alpha feature #2)
df['utilization'] = df['gas_used'] / df['gas_limit']

# Date range query
df = gmd.fetch_blocks(start='2024-01-01', end='2024-01-31')
```

## Installation

```bash
pip install gapless-network-data
```

## AI Agent Discoverability

This package is optimized for Claude Code CLI and AI coding agents.

### Probe Module

```python
import gapless_network_data as gmd

# Get ranked features for ML pipelines
features = gmd.probe.get_alpha_features()
for f in features[:5]:
    print(f"{f.rank}. {f.name} ({f.importance})")

# Get protocol era boundaries
eras = gmd.probe.get_protocol_eras()

# Get setup workflow
workflow = gmd.probe.get_setup_workflow()

# Get example code
print(gmd.probe.get_quick_start())
```

## Alpha Feature Rankings

AI agents should prioritize these features for ML pipelines:

| Rank | Feature           | Importance | Formula              |
| ---- | ----------------- | ---------- | -------------------- |
| 1    | base_fee_per_gas  | critical   | raw                  |
| 2    | block_utilization | critical   | gas_used / gas_limit |
| 3    | transaction_count | high       | raw                  |
| 4    | timestamp         | high       | raw                  |
| 5    | number            | high       | raw                  |
| 6    | size              | medium     | raw                  |
| 7    | blob_gas_used     | medium     | raw (post-EIP4844)   |
| 8    | excess_blob_gas   | low        | raw (post-EIP4844)   |
| 9    | gas_limit         | low        | raw                  |
| 10   | gas_used          | low        | raw                  |

Get rankings programmatically: `gmd.probe.get_alpha_features()`

## Protocol Era Boundaries

Filter data appropriately based on protocol changes:

- **EIP-1559** (block 12,965,000, Aug 2021): base_fee_per_gas introduced
- **The Merge** (block 15,537,394, Sep 2022): difficulty=0 forever
- **EIP-4844** (block 19,426,587, Mar 2024): blob_gas fields introduced

Get eras programmatically: `gmd.probe.get_protocol_eras()`

## API Reference

### fetch_blocks()

```python
gmd.fetch_blocks(
    start: str | None = None,     # ISO 8601 date
    end: str | None = None,       # ISO 8601 date
    limit: int | None = None,     # Max blocks
    include_deprecated: bool = False  # Include difficulty fields
) -> pd.DataFrame
```

Returns pandas DataFrame with columns:

- timestamp (datetime64[ns, UTC])
- number (uint64)
- gas_limit, gas_used, base_fee_per_gas, transaction_count, size (uint64)
- blob_gas_used, excess_blob_gas (uint64, nullable)

### Deprecated Fields

Excluded by default (use `include_deprecated=True` for pre-Merge analysis):

- `difficulty`: Always 0 post-Merge (Sep 2022)
- `total_difficulty`: Frozen post-Merge

## Setup

Credentials via Doppler (recommended) or environment variables.

```bash
# Option 1: Doppler (team setup)
doppler configure set token <token_from_1password>
doppler setup --project gapless-network-data --config prd

# Option 2: Environment variables
export CLICKHOUSE_HOST_READONLY=<host>
export CLICKHOUSE_USER_READONLY=<user>
export CLICKHOUSE_PASSWORD_READONLY=<password>
```

Get setup instructions: `gmd.probe.get_setup_workflow()`

## Data Coverage

- **Blocks**: 23.87M Ethereum blocks (2015-2025)
- **Update frequency**: Real-time (~12 second intervals)
- **Storage**: ClickHouse Cloud (AWS)
- **Deduplication**: Automatic via ReplacingMergeTree

## Exceptions

All exceptions include structured context (timestamp, endpoint, HTTP status):

- `CredentialException`: Credential resolution failed
- `DatabaseException`: ClickHouse query failed
- `MempoolException`: Base exception class

## Feature Engineering Integration

Combine with OHLCV price data:

```python
import gapless_crypto_data as gcd
import gapless_network_data as gmd

# Fetch both data sources
df_ohlcv = gcd.get_data(symbol="ETHUSDT", timeframe="1m", start_date="2024-01-01")
df_blocks = gmd.fetch_blocks(start="2024-01-01", end="2024-01-02")

# Temporal alignment (forward-fill prevents data leakage)
df_blocks_aligned = df_blocks.set_index('timestamp').reindex(
    df_ohlcv.index, method='ffill'
)

# Join and engineer features
df = df_ohlcv.join(df_blocks_aligned)
df['gas_pressure'] = df['base_fee_per_gas'] / df['base_fee_per_gas'].rolling(60).median()
df['block_utilization'] = df['gas_used'] / df['gas_limit']
```

## Infrastructure (Reference)

Dual-pipeline architecture for production reliability:

| Component           | Purpose                          | Technology       |
| ------------------- | -------------------------------- | ---------------- |
| BigQuery Sync       | Hourly batch from public dataset | Cloud Run Job    |
| Real-Time Collector | Block-level streaming            | e2-micro VM      |
| Database            | Storage with deduplication       | ClickHouse Cloud |
| Monitoring          | Dead Man's Switch                | Healthchecks.io  |

## Related Projects

- [gapless-crypto-data](https://github.com/terrylica/gapless-crypto-data) - OHLCV data collection
- [BigQuery Ethereum Dataset](https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=crypto_ethereum)

## Documentation

- [Architecture Overview](https://github.com/terrylica/gapless-network-data/blob/main/docs/architecture/README.md)
- [Data Format Specification](https://github.com/terrylica/gapless-network-data/blob/main/docs/architecture/DATA_FORMAT.md)

## License

[MIT License](https://github.com/terrylica/gapless-network-data/blob/main/LICENSE)
