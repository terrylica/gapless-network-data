---
version: "1.0.0"
last_updated: "2025-11-12"
supersedes: ["0.1.0"]
status: "operational"
---

# Architecture Overview

**Status**: ✅ Operational (deployed 2025-11-09, 23.8M blocks)

Dual-pipeline blockchain network metrics collection system with zero-gap guarantee.

## Current Implementation

### Core Components

**Data Sources**:

- BigQuery public dataset (`bigquery-public-data.crypto_ethereum.blocks`) - Historical data (2015-2025)
- Alchemy WebSocket API - Real-time stream (~12s block intervals)

**Storage**:

- ClickHouse Cloud database (`ethereum_mainnet.blocks` table)
- Automatic deduplication via `ReplacingMergeTree` on block number

**Compute Infrastructure**:

- Cloud Run Job `eth-md-updater` - Hourly BigQuery sync (~578 blocks/run)
- Cloud Run Job `eth-md-data-quality-checker` - Data freshness monitoring (every 5 min)
- Cloud Run Job `ethereum-historical-backfill` - Historical data loading (on-demand)
- Cloud Function Gen2 `clickhouse-gap-detector` - Gap detection (every 3 hours)
- Compute Engine VM `eth-realtime-collector` - WebSocket streaming (24/7)

**Monitoring**:

- Healthchecks.io - Dead Man's Switch
- Pushover - Alert notifications (priority=2 for failures)
- Cloud Logging - Operation tracking

### System Architecture Diagram

```
DATA SOURCES
├── BigQuery Public Dataset (crypto_ethereum.blocks)
│   └── Historical: 2015-2025, hourly batch (~578 blocks/run)
│
└── Alchemy WebSocket API (wss://eth-mainnet.ws...)
    └── Real-time: ~12s blocks, continuous stream (24/7)

COMPUTE LAYER
├── Cloud Run Job: eth-md-updater
│   ├── PyArrow streaming from BigQuery
│   ├── Last 2 hours lookback
│   └── INSERT INTO ClickHouse
│
└── Compute Engine VM: eth-realtime-collector
    ├── Batch writes (25 blocks buffer)
    ├── Flush every 5 minutes
    └── INSERT INTO ClickHouse

STORAGE
└── ClickHouse Cloud (AWS us-west-2)
    ├── Table: ethereum_mainnet.blocks
    ├── Engine: ReplacingMergeTree(number)
    └── Automatic deduplication on block number

MONITORING
├── Cloud Function Gen2: clickhouse-gap-detector
│   ├── Query every 3 hours
│   └── Gap detection: expected = max - min + 1
│
├── Healthchecks.io
│   └── Dead Man's Switch (expects ping)
│
└── Pushover
    └── Alert notifications (priority=2 on failure)
```

**Runtime Control Flow**:

```
BigQuery ──hourly──▶ Cloud Run Job ──INSERT──┐
                                             │
                                             ▼
Alchemy WS ──stream──▶ VM Collector ──────▶ ClickHouse Cloud
                                             │
                                             ▼
Cloud Scheduler ──3h──▶ Gap Detector ──────▶ Pushover Alert
```

### Data Flow Summary

| Path       | Source            | Processing     | Destination      | Frequency     |
| ---------- | ----------------- | -------------- | ---------------- | ------------- |
| Historical | BigQuery          | Cloud Run Job  | ClickHouse Cloud | Hourly        |
| Real-Time  | Alchemy WebSocket | VM Collector   | ClickHouse Cloud | Every ~12s    |
| Monitoring | ClickHouse Query  | Cloud Function | Pushover Alert   | Every 3 hours |

### Operational Metrics

**Data Loaded**: 23.8M Ethereum blocks
**Block Range**: #1 (2015-07-30) to #23,780,073 (2025-11-12)
**Time Span**: Genesis to present (9.4 years)
**Storage**: ClickHouse Cloud database (~1.5 GB)
**Cost**: $0/month (all within free tiers)

### Service Level Objectives (SLOs)

**Availability**: Data pipelines execute without manual intervention

- Measurement: Percentage of successful scheduled executions
- Current: 100% (hourly sync + 5-min quality checks)

**Correctness**: 100% data accuracy with no silent errors

- Measurement: Schema validation + deduplication + gap detection
- Current: 100% (23.8M blocks with zero gaps)

**Observability**: 100% operation tracking with queryable logs

- Measurement: Cloud Logging coverage + alert delivery
- Current: 100% (all operations logged, Pushover verified)

**Maintainability**: <30 minutes for common operations

- Measurement: Time to deploy fixes or investigate issues
- Current: Met (infrastructure fixes deployed in <15 min)

**Note**: Performance and security are explicitly excluded per project convention.

## Key Architectural Decisions

### 1. ClickHouse Cloud Database for Dual-Pipeline Ingestion

**Decision Date**: 2025-11-25 (migrated from MotherDuck)
**Rationale**: ClickHouse Cloud provides better analytics performance and simpler deduplication
**Implementation**: `ReplacingMergeTree` on `number` with `FINAL` queries
**Trade-offs**:

- Advantage: Better analytics performance, simpler deduplication
- Limitation: Requires `FINAL` keyword for accurate results

### 2. Batch Writes from VM Collector

**Decision Date**: 2025-11-11
**Rationale**: Batch writes improve throughput and reduce connection overhead
**Implementation**: Buffer 25 blocks in memory, flush every 5 minutes
**Trade-offs**:

- Advantage: Reduces write frequency, improves efficiency
- Limitation: Max 5-minute data lag

### 3. BigQuery for Historical Data

**Decision Date**: 2025-11-10
**Rationale**: RPC provider rate limits made 5-year backfill impractical (110-day timeline)
**Implementation**: BigQuery public dataset provides free access to complete history
**Trade-offs**:

- Advantage: 624x faster than RPC polling (<1 hour vs 26 days)
- Limitation: Requires GCP account

### 4. Deterministic Gap Detection via Block Numbers

**Decision Date**: 2025-11-11
**Rationale**: Timestamp gaps are normal Ethereum behavior (missed validator proposals)
**Implementation**: `expected_blocks = max_block - min_block + 1`, compare to `COUNT(*)`
**Trade-offs**:

- Advantage: Zero false positives from network timing variations
- Limitation: Does not detect data corruption within blocks

### 5. Separate Packages for OHLCV vs Network Data

**Decision Date**: 2025-11-04
**Rationale**: Incompatible data models (11-column OHLCV vs 11-column blockchain)
**Implementation**: gapless-crypto-data (OHLCV) + gapless-network-data (blockchain)
**Integration**: Temporal alignment via `DatetimeIndex` + forward-fill

### 6. Ethereum PRIMARY, Bitcoin SECONDARY

**Decision Date**: 2025-11-04
**Rationale**: Ethereum provides 12-second granularity, Bitcoin only 5-minute
**Implementation**: Ethereum fully operational, Bitcoin deferred to Phase 2+

## Current Limitations

1. **Single-chain support**: Ethereum only (Bitcoin planned for future)
2. **No Python SDK**: Package structure exists, API not yet published
3. **Data lag**: Max 5 minutes due to batch write mode
4. **Free tier dependency**: ClickHouse Cloud 10 GB storage limit
5. **Single region**: All GCP resources in us-east1/us-central1

## Related Documentation

- [ClickHouse Migration](/docs/architecture/decisions/2025-11-25-motherduck-clickhouse-migration.md) - Production database decision
- [Data Format Specification](./DATA_FORMAT.md) - Ethereum block schema
- [Real-Time Collector](../deployment/realtime-collector.md) - VM deployment
- [CLAUDE.md](../../CLAUDE.md) - Complete project context
