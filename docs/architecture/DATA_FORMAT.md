---
version: "0.1.0"
last_updated: "2025-11-04"
supersedes: []
status: "pending"
---

# Data Format Specification

**Status**: 🚧 Pending Phase 1 implementation

This document will provide comprehensive multi-chain data format specifications.

## Current Schemas (Quick Reference)

### Ethereum Block Data (PRIMARY - 12-second intervals)

| Field           | Type                | Description                     | Validation          |
| --------------- | ------------------- | ------------------------------- | ------------------- |
| `number`        | int64               | Block number                    | Strictly increasing |
| `timestamp`     | datetime64[ns, UTC] | Block timestamp                 | ISO 8601 format     |
| `baseFeePerGas` | int64               | Base fee per gas (wei)          | >= 0                |
| `gasUsed`       | int64               | Total gas used in block         | 0 to gasLimit       |
| `gasLimit`      | int64               | Block gas limit                 | >= 0                |
| `transactions`  | int64               | Number of transactions in block | >= 0                |

**Index**: DatetimeIndex on `timestamp` column

**File Pattern**: `ethereum_YYYYMMDD_HH.parquet` (300 blocks per hour)

**Compression**: Snappy

**Source**: LlamaRPC `eth_getBlockByNumber` method

---

### Bitcoin Mempool Data (SECONDARY - 5-minute intervals)

| Field               | Type                | Description                               | Validation      |
| ------------------- | ------------------- | ----------------------------------------- | --------------- |
| `timestamp`         | datetime64[ns, UTC] | Snapshot timestamp                        | ISO 8601 format |
| `unconfirmed_count` | int64               | Number of unconfirmed transactions        | >= 0            |
| `vsize_mb`          | float64             | Total mempool virtual size (MB)           | >= 0            |
| `total_fee_btc`     | float64             | Total fees in mempool (BTC)               | >= 0            |
| `fastest_fee`       | float64             | Fee rate for next block (sat/vB)          | 1-1000          |
| `half_hour_fee`     | float64             | Fee rate for ~30min confirmation (sat/vB) | 1-1000          |
| `hour_fee`          | float64             | Fee rate for ~1hr confirmation (sat/vB)   | 1-1000          |
| `economy_fee`       | float64             | Fee rate for low-priority tx (sat/vB)     | 1-1000          |
| `minimum_fee`       | float64             | Minimum relay fee (sat/vB)                | >= 1            |

**Index**: DatetimeIndex on `timestamp` column

**File Pattern**: `bitcoin_YYYYMMDD_HH.parquet` (12 snapshots per hour)

**Compression**: Snappy

**Sanity Check**: `fastest_fee >= half_hour_fee >= hour_fee >= economy_fee >= minimum_fee`

**Source**: mempool.space `/api/v1/fees/recommended` and `/api/mempool` endpoints

---

## Planned Content

### Multi-Chain Schema Design Principles

- DatetimeIndex-first design for temporal alignment
- Chain-specific field selection (prioritize network congestion metrics)
- Parquet column types for optimal compression
- Validation rules per chain

### Storage Optimization

- Snappy compression ratios per chain
- Parquet file granularity (hourly chunks)
- Column ordering for query performance
- Delta encoding opportunities

### Schema Versioning

- Backward compatibility strategy
- Migration paths for schema changes
- Version tracking in YAML frontmatter

### Future Chain Support

- Solana: Transaction per second (TPS), compute unit prices
- Avalanche: C-Chain gas prices, subnet metrics
- Polygon: Gas prices, validator metrics

---

## Current Context

Until this document is completed, refer to:

- [README.md](/Users/terryli/eon/gapless-network-data/README.md) - Data schemas section (lines 89-114)
- [CLAUDE.md](/Users/terryli/eon/gapless-network-data/CLAUDE.md) - Data format section (lines 409-435)
- [LlamaRPC Schema Documentation](/Users/terryli/eon/gapless-network-data/docs/llamarpc/schema/ETHEREUM_BLOCK_SCHEMA.md) - Complete 26-field Ethereum block schema

---

## Data Granularity Comparison

| Chain    | Granularity | Snapshots/Hour | File Size (Hourly) | Historical Depth | Status        |
| -------- | ----------- | -------------- | ------------------ | ---------------- | ------------- |
| Ethereum | ~12 seconds | 300 blocks     | ~50 KB compressed  | 2015+ (Genesis)  | **PRIMARY**   |
| Bitcoin  | 5 minutes   | 12 snapshots   | ~3 KB compressed   | 2016+            | **SECONDARY** |

**Rationale**: Ethereum provides TRUE high-frequency data for network congestion analysis, while Bitcoin mempool updates are lower frequency (M5 recent, H12 historical).

---

**Related Documentation**:

- [Architecture Overview](/Users/terryli/eon/gapless-network-data/docs/architecture/OVERVIEW.md) - System design
- [Metric Mapping](/Users/terryli/eon/gapless-network-data/docs/llamarpc/schema/METRIC_MAPPING.md) - Feature engineering guidance

**This document will be completed during Phase 1 implementation.**
