---
version: "1.0.0"
last_updated: "2025-11-12"
supersedes: ["0.1.0"]
status: "operational"
---

# Data Format Specification

**Status**: ✅ Operational (Ethereum schema deployed)

Multi-chain blockchain network metrics data format specification.

## Ethereum Block Data (11 fields)

**Storage**: MotherDuck cloud database `ethereum_mainnet.blocks`
**Granularity**: ~12-second block intervals
**Data Range**: Block #1 (2015-07-30) to present (23.8M blocks)

### Schema

| Field               | Type                     | Description                              | Validation          |
| ------------------- | ------------------------ | ---------------------------------------- | ------------------- |
| `timestamp`         | TIMESTAMP WITH TIME ZONE | Block timestamp                          | ISO 8601 format     |
| `number`            | BIGINT                   | Block number (PRIMARY KEY)               | Strictly increasing |
| `gas_limit`         | BIGINT                   | Block gas limit                          | >= 0                |
| `gas_used`          | BIGINT                   | Total gas used in block                  | 0 to gas_limit      |
| `base_fee_per_gas`  | BIGINT                   | Base fee per gas (wei, EIP-1559)         | >= 0                |
| `transaction_count` | BIGINT                   | Number of transactions in block          | >= 0                |
| `difficulty`        | HUGEINT                  | Mining difficulty                        | >= 0                |
| `total_difficulty`  | HUGEINT                  | Cumulative chain difficulty              | >= 0                |
| `size`              | BIGINT                   | Block size in bytes                      | > 0                 |
| `blob_gas_used`     | BIGINT                   | Blob gas used (EIP-4844, Dencun upgrade) | >= 0                |
| `excess_blob_gas`   | BIGINT                   | Excess blob gas (EIP-4844)               | >= 0                |

**Naming Convention**: `snake_case` (matches BigQuery public dataset)

**PRIMARY KEY**: `number` (enables automatic deduplication via `INSERT OR REPLACE`)

**DDL**:

```sql
CREATE TABLE ethereum_mainnet.blocks (
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    number BIGINT PRIMARY KEY,
    gas_limit BIGINT NOT NULL,
    gas_used BIGINT NOT NULL,
    base_fee_per_gas BIGINT,
    transaction_count BIGINT NOT NULL,
    difficulty HUGEINT NOT NULL,
    total_difficulty HUGEINT NOT NULL,
    size BIGINT NOT NULL,
    blob_gas_used BIGINT,
    excess_blob_gas BIGINT
);
```

### Data Sources

**Historical (2015-2025)**:

- Source: BigQuery public dataset `bigquery-public-data.crypto_ethereum.blocks`
- Method: Cloud Run Job hourly sync
- Fields: All 11 fields

**Real-Time (ongoing)**:

- Source: Alchemy WebSocket API `eth_subscribe` newHeads
- Method: VM collector with 5-minute batch writes
- Fields: All 11 fields

### Field Notes

**EIP-1559 Fields** (London upgrade, 2021-08-05):

- `base_fee_per_gas`: Algorithmic base fee, burned per transaction

**EIP-4844 Fields** (Dencun upgrade, 2024-03-13):

- `blob_gas_used`: Gas consumed by blob-carrying transactions
- `excess_blob_gas`: Blob gas pricing mechanism

**Legacy Fields**:

- `difficulty`: Proof-of-work mining difficulty (0 after Merge, 2022-09-15)
- `total_difficulty`: Cumulative difficulty (frozen after Merge)

### Validation Rules

1. **Monotonic Block Numbers**: `number[i+1] = number[i] + 1`
2. **Gas Constraints**: `0 <= gas_used <= gas_limit`
3. **Timestamp Ordering**: `timestamp[i+1] >= timestamp[i]` (not strictly increasing)
4. **Non-Negative Values**: All integer fields >= 0
5. **Zero Gaps**: Complete sequence from block #1 to latest

---

## Bitcoin Mempool Data (9 fields)

**Status**: 🚧 Planned for Phase 2+

| Field               | Type                     | Description                               |
| ------------------- | ------------------------ | ----------------------------------------- |
| `timestamp`         | TIMESTAMP WITH TIME ZONE | Snapshot timestamp                        |
| `unconfirmed_count` | BIGINT                   | Number of unconfirmed transactions        |
| `vsize_mb`          | DOUBLE                   | Total mempool virtual size (MB)           |
| `total_fee_btc`     | DOUBLE                   | Total fees in mempool (BTC)               |
| `fastest_fee`       | DOUBLE                   | Fee rate for next block (sat/vB)          |
| `half_hour_fee`     | DOUBLE                   | Fee rate for ~30min confirmation (sat/vB) |
| `hour_fee`          | DOUBLE                   | Fee rate for ~1hr confirmation (sat/vB)   |
| `economy_fee`       | DOUBLE                   | Fee rate for low-priority tx (sat/vB)     |
| `minimum_fee`       | DOUBLE                   | Minimum relay fee (sat/vB)                |

**Sanity Check**: `fastest_fee >= half_hour_fee >= hour_fee >= economy_fee >= minimum_fee >= 1`

**Source**: mempool.space API `/api/v1/fees/recommended` and `/api/mempool`

**Granularity**: 5-minute snapshots (M5 recent data, H12 historical archive)

---

## Storage Architecture

### MotherDuck Cloud Database

**Connection**: `md:ethereum_mainnet`
**Provider**: MotherDuck (cloud-hosted DuckDB)
**Tier**: Free (10 GB storage, 10 CU hours/month)

**Advantages**:

- Automatic deduplication via PRIMARY KEY
- SQL query interface
- Column-oriented storage
- Built-in compression
- No local storage required

**Limitations**:

- 10 GB storage limit (sufficient for ~100M blocks)
- 10 CU hours/month (batch writes stay within limit)
- Single database instance

### Alternative Storage (Future)

**Local DuckDB** (optional caching):

- Location: `~/.cache/gapless-network-data/data.duckdb`
- Purpose: Offline analysis
- Status: Not implemented

---

## Data Granularity Comparison

| Chain        | Granularity | Blocks/Hour  | Storage/Hour | Historical Depth      | Status             |
| ------------ | ----------- | ------------ | ------------ | --------------------- | ------------------ |
| **Ethereum** | ~12 seconds | 300 blocks   | ~150 KB      | 2015-07-30+ (Genesis) | ✅ **Operational** |
| **Bitcoin**  | 5 minutes   | 12 snapshots | ~3 KB        | 2016+                 | 🚧 **Planned**     |

**Rationale**: Ethereum provides 12-second granularity for network congestion analysis, while Bitcoin mempool updates are lower frequency (5-minute intervals).

---

## Schema Evolution

### Version 1.0.0 (2025-11-12)

- Ethereum schema deployed to MotherDuck
- 11 fields including EIP-4844 blob gas fields
- PRIMARY KEY on `number` for deduplication
- BigQuery + Alchemy dual-pipeline sources

### Version 0.1.0 (2025-11-04)

- Initial schema design
- Parquet storage planned (superseded by MotherDuck)
- LlamaRPC source planned (superseded by BigQuery + Alchemy)

---

## Related Documentation

- [MotherDuck Dual Pipeline](./_archive/motherduck-dual-pipeline.md) - Complete schema DDL (DEPRECATED - see MADR-0013)
- [BigQuery Integration](./_archive/bigquery-motherduck-integration.md) - Field mapping (DEPRECATED - see MADR-0013)
- [Architecture Overview](./OVERVIEW.md) - System design
