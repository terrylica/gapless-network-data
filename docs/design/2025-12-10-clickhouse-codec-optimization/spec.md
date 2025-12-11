# Design Spec: ClickHouse Compression Codec Optimization

**ADR**: [ClickHouse Codec Optimization](/docs/adr/2025-12-10-clickhouse-codec-optimization.md)

## Overview

Apply ClickHouse schema optimization best practices from the `quality-tools:clickhouse-architect` skill to the `gapless-network-data` repository. This includes compression codecs for all columns and a projection for timestamp-based queries.

**Migration Approach**: Full reconstruction (DROP + CREATE + Reload from BigQuery) - ~5.5 minutes total.

## User Decisions

| Decision           | Choice                                                   |
| ------------------ | -------------------------------------------------------- |
| Scope              | Full optimization (codecs + projection)                  |
| UInt256 columns    | CODEC(ZSTD(3))                                           |
| Baseline audit     | Yes, capture before/after metrics                        |
| ORDER BY           | Keep (number) + add projection for timestamp queries     |
| Migration approach | DROP + CREATE + Reload (full reconstruction)             |
| Script update      | Embed codecs + projection in create_schema.py            |
| Pipeline handling  | Pause Alchemy WebSocket + BigQuery sync during migration |

## Current State

- **Schema YAML**: `/schema/clickhouse/ethereum_mainnet.yaml` - NO codec specifications
- **Table**: `ethereum_mainnet.blocks` - 23.8M rows, ~1.5 GB
- **ORDER BY**: (number) - single column
- **Engine**: ReplacingMergeTree() with PARTITION BY toYYYYMM(timestamp)

## Target State

| Column                     | Current | Target Codec               |
| -------------------------- | ------- | -------------------------- |
| timestamp                  | None    | `CODEC(DoubleDelta, ZSTD)` |
| number                     | None    | `CODEC(DoubleDelta, ZSTD)` |
| gas_limit                  | None    | `CODEC(Delta, ZSTD)`       |
| gas_used                   | None    | `CODEC(T64, ZSTD)`         |
| base_fee_per_gas           | None    | `CODEC(T64, ZSTD)`         |
| transaction_count          | None    | `CODEC(T64, ZSTD)`         |
| difficulty (UInt256)       | None    | `CODEC(ZSTD(3))`           |
| total_difficulty (UInt256) | None    | `CODEC(ZSTD(3))`           |
| size                       | None    | `CODEC(T64, ZSTD)`         |
| blob_gas_used              | None    | `CODEC(T64, ZSTD)`         |
| excess_blob_gas            | None    | `CODEC(T64, ZSTD)`         |

**Projection**: `blocks_by_timestamp (SELECT * ORDER BY timestamp, number)` for timestamp-range queries.

## Implementation Steps

### Phase 1: Schema Updates (Code Changes)

#### 1.1 Update Schema YAML

**File**: `/schema/clickhouse/ethereum_mainnet.yaml`

Add `codec` to each column's `x-clickhouse` section:

```yaml
timestamp:
  x-clickhouse:
    type: "DateTime64(3)"
    not_null: true
    codec: "CODEC(DoubleDelta, ZSTD)"
```

#### 1.2 Update Schema Infrastructure

**Files to update**:

1. `src/gapless_network_data/schema/loader.py` - Parse codec field from x-clickhouse
2. `src/gapless_network_data/cli/schema/generators/clickhouse_ddl.py` - Emit codec in DDL

#### 1.3 Update create_schema.py

**File**: `/scripts/clickhouse/create_schema.py`

Embed codecs and projection directly in CREATE TABLE:

```python
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ethereum_mainnet.blocks (
    timestamp DateTime64(3) NOT NULL CODEC(DoubleDelta, ZSTD),
    number Int64 NOT NULL CODEC(DoubleDelta, ZSTD),
    gas_limit Int64 NOT NULL CODEC(Delta, ZSTD),
    gas_used Int64 NOT NULL CODEC(T64, ZSTD),
    base_fee_per_gas Int64 NOT NULL CODEC(T64, ZSTD),
    transaction_count Int64 NOT NULL CODEC(T64, ZSTD),
    difficulty UInt256 NOT NULL CODEC(ZSTD(3)),
    total_difficulty UInt256 NOT NULL CODEC(ZSTD(3)),
    size Int64 NOT NULL CODEC(T64, ZSTD),
    blob_gas_used Nullable(Int64) CODEC(T64, ZSTD),
    excess_blob_gas Nullable(Int64) CODEC(T64, ZSTD)
) ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY number
SETTINGS index_granularity = 8192
"""

# Add projection after table creation
ADD_PROJECTION_SQL = """
ALTER TABLE ethereum_mainnet.blocks ADD PROJECTION blocks_by_timestamp (
    SELECT * ORDER BY timestamp, number
);
ALTER TABLE ethereum_mainnet.blocks MATERIALIZE PROJECTION blocks_by_timestamp;
"""
```

#### 1.4 Regenerate DDL

```bash
uv run gapless-network-data schema generate-ddl
```

Verify output in `/schema/clickhouse/_generated/ethereum_mainnet.sql`

### Phase 2: Database Migration (Production Operations)

#### 2.1 Pre-Migration Audit

```bash
doppler run --project aws-credentials --config prd -- \
  uv run scripts/clickhouse/audit_schema.py --output tmp/clickhouse-audit-baseline.json
```

- Capture current compression ratios per column
- Measure current storage size
- Record sample query latencies

#### 2.2 Pause Data Pipelines

1. **Stop Alchemy real-time collector** (VM):

   ```bash
   gcloud compute ssh eth-collector --zone=us-west1-a --command="sudo systemctl stop eth-collector"
   ```

2. **Disable BigQuery hourly sync** (Cloud Run Job):

   ```bash
   gcloud scheduler jobs pause bq-clickhouse-sync --location=us-west1
   ```

#### 2.3 Execute Full Reconstruction (~5.5 minutes)

1. **Drop existing table**:

   ```sql
   DROP TABLE IF EXISTS ethereum_mainnet.blocks;
   ```

2. **Create new table with codecs**:

   ```bash
   doppler run --project aws-credentials --config prd -- \
     uv run scripts/clickhouse/create_schema.py
   ```

3. **Reload data from BigQuery**:

   ```bash
   doppler run --project aws-credentials --config prd -- \
     uv run scripts/clickhouse/migrate_from_bigquery.py
   ```

   - ~5 minutes for 23.8M rows at 80K rows/sec
   - Year-by-year chunking (memory safe)

4. **Add projection**:

   ```sql
   ALTER TABLE ethereum_mainnet.blocks ADD PROJECTION blocks_by_timestamp (
       SELECT * ORDER BY timestamp, number
   );
   ALTER TABLE ethereum_mainnet.blocks MATERIALIZE PROJECTION blocks_by_timestamp;
   ```

#### 2.4 Resume Data Pipelines

1. **Resume Alchemy collector**:

   ```bash
   gcloud compute ssh eth-collector --zone=us-west1-a --command="sudo systemctl start eth-collector"
   ```

2. **Resume BigQuery sync**:

   ```bash
   gcloud scheduler jobs resume bq-clickhouse-sync --location=us-west1
   ```

#### 2.5 E2E Validation

1. **Schema validation against live database**:

   ```bash
   uv run gapless-network-data schema validate
   ```

2. **Run full test suite**:

   ```bash
   uv run pytest tests/test_api.py -v
   ```

3. **Benchmark SDK queries**:

   ```python
   import gapless_network_data as gmd
   import time

   # Limit query
   start = time.time()
   df = gmd.fetch_blocks(limit=10000)
   print(f"Limit query: {time.time() - start:.2f}s")

   # Date range query
   start = time.time()
   df = gmd.fetch_blocks(start='2024-01-01', end='2024-01-31')
   print(f"Date range: {time.time() - start:.2f}s")
   ```

4. **Verify projection usage**:

   ```sql
   EXPLAIN SELECT * FROM ethereum_mainnet.blocks
   WHERE timestamp >= '2024-01-01' AND timestamp <= '2024-01-31'
   ORDER BY timestamp DESC;
   -- Should show projection: blocks_by_timestamp
   ```

#### 2.6 Post-Migration Audit

```bash
doppler run --project aws-credentials --config prd -- \
  uv run scripts/clickhouse/audit_schema.py --output tmp/clickhouse-audit-post.json
```

Compare before/after metrics.

### Phase 3: Documentation and Release

1. Update CLAUDE.md: ClickHouse Schema section with codec info
2. Update llms.txt: Feature references (if user-visible changes)
3. Update design spec: `2025-12-02-schema-first-data-contract/spec.md` with x-clickhouse.codec
4. Run semantic-release for version bump
5. Publish to PyPI

## Files to Modify

### Core Schema Files

| File                                                               | Action                                 |
| ------------------------------------------------------------------ | -------------------------------------- |
| `schema/clickhouse/ethereum_mainnet.yaml`                          | Add codec to each x-clickhouse section |
| `src/gapless_network_data/schema/loader.py`                        | Parse codec field from x-clickhouse    |
| `src/gapless_network_data/cli/schema/generators/clickhouse_ddl.py` | Emit codec in column definitions       |

### Auto-Generated Files (Regenerate)

| File                                                   | Command                                             |
| ------------------------------------------------------ | --------------------------------------------------- |
| `schema/clickhouse/_generated/ethereum_mainnet.sql`    | `uv run gapless-network-data schema generate-ddl`   |
| `src/gapless_network_data/schema/_generated/blocks.py` | `uv run gapless-network-data schema generate-types` |
| `docs/schema/ethereum_mainnet.md`                      | `uv run gapless-network-data schema doc`            |

### New Files

| File                                 | Purpose                                      |
| ------------------------------------ | -------------------------------------------- |
| `scripts/clickhouse/audit_schema.py` | Baseline capture & post-migration validation |

### Documentation Updates

| File                                                        | Section to Update                         |
| ----------------------------------------------------------- | ----------------------------------------- |
| `CLAUDE.md`                                                 | ClickHouse Schema section (~line 175-235) |
| `llms.txt`                                                  | Feature references (~line 54-150)         |
| `docs/design/2025-12-02-schema-first-data-contract/spec.md` | x-clickhouse extension examples           |

### Test Files

| File                | Action                                           |
| ------------------- | ------------------------------------------------ |
| `tests/test_api.py` | Run existing tests (should pass without changes) |

### Deployment Files (Verify)

| File                                           | Verification                       |
| ---------------------------------------------- | ---------------------------------- |
| `deployment/vm/realtime_collector.py`          | INSERT statements still compatible |
| `deployment/gcp-functions/gap-monitor/main.py` | Raw SQL queries still valid        |

## Expected Outcomes

| Metric                  | Before   | Expected After                         |
| ----------------------- | -------- | -------------------------------------- |
| Storage                 | ~1.5 GB  | ~500 MB (3x reduction from codecs)     |
| Storage with projection | -        | ~1 GB (2x for full projection)         |
| Timestamp query latency | Baseline | Improved via projection auto-selection |
| Compression ratio       | ~3-4x    | ~10-15x (with specialized codecs)      |
| Reconstruction time     | -        | ~5.5 minutes (BigQuery reload)         |
| Pipeline downtime       | -        | ~10 minutes total                      |

## Risk Assessment

| Risk                                | Mitigation                                              |
| ----------------------------------- | ------------------------------------------------------- |
| BigQuery reload fails mid-migration | migrate_from_bigquery.py is idempotent - rerun safely   |
| Pipeline data loss during pause     | ~10 min gap, real-time collector catches up post-resume |
| Projection materialization slow     | Monitor via system.mutations, ~30 seconds for 23M rows  |
| Wrong codec syntax                  | Test create_schema.py on local ClickHouse first         |
| Service restart fails               | SSH manual intervention available                       |

## References

- [T64 codec source](https://github.com/ClickHouse/ClickHouse/blob/master/src/Compression/CompressionCodecT64.cpp) - UInt256 not supported
- [Solving ORDER BY with Projections](https://medium.com/@sjksingh/solving-the-clickhouse-order-by-problem-with-projections-a3bec4da1f15)
- [ClickHouse Query Optimization Guide](https://clickhouse.com/resources/engineering/clickhouse-query-optimisation-definitive-guide)
- [Projections for faster queries](https://clickhouse.com/blog/clickhouse-faster-queries-with-projections-and-primary-indexes)
