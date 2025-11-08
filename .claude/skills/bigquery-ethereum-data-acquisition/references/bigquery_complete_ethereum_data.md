# Complete Ethereum Data Available in BigQuery

**Date**: 2025-11-06
**Dataset**: `bigquery-public-data:crypto_ethereum`
**Your Block Range**: 11,560,000 to 24,000,000 (12.44M blocks, ~2020-2024)

---

## BLOCKS Table - Complete Schema (23 Columns)

### What We Were Getting (6 columns):
```sql
number, timestamp, base_fee_per_gas, gas_used, gas_limit, transaction_count
Cost: 1.04 GB (0.1% of free tier)
```

### ALL Available Columns (23 total):

| Column | Type | Description | Useful? |
|--------|------|-------------|---------|
| **timestamp** | TIMESTAMP | When block was mined | ✅ CRITICAL |
| **number** | INTEGER | Block number | ✅ CRITICAL |
| **hash** | STRING | Block hash | ✅ YES (for verification) |
| parent_hash | STRING | Previous block hash | ⚠️ Maybe (for chain analysis) |
| nonce | STRING | Proof-of-work nonce | ❌ Low value |
| sha3_uncles | STRING | Uncles hash | ❌ Low value |
| logs_bloom | STRING | Event logs bloom filter | ❌ Low value (huge field) |
| transactions_root | STRING | Merkle root | ❌ Low value |
| state_root | STRING | State trie root | ❌ Low value |
| receipts_root | STRING | Receipts trie root | ❌ Low value |
| **miner** | STRING | Block reward recipient | ✅ YES (mining analysis) |
| **difficulty** | NUMERIC | Mining difficulty | ✅ YES (network health) |
| **total_difficulty** | NUMERIC | Cumulative difficulty | ✅ YES (chain analysis) |
| **size** | INTEGER | Block size in bytes | ✅ YES (capacity analysis) |
| extra_data | STRING | Arbitrary miner data | ⚠️ Maybe (sometimes interesting) |
| **gas_limit** | INTEGER | Max gas per block | ✅ CRITICAL |
| **gas_used** | INTEGER | Actual gas used | ✅ CRITICAL |
| **transaction_count** | INTEGER | Tx count in block | ✅ CRITICAL |
| **base_fee_per_gas** | INTEGER | EIP-1559 base fee | ✅ CRITICAL |
| withdrawals_root | STRING | Validator withdrawals root | ⚠️ Maybe (post-Merge) |
| **withdrawals** | RECORD | Validator withdrawal details | ✅ YES (post-Merge analysis) |
| blob_gas_used | INTEGER | EIP-4844 blob gas | ✅ YES (post-Dencun) |
| excess_blob_gas | INTEGER | Blob gas excess | ✅ YES (post-Dencun) |

### Cost Comparison:

| Selection | Columns | Size | % of Free Tier | Fits? |
|-----------|---------|------|----------------|-------|
| **Minimal (current)** | 6 | 1.04 GB | 0.1% | ✅ YES |
| **Recommended** | 15 | ~18 GB | 1.8% | ✅ YES |
| **ALL columns** | 23 | 34.4 GB | 3.4% | ✅ YES |

**Recommendation**: Get ALL 23 columns! Only uses 3.4% of free tier.

---

## OTHER TABLES Available

BigQuery has **11 tables** with Ethereum data:

### 1. **blocks** (What we've been discussing)
- **Rows**: 12.44M in your range
- **Cost (all columns)**: 34.4 GB
- **Contains**: Block-level network metrics

### 2. **transactions** ⚠️ HUGE
```
Schema: 25 columns including:
- hash, from_address, to_address, value
- gas, gas_price, max_fee_per_gas, max_priority_fee_per_gas
- receipt_status, receipt_gas_used
- input (contract data)
- EIP-1559 fields, EIP-4844 blob fields

Estimated rows: ~1.5 BILLION transactions in your block range
Cost (COUNT only): 24.6 GB
Cost (all columns, all rows): ~800-1000 GB ❌ EXCEEDS FREE TIER
```

**Analysis**:
- Transaction data is MASSIVE (billions of rows)
- Would cost $0-3,000+ depending on query
- Probably NOT worth it for general use
- Consider sampling or specific queries only

### 3. **logs** ⚠️ HUGE
```
Event logs emitted by smart contracts
Estimated: Several billion rows
Cost: Similar to transactions (800+ GB)
```

### 4. **traces** ⚠️ HUGE
```
Internal transactions (contract-to-contract calls)
Estimated: Billions of rows
Cost: 1000+ GB (exceeds free tier)
```

### 5. **contracts**
```
Smart contract deployments
Estimated: ~50M contracts
Cost: ~50-100 GB ✅ Might fit in free tier
```

### 6. **token_transfers**
```
ERC20/ERC721 token transfers
Estimated: Billions of rows
Cost: 500+ GB ❌ Exceeds free tier
```

### 7. **tokens**
```
Token metadata (name, symbol, decimals)
Estimated: ~1M tokens
Cost: ~1-5 GB ✅ Fits in free tier
```

### 8. **balances** ⚠️ SPECIALIZED
```
Account balances (snapshot-based)
May not cover your block range
Check availability before querying
```

### 9. **amended_tokens** (VIEW)
```
View combining tokens + additional metadata
Small, free to query
```

### 10. **sessions** ⚠️ UNCLEAR
```
User session data (usage unclear)
Check schema before querying
```

### 11. **load_metadata**
```
ETL metadata (when data was loaded)
Small table, negligible cost
```

---

## Recommended Data Collection Strategy

### Phase 1: Blocks - Get EVERYTHING ✅

**Query**: All 23 columns, 12.44M blocks

```sql
SELECT *  -- All 23 columns
FROM `bigquery-public-data.crypto_ethereum.blocks`
WHERE number BETWEEN 11560000 AND 24000000
ORDER BY number
```

**Cost**: 34.4 GB (3.4% of free tier)
**Timeline**: <1 hour
**Why**: Maximum bang for buck, all block-level data

### Phase 2: Tokens Metadata ✅ (Optional)

**Query**: All token info

```sql
SELECT *
FROM `bigquery-public-data.crypto_ethereum.tokens`
```

**Cost**: ~1-5 GB (0.1-0.5% of free tier)
**Why**: Useful for identifying popular tokens, exchange tokens, etc.

### Phase 3: Sample Transactions ✅ (Optional)

**Instead of ALL transactions**, query strategically:

```sql
-- Get transaction summaries per block (aggregate, not individual txs)
SELECT
  block_number,
  block_timestamp,
  COUNT(*) as tx_count,
  SUM(value) as total_value_transferred,
  AVG(gas_price) as avg_gas_price,
  AVG(receipt_gas_used) as avg_gas_used,
  SUM(CASE WHEN receipt_status = 1 THEN 1 ELSE 0 END) as successful_txs,
  SUM(CASE WHEN receipt_status = 0 THEN 1 ELSE 0 END) as failed_txs
FROM `bigquery-public-data.crypto_ethereum.transactions`
WHERE block_number BETWEEN 11560000 AND 24000000
GROUP BY block_number, block_timestamp
ORDER BY block_number
```

**Cost**: ~50-100 GB (5-10% of free tier)
**Why**: Aggregated transaction metrics without raw transaction data

### Phase 4: Skip These (Too Expensive)

❌ **transactions** (all rows): ~1000 GB
❌ **logs** (all rows): ~800 GB
❌ **traces** (all rows): ~1000 GB
❌ **token_transfers** (all rows): ~500 GB

---

## Optimized Query: Maximum Value Within Free Tier

This gets you the most useful data while staying well within 1 TB:

```sql
-- 1. All blocks data (34.4 GB)
SELECT *
FROM `bigquery-public-data.crypto_ethereum.blocks`
WHERE number BETWEEN 11560000 AND 24000000;

-- 2. All tokens metadata (1-5 GB)
SELECT *
FROM `bigquery-public-data.crypto_ethereum.tokens`;

-- 3. Aggregated transaction metrics per block (50-100 GB)
SELECT
  block_number,
  block_timestamp,
  COUNT(*) as tx_count,
  SUM(value) as total_value_wei,
  AVG(gas_price) as avg_gas_price,
  APPROX_QUANTILES(gas_price, 100)[OFFSET(50)] as median_gas_price,
  AVG(receipt_gas_used) as avg_gas_used,
  SUM(CASE WHEN receipt_status = 1 THEN 1 ELSE 0 END) as successful_txs,
  SUM(CASE WHEN receipt_status = 0 THEN 1 ELSE 0 END) as failed_txs,
  COUNT(DISTINCT from_address) as unique_senders,
  COUNT(DISTINCT to_address) as unique_receivers,
  SUM(CASE WHEN to_address IS NULL THEN 1 ELSE 0 END) as contract_creations
FROM `bigquery-public-data.crypto_ethereum.transactions`
WHERE block_number BETWEEN 11560000 AND 24000000
GROUP BY block_number, block_timestamp;

-- 4. Contract deployments summary (50-100 GB)
SELECT
  block_number,
  block_timestamp,
  address as contract_address,
  bytecode,
  function_sighashes,
  is_erc20,
  is_erc721
FROM `bigquery-public-data.crypto_ethereum.contracts`
WHERE block_number BETWEEN 11560000 AND 24000000;

-- Total: ~135-240 GB (13-24% of free tier) ✅
```

---

## Cost Breakdown

| Dataset | Size | % of Free Tier | Value |
|---------|------|----------------|-------|
| **Blocks (ALL 23 cols)** | 34.4 GB | 3.4% | ⭐⭐⭐⭐⭐ Maximum |
| **Tokens metadata** | 5 GB | 0.5% | ⭐⭐⭐⭐ High |
| **Tx aggregates** | 100 GB | 10% | ⭐⭐⭐⭐ High |
| **Contracts** | 100 GB | 10% | ⭐⭐⭐ Medium |
| **Total** | **~240 GB** | **24%** | **✅ Well within limit** |
| **Remaining** | 760 GB | 76% | For future queries |

---

## Recommended Columns for Blocks (15 Columns)

If you want to balance comprehensiveness with efficiency, select these 15 critical columns:

```sql
SELECT
  -- Identity
  number, timestamp, hash,

  -- Network Metrics
  miner, difficulty, total_difficulty, size,

  -- Gas Economics (CRITICAL for your use case)
  gas_limit, gas_used, base_fee_per_gas,

  -- Activity
  transaction_count,

  -- Post-Merge (if analyzing recent blocks)
  withdrawals,

  -- Post-Dencun (EIP-4844, if analyzing 2024+)
  blob_gas_used, excess_blob_gas

FROM `bigquery-public-data.crypto_ethereum.blocks`
WHERE number BETWEEN 11560000 AND 24000000
ORDER BY number
```

**Cost**: ~18 GB (1.8% of free tier)
**Skips**: Merkle roots, bloom filters, nonce, parent_hash (low-value fields)

---

## Final Recommendation

### Option A: Maximum Data (Recommended)
```
1. Blocks: ALL 23 columns (34.4 GB)
2. Tokens: ALL columns (5 GB)
3. Tx Aggregates: Per-block summary (100 GB)
4. Contracts: Deployment data (100 GB)

Total: ~240 GB (24% of free tier)
Timeline: 1-2 hours
Value: Complete historical Ethereum dataset
```

### Option B: Just Blocks (Conservative)
```
1. Blocks: ALL 23 columns (34.4 GB)

Total: 34.4 GB (3.4% of free tier)
Timeline: <1 hour
Value: All block-level data, room for future queries
```

### Option C: Current Plan (Minimal)
```
1. Blocks: 6 columns (1.04 GB)

Total: 1.04 GB (0.1% of free tier)
Timeline: <30 min
Value: Basic network metrics only
```

**My Recommendation**: **Option A** - Since you have 1 TB free, use 240 GB (24%) to get maximum historical data including block details, transaction aggregates, and contract deployments. You'll still have 76% quota remaining for future queries or re-runs.

---

## Next Steps

1. **Test cost of recommended query** (dry-run, free):
```bash
bq query --dry_run --use_legacy_sql=false \
  'SELECT * FROM `bigquery-public-data.crypto_ethereum.blocks`
   WHERE number BETWEEN 11560000 AND 24000000'
```

2. **Run actual download** (if cost acceptable):
```bash
# Export to Parquet (recommended for DuckDB)
bq query --use_legacy_sql=false \
  --destination_table=your_project:your_dataset.ethereum_blocks \
  'SELECT * FROM `bigquery-public-data.crypto_ethereum.blocks`
   WHERE number BETWEEN 11560000 AND 24000000'

bq extract --destination_format=PARQUET \
  your_project:your_dataset.ethereum_blocks \
  gs://your-bucket/ethereum_blocks_*.parquet
```

3. **Download transaction aggregates**:
```bash
bq query --destination_table=your_project:your_dataset.tx_summary \
  'SELECT block_number, COUNT(*) as tx_count, ...
   FROM `bigquery-public-data.crypto_ethereum.transactions`
   WHERE block_number BETWEEN 11560000 AND 24000000
   GROUP BY block_number'
```

Would you like me to run the optimized queries to get ALL available data while staying within free tier?
