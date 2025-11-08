# BigQuery Ethereum Data: Cost Comparison (Empirically Tested)

**Date**: 2025-11-06
**Block Range**: 11,560,000 to 24,000,000 (12.44M blocks)
**Free Tier**: 1 TB (1,000 GB) per month

---

## Empirical Test Results

| Query Type | Columns | Size (GB) | % Free Tier | Savings | ML Value |
|------------|---------|-----------|-------------|---------|----------|
| **Original plan** | 6 basic | 1.04 GB | 0.10% | Baseline | ⭐⭐⭐ |
| **Minimal ML** | 9 core | **1.94 GB** | **0.19%** | -87% waste | ⭐⭐⭐⭐⭐ |
| **Extended ML** | 11 + blobs | **2.01 GB** | **0.20%** | -85% waste | ⭐⭐⭐⭐⭐ |
| **ALL columns** | 23 total | 34.4 GB | 3.44% | 0% | ⭐⭐⭐ |

---

## Recommended: Extended ML Set (11 columns)

### Query
```sql
SELECT
  timestamp,
  number,
  gas_limit,
  gas_used,
  base_fee_per_gas,
  transaction_count,
  difficulty,
  total_difficulty,
  size,
  blob_gas_used,
  excess_blob_gas
FROM `bigquery-public-data.crypto_ethereum.blocks`
WHERE number BETWEEN 11560000 AND 24000000
ORDER BY number
```

### Results
```
Bytes processed: 2,013,671,672 bytes
               = 2.01 GB
               = 0.20% of free tier

Free tier remaining: 997.99 GB (99.8%)
Can run this query: ~497 times per month
Timeline: <1 hour
Storage: ~2 GB compressed Parquet
```

### What You Get
✅ **ALL time-series features** for forecasting:
- Gas economics (limit, used, base_fee)
- Network activity (transaction_count, size)
- Security/difficulty (difficulty, total_difficulty)
- Blob market (blob_gas_used, excess_blob_gas)

✅ **Future-proof**: Includes EIP-4844 blob fields for 2024+ analysis

✅ **No waste**: Zero random hashes or merkle roots

---

## What We're Discarding (12 columns, 32.4 GB)

### Cryptographic Hashes (No ML Value)
- `hash` - Random block hash
- `parent_hash` - Previous block hash
- `nonce` - Proof-of-work random value
- `sha3_uncles` - Uncle blocks hash
- `transactions_root` - Merkle root
- `state_root` - State trie root
- `receipts_root` - Receipts trie root
- `withdrawals_root` - Withdrawals trie root

### Other Non-ML Fields
- `logs_bloom` - 512-byte bloom filter (HUGE, no forecasting value)
- `extra_data` - Arbitrary miner text
- `miner` - Mining pool address (categorical, high cardinality)
- `withdrawals` - Nested array (complex structure)

**Why discard**: These have ZERO predictive value for time series forecasting. They're for blockchain verification, not ML.

**Storage waste**: 32.4 GB of random strings with no temporal patterns.

---

## Feature Engineering Examples

With the 11-column dataset, you can derive:

### Gas Market Features
```python
# Utilization pressure
df['gas_utilization'] = df['gas_used'] / df['gas_limit']

# Congestion indicator
df['is_congested'] = (df['gas_utilization'] > 0.95).astype(int)

# Base fee velocity
df['base_fee_pct_change'] = df['base_fee_per_gas'].pct_change()
df['base_fee_acceleration'] = df['base_fee_pct_change'].diff()
```

### Network Activity
```python
# Transactions per second
df['tps'] = df['transaction_count'] / 12  # ~12 sec blocks

# Average gas per transaction
df['avg_gas_per_tx'] = df['gas_used'] / df['transaction_count']

# Block fullness
df['fullness_ratio'] = df['size'] / df['size'].rolling(1000).max()
```

### Difficulty Dynamics
```python
# Pre/post Merge analysis
df['difficulty_ma'] = df['difficulty'].rolling(1000).mean()

# Chain growth rate
df['total_difficulty_velocity'] = df['total_difficulty'].diff()
```

### Blob Market (2024+)
```python
# Blob utilization
df['blob_utilization'] = df['blob_gas_used'] / 393216  # Max per block

# Blob fee pressure
df['excess_blob_ratio'] = df['excess_blob_gas'] / 393216
```

---

## Cost Breakdown by Column Type

| Column Type | Count | Size | % of Total | ML Value |
|-------------|-------|------|------------|----------|
| **Numeric time series** | 9 | 1.94 GB | 5.6% | ⭐⭐⭐⭐⭐ |
| **Blob metrics** | 2 | 0.07 GB | 0.2% | ⭐⭐⭐⭐⭐ |
| **Categorical** | 1 | 1.8 GB | 5.2% | ⭐⭐ |
| **Nested structures** | 1 | 0.3 GB | 0.9% | ⭐⭐ |
| **Hash/Merkle fields** | 10 | 30.3 GB | 88.1% | ❌ Zero |

**Insight**: 88% of the data (30 GB) is cryptographic hashes with zero ML value.

---

## Comparison: What 34 GB Gets You

### Option A: Get ALL 23 columns (34.4 GB)
```
✅ 11 useful columns (2 GB) - time series features
❌ 12 useless columns (32 GB) - random hashes

Result: 94% wasted storage
Value: Same as Option B for forecasting
```

### Option B: Get 11 ML columns (2 GB) ⭐ RECOMMENDED
```
✅ 11 useful columns (2 GB) - time series features
✅ Save 32 GB (94% reduction)
✅ Can query 497x/month vs 29x/month

Result: Zero waste
Value: Identical ML capability, 17x more queries available
```

---

## Real-World Analogy

Getting all 23 columns is like:

```
Ordering a 34 GB pizza where:
- 2 GB is actual pizza (the features you need)
- 32 GB is the cardboard box (hashes with no nutritional value)

Better approach:
- Order just the 2 GB pizza
- Throw away the cardboard
- Use saved money to order 17 more pizzas
```

---

## Final Recommendation

### Download This (11 columns, 2.01 GB)

```sql
SELECT
  timestamp,
  number,
  gas_limit,
  gas_used,
  base_fee_per_gas,
  transaction_count,
  difficulty,
  total_difficulty,
  size,
  blob_gas_used,
  excess_blob_gas
FROM `bigquery-public-data.crypto_ethereum.blocks`
WHERE number BETWEEN 11560000 AND 24000000
ORDER BY number
```

### Benefits
✅ **94% smaller** than all columns (2 GB vs 34 GB)
✅ **Same ML value** (hash fields have zero predictive power)
✅ **17x more queries** available with remaining free tier
✅ **Faster processing** (fewer columns to scan)
✅ **Easier feature engineering** (no hash string processing)

### What You're NOT Missing
❌ Random cryptographic hashes (cannot be forecasted)
❌ Merkle tree roots (deterministic checksums)
❌ Bloom filters (512-byte hex strings)
❌ Arbitrary miner text messages

**These have zero temporal patterns and zero correlation with gas prices, transaction volumes, or any forecastable metric.**

---

## Verification

Run this to confirm the exact cost before downloading:

```bash
bq query --dry_run --use_legacy_sql=false \
  'SELECT timestamp, number, gas_limit, gas_used, base_fee_per_gas,
          transaction_count, difficulty, total_difficulty, size,
          blob_gas_used, excess_blob_gas
   FROM `bigquery-public-data.crypto_ethereum.blocks`
   WHERE number BETWEEN 11560000 AND 24000000'
```

Expected output:
```
Query will process 2,013,671,672 bytes (2.01 GB)
✅ Well within free tier (0.20% of 1 TB/month)
```

Ready to download when you are!
