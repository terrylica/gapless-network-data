---
status: deprecated
deprecated_date: 2025-11-25
reason: "Migrated to ClickHouse Cloud (MADR-0013)"
replacement: "See docs/decisions/0013-motherduck-clickhouse-migration.md"
---

# MotherDuck Dual Pipeline Architecture

> **DEPRECATED**: This document describes the former MotherDuck architecture. The system was migrated to ClickHouse Cloud on 2025-11-25. See [MADR-0013](../../decisions/0013-motherduck-clickhouse-migration.md) for the current architecture.

**Version**: 1.0.0
**Last Updated**: 2025-11-09
**Status**: DEPRECATED (superseded by ClickHouse Cloud)

## Overview

Dual-pipeline architecture for Ethereum blockchain data collection with automatic deduplication via MotherDuck.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Sources                              │
└─────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌──────────────────────┐        ┌──────────────────────┐
│ BigQuery Public      │        │ Alchemy WebSocket    │
│ Dataset              │        │ (eth_subscribe)      │
│                      │        │                      │
│ crypto_ethereum      │        │ wss://...alchemy.com │
│ .blocks              │        │                      │
└──────────────────────┘        └──────────────────────┘
          │                               │
          │ Hourly batch                  │ Real-time stream
          │ (~578 blocks)                 │ (~12s intervals)
          │                               │
          ▼                               ▼
┌──────────────────────┐        ┌──────────────────────┐
│ Cloud Run Job        │        │ e2-micro VM          │
│ eth-md-updater       │        │ eth-realtime-        │
│                      │        │ collector            │
│ main.py              │        │ realtime_collector.py│
└──────────────────────┘        └──────────────────────┘
          │                               │
          │ PyArrow Table                 │ WebSocket blocks
          │                               │
          └───────────────┬───────────────┘
                          │
                          │ INSERT OR REPLACE
                          │ (dedup by block number)
                          ▼
                ┌─────────────────────┐
                │ MotherDuck          │
                │                     │
                │ ethereum_mainnet    │
                │   .blocks           │
                │                     │
                │ PRIMARY KEY: number │
                └─────────────────────┘
```

## Pipeline Components

### Pipeline 1: BigQuery Hourly Batch

**Purpose**: Batch sync of historical and recent blocks

**Infrastructure**:

- Cloud Run Job: `eth-md-updater`
- Region: `us-east1`
- Schedule: Every hour (via Cloud Scheduler)
- Service account: `eth-md-job-sa@eonlabs-ethereum-bq.iam.gserviceaccount.com`

**Data Flow**:

1. Cloud Scheduler triggers job every hour at minute 0
2. Job queries BigQuery public dataset for blocks from last 2 hours
3. Results returned as PyArrow table (zero-copy)
4. PyArrow table loaded to MotherDuck via `INSERT OR REPLACE`

**Performance**:

- Query time: ~30s
- Transfer time: ~10s
- Insert time: ~10s
- Blocks per run: ~578 (2 hours × 289 blocks/hour average)

**Code**: `deployment/cloud-run/main.py`

### Pipeline 2: Alchemy Real-Time Stream

**Purpose**: Real-time block streaming for low latency

**Infrastructure**:

- VM: `eth-realtime-collector` (e2-micro, us-east1-b)
- Runtime: systemd service
- Service account: Default compute SA (`893624294905-compute@...`)

**Data Flow**:

1. WebSocket connection to Alchemy (`eth_subscribe` with `newHeads`)
2. Block notifications received every ~12 seconds (Ethereum block time)
3. Block parsed and inserted to MotherDuck via `INSERT OR REPLACE`

**Performance**:

- Latency: <1 second from block creation
- Collection rate: ~12 seconds per block
- Blocks per day: ~7,200

**Code**: `deployment/vm/realtime_collector.py`

## Deduplication Strategy

**Method**: `INSERT OR REPLACE` with PRIMARY KEY on block number

**Schema**:

```sql
CREATE TABLE ethereum_mainnet.blocks (
    timestamp TIMESTAMP NOT NULL,
    number BIGINT PRIMARY KEY,  -- ← Deduplication key
    gas_limit BIGINT,
    gas_used BIGINT,
    base_fee_per_gas BIGINT,
    transaction_count BIGINT,
    difficulty HUGEINT,
    total_difficulty HUGEINT,
    size BIGINT,
    blob_gas_used BIGINT,
    excess_blob_gas BIGINT
)
```

**Behavior**:

- When BigQuery pipeline inserts block N: upsert (replace if exists)
- When real-time collector inserts block N: upsert (replace if exists)
- Result: Always latest data, no duplicates

**Idempotency**: Both pipelines can safely re-run without creating duplicates

## Security

### Credential Management

All credentials stored in Google Cloud Secret Manager:

- `alchemy-api-key` - Alchemy WebSocket access
- `motherduck-token` - MotherDuck authentication

**IAM Permissions**:

- VM service account: `roles/secretmanager.secretAccessor`
- Cloud Run service account: `roles/secretmanager.secretAccessor`

### Secret Access Pattern

Both pipelines use identical secret fetching:

```python
def get_secret(secret_id: str, project_id: str = GCP_PROJECT) -> str:
    """Fetch secret from Google Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8').strip()  # .strip() is CRITICAL
```

**Important**: `.strip()` prevents gRPC metadata validation errors from trailing newlines

### No Hardcoded Secrets

- No secrets in environment variables
- No secrets in systemd service files
- No secrets in container images
- All credentials fetched at runtime from Secret Manager

## Cost Analysis

**BigQuery**:

- Query: ~10 MB per run (within free tier)
- Monthly cost: $0

**Cloud Run**:

- Executions: 720/month (hourly)
- Duration: ~50s per execution
- Monthly cost: $0 (within free tier)

**Compute Engine (e2-micro)**:

- VM: 1 instance, us-east1-b
- Monthly cost: $0 (within free tier)

**MotherDuck**:

- Storage: ~1.5 GB
- Queries: <10 GB/month
- Monthly cost: $0 (within free tier)

**Total**: $0/month (all within GCP and MotherDuck free tiers)

## Monitoring

### BigQuery Pipeline

View job execution history:

```bash
gcloud run jobs executions list \
  --job eth-md-updater \
  --region us-east1 \
  --project eonlabs-ethereum-bq
```

View logs:

```bash
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=eth-md-updater" \
  --limit 50 \
  --project eonlabs-ethereum-bq
```

### Real-Time Pipeline

View service status:

```bash
gcloud compute ssh eth-realtime-collector \
  --zone=us-east1-b \
  --project=eonlabs-ethereum-bq \
  --command='sudo systemctl status eth-collector'
```

View logs:

```bash
gcloud compute ssh eth-realtime-collector \
  --zone=us-east1-b \
  --project=eonlabs-ethereum-bq \
  --command='sudo journalctl -u eth-collector -f'
```

## Failure Modes and Recovery

### BigQuery Pipeline Failure

**Symptom**: Cloud Run Job execution fails

**Recovery**:

1. Check Cloud Run logs for error message
2. Verify BigQuery API access
3. Verify Secret Manager access
4. Manual retry: `gcloud run jobs execute eth-md-updater --region us-east1`

**Impact**: Minimal (real-time pipeline continues collecting)

### Real-Time Pipeline Failure

**Symptom**: systemd service crash-looping or stopped

**Recovery**:

1. Check systemd logs: `sudo journalctl -u eth-collector -n 100`
2. Verify Alchemy WebSocket connectivity
3. Verify Secret Manager access
4. Restart service: `sudo systemctl restart eth-collector`

**Impact**: Temporary gap (filled by hourly BigQuery sync)

### Both Pipelines Down

**Symptom**: No new blocks in MotherDuck

**Recovery**:

1. Restore real-time pipeline first (lower latency)
2. Run historical backfill to fill gaps
3. Verify deduplication working correctly

**Impact**: Data gap (recoverable via backfill)

## Performance Characteristics

| Metric      | BigQuery Pipeline    | Real-Time Pipeline |
| ----------- | -------------------- | ------------------ |
| Latency     | 30-60 minutes        | <1 second          |
| Throughput  | ~578 blocks/hour     | ~300 blocks/hour   |
| Reliability | High (Cloud Run SLA) | Medium (e2-micro)  |
| Cost        | $0 (free tier)       | $0 (free tier)     |
| Data source | Historical archive   | Live stream        |

## Design Rationale

### Why Dual Pipelines?

1. **Reliability**: Single pipeline failure doesn't stop data collection
2. **Latency**: Real-time pipeline provides <1s latency for recent blocks
3. **Completeness**: Batch pipeline ensures no gaps in historical data
4. **Cost**: Both pipelines fit within free tiers

### Why MotherDuck for Deduplication?

1. **Automatic**: `INSERT OR REPLACE` handles deduplication natively
2. **No coordination**: Pipelines don't need to communicate
3. **Idempotent**: Safe to re-run either pipeline
4. **Simple**: No custom merge logic required

### Alternative Considered: Single Pipeline

**Rejected**: Single pipeline requires complex gap detection and backfill logic. Dual pipeline with automatic deduplication is simpler and more reliable.

## Related Documentation

- [BigQuery Integration](bigquery-motherduck-integration.md)
- [ClickHouse Migration Decision](../../decisions/0013-motherduck-clickhouse-migration.md) - Current architecture
