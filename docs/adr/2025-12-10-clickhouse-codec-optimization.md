---
status: implemented
date: 2025-12-10
decision-maker: Terry Li
consulted: [Explore-Agent, Plan-Agent]
research-method: multi-agent
clarification-iterations: 5
perspectives: [Schema, Performance, Operations]
implemented: 2025-12-10
---

# ADR: ClickHouse Compression Codec Optimization

**Design Spec**: [Implementation Spec](/docs/design/2025-12-10-clickhouse-codec-optimization/spec.md)

## Context and Problem Statement

The `ethereum_mainnet.blocks` table in ClickHouse Cloud has no compression codecs specified, relying on default LZ4. Additionally, timestamp-based queries perform suboptimally because ORDER BY is `(number)` only.

| Issue                   | Current State                            | Impact                           |
| ----------------------- | ---------------------------------------- | -------------------------------- |
| No compression codecs   | Default LZ4 for all columns              | ~3x storage (vs 10-15x possible) |
| Single ORDER BY key     | `ORDER BY (number)` only                 | Full scans for timestamp queries |
| No timestamp projection | Missing `ORDER BY timestamp` projection  | Slow date range queries          |
| Schema YAML incomplete  | No `codec` field in x-clickhouse section | DDL doesn't emit codecs          |

### Before/After

```
 Before / After: ClickHouse Schema Optimization

        ┌─────────────────────────────┐
        │ Before: No codecs (~1.5 GB) │
        └─────────────────────────────┘
          │
          │ add codecs
          ∨
        ┌─────────────────────────────┐
        │ After: T64/ZSTD (~500 MB)   │
        └─────────────────────────────┘
        ┌─────────────────────────────┐
        │  Before: ORDER BY (number)  │
        └─────────────────────────────┘
          │
          │ add projection
          ∨
        ┌─────────────────────────────┐
        │ After: + timestamp proj.    │
        └─────────────────────────────┘
```

<details>
<summary>graph-easy source</summary>

```
graph { label: "Before / After: ClickHouse Schema Optimization"; flow: south; }

[before_codec] { label: "Before: No codecs (~1.5 GB)"; }
[after_codec] { label: "After: T64/ZSTD (~500 MB)"; }
[before_order] { label: "Before: ORDER BY (number)"; }
[after_order] { label: "After: + timestamp proj."; }

[before_codec] -- add codecs --> [after_codec]
[before_order] -- add projection --> [after_order]
```

</details>

## Research Summary

| Agent Perspective | Key Finding                                            | Confidence |
| ----------------- | ------------------------------------------------------ | ---------- |
| Explore-Agent     | Schema YAML has no codec specifications                | High       |
| Explore-Agent     | T64 codec not supported for UInt256                    | High       |
| Plan-Agent        | Full reconstruction (DROP+CREATE) preferred over ALTER | High       |
| Plan-Agent        | BigQuery reload takes ~5.5 min for 23.8M rows          | High       |
| Plan-Agent        | Projection blocks INSERT during materialization        | Medium     |

## Decision Drivers

- Storage cost reduction (ClickHouse Cloud free tier: 10GB limit)
- Query performance for timestamp-based SDK queries (`fetch_blocks(start=..., end=...)`)
- Schema-first architecture (YAML as single source of truth)
- Minimal pipeline downtime during migration

## Considered Options

### Option A: ALTER TABLE (Codec changes only)

Add codecs via ALTER TABLE for each column. Cannot add projection without materialization pause.

- Pros: No data reload
- Cons: Slow per-column ALTER, cannot change ORDER BY

### Option B: DROP + CREATE + Reload (Full reconstruction)

Drop table, create with codecs + projection, reload from BigQuery.

- Pros: Clean schema, projection included, ~5.5 min total
- Cons: ~10 min pipeline downtime

### Option C: Keep as-is

No changes to schema.

- Pros: No risk
- Cons: Suboptimal storage and query performance

## Decision Outcome

Chosen option: **Option B (Full reconstruction)**, because:

1. User explicitly stated data wipe is acceptable
2. BigQuery reload is fast (~80K rows/sec, 5.5 min total)
3. Projection can only be efficiently added during CREATE
4. Clean schema with all optimizations applied at once
5. Schema-first approach requires YAML to be authoritative

## Consequences

### Positive

- ~3x storage reduction (1.5 GB → 500 MB)
- Faster timestamp queries via projection
- Schema YAML becomes complete source of truth for codecs
- DDL generator emits codec specifications

### Negative

- ~10 min pipeline downtime (acceptable per user)
- Requires pipeline pause coordination
- One-time BigQuery reload cost (minimal)

## Architecture

### Codec Selection by Column Type

| Column            | Type            | Codec                      | Rationale                   |
| ----------------- | --------------- | -------------------------- | --------------------------- |
| timestamp         | DateTime64(3)   | `CODEC(DoubleDelta, ZSTD)` | Monotonic timestamps        |
| number            | Int64           | `CODEC(DoubleDelta, ZSTD)` | Strictly increasing         |
| gas_limit         | Int64           | `CODEC(Delta, ZSTD)`       | Rarely changes              |
| gas_used          | Int64           | `CODEC(T64, ZSTD)`         | High variance integers      |
| base_fee_per_gas  | Int64           | `CODEC(T64, ZSTD)`         | High variance integers      |
| transaction_count | Int64           | `CODEC(T64, ZSTD)`         | Bounded integer range       |
| difficulty        | UInt256         | `CODEC(ZSTD(3))`           | T64 unsupported for UInt256 |
| total_difficulty  | UInt256         | `CODEC(ZSTD(3))`           | T64 unsupported for UInt256 |
| size              | Int64           | `CODEC(T64, ZSTD)`         | Bounded integer range       |
| blob_gas_used     | Nullable(Int64) | `CODEC(T64, ZSTD)`         | Sparse nulls, high variance |
| excess_blob_gas   | Nullable(Int64) | `CODEC(T64, ZSTD)`         | Sparse nulls, high variance |

### Projection for Timestamp Queries

```sql
ALTER TABLE ethereum_mainnet.blocks ADD PROJECTION blocks_by_timestamp (
    SELECT * ORDER BY timestamp, number
);
ALTER TABLE ethereum_mainnet.blocks MATERIALIZE PROJECTION blocks_by_timestamp;
```

### Migration Flow

```
 Migration: Full Reconstruction Flow

      ╭───────────────────────────╮
      │     Pause Pipelines       │
      │ (VM + Cloud Scheduler)    │
      ╰───────────────────────────╯
        │
        │
        ∨
      ┌───────────────────────────┐
      │   DROP TABLE IF EXISTS    │
      └───────────────────────────┘
        │
        │
        ∨
      ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
      ┃   CREATE TABLE            ┃
      ┃   (with codecs)           ┃
      ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
        │
        │
        ∨
      ┌───────────────────────────┐
      │  Reload from BigQuery     │
      │  (~5.5 min, 23.8M rows)   │
      └───────────────────────────┘
        │
        │
        ∨
      ┌───────────────────────────┐
      │   ADD + MATERIALIZE       │
      │   projection (~30 sec)    │
      └───────────────────────────┘
        │
        │
        ∨
      ╭───────────────────────────╮
      │    Resume Pipelines       │
      ╰───────────────────────────╯
```

<details>
<summary>graph-easy source</summary>

```
graph { label: "Migration: Full Reconstruction Flow"; flow: south; }

[pause] { label: "Pause Pipelines\n(VM + Cloud Scheduler)"; shape: rounded; }
[drop] { label: "DROP TABLE IF EXISTS"; }
[create] { label: "CREATE TABLE\n(with codecs)"; border: bold; }
[reload] { label: "Reload from BigQuery\n(~5.5 min, 23.8M rows)"; }
[project] { label: "ADD + MATERIALIZE\nprotection (~30 sec)"; }
[resume] { label: "Resume Pipelines"; shape: rounded; }

[pause] -> [drop]
[drop] -> [create]
[create] -> [reload]
[reload] -> [project]
[project] -> [resume]
```

</details>

## Files Affected

### Core Schema Files

| File                                                               | Change                                 |
| ------------------------------------------------------------------ | -------------------------------------- |
| `schema/clickhouse/ethereum_mainnet.yaml`                          | Add codec to each x-clickhouse section |
| `src/gapless_network_data/schema/loader.py`                        | Parse codec field                      |
| `src/gapless_network_data/cli/schema/generators/clickhouse_ddl.py` | Emit codec in DDL                      |

### Generated Files (Regenerate)

| File                                                   | Command                                             |
| ------------------------------------------------------ | --------------------------------------------------- |
| `schema/clickhouse/_generated/ethereum_mainnet.sql`    | `uv run gapless-network-data schema generate-ddl`   |
| `src/gapless_network_data/schema/_generated/blocks.py` | `uv run gapless-network-data schema generate-types` |

### Scripts

| File                                  | Change                                    |
| ------------------------------------- | ----------------------------------------- |
| `scripts/clickhouse/create_schema.py` | Embed codecs + projection in CREATE TABLE |
| `scripts/clickhouse/audit_schema.py`  | New: baseline capture + post-migration    |

### Documentation

| File        | Change                           |
| ----------- | -------------------------------- |
| `CLAUDE.md` | Update ClickHouse Schema section |
| `llms.txt`  | Update if user-visible changes   |

## References

- [Global Plan](/Users/terryli/.claude/plans/mossy-weaving-yao.md) (ephemeral)
- [ClickHouse Compression Codecs](https://clickhouse.com/docs/en/sql-reference/statements/create/table#column_compression_codec)
- [T64 Codec Source](https://github.com/ClickHouse/ClickHouse/blob/master/src/Compression/CompressionCodecT64.cpp) - UInt256 not supported
- [Projections for Faster Queries](https://clickhouse.com/blog/clickhouse-faster-queries-with-projections-and-primary-indexes)
