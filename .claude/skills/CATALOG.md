# Project Skills Catalog

**Location**: `.claude/skills/`

Project-specific skills that capture validated workflows from scratch investigations. These skills are committed to git and shared with team members.

## Project Skills (5)

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

### motherduck-pipeline-operations

**Description**: Operations for managing the Ethereum blockchain data pipeline that populates MotherDuck cloud database. Use when verifying MotherDuck database state, executing historical backfills, or troubleshooting missing historical data despite pipeline health checks showing systems are operational.

**Key Principle**: Pipeline health monitoring (whether services are running) is separate from data completeness verification (whether historical data exists in MotherDuck).

**What This Skill Provides**:

- 3 core operations: Verify database state, Execute chunked backfill, Troubleshoot missing data
- Scripts: `verify_motherduck.py` (database verification)
- References: `pipeline-architecture-and-troubleshooting.md` (dual-pipeline architecture, common failure modes)
- Canonical pattern: 1-year chunked backfills to prevent OOM failures (empirically validated 2025-11-10)

**When to Use**:

- Verifying actual MotherDuck database state (block counts, historical data presence)
- Executing historical backfills for Ethereum blockchain data
- Troubleshooting "No historical data despite healthy pipelines" scenarios
- Understanding dual-pipeline architecture responsibilities

**Validated Pattern From**: Complete historical backfill execution (23.8M blocks, 2015-2025) using `deployment/backfill/chunked_backfill.sh`

**Cross-References**: Works with `data-pipeline-monitoring` skill (pipeline health) and `bigquery-ethereum-data-acquisition` skill (BigQuery → MotherDuck workflow)

### data-pipeline-monitoring

**Description**: Monitor and troubleshoot dual-pipeline data collection systems on GCP. This skill should be used when checking pipeline health, viewing logs, diagnosing failures, or monitoring long-running operations for data collection workflows. Supports Cloud Run Jobs (batch pipelines) and VM systemd services (real-time streams).

**When to Use**:

- Checking whether Cloud Run Jobs and VM services are running
- Viewing logs for debugging pipeline failures
- Sending test alerts (Pushover, Healthchecks.io)
- Understanding dual-pipeline architecture health

**Note**: This skill monitors whether services are running. For verifying actual data completeness in MotherDuck, use `motherduck-pipeline-operations` skill.

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
