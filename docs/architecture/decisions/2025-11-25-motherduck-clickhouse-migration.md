# MotherDuck to ClickHouse Cloud Migration

## Status

Accepted

## Date

2025-11-25

## Context

MotherDuck trial ending in 2-3 days required migration of 23.87M Ethereum blocks and 4 production pipeline components to a sustainable database solution.

**Production Data**:

- 23.87M Ethereum blocks (2015-2025)
- ~1.5 GB storage (76-100 bytes/block)
- Dual-pipeline architecture: BigQuery hourly batch (578 blocks/run) + Alchemy real-time (12s intervals)

**Infrastructure Components**:
| Component | Purpose |
|-----------|---------|
| VM Real-Time Collector | Alchemy WebSocket subscription for new blocks |
| Cloud Run Batch Updater | BigQuery hourly sync for redundancy |
| Data Quality Checker | Freshness validation (16-minute threshold) |
| Gap Monitor Function | 3-hour gap detection with Pushover alerts |

**Constraints**:

- Zero downtime requirement
- 2-3 days to trial expiration
- Exception-only failure policy (no silent errors)
- Cost optimization (free tier preferred)

## Decision

Migrate from MotherDuck to ClickHouse Cloud (managed AWS) using dual-write strategy with environment variable toggles for safe rollback.

**Target Architecture**:

- **Database**: ClickHouse Cloud (managed AWS, us-east-1)
- **Engine**: ReplacingMergeTree (automatic deduplication on block number)
- **Credentials**: GCP Secret Manager (`clickhouse-host`, `clickhouse-password`)
- **Cutover Toggle**: `MOTHERDUCK_WRITE_ENABLED` environment variable

**Migration Strategy**:

1. Historical migration: BigQuery → ClickHouse (direct, 5 minutes)
2. Dual-write deployment: Both databases active during validation
3. Compressed validation: 12+ hours of parallel writes
4. Cutover: Toggle `MOTHERDUCK_WRITE_ENABLED=false`
5. Archive: MotherDuck snapshot to GCS (30-day retention)

## Consequences

**Positive**:

- Sustainable production database (no trial expiration)
- ReplacingMergeTree eliminates manual deduplication logic
- ClickHouse Cloud handles infrastructure management
- GCS archive provides emergency rollback path

**Negative**:

- Additional cloud provider (AWS) alongside GCP
- ClickHouse-specific query syntax differences
- Migration required code changes to 4 components

**Risks Mitigated**:

- Safe rollback via dual-write and environment toggles
- 12+ hour validation period before cutover
- GCS archive for 30-day emergency recovery

## Implementation

**Migration Plan**: [ClickHouse Migration Plan](/docs/development/plan/2025-11-25-motherduck-clickhouse-migration/plan.md)

**Scripts**: `scripts/clickhouse/`

- `validate_connection.py` - Connection validation
- `create_schema.py` - ReplacingMergeTree table creation
- `migrate_from_bigquery.py` - Historical migration (23.87M blocks in 5 min)
- `verify_consistency.py` - Cross-database comparison
- `backfill_from_motherduck.py` - Gap backfill
- `archive_motherduck_to_gcs.py` - GCS archival

**Archive Location**: `gs://eonlabs-ethereum-backups/motherduck-archive/2025-11-25/`

## References

- ClickHouse ReplacingMergeTree: https://clickhouse.com/docs/en/engines/table-engines/mergetree-family/replacingmergetree
- MotherDuck Archive: `gs://eonlabs-ethereum-backups/motherduck-archive/2025-11-25/`
