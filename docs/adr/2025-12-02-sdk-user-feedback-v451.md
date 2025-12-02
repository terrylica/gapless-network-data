---
status: implemented
date: 2025-12-02
decision-maker: Terry Li
consulted: [Explore-BlobGasDtype, Explore-EnvExample, Explore-VersionAttr]
research-method: single-agent
clarification-iterations: 1
perspectives: [EcosystemArtifact, BoundaryInterface]
---

# ADR: SDK User Feedback Improvements for v4.5.1

**Design Spec**: [Implementation Spec](/docs/design/2025-12-02-sdk-user-feedback-v451/spec.md)

## Context and Problem Statement

User (Alpha Forge team) reported 3 improvement areas after evaluating gapless-network-data v4.5.1:

1. **Blob gas columns return `object` dtype** - Pre-Dencun blocks have NULL values, causing pandas to infer `object` dtype instead of integer. This forces downstream type conversion.

2. **`.env.example` not accessible** - Users installing via pip need credential variable names but `.env.example` isn't included in wheel distributions.

3. **`__version__` returns 'unknown'** - Reported version mismatch, though investigation found hardcoded version works correctly from source.

The primary friction is the blob gas dtype issue, which violates the API contract (docstring promises `uint64, nullable`) and requires manual handling in ML pipelines.

### Before/After

```
     ⏮️ Before / ⏭️ After: Blob Gas Column Dtypes

┌−−−−−−−−−−−−−−−−−−−−−┐        ┌−−−−−−−−−−−−−−−−−−−−−−┐
╎ Before v4.5.1:      ╎        ╎ After v4.6.0:        ╎
╎                     ╎        ╎                      ╎
╎ ┌─────────────────┐ ╎        ╎ ┌──────────────────┐ ╎
╎ │  blob_gas_used  │ ╎  fix   ╎ │  blob_gas_used   │ ╎
╎ │  object dtype   │ ╎ ─────> ╎ │ Int64 (nullable) │ ╎
╎ └─────────────────┘ ╎        ╎ └──────────────────┘ ╎
╎ ┌─────────────────┐ ╎        ╎ ┌──────────────────┐ ╎
╎ │ excess_blob_gas │ ╎  fix   ╎ │ excess_blob_gas  │ ╎
╎ │  object dtype   │ ╎ ─────> ╎ │ Int64 (nullable) │ ╎
╎ └─────────────────┘ ╎        ╎ └──────────────────┘ ╎
╎                     ╎        ╎                      ╎
└−−−−−−−−−−−−−−−−−−−−−┘        └−−−−−−−−−−−−−−−−−−−−−−┘
```

<details>
<summary>graph-easy source</summary>

```
graph { label: "⏮️ Before / ⏭️ After: Blob Gas Column Dtypes"; flow: east; }

( Before v4.5.1:
  [blob_gas_used] { label: "blob_gas_used\nobject dtype"; }
  [excess_blob_gas] { label: "excess_blob_gas\nobject dtype"; }
)

( After v4.6.0:
  [blob_gas_used_new] { label: "blob_gas_used\nInt64 (nullable)"; }
  [excess_blob_gas_new] { label: "excess_blob_gas\nInt64 (nullable)"; }
)

[blob_gas_used] -- fix --> [blob_gas_used_new]
[excess_blob_gas] -- fix --> [excess_blob_gas_new]
```

</details>

## Research Summary

| Agent Perspective    | Key Finding                                                                                                        | Confidence |
| -------------------- | ------------------------------------------------------------------------------------------------------------------ | ---------- |
| Explore-BlobGasDtype | ClickHouse returns NULL for pre-Dencun blocks; pandas infers `object` dtype; no conversion in api.py lines 249-255 | High       |
| Explore-EnvExample   | `.env.example` EXISTS but excluded from wheel; only in sdist                                                       | High       |
| Explore-VersionAttr  | `__version__ = "4.5.1"` hardcoded correctly; returns correct value from source install                             | High       |

## Decision Log

| Decision Area          | Options Evaluated                                 | Chosen             | Rationale                                                             |
| ---------------------- | ------------------------------------------------- | ------------------ | --------------------------------------------------------------------- |
| Blob gas NULL handling | int64+0, Int64 (nullable)                         | Int64              | Preserves NULL semantics via `pd.NA`; semantically correct (NULL ≠ 0) |
| Credential visibility  | Include .env.example in wheel, Document in README | README table       | Simpler; error messages already show variable names                   |
| Version discovery      | Keep hardcoded, Use importlib.metadata            | importlib.metadata | More robust across install methods; single source of truth            |

### Trade-offs Accepted

| Trade-off        | Choice             | Accepted Cost                                                             |
| ---------------- | ------------------ | ------------------------------------------------------------------------- |
| Int64 vs int64+0 | Int64              | Slightly more complex downstream (pd.NA propagates vs simple math with 0) |
| Dynamic version  | importlib.metadata | Requires fallback for editable installs                                   |

## Decision Drivers

- API contract compliance (docstring promises nullable integer)
- ML pipeline ergonomics (blob gas columns should support math operations)
- User feedback priority (blob gas dtype is "main friction point")
- Semantic correctness (NULL means "didn't exist", not "zero")

## Considered Options

- **Option A**: Fill NULL with 0, return int64
  - Simple, matches user's literal suggestion
  - Loses information about pre-Dencun blocks
  - Semantically incorrect (0 ≠ NULL)

- **Option B**: Use pandas nullable Int64 dtype <- Selected
  - Preserves NULL semantics via `pd.NA`
  - Matches modern pandas best practices
  - Enables numeric operations (NA propagates cleanly)

- **Option C**: Return float64 with NaN
  - Standard scientific computing approach
  - Loses integer precision for large values
  - Not semantically appropriate for block counts

## Decision Outcome

Chosen option: **Option B (Int64 nullable)**, because:

1. Preserves NULL semantics - pre-Dencun blocks truly had no blob gas, not "zero blob gas"
2. User chose this option when asked during clarification
3. Matches API contract expectation (nullable integer type)
4. Enables numeric operations while maintaining data integrity

## Synthesis

**Convergent findings**: All three issues are real and fixable; blob gas dtype is highest priority.

**Divergent findings**: User suggested 0 for pre-Dencun, but semantic analysis preferred NULL preservation.

**Resolution**: User explicitly chose Int64 (nullable) when presented with trade-off.

## Consequences

### Positive

- Blob gas columns now support numeric operations directly
- API contract fulfilled (docstring matches reality)
- Users don't need manual type conversion
- Dynamic `__version__` more robust across install methods

### Negative

- Int64 with pd.NA requires users to handle NA in their pipelines (standard pandas practice)
- Minor version bump (4.6.0) for behavior change

## Architecture

```
🏗️ SDK Data Flow with Dtype Conversion

        ╭──────────────────────╮
        │      ClickHouse      │
        │     blocks table     │
        ╰──────────────────────╯
          │
          │
          ∨
        ┌──────────────────────┐
        │    SELECT columns    │
        │        FINAL         │
        └──────────────────────┘
          │
          │ NULL for pre-Dencun
          ∨
        ┌──────────────────────┐
        │    Raw DataFrame     │
        │    (object dtype)    │
        └──────────────────────┘
          │
          │
          ∨
        ┏━━━━━━━━━━━━━━━━━━━━━━┓
        ┃  [+] astype(Int64)   ┃
        ┃    blob gas cols     ┃
        ┗━━━━━━━━━━━━━━━━━━━━━━┛
          │
          │ pd.NA preserved
          ∨
        ╭──────────────────────╮
        │   Final DataFrame    │
        │   (Int64 nullable)   │
        ╰──────────────────────╯
```

<details>
<summary>graph-easy source</summary>

```
graph { label: "🏗️ SDK Data Flow with Dtype Conversion"; flow: south; }

[clickhouse] { label: "ClickHouse\nblocks table"; shape: rounded; }
[query] { label: "SELECT columns\nFINAL"; }
[rawdf] { label: "Raw DataFrame\n(object dtype)"; }
[convert] { label: "[+] astype(Int64)\nblog gas cols"; border: bold; }
[finaldf] { label: "Final DataFrame\n(Int64 nullable)"; shape: rounded; }

[clickhouse] -> [query]
[query] -- NULL for pre-Dencun --> [rawdf]
[rawdf] -> [convert]
[convert] -- pd.NA preserved --> [finaldf]
```

</details>

## References

- [Alpha Features API ADR](/docs/architecture/decisions/2025-11-28-alpha-features-api.md)
- [User Feedback Source](/Users/terryli/.claude/plans/luminous-moseying-tarjan.md) (ephemeral)
