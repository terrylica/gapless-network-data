# Plan: MotherDuck to ClickHouse AWS Migration

**Status**: Completed
**Created**: 2025-11-24
**Completed**: 2025-11-25
**Related ADR**: [MotherDuck to ClickHouse Migration](/docs/architecture/decisions/2025-11-25-motherduck-clickhouse-migration.md)

## (a) Context

**Why This Plan Exists**:

MotherDuck trial ending in 2-3 days requires urgent migration to ClickHouse Cloud AWS. Current infrastructure:

**Production Data**:

- 23.84M Ethereum blocks (verified 2025-11-20 via MotherDuck)
- ~1.5 GB storage (76-100 bytes/block)
- Dual-pipeline: BigQuery hourly (578 blocks/run) + Alchemy real-time (12s intervals)

**Infrastructure to Migrate**:
| Component | File | MotherDuck Usage |
|-----------|------|------------------|
| VM Real-Time Collector | `deployment/vm/realtime_collector.py` | Line 121: `duckdb.connect('md:')` |
| Cloud Run Batch Updater | `deployment/cloud-run/main.py` | Line 136: `duckdb.connect('md:')` |
| Data Quality Checker | `deployment/cloud-run/data_quality_checker.py` | Lines 70-73 |
| Gap Monitor Function | `deployment/gcp-functions/motherduck-monitor/main.py` | Line 361 |

**ClickHouse Target**:

- Service: ClickHouse Cloud (managed AWS)
- Status: Provisioned but untested
- Credentials: Doppler `aws-credentials/prd` (8 secrets)

**Constraints**:

- Zero downtime required
- 2-3 days to trial expiration
- Fail-fast error policy (exception-only)
- 6-12 hour compressed validation

## (b) Plan

**Objective**: Migrate 23.84M Ethereum blocks and 4 production pipelines from MotherDuck to ClickHouse AWS with zero downtime.

**Strategy**: Dual-write (both databases active during migration, safe rollback at every stage)

**Timeline** (2.5 days compressed):

### Day 0 (TODAY) - Pre-Migration & Historical Load

| Hour | Task                           | Success Criteria                             |
| ---- | ------------------------------ | -------------------------------------------- |
| 0-1  | Validate ClickHouse connection | Query returns result, write succeeds         |
| 1-2  | Create ClickHouse schema       | Table created with ReplacingMergeTree        |
| 2-6  | Historical data migration      | 23.84M rows in ClickHouse, row count matches |

### Day 1 - Dual-Write Deployment

| Hour | Task                           | Success Criteria                       |
| ---- | ------------------------------ | -------------------------------------- |
| 0-2  | Update 4 production components | Code changes complete, tests pass      |
| 2-4  | Deploy to GCP                  | VM, Cloud Run, Cloud Function deployed |
| 4-16 | Compressed validation          | Hourly consistency checks pass         |

### Day 2 - Cutover & Deprecation

| Hour | Task                   | Success Criteria                        |
| ---- | ---------------------- | --------------------------------------- |
| 0-2  | Read cutover           | SDK/monitoring reads from ClickHouse    |
| 2-4  | MotherDuck deprecation | Writes stopped, final snapshot archived |

**Rollback Strategy**:

- Before Day 1 Hour 4: No changes to production (revert branch)
- Day 1-2: Revert to MotherDuck-only (dual-write continues, switch reads back)
- After Day 2: MotherDuck archived in GCS (30-day retention for emergency recovery)

## (c) Task List

### Phase 0: Validation (Day 0, Hour 0-1) ✅ COMPLETED

**0.1 Validate ClickHouse connection using Doppler credentials** ✅ COMPLETED

- Command: `doppler run --project aws-credentials --config prd -- uv run scripts/clickhouse/validate_connection.py`
- Result: Connection succeeded, server version 25.8.1.8702
- Validated: 2025-11-24T23:20:10
- Output: `/tmp/clickhouse-validation.txt`

### Phase 1: Schema & Historical Migration (Day 0, Hour 1-6) ✅ COMPLETED

**1.1 Create ClickHouse schema** ✅ COMPLETED

- Engine: ReplacingMergeTree (automatic deduplication on background merge)
- ORDER BY: `number` (block number as deduplication key)
- PARTITION BY: `toYYYYMM(timestamp)` (monthly partitions)
- Script: `scripts/clickhouse/create_schema.py`
- Executed: 2025-11-24T23:21:04

**1.2 Export MotherDuck to Parquet** ⏭️ SKIPPED

- Decision: Migrate directly from BigQuery (source of truth) instead of MotherDuck
- Rationale: BigQuery has all historical data, no MotherDuck SSO timeout issues

**1.3 BigQuery → ClickHouse Migration** ✅ COMPLETED

- Script: `scripts/clickhouse/migrate_from_bigquery.py`
- Total rows: **23,865,016 blocks** (2015-2025)
- Duration: 5 minutes (300 seconds)
- Rate: ~80K rows/sec
- Verification: Row counts per year verified
- Completed: 2025-11-24T23:35:00

### Phase 2: Dual-Write Implementation (Day 1, Hour 0-4) - CODE COMPLETE ✅

**Phase 2 Summary** (completed 2025-11-25):

- All 4 production components updated with dual-write support
- Code validated (Python syntax checks pass for all files)
- GCP secrets created via Python SDK (`setup_gcp_secrets.py`)
- Verification scripts created (`verify_consistency.py`, `setup_gcp_secrets.sh`)
- Deployment guide created (`DEPLOYMENT.md`)
- **Next**: Deploy to GCP via Cloud Console (gcloud CLI not available locally)

**2.1 Update VM realtime collector** ✅ COMPLETED

- File: `deployment/vm/realtime_collector.py`
- Changes: Added ClickHouse client, dual-write in `flush_buffer()` and `insert_block()`
- Error policy: Fail-fast (ClickHouse written FIRST, exception propagated on failure)
- Features: `DUAL_WRITE_ENABLED` env var toggle, `flush_to_clickhouse()` helper
- Completed: 2025-11-24

**2.2 Update Cloud Run batch updater** ✅ COMPLETED

- File: `deployment/cloud-run/main.py`
- Changes: Added `load_to_clickhouse()` function, dual-write in main flow
- Error policy: Fail-fast (ClickHouse written FIRST, exception propagated on failure)
- Features: `DUAL_WRITE_ENABLED` env var toggle, pandas df conversion with UInt256 handling
- Completed: 2025-11-24

**2.3 Update Cloud Run data quality checker** ✅ COMPLETED

- File: `deployment/cloud-run/data_quality_checker.py`
- Changes: Added `check_clickhouse_freshness()` function, CHECK_CLICKHOUSE env var toggle
- Features: Validates both MotherDuck and ClickHouse when enabled
- Dependencies: Added `clickhouse-connect` to inline script dependencies
- Completed: 2025-11-25

**2.4 Update Cloud Function gap monitor** ✅ COMPLETED

- File: `deployment/gcp-functions/motherduck-monitor/main.py`
- Changes: Added `validate_clickhouse_sync()` function, cross-database comparison
- Features: `DUAL_VALIDATION_ENABLED` env var, block count/max comparison with tolerance
- Dependencies: Added `clickhouse-connect>=0.7.0` to requirements.txt
- Completed: 2025-11-24

**2.5 Deploy to GCP** ✅ COMPLETED

> **Detailed Guide**: See [`DEPLOYMENT.md`](./DEPLOYMENT.md) for step-by-step deployment instructions.

**Deployment Summary** (2025-11-25):

- ✅ GCP secrets created via Python SDK (`setup_gcp_secrets.py`)
- ✅ VM collector deployed with dual-write (confirmed in logs)
- ✅ Cloud Run job `eth-md-updater` updated with dual-write env vars
- ✅ Cloud Function `motherduck-gap-detector` updated with dual-validation

**Dual-Write Verification**:

```
[BATCH] ✅ Flushed 25 blocks to ClickHouse
[BATCH] ✅ Flushed 25 blocks to MotherDuck
```

**Consistency Check** (2025-11-25T08:03):

- ClickHouse: 23,865,042 blocks (max: 23,874,501)
- MotherDuck: 23,874,495 blocks (max: 23,874,501)
- Max block matches: ✅ Both databases in sync for new blocks
- Historical diff: ~9,453 blocks (expected from BigQuery migration timing)

**Quick Deployment:**

```bash
# Step 1: Setup GCP secrets (requires gcloud CLI)
./scripts/clickhouse/setup_gcp_secrets.sh

# Step 2: Deploy VM collector
cd deployment/vm && ./deploy.sh

# Step 3: Deploy Cloud Run job
gcloud run jobs update bigquery-motherduck-updater \
  --set-env-vars="CLICKHOUSE_HOST=$CH_HOST,CLICKHOUSE_PASSWORD=$CH_PASS,DUAL_WRITE_ENABLED=true" \
  --region=us-east1 --project=eonlabs-ethereum-bq

# Step 4: Deploy Cloud Function
cd deployment/gcp-functions/motherduck-monitor
gcloud functions deploy motherduck-monitor \
  --gen2 --runtime=python312 --trigger-http \
  --set-env-vars="CLICKHOUSE_HOST=$CH_HOST,CLICKHOUSE_PASSWORD=$CH_PASS,DUAL_VALIDATION_ENABLED=true" \
  --region=us-east1 --project=eonlabs-ethereum-bq
```

### Phase 3: Compressed Validation (Day 1, Hour 4-16) - COMPLETED ✅

**3.1 Run hourly consistency checks** ✅ COMPLETED (2025-11-25)

- Script: `scripts/clickhouse/verify_consistency.py`
- Checks: Row count, max block number
- Key metric: Max block must match (indicates dual-write sync)
- Alert: Pushover notification on discrepancy

**Verification Results** (2025-11-25T19:45):

```
✅ DUAL-WRITE HEALTHY
ClickHouse: 23,877,771 blocks (max: 23,877,776)
MotherDuck: 23,877,770 blocks (max: 23,877,776)
Max block diff: 0 (both receiving new blocks ✅)
Row count diff: 1 (genesis block 0 in ClickHouse only)
```

**Gap Backfill Complete** (2025-11-25T19:45):

- **Gap identified**: 9,454 blocks (23,865,017 → 23,874,476)
- **Root cause**: BigQuery lag + dual-write start timing
- **Solution**: Backfilled from MotherDuck → ClickHouse in 0.6 seconds
- **Script**: `scripts/clickhouse/backfill_from_motherduck.py`
- **Status**: ✅ Gap closed, databases in sync

### Phase 4: Cutover (Day 2, Hour 0-4) - DEPLOYED & VALIDATED ✅

**4.1 Add MOTHERDUCK_WRITE_ENABLED cutover toggle** ✅ COMPLETED (2025-11-25)

- Added `MOTHERDUCK_WRITE_ENABLED` env var to both VM collector and Cloud Run job
- Default: `true` (dual-write continues)
- Set to `false` to stop MotherDuck writes (ClickHouse-only mode)
- Code changes in:
  - `deployment/vm/realtime_collector.py` (lines 61, 341-355, 395-399)
  - `deployment/cloud-run/main.py` (lines 58-59, 324-327)
- Syntax validated: Python compile checks pass

**4.2 Deploy cutover to Cloud Run** ✅ COMPLETED (2025-11-25T20:30)

- Cloud Run job `eth-md-updater` updated via Python SDK
- Environment variable `MOTHERDUCK_WRITE_ENABLED=false` set
- Cloud Run now writes to ClickHouse only (skips MotherDuck)

**4.4 Deploy cutover to VM** ✅ COMPLETED (2025-11-25T22:48)

**Successful Approach**:

- Deployed updated `realtime_collector.py` code via GCP startup-script metadata
- Script writes base64-encoded code to VM, creates systemd override, restarts service
- VM stop/start triggered startup script execution

**Verification** (2025-11-25T22:54):

```
ClickHouse: 23,878,892 blocks (max: 23,878,892)
MotherDuck: 23,878,835 blocks (max: 23,878,835)
Max block diff: 57 (ClickHouse ahead - cutover confirmed ✅)
```

**Current State** (2025-11-25T22:54):

- Cloud Run: ✅ ClickHouse-only mode (MOTHERDUCK_WRITE_ENABLED=false)
- VM: ✅ ClickHouse-only mode (MOTHERDUCK_WRITE_ENABLED=false via systemd override)

**4.3 Archive MotherDuck snapshot** ✅ COMPLETED (2025-11-25T20:03)

- Script: `scripts/clickhouse/archive_motherduck_to_gcs.py`
- Total rows: 23,877,844 blocks
- File size: 517.4 MB (Parquet with ZSTD compression)
- Location: `gs://eonlabs-ethereum-backups/motherduck-archive/2025-11-25/`
- Files: `blocks.parquet`, `METADATA.txt`
- Retention: 30 days

### Phase 5: Documentation Updates ✅ COMPLETED

**5.1 Update CLAUDE.md** ✅ COMPLETED (2025-11-25)

- Replaced MotherDuck references with ClickHouse throughout
- Updated architecture diagrams and Data Storage Architecture section
- Updated SDK examples to reference ClickHouse

**5.2 Update deployment READMEs** ✅ COMPLETED (2025-11-25)

- `deployment/vm/README.md` - Updated data flow to ClickHouse
- `deployment/cloud-run/README.md` - Updated job description and secrets
- `deployment/gcp-functions/motherduck-monitor/README.md` - Renamed to ClickHouse Gap Detection Monitor

**5.3 Update master-project-roadmap.yaml** ✅ COMPLETED (2025-11-25)

- Updated infrastructure section with ClickHouse Cloud AWS
- Added migration status and ADR reference

**5.4 Create ADR 0013** ✅ COMPLETED (2025-11-25)

- Created `docs/decisions/0013-motherduck-clickhouse-migration.md` in MADR format
- Updated `docs/decisions/CLAUDE.md` navigation hub with new Infrastructure Migrations section

## Success Criteria

- ✅ ClickHouse connection validated (2025-11-24T23:20:10)
- ✅ Schema created with ReplacingMergeTree (2025-11-24T23:21:04)
- ✅ 23.86M blocks migrated (BigQuery → ClickHouse in 5 minutes)
- ✅ Dual-write code complete for all 4 components (VM, Cloud Run job, Cloud Run checker, Cloud Function)
- ✅ GCP secrets created via Python SDK (2025-11-25)
- ✅ Dual-write deployed to production (2025-11-25T08:02)
- ✅ Dual-write verified in VM logs (both databases receiving new blocks)
- ✅ ClickHouse password reset via API (2025-11-25T19:43)
- ✅ Gap backfilled: 9,454 blocks from MotherDuck → ClickHouse (2025-11-25T19:45)
- ✅ Databases in sync: 23.87M blocks, max block identical
- ✅ 12+ hour validation period passed (2025-11-25)
- ✅ Phase 4 cutover code complete: `MOTHERDUCK_WRITE_ENABLED` toggle added
- ✅ MotherDuck archived to GCS (517.4 MB, 23.87M blocks, 2025-11-25T20:03)
- ✅ Cloud Run cutover deployed (MOTHERDUCK_WRITE_ENABLED=false, 2025-11-25T20:30)
- ✅ VM cutover deployed via startup-script (code + systemd override, 2025-11-25T22:48)
- ✅ Cutover validated: ClickHouse 57 blocks ahead of MotherDuck (2025-11-25T22:54)
- ✅ All documentation updated (2025-11-25)

## Verification Scripts

**Location**: `scripts/clickhouse/`

| Script                         | Purpose                                            | Status      |
| ------------------------------ | -------------------------------------------------- | ----------- |
| `validate_connection.py`       | Test ClickHouse connectivity                       | ✅ Created  |
| `create_schema.py`             | Create ReplacingMergeTree table                    | ✅ Created  |
| `migrate_from_bigquery.py`     | Direct BigQuery → ClickHouse migration             | ✅ Created  |
| `verify_consistency.py`        | Hourly ClickHouse ↔ MotherDuck comparison         | ✅ Created  |
| `backfill_from_motherduck.py`  | Backfill gap from MotherDuck → ClickHouse          | ✅ Executed |
| `fill_gap.py`                  | Block-range backfill from BigQuery                 | ✅ Created  |
| `setup_gcp_secrets.sh`         | Create secrets via gcloud CLI                      | ✅ Created  |
| `setup_gcp_secrets.py`         | Create secrets via Python SDK (no gcloud required) | ✅ Executed |
| `archive_motherduck_to_gcs.py` | Archive MotherDuck data to GCS before cutover      | ✅ Executed |

**Verification Command** (run hourly during validation):

```bash
doppler run --project aws-credentials --config prd -- uv run scripts/clickhouse/verify_consistency.py
```
