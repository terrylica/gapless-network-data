# BigQuery Cost Analysis

This document provides detailed cost comparison for Ethereum data acquisition approaches.

---

## Cost Comparison Table

| Selection     | Columns | Cost (GB) | % Free Tier | Monthly Runs | Status       |
|---------------|---------|-----------|-------------|--------------|--------------|
| Optimized ML  | 11      | 0.97      | 0.1%        | 1,061        | ✅ TESTED    |
| All columns   | 23      | 34.4      | 3.4%        | 29           | ⚠️ ESTIMATED |
| Minimal (6)   | 6       | 0.45      | 0.045%      | 2,275        | ⚠️ ESTIMATED |

**Recommendation**: Use 11-column selection (0.97 GB, 0.1% of free tier)

---

## Column Selection Rationale

### Optimized ML Selection (11 columns, 0.97 GB)

**Included fields**:
1. `timestamp` - Time-series index
2. `number` - Block number (sequential identifier)
3. `gas_limit` - Network capacity
4. `gas_used` - Actual usage
5. `base_fee_per_gas` - EIP-1559 base fee
6. `transaction_count` - Activity level
7. `difficulty` - Mining difficulty
8. `total_difficulty` - Cumulative difficulty
9. `size` - Block size in bytes
10. `blob_gas_used` - EIP-4844 blob usage
11. `excess_blob_gas` - EIP-4844 excess

**Why 11 columns**:
- Complete time-series context (timestamp, sequential ordering)
- Network metrics (gas, transaction count, difficulty)
- Resource utilization (size, blob gas)
- No redundant hash fields

**Cost efficiency**: 97% reduction vs all columns (0.97 GB vs 34.4 GB)

### Discarded Columns (12 columns, 33.4 GB)

**Hash fields** (6 columns, ~20 GB):
- `hash` - Block hash (32 bytes random)
- `parent_hash` - Previous block hash
- `nonce` - Mining nonce
- `miner` - Miner address hash
- `sha3_uncles` - Uncle blocks hash
- `mix_hash` - PoW mix hash

**Why discarded**: Zero ML value, high storage cost, random strings provide no forecasting signal

**Merkle roots** (4 columns, ~10 GB):
- `transactions_root` - Transaction trie root
- `state_root` - State trie root
- `receipts_root` - Receipts trie root
- `withdrawals_root` - Withdrawals trie root

**Why discarded**: Deterministic checksums, no predictive value, redundant with transaction_count

**Other** (2 columns, ~3 GB):
- `extra_data` - Arbitrary miner data (high cardinality)
- `logs_bloom` - 256-byte bloom filter (sparse, high storage cost)

**Why discarded**: Categorical noise, minimal signal for forecasting

---

## Free Tier Utilization

**Google BigQuery Free Tier**:
- Query processing: 1 TB (1,024 GB) per month
- Storage: 10 GB (not used with streaming approach)

**Optimized selection usage**:
- Query cost: 0.97 GB
- % of free tier: 0.1%
- Runs per month: 1,024 GB ÷ 0.97 GB = 1,061 runs
- **Conclusion**: Can re-run query 1,000+ times within free tier

**All columns usage**:
- Query cost: 34.4 GB
- % of free tier: 3.4%
- Runs per month: 1,024 GB ÷ 34.4 GB = 29 runs
- **Conclusion**: Limited re-runs, 97% wasted on hash fields

---

## BigQuery vs RPC Polling Comparison

### BigQuery Approach

**Timeline**: < 1 hour
- Query execution: < 5 minutes
- Streaming download: 30-60 minutes (network-bound)
- DuckDB import: < 1 minute

**Cost**: $0 (within free tier)
- Query: 0.97 GB (0.1% of 1 TB free tier)
- Storage: 0 GB (streaming avoids BigQuery storage)

**Effort**: Minimal
- One-time setup: gcloud auth (5 minutes)
- Execution: 2 commands (cost validation + download)

### RPC Polling Approach

**Timeline**: 26 days (Alchemy 5.79 RPS)
- 12.44M blocks ÷ 5.79 RPS ÷ 86,400 sec/day = 26 days
- Requires continuous operation (no interruptions)

**Cost**: $0 (free tier) but opportunity cost
- Time investment: 26 days of machine runtime
- Risk: Network errors, rate limit changes, interruptions

**Effort**: High
- POC validation required
- Error handling and retry logic
- Checkpoint/resume capability
- Monitoring and alerting

**Alternative RPC**: LlamaRPC at 1.37 RPS
- Timeline: 110 days (4x slower than Alchemy)
- Same operational complexity

---

## Key Findings

### 1. BigQuery is 624x Faster

**Calculation**:
- BigQuery: < 1 hour
- RPC (Alchemy): 26 days = 624 hours
- **Speedup**: 624x

**Why**:
- BigQuery: Massively parallel query engine, optimized for analytics
- RPC: Sequential polling, rate-limited, network-bound

### 2. Hash Fields are 97% Waste

**Empirical evidence**:
- All columns: 34.4 GB
- Hash fields: 33.4 GB
- **Waste**: 33.4 GB ÷ 34.4 GB = 97%

**ML value**:
- Hashes: Random 32-byte strings, zero correlation with network metrics
- Merkle roots: Deterministic checksums, redundant with counts
- **Forecasting value**: None

### 3. Free Tier Sufficient

**Query budget**:
- Monthly limit: 1 TB
- Query cost: 0.97 GB
- **Utilization**: 0.1% (999 GB unused)

**Re-run capability**:
- Full dataset download: 1,061 times per month
- Incremental updates: Unlimited (< 0.01 GB per day)

### 4. Storage Avoidance Confirmed

**Streaming approach** (validated 2025-11-07):
- Query → Stream to Parquet → DuckDB
- BigQuery storage: 0 GB ✅
- Local storage: 62 bytes/row (0.73 GB for 12.44M blocks)

**Alternative (not recommended)**:
- Query → Save to BigQuery table → Export
- BigQuery storage: 10+ GB ❌ (exceeds free tier limit)

### 5. Alternative Exists (1RPC)

**Fallback option** (if BigQuery unavailable):
- Provider: 1RPC (public endpoint)
- Rate: 77 RPS (empirically validated by community)
- Timeline: 1.9 days (33x faster than Alchemy)
- Cost: $0 (public endpoint)

**When to use**:
- BigQuery authentication issues
- Need for real-time streaming (not batch)
- Compliance requires RPC-only approach

---

## Cost Optimization Strategies

### 1. Column Pruning

**Impact**: 97% cost reduction (34.4 GB → 0.97 GB)

**Method**: Remove hash fields and merkle roots
```sql
-- Before (34.4 GB)
SELECT * FROM `bigquery-public-data.crypto_ethereum.blocks`

-- After (0.97 GB)
SELECT timestamp, number, gas_limit, gas_used, base_fee_per_gas,
       transaction_count, difficulty, total_difficulty, size,
       blob_gas_used, excess_blob_gas
FROM `bigquery-public-data.crypto_ethereum.blocks`
```

### 2. Date Range Filtering

**Impact**: Linear cost scaling with date range

**Example**:
- 5 years (2020-2025): 0.97 GB
- 1 year (2024-2025): ~0.19 GB (20% of cost)
- 1 month (recent): ~0.016 GB (1.6% of cost)

**Use case**: Incremental updates (download only new blocks)

### 3. Streaming Download

**Impact**: Avoid 10 GB BigQuery storage limit

**Method**: Use `download_bigquery_to_parquet.py` instead of saving to BigQuery table

**Benefit**: Unlimited dataset size (storage is local, not BigQuery)

### 4. Partition Queries

**Impact**: Reduce individual query cost for large ranges

**Method**: Split into chunks
```bash
# Option A: Sequential chunks
for year in 2020 2021 2022 2023 2024; do
  uv run scripts/download_bigquery_to_parquet.py \
    ${year}0000 ${year}9999 blocks_${year}.parquet
done

# Option B: Parallel chunks (faster)
parallel uv run scripts/download_bigquery_to_parquet.py \
  {}0000 {}9999 blocks_{}.parquet ::: 2020 2021 2022 2023 2024
```

---

## ROI Analysis

### BigQuery Approach

**Investment**:
- Setup time: 10 minutes (gcloud auth, dependency install)
- Execution time: < 1 hour
- **Total**: 1.2 hours

**Output**:
- 12.44M blocks of Ethereum data
- 11 columns optimized for ML
- DuckDB-ready format

**Cost**: $0 (free tier)

**ROI**: Immediate data availability for feature engineering

### RPC Polling Approach

**Investment**:
- POC validation: 8 hours (rate limit testing, pipeline validation)
- Implementation: 16 hours (error handling, checkpoint/resume, monitoring)
- Runtime: 26 days continuous operation
- **Total**: 24 hours + 26 days machine time

**Output**:
- Same 12.44M blocks
- Same data quality

**Cost**: $0 (free tier) + opportunity cost of 26-day delay

**ROI**: Delayed by 26 days, higher operational complexity

**Conclusion**: BigQuery provides 624x faster time-to-insight with lower operational risk

---

## Related Documentation

- **Workflow steps**: `workflow-steps.md` - Complete 5-step download guide
- **Setup guide**: `setup-guide.md` - Authentication and dependencies
- **Column evaluation**: `ethereum_columns_ml_evaluation.md` - Detailed ML value analysis
- **Cost estimate**: `bigquery_cost_estimate.md` - Free tier limits and methodology
