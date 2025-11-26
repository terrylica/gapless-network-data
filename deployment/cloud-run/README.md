# Cloud Run Job: BigQuery → ClickHouse Hourly Sync

Cloud Run Job that syncs latest Ethereum blocks from BigQuery to ClickHouse on an hourly schedule.

## Files

- `main.py` - Python script that fetches blocks from BigQuery and loads to ClickHouse
- `Dockerfile` - Container image definition
- `requirements.txt` - Python dependencies

## Prerequisites

1. GCP project configured: `eonlabs-ethereum-bq`
2. Cloud Run Job created: `eth-md-updater`
3. Secrets stored in Secret Manager:
   - `clickhouse-host`
   - `clickhouse-password`
4. Cloud Run service account has permissions:
   - `roles/secretmanager.secretAccessor`
   - `roles/bigquery.user`
   - Service account: `eth-md-job-sa@eonlabs-ethereum-bq.iam.gserviceaccount.com`

## Deployment

Build and push container:

```bash
cd deployment/cloud-run

gcloud builds submit \
  --tag gcr.io/eonlabs-ethereum-bq/eth-md-updater \
  --project eonlabs-ethereum-bq
```

Update Cloud Run Job:

```bash
gcloud run jobs update eth-md-updater \
  --image gcr.io/eonlabs-ethereum-bq/eth-md-updater \
  --region us-central1 \
  --project eonlabs-ethereum-bq
```

## Manual Execution

Run the job manually:

```bash
gcloud run jobs execute eth-md-updater \
  --region us-central1 \
  --project eonlabs-ethereum-bq
```

## Configuration

Environment variables (set on Cloud Run Job):

- `GCP_PROJECT`: `eonlabs-ethereum-bq`
- `LOOKBACK_HOURS`: `2` (default, fetch blocks from last 2 hours)
- `CLICKHOUSE_HOST`: ClickHouse Cloud hostname
- `CLICKHOUSE_PASSWORD`: ClickHouse password (from Secret Manager)

## Data Flow

```
BigQuery (crypto_ethereum.blocks) → PyArrow → ClickHouse (ethereum_mainnet.blocks)
```

**Collection rate**: ~578 blocks per run (every hour)

**Deduplication**: Uses ReplacingMergeTree engine with block number as sort key

## Schedule

Cloud Scheduler runs this job every hour at minute 0:

```
0 * * * *
```

## Monitoring

View job execution history:

```bash
gcloud run jobs executions list \
  --job eth-md-updater \
  --region us-central1 \
  --project eonlabs-ethereum-bq
```

View logs for latest execution:

```bash
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=eth-md-updater" \
  --limit 50 \
  --project eonlabs-ethereum-bq \
  --format json
```

## Security

- No secrets in container image or environment variables
- All credentials fetched from Secret Manager at runtime
- Container runs as non-root user (uid 1000)
- `.strip()` applied to secrets to prevent gRPC metadata validation errors

---

## Data Quality Monitoring

Separate Cloud Run Job (`eth-md-data-quality-checker`) monitors data freshness.

### Configuration

- **Schedule**: Every 5 minutes via Cloud Scheduler (`eth-md-data-quality`)
- **Staleness Threshold**: 960 seconds (16 minutes) to accommodate batch mode
- **Script**: `data_quality_checker.py`
- **Dockerfile**: `Dockerfile.data-quality`

### Environment Variables

- `STALE_THRESHOLD_SECONDS`: `960` (default, 16 minutes)
- `GCP_PROJECT`: `eonlabs-ethereum-bq`
- `CLICKHOUSE_HOST`: ClickHouse Cloud hostname
- `CLICKHOUSE_PASSWORD`: ClickHouse password (from Secret Manager)

### Manual Execution

Run the data quality check manually:

```bash
gcloud run jobs execute eth-md-data-quality-checker \
  --region us-central1 \
  --project eonlabs-ethereum-bq
```

View execution history:

```bash
gcloud run jobs executions list \
  --job eth-md-data-quality-checker \
  --region us-central1 \
  --project eonlabs-ethereum-bq
```

### Monitoring

Healthchecks.io check: **Data Quality | ClickHouse Growing & Gapless**

- Receives ping on success (data fresh)
- Receives `/fail` ping if data stale (>960s)
- Grace period: 10 minutes
