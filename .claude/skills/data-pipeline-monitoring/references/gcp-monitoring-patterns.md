# GCP Data Pipeline Monitoring Patterns

Reference guide for monitoring GCP-based data collection pipelines.

## Cloud Run Jobs

### View Execution History

```bash
gcloud run jobs executions list \
  --job JOB_NAME \
  --region REGION \
  --project PROJECT_ID \
  [--limit N]
```

**Output**: List of executions with status, start time, duration

### View Job Configuration

```bash
gcloud run jobs describe JOB_NAME \
  --region REGION \
  --project PROJECT_ID \
  --format yaml
```

### Manually Trigger Execution

```bash
gcloud run jobs execute JOB_NAME \
  --region REGION \
  --project PROJECT_ID
```

### View Logs

**Cloud Logging query**:
```bash
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME" \
  --limit 50 \
  --project PROJECT_ID \
  --format "value(timestamp,severity,textPayload)"
```

**Filter by severity**:
```bash
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME AND severity>=ERROR" \
  --limit 50 \
  --project PROJECT_ID
```

**Filter by time range**:
```bash
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=JOB_NAME" \
  --limit 50 \
  --project PROJECT_ID \
  --freshness="1h"
```

### Get Latest Execution Status

```bash
gcloud run jobs executions list \
  --job JOB_NAME \
  --region REGION \
  --project PROJECT_ID \
  --limit 1 \
  --format "value(metadata.name,status.conditions[0].type)"
```

**Status values**:
- `Completed` - Success
- `Failed` - Execution failed
- `Running` - Currently executing
- `Pending` - Waiting to start

## VM Systemd Services

### Check Service Status

```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo systemctl status SERVICE_NAME'
```

### Check if Service is Active

```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo systemctl is-active SERVICE_NAME'
```

**Returns**: `active`, `inactive`, `failed`, `unknown`

### View Service Logs

**Last N lines**:
```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo journalctl -u SERVICE_NAME -n 100'
```

**Follow logs (real-time)**:
```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo journalctl -u SERVICE_NAME -f'
```

**Filter by time**:
```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo journalctl -u SERVICE_NAME --since "1 hour ago"'
```

**Filter by severity**:
```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo journalctl -u SERVICE_NAME -p err'
```

**Priorities**: `emerg`, `alert`, `crit`, `err`, `warning`, `notice`, `info`, `debug`

### Restart Service

```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo systemctl restart SERVICE_NAME'
```

### Stop Service

```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo systemctl stop SERVICE_NAME'
```

### Enable Service (Auto-start on Boot)

```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo systemctl enable SERVICE_NAME'
```

### View Service Configuration

```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo systemctl cat SERVICE_NAME'
```

## VM Instance Management

### Check VM Status

```bash
gcloud compute instances describe VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --format "value(status)"
```

**Status values**: `RUNNING`, `TERMINATED`, `STOPPING`, `PROVISIONING`, `STAGING`, `SUSPENDED`

### Get VM External IP

```bash
gcloud compute instances describe VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --format "value(networkInterfaces[0].accessConfigs[0].natIP)"
```

### SSH into VM

```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID
```

### Execute Single Command on VM

```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command="COMMAND_HERE"
```

### Copy File to VM

```bash
gcloud compute scp LOCAL_FILE VM_NAME:REMOTE_PATH \
  --zone ZONE \
  --project PROJECT_ID
```

### Copy File from VM

```bash
gcloud compute scp VM_NAME:REMOTE_PATH LOCAL_FILE \
  --zone ZONE \
  --project PROJECT_ID
```

## Process Monitoring on VM

### Check if Process is Running

```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='ps aux | grep PROCESS_NAME | grep -v grep'
```

### View Process Resource Usage

```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='top -b -n 1 | grep PROCESS_NAME'
```

### Kill Process

```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='pkill -f PROCESS_NAME'
```

## File Monitoring on VM

### Tail Log File

```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='tail -f /path/to/logfile.log'
```

### View Last N Lines

```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='tail -n 100 /path/to/logfile.log'
```

### Search Log File

```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='grep "PATTERN" /path/to/logfile.log'
```

### Count Lines/Errors

```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='grep -c "ERROR" /path/to/logfile.log'
```

## Cloud Scheduler

### List Scheduled Jobs

```bash
gcloud scheduler jobs list \
  --location REGION \
  --project PROJECT_ID
```

### View Job Configuration

```bash
gcloud scheduler jobs describe JOB_NAME \
  --location REGION \
  --project PROJECT_ID
```

### Manually Trigger Scheduled Job

```bash
gcloud scheduler jobs run JOB_NAME \
  --location REGION \
  --project PROJECT_ID
```

### Pause Scheduled Job

```bash
gcloud scheduler jobs pause JOB_NAME \
  --location REGION \
  --project PROJECT_ID
```

### Resume Scheduled Job

```bash
gcloud scheduler jobs resume JOB_NAME \
  --location REGION \
  --project PROJECT_ID
```

## Secret Manager

### Verify Secret Exists

```bash
gcloud secrets describe SECRET_NAME \
  --project PROJECT_ID
```

### Test Secret Access

```bash
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='python3 -c "
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
name = \"projects/PROJECT_ID/secrets/SECRET_NAME/versions/latest\"
try:
    response = client.access_secret_version(request={\"name\": name})
    print(\"✅ Secret accessible\")
except Exception as e:
    print(f\"❌ Secret access failed: {e}\")
"'
```

### Grant Secret Access to Service Account

```bash
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/secretmanager.secretAccessor" \
  --project PROJECT_ID
```

## Monitoring Patterns for Dual Pipelines

### Pattern 1: Health Check Both Pipelines

```bash
# Check batch pipeline (Cloud Run Job)
echo "=== Batch Pipeline ==="
gcloud run jobs executions list \
  --job BATCH_JOB_NAME \
  --region REGION \
  --project PROJECT_ID \
  --limit 1 \
  --format "value(metadata.name,status.conditions[0].type)"

# Check real-time pipeline (VM systemd service)
echo "=== Real-Time Pipeline ==="
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo systemctl is-active REALTIME_SERVICE_NAME'
```

### Pattern 2: View Logs from Both Pipelines

```bash
# Batch pipeline logs
echo "=== Batch Pipeline Logs (last 10 entries) ==="
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=BATCH_JOB_NAME" \
  --limit 10 \
  --project PROJECT_ID \
  --format "value(timestamp,textPayload)"

echo ""
echo "=== Real-Time Pipeline Logs (last 10 entries) ==="
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo journalctl -u REALTIME_SERVICE_NAME -n 10 --no-pager'
```

### Pattern 3: Monitor Progress of Long-Running Operation

```bash
# Start background task and monitor
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='
    cd ~/workdir
    nohup python3 long_running_script.py > progress.log 2>&1 &
    echo "Started with PID: $!"
  '

# Check progress (repeat as needed)
gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='tail -50 ~/workdir/progress.log'
```

### Pattern 4: Quick Status Check

```bash
#!/bin/bash
# quick_status.sh - One-liner status for all pipelines

echo "Pipeline Status Check - $(date)"
echo "======================================"

# Batch pipeline
BATCH_STATUS=$(gcloud run jobs executions list \
  --job BATCH_JOB_NAME \
  --region REGION \
  --project PROJECT_ID \
  --limit 1 \
  --format "value(status.conditions[0].type)" 2>/dev/null)
echo "Batch Pipeline: ${BATCH_STATUS:-UNKNOWN}"

# Real-time pipeline
RT_STATUS=$(gcloud compute ssh VM_NAME \
  --zone ZONE \
  --project PROJECT_ID \
  --command='sudo systemctl is-active REALTIME_SERVICE_NAME' 2>/dev/null)
echo "Real-Time Pipeline: ${RT_STATUS:-UNKNOWN}"
```
