---
status: implemented
date: 2025-12-02
decision-maker: Terry Li
consulted: [Explore-API, Explore-Pipeline, Explore-Tests]
research-method: multi-agent
clarification-iterations: 2
perspectives: [BoundaryInterface, EcosystemArtifact]
---

# ADR: Adopt Half-Open Interval [start, end) for Date Range Queries

**Design Spec**: [Implementation Spec](/docs/design/2025-12-02-half-open-interval-timestamps/spec.md)

## Context and Problem Statement

Upstream bug report from Alpha Forge: `fetch_blocks(start='2024-03-13', end='2024-03-13')` fails with `DatabaseException: 'number'`.

**Root Cause (Empirically Validated)**:

1. **Date interpretation**: ClickHouse interprets `'2024-03-13'` as `'2024-03-13 00:00:00'`, making same-day = exact timestamp (0 matches)
2. **Empty result handling**: clickhouse-connect returns empty `column_names: ()` when 0 rows, causing KeyError on `sort_values("number")`

Secondary discovery: CLAUDE.md documents `DateTime` but actual schema is `DateTime64(3)` (millisecond precision).

### Before/After

```
     ⏮️ Before / ⏭️ After: Date Range Query Behavior

┌−−−−−−−−−−−−−−−−−−−−−−−−−−−−┐        ┌−−−−−−−−−−−−−−−−−−−−−−−−−−−−−┐
╎ Before (Inclusive End):    ╎        ╎ After (Half-Open):          ╎
╎                            ╎        ╎                             ╎
╎ ┌────────────────────────┐ ╎        ╎ ┌─────────────────────────┐ ╎
╎ │ start='2024-03-13'     │ ╎  fix   ╎ │ start='2024-03-13'      │ ╎
╎ │ end='2024-03-13'       │ ╎ ─────> ╎ │ end='2024-03-13'        │ ╎
╎ │ → 0 rows (KeyError)    │ ╎        ╎ │ → 7,117 blocks          │ ╎
╎ └────────────────────────┘ ╎        ╎ └─────────────────────────┘ ╎
╎                            ╎        ╎                             ╎
╎ WHERE ts >= 'date'         ╎        ╎ WHERE ts >= 'date 00:00'    ╎
╎   AND ts <= 'date'         ╎        ╎   AND ts < 'next_day 00:00' ╎
╎                            ╎        ╎                             ╎
└−−−−−−−−−−−−−−−−−−−−−−−−−−−−┘        └−−−−−−−−−−−−−−−−−−−−−−−−−−−−−┘
```

<details>
<summary>graph-easy source</summary>

```
graph { label: "⏮️ Before / ⏭️ After: Date Range Query Behavior"; flow: east; }

( Before (Inclusive End):
  [before] { label: "start='2024-03-13'\nend='2024-03-13'\n→ 0 rows (KeyError)"; }
  [before_sql] { label: "WHERE ts >= 'date'\n  AND ts <= 'date'"; }
)

( After (Half-Open):
  [after] { label: "start='2024-03-13'\nend='2024-03-13'\n→ 7,117 blocks"; }
  [after_sql] { label: "WHERE ts >= 'date 00:00'\n  AND ts < 'next_day 00:00'"; }
)

[before] -- fix --> [after]
```

</details>

## Research Summary

| Agent Perspective | Key Finding                                                            | Confidence |
| ----------------- | ---------------------------------------------------------------------- | ---------- |
| Explore-API       | SDK uses inclusive end (`<=`) while cloud jobs use exclusive end (`<`) | High       |
| Explore-Pipeline  | No production code uses SDK API (deployment bypasses it)               | High       |
| Explore-Tests     | No existing timestamp boundary tests                                   | High       |

**Industry Research** (PostgreSQL, BigQuery, yfinance):

| Source               | Pattern        | Evidence                                           |
| -------------------- | -------------- | -------------------------------------------------- |
| PostgreSQL ranges    | `[start, end)` | "Default is from start inclusive to end exclusive" |
| BigQuery time series | `[start, end)` | "`end_timestamp` is exclusive"                     |
| yfinance             | `[start, end)` | "Similar to Python's range()"                      |
| pandas date_range    | Configurable   | `inclusive='left'` for half-open                   |
| SQL BETWEEN          | Inclusive both | **⚠️ Not recommended for time series**             |

## Decision Log

| Decision Area       | Options Evaluated                    | Chosen       | Rationale                                 |
| ------------------- | ------------------------------------ | ------------ | ----------------------------------------- |
| End boundary        | Inclusive (`<=`), Exclusive (`<`)    | Exclusive    | Industry standard; aligns with cloud jobs |
| Date-only expansion | Keep as-is, Expand to day boundaries | Expand       | Makes same-day queries intuitive          |
| Precision           | Seconds, Milliseconds, Microseconds  | Milliseconds | Matches DateTime64(3) schema              |

### Trade-offs Accepted

| Trade-off         | Choice             | Accepted Cost                                                          |
| ----------------- | ------------------ | ---------------------------------------------------------------------- |
| Behavioral change | Half-open interval | Existing code with explicit times may return 1 fewer block at boundary |
| Date expansion    | Next-day for end   | Users must understand date-only vs explicit time semantics             |

## Decision Drivers

- **Industry alignment**: PostgreSQL, BigQuery, yfinance all use half-open intervals
- **Internal consistency**: Cloud jobs already use exclusive end
- **Bug resolution**: Same-day queries must return blocks
- **Semantic correctness**: Non-overlapping consecutive ranges

## Considered Options

- **Option A**: Keep inclusive end, only fix empty result handling
  - Quick fix but doesn't address root cause
  - Leaves SDK inconsistent with industry and internal patterns

- **Option B**: Adopt half-open interval [start, end) <- Selected
  - Fixes bug and aligns with industry standard
  - Consistent with internal cloud jobs
  - Enables non-overlapping consecutive queries

- **Option C**: Always expand date-only to full day (both ends inclusive)
  - Would fix same-day queries
  - Creates overlapping boundaries between consecutive days

## Decision Outcome

Chosen option: **Option B (Half-open interval)**, because:

1. Industry standard (PostgreSQL, BigQuery, yfinance all use this pattern)
2. Internal consistency (cloud jobs already use exclusive end)
3. Prevents boundary overlap between consecutive ranges
4. Aligns with Python's `range()` semantics

## Synthesis

**Convergent findings**: All explored components confirm SDK is isolated; change won't impact pipelines.

**Divergent findings**: SDK used inclusive end while cloud jobs used exclusive end.

**Resolution**: Align SDK with industry standard and internal cloud jobs.

## Consequences

### Positive

- Same-day queries work correctly (`start='2024-03-13', end='2024-03-13'` returns full day)
- Consecutive ranges don't overlap
- Industry-standard semantics (less surprising to users)
- Internal consistency with cloud jobs

### Negative

- Minor behavioral change for explicit timestamps at boundary
- Documentation updates required (README, llms.txt, probe.py)

## Architecture

```
🏗️ Timestamp Normalization Flow

        ╭──────────────────────╮
        │     User Input       │
        │ start='2024-03-13'   │
        │ end='2024-03-13'     │
        ╰──────────────────────╯
          │
          │
          ∨
        ┏━━━━━━━━━━━━━━━━━━━━━━┓
        ┃ _normalize_timestamp ┃
        ┃ (detect date-only)   ┃
        ┗━━━━━━━━━━━━━━━━━━━━━━┛
          │
          │
          ∨
        ┌──────────────────────┐
        │  Expanded Bounds     │
        │ start: 03-13 00:00   │
        │ end: 03-14 00:00     │
        └──────────────────────┘
          │
          │
          ∨
        ┌──────────────────────┐
        │    SQL Query         │
        │ WHERE ts >= start    │
        │   AND ts < end       │
        └──────────────────────┘
          │
          │
          ∨
        ╭──────────────────────╮
        │    ClickHouse        │
        │  DateTime64(3)       │
        ╰──────────────────────╯
          │
          │ 7,117 blocks
          ∨
        ╭──────────────────────╮
        │     DataFrame        │
        │   (with schema)      │
        ╰──────────────────────╯
```

<details>
<summary>graph-easy source</summary>

```
graph { label: "🏗️ Timestamp Normalization Flow"; flow: south; }

[input] { label: "User Input\nstart='2024-03-13'\nend='2024-03-13'"; shape: rounded; }
[normalize] { label: "_normalize_timestamp\n(detect date-only)"; border: bold; }
[expanded] { label: "Expanded Bounds\nstart: 03-13 00:00\nend: 03-14 00:00"; }
[sql] { label: "SQL Query\nWHERE ts >= start\n  AND ts < end"; }
[clickhouse] { label: "ClickHouse\nDateTime64(3)"; shape: rounded; }
[result] { label: "DataFrame\n(with schema)"; shape: rounded; }

[input] -> [normalize]
[normalize] -> [expanded]
[expanded] -> [sql]
[sql] -> [clickhouse]
[clickhouse] -- 7,117 blocks --> [result]
```

</details>

## Schema Update

**CLAUDE.md correction**: `timestamp DateTime` → `timestamp DateTime64(3) NOT NULL`

This matches the actual schema in `scripts/clickhouse/create_schema.py:65`.

## References

- [PostgreSQL Range Types](https://www.postgresql.org/docs/current/rangetypes.html)
- [BigQuery Time Series Functions](https://cloud.google.com/bigquery/docs/reference/standard-sql/time-series-functions)
- [pandas.date_range](https://pandas.pydata.org/docs/reference/api/pandas.date_range.html)
- [yfinance API Guide](https://marketxls.com/blog/yahoo-finance-api-the-ultimate-guide-for-2024)
- [Global Plan](/Users/terryli/.claude/plans/floating-mapping-eagle.md) (ephemeral)
