# ClickHouse Gap Detection Monitor - GCP Cloud Functions

Serverless monitoring for ClickHouse Ethereum database gaps and staleness.

> **Historical Note**: GCP resources retain legacy "motherduck" names from the pre-ClickHouse migration (2025-11-25). These include: `motherduck-gap-detector` (Cloud Function), `motherduck-monitor-sa` (Service Account), `motherduck-monitor-trigger` (Cloud Scheduler). Renaming GCP resources requires recreation with associated downtime risk. See [Migration ADR](/docs/architecture/decisions/2025-11-25-motherduck-clickhouse-migration.md) for details.

## Architecture

- **Platform**: GCP Cloud Functions gen2 (Python 3.12)
- **Trigger**: Cloud Scheduler HTTP (every 3 hours)
- **Secrets**: GCP Secret Manager (clickhouse-host, clickhouse-password, pushover-token, pushover-user)
- **Logging**: Cloud Logging (stdout/stderr auto-captured)
- **Notifications**: Pushover (priority=2, all executions) + Healthchecks.io Dead Man's Switch
- **Cost**: $0/month (240 invocations << 2M free tier)

## Deployment

### Prerequisites

```bash
# Authenticate
gcloud auth login
gcloud config set project eonlabs-ethereum-bq

# Store secrets (if not already done)
doppler secrets get PUSHOVER_TOKEN --plain | gcloud secrets create pushover-token --data-file=-
doppler secrets get PUSHOVER_USER --plain | gcloud secrets create pushover-user --data-file=-
```

### Deploy Function

```bash
cd deployment/gcp-functions/gap-monitor

gcloud functions deploy motherduck-gap-detector \
  --gen2 \
  --runtime=python312 \
  --region=us-east1 \
  --source=. \
  --entry-point=monitor \
  --trigger-http \
  --no-allow-unauthenticated \
  --service-account=motherduck-monitor-sa@eonlabs-ethereum-bq.iam.gserviceaccount.com \
  --set-env-vars="HEALTHCHECKS_PING_URL=$(doppler secrets get HEALTHCHECKS_PING_URL --plain)" \
  --set-secrets="CLICKHOUSE_HOST=clickhouse-host:latest,CLICKHOUSE_PASSWORD=clickhouse-password:latest,PUSHOVER_TOKEN=pushover-token:latest,PUSHOVER_USER=pushover-user:latest" \
  --max-instances=1 \
  --timeout=540s \
  --memory=512MB
```

### Create Scheduler

```bash
# Get function URL
FUNCTION_URL=$(gcloud functions describe motherduck-gap-detector --region=us-east1 --gen2 --format='value(serviceConfig.uri)')

# Create scheduler (every 3 hours)
gcloud scheduler jobs create http motherduck-monitor-trigger \
  --location=us-east1 \
  --schedule="0 */3 * * *" \
  --uri="$FUNCTION_URL" \
  --http-method=POST \
  --oidc-service-account-email=motherduck-monitor-sa@eonlabs-ethereum-bq.iam.gserviceaccount.com \
  --time-zone="America/New_York"
```

## Testing

```bash
# Manual trigger
gcloud scheduler jobs run motherduck-monitor-trigger --location=us-east1

# View logs
gcloud functions logs read motherduck-gap-detector --region=us-east1 --gen2 --limit=50
```

## Validation

✅ Cloud Function executes successfully (200 response)
✅ Pushover emergency notification received (ULID present)
✅ Healthchecks.io pinged successfully
✅ Cloud Logging shows gap detection query results

## SLOs

**Availability**: 99% success rate (≤7 failures/month)
**Correctness**: Exception-only failures, no silent errors
**Observability**: Cloud Logging + Pushover + Healthchecks.io
**Maintainability**: <30 minutes for common operations

## Monitoring

- **Cloud Logging**: https://console.cloud.google.com/logs (search: `resource.type="cloud_function" resource.labels.function_name="motherduck-gap-detector"`)
- **Pushover**: Emergency notifications every 3 hours
- **Healthchecks.io**: Dead Man's Switch (3-hour check-in)
