# BigQuery Setup Guide

This document provides complete setup instructions for Google BigQuery Ethereum data acquisition.

---

## Prerequisites

### System Requirements

- **Operating System**: macOS, Linux, or Windows with WSL
- **Python**: 3.9+ (3.12+ recommended)
- **Package Manager**: uv (for PEP 723 inline dependencies)
- **Network**: Stable internet connection (download is network-bound)
- **Disk Space**: ~1 GB for 12.44M blocks (Parquet format)

### Optional Requirements

- **DuckDB**: 1.4.1+ for local queries (optional, not required for download)
- **gcloud CLI**: For authentication (alternative: service account key)

---

## Authentication Setup

### Method A: Application Default Credentials (Recommended)

**One-time setup** (< 5 minutes):

```bash
# Install gcloud CLI (if not installed)
# macOS
brew install google-cloud-sdk

# Ubuntu/Debian
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Windows (WSL)
curl https://sdk.cloud.google.com | bash

# Authenticate
gcloud auth application-default login
```

**What this does**:
- Opens browser for Google account authentication
- Stores credentials at `~/.config/gcloud/application_default_credentials.json`
- Python BigQuery client automatically finds credentials

**Verify authentication**:

```bash
gcloud auth application-default print-access-token
```

**Expected output**: Access token string (means authentication successful)

### Method B: Service Account Key (Alternative)

**Use case**: Headless servers, CI/CD pipelines, no browser access

**Steps**:

1. Create service account in Google Cloud Console
2. Download JSON key file
3. Set environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
   ```

**Not recommended for local development** (use Method A instead)

---

## Verify BigQuery Access

**Check access to public dataset**:

```bash
bq ls bigquery-public-data:crypto_ethereum
```

**Expected output**:
```
         tableId           Type
-------------------------- -------
 blocks                    TABLE
 contracts                 TABLE
 logs                      TABLE
 token_transfers           TABLE
 traces                    TABLE
 transactions              TABLE
 ...
```

**If error occurs**:
- "Permission denied": Re-run `gcloud auth application-default login`
- "Dataset not found": Check dataset path (should be `bigquery-public-data.crypto_ethereum`)

---

## Python Dependencies

### Install Dependencies (PEP 723)

All scripts use PEP 723 inline dependencies (no manual installation required):

```python
# /// script
# dependencies = [
#   "google-cloud-bigquery==3.38.0",
#   "pandas==2.3.3",
#   "pyarrow==22.0.0",
#   "db-dtypes==1.4.3",
# ]
# ///
```

**Run with uv**:

```bash
uv run scripts/test_bigquery_cost.py
```

uv automatically installs dependencies in isolated environment.

### Manual Installation (Optional)

**If not using uv**:

```bash
pip install google-cloud-bigquery==3.38.0 pandas==2.3.3 pyarrow==22.0.0 db-dtypes==1.4.3
```

**Dependency purposes**:
- `google-cloud-bigquery`: BigQuery client library
- `pandas`: DataFrame for data manipulation
- `pyarrow`: Parquet file format support
- `db-dtypes`: BigQuery timestamp type conversion

---

## Verification Tests

### Test 1: Authentication

```bash
python -c "from google.cloud import bigquery; client = bigquery.Client(); print('✅ Authentication successful')"
```

**Expected output**: `✅ Authentication successful`

**If error occurs**:
- `DefaultCredentialsError`: Run `gcloud auth application-default login`
- `ImportError`: Install `google-cloud-bigquery`

### Test 2: BigQuery Access

```bash
bq query --dry_run --use_legacy_sql=false \
  'SELECT COUNT(*) FROM `bigquery-public-data.crypto_ethereum.blocks` LIMIT 1'
```

**Expected output**:
```
Query successfully validated.
```

### Test 3: Cost Estimation

```bash
uv run scripts/test_bigquery_cost.py
```

**Expected output**:
```
Bytes processed: 1,036,281,104 (0.97 GB)
Free tier usage: 0.1% of 1 TB monthly quota
Cost: $0
```

### Test 4: Small Download

```bash
uv run scripts/download_bigquery_to_parquet.py 21000000 21001000 test.parquet
```

**Expected output**:
```
Downloaded 1001 rows to test.parquet (62 KB)
```

---

## DuckDB Setup (Optional)

### Install DuckDB

**macOS**:
```bash
brew install duckdb
```

**Ubuntu/Debian**:
```bash
wget https://github.com/duckdb/duckdb/releases/download/v1.4.1/duckdb_cli-linux-amd64.zip
unzip duckdb_cli-linux-amd64.zip
sudo mv duckdb /usr/local/bin/
```

**Verify installation**:
```bash
duckdb --version
```

**Expected output**: `v1.4.1` or higher

### Import Parquet to DuckDB

```bash
duckdb ethereum.db << EOF
CREATE TABLE blocks AS SELECT * FROM read_parquet('test.parquet');
CHECKPOINT;
SELECT COUNT(*) FROM blocks;
EOF
```

**Expected output**:
```
┌──────────────┐
│ count_star() │
├──────────────┤
│         1001 │
└──────────────┘
```

---

## Troubleshooting

### Issue: "Permission denied" or "Unauthenticated"

**Cause**: Application default credentials not set

**Fix**:
```bash
gcloud auth application-default login
```

**Verify**:
```bash
ls ~/.config/gcloud/application_default_credentials.json
```

### Issue: "Module 'db-dtypes' not found"

**Cause**: Missing dependency for BigQuery timestamp conversion

**Fix**:
```bash
pip install db-dtypes==1.4.3
```

**Why needed**: BigQuery returns timestamps as `db_dtypes.TimestampDtype`, not native pandas types

### Issue: "Query exceeds free tier"

**Cause**: Selected too many columns or invalid date range

**Fix**: Run cost estimation first:
```bash
uv run scripts/test_bigquery_cost.py
```

**Verify**: Bytes processed < 1 GB (well within free tier)

### Issue: "Dataset not found"

**Cause**: Invalid BigQuery dataset path

**Fix**: Verify dataset exists:
```bash
bq ls bigquery-public-data:crypto_ethereum
```

**Correct path**: `bigquery-public-data.crypto_ethereum.blocks`

### Issue: "Connection timeout" during download

**Cause**: Network instability or firewall blocking BigQuery API

**Fix**:
1. Check internet connection
2. Verify firewall allows HTTPS to `*.googleapis.com`
3. Try smaller batch (1,000 blocks instead of 1M)

### Issue: DuckDB import fails with "Type mismatch"

**Cause**: CSV format loses type information

**Fix**: Use Parquet format (default in `download_bigquery_to_parquet.py`)

**Why Parquet**: Preserves column types (BIGINT, TIMESTAMP, DOUBLE) without parsing

---

## Performance Optimization

### Parallel Downloads

**For large datasets** (10M+ blocks), split into chunks:

```bash
# Sequential
for start in 11560000 12560000 13560000 14560000; do
  end=$((start + 1000000))
  uv run scripts/download_bigquery_to_parquet.py $start $end blocks_${start}.parquet
done

# Parallel (requires GNU parallel)
parallel uv run scripts/download_bigquery_to_parquet.py \
  {} $(({}+1000000)) blocks_{}.parquet \
  ::: 11560000 12560000 13560000 14560000
```

### Network Optimization

**Resume interrupted downloads**:
- BigQuery does not support resume
- Workaround: Split into smaller chunks (100K blocks each)
- If chunk fails, retry only that chunk

**Bandwidth estimation**:
- 62 bytes/row × 12.44M rows = 771 MB total
- 100 Mbps connection: ~60 seconds
- 10 Mbps connection: ~10 minutes

---

## Security Considerations

### Credentials Management

**DO**:
- Use application default credentials (gcloud auth)
- Store service account keys in secure location (not in git)
- Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable

**DO NOT**:
- Commit credentials to version control
- Share credentials via email or chat
- Use personal credentials for production services

### Data Privacy

**Public dataset**:
- Ethereum blockchain is public data
- No PII or sensitive information
- Safe to download and analyze

**Query logs**:
- BigQuery logs all queries
- Logs stored in Google Cloud (not shared publicly)
- Queries are not billed in free tier

---

## Related Documentation

- **Workflow steps**: `workflow-steps.md` - Complete download workflow
- **Cost analysis**: `cost-analysis.md` - Free tier utilization and cost optimization
- **Scripts usage**: `scripts/README.md` - Script documentation with examples
