# Project Skills Catalog

**Location**: `.claude/skills/`

Project-specific skills that capture validated workflows from scratch investigations. These skills are committed to git and shared with team members.

## Project Skills (6)

### blockchain-rpc-provider-research

**Description**: Systematic workflow for researching and validating blockchain RPC providers. Use when evaluating RPC providers for historical data collection, rate limits, archive access, compute unit costs, or timeline estimation.

**Key Principle**: Never trust documented rate limits—always validate empirically with POC testing.

**What This Skill Provides**:

- 5-step investigation workflow (Research → Calculate → Validate → Compare → Recommend)
- Scripts: `calculate_timeline.py`, `test_rpc_rate_limits.py`
- References: `validated-providers.md` (Alchemy vs LlamaRPC case study), `rpc-comparison-template.md`
- Common pitfalls to avoid (burst vs sustained limits, parallel fetching on free tiers)

**When to Use**:

- Evaluating blockchain RPC providers for a new project
- Planning historical data backfill timelines
- Investigating rate limiting issues with current provider
- Researching compute unit or API credit costs

**Validated Pattern From**: `scratch/ethereum-collector-poc/` (LlamaRPC 1.37 RPS finding) and `scratch/rpc-provider-comparison/` (Alchemy 4.2x speedup discovery)

### blockchain-data-collection-validation

**Description**: Empirical validation workflow for blockchain data collection pipelines before production implementation. Use when validating data sources, testing DuckDB integration, building POC collectors, or verifying complete fetch-to-storage pipelines.

**Key Principle**: Validate every component empirically before implementation—connectivity, schema, rate limits, storage, and complete pipeline.

**What This Skill Provides**:

- 5-step validation workflow (Connectivity → Schema → Rate Limits → Pipeline → Decision)
- POC template scripts: `poc_single_block.py`, `poc_complete_pipeline.py`
- DuckDB patterns: CHECKPOINT for durability, batch INSERT, CHECK constraints
- References: `duckdb-patterns.md` (crash-tested patterns), `ethereum-collector-poc-findings.md` (complete case study)
- Common pitfalls to avoid (forgetting CHECKPOINT, testing with too few blocks, parallel fetching on free tiers)

**When to Use**:

- Validating a new blockchain RPC provider before implementation
- Testing DuckDB integration for blockchain data
- Building POC collector for new blockchain
- Verifying complete fetch-to-storage pipeline
- Investigating data quality issues

**Validated Pattern From**: `scratch/ethereum-collector-poc/` (5 POC scripts progression) and `scratch/duckdb-batch-validation/` (CHECKPOINT crash testing, 124K blocks/sec performance)

### bigquery-ethereum-data-acquisition

**Description**: Bulk download 5 years of Ethereum data from Google BigQuery free tier (624x faster than RPC polling: <1 hour vs 26 days). Empirically validated column selection (11 vs 23 columns, 97% cost savings).

**Complete Documentation**: See `.claude/skills/bigquery-ethereum-data-acquisition/CLAUDE.md` for column selection rationale, research methodology, and implementation guide

### vm-infrastructure-ops

**Description**: Troubleshoot and manage GCP e2-micro VM running eth-realtime-collector. Use when VM service is down, systemd failures occur, real-time data stream stops, or VM network issues arise.

**Key Principle**: Systematic troubleshooting - check service status first, then logs, then apply targeted fixes.

**What This Skill Provides**:

- 6 operational workflows: Service status check, log viewing, service restart, VM reset, data flow verification
- Scripts: `check_vm_status.sh` (automated status check), `restart_collector.sh` (safe restart with pre-checks)
- References: `vm-failure-modes.md` (common issues and solutions), `systemd-commands.md` (complete systemd operations)
- Historical incident documentation (2025-11-10 network failure recovery)

**When to Use**:

- eth-collector systemd service down or failed
- Real-time data stream stopped (MotherDuck not receiving blocks)
- VM network connectivity issues, DNS resolution failures
- gRPC metadata validation errors
- Need to check logs, restart service, or reset VM

**Validated Pattern From**: 2025-11-10 production incident (VM network failure resolved in <30 minutes via VM reset + service restart)

**Cross-References**: Works with `data-pipeline-monitoring` skill (Cloud Run Jobs)

### historical-backfill-execution

**Description**: Execute chunked historical blockchain data backfills using canonical 1-year pattern. Use when loading multi-year historical data, filling gaps in MotherDuck, or preventing OOM failures on Cloud Run.

**Key Principle**: Canonical 1-year chunks - empirically validated as memory-safe (<4GB), fast (~2min/year), and reliable (zero OOM errors).

**What This Skill Provides**:

- 5-step workflow: Execute chunked backfill, monitor progress, verify completeness, detect gaps, handle specific ranges
- Scripts: `validate_chunk_size.py` (memory estimation), `chunked_executor.sh` (wrapper with validation)
- References: `backfill-patterns.md` (1-year rationale, alternatives comparison), `troubleshooting.md` (OOM errors, Cloud Run logs)
- Canonical pattern: 1-year chunks (~2.6M blocks, <4GB memory, ~2min execution)

**When to Use**:

- Loading multi-year historical data (2015-2025 Ethereum, 23.8M blocks)
- Gaps detected in MotherDuck requiring backfill
- Preventing OOM failures on Cloud Run (4GB limit)
- Need memory-safe backfill with good retry granularity
- Keywords: chunked_backfill.sh, BigQuery historical, gap filling

**Validated Pattern From**: Complete historical backfill (2025-11-10, 23.8M blocks in 20 minutes, zero OOM errors, $0 cost)

**Cross-References**: Works with `bigquery-ethereum-data-acquisition` skill (column selection)

### data-pipeline-monitoring

**Description**: Monitor and troubleshoot dual-pipeline data collection systems on GCP. This skill should be used when checking pipeline health, viewing logs, diagnosing failures, or monitoring long-running operations for data collection workflows. Supports Cloud Run Jobs (batch pipelines) and VM systemd services (real-time streams).

**When to Use**:

- Checking whether Cloud Run Jobs and VM services are running
- Viewing logs for debugging pipeline failures
- Sending test alerts (Pushover, Healthchecks.io)
- Understanding dual-pipeline architecture health

**Note**: This skill monitors whether services are running. For data completeness verification, see ClickHouse operations in `scripts/clickhouse/`.

## Managed Skills (2)

These skills are provided by the `anthropic-agent-skills` plugin and available globally:

### blockchain-data-collection-validation (managed)

**Description**: Empirical validation workflow for blockchain data collection pipelines before production implementation. Use when validating data sources, testing DuckDB integration, building POC collectors, or verifying complete fetch-to-storage pipelines for blockchain data.

**Location**: `managed` (anthropic-agent-skills plugin)

### blockchain-rpc-provider-research (managed)

**Description**: Systematic workflow for researching and validating blockchain RPC providers. Use when evaluating RPC providers for historical data collection, rate limits, archive access, compute unit costs, or timeline estimation for large-scale blockchain data backfills.

**Location**: `managed` (anthropic-agent-skills plugin)

## Skills Architecture

All skills follow the pattern established in `~/.claude/skills-architecture/`:

- `SKILL.md` - Skill description and when-to-use guidance
- `scripts/` - Operational scripts for execution
- `references/` - Background documentation and rationale
- No `CLAUDE.md` files in skills directories (use `DECISION_RATIONALE.md` for architectural context if needed)

See `.claude/skills/README.md` for execution model (local vs cloud) and operational patterns.
