# MADR-0013: MotherDuck to ClickHouse AWS Migration

**Status**: Accepted

**Date**: 2025-11-24

**Related**: Plan 0013 (`docs/development/plan/0013-motherduck-clickhouse-migration/plan.md`)

## Context

MotherDuck trial ending requires migration to alternative cloud database. Current production infrastructure:

**Data Volume**:

- 23.84M Ethereum blocks (~1.5 GB)
- Dual-pipeline architecture (BigQuery hourly + Alchemy real-time WebSocket)
- Zero-gap guarantee via INSERT OR REPLACE deduplication

**Production Components** (4 requiring migration):

1. VM Real-Time Collector (`deployment/vm/realtime_collector.py`)
2. Cloud Run Batch Updater (`deployment/cloud-run/main.py`)
3. Cloud Run Data Quality Checker (`deployment/cloud-run/data_quality_checker.py`)
4. GCP Cloud Function Gap Monitor (`deployment/gcp-functions/motherduck-monitor/main.py`)

**Constraints**:

- Trial expires in 2-3 days (URGENT)
- Zero downtime required
- Existing ClickHouse Cloud AWS provisioned (untested)
- Credentials available in Doppler (`aws-credentials/prd`)

## Decision

Migrate from MotherDuck to ClickHouse Cloud (AWS) using dual-write strategy with compressed 2.5-day timeline.

**Database**: ClickHouse Cloud (managed AWS us-east-1)

**Python Client**: `clickhouse-connect` (official HTTP client, automatic connection pooling)

**Deduplication Strategy**: ReplacingMergeTree engine with `number` as ORDER BY key

**Migration Strategy**: Dual-write (both databases active during migration)

**Error Policy**: Fail-fast (exception-only, aligns with project SLO)

**Validation Period**: 6-12 hours compressed (vs standard 72 hours)

## Consequences

**Positive**:

- Maintains zero-downtime requirement
- Safe rollback at every stage (MotherDuck continues receiving writes)
- Fail-fast policy ensures immediate alerts if ClickHouse writes fail
- ClickHouse provides superior analytical performance (10-100x for complex queries)

**Negative**:

- Cost increase: $0/month → estimated $50-300/month (ClickHouse Cloud)
- Compressed validation increases bug risk
- No MotherDuck backup (user decision: trust migration)
- Code complexity during dual-write phase

**Risks**:

- ClickHouse connection failure during migration (Mitigation: validate connection FIRST)
- Trial expires mid-migration (Mitigation: complete historical load Day 0)
- Dual-write consistency issues (Mitigation: hourly verification checks)

## Alternatives Considered

### Alternative 1: Direct Export-Import Cutover

**Rejected**: Requires 15-30 minute downtime, violates zero-downtime requirement

### Alternative 2: Local DuckDB on GCP VM

**Kept as Fallback**: If ClickHouse validation fails, emergency pivot to local DuckDB file storage

### Alternative 3: Extend MotherDuck Trial

**Not Pursued**: Uncertain outcome, doesn't solve long-term database requirement

## Implementation

See Plan 0013 for detailed 2.5-day timeline and task breakdown.

**Critical Path**:

1. Day 0: Validate ClickHouse → Historical migration (23.84M blocks)
2. Day 1: Deploy dual-write → Compressed validation (6-12 hours)
3. Day 2: Read cutover → MotherDuck deprecation
