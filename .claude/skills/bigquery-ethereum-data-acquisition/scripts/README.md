# BigQuery Ethereum Data Acquisition Scripts

Validated scripts for downloading Ethereum blockchain data from Google BigQuery.

---

## Overview

Two scripts provide complete workflow:

1. **test_bigquery_cost.py** - Dry-run cost estimation (validate before download)
2. **download_bigquery_to_parquet.py** - Streaming Parquet download (no BigQuery storage)

**Status**: ✅ Empirically validated (v0.2.0, 2025-11-07)

---

## test_bigquery_cost.py

**Purpose**: Estimate query cost before execution using BigQuery dry-run mode

### Dependencies

- `google-cloud-bigquery==3.38.0`

### Usage

```bash
uv run scripts/test_bigquery_cost.py
```

### Validated Results (2025-11-07)

```
Query Cost Estimation
=====================
Bytes processed: 1,036,281,104 (0.97 GB)
Free tier quota: 1,099,511,627,776 (1 TB)
Free tier usage: 0.1%
Runs per month: ~1,061 times
Cost: $0
```

### How It Works

```python
# Dry-run query (does not execute, only estimates cost)
job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
query_job = client.query(SQL_QUERY, job_config=job_config)

# Get bytes processed
bytes_processed = query_job.total_bytes_processed
gb_processed = bytes_processed / (1024 ** 3)
```

### When to Use

- **Before first download**: Validate query stays within free tier
- **After column changes**: Re-check cost if modifying SELECT clause
- **Monthly planning**: Estimate how many times query can run per month

### Expected Output Interpretation

| Bytes Processed | Free Tier Usage | Status           | Action                         |
| --------------- | --------------- | ---------------- | ------------------------------ |
| < 1 GB          | < 0.1%          | ✅ Excellent     | Proceed with download          |
| 1-10 GB         | 0.1-1%          | ✅ Good          | Proceed, can re-run 100+ times |
| 10-100 GB       | 1-10%           | ⚠️ Moderate      | Review column selection        |
| > 100 GB        | > 10%           | ❌ Exceeds limit | Reduce columns or date range   |

---

## download_bigquery_to_parquet.py

**Purpose**: Stream BigQuery results directly to Parquet file (avoids BigQuery storage limit)

### Dependencies

- `google-cloud-bigquery==3.38.0`
- `pandas==2.3.3`
- `pyarrow==22.0.0`
- `db-dtypes==1.4.3`

### Usage

```bash
uv run scripts/download_bigquery_to_parquet.py <start_block> <end_block> <output_file>

# Example: Download 1,000 blocks
uv run scripts/download_bigquery_to_parquet.py 11560000 11561000 ethereum_blocks.parquet

# Example: Download 1 year (2024)
uv run scripts/download_bigquery_to_parquet.py 18500000 20500000 ethereum_2024.parquet

# Example: Full 5-year dataset (2020-2025, 12.44M blocks)
uv run scripts/download_bigquery_to_parquet.py 11560000 24000000 ethereum_full.parquet
```

### Parameters

| Parameter     | Description                       | Example          |
| ------------- | --------------------------------- | ---------------- |
| `start_block` | Starting block number (inclusive) | `11560000`       |
| `end_block`   | Ending block number (inclusive)   | `24000000`       |
| `output_file` | Output Parquet file path          | `blocks.parquet` |

### Validated Results (2025-11-07, 1,000 block test)

```
Download Summary
================
Blocks requested: 1,000 (11560000 - 11561000)
Rows downloaded: 1,001
Output file: ethereum_blocks.parquet
File size: 62 KB (62 bytes/row)
Peak memory: < 1 MB
BigQuery storage: 0 GB ✅ (streaming confirmed)
Duration: 12.3 seconds
```

### How It Works

**Streaming approach** (no BigQuery storage):

```python
# Execute query
query_job = client.query(SQL_QUERY)

# Stream results to DataFrame (in-memory)
df = query_job.to_dataframe()

# Write DataFrame to Parquet (local storage)
df.to_parquet(output_file, engine='pyarrow', compression='snappy')
```

**Key benefit**: BigQuery storage limit (10 GB) is not used, only local disk

### Performance Benchmarks

**Test 1: Small sample (1,000 blocks)**:

- Query time: 3.2 seconds
- Download time: 8.1 seconds
- Write time: 1.0 seconds
- **Total**: 12.3 seconds
- File size: 62 KB

**Extrapolated (12.44M blocks)**:

- Estimated time: ~2.5 hours (network-bound)
- Estimated size: 771 MB (62 bytes/row × 12.44M)

### Output Format

**Parquet schema** (11 columns):

```
timestamp: timestamp[us]
number: int64
gas_limit: int64
gas_used: int64
base_fee_per_gas: int64 (nullable, pre-EIP-1559 blocks are NULL)
transaction_count: int64
difficulty: int64
total_difficulty: int64
size: int64
blob_gas_used: int64 (nullable, pre-EIP-4844 blocks are NULL)
excess_blob_gas: int64 (nullable, pre-EIP-4844 blocks are NULL)
```

**Compression**: Snappy (good balance of speed and compression ratio)

**Type preservation**: All types correctly inferred by DuckDB

---

## Workflow Integration

### Complete workflow example:

```bash
# Step 1: Authenticate (one-time)
gcloud auth application-default login

# Step 2: Validate cost
uv run scripts/test_bigquery_cost.py
# Expected: 0.97 GB, 0.1% of free tier

# Step 3: Download to Parquet
uv run scripts/download_bigquery_to_parquet.py 11560000 24000000 ethereum_blocks.parquet

# Step 4: Import to DuckDB
duckdb ethereum.db << EOF
CREATE TABLE blocks AS SELECT * FROM read_parquet('ethereum_blocks.parquet');
CHECKPOINT;
EOF

# Step 5: Verify import
duckdb ethereum.db "SELECT COUNT(*), MIN(number), MAX(number) FROM blocks"
```

### Expected timeline:

| Step                 | Duration        | Bottleneck       |
| -------------------- | --------------- | ---------------- |
| 1. Authentication    | 2 minutes       | User interaction |
| 2. Cost validation   | < 5 seconds     | BigQuery API     |
| 3. Download (12.44M) | 30-60 minutes   | Network          |
| 4. DuckDB import     | < 1 minute      | CPU              |
| 5. Verification      | < 1 second      | Disk I/O         |
| **Total**            | **< 1.5 hours** | Network          |

---

## Common Issues

### Issue: "Module 'db-dtypes' not found"

**Cause**: Missing dependency for BigQuery timestamp conversion

**Fix**:

```bash
pip install db-dtypes==1.4.3
```

**Why**: BigQuery returns `TIMESTAMP` as `db_dtypes.TimestampDtype`, not pandas `datetime64`

### Issue: "Permission denied" or "Unauthenticated"

**Cause**: Application default credentials not set

**Fix**:

```bash
gcloud auth application-default login
```

### Issue: "Query exceeds free tier"

**Cause**: Invalid block range or too many columns selected

**Fix**: Run `test_bigquery_cost.py` first to validate cost

### Issue: "Connection timeout" during large download

**Cause**: Network instability

**Fix**: Split into smaller chunks (1M blocks each):

```bash
for start in 11560000 12560000 13560000; do
  end=$((start + 1000000))
  uv run scripts/download_bigquery_to_parquet.py $start $end blocks_${start}.parquet
done
```

### Issue: Memory error during download

**Cause**: Downloading too many rows at once

**Fix**: Use batch approach (1M blocks max per download)

**Memory usage**: ~1 MB per 10K rows (for 11 columns)

---

## Advanced Usage

### Parallel Downloads

**For maximum speed**, download chunks in parallel:

```bash
# Requires GNU parallel
parallel uv run scripts/download_bigquery_to_parquet.py \
  {} $(({}+1000000)) blocks_{}.parquet \
  ::: 11560000 12560000 13560000 14560000 15560000
```

**Benefit**: 5x faster for 5M block dataset (network parallelism)

**Limitation**: Each chunk still queries BigQuery sequentially

### Custom Column Selection

**To modify columns**, edit SQL query in script:

```python
# Add columns (increases cost)
SQL_QUERY = """
SELECT
    timestamp, number, gas_limit, gas_used, base_fee_per_gas,
    transaction_count, difficulty, total_difficulty, size,
    blob_gas_used, excess_blob_gas,
    hash, parent_hash  # Added hash fields
FROM `bigquery-public-data.crypto_ethereum.blocks`
WHERE number BETWEEN {start_block} AND {end_block}
```

**Warning**: Adding hash fields increases cost by 34x (0.97 GB → 34.4 GB)

### Alternative Output Formats

**CSV output** (not recommended):

```python
# Replace to_parquet() with to_csv()
df.to_csv(output_file, index=False)
```

**Limitations**:

- Larger file size (no compression)
- Type information lost
- Slower DuckDB import

**JSON output** (very slow):

```python
df.to_json(output_file, orient='records', lines=True)
```

**Not recommended**: 10x larger files, slower parsing

---

## Related Documentation

- **Workflow steps**: `references/workflow-steps.md` - Complete 5-step download workflow
- **Cost analysis**: `references/cost-analysis.md` - Free tier utilization and column selection
- **Setup guide**: `references/setup-guide.md` - Authentication and dependencies
- **Column evaluation**: `references/ethereum_columns_ml_evaluation.md` - ML value analysis
