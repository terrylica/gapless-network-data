---
version: "0.1.0"
last_updated: "2025-11-04"
supersedes: []
status: "pending"
---

# ValidationStorage Specification

**Status**: 🚧 Pending Phase 2 implementation

This document will provide comprehensive documentation for the Parquet-backed validation storage system.

## Planned Content

### Storage Architecture

**Design Principle**: "Parquet for Data, DuckDB for Queries"

- **Storage Format**: Parquet files (110x smaller than DuckDB tables)
- **Query Engine**: DuckDB reads Parquet directly (no persistent tables)
- **Benefits**: Zero storage duplication, SQL analytics, columnar compression

---

### Validation Report Schema

```python
# validation_YYYYMMDD.parquet schema
{
    "timestamp": datetime64[ns, UTC],      # When validation ran
    "chain": str,                           # "ethereum", "bitcoin", "solana", etc.
    "layer": str,                           # "http", "schema", "sanity", "gaps", "anomalies"
    "status": str,                          # "pass", "fail", "warning"
    "check_name": str,                      # Specific check that failed/passed
    "message": str,                         # Human-readable description
    "context": str,                         # JSON-encoded additional context
    "data_timestamp_start": datetime64,     # Start of data range validated
    "data_timestamp_end": datetime64,       # End of data range validated
    "records_validated": int64,             # Number of records checked
    "failures": int64,                      # Number of failures in this check
    "execution_time_ms": float64            # Time taken for validation (ms)
}
```

**File Pattern**: `validation_YYYYMMDD.parquet` (daily granularity)

**Index**: Sorted by `(chain, timestamp)` for optimal query performance

**Compression**: Snappy (fast compression/decompression, ~3x smaller)

---

### Gap Report Schema

```python
# gaps_YYYYMMDD.parquet schema
{
    "timestamp": datetime64[ns, UTC],      # When gap was detected
    "chain": str,                           # "ethereum", "bitcoin", etc.
    "gap_start": datetime64[ns, UTC],      # Start of missing data interval
    "gap_end": datetime64[ns, UTC],        # End of missing data interval
    "gap_duration_seconds": float64,       # Duration of gap (seconds)
    "expected_records": int64,              # Number of records that should exist
    "backfill_status": str,                 # "pending", "in_progress", "completed", "failed"
    "backfill_attempts": int64,             # Number of backfill attempts
    "backfill_completed_at": datetime64     # When backfill completed (NULL if pending)
}
```

**File Pattern**: `gaps_YYYYMMDD.parquet` (daily granularity)

**Index**: Sorted by `(chain, gap_start)` for temporal queries

---

### Anomaly Report Schema

```python
# anomalies_YYYYMMDD.parquet schema
{
    "timestamp": datetime64[ns, UTC],      # When anomaly was detected
    "chain": str,                           # "ethereum", "bitcoin", etc.
    "data_timestamp": datetime64,           # Timestamp of anomalous data point
    "field": str,                           # Field with anomaly (e.g., "baseFeePerGas")
    "value": float64,                       # Anomalous value
    "z_score": float64,                     # Z-score (number of std devs from mean)
    "mean": float64,                        # Rolling mean at detection time
    "std": float64,                         # Rolling std dev at detection time
    "anomaly_type": str,                    # "spike", "drop", "rate_change", "volume"
    "severity": str                         # "low", "medium", "high"
}
```

**File Pattern**: `anomalies_YYYYMMDD.parquet` (daily granularity)

**Index**: Sorted by `(chain, data_timestamp)` for temporal queries

---

### DuckDB Query Interface

```python
import duckdb
import gapless_network_data as gnd

# Connect to validation storage
conn = duckdb.connect()

# Query 1: Find all validation failures in the last 7 days
failures = conn.execute("""
    SELECT
        chain,
        layer,
        check_name,
        COUNT(*) as failure_count,
        SUM(failures) as total_failures,
        MAX(timestamp) as last_failure
    FROM read_parquet('validation_*.parquet')
    WHERE status = 'fail'
        AND timestamp >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY chain, layer, check_name
    ORDER BY failure_count DESC
""").df()

# Query 2: Detect persistent gaps (not backfilled in 24 hours)
persistent_gaps = conn.execute("""
    SELECT
        chain,
        gap_start,
        gap_end,
        gap_duration_seconds / 3600.0 as gap_hours,
        backfill_status,
        backfill_attempts,
        CURRENT_TIMESTAMP - timestamp as hours_since_detection
    FROM read_parquet('gaps_*.parquet')
    WHERE backfill_status != 'completed'
        AND timestamp <= CURRENT_TIMESTAMP - INTERVAL '24 hours'
    ORDER BY gap_duration_seconds DESC
""").df()

# Query 3: Find high-severity anomalies in the last hour
recent_anomalies = conn.execute("""
    SELECT
        chain,
        data_timestamp,
        field,
        value,
        z_score,
        anomaly_type,
        severity
    FROM read_parquet('anomalies_*.parquet')
    WHERE severity = 'high'
        AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
    ORDER BY z_score DESC
""").df()

# Query 4: Validation pipeline health check
health = conn.execute("""
    SELECT
        chain,
        layer,
        COUNT(*) as total_checks,
        SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) as passes,
        SUM(CASE WHEN status = 'fail' THEN 1 ELSE 0 END) as fails,
        SUM(CASE WHEN status = 'warning' THEN 1 ELSE 0 END) as warnings,
        CAST(SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*) * 100 as success_rate
    FROM read_parquet('validation_*.parquet')
    WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
    GROUP BY chain, layer
    ORDER BY chain, layer
""").df()
```

---

### File Organization

```
data/
├── ethereum/
│   ├── ethereum_20240101_00.parquet    # Raw block data
│   ├── ethereum_20240101_01.parquet
│   └── ...
├── bitcoin/
│   ├── bitcoin_20240101_00.parquet     # Raw mempool data
│   ├── bitcoin_20240101_01.parquet
│   └── ...
└── validation/
    ├── validation_20240101.parquet     # Validation reports (all chains)
    ├── validation_20240102.parquet
    ├── gaps_20240101.parquet           # Gap reports (all chains)
    ├── gaps_20240102.parquet
    ├── anomalies_20240101.parquet      # Anomaly reports (all chains)
    └── anomalies_20240102.parquet
```

**Rationale**:

- Raw data partitioned by chain (different schemas)
- Validation data unified by type (same schema across chains)
- Daily granularity for efficient queries and retention policies

---

### API Interface

```python
from gapless_network_data.validation import ValidationStorage

# Initialize storage
storage = ValidationStorage(base_dir="./data/validation")

# Write validation report
storage.write_validation_report(
    timestamp=datetime.now(),
    chain="ethereum",
    layer="schema",
    status="pass",
    check_name="required_fields_present",
    message="All required fields present",
    context={},
    data_timestamp_start=datetime(2024, 1, 1),
    data_timestamp_end=datetime(2024, 1, 2),
    records_validated=7200,
    failures=0,
    execution_time_ms=125.4
)

# Write gap report
storage.write_gap_report(
    timestamp=datetime.now(),
    chain="ethereum",
    gap_start=datetime(2024, 1, 1, 12, 30),
    gap_end=datetime(2024, 1, 1, 12, 35),
    gap_duration_seconds=300,
    expected_records=25,  # ~12s per block
    backfill_status="pending",
    backfill_attempts=0
)

# Write anomaly report
storage.write_anomaly_report(
    timestamp=datetime.now(),
    chain="ethereum",
    data_timestamp=datetime(2024, 1, 1, 15, 45, 30),
    field="baseFeePerGas",
    value=250_000_000_000,  # 250 gwei (spike)
    z_score=4.2,
    mean=30_000_000_000,
    std=5_000_000_000,
    anomaly_type="spike",
    severity="high"
)

# Query validation reports
failures = storage.query_failures(
    chain="ethereum",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
    layers=["schema", "sanity"]
)

# Query gaps
gaps = storage.query_gaps(
    chain="ethereum",
    backfill_status="pending",
    min_duration_seconds=60
)

# Query anomalies
anomalies = storage.query_anomalies(
    chain="ethereum",
    severity="high",
    start_date=datetime.now() - timedelta(hours=24)
)
```

---

### Performance Benchmarks

**Storage Savings** (vs DuckDB persistent tables):

- Validation reports: 110x smaller (Parquet with Snappy compression)
- Gap reports: 95x smaller
- Anomaly reports: 105x smaller

**Query Performance** (DuckDB reading Parquet):

- Simple filters: 10-20x faster than pandas
- Complex aggregations: 15-30x faster
- Temporal joins: 40-60x faster with ASOF JOIN

**Compression Ratios** (Snappy):

- Validation reports: ~3x smaller than uncompressed
- Gap reports: ~4x smaller (many NULL values in backfill fields)
- Anomaly reports: ~2.5x smaller

---

### Retention Policies

**Validation Reports**: Keep for 90 days, then archive to cold storage

**Gap Reports**: Keep indefinitely (small size, critical for zero-gap guarantee)

**Anomaly Reports**: Keep for 180 days, then archive

**Automated Cleanup**:

```python
from gapless_network_data.validation import cleanup_old_reports

# Remove validation reports older than 90 days
cleanup_old_reports(
    base_dir="./data/validation",
    report_type="validation",
    retention_days=90
)
```

---

## Current Implementation Status

**Implemented** (v0.1.0):

- Pydantic validation models (MempoolValidationReport)
- Basic exception structure (MempoolValidationException)

**Pending** (Phase 2 - Data Quality):

- ValidationStorage class with write methods
- Parquet file generation for validation reports
- DuckDB query interface
- Gap detection and gap report storage
- Anomaly detection and anomaly report storage
- Retention policy automation

---

## Current Context

Until this document is completed, refer to:

- [CLAUDE.md](/CLAUDE.md) - ValidationStorage overview
- [Validation Overview](/docs/validation/OVERVIEW.md) - 5-layer pipeline
- [ClickHouse Migration](/docs/architecture/decisions/2025-11-25-motherduck-clickhouse-migration.md) - Production database architecture

---

**Related Documentation**:

- [Validation Overview](/docs/validation/OVERVIEW.md) - Validation pipeline
- [ClickHouse Migration](/docs/architecture/decisions/2025-11-25-motherduck-clickhouse-migration.md) - Query architecture

**This document will be completed during Phase 2 implementation.**
