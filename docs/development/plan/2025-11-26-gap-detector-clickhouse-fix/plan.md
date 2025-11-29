# Plan: Gap Detector ClickHouse Fix

**Status**: Completed
**Created**: 2025-11-26
**Completed**: 2025-11-27
**Related ADR**: [Gap Detector ClickHouse Fix](/docs/architecture/decisions/2025-11-26-gap-detector-clickhouse-fix.md)

## (a) Context

### Problem Statement

The `motherduck-gap-detector` Cloud Function has been **failing every 3 hours** since 2025-11-25:

```
_duckdb.InvalidInputException: Invalid Input Error: The following options were not recognized: connect_timeout
```

**Root Cause**: Function still uses MotherDuck/DuckDB code after ClickHouse migration (MADR-0013) completed.

### Current State

**Failing Code** (`deployment/gcp-functions/motherduck-monitor/main.py`):

| Line    | Issue                                            |
| ------- | ------------------------------------------------ |
| 38      | `import duckdb` - Imports deprecated dependency  |
| 52-53   | `MD_DATABASE`, `MD_TABLE` - MotherDuck config    |
| 119     | `motherduck_token` secret - No longer valid      |
| 132-226 | `detect_gaps()` - Uses DuckDB LAG()              |
| 229-269 | `check_staleness()` - Uses DuckDB queries        |
| 458-459 | `connect_timeout: 30000` - Invalid DuckDB config |

**Working Code** (reusable):

| Lines   | Function                     | Notes                           |
| ------- | ---------------------------- | ------------------------------- |
| 276-342 | `validate_clickhouse_sync()` | Already uses clickhouse-connect |
| 349-420 | Notification functions       | Pushover + Healthchecks.io      |

### Infrastructure

- **Cloud Function**: `motherduck-gap-detector` (Gen2, Python 3.12, us-east1)
- **Scheduler**: Every 3 hours
- **Database**: ClickHouse Cloud AWS (`ethereum_mainnet.blocks`)
- **Monitoring**: Healthchecks.io + Pushover

## (b) Plan

### Objective

Remove MotherDuck/DuckDB code from gap detector, replace with ClickHouse-native queries.

### Strategy

Single-phase fix: Remove deprecated code, add ClickHouse implementations, deploy, validate.

### Semantic Constants

```python
# Thresholds (derived from Ethereum network characteristics)
STALENESS_THRESHOLD_SECONDS = 960  # 16 minutes (~80 blocks)
GAP_DETECTION_LIMIT = 20           # Top N gaps to report

# ClickHouse connection
CLICKHOUSE_PORT_HTTPS = 8443       # Standard HTTPS port
CLICKHOUSE_CONNECT_TIMEOUT = 30    # Seconds
```

### Implementation

#### Phase 1: Code Changes

**1.1 Update requirements.txt**

```diff
- duckdb==1.4.1
  httpx>=0.27.0
  google-cloud-secret-manager>=2.21.0
  python-ulid>=3.1.0
  functions-framework>=3.8.0
  clickhouse-connect>=0.7.0
```

**1.2 Remove MotherDuck imports and config**

- Remove `import duckdb`
- Remove `MD_DATABASE`, `MD_TABLE` constants
- Remove `motherduck_token` from `load_secrets()`

**1.3 Replace gap detection functions**

```python
def detect_gaps_clickhouse(client) -> tuple[list[dict], int]:
    """Detect gaps using ClickHouse native SQL with ReplacingMergeTree FINAL."""
    result = client.query("""
        SELECT COUNT(*), MIN(number), MAX(number)
        FROM ethereum_mainnet.blocks FINAL
    """)
    total, min_block, max_block = result.result_rows[0]
    expected = (max_block - min_block + 1) if min_block else 0
    missing = expected - total

    gaps = []
    if missing > 0:
        gap_result = client.query("""
            WITH gaps AS (
                SELECT number,
                       lagInFrame(number, 1) OVER (ORDER BY number) as prev,
                       number - lagInFrame(number, 1) OVER (ORDER BY number) - 1 as gap_size
                FROM ethereum_mainnet.blocks FINAL
            )
            SELECT prev + 1 as start_block, number - 1 as end_block, gap_size
            FROM gaps WHERE gap_size > 0
            ORDER BY gap_size DESC LIMIT 20
        """)
        for row in gap_result.result_rows:
            gaps.append({
                'block_number': row[0],
                'gap_type': 'missing_block',
                'description': f'{row[2]} blocks missing: {row[0]:,} to {row[1]:,}'
            })
    return gaps, total

def check_staleness_clickhouse(client) -> tuple[bool, int, datetime, int]:
    """Check data freshness using ClickHouse."""
    result = client.query("""
        SELECT MAX(number), MAX(timestamp)
        FROM ethereum_mainnet.blocks FINAL
    """)
    latest_block, latest_ts = result.result_rows[0]
    age = (datetime.now(timezone.utc).replace(tzinfo=None) - latest_ts).total_seconds()
    is_fresh = age <= STALENESS_THRESHOLD_SECONDS
    return is_fresh, int(age), latest_ts, latest_block
```

**1.4 Update monitor() entry point**

Replace MotherDuck connection with ClickHouse client:

```python
# Connect to ClickHouse
client = clickhouse_connect.get_client(
    host=get_secret('clickhouse-host'),
    port=CLICKHOUSE_PORT_HTTPS,
    username='default',
    password=get_secret('clickhouse-password'),
    secure=True,
    connect_timeout=CLICKHOUSE_CONNECT_TIMEOUT,
)

# Run checks
is_fresh, age_seconds, latest_timestamp, latest_block = check_staleness_clickhouse(client)
gaps, total_blocks = detect_gaps_clickhouse(client)
is_healthy = is_fresh and len(gaps) == 0
```

#### Phase 2: Deploy & Validate

**2.1 Local Testing**

```bash
doppler run --project aws-credentials --config prd -- \
  python -c "import clickhouse_connect; print('OK')"
```

**2.2 Deploy Cloud Function**

```bash
cd deployment/gcp-functions/motherduck-monitor
gcloud functions deploy clickhouse-gap-detector \
  --gen2 --runtime=python312 --region=us-east1 \
  --project=eonlabs-ethereum-bq \
  --source=. --entry-point=monitor \
  --trigger-http --no-allow-unauthenticated \
  --service-account=motherduck-monitor-sa@eonlabs-ethereum-bq.iam.gserviceaccount.com \
  --timeout=540s --memory=512MB
```

**2.3 Manual Trigger**

```bash
gcloud scheduler jobs run clickhouse-monitor-trigger --location=us-east1
```

**2.4 Verification**

- [ ] HTTP 200 response
- [ ] Pushover notification received
- [ ] Healthchecks.io shows green
- [ ] No errors in Cloud Logging

## (c) Task List

### Phase 1: Code Changes - COMPLETED

- [x] **1.1** Update `requirements.txt` - Remove `duckdb==1.4.1`
- [x] **1.2** Remove MotherDuck imports (`import duckdb`)
- [x] **1.3** Remove MotherDuck config (`MD_DATABASE`, `MD_TABLE`)
- [x] **1.4** Remove `motherduck_token` from `load_secrets()`
- [x] **1.5** Remove `detect_gaps()` function (DuckDB-based)
- [x] **1.6** Remove `check_staleness()` function (DuckDB-based)
- [x] **1.7** Add `detect_gaps_clickhouse()` function
- [x] **1.8** Add `check_staleness_clickhouse()` function
- [x] **1.9** Update `monitor()` to use ClickHouse client
- [x] **1.10** Remove dual-validation code (no longer needed)

### Phase 2: Deploy & Validate - COMPLETED

- [x] **2.1** Local syntax check (`python -m py_compile main.py`)
- [x] **2.2** Deploy Cloud Function (revision 00018-wur)
- [x] **2.3** Manual trigger via Cloud Scheduler
- [x] **2.4** Verify Pushover notification (ULID: 01KB1EDPRY6SBJ9PVKB6NX0Y71)
- [x] **2.5** Healthchecks.io ping - Configured via MADR-0016 (`1a74805b-5315-4808-91d2-1b8b248422b6`)
- [x] **2.6** Update ADR status to Accepted

### Verification Results (2025-11-27T01:21)

```
Block range: 0 to 23,886,743
Expected: 23,886,744 blocks
Actual: 23,886,437 blocks
Missing: 307 blocks (9 gap regions)
Largest gap: 185 blocks (23,877,777 to 23,877,961)
```

Note: Gap detection working correctly. Found real gaps in database requiring backfill.

## Success Criteria

- Gap detector executes without errors
- Pushover notification received with accurate block count
- Healthchecks.io shows success ping (not `/fail`)
- Cloud Logging shows no errors for 24+ hours (8 cycles)

## Rollback Procedure

```bash
# Revert code
git revert HEAD --no-edit
git push origin migrate-to-clickhouse

# Redeploy
cd deployment/gcp-functions/motherduck-monitor
gcloud functions deploy motherduck-gap-detector \
  --gen2 --runtime=python312 --region=us-east1 --source=.
```
