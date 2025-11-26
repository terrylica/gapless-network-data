# MADR-0003: MotherDuck Connection Timeout and Fallback Architecture

## Status

**Superseded** by [MADR-0013: MotherDuck to ClickHouse Migration](./0013-motherduck-clickhouse-migration.md) (2025-11-25)

> **Note**: MotherDuck was replaced by ClickHouse Cloud as the production database. ClickHouse uses native TCP connections with built-in retry logic. The timeout and fallback patterns documented here are no longer applicable to the current architecture.

## Context

MotherDuck is a single point of failure affecting all 6 components. When MotherDuck is down or slow, components hang indefinitely with no automatic recovery.

### Current Behavior (Problematic)

```python
# No timeout
conn = duckdb.connect(f'md:{MD_DATABASE}?motherduck_token={token}')
# ❌ Hangs forever if MotherDuck unreachable
```

**Observed failures**:

- VM systemd service enters "activating" state, never restarts
- Cloud Run Jobs hang until 10-minute job timeout
- No visibility into connection failures (silent hang)

### Impact

- **Availability**: Complete data collection stops during MotherDuck outage
- **Observability**: No error logs, appears as timeout
- **Recovery**: Manual intervention required (restart services)

## Decision

Implement **30-second connection timeout** on all MotherDuck connections with explicit error handling.

### Pattern

```python
try:
    conn = duckdb.connect(
        f'md:{MD_DATABASE}?motherduck_token={token}',
        config={'connect_timeout': 30000}  # 30 seconds in milliseconds
    )
except Exception as e:
    # Log error
    logger.error(f"MotherDuck connection failed: {e}")

    # Ping Healthchecks.io /fail
    if healthcheck_url:
        requests.post(f"{healthcheck_url}/fail",
                      data=f"MotherDuck timeout: {e}", timeout=10)

    # Re-raise for visibility
    raise
```

### Rationale for 30 seconds

- **P95 connection time**: <2 seconds (normal)
- **P99 connection time**: <5 seconds (slow)
- **Timeout**: 30 seconds = 6× P99 (generous buffer)
- **Trade-off**: Fast failure vs connection retry tolerance

## Consequences

### Positive

- **Fast failure**: Services fail within 30 seconds instead of hanging indefinitely
- **Automatic recovery**: systemd RestartSec=10s triggers after failure
- **Visibility**: Clear error logs instead of silent hangs
- **Monitoring**: Healthchecks.io receives /fail ping immediately

### Negative

- **No automatic retry**: Services exit on timeout (rely on systemd/Cloud Run retry)
- **Potential false failures**: If MotherDuck legitimately slow >30s (rare)

### Mitigation

- systemd `RestartSec=10s` provides automatic retry every 10 seconds
- Cloud Run Jobs retry 3 times by default
- 30-second timeout is generous (6× P99)

## Alternatives Considered

### Alternative 1: No timeout (current)

**Rejected**: Causes indefinite hangs, manual intervention required

### Alternative 2: Short timeout (5 seconds) + retry logic

**Rejected**: Adds complexity, prefer relying on systemd/Cloud Run orchestration

### Alternative 3: Local DuckDB fallback

**Deferred to P1**: Requires architectural changes (schema sync, data reconciliation)

Current decision focuses on **fail-fast** with orchestration-level retry. Future enhancement can add local fallback without changing timeout strategy.

## Implementation

### All 6 Components

**Files to modify**:

1. `deployment/cloud-run/data_quality_checker.py` (line ~70)
2. `deployment/gcp-functions/motherduck-monitor/main.py` (line ~362)
3. `deployment/cloud-run/main.py` (BigQuery sync, line ~150)
4. `deployment/vm/realtime_collector.py` (line ~120)
5. `deployment/backfill/main.py` (historical backfill, line ~80)
6. `.claude/skills/motherduck-pipeline-operations/scripts/verify_motherduck.py`

**Change pattern**:

```python
# Before
conn = duckdb.connect(f'md:{MD_DATABASE}?motherduck_token={token}')

# After
conn = duckdb.connect(
    f'md:{MD_DATABASE}?motherduck_token={token}',
    config={'connect_timeout': 30000}
)
```

### Error Handling Pattern

```python
try:
    conn = duckdb.connect(
        f'md:{MD_DATABASE}?motherduck_token={token}',
        config={'connect_timeout': 30000}
    )
except duckdb.IOException as e:
    # Network/timeout errors
    logger.error(f"MotherDuck connection timeout: {e}")
    if healthcheck_url:
        requests.post(f"{healthcheck_url}/fail",
                      data=f"MotherDuck timeout after 30s", timeout=10)
    raise
except Exception as e:
    # Other errors (auth, etc)
    logger.error(f"MotherDuck connection error: {e}")
    if healthcheck_url:
        requests.post(f"{healthcheck_url}/fail",
                      data=f"MotherDuck error: {e.__class__.__name__}", timeout=10)
    raise
```

## Validation

### Test Script

```python
# File: tmp/monitoring-fixes-validation/test_motherduck_timeout.py
import duckdb
import time

# Test: Connection timeout enforced
start = time.time()
try:
    conn = duckdb.connect(
        'md:nonexistent?motherduck_token=invalid',
        config={'connect_timeout': 5000}  # 5 seconds for test
    )
except Exception as e:
    elapsed = time.time() - start
    assert elapsed < 10, f"Timeout too long: {elapsed}s"
    assert 'timeout' in str(e).lower() or 'connection' in str(e).lower()
    print(f"✅ Timeout enforced in {elapsed:.1f}s")
```

### Production Validation

```bash
# 1. Deploy changes
# 2. Simulate MotherDuck outage (block access via firewall)
# 3. Verify services fail within 30 seconds
# 4. Verify systemd/Cloud Run automatic retry
# 5. Verify Healthchecks.io receives /fail ping
```

## SLO Impact

### Before

- **Availability**: Services hang indefinitely (0% during outage)
- **Observability**: Silent hangs, no error logs

### After

- **Availability**: Services fail fast, automatic retry every 10s
- **Observability**: Clear error logs + Healthchecks.io /fail pings

## Future Enhancements (P1)

### Local DuckDB Fallback

```python
try:
    conn = duckdb.connect(f'md:{MD_DATABASE}?motherduck_token={token}',
                          config={'connect_timeout': 30000})
except Exception as e:
    logger.warning(f"MotherDuck unavailable, using local fallback: {e}")
    conn = duckdb.connect('~/.cache/gapless-network-data/fallback.duckdb')
    # Write to local, sync to MotherDuck when available
```

**Requires**:

- Local schema sync mechanism
- Data reconciliation on recovery
- Disk space management
- Separate MADR for architecture

## References

- Audit: `/tmp/monitoring-audit-failures/00-EXECUTIVE_SUMMARY.md`
- Specification: `specifications/monitoring-fixes-phase.yaml` (task P0-4)
- DuckDB config docs: https://duckdb.org/docs/configuration/overview

## Decision Date

2025-11-13

## Related ADRs

- MADR-0002: Exception Handler Notifications (complementary pattern)
