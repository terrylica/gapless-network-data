# Troubleshooting Historical Backfill

**Version**: 1.0.0
**Last Updated**: 2025-11-13
**Canonical Pattern**: 1-year chunks (Cloud Run safe)

## Common Issues

### 1. OOM Error (Exit Code 137)

**Symptom**:
```
Cloud Run Job failed: Memory limit exceeded
Exit code: 137 (SIGKILL)
```

**Root Cause**: Chunk size exceeds Cloud Run memory limit (4GB default)

**Solution 1** - Reduce chunk size:
```bash
# Instead of 1 year
./chunked_backfill.sh 2020 2020

# Use 6 months
./chunked_backfill.sh 2020-01-01 2020-06-30
./chunked_backfill.sh 2020-07-01 2020-12-31
```

**Solution 2** - Increase Cloud Run memory:
```bash
# Update Cloud Run Job to 8GB memory
gcloud run jobs update ethereum-historical-backfill \
  --region us-central1 \
  --memory 8Gi
```

**Validation**:
```bash
# Estimate memory before execution
uv run .claude/skills/historical-backfill-execution/scripts/validate_chunk_size.py --year 2020
```

### 2. BigQuery Quota Exceeded

**Symptom**:
```
ERROR: Quota exceeded: Your project exceeded quota for free tier bytes scanned
```

**Root Cause**: Exceeded 1TB/month free tier in BigQuery

**Solution**:
1. **Wait for quota reset**: Quotas reset monthly (1st of each month)
2. **Reduce query frequency**: Don't run backfill multiple times in same month
3. **Verify query size**:
   ```bash
   # Check query cost in BigQuery Console
   # Expected: ~10 MB per year (11 columns)
   ```

**Prevention**:
- Use 11-column optimized schema (97% cost savings vs full 23 columns)
- Don't query full table unless necessary
- See `.claude/skills/bigquery-ethereum-data-acquisition/DECISION_RATIONALE.md` for column selection

### 3. Permission Denied (BigQuery)

**Symptom**:
```
ERROR: Permission denied: User does not have bigquery.jobs.create permission
```

**Root Cause**: Missing IAM roles for service account

**Solution**:
```bash
# Grant required role to service account
gcloud projects add-iam-policy-binding eonlabs-ethereum-bq \
  --member="serviceAccount:eth-md-job-sa@eonlabs-ethereum-bq.iam.gserviceaccount.com" \
  --role="roles/bigquery.user"
```

**Required Roles**:
- `roles/bigquery.user` - Run queries
- `roles/bigquery.dataViewer` - Read public dataset (auto-granted for public datasets)

### 4. MotherDuck Connection Failed

**Symptom**:
```
ERROR: Failed to connect to MotherDuck
ERROR: Authentication failed
```

**Root Cause**: Missing or invalid MotherDuck token

**Solution 1** - Verify Secret Manager:
```bash
# Check secret exists
gcloud secrets describe motherduck-token --project eonlabs-ethereum-bq

# Verify service account has access
gcloud secrets get-iam-policy motherduck-token --project eonlabs-ethereum-bq
```

**Solution 2** - Test connection locally:
```python
import duckdb

# Test MotherDuck connection
conn = duckdb.connect('md:?motherduck_token=<token>')
conn.execute("SELECT 1").fetchall()
```

### 5. Slow Execution (>5 minutes per year)

**Symptom**: Backfill takes significantly longer than expected (~2 minutes per year)

**Root Cause**: Network latency, wrong Cloud Run region, or BigQuery throttling

**Solution 1** - Check Cloud Run region:
```bash
# Cloud Run should be in same region as BigQuery (US)
gcloud run jobs describe ethereum-historical-backfill --region us-central1 | grep region
```

**Solution 2** - Check network connectivity:
```bash
# Test BigQuery connection speed
time gcloud bigquery query --use_legacy_sql=false \
  'SELECT COUNT(*) FROM `bigquery-public-data.crypto_ethereum.blocks` WHERE number < 1000'
```

**Expected**: <5 seconds for test query

### 6. Table Not Found

**Symptom**:
```
ERROR: Table not found: bigquery-public-data.crypto_ethereum.blocks
```

**Root Cause**: Incorrect dataset name or project ID

**Solution**:
```bash
# Verify public dataset exists
bq show bigquery-public-data:crypto_ethereum.blocks

# Expected output:
#   Last modified: ...
#   Schema: ...
```

**Correct Dataset**: `bigquery-public-data.crypto_ethereum.blocks` (not `crypto_ethereum_classic`)

### 7. Duplicate Blocks

**Symptom**: Same block appears multiple times in MotherDuck

**Root Cause**: Backfill script run multiple times without `INSERT OR REPLACE`

**Solution**:
```sql
-- Check for duplicates
SELECT number, COUNT(*) as count
FROM ethereum_mainnet.blocks
GROUP BY number
HAVING COUNT(*) > 1;
```

**Fix**:
```sql
-- Remove duplicates (keep latest by timestamp)
DELETE FROM ethereum_mainnet.blocks
WHERE (number, timestamp) NOT IN (
    SELECT number, MAX(timestamp)
    FROM ethereum_mainnet.blocks
    GROUP BY number
);
```

**Prevention**: Always use `INSERT OR REPLACE` in backfill script (idempotent)

### 8. Missing Blocks (Gaps)

**Symptom**: Gap detection shows missing block ranges

**Root Cause**: Partial backfill execution (script failed mid-execution)

**Solution**:
```bash
# Trigger gap detection via Cloud Scheduler
gcloud scheduler jobs run motherduck-monitor-trigger --location=us-east1

# View gap monitor logs
gcloud functions logs read motherduck-gap-detector --region=us-east1 --gen2 --limit=50
```

**Manual Fill** (specific year):
```bash
# Re-run backfill for specific year
cd deployment/backfill
./chunked_backfill.sh 2018 2018
```

## Diagnostic Workflow

```
1. Check Cloud Run Job logs
   ↓
   └─ Exit code? ──137──> OOM error ──> Reduce chunk size or increase memory
         │
       0 (success)
         ↓
2. Verify blocks in MotherDuck
   ↓
   └─ Expected count? ──No──> Detect gaps ──> Auto-fill
         │
        Yes
         ↓
3. Check for duplicates
   ↓
   └─ Duplicates? ──Yes──> Remove duplicates (keep latest)
         │
         No
         ↓
4. Backfill successful ✅
```

## Cloud Run Logs

### View Recent Execution Logs

```bash
# List recent executions
gcloud run jobs executions list \
  --job ethereum-historical-backfill \
  --region us-central1

# View specific execution logs
gcloud run jobs executions logs <EXECUTION_NAME> \
  --region us-central1
```

### Useful Log Filters

```bash
# Filter for errors only
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=ethereum-historical-backfill AND severity>=ERROR" --limit 50

# Filter for OOM errors
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=ethereum-historical-backfill AND jsonPayload.message=~'Memory limit'" --limit 50
```

## Performance Tuning

### Expected Performance

| Metric | Expected Value | Measured (2025-11-10) |
|--------|---------------|------------------------|
| Time per year | 1m40s-2m | 1m42s-1m58s ✅ |
| Total time (10yr) | 17-20 min | 18m45s ✅ |
| Memory per year | <4GB | 3.2GB peak ✅ |
| Cost | $0 (free tier) | $0 ✅ |

### Optimization Opportunities

1. **Parallel Execution**: Run multiple years in parallel (future)
   ```bash
   # Current: Sequential (year by year)
   # Future: Parallel (5 years at once)
   # Expected: 5x speedup (~4 minutes total for 10 years)
   ```

2. **Column Pruning**: Already optimized (11 columns vs 23 full schema)
   - Current: 97% cost savings
   - No further optimization available

3. **PyArrow Zero-Copy**: Already implemented (no Parquet intermediate)
   - Current: Direct BigQuery → ClickHouse transfer
   - No further optimization available

## Related Documentation

- [SKILL.md](../SKILL.md) - Historical backfill workflows
- [Backfill Patterns](./backfill-patterns.md) - 1-year chunking rationale
- [Gap Monitor README](/deployment/gcp-functions/gap-monitor/README.md) - Automated gap detection (Cloud Functions)
