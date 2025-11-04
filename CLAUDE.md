# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gapless Network Data is a multi-chain blockchain network metrics collection tool with zero-gap guarantee. Designed for feature engineering in cryptocurrency trading and ML pipelines.

**Core Capability**: Collect complete historical blockchain network data with high-frequency granularity:
- **Ethereum** (PRIMARY): Block-level data via LlamaRPC (~12 second intervals)
- **Bitcoin**: Mempool snapshots via mempool.space (5-minute intervals)
- **Multi-chain**: Extensible to Solana, Avalanche, Polygon, etc.

**Version**: v0.1.0 (alpha)

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
- Validation pipeline architecture (5-layer validation, DuckDB persistence)
- Documentation patterns (hub-and-spoke, version tracking, SLO framework)
- API design (function-based API, DatetimeIndex output, exception-only failures)
- Development toolchain (uv, pytest, ruff, mypy)

**Architectural Separation Rationale**: These packages are intentionally separate due to fundamental data model incompatibilities:

- **gapless-crypto-data**: OHLCV 11-column format, interval-based time series, price/volume metrics
- **gapless-network-data**: Variable schema, point-in-time snapshots, network congestion metrics

See `/Users/terryli/eon/gapless-crypto-data/docs/audit/mempool-probe-adversarial-audit.yaml` for complete analysis (22 violations identified if integrated).

## Single Source of Truth (SSoT)

**Master Plan**: `/Users/terryli/eon/gapless-network-data/specifications/master-project-roadmap.yaml`

Coordinates all project phases, specifications, and implementation work.

**Architecture**: OpenAPI 3.1.1 machine-readable format with logical dependencies

**Sub-Specifications**:

- `documentation-audit-phase.yaml` - Documentation audit (completed 2025-11-03, 6 findings resolved)
- `duckdb-integration-strategy.yaml` - DuckDB integration (23 features, 29-40 hours total)

**Current Status**:

- **Phase**: Phase 1 (DuckDB Foundation, 14-19 hours) - planned
- **Version**: v0.1.0 (alpha)
- **Next Milestone**: v0.2.0 (Phase 1 complete) or v0.1.1 (doc-fix only) - TBD

**Key Decisions Logged**:

1. Architecture: "Parquet for Data, DuckDB for Queries" (110x storage savings)
2. Separate databases for gapless-crypto-data and gapless-network-data (9-2 score)
3. ASOF JOIN as P0 feature (prevents data leakage, 16x faster)

## Quick Navigation

### Architecture

- [Architecture Overview](/Users/terryli/eon/gapless-network-data/docs/architecture/OVERVIEW.md) - Core components, data flow, SLOs (pending)
- [Data Format Specification](/Users/terryli/eon/gapless-network-data/docs/architecture/DATA_FORMAT.md) - Mempool snapshot schema (pending)
- [Cross-Package Integration](/Users/terryli/eon/gapless-crypto-data/docs/architecture/cross-package-feature-integration.yaml) - How to use with gapless-crypto-data

### Usage Guides

- [Data Collection Guide](/Users/terryli/eon/gapless-network-data/docs/guides/DATA_COLLECTION.md) - CLI usage, collection modes (pending)
- [Python API Reference](/Users/terryli/eon/gapless-network-data/docs/guides/python-api.md) - `fetch_snapshots()`, `get_latest_snapshot()` (pending)
- [Feature Engineering Guide](/Users/terryli/eon/gapless-network-data/docs/guides/FEATURE_ENGINEERING.md) - Temporal alignment, feature fusion (pending)

### Validation System

- [Validation Overview](/Users/terryli/eon/gapless-network-data/docs/validation/OVERVIEW.md) - 5-layer validation pipeline (pending)
- [ValidationStorage Specification](/Users/terryli/eon/gapless-network-data/docs/validation/STORAGE.md) - Parquet-backed validation reports with DuckDB queries (pending)

### Development

- [Development Setup](/Users/terryli/eon/gapless-network-data/docs/development/SETUP.md) - Environment setup (pending)
- [Development Commands](/Users/terryli/eon/gapless-network-data/docs/development/COMMANDS.md) - Testing, linting, build (pending)
- [Publishing Guide](/Users/terryli/eon/gapless-network-data/docs/development/PUBLISHING.md) - PyPI publishing workflow (pending)

### Data Sources Research

- [Research Index](/Users/terryli/eon/gapless-network-data/docs/research/INDEX.md) - Free on-chain network metrics sources (2025-11-03)
- [LlamaRPC Deep Dive](/Users/terryli/eon/gapless-network-data/docs/llamarpc/INDEX.md) - Comprehensive Ethereum RPC research (2025-11-03)

**Focus**: On-chain network metrics (gas prices, mempool congestion, block data, transaction counts)

**Verified Sources for High-Granularity Historical Data (3-5+ years)**:

- **Ethereum**: LlamaRPC (block-level ~12s, 2015+, no auth) ✅ PRIMARY
  - [Official Docs](/Users/terryli/eon/gapless-network-data/docs/llamarpc/official/) - Capabilities, pricing, rate limits
  - [Python SDK](/Users/terryli/eon/gapless-network-data/docs/llamarpc/sdk/) - web3.py recommended
  - [Data Schema](/Users/terryli/eon/gapless-network-data/docs/llamarpc/schema/) - 26 block fields, 20+ metrics
  - [Historical Access](/Users/terryli/eon/gapless-network-data/docs/llamarpc/historical/) - Bulk fetching strategies
  - [Community](/Users/terryli/eon/gapless-network-data/docs/llamarpc/community/) - Collector patterns, RPC comparison
- **Bitcoin**: mempool.space (M5 recent / H12 historical, 2016+, no auth)
- **Bitcoin**: blockchain.info (mempool size, ~H29, 2009+, no auth)
- **Ethereum**: Alchemy RPC (300M CU/month free tier)
- **Multi-chain**: Dune Analytics (SQL aggregation, block-level, 2020+, free signup)

**What This Research EXCLUDES**: Exchange OHLCV price data (Binance, Coinbase, Kraken) - not on-chain network metrics

## SDK Quality Standards

**Primary Use Case**: Programmatic API consumption (`import gapless_network_data`) by downstream packages and AI coding agents

**Implementation Status**: Following gapless-crypto-data SDK standards

**Key Abstractions**:

- **Type Safety**: PEP 561 compliance via py.typed marker (implemented)
- **AI Discoverability**: llms.txt, probe module (pending)
- **Structured Exceptions**: Machine-parseable error context with timestamp, endpoint, HTTP status (implemented)
- **Coverage Strategy**: SDK entry points (85%+), Core engines (70%+) (pending)

## Network Architecture

**Data Source**: mempool.space REST API (99.9%+ uptime SLA)

**Performance**: httpx with async support for concurrent requests

**Caching**: ETag-based HTTP caching for bandwidth optimization (pending)

**Retry Logic**: Exponential backoff with max 3 retries on API errors (implemented via tenacity library)

**Rate Limiting**: mempool.space allows 10 req/sec (generous, no auth required)

**Contrast with gapless-crypto-data**: Unlike OHLCV package (CloudFront CDN, no retry), mempool API requires retry logic due to live API dependency.

## Authentication

**No authentication required** - mempool.space provides public API endpoints. No rate limit keys needed.

## Current Architecture

**Version**: v0.1.0 (alpha - initial implementation)

**Status**: Foundation phase - core modules implemented, full pipeline pending

**Implemented**:

- Package structure (src/gapless_network_data/)
- API interface (fetch_snapshots, get_latest_snapshot)
- Basic collector (mempool.space REST client)
- Validation models (MempoolValidationReport)
- CLI entry point (command dispatch)
- Type stubs (py.typed)
- Structured exceptions (MempoolHTTPException, MempoolValidationException, MempoolRateLimitException)
- Retry logic with exponential backoff (tenacity, max 3 retries)
- Forward-collection-only enforcement

**Pending**:

- ETag caching
- 5-layer validation pipeline
- DuckDB validation storage
- Gap detection and backfill
- Anomaly detection
- Comprehensive test suite
- Documentation generation

## DuckDB Architecture & Strategy

**Version**: Based on 5-agent investigation (2025-11-03)
**Investigation Output**: `/tmp/duckdb-*/` (~12,000 lines, 15 reports)

### Architectural Principle: "Parquet for Data, DuckDB for Queries"

**Core Insight**: DuckDB excels as a **query engine**, not persistent storage. Store all immutable data in Parquet, use DuckDB to query it.

**Architecture**:

```
User API (pandas) → DuckDB Query Engine → Storage Layer
                    (analytics, validation)  (Parquet files)
```

**Why This Matters**:

- **110x storage savings**: Parquet validation reports (4.9KB) vs DuckDB tables (537KB)
- **Zero-copy queries**: Query Parquet directly without loading into memory
- **10-100x performance**: DuckDB SQL vs Python iteration for analytics
- **Proven at scale**: DoorDash uses DuckDB for same use case (1-min intervals, z-score anomaly detection)

### DuckDB Use Cases (23 Features Discovered)

#### 1. Validation Storage (Parquet-Backed)

**Pattern**: Write validation reports to Parquet, query with DuckDB

```python
# Write validation reports
duckdb.execute("""
    COPY (SELECT * FROM validation_results)
    TO 'validation_reports/YYYYMMDD.parquet'
    (FORMAT PARQUET, COMPRESSION ZSTD)
""")

# Query validation history
duckdb.execute("""
    SELECT validation_layer, severity, COUNT(*)
    FROM read_parquet('validation_reports/*.parquet')
    WHERE timestamp BETWEEN ? AND ?
    GROUP BY validation_layer, severity
""")
```

**Benefits**:

- 110x smaller storage
- Queryable validation history
- No schema migrations (Parquet is immutable)

#### 2. Gap Detection (LAG Window Function)

**Current**: CLAUDE.md mentions "gap detection logic" but NO implementation
**DuckDB Solution**: 20x faster than Python iteration

```sql
WITH gaps AS (
    SELECT
        timestamp,
        LAG(timestamp) OVER (ORDER BY timestamp) AS prev_timestamp,
        EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (ORDER BY timestamp))) AS gap_seconds
    FROM read_parquet('mempool_*.parquet')
)
SELECT * FROM gaps WHERE gap_seconds > 90  -- Detect >90s gaps (1.5× expected 60s)
```

**Implementation**: `/tmp/duckdb-analytics/analytics_query_patterns_report.md` lines 892-950

#### 3. Anomaly Detection (Z-Score with QUALIFY)

**Current**: CLAUDE.md mentions "anomaly detection (z-score on vsize, fee spikes)" but NO implementation
**DuckDB Solution**: 10x faster, filters anomalies directly in SQL

```sql
SELECT timestamp, unconfirmed_count, z_score
FROM (
    SELECT
        timestamp,
        unconfirmed_count,
        (unconfirmed_count - AVG(unconfirmed_count) OVER w) /
        (STDDEV(unconfirmed_count) OVER w + 1e-10) AS z_score
    FROM read_parquet('mempool_*.parquet')
    WINDOW w AS (ORDER BY timestamp ROWS BETWEEN 60 PRECEDING AND CURRENT ROW)
)
QUALIFY ABS(z_score) > 3  -- Filter anomalies (>3σ from mean)
```

**Production Evidence**: DoorDash case study (same algorithm, <10 min vs hours with Spark)

#### 4. Temporal Alignment (ASOF JOIN)

**Current**: Feature engineering uses `df_mempool.reindex(df_ohlcv.index, method='ffill')`
**DuckDB Solution**: 16x faster, prevents lookahead bias

```sql
-- Align mempool snapshots to OHLCV timestamps (forward-fill)
SELECT ohlcv.*, mempool.* EXCLUDE (timestamp)
FROM read_parquet('ohlcv/*.parquet') AS ohlcv
ASOF LEFT JOIN read_parquet('mempool/*.parquet') AS mempool
ON ohlcv.timestamp >= mempool.timestamp
```

**Critical**: Prevents data leakage in trading models (no future information)
**Performance**: 800ms → 50ms for 525K rows
**Implementation**: `/tmp/duckdb-analytics/analytics_query_patterns_report.md` lines 274-358

#### 5. Schema Validation (CHECK Constraints)

**Pattern**: Database-level validation for fee ordering sanity check

```sql
CREATE TABLE mempool_snapshots (
    timestamp TIMESTAMP NOT NULL,
    fastest_fee DOUBLE,
    half_hour_fee DOUBLE,
    hour_fee DOUBLE,
    economy_fee DOUBLE,
    minimum_fee DOUBLE,
    CHECK (fastest_fee >= half_hour_fee),
    CHECK (half_hour_fee >= hour_fee),
    CHECK (hour_fee >= economy_fee),
    CHECK (economy_fee >= minimum_fee),
    CHECK (minimum_fee >= 1)
)
```

**Benefit**: Catches data corruption at ingestion time (exception-only failures)

#### 6. Time-Series Aggregations (time_bucket)

**Pattern**: Native function for bucketing timestamps

```sql
-- Hourly aggregations
SELECT
    time_bucket(INTERVAL '1 hour', timestamp) AS hour,
    AVG(fastest_fee) AS avg_fastest_fee,
    MAX(unconfirmed_count) AS max_unconfirmed
FROM read_parquet('mempool_*.parquet')
GROUP BY hour
ORDER BY hour
```

### Performance Benchmarks (525K rows, 1 year of 1-min data)

| Operation                  | Pandas | DuckDB | Speedup |
| -------------------------- | ------ | ------ | ------- |
| Rolling mean (10-period)   | 150ms  | 15ms   | **10x** |
| ASOF JOIN (temporal align) | 800ms  | 50ms   | **16x** |
| Gap detection              | 1200ms | 60ms   | **20x** |
| Z-score (60-period)        | 300ms  | 30ms   | **10x** |
| Full table scan            | N/A    | 0.15ms | N/A     |
| Cross-package join         | N/A    | 2.3ms  | N/A     |

**Source**: `/tmp/duckdb-analytics/SUMMARY.md` - Performance comparison table

### Integration with gapless-crypto-data

**Strategy**: Separate databases, parallel patterns (cross-package investigation confirmed this approach)

- **gapless-crypto-data**: `~/.cache/gapless-crypto-data/validation.duckdb` (fully implemented, v3.3.0)
- **gapless-network-data**: `~/.cache/gapless-network-data/validation.duckdb` (planned)

**Cross-Package Analytics**:

```python
import duckdb

# Option 1: Pandas join (recommended for simplicity)
df_ohlcv = gcd.get_data(...)
df_mempool = gmd.fetch_snapshots(...)
df_features = df_ohlcv.join(df_mempool.reindex(df_ohlcv.index, method='ffill'))

# Option 2: DuckDB ASOF join (16x faster, prevents data leakage)
result = duckdb.execute("""
    SELECT ohlcv.*, mempool.* EXCLUDE (timestamp)
    FROM read_parquet('ohlcv/*.parquet') AS ohlcv
    ASOF LEFT JOIN read_parquet('mempool/*.parquet') AS mempool
    ON ohlcv.timestamp >= mempool.timestamp
""").df()
```

**Source**: `/tmp/duckdb-cross-package/cross-package-duckdb-strategy-report.md`

### Top 6 High-Priority Features (14-19 hours total)

Prioritized by impact and effort:

1. **ASOF JOIN** (2-4h) - Temporal alignment, core feature engineering use case
2. **CHECK Constraints** (2-3h) - Schema validation (fee ordering, non-negative values)
3. **Window Functions + QUALIFY** (3-4h) - Z-score anomaly detection
4. **Gap Detection with LAG()** (3-4h) - Zero-gap guarantee implementation
5. **time_bucket()** (1-2h) - Time-series aggregation primitive
6. **Statistical Aggregates** (2-3h) - MEDIAN, MAD, PERCENTILE_CONT for validation reports

**Full Feature List**: 23 features documented in `/tmp/duckdb-capabilities/feature-priority-matrix.md`

### Why DuckDB vs Alternatives

| Criteria                      | DuckDB               | pandas             | Polars        | Spark      |
| ----------------------------- | -------------------- | ------------------ | ------------- | ---------- |
| **Performance (time-series)** | 10-100x              | Baseline           | ~5x           | Overkill   |
| **SQL Support**               | Modern SQL:2023      | N/A                | Limited       | SQL:2003   |
| **Embedded**                  | ✅ Single file       | ✅ In-process      | ✅ In-process | ❌ Cluster |
| **Parquet Integration**       | ✅ Native, zero-copy | ⚠️ Loads to memory | ✅ Native     | ✅ Native  |
| **Installation Size**         | 50MB                 | 30MB               | 40MB          | 300MB+     |
| **Production Evidence**       | DoorDash             | Ubiquitous         | Emerging      | Mature     |
| **ASOF JOIN**                 | ✅ Native            | ⚠️ Manual reindex  | ✅ Native     | ❌ Manual  |

**Decision**: DuckDB chosen for time-series primitives (ASOF JOIN, window functions, time_bucket), proven production use (DoorDash), and embedded architecture.

### Investigation References

All investigation materials with absolute paths:

- **Capabilities Analysis**: `/tmp/duckdb-capabilities/EXECUTIVE_SUMMARY.md` - 23 features, priority matrix
- **Current Usage Audit**: `/tmp/duckdb-current-usage/duckdb-usage-audit-report.md` - 0% implementation gap
- **Parquet Integration**: `/tmp/duckdb-parquet/REPORT.md` - 110x storage savings, zero-copy queries
- **Analytics Patterns**: `/tmp/duckdb-analytics/analytics_query_patterns_report.md` - 10-100x speedups
- **Cross-Package Strategy**: `/tmp/duckdb-cross-package/EXECUTIVE_SUMMARY.md` - Separate databases confirmed

**Total Investigation**: ~12,000 lines, 15 files, 5 perspectives

## Data Format

**Output Format**: Parquet with snappy compression

**File Granularity**: 1-hour per file (60 snapshots)

**File Pattern**: `mempool_YYYYMMDD_HH.parquet`

**Schema Version**: 1.0.0

**Column Schema**:

| Column              | Type                | Description                      | Validation      |
| ------------------- | ------------------- | -------------------------------- | --------------- |
| `timestamp`         | datetime64[ns, UTC] | Snapshot timestamp               | ISO 8601 format |
| `unconfirmed_count` | int64               | Unconfirmed transactions         | >= 0            |
| `vsize_mb`          | float64             | Mempool virtual size (MB)        | >= 0            |
| `total_fee_btc`     | float64             | Total fees (BTC)                 | >= 0            |
| `fastest_fee`       | float64             | Fee rate for next block (sat/vB) | 1-1000          |
| `half_hour_fee`     | float64             | Fee rate ~30min (sat/vB)         | 1-1000          |
| `hour_fee`          | float64             | Fee rate ~1hr (sat/vB)           | 1-1000          |
| `economy_fee`       | float64             | Low-priority fee (sat/vB)        | 1-1000          |
| `minimum_fee`       | float64             | Minimum relay fee (sat/vB)       | >= 1            |

**Index**: DatetimeIndex on timestamp column (enables temporal alignment with gapless-crypto-data)

**Sanity Checks**: Fee rates must satisfy `fastest_fee >= half_hour_fee >= hour_fee >= economy_fee >= minimum_fee`

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

**Example**: `/tmp/feature_integration_example.py` - Complete workflow generating 43 features from OHLCV + mempool

**Design Specification**: `/Users/terryli/eon/gapless-crypto-data/docs/architecture/cross-package-feature-integration.yaml`

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
last_updated: "2025-01-20"
supersedes: []
---
```

**SLO Framework**: Correctness, Observability, Maintainability (explicitly excluding performance and security per gapless-crypto-data convention)

**Language Guidelines**: Neutral technical language, no promotional terms ("enhanced", "production-graded", "corrected", "SOTA")

**File Paths**: Absolute paths with space after extension for iTerm2 Cmd+click

## Feature Roadmap (Feature-Driven Planning)

**Context**: Roadmap refocused (2025-11-04) to emphasize user-facing features (WHAT users get) rather than implementation architecture (HOW we build it).

**Master Plan**: `/Users/terryli/eon/gapless-network-data/specifications/master-project-roadmap.yaml ` (Single Source of Truth)

**Key Insight**: DuckDB optimizations are implementation details supporting features, not features themselves.

### Phase 1: Core Data Collection Features (3-4 weeks)

**Goal**: Bitcoin + Ethereum network data collection with zero-gap guarantee

**Features**:

1. **Bitcoin Mempool Data Collection** (8-12 hours)
   - Complete 5-layer validation pipeline (HTTP, schema, sanity, gaps, anomalies)
   - Zero-gap guarantee (automatic gap detection + backfill)
   - ETag caching for bandwidth optimization
   - Validation reporting with queryable history
   - **User Value**: Reliable 1-minute Bitcoin mempool data for trading models

2. **Ethereum Network Data Collection** (10-15 hours)
   - LlamaRPC integration (web3.py)
   - Block-level gas prices (baseFeePerGas, gasUsed, gasLimit)
   - Network health metrics (TPS, block utilization)
   - Historical data from 2015+ (archive node access)
   - Multi-chain API: `fetch_snapshots(chain='bitcoin'|'ethereum')`
   - **User Value**: Complete Ethereum network metrics for gas optimization

3. **Feature Engineering Integration** (6-8 hours)
   - Temporal alignment with OHLCV data (prevents data leakage)
   - Cross-domain features (mempool + price data)
   - Production-ready examples (Bitcoin + Ethereum)
   - **User Value**: Ready-to-use features for ML pipelines

**Deliverables**:

- Bitcoin + Ethereum data collection operational
- Multi-chain support (chain parameter)
- Feature engineering examples (43 features)
- Documentation for both chains

**Version**: v0.2.0

### Phase 2: Advanced Features & Analytics (2-3 weeks)

**Goal**: Multi-chain expansion + network insights + production CLI

**Features**:

1. **Multi-Chain Expansion** (8-12 hours)
   - Solana network metrics (TPS, block times, fee rates)
   - Avalanche C-Chain gas data
   - Bitcoin L2 metrics (Lightning Network)
   - **User Value**: 5+ blockchain support for portfolio-wide insights

2. **Network Insights & Analytics** (6-8 hours)
   - Congestion forecasting (short-term predictions)
   - Fee optimization recommendations (best timing)
   - Transaction success probability estimation
   - Historical trend analysis
   - **User Value**: Actionable insights for transaction timing

3. **Production CLI** (4-6 hours)
   - `stream` command (real-time continuous collection)
   - `backfill` command (historical data with progress tracking)
   - `validate` command (view validation reports)
   - `export` command (CSV, JSON, Parquet, Arrow)
   - **User Value**: Production-ready tooling for data operations

**Deliverables**:

- 5+ blockchain support
- Network insights API
- Full-featured CLI
- Multi-format export

**Version**: v0.3.0

### Phase 3: Production Optimization (2-3 weeks)

**Goal**: Real-time monitoring + large dataset performance + advanced validation

**Features**:

1. **Network Monitoring & Alerts** (6-8 hours)
   - Real-time anomaly detection (fee spikes, congestion events)
   - Custom alerting rules (user-defined thresholds)
   - Alert delivery (email, webhook, Telegram)
   - Health monitoring dashboard
   - **User Value**: Proactive alerts for trading opportunities/risks

2. **Large Dataset Performance** (8-10 hours)
   - Query optimization for multi-year datasets (DuckDB)
   - Remote Parquet access (S3, CDN) without local storage
   - Parallel query execution
   - 10x+ speedup for aggregations
   - **User Value**: Efficient analysis of historical data (2015-2025)

3. **Enhanced Data Quality** (4-6 hours)
   - Cross-chain validation (detect chain-split events)
   - Data provenance tracking
   - Quality scoring system
   - Automatic correction recommendations
   - **User Value**: Trustworthy data for critical trading decisions

**Deliverables**:

- Real-time alerting system
- Optimized large dataset queries
- Remote data access
- Quality scoring system

**Version**: v0.4.0

### Phase 4: Production Readiness (2-3 weeks)

**Goal**: Complete documentation, testing, CI/CD, PyPI publishing

**Scope**:

- All 9 pending documentation files
- 70%+ test coverage
- GitHub Actions CI/CD
- PyPI publishing
- Community resources

**Version**: v1.0.0

**Total Timeline**: 8-12 weeks from Phase 1 start

## Feature Implementation Status

**Phase 0: Foundation** (completed 2025-11-03)

- [x] Package structure with PEP 561 compliance
- [x] API interface (fetch_snapshots, get_latest_snapshot)
- [x] Basic collector (mempool.space REST client)
- [x] Structured exceptions (HTTP, Validation, RateLimit)
- [x] Retry logic (exponential backoff, max 3 retries)
- [x] LlamaRPC research (52 files, comprehensive Ethereum RPC docs)
- [x] DuckDB investigation (23 features, performance validation)
- [x] Documentation audit (6 findings resolved)

**Phase 1: Core Data Collection Features** (in planning)

Bitcoin Mempool Collection:

- [ ] Complete 5-layer validation pipeline
  - [ ] Layer 1: HTTP validation
  - [ ] Layer 2: Schema validation
  - [ ] Layer 3: Sanity checks (fee ordering)
  - [ ] Layer 4: Gap detection (implemented with DuckDB LAG)
  - [ ] Layer 5: Anomaly detection (z-score with DuckDB QUALIFY)
- [ ] Gap detection and automatic backfill
- [ ] ETag caching for bandwidth optimization
- [ ] Validation storage (Parquet backend)
- [ ] Validation reporting and query interface

Ethereum Network Collection:

- [ ] LlamaRPC integration (web3.py client)
- [ ] Ethereum data schema (26 fields + 20 metrics)
- [ ] Block-level gas price collection
- [ ] Historical backfill strategy (2015-2025)
- [ ] Multi-chain architecture (bitcoin/, ethereum/ directories)
- [ ] Multi-chain API: fetch_snapshots(chain=...)

Feature Engineering Integration:

- [ ] Temporal alignment API (ASOF JOIN, prevents data leakage)
- [ ] align_with_ohlcv() function
- [ ] Cross-domain feature examples (10+ features)
- [ ] Documentation: docs/guides/FEATURE_ENGINEERING.md
- [ ] Examples: Bitcoin + BTCUSDT, Ethereum + ETHUSDT

**Phase 2: Advanced Features** (future)

- [ ] Multi-chain expansion (Solana, Avalanche, Bitcoin L2s)
- [ ] Network insights (congestion forecasting, fee optimization)
- [ ] Production CLI (stream, backfill, validate, export commands)
- [ ] Multi-format export (CSV, JSON, Parquet, Arrow)

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
