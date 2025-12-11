# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gapless Network Data is a multi-chain blockchain network metrics collection tool with zero-gap guarantee. Designed for feature engineering in cryptocurrency trading and ML pipelines.

**Core Capability**: Collect complete historical blockchain network data with high-frequency granularity:

- **Ethereum** (PRIMARY): Block-level data via Alchemy real-time stream (~12 second intervals, 23.87M blocks operational) <!-- Verified 2025-11-25 via ClickHouse: 23,877,845 blocks -->
- **Bitcoin**: Mempool snapshots via mempool.space (5-minute intervals, future work)
- **Multi-chain**: Extensible to Solana, Avalanche, Polygon, etc.

**Version**: v5.1.0 (production operational)

## Data Scope

**What This Package IS For**: On-chain network metrics

- Bitcoin mempool pressure (fee rates, transaction counts, mempool size)
- Ethereum gas prices (base fee, priority fee, gas used, block utilization)
- Blockchain block-level data (timestamps, transaction counts, network congestion)
- Network health metrics (TPS, block times, resource utilization)

**What This Package IS NOT For**: Exchange price data

- ❌ OHLCV candles (Open, High, Low, Close, Volume)
- ❌ Exchange order book data
- ❌ Trading pair prices from centralized exchanges (Binance, Coinbase, Kraken)
- ❌ DEX token prices (unless coupled with network metrics like gas spent)

**Rationale**: Network metrics measure blockchain health and congestion, which directly impacts transaction success rates, confirmation times, and operational costs. Price data alone does not capture these operational characteristics.

## Referential Implementation

**This package follows architectural patterns from [gapless-crypto-data](https://github.com/terrylica/gapless-crypto-data)**, the OHLCV data collection package that serves as the referential implementation for:

- SDK quality standards (PEP 561 compliance, structured exceptions, AI discoverability)
- Validation pipeline architecture (5-layer validation)
- Documentation patterns (hub-and-spoke, version tracking, SLO framework)
- API design (function-based API, DatetimeIndex output, exception-only failures)
- Development toolchain (uv, pytest, ruff, mypy)

**Architectural Separation Rationale**: These packages are intentionally separate due to fundamental data model incompatibilities:

- **gapless-crypto-data**: OHLCV 11-column format, interval-based time series, price/volume metrics
- **gapless-network-data**: Variable schema, point-in-time snapshots, network congestion metrics

These packages are kept separate to avoid data model conflicts (different schemas, different time semantics).

## Single Source of Truth (SSoT)

**Master Plan**: `./specifications/master-project-roadmap.yaml`

Coordinates all project phases, specifications, and implementation work.

**Architecture**: OpenAPI 3.1.1 machine-readable format with logical dependencies

**Archived Specifications** (in `archive/` folder):

- `archive/motherduck-integration.yaml` - MotherDuck dual pipeline (deprecated 2025-11-25, migrated to ClickHouse)
- `archive/core-collection-phase1.yaml` - Bitcoin-only Phase 1 (superseded 2025-11-04, archived)

**Current Status**:

- **Phase**: Phase 1 (Historical Data Collection: Complete History) - **COMPLETED** (2025-11-25)
- **Version**: v4.3.1 (production operational)
- **Data Loaded**: 23.87M Ethereum blocks (2015-2025) in ClickHouse Cloud <!-- Verified 2025-11-25: 23,877,845 blocks -->
- **Architecture**: Dual-pipeline (Alchemy WebSocket VM + BigQuery hourly Cloud Run Job) → ClickHouse
- **Monitoring**: Healthchecks.io + Pushover (cloud-based, UptimeRobot removed)
- **Authoritative Spec**: `./specifications/master-project-roadmap.yaml` Phase 1
- **Validation**: Empirical validation complete - see `./scratch/README.md` and `./scratch/ethereum-collector-poc/ETHEREUM_COLLECTOR_POC_REPORT.md`

**Key Decisions Logged**:

1. Architecture: ClickHouse Cloud (AWS) for production storage (2025-11-25, operational)
2. Data Sources: BigQuery public dataset (historical) + Alchemy WebSocket (real-time) - rejected LlamaRPC due to rate limits (2025-11-10)
3. Separate databases for gapless-crypto-data and gapless-network-data (9-2 score)
4. ASOF JOIN as P0 feature (prevents data leakage, 16x faster)
5. Ethereum PRIMARY, Bitcoin SECONDARY (12s vs 5min granularity)
6. Monitoring: Cloud-based only (Healthchecks.io Dead Man's Switch, Pushover alerts)
7. Database Migration: MotherDuck → ClickHouse (2025-11-25, trial expiration driven)

## Quick Navigation

### Architecture

- [Architecture Overview](/docs/architecture/README.md) - Core components, data flow, SLOs
- [Data Format Specification](/docs/architecture/DATA_FORMAT.md) - Mempool snapshot schema

### Usage Guides

- [Data Collection Guide](/docs/guides/DATA_COLLECTION.md) - CLI usage, collection modes (pending)
- [Python API Reference](/docs/guides/python-api.md) - `fetch_snapshots()`, `get_latest_snapshot()` (pending)
- [Feature Engineering Guide](/docs/guides/FEATURE_ENGINEERING.md) - Temporal alignment, feature fusion (pending)

### Validation System

- [Validation Overview](/docs/validation/OVERVIEW.md) - 5-layer validation pipeline (pending)
- [ValidationStorage Specification](/docs/validation/STORAGE.md) - Parquet-backed validation reports (pending)

### Development

- Development Setup - Environment setup (pending)
- Development Commands - Testing, linting, build (pending)
- Publishing Guide - PyPI publishing workflow (pending)

### Data Sources

**Production**: BigQuery (historical) + Alchemy (real-time) → ClickHouse Cloud (AWS)

**Complete Documentation**: See [Data Sources](/docs/research/data-sources.md) for production sources, rejected alternatives (LlamaRPC: 1.37 RPS sustained vs 50 RPS documented), and future multi-chain plans.

## ClickHouse Integration

**Status**: Operational - Dual-pipeline (BigQuery hourly + Alchemy real-time) → ClickHouse Cloud (AWS) with ReplacingMergeTree automatic deduplication

**Migration**: MotherDuck → ClickHouse completed 2025-11-25 (trial expiration driven). See `docs/development/plan/2025-11-25-motherduck-clickhouse-migration/plan.md` for migration details.

**Operations**:

- **VM Management**: Use `vm-infrastructure-ops` skill for service restarts, log viewing, troubleshooting
- **Database Operations**: Use `clickhouse-connect` Python SDK for queries and verification
- **Credentials**: Doppler `aws-credentials/prd` → ClickHouse host/password

**Monitoring**: Gap detection runs every 3 hours via GCP Cloud Functions (consistency checks, Pushover + Healthchecks.io alerts)

**Connection**:

```python
import clickhouse_connect
client = clickhouse_connect.get_client(
    host=os.environ['CLICKHOUSE_HOST'],
    port=8443,
    username='default',
    password=os.environ['CLICKHOUSE_PASSWORD'],
    secure=True
)
result = client.query('SELECT COUNT(*) FROM ethereum_mainnet.blocks FINAL')
```

## Project Skills

**Skills**: 6 project skills + 2 managed skills (blockchain RPC research, data collection validation, BigQuery acquisition, ClickHouse operations, pipeline monitoring, VM infrastructure ops)

**Complete Catalog**: See [Skills Catalog](/.claude/skills/CATALOG.md) for descriptions, when-to-use guidance, and validated patterns from scratch investigations.

## Project Scope

**Primary Use Case**: Blockchain network metrics infrastructure (operational)

**Operational (v3.0.0)**:

- **Ethereum Block Data Collection**: 23.87M blocks (2015-2025) via dual-pipeline architecture
- **Infrastructure**: Alchemy WebSocket → ClickHouse Cloud (AWS)
- **Monitoring**: Healthchecks.io, Pushover
- **Purpose**: Network metrics for ML feature engineering pipelines

**Python SDK (v3.0.0)**:

- **Alpha Features API**: `fetch_blocks()` with ranked features for ML pipelines
- **AI Discoverability**: `probe` module with `get_alpha_features()`, `get_protocol_eras()`, `get_setup_workflow()`
- **LLM Integration**: `llms.txt` for Claude Code CLI consumption

**Future Work**:

- **Bitcoin Integration**: mempool.space data collection (experimental code exists)
- **Package Distribution**: pip install (not yet published to PyPI)

**Current Focus**: SDK alpha features API operational. Infrastructure maintenance ongoing.

## SDK Quality Standards

**Intended Use Case**: Programmatic API consumption by downstream packages and AI coding agents

**Implementation Status**: v3.0.0 - Production API with alpha features optimized for AI agents

**Key Abstractions**:

- **Type Safety**: PEP 561 compliance via py.typed marker (implemented)
- **AI Discoverability**: llms.txt, probe module (implemented v3.0.0)
- **Structured Exceptions**: Machine-parseable error context with timestamp, endpoint, HTTP status (implemented)
- **Coverage Strategy**: SDK entry points (85%+), Core engines (70%+) (pending)

## Alpha Features API

**Purpose**: Opinionated API for financial time series forecasting with Ethereum block data.

**Design Decision**: ADR `docs/architecture/decisions/2025-11-28-alpha-features-api.md`

### Quick Start

```python
import gapless_network_data as gmd

# Fetch latest blocks (recommended for live trading)
df = gmd.fetch_blocks(limit=1000)

# Compute block utilization (alpha feature #2)
df['utilization'] = df['gas_used'] / df['gas_limit']

# Date range query (inclusive [start, end])
# Returns all blocks from Jan 1 through Jan 31 (both dates included)
df = gmd.fetch_blocks(start='2024-01-01', end='2024-01-31')

# Same-day query (returns all blocks on March 13)
df = gmd.fetch_blocks(start='2024-03-13', end='2024-03-13')

# Include deprecated fields (pre-Merge analysis only)
df = gmd.fetch_blocks(include_deprecated=True)
```

### Alpha Feature Rankings

AI agents should prioritize these features for ML pipelines:

| Rank | Feature           | Importance | Formula              |
| ---- | ----------------- | ---------- | -------------------- |
| 1    | base_fee_per_gas  | critical   | raw                  |
| 2    | block_utilization | critical   | gas_used / gas_limit |
| 3    | transaction_count | high       | raw                  |
| 4    | timestamp         | high       | raw                  |
| 5    | number            | high       | raw                  |
| 6    | size              | medium     | raw                  |
| 7    | blob_gas_used     | medium     | raw (post-EIP4844)   |
| 8    | excess_blob_gas   | low        | raw (post-EIP4844)   |
| 9    | gas_limit         | low        | raw                  |
| 10   | gas_used          | low        | raw                  |

Get rankings programmatically: `gmd.probe.get_alpha_features()`

### Protocol Era Boundaries

| Era       | Block      | Date     | Impact                      |
| --------- | ---------- | -------- | --------------------------- |
| EIP-1559  | 12,965,000 | Aug 2021 | base_fee_per_gas introduced |
| The Merge | 15,537,394 | Sep 2022 | difficulty=0 forever        |
| EIP-4844  | 19,426,587 | Mar 2024 | blob_gas fields introduced  |

Get eras programmatically: `gmd.probe.get_protocol_eras()`

### Deprecated Features

Excluded by default (use `include_deprecated=True` for pre-Merge analysis):

- `difficulty`: Always 0 post-Merge (Sep 2022)
- `total_difficulty`: Frozen post-Merge

### Credential Setup

Double-layer security: ClickHouse read-only user + Doppler service token

```bash
# Option 1: Doppler (recommended for teams)
# Get token from 1Password: Engineering vault → 'gapless-network-data Doppler Service Token'
doppler configure set token <token_from_1password>
doppler setup --project gapless-network-data --config prd

# Option 2: Environment variables
export CLICKHOUSE_HOST_READONLY=<host>
export CLICKHOUSE_USER_READONLY=<user>
export CLICKHOUSE_PASSWORD_READONLY=<password>
```

Get setup instructions: `gmd.probe.get_setup_workflow()`

## Network Architecture (Future Work: Bitcoin Integration)

**Data Source**: mempool.space REST API (99.9%+ uptime SLA) - experimental, not operational

**Performance**: httpx with async support for concurrent requests

**Caching**: ETag-based HTTP caching for bandwidth optimization (pending)

**Retry Logic**: Exponential backoff with max 3 retries on API errors (implemented via tenacity library)

**Rate Limiting**: mempool.space allows 10 req/sec (generous, no auth required)

**Contrast with gapless-crypto-data**: Unlike OHLCV package (CloudFront CDN, no retry), mempool API requires retry logic due to live API dependency.

## Authentication (Future Work)

**No authentication required** - mempool.space provides public API endpoints. No rate limit keys needed.

**Note**: This section describes planned Bitcoin integration. Current operational infrastructure (Ethereum) uses Alchemy API key from Secret Manager.

## Current Architecture

**Version**: v5.1.0 (production operational)

**Status**: Production operational - dual-pipeline collection with 23.87M blocks

**Operational Infrastructure**:

- **Alchemy Real-Time Stream** (e2-micro VM): WebSocket subscription for real-time blocks (~12s intervals) - OPERATIONAL
- **BigQuery Hourly Batch** (Cloud Run Job): Syncs latest blocks from BigQuery every hour (~578 blocks/run) - OPERATIONAL
- **ClickHouse Cloud Database** (AWS us-west-2): ReplacingMergeTree with automatic deduplication on block number
- **Monitoring**: Healthchecks.io (Dead Man's Switch) + Pushover (alerts)

**Data Pipeline**:

- Historical data: 23.87M Ethereum blocks (2015-2025) migrated from BigQuery
- Real-time streaming: Alchemy WebSocket feeds new blocks every ~12 seconds
- Deduplication: Both pipelines write to same ClickHouse table with ReplacingMergeTree (ORDER BY number)
- Cost: ClickHouse Cloud free tier (10GB storage, 100GB egress/month)

**SDK Package** (implemented):

- Package structure (src/gapless_network_data/)
- API interface (fetch_blocks, fetch_snapshots, get_latest_snapshot) - implemented (src/gapless_network_data/api.py)
- Bitcoin mempool.space collector - deferred to Phase 2+

## Data Format

## Data Storage Architecture

**Production (Cloud)**:

- **Location**: ClickHouse Cloud AWS (`ethereum_mainnet.blocks`)
- **Purpose**: Always up-to-date production data (23.87M blocks, 2015-2025)
- **Access**: SDK queries this by default (`import gapless_network_data`)
- **Deployment**: Maintained by cloud pipelines (no user setup required)
- **Current Status**: Operational (dual-pipeline architecture → ClickHouse)

**Default Mode**: SDK queries ClickHouse Cloud directly

**Schema Version**: 1.0.0

**Tables** (ClickHouse Cloud):

- `ethereum_mainnet.blocks` - 23.87M Ethereum blocks (2015-2025, ~500 MB compressed)
- `bitcoin_mempool` - Deferred to Phase 2+ (Bitcoin is SECONDARY)

**ClickHouse Schema**:

```sql
CREATE TABLE ethereum_mainnet.blocks (
    -- Temporal (DoubleDelta for monotonic timestamps)
    timestamp DateTime64(3) NOT NULL CODEC(DoubleDelta, ZSTD),

    -- Block identification (DoubleDelta for strictly increasing)
    number Int64 CODEC(DoubleDelta, ZSTD),

    -- Gas metrics (Delta for slow-changing, T64 for high-variance)
    gas_limit Int64 CODEC(Delta, ZSTD),
    gas_used Int64 CODEC(T64, ZSTD),
    base_fee_per_gas Int64 CODEC(T64, ZSTD),

    -- Transaction count (T64 for bounded integers)
    transaction_count Int64 CODEC(T64, ZSTD),

    -- Mining difficulty (ZSTD(3) - T64 doesn't support UInt256)
    difficulty UInt256 CODEC(ZSTD(3)),
    total_difficulty UInt256 CODEC(ZSTD(3)),

    -- Block size in bytes (T64 for bounded integers)
    size Int64 CODEC(T64, ZSTD),

    -- EIP-4844 blob fields (T64 for sparse nulls, high variance)
    blob_gas_used Nullable(Int64) CODEC(T64, ZSTD),
    excess_blob_gas Nullable(Int64) CODEC(T64, ZSTD)
) ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY number
SETTINGS index_granularity = 8192
```

**Compression Codecs** (ADR: 2025-12-10-clickhouse-codec-optimization):

- **DoubleDelta**: Monotonic sequences (timestamp, block number) - best for strictly increasing
- **Delta**: Slow-changing values (gas_limit) - good for values that change infrequently
- **T64**: High-variance bounded integers (gas_used, transaction_count) - optimal for Int64
- **ZSTD(3)**: Large integers (UInt256 difficulty) - T64 doesn't support UInt256

## Feature Engineering Integration

**Cross-Domain Features**: Combine mempool data with OHLCV from gapless-crypto-data

**Integration Pattern**:

```python
import gapless_crypto_data as gcd
import gapless_network_data as gmd

# Step 1: Collect OHLCV data (1-minute BTCUSDT)
df_ohlcv = gcd.get_data(
    symbol="BTCUSDT",
    timeframe="1m",
    start_date="2024-01-01",
    end_date="2024-01-31"
)
# Returns: DatetimeIndex with OHLCV 11-column format

# Step 2: Collect mempool data (1-minute snapshots)
df_mempool = gmd.fetch_snapshots(
    start="2024-01-01 00:00:00",
    end="2024-01-31 23:59:59"
)
# Returns: DatetimeIndex with mempool 9-column format

# Step 3: Temporal alignment (forward-fill for live trading)
df_mempool_aligned = df_mempool.reindex(df_ohlcv.index, method='ffill')

# Step 4: Feature fusion via join
df = df_ohlcv.join(df_mempool_aligned)

# Step 5: Engineer cross-domain features
df['fee_pressure'] = df['fastest_fee'] / (df['economy_fee'] + 1e-10)
df['congestion_z'] = (
    (df['unconfirmed_count'] - df['unconfirmed_count'].rolling(60).mean()) /
    (df['unconfirmed_count'].rolling(60).std() + 1e-10)
)
df['volume_per_tx'] = df['volume'] / (df['number_of_trades'] + 1e-10)
```

## Error Handling

**Exception-Only Failures**: No fallbacks, no defaults, no silent errors (follows gapless-crypto-data pattern)

**Structured Exceptions**: All exceptions include context:

- `timestamp`: When error occurred (ISO 8601)
- `endpoint`: API endpoint that failed
- `http_status`: HTTP status code (if applicable)
- `message`: Human-readable error description

**Gap Detection**: 100% of missing 1-minute intervals flagged in validation reports

**Validation Failure Modes**:

- `HTTPError`: API request failed (network, 4xx, 5xx)
- `ValidationError`: Data quality check failed (schema, sanity, gaps, anomalies)
- `ValueError`: Invalid parameters (start >= end, interval <= 0)

## Testing

**Primary Toolchain**: pytest with coverage tracking

**Coverage Strategy** (follows gapless-crypto-data):

- SDK entry points (api.py): 85%+ coverage
- Core engines (collectors, validation): 70%+ coverage
- CLI: Basic smoke tests

**Test Commands**:

```bash
uv run pytest                          # Run all tests
uv run pytest --cov                    # With coverage report
uv run pytest -k test_collector        # Specific test module
uv run pytest --cov-report=html        # HTML coverage report
```

**Test Structure**:

```
tests/
├── test_api.py              # API export verification
├── test_collectors.py       # Collector logic (pending)
├── test_validation.py       # Validation pipeline (pending)
└── test_cli.py              # CLI commands (pending)
```

## Development Environment

**Package Manager**: uv (NOT pip, conda, or poetry)

**Execution**: `uv run scriptname.py` (uses inline dependencies via PEP 723)

**Python Version**: 3.9+ (3.12+ recommended for performance)

**Type Checking**: mypy in strict mode (`disallow_untyped_defs = true`)

**Linting**: ruff with flake8-bugbear, isort, pycodestyle

**Pre-commit Hooks**: (pending) ruff format, mypy, pytest

**Development Workflow**:

```bash
# Setup
git clone https://github.com/terrylica/gapless-network-data.git
cd gapless-network-data

# Install dependencies
uv sync

# Run tests
uv run pytest --cov

# Type check
uv run mypy src/

# Lint
uv run ruff check src/

# Format
uv run ruff format src/
```

## Documentation Standards

**Architecture**: Link Farm + Hub-and-Spoke with Progressive Disclosure (follows gapless-crypto-data)

**Version Tracking**: YAML frontmatter in all docs:

```yaml
---
version: "1.0.0"
last_updated: "2025-11-10"
supersedes: []
---
```

**SLO Framework**: Correctness, Observability, Maintainability (explicitly excluding performance and security per gapless-crypto-data convention)

**Language Guidelines**: Neutral technical language, no promotional terms ("enhanced", "production-graded", "corrected", "SOTA")

**File Paths**: Absolute paths with space after extension for iTerm2 Cmd+click

## Feature Implementation Status

**Phase 0: Foundation** (completed 2025-11-03)

- [x] Package structure with PEP 561 compliance
- [x] API interface (fetch_snapshots, get_latest_snapshot)
- [x] Basic collector (mempool.space REST client)
- [x] Structured exceptions (HTTP, Validation, RateLimit)
- [x] Retry logic (exponential backoff, max 3 retries)
- [x] LlamaRPC research (52 files, comprehensive Ethereum RPC docs)
- [x] Database architecture investigation (ClickHouse selected)
- [x] Documentation audit (6 findings resolved)

**Phase 1: Historical Data Collection (Complete History)** - **COMPLETED** (2025-11-25)

**Goal**: Collect complete historical blockchain data (2015-2025) for Ethereum ✅

Ethereum Historical Backfill (PRIMARY) - **COMPLETED**:

- [x] BigQuery public dataset integration (replaced LlamaRPC due to rate limits)
- [x] Complete Ethereum block collection (2015-2025, 23.87M blocks loaded)
- [x] Batch fetching with 1-year chunking pattern (prevents OOM)
- [x] ClickHouse Cloud database: ReplacingMergeTree with ORDER BY number
- [x] Dual-pipeline architecture (BigQuery hourly + Alchemy real-time)
- [x] Production monitoring (Healthchecks.io + Pushover)
- [x] Cost optimization (ClickHouse Cloud free tier)
- [x] SLO compliance (Availability, Correctness, Observability, Maintainability)
- [x] Database migration: MotherDuck → ClickHouse (2025-11-25)

Bitcoin Historical Collection (SECONDARY) - **DEFERRED TO PHASE 2+**:

- [ ] mempool.space historical API integration
- [ ] 5-year Bitcoin mempool data (H12 granularity, 3,650 snapshots)
- [ ] ClickHouse storage: INSERT INTO bitcoin_mempool
- [ ] Multi-chain API: fetch_snapshots(chain='bitcoin', mode='historical')

Data Quality - **PARTIALLY IMPLEMENTED**:

- [x] Schema validation (Ethereum blocks via ClickHouse table schema)
- [x] Deduplication (ReplacingMergeTree ORDER BY number)
- [x] Monitoring and alerting (cloud-based Dead Man's Switch)
- [ ] ClickHouse CHECK constraints (fee ordering, non-negative values) - pending
- [ ] Complete 5-layer validation pipeline - deferred to Phase 2+

**Phase 2: Real-Time Collection & Data Quality** (in progress)

- [x] Forward-only collection (Alchemy WebSocket real-time streaming) - OPERATIONAL
- [x] Gap detection (Cloud Function every 3 hours with Pushover alerts) - OPERATIONAL
- [ ] Complete 5-layer validation pipeline (Layers 3-5: sanity, gaps, anomalies) - pending
- [ ] Automatic backfill (currently manual via BigQuery sync) - pending
- [ ] ValidationStorage for audit trail (Parquet-backed validation reports) - pending
- [ ] Production CLI (stream, validate, export commands) - STUBS ONLY (not implemented)

**Phase 3: Production Optimization** (future)

- [ ] Real-time alerting system
- [ ] Network monitoring dashboard
- [ ] Large dataset performance optimization
- [ ] Remote Parquet access (S3, CDN)
- [ ] Cross-chain validation and quality scoring

**Phase 4: Production Readiness** (future)

- [ ] All 9 pending documentation files
- [ ] 70%+ test coverage
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] PyPI publishing (v1.0.0)
- [ ] Community resources (examples, tutorials)

## Related Projects

- [gapless-crypto-data](https://github.com/terrylica/gapless-crypto-data) - OHLCV data collection (referential implementation)
- [mempool.space](https://mempool.space) - Data source API
- [gapless-features](https://github.com/terrylica/gapless-features) - Feature engineering toolkit (future)

## Design Principles

1. **Referential Conformity**: Follow gapless-crypto-data architectural patterns wherever applicable
2. **Temporal Alignment First**: All data structured for DatetimeIndex joining with OHLCV
3. **Zero-Gap Guarantee**: Automated gap detection and backfill recovery
4. **Feature Engineering Ready**: Schema designed for ML pipeline consumption
5. **Type Safety**: PEP 561 compliance throughout
6. **Exception-Only Failures**: No silent errors or default values
7. **Separation of Concerns**: Keep mempool and OHLCV domains separate (do NOT merge into gapless-crypto-data)
