# Enable Healthchecks.io for Gap Detector

## Status

Accepted

## Date

2025-11-28

## Context

The gap detector Cloud Function (`motherduck-gap-detector`) has Healthchecks.io Dead Man's Switch code fully implemented but **DISABLED** because the `HEALTHCHECKS_PING_URL` environment variable was never set during deployment.

**Current State** (from `deployment/gcp-functions/motherduck-monitor/main.py:457-460`):

```python
if HEALTHCHECKS_PING_URL:
    ping_healthchecks(HEALTHCHECKS_PING_URL, diagnostic_data, is_healthy)
else:
    print("  Healthchecks.io not configured (skipping)")  # <-- Currently hitting this
```

**Monitoring Inventory** (post-cleanup):

| Check Name                                            | UUID           | Period | Grace | Status |
| ----------------------------------------------------- | -------------- | ------ | ----- | ------ |
| VM Systemd \| Alchemy → ClickHouse \| Real-Time (12s) | `d73a71f2-...` | 5min   | 5min  | ACTIVE |
| Cloud Run Job \| BigQuery → ClickHouse \| Hourly      | `616d5e4b-...` | 1h     | 15min | ACTIVE |
| clickhouse-gap-detector                               | `1a74805b-...` | 3h     | 15min | ACTIVE |

**Impact**: Gap detector executes successfully but lacks Dead Man's Switch monitoring. If the Cloud Scheduler fails or the function stops being invoked, there is no alert mechanism.

## Decision

Enable Healthchecks.io monitoring for the gap detector by:

1. Creating a new Healthchecks.io check with appropriate period/grace
2. Setting the `HEALTHCHECKS_PING_URL` environment variable on the Cloud Function

### Semantic Constants

| Constant                     | Value | Rationale                                |
| ---------------------------- | ----- | ---------------------------------------- |
| `GAP_DETECTOR_PERIOD_HOURS`  | 3     | Matches Cloud Scheduler interval         |
| `GAP_DETECTOR_GRACE_MINUTES` | 15    | Allows for execution time + minor delays |

## Consequences

### Positive

- Complete monitoring parity with VM and Cloud Run components
- Dead Man's Switch alerts if gap detector stops running
- `/fail` endpoint receives pings when gaps detected (existing code)

### Negative

- None (code already implemented, only config needed)

### SLO Impact

| SLO           | Before                     | After                        |
| ------------- | -------------------------- | ---------------------------- |
| Availability  | Pushover-only alerts       | Dead Man's Switch + Pushover |
| Observability | Execution-time alerts only | Full lifecycle monitoring    |

## Alternatives Considered

### 1. Store UUID in Secret Manager

**Deferred**: VM and Cloud Run use hardcoded UUIDs successfully. Consistency favored over abstraction for non-sensitive data.

### 2. Add /start Signals

**Deferred**: Adds complexity without proportional benefit. Keep it simple (KISS).

## Validation

1. Manual trigger via Cloud Scheduler
2. Verify logs show "Pinged Healthchecks.io" (not "skipping")
3. Confirm Healthchecks.io dashboard shows green status

## Related

- [Gap Detector ClickHouse Fix](/docs/architecture/decisions/2025-11-26-gap-detector-clickhouse-fix.md)
- [Healthchecks Grace Period Calibration](/docs/architecture/decisions/2025-11-13-healthchecks-grace-period-calibration.md)
- [Implementation Plan](/docs/development/plan/2025-11-28-healthchecks-gap-detector-enable/plan.md)
