---
version: "0.1.0"
last_updated: "2025-11-04"
supersedes: []
status: "pending"
---

# Validation System Overview

**Status**: 🚧 Pending Phase 2 implementation

This document will provide comprehensive documentation for the 5-layer validation pipeline.

## Planned Content

### 5-Layer Validation Pipeline

#### Layer 1: HTTP/RPC Validation

- **Purpose**: Verify API responses are valid before processing
- **Checks**:
  - HTTP status code (200-299 success range)
  - Response content type (JSON expected)
  - Response size (not empty, within expected bounds)
  - RPC error codes (if applicable)
- **Action on Failure**: Raise `MempoolHTTPException`, retry with exponential backoff (max 3 retries)

#### Layer 2: Schema Validation

- **Purpose**: Ensure data structure matches expected schema
- **Checks**:
  - Required fields present
  - Field types correct (int64, float64, datetime64[ns, UTC])
  - Pydantic model validation
- **Action on Failure**: Raise `MempoolValidationException` with schema mismatch details

#### Layer 3: Sanity Validation

- **Purpose**: Verify data values are logically consistent
- **Checks**:
  - Non-negative values (gas prices, fees, counts)
  - Range checks (fee rates 1-1000 sat/vB)
  - Ordering constraints (fastest_fee >= half_hour_fee >= hour_fee >= economy_fee)
  - Timestamp monotonicity (block numbers strictly increasing)
- **Action on Failure**: Raise `MempoolValidationException` with sanity check failures

#### Layer 4: Gap Detection

- **Purpose**: Identify missing data intervals (zero-gap guarantee)
- **Checks**:
  - Ethereum: Missing block numbers (should be consecutive)
  - Bitcoin: Missing 5-minute intervals
  - Unexpected time jumps (>2x expected interval)
- **Action on Failure**: Log gaps, trigger automatic backfill, store gap report in DuckDB

#### Layer 5: Anomaly Detection

- **Purpose**: Flag unusual but not necessarily invalid data
- **Checks**:
  - Z-score outliers (base fee spikes >3 standard deviations)
  - Volume anomalies (sudden mempool size changes)
  - Rate-of-change anomalies (gas price jumps)
- **Action on Failure**: Log anomalies, store report in DuckDB (data not rejected)

---

### Validation Report Structure

Each validation run produces a Parquet report with:

```python
# Validation report schema
{
    "timestamp": datetime64[ns, UTC],      # When validation ran
    "chain": str,                           # "ethereum" or "bitcoin"
    "layer": str,                           # "http", "schema", "sanity", "gaps", "anomalies"
    "status": str,                          # "pass", "fail", "warning"
    "check_name": str,                      # Specific check that failed
    "message": str,                         # Human-readable description
    "context": dict,                        # Additional context (e.g., failed values)
    "data_timestamp_start": datetime64,     # Start of data range validated
    "data_timestamp_end": datetime64,       # End of data range validated
    "records_validated": int64,             # Number of records checked
    "failures": int64                       # Number of failures in this check
}
```

Stored as: `validation_YYYYMMDD.parquet` in DuckDB-queryable format.

---

### Validation Workflow

```python
import gapless_network_data as gnd

# Automatic validation (default)
df = gnd.fetch_snapshots(
    chain="ethereum",
    start="2024-01-01",
    end="2024-01-02",
    validate=True  # Default
)

# Manual validation
from gapless_network_data.validation import validate_data

report = validate_data(
    df=df,
    chain="ethereum",
    layers=["schema", "sanity", "gaps", "anomalies"]  # Skip HTTP layer (already collected)
)

# Query validation reports with DuckDB
import duckdb
conn = duckdb.connect()

failures = conn.execute("""
    SELECT layer, check_name, COUNT(*) as failure_count
    FROM read_parquet('validation_*.parquet')
    WHERE status = 'fail'
    GROUP BY layer, check_name
    ORDER BY failure_count DESC
""").df()

print(failures)
```

---

### Exception Handling

```python
from gapless_network_data import (
    MempoolHTTPException,
    MempoolValidationException
)

try:
    df = gnd.fetch_snapshots(chain="ethereum", start="2024-01-01", end="2024-01-02")
except MempoolHTTPException as e:
    print(f"HTTP error: {e.message}")
    print(f"Status code: {e.http_status}")
    print(f"Endpoint: {e.endpoint}")
except MempoolValidationException as e:
    print(f"Validation failed: {e.message}")
    print(f"Failed layer: {e.layer}")
    print(f"Failed checks: {e.failed_checks}")
    # Access detailed validation report
    print(e.validation_report)
```

---

### Configuration

```python
# Set validation strictness
gnd.config.set(
    validation_level="strict",     # "strict", "standard", "permissive"
    gap_tolerance_seconds=30,      # Allow 30s gaps without failing
    anomaly_z_threshold=3.0,       # Z-score threshold for anomalies
    enable_anomaly_detection=True  # Enable Layer 5
)

# Per-request validation config
df = gnd.fetch_snapshots(
    chain="ethereum",
    start="2024-01-01",
    end="2024-01-02",
    validation_level="permissive",
    gap_tolerance_seconds=60
)
```

---

## Current Implementation Status

**Implemented** (v0.1.0):

- Layer 1: HTTP validation (basic)
- Layer 2: Schema validation (Pydantic models)
- Structured exceptions (MempoolHTTPException, MempoolValidationException)
- Retry logic with exponential backoff

**Pending** (Phase 2 - Data Quality):

- Layer 3: Sanity validation (range checks, ordering constraints)
- Layer 4: Gap detection (missing intervals, automatic backfill)
- Layer 5: Anomaly detection (z-score outliers, rate-of-change)
- Validation report persistence (Parquet format)
- DuckDB query interface for validation reports

---

## Current Context

Until this document is completed, refer to:

- [CLAUDE.md](/Users/terryli/eon/gapless-network-data/CLAUDE.md) - Validation pipeline overview (lines 225-245)
- [ValidationStorage Specification](/Users/terryli/eon/gapless-network-data/docs/validation/STORAGE.md) - Parquet-backed storage
- [src/gapless_network_data/validation/models.py](/Users/terryli/eon/gapless-network-data/src/gapless_network_data/validation/models.py) - Pydantic validation models

---

**Related Documentation**:

- [ValidationStorage Specification](/Users/terryli/eon/gapless-network-data/docs/validation/STORAGE.md) - Storage format details
- [Architecture Overview](/Users/terryli/eon/gapless-network-data/docs/architecture/OVERVIEW.md) - System design

**This document will be completed during Phase 2 implementation.**
