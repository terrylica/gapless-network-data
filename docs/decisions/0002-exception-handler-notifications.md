# MADR-0002: Exception Handler Notification Strategy

## Status

Proposed

## Context

Adversarial audit discovered 3 execution paths that can skip Healthchecks.io pings, creating monitoring blind spots where fatal errors go undetected.

### Problem: Silent Failures

Current pattern (INCORRECT):
```python
try:
    # Do work
    # Ping Healthchecks.io on success
except Exception as e:
    logger.error(f"Fatal error: {e}")
    sys.exit(1)
    # ❌ No Healthchecks.io ping - creates false negative
```

Result: Dead Man's Switch never receives notification, marks check as "down" only after grace period expires (5-30 minutes later).

### Affected Components

1. **eth-md-data-quality-checker** (lines 149-153): Exception path doesn't ping
2. **motherduck-gap-detector** (lines 453-457): Exception path doesn't ping
3. **eth-md-updater** (lines 212-216): "No new blocks" early exit doesn't ping

## Decision

Implement **"Always Ping, Vary Endpoint"** pattern:
- **Success path**: Ping `https://hc-ping.com/{uuid}`
- **Failure path**: Ping `https://hc-ping.com/{uuid}/fail`
- **No execution path** may skip notification

### Pattern

```python
try:
    # Do work
    result = perform_operation()

    # Ping success
    if healthcheck_url:
        requests.post(healthcheck_url, data=f"Success: {result}", timeout=10)

    return 0

except Exception as e:
    # Ping failure
    if healthcheck_url:
        requests.post(
            f"{healthcheck_url}/fail",
            data=f"Fatal error: {e.__class__.__name__}: {e}",
            timeout=10
        )

    # Re-raise for visibility
    raise
```

## Consequences

### Positive

- **Eliminates false negatives**: Fatal errors immediately visible
- **Reduces detection latency**: From grace period (5-30 min) to <1 second
- **Simplifies debugging**: Healthchecks.io shows last error message
- **Follows OSS pattern**: Standard Dead Man's Switch implementation

### Negative

- **Slight latency increase**: +10-50ms per execution (negligible)
- **Requires network call in error path**: Could fail if network down (acceptable - service already failing)

### Mitigation

Network call timeout (10 seconds) prevents hanging in error path. If Healthchecks.io unreachable, exception still propagates (fail-loud principle).

## Alternatives Considered

### Alternative 1: No notification on failure

**Rejected**: Current behavior, creates monitoring blind spots

### Alternative 2: Best-effort ping without re-raising

**Rejected**: Violates "raise and propagate errors" principle, hides failures

### Alternative 3: Async notification

**Rejected**: Over-engineering for 10-50ms operation, adds complexity

## Implementation

### eth-md-data-quality-checker

```python
# File: deployment/cloud-run/data_quality_checker.py
# Lines: 149-153

except Exception as e:
    print(f"\n❌ FATAL ERROR: {e}")
    import traceback
    traceback.print_exc()

    # ADD THIS:
    if healthcheck_url:
        try:
            requests.post(
                f"{healthcheck_url}/fail",
                data=f"Fatal error: {e.__class__.__name__}: {e}",
                timeout=10
            )
        except:
            pass  # Don't mask original error

    return 1
```

### motherduck-gap-detector

```python
# File: deployment/gcp-functions/motherduck-monitor/main.py
# Lines: 453-457

except Exception as e:
    diagnostic_data['error'] = str(e)
    diagnostic_data['status'] = 'fatal_error'

    # ADD THIS:
    if HEALTHCHECKS_PING_URL:
        try:
            httpx.post(
                f"{HEALTHCHECKS_PING_URL}/fail",
                data=json.dumps(diagnostic_data),
                timeout=10
            )
        except:
            pass

    raise
```

### eth-md-updater

```python
# File: deployment/cloud-run/main.py
# Lines: 212-216

if new_blocks.empty:
    print("No new blocks within lookback window")

    # ADD THIS:
    if healthcheck_url:
        requests.post(
            healthcheck_url,  # Success endpoint (no new data is OK)
            data="No new blocks (within lookback)",
            timeout=10
        )

    return 0
```

## Validation

```bash
# Test failure path
python3 deployment/cloud-run/data_quality_checker.py
# Expected: /fail ping sent, exit code 1

# Test success path
python3 deployment/cloud-run/data_quality_checker.py
# Expected: success ping sent, exit code 0

# Verify Healthchecks.io received both
curl -H "X-Api-Key: $HEALTHCHECKS_API_KEY" \
  https://healthchecks.io/api/v3/checks/{check_id}/pings | \
  jq '.[-2:]'  # Last 2 pings
```

## SLO Impact

### Before

- **Observability**: Fatal errors detected in 5-30 minutes (grace period)
- **Correctness**: False negative risk (silent failures)

### After

- **Observability**: Fatal errors detected in <1 second
- **Correctness**: Zero false negatives

## References

- Audit: `/tmp/monitoring-audit-deadmans/COMPREHENSIVE_AUDIT_REPORT.md`
- Specification: `specifications/monitoring-fixes-phase.yaml` (task P0-3)
- Healthchecks.io /fail endpoint: https://healthchecks.io/docs/signaling_failures/

## Decision Date

2025-11-13

## Related ADRs

- MADR-0001: Grace Period Calibration (complementary slow alerting)
