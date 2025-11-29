# Plan: Enable Healthchecks.io for Gap Detector

**Status**: Completed
**Created**: 2025-11-26
**Related ADR**: [Healthchecks Gap Detector Enable](/docs/architecture/decisions/2025-11-28-healthchecks-gap-detector-enable.md)

## (a) Context

### Problem Statement

The gap detector Cloud Function has Healthchecks.io code fully implemented but **DISABLED** because the `HEALTHCHECKS_PING_URL` environment variable was never set during deployment.

**Current Code Path** (`deployment/gcp-functions/motherduck-monitor/main.py:457-460`):

```python
if HEALTHCHECKS_PING_URL:
    ping_healthchecks(HEALTHCHECKS_PING_URL, diagnostic_data, is_healthy)
else:
    print("  Healthchecks.io not configured (skipping)")  # <-- Currently hitting this
```

### Current Monitoring Inventory (post-cleanup)

| Check Name                                            | UUID           | Period | Grace | Status |
| ----------------------------------------------------- | -------------- | ------ | ----- | ------ |
| VM Systemd \| Alchemy → ClickHouse \| Real-Time (12s) | `d73a71f2-...` | 5min   | 5min  | ACTIVE |
| Cloud Run Job \| BigQuery → ClickHouse \| Hourly      | `616d5e4b-...` | 1h     | 15min | ACTIVE |
| clickhouse-gap-detector                               | `1a74805b-...` | 3h     | 15min | ACTIVE |

### Infrastructure

- **Cloud Function**: `motherduck-gap-detector` (Gen2, Python 3.12, us-east1)
- **Scheduler**: Cloud Scheduler trigger every 3 hours
- **Code**: Healthchecks.io integration fully implemented (just needs env var)

## (b) Plan

### Objective

Enable Healthchecks.io Dead Man's Switch monitoring for the gap detector to achieve parity with VM and Cloud Run monitors.

### Strategy

Configuration-only fix: Create Healthchecks.io check, update Cloud Function env var, verify.

### Semantic Constants

| Constant                     | Value | Rationale                        |
| ---------------------------- | ----- | -------------------------------- |
| `GAP_DETECTOR_PERIOD_HOURS`  | 3     | Matches Cloud Scheduler interval |
| `GAP_DETECTOR_GRACE_MINUTES` | 15    | Allows for execution time        |

### Implementation

#### Phase 1: Create Healthchecks.io Check

Create check at healthchecks.io dashboard:

- **Name**: `clickhouse-gap-detector`
- **Period**: 3 hours
- **Grace**: 15 minutes
- **Tags**: `ethereum`, `clickhouse`, `gap-detector`

#### Phase 2: Update Cloud Function

```bash
gcloud functions deploy motherduck-gap-detector \
  --gen2 --region=us-east1 \
  --project=eonlabs-ethereum-bq \
  --update-env-vars="HEALTHCHECKS_PING_URL=https://hc-ping.com/<UUID>"
```

#### Phase 3: Verify Integration

```bash
# Manual trigger
gcloud scheduler jobs run clickhouse-monitor-trigger \
  --location=us-east1 --project=eonlabs-ethereum-bq

# Check logs
gcloud functions logs read motherduck-gap-detector \
  --region=us-east1 --project=eonlabs-ethereum-bq --limit=50
```

**Expected**: Logs show "Pinged Healthchecks.io" instead of "Healthchecks.io not configured (skipping)"

## (c) Task List

### Phase 1: Create Healthchecks.io Check - COMPLETED

- [x] **1.1** Create check at healthchecks.io with 3h period, 15min grace
- [x] **1.2** Note UUID for environment variable: `1a74805b-5315-4808-91d2-1b8b248422b6`

### Phase 2: Update Cloud Function - COMPLETED

- [x] **2.1** Update `HEALTHCHECKS_PING_URL` env var via gcloud (revision 00019-siq)
- [x] **2.2** Verify deployment succeeds

### Phase 3: Verify Integration - COMPLETED

- [x] **3.1** Manual trigger via Cloud Scheduler (execution: aZJ2F8aWqvKn)
- [x] **3.2** Check logs show "Pinged Healthchecks.io"
- [x] **3.3** Confirm Healthchecks.io dashboard shows green (status: up)
- [x] **3.4** Update ADR status to Accepted

## Success Criteria

1. Cloud Function logs show "Pinged Healthchecks.io" (not "skipping")
2. Healthchecks.io dashboard shows green status after manual trigger
3. `/fail` endpoint receives pings when gaps detected

## Critical Files

- `deployment/gcp-functions/motherduck-monitor/main.py` (no changes - code complete)
- `/docs/architecture/decisions/2025-11-28-healthchecks-gap-detector-enable.md` (ADR)

## Notes

- No code changes required - purely deployment configuration
- Hardcoded UUIDs in VM/Cloud Run kept as-is (working pattern)
