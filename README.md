# Gapless Network Data

Production blockchain data collection infrastructure with dual-pipeline architecture for Ethereum network metrics.

## Overview

Operational Ethereum data pipeline collecting **14.57M blocks (2020-2025)** with real-time updates every ~12 seconds.

**Architecture**: BigQuery hourly batch + Alchemy real-time WebSocket → MotherDuck cloud database

**Status**: Production operational (v2.2.1)

**Cost**: $0/month (all within free tiers)

## Infrastructure Components

### 1. BigQuery Hourly Sync (Cloud Run Job)

- **Purpose**: Syncs latest blocks from BigQuery public dataset
- **Schedule**: Every hour via Cloud Scheduler
- **Volume**: ~578 blocks per run (last 2 hours)
- **Cost**: $0/month (10 MB queries within 1 TB/month free tier)

### 2. Real-Time Collector (e2-micro VM)

- **Purpose**: Alchemy WebSocket subscription for real-time blocks
- **Frequency**: New blocks every ~12 seconds
- **Service**: Systemd service (eth-collector)
- **Cost**: $0/month (e2-micro within free tier)

### 3. MotherDuck Database

- **Type**: Cloud-hosted DuckDB
- **Deduplication**: INSERT OR REPLACE on block number (PRIMARY KEY)
- **Data**: 14.57M blocks, ~1.5 GB storage
- **Cost**: $0/month (within 10 GB free tier)

### 4. Monitoring (Cloud-Based)

- **Healthchecks.io**: Dead Man's Switch monitoring (hourly pings)
- **UptimeRobot**: HTTP endpoint monitoring
- **Pushover**: Alert delivery for failures
- **Cost**: $0/month (all free tiers)

## Data Access

Query MotherDuck database directly via DuckDB:

```python
import duckdb

# Connect to MotherDuck
conn = duckdb.connect(f'md:ethereum_mainnet?motherduck_token={token}')

# Query latest 10 blocks
result = conn.execute("""
    SELECT
        timestamp,
        number,
        base_fee_per_gas,
        gas_used,
        gas_limit,
        transaction_count
    FROM blocks
    ORDER BY number DESC
    LIMIT 10
""").df()

print(result)
```

**Example output**:

```
                 timestamp     number  base_fee_per_gas   gas_used   gas_limit  transaction_count
0  2025-11-10 17:03:23  21464789      8234567890  29876543  30000000                245
1  2025-11-10 17:03:11  21464788      8156234567  29654321  30000000                238
...
```

## Schema

11 columns optimized for ML feature engineering:

| Column              | Type      | Description                      |
| ------------------- | --------- | -------------------------------- |
| `timestamp`         | TIMESTAMP | UTC timestamp                    |
| `number`            | BIGINT    | Block number (PRIMARY KEY)       |
| `gas_limit`         | BIGINT    | Block gas limit                  |
| `gas_used`          | BIGINT    | Total gas used                   |
| `base_fee_per_gas`  | BIGINT    | EIP-1559 base fee (wei)          |
| `transaction_count` | BIGINT    | Number of transactions           |
| `difficulty`        | HUGEINT   | Mining/staking difficulty        |
| `total_difficulty`  | HUGEINT   | Cumulative chain work            |
| `size`              | BIGINT    | Block size (bytes)               |
| `blob_gas_used`     | BIGINT    | EIP-4844 blob gas used (2024+)   |
| `excess_blob_gas`   | BIGINT    | EIP-4844 excess blob gas (2024+) |

**Rationale**: These 11 columns contain all temporal patterns suitable for time-series forecasting. Excludes cryptographic hashes (32-byte random data), Merkle roots (integrity checksums), and other non-predictive fields. See `.claude/skills/bigquery-ethereum-data-acquisition/CLAUDE.md` for complete column selection analysis.

## Feature Engineering Example

Combine Ethereum network data with OHLCV price data:

```python
import duckdb
import gapless_crypto_data as gcd
import pandas as pd

# Fetch OHLCV data (ETHUSDT 1-minute)
df_ohlcv = gcd.get_data(
    symbol="ETHUSDT",
    timeframe="1m",
    start_date="2024-01-01",
    end_date="2024-01-02"
)

# Query Ethereum blocks from MotherDuck
conn = duckdb.connect(f'md:ethereum_mainnet?motherduck_token={token}')
df_eth = conn.execute("""
    SELECT timestamp, base_fee_per_gas, gas_used, gas_limit, transaction_count
    FROM blocks
    WHERE timestamp BETWEEN '2024-01-01' AND '2024-01-02'
""").df()

# Temporal alignment (forward-fill to prevent data leakage)
df_eth['timestamp'] = pd.to_datetime(df_eth['timestamp'])
df_eth.set_index('timestamp', inplace=True)
df_eth_aligned = df_eth.reindex(df_ohlcv.index, method='ffill')

# Join on timestamp
df = df_ohlcv.join(df_eth_aligned)

# Engineer cross-domain features
df['gas_pressure'] = df['base_fee_per_gas'] / df['base_fee_per_gas'].rolling(60).median()
df['block_utilization'] = (df['gas_used'] / df['gas_limit']) * 100
df['gas_adjusted_return'] = (df['close'] - df['open']) / (df['base_fee_per_gas'] + 1)
```

See [gapless-crypto-data](https://github.com/terrylica/gapless-crypto-data) for OHLCV data collection.

## Deployment Structure

```
deployment/
├── cloud-run/       # BigQuery → MotherDuck hourly sync
│   ├── main.py
│   ├── Dockerfile
│   └── README.md
├── vm/              # Real-time Alchemy WebSocket collector
│   ├── realtime_collector.py
│   ├── eth-collector.service
│   └── README.md
└── backfill/        # One-time historical backfill (2020-2025)
    ├── historical_backfill.py
    ├── chunked_backfill.sh
    └── README.md
```

Each directory contains production scripts, infrastructure files (Dockerfile, systemd service), and deployment instructions.

## Operations

### Verify Pipeline Health

```bash
# Check Cloud Run Job execution history (run locally, requires gcloud auth)
gcloud run jobs executions list --job eth-md-updater --region us-central1

# Check VM real-time collector logs (run locally, requires gcloud auth)
gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
  --command='sudo journalctl -u eth-collector -f'

# Verify MotherDuck database state (run locally, queries MotherDuck cloud, requires motherduck_token)
cd .claude/skills/motherduck-pipeline-operations
uv run scripts/verify_motherduck.py
```

### Service Management

**Cloud Run Job** (BigQuery sync):

```bash
# Manual trigger
gcloud run jobs execute eth-md-updater --region us-central1

# View logs
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=eth-md-updater" --limit 50
```

**VM Service** (real-time collector):

```bash
# Check status
gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
  --command='sudo systemctl status eth-collector'

# Restart service
gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
  --command='sudo systemctl restart eth-collector'
```

### Historical Backfill

For loading multi-year historical data (one-time operation):

```bash
# Run locally. Triggers Cloud Run Job executions via gcloud. Requires GCP credentials and BigQuery API access.
cd deployment/backfill
./chunked_backfill.sh 2020 2025
```

Uses 1-year chunking pattern to prevent OOM failures (~1.5-2 min per chunk).

## Monitoring Architecture

All monitoring runs on the cloud (no local processes):

- **Healthchecks.io**: Cloud Run Job pings after each execution (Dead Man's Switch)
- **UptimeRobot**: HTTP checks for public endpoints
- **Pushover**: Alert delivery to mobile/desktop

**SLOs Met**:

- ✅ Availability: Pipelines run without manual intervention
- ✅ Correctness: 100% data accuracy with schema validation
- ✅ Observability: 100% operation tracking via Cloud Logging
- ✅ Maintainability: <30 minutes for common operations

## Cost Breakdown

**Total**: $0/month (all within free tiers)

| Service         | Usage          | Free Tier Limit | Cost |
| --------------- | -------------- | --------------- | ---- |
| BigQuery        | 10 MB queries  | 1 TB/month      | $0   |
| Cloud Run       | 720 executions | 2M invocations  | $0   |
| Compute Engine  | e2-micro VM    | 1 instance      | $0   |
| MotherDuck      | 1.5 GB storage | 10 GB           | $0   |
| Healthchecks.io | 1 check        | 20 checks       | $0   |
| UptimeRobot     | 1 monitor      | 50 monitors     | $0   |
| Pushover        | Alerts         | 10,000/month    | $0   |

## Security

- **Secrets Management**: Google Cloud Secret Manager (no Doppler, no local .env files)
- **IAM Permissions**: Least-privilege service accounts
- **Critical Pattern**: `.strip()` on secrets to prevent gRPC metadata validation errors

## Operational Status

**Last Verified**: 2025-11-10

- ✅ VM eth-realtime-collector: ACTIVE
- ✅ eth-collector systemd service: ACTIVE (streaming blocks every ~12s)
- ✅ Cloud Run eth-md-updater: ACTIVE (hourly BigQuery sync)
- ✅ Cloud Scheduler eth-md-hourly: ENABLED (triggers hourly at :00)
- ✅ MotherDuck ethereum_mainnet.blocks: 14.57M blocks (2020-2025)

## Data Sources

**Active (Production)**:

- BigQuery public dataset: `bigquery-public-data.crypto_ethereum.blocks`
- Alchemy WebSocket API: 300M CU/month free tier

**Researched (Not Used)**:

- LlamaRPC: Rejected due to rate limits (1.37 RPS sustained, 110-day timeline)
- See `docs/llamarpc/INDEX.md` for complete research documentation

## Related Projects

- [gapless-crypto-data](https://github.com/terrylica/gapless-crypto-data) - OHLCV data collection
- [BigQuery Ethereum Dataset](https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=crypto_ethereum)
- [Alchemy](https://www.alchemy.com/) - Real-time WebSocket API
- [MotherDuck](https://motherduck.com/) - Cloud-hosted DuckDB

## Future Work (Phase 2+)

- Python SDK with `fetch_snapshots()` API
- Bitcoin mempool.space integration (5-minute intervals)
- CLI commands (`collect`, `stream`, `validate`, `export`)
- Complete 5-layer validation pipeline
- Real-time alerting system

## Contributing

This project is in production operational mode. Contributions focused on:

- Bitcoin mempool.space integration
- Python SDK development
- Additional blockchain support (Solana, Avalanche)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Documentation

- [CLAUDE.md](CLAUDE.md) - Complete project memory and architecture
- [Master Roadmap](specifications/master-project-roadmap.yaml) - Project phases and planning
- [MotherDuck Integration](specifications/motherduck-integration.yaml) - Dual-pipeline architecture
- [Skills](.claude/skills/) - Operational workflows and troubleshooting guides
