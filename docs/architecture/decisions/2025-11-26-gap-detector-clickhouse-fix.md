# MADR-0015: Gap Detector ClickHouse Fix

**Status**: Accepted
**Date**: 2025-11-26
**Deciders**: Terry Li
**Related ADR**: [MADR-0013: MotherDuck to ClickHouse Migration](./0013-motherduck-clickhouse-migration.md)
**Plan**: [`docs/development/plan/0015-gap-detector-clickhouse-fix/plan.md`](../development/plan/0015-gap-detector-clickhouse-fix/plan.md)

## Context

The `motherduck-gap-detector` Cloud Function has been **failing every 3 hours** since 2025-11-25 with:

```
_duckdb.InvalidInputException: Invalid Input Error: The following options were not recognized: connect_timeout
```

**Root Cause**: The function still uses MotherDuck/DuckDB code after the ClickHouse migration (MADR-0013) was completed. The `connect_timeout` configuration option is not valid for DuckDB.

**Impact**: Gap detection and Pushover notifications have been non-functional for ~24 hours. Healthchecks.io receives `/fail` pings but the actual gap detection queries never execute.

## Decision

Remove all MotherDuck/DuckDB code from the gap detector and use ClickHouse-native queries exclusively.

### Changes

| Component           | Action                                             |
| ------------------- | -------------------------------------------------- |
| `requirements.txt`  | Remove `duckdb==1.4.1`                             |
| `load_secrets()`    | Remove `motherduck_token`                          |
| `detect_gaps()`     | Replace with ClickHouse-native implementation      |
| `check_staleness()` | Replace with ClickHouse-native implementation      |
| `monitor()`         | Use ClickHouse client instead of DuckDB connection |

### Semantic Constants

Configuration values abstracted for maintainability:

| Constant                      | Value | Rationale                            |
| ----------------------------- | ----- | ------------------------------------ |
| `STALENESS_THRESHOLD_SECONDS` | 960   | 16 minutes (~80 blocks at 12s/block) |
| `GAP_DETECTION_LIMIT`         | 20    | Top N largest gaps to report         |
| `CLICKHOUSE_CONNECT_TIMEOUT`  | 30    | Connection timeout in seconds        |
| `CLICKHOUSE_PORT_HTTPS`       | 8443  | Standard ClickHouse HTTPS port       |

## Consequences

### Positive

- Gap detector will execute successfully
- Pushover notifications resume with accurate data
- Simplified codebase (single database, no dual-validation)
- Reduced dependencies (no `duckdb` package)

### Negative

- MotherDuck validation path removed (acceptable: migration complete)
- Must ensure ClickHouse credentials are in Secret Manager

### SLO Impact

| SLO             | Before                   | After                        |
| --------------- | ------------------------ | ---------------------------- |
| Availability    | 0% (failing)             | 99.9% (expected)             |
| Correctness     | N/A (no execution)       | Block sequence validation    |
| Observability   | Healthchecks /fail only  | Full Pushover + Healthchecks |
| Maintainability | Dual-database complexity | Single-database simplicity   |

## Alternatives Considered

### 1. Fix DuckDB connect_timeout Option

**Rejected**: The underlying issue is using MotherDuck after migration. Fixing just the config option leaves dead code.

### 2. Keep Dual-Validation Mode

**Rejected**: MotherDuck trial expired. Dual-validation serves no purpose post-migration.

## Validation

1. Local test with Doppler credentials
2. Deploy Cloud Function
3. Manual trigger via Cloud Scheduler
4. Verify Pushover notification received
5. Verify Healthchecks.io shows success ping
6. Monitor for 24 hours (8 cycles)

## References

- [MADR-0013: MotherDuck to ClickHouse Migration](./0013-motherduck-clickhouse-migration.md)
- [Plan 0015](../development/plan/0015-gap-detector-clickhouse-fix/plan.md)
- [Cloud Function logs](https://console.cloud.google.com/functions/details/us-east1/motherduck-gap-detector)
