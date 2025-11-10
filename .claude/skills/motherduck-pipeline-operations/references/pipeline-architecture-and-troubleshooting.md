# MotherDuck Pipeline Architecture & Troubleshooting

## Dual-Pipeline Architecture

The Ethereum data pipeline uses **three separate components** to populate MotherDuck:

### 1. Cloud Run Job: eth-md-updater (Incremental Sync)
- **Purpose**: Hourly incremental updates (last 2 hours of blocks)
- **Location**: Cloud Run (us-east1)
- **Schedule**: Every hour
- **Data source**: BigQuery public dataset
- **Key point**: Does NOT perform historical backfill

### 2. VM: eth-realtime-collector (Real-Time Streaming)
- **Purpose**: Real-time block collection (~12s intervals)
- **Location**: GCE VM (us-east1-b)
- **Service**: systemd eth-collector.service
- **Data source**: Ethereum RPC (LlamaRPC)
- **Key point**: Only collects forward-going blocks, no historical data

### 3. Cloud Run Job: ethereum-historical-backfill (One-Time Backfill)
- **Purpose**: One-time historical data loading (2020-2025)
- **Location**: Cloud Run (us-central1)
- **Execution**: Manual, parameterized by START_YEAR/END_YEAR
- **Data source**: BigQuery public dataset
- **Key point**: Uses 1-year chunking to avoid OOM failures

## Common Troubleshooting Scenarios

### Problem: No Historical Data in MotherDuck

**Symptoms**:
- MotherDuck shows only recent blocks (e.g., 7,420 blocks from last 2 days)
- Expected ~14.5M blocks for 2020-2025 backfill

**Root Cause**:
- Neither Cloud Run hourly sync nor VM real-time collector performs historical backfill
- Historical backfill Cloud Run Job was never executed

**Solution**:
1. Verify database state: `uv run scripts/verify_motherduck.py`
2. Execute chunked backfill: See deployment/backfill/chunked_backfill.sh

### Problem: Cloud Run Job OOM Failure (Exit Code 137)

**Symptoms**:
- Job execution shows "Container called exit(137)"
- Logs show successful fetch but failure during MotherDuck INSERT
- Memory limit: 4GB

**Root Cause**:
- Attempting to load too many blocks in single execution (e.g., 5 years = 12.3M blocks)
- PyArrow table + DuckDB operations exceed 4GB memory

**Solution**:
- Use 1-year chunks (~2.6M blocks each, ~1.5-2GB peak memory)
- Canonical pattern: `deployment/backfill/chunked_backfill.sh`

### Problem: Distinguishing Pipeline Responsibilities

**Question**: "Why is there no historical data despite monitoring skills showing pipelines are healthy?"

**Answer**:
- Cloud Run `eth-md-updater`: Hourly sync of **last 2 hours** only
- VM `eth-realtime-collector`: Real-time streaming of **new blocks** only
- Historical backfill: **Separate one-time operation**, not monitored by data-pipeline-monitoring skill

**Verification**:
- Use `scripts/verify_motherduck.py` to check actual database state
- Don't rely solely on pipeline health checks for data completeness

## Chunked Backfill Pattern (Canonical)

**Rationale**: 1-year chunks prevent OOM failures and establish safe pattern for future 6-8+ year backfills.

**Performance** (empirically validated 2025-11-10):
- 2020: 2.37M blocks in 1m51s
- 2021: 2.35M blocks in 1m57s
- 2022: 2.34M blocks in 1m47s
- 2023: 2.65M blocks in 1m47s
- 2024-2025: 4.86M blocks in 1m39s

**Memory Usage**: Each 1-year chunk uses ~1.5-2GB peak (safely within 4GB Cloud Run limit)

**Idempotency**: Uses `INSERT OR REPLACE` - safe to re-run chunks

**Future Use**: Template established for 6, 7, 8+ year backfills as Ethereum blockchain grows
