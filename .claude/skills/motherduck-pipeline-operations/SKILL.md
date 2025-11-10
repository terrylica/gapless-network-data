---
name: motherduck-pipeline-operations
description: This skill should be used when verifying MotherDuck database state, executing historical backfills for Ethereum blockchain data, or troubleshooting missing historical data. Use when user mentions MotherDuck verification, chunked backfill execution, or questions about why historical data is missing despite pipeline health checks showing systems are operational.
---

# MotherDuck Pipeline Operations

## Overview

This skill provides operations for managing the Ethereum blockchain data pipeline that populates MotherDuck cloud database. It addresses the common confusion between pipeline health monitoring (covered by data-pipeline-monitoring skill) and actual data completeness verification, and provides the canonical 1-year chunked backfill pattern for safe historical data loading.

## Core Operations

### 1. Verify MotherDuck Database State

To check the actual state of data in MotherDuck (not just pipeline health), use the verification script:

```bash
cd /Users/terryli/eon/gapless-network-data/.claude/skills/motherduck-pipeline-operations
uv run scripts/verify_motherduck.py
```

This script:
- Connects to MotherDuck `ethereum_mainnet.blocks` table
- Reports total block count, block range, time range
- Provides yearly breakdown for multi-million block datasets
- Validates against expected range (13-15M blocks for 2020-2025 backfill)

**When to use**: When user asks about data completeness, historical data availability, or suspects missing blocks despite healthy pipeline status.

### 2. Execute Chunked Historical Backfill

For loading multi-year historical data, use the canonical 1-year chunking pattern to avoid OOM failures:

```bash
cd /Users/terryli/eon/gapless-network-data/deployment/backfill
./chunked_backfill.sh <START_YEAR> <END_YEAR>
```

**Example**: `./chunked_backfill.sh 2020 2025` executes 5 chunks: 2020, 2021, 2022, 2023, 2024-2025

**Pattern Details**:
- Chunk size: 1 year (~2.6M blocks, ~1.5-2GB memory)
- Execution time: ~1m40s-2m per chunk
- Memory safety: Fits comfortably within 4GB Cloud Run limit
- Idempotency: Uses `INSERT OR REPLACE` - safe to re-run

**When to use**: When executing initial 5-year backfill, or future 6-8+ year backfills as blockchain grows.

### 3. Troubleshoot Missing Historical Data

**Common Scenario**: User reports "No historical data despite monitoring showing pipelines are healthy"

**Root Cause**: Understanding dual-pipeline architecture is critical:
- Cloud Run `eth-md-updater`: Hourly sync of **last 2 hours only** (NOT historical)
- VM `eth-realtime-collector`: Real-time streaming of **new blocks only** (NOT historical)
- Historical backfill: **Separate one-time operation** (often never executed)

**Resolution Workflow**:
1. Verify actual database state: `uv run scripts/verify_motherduck.py`
2. If missing historical blocks, execute chunked backfill (Operation #2)
3. After backfill, verify again to confirm 13-15M blocks loaded

**Key Insight**: Pipeline health checks do NOT verify data completeness - use verification script instead.

## Understanding the Architecture

The Ethereum data pipeline uses three separate components:

1. **Cloud Run Job: eth-md-updater** (Incremental Sync)
   - Hourly updates of last 2 hours
   - Does NOT perform historical backfill

2. **VM: eth-realtime-collector** (Real-Time Streaming)
   - Real-time block collection (~12s intervals)
   - Only forward-going blocks, no historical data

3. **Cloud Run Job: ethereum-historical-backfill** (One-Time Backfill)
   - Manual execution with START_YEAR/END_YEAR parameters
   - Uses 1-year chunking to avoid OOM

For detailed architecture explanation and additional troubleshooting scenarios, refer to `references/pipeline-architecture-and-troubleshooting.md`.

## Resources

### scripts/verify_motherduck.py
Python script to verify MotherDuck database state. Checks actual data completeness, not just pipeline health.

### references/pipeline-architecture-and-troubleshooting.md
Comprehensive documentation covering:
- Dual-pipeline architecture details
- Common troubleshooting scenarios
- OOM failure solutions
- Chunked backfill performance benchmarks

### Canonical Backfill Script
Located at `deployment/backfill/chunked_backfill.sh` in the project repository. Provides automated 1-year chunking for multi-year historical loads.
