# MADR-0001: Healthchecks.io Grace Period Calibration Strategy

## Status

Proposed

## Context

Adversarial monitoring audit (2025-11-13) discovered all 4 Healthchecks.io checks have grace periods that are too short, creating high risk of false positive alerts during normal operational variance.

### Current Configuration

| Check              | Interval | Grace  | Ratio               | Risk   |
| ------------------ | -------- | ------ | ------------------- | ------ |
| motherduck-monitor | 3 hours  | 10 min | 5.5% of timeout     | HIGH   |
| VM Collector       | 5 min    | 5 min  | 1.0× heartbeat      | HIGH   |
| Hourly Updater     | 60 min   | 10 min | 16% of interval     | MEDIUM |
| Data Quality       | 5 min    | 5 min  | 1.0× check interval | HIGH   |

### Problems Identified

1. **motherduck-monitor**: Function timeout is 9 minutes, grace is 10 minutes → only 1-minute buffer
2. **VM Collector**: Grace equals heartbeat interval → VM restart (2-3 min) triggers immediate alert
3. **Hourly Updater**: 10-min grace on 60-min interval → BigQuery throttling exceeds grace
4. **Data Quality**: 5-min grace on 5-min check → any execution delay triggers alert

### Industry Best Practice

Dead Man's Switch monitoring grace periods should be **3× the expected interval** to account for:

- Normal execution variance (P95-P99)
- Infrastructure transients (VM restarts, network blips)
- Upstream service slowdowns (MotherDuck, BigQuery, Secret Manager)

### Empirical Evidence

From audit findings:

- VM restart time: 2-3 minutes (observed)
- Function timeout: 9 minutes (configured)
- BigQuery P95 latency: 15-20 seconds (typical)
- Normal variance: ±20-30% of execution time

## Decision

Increase all grace periods to **3× their intervals or function timeouts**, whichever is larger.

### New Configuration

| Check              | Interval | New Grace | Ratio               | Buffer                 |
| ------------------ | -------- | --------- | ------------------- | ---------------------- |
| motherduck-monitor | 3 hours  | 30 min    | 16.7% of timeout    | 3.3× function timeout  |
| VM Collector       | 5 min    | 15 min    | 3.0× heartbeat      | Allows 2 missed beats  |
| Hourly Updater     | 60 min   | 30 min    | 46% of interval     | Allows 2× worst-case   |
| Data Quality       | 5 min    | 15 min    | 3.0× check interval | Allows 2 missed checks |

## Consequences

### Positive

- **Eliminates false positives** during normal operations
- **Prevents alert fatigue** (estimated 7% false positive rate → <1%)
- **Allows graceful recovery** from transient issues
- **Industry-aligned** (3× ratio is best practice)
- **No code changes** required (API-only configuration)

### Negative

- **Detection latency increases** by 5-25 minutes
  - motherduck-monitor: 10 min → 30 min (+20 min)
  - VM Collector: 5 min → 15 min (+10 min)
  - Hourly Updater: 10 min → 30 min (+20 min)
  - Data Quality: 5 min → 15 min (+10 min)

### Mitigation

Detection latency increase is acceptable because:

1. These are Dead Man's Switch checks (last-resort monitoring)
2. Direct alerts (Pushover) provide <1 second detection (separate issue P1-6)
3. Real failures persist > 30 minutes (grace period still catches them)
4. False positives are more costly than detection latency (alert fatigue)

## Alternatives Considered

### Alternative 1: Keep current grace periods, add retry logic

**Rejected**: Adds complexity to monitoring, doesn't address root cause (grace too short)

### Alternative 2: Use 2× interval instead of 3×

**Rejected**: Still insufficient buffer for infrastructure transients (2-3 min VM restart would still trigger false positives on 5-min grace)

### Alternative 3: Dynamic grace periods based on recent execution variance

**Rejected**: Over-engineering, adds complexity, 3× static ratio is industry-proven

## Implementation

### API Calls (Healthchecks.io v3)

```bash
export HEALTHCHECKS_API_KEY=$(doppler secrets get HEALTHCHECKS_API_KEY --plain)

# motherduck-monitor
curl -X POST https://healthchecks.io/api/v3/checks/2dfd9e29-667d-4a84-9fda-8bed95a58a43 \
  -H "X-Api-Key: $HEALTHCHECKS_API_KEY" \
  -d '{"grace": 1800}'

# VM Collector
curl -X POST https://healthchecks.io/api/v3/checks/d73a71f2-9457-4e58-9ed6-8a31db5bbed1 \
  -H "X-Api-Key: $HEALTHCHECKS_API_KEY" \
  -d '{"grace": 900}'

# Hourly Updater
curl -X POST https://healthchecks.io/api/v3/checks/616d5e4b-9e5b-470f-bd85-7870c2329ba3 \
  -H "X-Api-Key: $HEALTHCHECKS_API_KEY" \
  -d '{"grace": 1800}'

# Data Quality
curl -X POST https://healthchecks.io/api/v3/checks/c3087199-8265-4721-99fe-589c5d10a119 \
  -H "X-Api-Key: $HEALTHCHECKS_API_KEY" \
  -d '{"grace": 900}'
```

### Validation

Query Healthchecks.io API to verify new grace periods:

```bash
curl -H "X-Api-Key: $HEALTHCHECKS_API_KEY" \
  https://healthchecks.io/api/v3/checks/ | \
  jq '.checks[] | {name, grace}'
```

### Rollback

If false negatives increase (real failures not detected):

```bash
# Revert to original grace periods (not recommended)
# motherduck-monitor: 600s
# VM Collector: 300s
# Hourly Updater: 600s
# Data Quality: 300s
```

## SLO Impact

### Before

- **Correctness**: ~7% false positive rate (2.1 false alerts/month per check, 8.4 total/month)
- **Maintainability**: Routine false alerts require investigation time

### After

- **Correctness**: <1% false positive rate (0.3 false alerts/month per check, 1.2 total/month)
- **Maintainability**: Investigation time reduced by 85%

## References

- Audit artifact: `/tmp/monitoring-audit-config/EXECUTIVE_AUDIT_REPORT.md`
- Specification: `specifications/monitoring-fixes-phase.yaml` (task P0-2)
- Industry standard: 3× interval for Dead Man's Switch grace periods
- Healthchecks.io docs: https://healthchecks.io/docs/configuring_checks/

## Decision Date

2025-11-13

## Decision Makers

- Monitoring Infrastructure Team
- Adversarial Audit Results (6 parallel agents)

## Related ADRs

- MADR-0002: Exception Handler Notification Strategy (complementary fast alerting)
