# DuckDB Architecture & Strategy

**Version**: 1.0.0
**Last Updated**: 2025-11-13
**Status**: DuckDB PRIMARY architecture (2025-11-04)
**Supersedes**: "Parquet for Data" architecture (2025-11-03)

## Architectural Principle: "DuckDB for Everything"

**Core Insight**: For historical data collection + flexible feature engineering, DuckDB PRIMARY storage provides maximum flexibility at negligible storage cost.

**Architecture**:

```
Collection → DuckDB Tables (raw data) → SQL Queries → Features
             ~/.cache/gapless-network-data/data.duckdb
                 └── ethereum_blocks (~1.5 GB, 13M rows)
```

**Why This Approach**:

- **Maximum flexibility**: Direct SQL resampling (time_bucket), temporal joins (ASOF JOIN), window functions
- **10-100x faster**: DuckDB SQL vs Pandas operations for feature engineering
- **Simplicity**: Single data.duckdb file, no file management complexity
- **Compact storage**: ~1.5 GB for 5 years of Ethereum data (76-100 bytes/block empirically validated)
- **Proven at scale**: DoorDash uses DuckDB for 1-min time-series with z-score anomaly detection

## DuckDB Use Cases (23 Features Discovered)

### 1. Validation Storage (Parquet-Backed)

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

### 2. Gap Detection (LAG Window Function)

**DuckDB Solution**: 20x faster than Python iteration

```sql
WITH gaps AS (
    SELECT
        timestamp,
        LAG(timestamp) OVER (ORDER BY timestamp) AS prev_timestamp,
        EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (ORDER BY timestamp))) AS gap_seconds
    FROM bitcoin_mempool
)
SELECT * FROM gaps WHERE gap_seconds > 90  -- Detect >90s gaps (1.5× expected 60s)
```

**Implementation**: Direct queries against DuckDB tables for zero-gap guarantee

### 3. Anomaly Detection (Z-Score with QUALIFY)

**DuckDB Solution**: 10x faster, filters anomalies directly in SQL

```sql
SELECT timestamp, unconfirmed_count, z_score
FROM (
    SELECT
        timestamp,
        unconfirmed_count,
        (unconfirmed_count - AVG(unconfirmed_count) OVER w) /
        (STDDEV(unconfirmed_count) OVER w + 1e-10) AS z_score
    FROM bitcoin_mempool
    WINDOW w AS (ORDER BY timestamp ROWS BETWEEN 60 PRECEDING AND CURRENT ROW)
)
QUALIFY ABS(z_score) > 3  -- Filter anomalies (>3σ from mean)
```

**Production Evidence**: DoorDash case study (same algorithm, <10 min vs hours with Spark)

### 4. Temporal Alignment (ASOF JOIN)

**DuckDB Solution**: 16x faster than pandas reindex, prevents lookahead bias

```sql
-- Align mempool snapshots to OHLCV timestamps (forward-fill)
SELECT ohlcv.*, mempool.* EXCLUDE (timestamp)
FROM read_parquet('~/.cache/gapless-crypto-data/ohlcv/*.parquet') AS ohlcv
ASOF LEFT JOIN bitcoin_mempool AS mempool
ON ohlcv.timestamp >= mempool.timestamp
```

**Critical**: Prevents data leakage in trading models (no future information)
**Performance**: 800ms → 50ms for 525K rows
**Cross-package**: Queries OHLCV Parquet files from gapless-crypto-data + network data from DuckDB

### 5. Schema Validation (CHECK Constraints)

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

### 6. Time-Series Aggregations (time_bucket)

**Pattern**: Native function for bucketing timestamps

```sql
-- Hourly aggregations
SELECT
    time_bucket(INTERVAL '1 hour', timestamp) AS hour,
    AVG(fastest_fee) AS avg_fastest_fee,
    MAX(unconfirmed_count) AS max_unconfirmed
FROM bitcoin_mempool
GROUP BY hour
ORDER BY hour
```

## Performance Benchmarks (525K rows, 1 year of 1-min data)

| Operation                  | Pandas | DuckDB | Speedup |
| -------------------------- | ------ | ------ | ------- |
| Rolling mean (10-period)   | 150ms  | 15ms   | **10x** |
| ASOF JOIN (temporal align) | 800ms  | 50ms   | **16x** |
| Gap detection              | 1200ms | 60ms   | **20x** |
| Z-score (60-period)        | 300ms  | 30ms   | **10x** |
| Full table scan            | N/A    | 0.15ms | N/A     |
| Cross-package join         | N/A    | 2.3ms  | N/A     |

**Source**: `/tmp/duckdb-analytics/SUMMARY.md` - Performance comparison table

## Integration with gapless-crypto-data

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
conn = duckdb.connect('~/.cache/gapless-network-data/data.duckdb')
result = conn.execute("""
    SELECT ohlcv.*, mempool.* EXCLUDE (timestamp)
    FROM read_parquet('~/.cache/gapless-crypto-data/ohlcv/*.parquet') AS ohlcv
    ASOF LEFT JOIN bitcoin_mempool AS mempool
    ON ohlcv.timestamp >= mempool.timestamp
""").df()
```

**Architecture**: OHLCV data from gapless-crypto-data (Parquet files) + network data from gapless-network-data (DuckDB tables)

## Top 6 High-Priority Features (14-19 hours total)

Prioritized by impact and effort:

1. **ASOF JOIN** (2-4h) - Temporal alignment, core feature engineering use case
2. **CHECK Constraints** (2-3h) - Schema validation (fee ordering, non-negative values)
3. **Window Functions + QUALIFY** (3-4h) - Z-score anomaly detection
4. **Gap Detection with LAG()** (3-4h) - Zero-gap guarantee implementation
5. **time_bucket()** (1-2h) - Time-series aggregation primitive
6. **Statistical Aggregates** (2-3h) - MEDIAN, MAD, PERCENTILE_CONT for validation reports

**Full Feature List**: 23 features documented in `/tmp/duckdb-capabilities/feature-priority-matrix.md`

## Why DuckDB vs Alternatives

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

## Investigation References

All investigation materials with absolute paths:

- **Capabilities Analysis**: `/tmp/duckdb-capabilities/EXECUTIVE_SUMMARY.md` - 23 features, priority matrix
- **Current Usage Audit**: `/tmp/duckdb-current-usage/duckdb-usage-audit-report.md` - 0% implementation gap
- **Parquet Integration**: `/tmp/duckdb-parquet/REPORT.md` - 110x storage savings, zero-copy queries
- **Analytics Patterns**: `/tmp/duckdb-analytics/analytics_query_patterns_report.md` - 10-100x speedups
- **Cross-Package Strategy**: `/tmp/duckdb-cross-package/EXECUTIVE_SUMMARY.md` - Separate databases confirmed

**Total Investigation**: ~12,000 lines, 15 files, 5 perspectives
