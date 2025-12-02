# BigQuery Ethereum Data Acquisition Workflow

This document provides the complete 5-step workflow for acquiring Ethereum blockchain data from Google BigQuery.

---

## Step 1: Understand Free Tier Limits

BigQuery has two separate limits:

- **Query Processing**: 1 TB/month (data scanned)
- **Storage**: 10 GB (saved tables)

**Key principle**: Query public datasets and stream results directly to avoid storage limits.

**Why this matters**:

- Query limit applies to data scanned, not rows returned
- Storage limit only applies to tables you create/save in BigQuery
- Streaming results directly bypasses storage entirely

**Free tier strategy**:

```
Query public dataset → Stream to Parquet → Load to DuckDB
                      ↑ No BigQuery storage used
```

---

## Step 2: Select Columns for ML/Time-Series

**Recommended columns** (11 total, 0.97 GB cost):

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
```

**Discarded columns** (12 total, 33.4 GB):

- Cryptographic hashes (zero ML value):
  - `hash` (32-byte block hash)
  - `parent_hash` (previous block hash)
  - `nonce` (mining nonce)
  - `miner` (address hash)

- Merkle roots (deterministic checksums):
  - `transactions_root`
  - `state_root`
  - `receipts_root`
  - `withdrawals_root`

- Categorical fields (high cardinality):
  - `extra_data` (arbitrary miner data)
  - `logs_bloom` (256-byte bloom filter)
  - `sha3_uncles`
  - `mix_hash`

**Rationale**: 11-column selection reduces query cost by 97% (0.97 GB vs 34.4 GB) with no loss of forecasting capability.

**Column analysis**: See `ethereum_columns_ml_evaluation.md` for detailed column-by-column ML value analysis.

---

## Step 3: Validate Query Cost (Dry-Run)

**Status**: ✅ TESTED (2025-11-07)

Test query cost before execution using Python:

```bash
uv run scripts/test_bigquery_cost.py
```

**Validated Results**:

- Bytes processed: 1,036,281,104 (0.97 GB)
- Free tier usage: 0.1% of 1 TB monthly quota
- Runs per month: ~1,061 times
- Cost: $0

**Alternative (bq CLI)**:

```bash
bq query --dry_run --use_legacy_sql=false \
  'SELECT timestamp, number, gas_limit, gas_used, base_fee_per_gas,
          transaction_count, difficulty, total_difficulty, size,
          blob_gas_used, excess_blob_gas
   FROM `bigquery-public-data.crypto_ethereum.blocks`
   WHERE number BETWEEN 11560000 AND 24000000'
```

**Output interpretation**:

```
Query successfully validated. Assuming the tables are not modified,
running this query will process 1036281104 bytes of data.
```

**Cost calculation**:

- First 1 TB free per month
- Beyond 1 TB: $5 per TB
- 0.97 GB is well within free tier

---

## Step 4: Stream Results Directly (No Storage Used)

**Status**: ✅ TESTED (2025-11-07)

### Method A: Python + Parquet (Recommended)

**Usage**:

```bash
uv run scripts/download_bigquery_to_parquet.py 11560000 24000000 ethereum_blocks.parquet
```

**Validated Results** (1,000 block test):

- Rows: 1,001
- File size: 62 KB (62 bytes/row)
- Memory: < 1 MB
- BigQuery storage: 0 GB (streaming confirmed)

**Why Parquet**:

- Columnar storage format (efficient for time-series)
- Compression (smaller file size)
- DuckDB native support (zero-copy reads)
- Type preservation (no CSV parsing issues)

### Method B: bq CLI + CSV (Alternative)

**Usage**:

```bash
bq query --format=csv --max_rows=15000000 --use_legacy_sql=false \
  'SELECT timestamp, number, gas_limit, gas_used, base_fee_per_gas,
          transaction_count, difficulty, total_difficulty, size,
          blob_gas_used, excess_blob_gas
   FROM `bigquery-public-data.crypto_ethereum.blocks`
   WHERE number BETWEEN 11560000 AND 24000000
   ORDER BY number' > ethereum_blocks.csv
```

**Limitations**:

- CSV format loses type information
- Larger file size (no compression)
- Requires parsing (slower DuckDB import)

**Recommendation**: Use Method A (Parquet) unless CSV needed for compatibility.

---

## Step 5: Load into DuckDB

**Status**: ✅ TESTED (2025-11-07)

### Import Parquet to DuckDB

```bash
duckdb ethereum.db << EOF
CREATE TABLE blocks AS SELECT * FROM read_parquet('ethereum_blocks.parquet');
CHECKPOINT;
EOF
```

**Validated Results**:

- DuckDB version: 1.4.1
- Query time: < 100ms for 1,001 rows
- Schema: Correctly inferred from Parquet

### Verify Import

```bash
duckdb ethereum.db "SELECT COUNT(*), MIN(number), MAX(number) FROM blocks"
```

**Expected output** (1,000 block test):

```
┌──────────────┬─────────────┬─────────────┐
│ count_star() │ min(number) │ max(number) │
├──────────────┼─────────────┼─────────────┤
│         1001 │    11560000 │    11561000 │
└──────────────┴─────────────┴─────────────┘
```

### Query Examples

**Time-series aggregation**:

```sql
SELECT
    time_bucket(INTERVAL '1 day', timestamp) AS day,
    AVG(gas_used) AS avg_gas_used,
    AVG(transaction_count) AS avg_tx_count
FROM blocks
GROUP BY day
ORDER BY day;
```

**Block utilization analysis**:

```sql
SELECT
    number,
    timestamp,
    (gas_used::DOUBLE / gas_limit::DOUBLE) * 100 AS utilization_pct
FROM blocks
WHERE gas_used > gas_limit * 0.95
ORDER BY timestamp;
```

---

## Complete Workflow Example

**Scenario**: Download 12.44M Ethereum blocks (2020-2025) for ML feature engineering

### Step-by-step execution:

```bash
# 1. Authenticate (one-time)
gcloud auth application-default login

# 2. Validate cost (expect 0.97 GB)
uv run scripts/test_bigquery_cost.py

# 3. Download to Parquet (streaming, no BigQuery storage)
uv run scripts/download_bigquery_to_parquet.py 11560000 24000000 ethereum_blocks.parquet

# 4. Import to DuckDB
duckdb ethereum.db << EOF
CREATE TABLE blocks AS SELECT * FROM read_parquet('ethereum_blocks.parquet');
CHECKPOINT;
EOF

# 5. Verify import
duckdb ethereum.db "SELECT COUNT(*), MIN(number), MAX(number), MIN(timestamp), MAX(timestamp) FROM blocks"
```

**Expected timeline**:

- Cost validation: < 5 seconds
- Download: < 1 hour (network-bound)
- DuckDB import: < 1 minute
- Total: < 1.5 hours

**Comparison to RPC polling**:

- BigQuery: < 1 hour
- RPC (Alchemy 5.79 RPS): 26 days
- **Speedup: 624x faster**

---

## Troubleshooting

### Issue: "Permission denied" during authentication

**Cause**: Application default credentials not set

**Fix**:

```bash
gcloud auth application-default login
```

### Issue: "Table not found" error

**Cause**: Invalid dataset path

**Fix**: Verify BigQuery dataset exists:

```bash
bq ls bigquery-public-data:crypto_ethereum
```

### Issue: Query exceeds free tier

**Cause**: Selected too many columns or wrong date range

**Fix**: Run dry-run first to validate cost:

```bash
uv run scripts/test_bigquery_cost.py
```

### Issue: DuckDB import fails with type errors

**Cause**: CSV format loses type information

**Fix**: Use Parquet format (Method A) instead of CSV (Method B)

---

## Performance Optimization

**For large downloads** (10M+ blocks):

1. **Batch downloads**: Split into 1M block chunks

   ```bash
   for start in 11560000 12560000 13560000 14560000; do
     end=$((start + 1000000))
     uv run scripts/download_bigquery_to_parquet.py $start $end blocks_${start}.parquet
   done
   ```

2. **Parallel imports**: Use DuckDB UNION ALL

   ```sql
   CREATE TABLE blocks AS
   SELECT * FROM read_parquet('blocks_11560000.parquet')
   UNION ALL
   SELECT * FROM read_parquet('blocks_12560000.parquet')
   UNION ALL
   SELECT * FROM read_parquet('blocks_13560000.parquet');
   CHECKPOINT;
   ```

3. **Monitor progress**: Add logging to scripts
   ```python
   print(f"Downloaded {rows_downloaded}/{total_rows} rows ({rows_downloaded/total_rows*100:.1f}%)")
   ```

---

## Related Documentation

- **Cost analysis**: `cost-analysis.md` - Detailed cost comparison and column selection rationale
- **Setup guide**: `setup-guide.md` - Authentication, dependencies, verification
- **Column evaluation**: `ethereum_columns_ml_evaluation.md` - ML value analysis for each column
- **Scripts usage**: `scripts/README.md` - Complete script documentation
