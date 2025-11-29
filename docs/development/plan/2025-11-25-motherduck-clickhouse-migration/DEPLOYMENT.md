# ClickHouse Migration Deployment Guide

**ADR**: 0013 | **Plan**: `plan.md` | **Status**: Phase 2 Ready for Deployment

## Prerequisites

**Option A: gcloud CLI (local machine)**:

- [ ] gcloud CLI installed and authenticated (`gcloud auth login`)
- [ ] Doppler CLI configured with `aws-credentials/prd` project access
- [ ] SSH access to GCP VM (eth-realtime-collector)

**Option B: Cloud Console (web-based)**:

- [ ] Access to GCP Console (console.cloud.google.com)
- [ ] Access to Doppler dashboard (dashboard.doppler.com)
- [ ] Project: `eonlabs-ethereum-bq`

## GCP Secrets Status

**✅ COMPLETED** (2025-11-25): Secrets created via Python SDK (`scripts/clickhouse/setup_gcp_secrets.py`)

- `clickhouse-host`: ✅ Created
- `clickhouse-password`: ✅ Created

## Quick Deployment

```bash
# From repository root
cd

# Step 1: Setup GCP secrets
./scripts/clickhouse/setup_gcp_secrets.sh

# Step 2: Deploy VM collector
cd deployment/vm && ./deploy.sh

# Step 3: Deploy Cloud Run (see detailed commands below)

# Step 4: Deploy Cloud Function (see detailed commands below)
```

## Detailed Deployment Steps

### Step 1: Create ClickHouse Secrets in GCP Secret Manager

```bash
# Run the setup script (requires gcloud + doppler)
./scripts/clickhouse/setup_gcp_secrets.sh
```

Or manually:

```bash
# Get credentials from Doppler
CH_HOST=$(doppler secrets get CLICKHOUSE_HOST --project aws-credentials --config prd --plain)
CH_PASS=$(doppler secrets get CLICKHOUSE_PASSWORD --project aws-credentials --config prd --plain)

# Create secrets in GCP
gcloud secrets create clickhouse-host --project eonlabs-ethereum-bq --replication-policy=automatic
echo -n "$CH_HOST" | gcloud secrets versions add clickhouse-host --data-file=- --project eonlabs-ethereum-bq

gcloud secrets create clickhouse-password --project eonlabs-ethereum-bq --replication-policy=automatic
echo -n "$CH_PASS" | gcloud secrets versions add clickhouse-password --data-file=- --project eonlabs-ethereum-bq
```

### Step 2: Deploy VM Collector

```bash
cd deployment/vm
./deploy.sh
```

The deploy script will:

- Grant Secret Manager access to VM service account
- Copy updated realtime_collector.py to VM
- Install clickhouse-connect dependency
- Restart eth-collector systemd service

**Verify deployment:**

```bash
gcloud compute ssh eth-realtime-collector --zone=us-east1-b --project=eonlabs-ethereum-bq \
  --command="sudo journalctl -u eth-collector -n 50"
```

Look for:

- `✅ ClickHouse connected`
- `[BATCH] ✅ Flushed X blocks to ClickHouse`
- `[BATCH] ✅ Flushed X blocks to MotherDuck`

### Step 3: Deploy Cloud Run Job

Get ClickHouse credentials:

```bash
CH_HOST=$(doppler secrets get CLICKHOUSE_HOST --project aws-credentials --config prd --plain)
CH_PASS=$(doppler secrets get CLICKHOUSE_PASSWORD --project aws-credentials --config prd --plain)
```

Update Cloud Run Job:

```bash
gcloud run jobs update bigquery-motherduck-updater \
  --set-env-vars="CLICKHOUSE_HOST=$CH_HOST,CLICKHOUSE_PASSWORD=$CH_PASS,DUAL_WRITE_ENABLED=true" \
  --region=us-east1 \
  --project=eonlabs-ethereum-bq
```

**Or via Cloud Console:**

1. Go to Cloud Run Jobs
2. Select `bigquery-motherduck-updater`
3. Edit > Variables & Secrets
4. Add environment variables:
   - `CLICKHOUSE_HOST`: ebmf8f35lu.us-west-2.aws.clickhouse.cloud
   - `CLICKHOUSE_PASSWORD`: (from Doppler)
   - `DUAL_WRITE_ENABLED`: true

### Step 4: Deploy Cloud Function

```bash
cd deployment/gcp-functions/motherduck-monitor

# Get credentials
CH_HOST=$(doppler secrets get CLICKHOUSE_HOST --project aws-credentials --config prd --plain)
CH_PASS=$(doppler secrets get CLICKHOUSE_PASSWORD --project aws-credentials --config prd --plain)

gcloud functions deploy motherduck-monitor \
  --gen2 \
  --runtime=python312 \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars="CLICKHOUSE_HOST=$CH_HOST,CLICKHOUSE_PASSWORD=$CH_PASS,DUAL_VALIDATION_ENABLED=true" \
  --region=us-east1 \
  --project=eonlabs-ethereum-bq \
  --source=.
```

## Cloud Console Deployment (Alternative)

When gcloud CLI is unavailable, deploy via Cloud Console:

### VM Collector via Cloud Console

1. **Grant Secret Access**:
   - Go to: Secret Manager > clickhouse-host > Permissions
   - Add: `893624294905-compute@developer.gserviceaccount.com`
   - Role: `Secret Manager Secret Accessor`
   - Repeat for `clickhouse-password`

2. **Update Collector Script**:
   - Go to: Compute Engine > VM instances > eth-realtime-collector
   - Click SSH (opens browser terminal)
   - Upload `deployment/vm/realtime_collector.py` via SSH file upload
   - Run:
     ```bash
     pip3 install clickhouse-connect
     sudo mv ~/realtime_collector.py ~/eth-collector/
     sudo systemctl restart eth-collector
     sudo journalctl -u eth-collector -f
     ```

### Cloud Run Job via Cloud Console

1. **Navigate**: Cloud Run > Jobs > bigquery-motherduck-updater
2. **Edit & Deploy New Revision**:
   - Click "Edit & Deploy New Revision"
   - Go to "Variables & Secrets" tab
   - Add environment variables:
     - `CLICKHOUSE_HOST`: (from Doppler aws-credentials/prd)
     - `CLICKHOUSE_PASSWORD`: (from Doppler aws-credentials/prd)
     - `DUAL_WRITE_ENABLED`: `true`
   - Click "Deploy"

### Cloud Function via Cloud Console

1. **Navigate**: Cloud Functions > motherduck-monitor
2. **Edit Function**:
   - Click "Edit"
   - Go to "Runtime, build, connections and security settings"
   - Add environment variables:
     - `CLICKHOUSE_HOST`: (from Doppler)
     - `CLICKHOUSE_PASSWORD`: (from Doppler)
     - `DUAL_VALIDATION_ENABLED`: `true`
   - Click "Deploy"

### Get Credentials from Doppler

1. Go to: dashboard.doppler.com
2. Project: `aws-credentials` > Config: `prd`
3. Copy values for: `CLICKHOUSE_HOST`, `CLICKHOUSE_PASSWORD`

## Post-Deployment Verification

### 1. Verify Dual-Write (VM Collector)

```bash
# Check logs for dual-write success
gcloud compute ssh eth-realtime-collector --zone=us-east1-b --project=eonlabs-ethereum-bq \
  --command="sudo journalctl -u eth-collector -f"
```

Expected output:

```
[BATCH] ✅ Flushed 25 blocks to ClickHouse
[BATCH] ✅ Flushed 25 blocks to MotherDuck
```

### 2. Run Consistency Check

```bash
doppler run --project aws-credentials --config prd -- \
  uv run scripts/clickhouse/verify_consistency.py
```

Expected output:

```
✅ DATABASES IN SYNC
ClickHouse: 23,865,017 blocks
MotherDuck: 23,865,017 blocks
```

### 3. Verify ClickHouse Data Growth

```bash
doppler run --project aws-credentials --config prd -- python3 -c "
import clickhouse_connect, os
client = clickhouse_connect.get_client(
    host=os.environ['CLICKHOUSE_HOST'],
    port=8443, username='default',
    password=os.environ['CLICKHOUSE_PASSWORD'],
    secure=True
)
result = client.query('SELECT MAX(number), MAX(timestamp) FROM ethereum_mainnet.blocks')
print(f'Latest block: {result.result_rows[0][0]:,}')
print(f'Latest time: {result.result_rows[0][1]}')
"
```

## Rollback Procedure

If issues detected during validation:

### Disable Dual-Write (Keep MotherDuck Only)

**VM Collector:**

```bash
gcloud compute ssh eth-realtime-collector --zone=us-east1-b --project=eonlabs-ethereum-bq \
  --command="sudo systemctl stop eth-collector"

# Edit service to add: Environment="DUAL_WRITE_ENABLED=false"
# Then restart
gcloud compute ssh eth-realtime-collector --zone=us-east1-b --project=eonlabs-ethereum-bq \
  --command="sudo systemctl start eth-collector"
```

**Cloud Run:**

```bash
gcloud run jobs update bigquery-motherduck-updater \
  --set-env-vars="DUAL_WRITE_ENABLED=false" \
  --region=us-east1 --project=eonlabs-ethereum-bq
```

## Phase 3: Validation Schedule

Run consistency check every hour for 6-12 hours:

```bash
# Set up cron job or run manually
while true; do
  doppler run --project aws-credentials --config prd -- \
    uv run scripts/clickhouse/verify_consistency.py
  echo "Next check in 1 hour..."
  sleep 3600
done
```

## Phase 4: Cutover Checklist

After successful validation period:

- [ ] Verify 6+ consecutive hourly consistency checks passed
- [ ] Verify no Pushover alerts during validation
- [ ] Update SDK to read from ClickHouse (PRIMARY_DATABASE=clickhouse)
- [ ] Remove dual-write code (ClickHouse-only)
- [ ] Archive MotherDuck snapshot to GCS
- [ ] Update CLAUDE.md documentation
