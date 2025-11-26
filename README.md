# Gapless Network Data

Ethereum blockchain network metrics collection infrastructure with dual-pipeline architecture.

## Installation

```bash
pip install gapless-network-data
```

## Overview

Collects Ethereum block-level network metrics with real-time updates at block intervals (approximately 12 seconds). Data stored in ClickHouse Cloud with automatic deduplication.

**Architecture**: BigQuery hourly batch + Alchemy real-time WebSocket

**Data Range**: Genesis block (2015) to present

**Cost**: All components operate within free tier limits

## Data Access

```python
import clickhouse_connect

client = clickhouse_connect.get_client(
    host='your-host.aws.clickhouse.cloud',
    port=8443,
    username='default',
    password=password,
    secure=True
)

# Query latest blocks
result = client.query_df("""
    SELECT
        timestamp,
        number,
        base_fee_per_gas,
        gas_used,
        gas_limit,
        transaction_count
    FROM ethereum_mainnet.blocks FINAL
    ORDER BY number DESC
    LIMIT 10
""")
```

## Schema

11 columns for ML feature engineering:

| Column              | Type      | Description                |
| ------------------- | --------- | -------------------------- |
| `timestamp`         | TIMESTAMP | UTC timestamp              |
| `number`            | BIGINT    | Block number (PRIMARY KEY) |
| `gas_limit`         | BIGINT    | Block gas limit            |
| `gas_used`          | BIGINT    | Total gas used             |
| `base_fee_per_gas`  | BIGINT    | EIP-1559 base fee (wei)    |
| `transaction_count` | BIGINT    | Number of transactions     |
| `difficulty`        | HUGEINT   | Mining/staking difficulty  |
| `total_difficulty`  | HUGEINT   | Cumulative chain work      |
| `size`              | BIGINT    | Block size (bytes)         |
| `blob_gas_used`     | BIGINT    | EIP-4844 blob gas used     |
| `excess_blob_gas`   | BIGINT    | EIP-4844 excess blob gas   |

Schema excludes cryptographic hashes and Merkle roots (non-predictive fields).

## Feature Engineering

Combine with OHLCV price data for cross-domain features:

```python
import clickhouse_connect
import gapless_crypto_data as gcd
import pandas as pd

# Fetch OHLCV data
df_ohlcv = gcd.get_data(
    symbol="ETHUSDT",
    timeframe="1m",
    start_date="2024-01-01",
    end_date="2024-01-02"
)

# Query Ethereum blocks
client = clickhouse_connect.get_client(...)
df_eth = client.query_df("""
    SELECT timestamp, base_fee_per_gas, gas_used, gas_limit, transaction_count
    FROM ethereum_mainnet.blocks FINAL
    WHERE timestamp BETWEEN '2024-01-01' AND '2024-01-02'
""")

# Temporal alignment (forward-fill prevents data leakage)
df_eth['timestamp'] = pd.to_datetime(df_eth['timestamp'])
df_eth.set_index('timestamp', inplace=True)
df_eth_aligned = df_eth.reindex(df_ohlcv.index, method='ffill')

# Join and engineer features
df = df_ohlcv.join(df_eth_aligned)
df['gas_pressure'] = df['base_fee_per_gas'] / df['base_fee_per_gas'].rolling(60).median()
df['block_utilization'] = (df['gas_used'] / df['gas_limit']) * 100
```

## Infrastructure

### Pipeline Components

| Component           | Purpose                      | Technology           |
| ------------------- | ---------------------------- | -------------------- |
| BigQuery Sync       | Hourly batch from public dataset | Cloud Run Job    |
| Real-Time Collector | Block-level streaming        | e2-micro VM          |
| Database            | Storage with deduplication   | ClickHouse Cloud     |
| Monitoring          | Dead Man's Switch            | Healthchecks.io      |

### Deployment Structure

```
deployment/
├── cloud-run/       # BigQuery sync job
├── vm/              # Real-time collector
└── backfill/        # Historical data loading
```

## Operations

```bash
# Verify pipeline health
gcloud run jobs executions list --job eth-md-updater --region us-central1

# View real-time collector logs
gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
  --command='sudo journalctl -u eth-collector -f'

# Verify database state
uv run scripts/clickhouse/verify_blocks.py
```

## Data Sources

| Source   | Purpose           | Method    |
| -------- | ----------------- | --------- |
| BigQuery | Historical blocks | Hourly sync |
| Alchemy  | Real-time blocks  | WebSocket |

## Related Projects

- [gapless-crypto-data](https://github.com/terrylica/gapless-crypto-data) - OHLCV data collection
- [BigQuery Ethereum Dataset](https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=crypto_ethereum)
- [Alchemy](https://www.alchemy.com/) - Real-time WebSocket API
- [ClickHouse Cloud](https://clickhouse.cloud/) - Cloud-hosted ClickHouse

## Documentation

- [Architecture Overview](https://github.com/terrylica/gapless-network-data/blob/main/docs/architecture/OVERVIEW.md)
- [Data Format Specification](https://github.com/terrylica/gapless-network-data/blob/main/docs/architecture/DATA_FORMAT.md)
- [ClickHouse Migration Decision](https://github.com/terrylica/gapless-network-data/blob/main/docs/decisions/0013-motherduck-clickhouse-migration.md)

## License

[MIT License](https://github.com/terrylica/gapless-network-data/blob/main/LICENSE)
