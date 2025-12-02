# Ethereum Blocks Columns: ML/Time Series Forecasting Value Analysis

**Purpose**: Evaluate which columns to keep/discard for time series forecasting and feature construction

**Evaluation Criteria**:

- ✅ **KEEP**: Numeric, varies over time, shows patterns/trends, predictive value
- ⚠️ **MAYBE**: Limited utility, situational, or sparse
- ❌ **DISCARD**: No predictive value, random data, integrity-only fields

---

## Column-by-Column Analysis (23 Total)

### ✅ CRITICAL - Must Keep (9 columns)

| Column                | Type      | Why Keep                  | Use Cases                                                |
| --------------------- | --------- | ------------------------- | -------------------------------------------------------- |
| **timestamp**         | TIMESTAMP | Target variable alignment | Time index for all features                              |
| **number**            | INTEGER   | Block sequence index      | Primary key, gap detection                               |
| **gas_limit**         | INTEGER   | Network capacity ceiling  | Capacity planning, congestion forecasting                |
| **gas_used**          | INTEGER   | Actual network usage      | **Utilization = gas_used/gas_limit**, demand forecasting |
| **base_fee_per_gas**  | INTEGER   | EIP-1559 price signal     | **PRIMARY TARGET** for price forecasting                 |
| **transaction_count** | INTEGER   | Activity level            | Network demand indicator                                 |
| **difficulty**        | NUMERIC   | Mining/staking difficulty | Network health, security level                           |
| **total_difficulty**  | NUMERIC   | Cumulative chain work     | Chain growth rate, long-term trends                      |
| **size**              | INTEGER   | Block size in bytes       | Data throughput, capacity usage                          |

**Why critical**: These are the ONLY columns with temporal patterns suitable for forecasting. All contain numeric time series data that varies meaningfully over time.

### ✅ USEFUL - Keep for Post-2020 Data (2 columns)

| Column              | Type    | Why Keep               | Limitations                                        |
| ------------------- | ------- | ---------------------- | -------------------------------------------------- |
| **blob_gas_used**   | INTEGER | EIP-4844 blob usage    | Only post-Dencun (March 2024+), mostly NULL before |
| **excess_blob_gas** | INTEGER | Blob pricing mechanism | Only post-Dencun (March 2024+), mostly NULL before |

**Why useful**: Important for 2024+ data, but will be NULL for most of your 2020-2024 range. Keep for future-proofing.

### ⚠️ MARGINAL - Situational Value (2 columns)

| Column          | Type     | Why Maybe                     | Issues                                                                 |
| --------------- | -------- | ----------------------------- | ---------------------------------------------------------------------- |
| **miner**       | STRING   | Mining pool distribution      | **Categorical** with 100s of values, high cardinality, encoding issues |
| **withdrawals** | RECORD[] | Validator withdrawal activity | Only post-Merge (Sept 2022+), **nested structure**, complex to process |

**Analysis**:

- **miner**: Could be useful for "which pool is most active" analysis, but terrible for time series (categorical). If you want mining pool concentration metrics, better to aggregate separately.
- **withdrawals**: Complex nested structure (array of records). Useful for post-Merge validator analysis, but adds complexity. Better extracted separately if needed.

**Recommendation**: **Skip both unless you specifically need mining pool or validator analysis**

### ❌ DISCARD - Zero ML Value (12 columns)

| Column                | Type   | Why Discard                                                   |
| --------------------- | ------ | ------------------------------------------------------------- |
| **hash**              | STRING | Cryptographically random, zero predictive value               |
| **parent_hash**       | STRING | Just links to previous block, no forecasting value            |
| **nonce**             | STRING | Random proof-of-work value, unpredictable by design           |
| **sha3_uncles**       | STRING | Hash of uncle blocks, no temporal patterns                    |
| **logs_bloom**        | STRING | **HUGE hex string** (512 bytes), just a bloom filter for logs |
| **transactions_root** | STRING | Merkle tree root, deterministic from transactions             |
| **state_root**        | STRING | Merkle tree root, deterministic from state                    |
| **receipts_root**     | STRING | Merkle tree root, deterministic from receipts                 |
| **extra_data**        | STRING | Arbitrary miner text, no predictive value                     |
| **withdrawals_root**  | STRING | Hash of withdrawals, deterministic                            |

**Why discard**:

1. **Cryptographic hashes**: Completely random by design, contain zero predictive information
2. **Merkle roots**: Deterministic checksums, not time series features
3. **Arbitrary data**: extra_data is just miner messages ("geth 1.10.0" etc.)
4. **Huge storage**: logs_bloom alone is 512 bytes per row × 12.44M = 6.4 GB of useless hex strings

**Cost savings**: Removing these 12 columns reduces data size from 34.4 GB → ~5-8 GB

---

## Recommended Feature Set

### Minimal Set (9 columns) - For Pure Time Series Forecasting

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
  size
FROM `bigquery-public-data.crypto_ethereum.blocks`
WHERE number BETWEEN 11560000 AND 24000000
ORDER BY number
```

**Cost**: ~5-8 GB (estimated)
**Use case**: Time series forecasting of gas prices, network utilization, transaction volume

### Extended Set (11 columns) - For 2024+ Data

Add if analyzing recent blocks:

```sql
  blob_gas_used,
  excess_blob_gas
```

**Cost**: ~6-9 GB
**Use case**: Forecasting with EIP-4844 blob pricing features

---

## Feature Engineering Recommendations

Once you have the 9-11 core columns, derive these features:

### 1. Utilization Metrics

```python
df['gas_utilization'] = df['gas_used'] / df['gas_limit']
df['capacity_pressure'] = df['gas_used'].rolling(100).mean() / df['gas_limit']
```

### 2. Price Velocity

```python
df['base_fee_change'] = df['base_fee_per_gas'].pct_change()
df['base_fee_volatility'] = df['base_fee_per_gas'].rolling(100).std()
```

### 3. Network Activity

```python
df['tx_per_second'] = df['transaction_count'] / 12  # ~12 sec blocks
df['avg_gas_per_tx'] = df['gas_used'] / df['transaction_count']
```

### 4. Difficulty Trends

```python
df['difficulty_change'] = df['difficulty'].pct_change()
df['difficulty_ma'] = df['difficulty'].rolling(1000).mean()  # Smooth pre/post-Merge
```

### 5. Block Capacity

```python
df['bytes_per_tx'] = df['size'] / df['transaction_count']
df['size_utilization'] = df['size'] / df['size'].rolling(1000).max()
```

### 6. Blob Metrics (2024+ only)

```python
df['blob_utilization'] = df['blob_gas_used'] / 393216  # Max blob gas per block
df['blob_fee_market_pressure'] = df['excess_blob_gas'] / 393216
```

---

## Cost-Benefit Analysis

| Column Set          | Columns            | Est. Size | % Free Tier | ML Value   | Storage Waste               |
| ------------------- | ------------------ | --------- | ----------- | ---------- | --------------------------- |
| **Minimal (9)**     | Core features only | ~5-8 GB   | 0.5-0.8%    | ⭐⭐⭐⭐⭐ | 0%                          |
| **Extended (11)**   | + blob metrics     | ~6-9 GB   | 0.6-0.9%    | ⭐⭐⭐⭐⭐ | 0%                          |
| **With miner (12)** | + mining pools     | ~8-11 GB  | 0.8-1.1%    | ⭐⭐⭐     | ~20% (categorical noise)    |
| **All 23 columns**  | Including hashes   | 34.4 GB   | 3.4%        | ⭐⭐⭐     | ~65% (hashes have no value) |

---

## Why Hash Fields Are Worthless for ML

### Example: Block Hash

```
Block 12345678:
hash = "0x3f07a9c8e1d2b5a4c6d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"

This is:
- Cryptographically random (by design)
- Unique per block (no patterns)
- Unpredictable (even 1 bit change in block = completely different hash)
- Zero correlation with gas prices, transaction counts, or any forecastable metric
```

**Storage cost**: 66 bytes per hash × 12.44M blocks × 10 hash fields = ~8 GB of random strings

**ML value**: Literally zero. You cannot forecast hash[n+1] from hash[n].

---

## What Hash Fields ARE Good For

These fields are for **data integrity and verification**, not ML:

1. **Blockchain validation**: Verify chain hasn't been tampered with
2. **Transaction verification**: Prove a transaction was included
3. **Smart contract calls**: Identify specific blocks/transactions

**Use case example**:

```python
# Verify block chain integrity (NOT ML)
assert block[n].parent_hash == block[n-1].hash

# Query specific transaction (NOT ML)
tx = eth.get_transaction('0x3f07a9...')
```

**For time series forecasting**: Completely irrelevant.

---

## Recommended Query (Optimized for ML)

### Version 1: Minimal (Best for Most Use Cases)

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
  size
FROM `bigquery-public-data.crypto_ethereum.blocks`
WHERE number BETWEEN 11560000 AND 24000000
ORDER BY number
```

**Estimated cost**: 5-8 GB (0.5-0.8% of free tier)
**Reduction**: 34.4 GB → 6 GB = **82% storage savings**
**Loss**: None (discarded columns have zero ML value)

### Version 2: Extended (For 2024+ Analysis)

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

**Estimated cost**: 6-9 GB (0.6-0.9% of free tier)

---

## Summary

### Keep These (9-11 columns):

✅ timestamp, number, gas_limit, gas_used, base_fee_per_gas, transaction_count, difficulty, total_difficulty, size
✅ blob_gas_used, excess_blob_gas (if analyzing 2024+ data)

### Discard These (12 columns):

❌ hash, parent_hash, nonce, sha3_uncles, logs_bloom, transactions_root, state_root, receipts_root, extra_data, withdrawals_root

### Skip These (2 columns):

⚠️ miner (high cardinality categorical, minimal time series value)
⚠️ withdrawals (complex nested structure, post-Merge only, better extracted separately)

### Result:

- **82% smaller dataset** (34.4 GB → 6 GB)
- **Zero loss of predictive features**
- **Easier feature engineering** (no hash string processing)
- **Faster queries** (columnar scan of 9 vs 23 columns)

---

## Test Query to Confirm Cost

```bash
# Check actual cost of minimal feature set
bq query --dry_run --use_legacy_sql=false \
  'SELECT timestamp, number, gas_limit, gas_used, base_fee_per_gas,
          transaction_count, difficulty, total_difficulty, size
   FROM `bigquery-public-data.crypto_ethereum.blocks`
   WHERE number BETWEEN 11560000 AND 24000000'
```

Want me to run this to confirm the exact cost?
