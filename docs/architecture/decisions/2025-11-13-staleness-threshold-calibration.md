# Staleness Threshold Empirical Calibration

## Status

**Superseded** by [MotherDuck to ClickHouse Migration](./2025-11-25-motherduck-clickhouse-migration.md) (2025-11-25)

## Date

2025-11-13

> **Note**: MotherDuck was replaced by ClickHouse Cloud as the production database. The staleness monitoring now uses ClickHouse queries via the `clickhouse-gap-detector` Cloud Function. Threshold values may differ for the new architecture.

## Context

Data quality checker monitors MotherDuck for stale data by querying the latest block timestamp. Current threshold is 960 seconds (16 minutes), but empirical analysis shows this is unnecessarily conservative.

### Current Configuration

- **Threshold**: 960 seconds (16 minutes)
- **Grace period**: 300 seconds (5 minutes)
- **Total detection window**: 21 minutes (960s + 300s grace)

### Empirical Evidence

Threshold validation agent analyzed 100 recent executions:

- **P50 age**: 156 seconds (2.6 minutes)
- **P95 age**: 287 seconds (4.8 minutes)
- **P99 age**: 312 seconds (5.2 minutes)
- **Max age**: 342 seconds (5.7 minutes)

### Current State Analysis

```
Current threshold: 960s
P99 age: 312s
Safety margin: 3.1× P99 (960 / 312 = 3.08)
```

**Problem**: 960-second threshold is 3.1× the P99 age, far exceeding industry standard 2× safety margin. This creates unnecessarily slow detection of real data staleness issues.

### Industry Best Practice

Staleness thresholds should be **2× P99 age** to balance:

- False positive prevention (adequate buffer for normal variance)
- Fast detection (catch real issues quickly)

**Recommended threshold**: 600 seconds (1.92× P99, within best practice)

## Decision

Reduce staleness threshold from **960 seconds to 600 seconds** (37.5% reduction).

### Rationale

- **Empirical validation**: 0% false positives at 600s on 100-sample dataset
- **Safety margin**: 1.92× P99 (600 / 312 = 1.92), industry-aligned
- **Detection improvement**: 21-minute window → 15-minute window (28.6% faster)
- **Conservative approach**: Still maintains generous buffer above P99

### New Configuration

- **Threshold**: 600 seconds (10 minutes)
- **Grace period**: 300 seconds (5 minutes) - unchanged
- **Total detection window**: 15 minutes (600s + 300s grace)

## Consequences

### Positive

- **Faster detection**: 21-minute detection window → 15-minute window (28.6% improvement)
- **Zero false positives**: Validated on 100 executions, 0 would-be violations at 600s
- **Industry-aligned**: 1.92× P99 safety margin follows best practices
- **Maintains reliability**: Still 2× buffer above P95 (600 / 287 = 2.09)

### Negative

- **Potential edge case sensitivity**: If P99 increases significantly (>50%), may require re-calibration
- **Monitoring dependency**: Requires 24-hour post-deployment observation to confirm

### Mitigation

- Monitor false positive rate for 24 hours post-deployment
- Rollback to 960s if false positive rate >1% (acceptable threshold)
- Schedule quarterly threshold re-validation using same empirical methodology

## Alternatives Considered

### Alternative 1: Keep 960s threshold (current)

**Rejected**: Unnecessarily conservative (3.1× P99), creates slow detection of real staleness issues

### Alternative 2: Aggressive 400s threshold (1.3× P99)

**Rejected**: Insufficient safety margin, high risk of false positives during normal variance

### Alternative 3: Moderate 500s threshold (1.6× P99)

**Rejected**: Still below 2× best practice, marginal detection improvement (1 minute) over 600s

## Implementation

### Code Changes

```python
# File: deployment/cloud-run/data_quality_checker.py
# Line: 34

# Before
STALE_THRESHOLD_SECONDS = int(os.environ.get('STALE_THRESHOLD_SECONDS', '960'))

# After
STALE_THRESHOLD_SECONDS = int(os.environ.get('STALE_THRESHOLD_SECONDS', '600'))
```

### Documentation Updates

```python
# File: deployment/cloud-run/data_quality_checker.py
# Lines: 15, 18-19

# Before
# STALE_THRESHOLD_SECONDS: Maximum age before alert (default: 960)

# After
# STALE_THRESHOLD_SECONDS: Maximum age before alert (default: 600)

# Before
# Exit Codes:
#     0: Data is fresh (<960s old)
#     1: Data is stale (>960s old)

# After
# Exit Codes:
#     0: Data is fresh (<600s old)
#     1: Data is stale (>600s old)
```

### Environment Variable Update

```bash
gcloud run jobs update eth-md-data-quality-checker \
  --region us-central1 \
  --update-env-vars="STALE_THRESHOLD_SECONDS=600"
```

## Validation

### Pre-Deployment Validation

```python
# File: tmp/monitoring-fixes-validation/validate_threshold.py

import duckdb

# Query last 100 executions from validation.duckdb
conn = duckdb.connect('~/.cache/gapless-network-data/validation.duckdb')

# Simulate 600s threshold on historical data
violations = conn.execute("""
    SELECT COUNT(*)
    FROM validation_results
    WHERE timestamp > NOW() - INTERVAL '7 days'
      AND latest_block_age > 600
""").fetchone()[0]

assert violations == 0, f"Would-be false positives: {violations}"
print("✅ 0 false positives at 600s threshold")
```

### Post-Deployment Validation

```bash
# Monitor for 24 hours after deployment
# Expected: 0 false positive alerts

# Query Healthchecks.io for any /fail pings
curl -H "X-Api-Key: $HEALTHCHECKS_API_KEY" \
  https://healthchecks.io/api/v3/checks/c3087199-8265-4721-99fe-589c5d10a119/pings | \
  jq '.[] | select(.type == "fail") | {created, body}'

# Expected: Empty (no failures in 24 hours)
```

## SLO Impact

### Before

- **Observability**: Data staleness detected in 21 minutes (960s threshold + 300s grace)
- **Correctness**: 0% false positives (overly conservative threshold)

### After

- **Observability**: Data staleness detected in 15 minutes (600s threshold + 300s grace)
  - **Improvement**: 28.6% faster detection (6-minute reduction)
- **Correctness**: 0% false positives maintained (validated on 100 samples)

### Real-World Impact

**Scenario**: MotherDuck ingestion stops at 10:00 AM

- **Before**: Alert triggered at 10:21 AM (21-minute delay)
- **After**: Alert triggered at 10:15 AM (15-minute delay)
- **Benefit**: 6 minutes faster response to production issues

## References

- Audit artifact: `/tmp/monitoring-audit-thresholds/THRESHOLD_VALIDATION_REPORT.md`
- Specification: `specifications/monitoring-fixes-phase.yaml` (task P1-5)
- Empirical data: 100 execution samples (P99: 312s, P95: 287s)
- Industry standard: 2× P99 safety margin for staleness thresholds

## Related

- [Grace Period Calibration](./2025-11-13-healthchecks-grace-period-calibration.md) (complementary slow alerting)
- [Exception Handler Notifications](./2025-11-13-exception-handler-notifications.md) (complementary fast alerting)
