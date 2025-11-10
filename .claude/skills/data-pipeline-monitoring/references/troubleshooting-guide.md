# Data Pipeline Troubleshooting Guide

Common failure modes and recovery procedures for dual-pipeline data collection systems.

## Cloud Run Job Failures

### Symptom: Execution Status Shows "Failed"

**Check execution logs**:
```bash
# Get latest execution name
EXECUTION=$(gcloud run jobs executions list \
  --job JOB_NAME \
  --region REGION \
  --project PROJECT_ID \
  --limit 1 \
  --format "value(metadata.name)")

# View logs for that execution
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.execution_name=$EXECUTION" \
  --limit 100 \
  --project PROJECT_ID \
  --format "value(timestamp,severity,textPayload)"
```

**Common causes**:
1. **Timeout** - Job exceeded max execution time
   - Check logs for "deadline exceeded" or "timeout"
   - Solution: Increase timeout in job configuration or optimize code

2. **Memory limit** - Out of memory error
   - Check logs for "OOMKilled" or "memory limit exceeded"
   - Solution: Increase memory limit in job configuration

3. **API access denied** - Missing permissions
   - Check logs for "403" or "permission denied"
   - Solution: Grant required IAM roles to service account

4. **Secret Manager access** - Cannot fetch credentials
   - Check logs for "ENOENT" or "secret not found"
   - Solution: Verify secret exists and service account has secretAccessor role

**Recovery**:
```bash
# Manual retry
gcloud run jobs execute JOB_NAME \
  --region REGION \
  --project PROJECT_ID
```

## VM Systemd Service Failures

### Symptom: Service Status Shows "failed" or "inactive"

**Check service status**:
```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo systemctl status SERVICE_NAME --no-pager -l'
```

**View recent logs**:
```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo journalctl -u SERVICE_NAME -n 100 --no-pager'
```

**Common causes**:

1. **Crash loop** - Service crashes immediately after start
   - Check logs for Python tracebacks or segfaults
   - Look for "Main process exited, code=dumped"
   - Solution: Fix code bug, redeploy, restart service

2. **gRPC metadata validation errors** - Secrets with trailing newlines
   - Check logs for "INTERNAL:Illegal header value"
   - Solution: Ensure `.strip()` is applied to secrets fetched from Secret Manager

3. **WebSocket connection failure** - Cannot connect to data source
   - Check logs for "ConnectionRefused" or "timeout"
   - Solution: Verify network connectivity, API key validity

4. **Missing dependencies** - Python packages not installed
   - Check logs for "ModuleNotFoundError"
   - Solution: Install missing packages via pip

**Recovery**:
```bash
# Restart service
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo systemctl restart SERVICE_NAME'

# If restart fails, check logs again
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo journalctl -u SERVICE_NAME -n 50 --no-pager'
```

### Symptom: Service Running but Not Collecting Data

**Check if process is actually running**:
```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='ps aux | grep SCRIPT_NAME | grep -v grep'
```

**Check for errors in application logs**:
```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='tail -100 ~/workdir/app.log'
```

**Common causes**:
1. **Silent failures** - Errors caught but not logged
   - Solution: Add logging to exception handlers

2. **Rate limiting** - API rejecting requests
   - Check logs for "429" or "rate limit exceeded"
   - Solution: Implement exponential backoff, reduce request rate

3. **Database connection lost** - Cannot write to storage
   - Check logs for "connection refused" or "timeout"
   - Solution: Verify database credentials, network connectivity

## Secret Manager Issues

### Symptom: "Permission Denied" When Accessing Secrets

**Verify secret exists**:
```bash
gcloud secrets describe SECRET_NAME --project PROJECT_ID
```

**Check service account permissions**:
```bash
gcloud secrets get-iam-policy SECRET_NAME --project PROJECT_ID
```

**Expected output should include**:
```
bindings:
- members:
  - serviceAccount:SERVICE_ACCOUNT_EMAIL
  role: roles/secretmanager.secretAccessor
```

**Grant permissions if missing**:
```bash
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/secretmanager.secretAccessor" \
  --project PROJECT_ID
```

### Symptom: gRPC Metadata Validation Error

**Error message**:
```
E0000 filter_stack_call.cc:405] validate_metadata: INTERNAL:Illegal header value
F0000 call_op_set.h:981] Check failed: false
```

**Root cause**: Secrets stored via `gcloud secrets create` contain trailing newlines, causing gRPC metadata validation to fail.

**Solution**: Apply `.strip()` to secrets fetched from Secret Manager:

```python
def get_secret(secret_id: str, project_id: str) -> str:
    """Fetch secret from Google Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8').strip()  # ← .strip() is CRITICAL
```

**Verification**:
```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='python3 -c "
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
name = \"projects/PROJECT_ID/secrets/SECRET_NAME/versions/latest\"
response = client.access_secret_version(request={\"name\": name})
secret = response.payload.data.decode(\"UTF-8\")
print(f\"Secret length: {len(secret)}\")
print(f\"Secret repr: {repr(secret)}\")
print(f\"Has trailing newline: {secret.endswith(chr(10))}\")
"'
```

## Dual Pipeline Issues

### Symptom: Both Pipelines Down

**Impact**: Data gap (recoverable via historical backfill)

**Recovery priority**:
1. Restore real-time pipeline first (lower latency)
2. Restore batch pipeline second
3. Run historical backfill to fill gaps
4. Verify deduplication working correctly

**Verification after recovery**:
```bash
# Check both pipelines operational
echo "Batch Pipeline:"
gcloud run jobs executions list \
  --job BATCH_JOB_NAME \
  --region REGION \
  --project PROJECT_ID \
  --limit 1 \
  --format "value(status.conditions[0].type)"

echo "Real-Time Pipeline:"
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo systemctl is-active REALTIME_SERVICE_NAME'
```

### Symptom: Data Duplication

**Check for duplicate entries in database**:
```sql
SELECT number, COUNT(*) as count
FROM database.table
GROUP BY number
HAVING COUNT(*) > 1
LIMIT 10;
```

**Common causes**:
1. **Missing PRIMARY KEY constraint** - No deduplication enforcement
   - Solution: Add PRIMARY KEY constraint on unique identifier

2. **INSERT vs INSERT OR REPLACE** - Wrong SQL statement
   - Solution: Use `INSERT OR REPLACE` for idempotent upserts

3. **Race condition** - Both pipelines insert simultaneously
   - Solution: `INSERT OR REPLACE` handles this automatically

## Performance Issues

### Symptom: Slow Query Performance

**Check database size**:
```sql
SELECT COUNT(*) as total_rows FROM database.table;
```

**Check query execution time**:
```sql
EXPLAIN ANALYZE
SELECT * FROM database.table WHERE number > 10000000 LIMIT 100;
```

**Common solutions**:
1. **Add indexes** - On frequently queried columns
2. **Partition tables** - By date/time for time-series data
3. **Archive old data** - Move historical data to cold storage

### Symptom: High Memory Usage on VM

**Check memory usage**:
```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='free -h'
```

**Check process memory**:
```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='ps aux --sort=-%mem | head -10'
```

**Common solutions**:
1. **Memory leaks** - Upgrade VM to larger instance
2. **Batch processing** - Reduce batch size
3. **Connection pooling** - Reuse database connections

## Escalation Checklist

When troubleshooting fails, gather diagnostic information:

1. **Service logs** (last 100 lines from both pipelines)
2. **Error messages** (exact error text, timestamps)
3. **Service configuration** (environment variables, IAM roles)
4. **Recent changes** (code deploys, configuration updates)
5. **Timeline** (when did issue start, what changed)

**Diagnostic script**:
```bash
#!/bin/bash
# collect_diagnostics.sh

echo "=== Diagnostic Report $(date) ===" > diagnostics.txt
echo "" >> diagnostics.txt

echo "=== Batch Pipeline ===" >> diagnostics.txt
gcloud run jobs executions list \
  --job BATCH_JOB_NAME \
  --region REGION \
  --project PROJECT_ID \
  --limit 3 >> diagnostics.txt

echo "" >> diagnostics.txt
echo "=== Batch Pipeline Logs ===" >> diagnostics.txt
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=BATCH_JOB_NAME" \
  --limit 50 \
  --project PROJECT_ID >> diagnostics.txt

echo "" >> diagnostics.txt
echo "=== Real-Time Pipeline ===" >> diagnostics.txt
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo systemctl status REALTIME_SERVICE_NAME --no-pager' >> diagnostics.txt

echo "" >> diagnostics.txt
echo "=== Real-Time Pipeline Logs ===" >> diagnostics.txt
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo journalctl -u REALTIME_SERVICE_NAME -n 100 --no-pager' >> diagnostics.txt

echo "" >> diagnostics.txt
echo "Diagnostics saved to diagnostics.txt"
```
