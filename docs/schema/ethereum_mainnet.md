# ethereum_mainnet.blocks

_Generated from: schema/clickhouse/ethereum_mainnet.yaml_

_Generated at: 2025-12-02 20:02:05_

Block-level data for ML feature engineering.
Contains gas metrics, transaction counts, and EIP-4844 blob data.
Used by Alpha Features API for financial time series forecasting.


## Alpha Feature Rankings

| Rank | Column | Importance | Description |
| --- | --- | --- | --- |
| 1 | base_fee_per_gas | critical | EIP-1559 base fee per gas unit (wei) |
| 3 | transaction_count | high | Number of transactions in block |
| 4 | timestamp | high | Block timestamp with millisecond precision |
| 5 | number | high | Block number - used as deduplication key |
| 6 | size | medium | Block size in bytes |
| 7 | blob_gas_used | medium | EIP-4844 blob gas used (null pre-Dencun, Mar 2024) |
| 8 | excess_blob_gas | low | EIP-4844 excess blob gas (null pre-Dencun) |
| 9 | gas_limit | low | Maximum gas allowed in block |
| 10 | gas_used | low | Total gas consumed by transactions |
## Schema

| Column | Type | Nullable | Description |
| --- | --- | --- | --- |
| timestamp | DateTime64(3) | NO | Block timestamp with millisecond precision |
| number | Int64 | NO | Block number - used as deduplication key |
| gas_limit | Int64 | NO | Maximum gas allowed in block |
| gas_used | Int64 | NO | Total gas consumed by transactions |
| base_fee_per_gas | Int64 | NO | EIP-1559 base fee per gas unit (wei) |
| transaction_count | Int64 | NO | Number of transactions in block |
| difficulty | UInt256 | NO | Mining difficulty (0 post-Merge, Sep 2022) |
| total_difficulty | UInt256 | NO | Cumulative difficulty (frozen post-Merge) |
| size | Int64 | NO | Block size in bytes |
| blob_gas_used | Nullable(Int64) | YES | EIP-4844 blob gas used (null pre-Dencun, Mar 2024) |
| excess_blob_gas | Nullable(Int64) | YES | EIP-4844 excess blob gas (null pre-Dencun) |
## Deprecated Columns

### difficulty

- **Deprecated since**: 2022-09-15
- **Reason**: Always 0 after The Merge

### total_difficulty

- **Deprecated since**: 2022-09-15
- **Reason**: Frozen after The Merge
## Column Availability

Some columns are only available after specific protocol upgrades:

- **blob_gas_used**: Block 19,426,587 (2024-03-13)
- **excess_blob_gas**: Block 19,426,587 (2024-03-13)
## ClickHouse Configuration

- **Engine**: `ReplacingMergeTree()`
- **Partition By**: `toYYYYMM(timestamp)`
- **Order By**: `(number)`
- **Settings**:
  - `index_granularity`: 8192
