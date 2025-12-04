---
status: implemented
date: 2025-12-03
decision-maker: Terry Li
consulted: [Alpha-Forge-Validator]
research-method: single-agent
clarification-iterations: 0
perspectives: [Documentation, UserExperience]
---

# ADR: Alpha Features Documentation Fixes

**Design Spec**: [Implementation Spec](/docs/design/2025-12-03-alpha-features-doc-fixes/spec.md)

## Context and Problem Statement

Alpha Forge v4.9.0 validation identified two documentation inaccuracies in the SDK:

1. **Interval semantics**: Docs claim half-open `[start, end)` but actual behavior is inclusive `[start, end]`
2. **Blob gas dtype**: Nullable Int64 with `<NA>` values not documented, users may expect NaN

These documentation issues cause user confusion when querying date ranges and handling pre-Dencun blob gas fields.

### Before/After

```
⏮️ Before / ⏭️ After: Documentation Mismatch

             ┌──────────────────┐
             │  Docs: no dtype  │
             └──────────────────┘
               │
               │ missing
               ∨
             ┌──────────────────┐
             │ Code: Int64 <NA> │
             └──────────────────┘
             ┌──────────────────┐
             │ Docs: half-open  │
             └──────────────────┘
               │
               │ mismatch
               ∨
             ┌──────────────────┐
             │ Code: inclusive  │
             └──────────────────┘
```

<details>
<summary>graph-easy source</summary>

```
graph { label: "⏮️ Before / ⏭️ After: Documentation Mismatch"; flow: south; }

[docs_interval] { label: "Docs: half-open"; }
[code_interval] { label: "Code: inclusive"; }
[docs_interval] -- mismatch --> [code_interval]

[docs_dtype] { label: "Docs: no dtype"; }
[code_dtype] { label: "Code: Int64 <NA>"; }
[docs_dtype] -- missing --> [code_dtype]
```

</details>

**After fix**: Documentation accurately reflects implementation behavior.

## Research Summary

| Agent Perspective     | Key Finding                                          | Confidence |
| --------------------- | ---------------------------------------------------- | ---------- |
| Alpha-Forge-Validator | Interval test shows Jan 3 included when end='Jan 3'  | High       |
| Alpha-Forge-Validator | blob_gas_used dtype is Int64, pre-Dencun values <NA> | High       |

## Decision Log

| Decision Area      | Options Evaluated              | Chosen   | Rationale                                |
| ------------------ | ------------------------------ | -------- | ---------------------------------------- |
| Interval semantics | Change docs vs change code     | Fix docs | Code behavior is correct, docs are wrong |
| Blob gas docs      | Add dtype note vs add examples | Both     | Users need dtype + conversion pattern    |

### Trade-offs Accepted

| Trade-off                  | Choice  | Accepted Cost                    |
| -------------------------- | ------- | -------------------------------- |
| Doc fix vs breaking change | Doc fix | None - no breaking change needed |

## Decision Drivers

- Accurate documentation for AI agent consumption
- Prevent user confusion with date range queries
- Enable proper handling of nullable Int64 columns

## Considered Options

- **Option A**: Change code to match docs (half-open intervals)
- **Option B**: Change docs to match code (inclusive intervals) <- Selected

## Decision Outcome

Chosen option: **Option B** (fix documentation), because:

- The inclusive interval behavior is user-friendly (end date is included)
- Changing code would be a breaking change requiring major version bump
- Documentation should reflect actual behavior

## Synthesis

**Convergent findings**: Alpha Forge validation clearly showed end date is included in results.
**Resolution**: Update all documentation to reflect inclusive interval semantics.

## Consequences

### Positive

- SDK documentation accurately reflects behavior
- Users can correctly predict query results
- AI agents get correct information for code generation

### Negative

- None - this is a documentation-only change

## Architecture

```
📚 Documentation Sources

    ┌────────────────┐
    │     api.py     │
    └────────────────┘
      │
      │ docstring
      ∨
    ┌────────────────┐
    │ fetch_blocks() │
    └────────────────┘
    ┌────────────────┐
    │   CLAUDE.md    │
    └────────────────┘
      │
      │ project docs
      ∨
    ┌────────────────┐
    │   Developers   │
    └────────────────┘
    ┌────────────────┐
    │    llms.txt    │
    └────────────────┘
      │
      │ AI docs
      ∨
    ┌────────────────┐
    │  Claude Code   │
    └────────────────┘
```

<details>
<summary>graph-easy source</summary>

```
graph { label: "📚 Documentation Sources"; flow: south; }

[api] { label: "api.py"; }
[llms] { label: "llms.txt"; }
[claude] { label: "CLAUDE.md"; }

[fetch] { label: "fetch_blocks()"; }
[claude_code] { label: "Claude Code"; }
[developers] { label: "Developers"; }

[api] -- docstring --> [fetch]
[llms] -- AI docs --> [claude_code]
[claude] -- project docs --> [developers]
```

</details>

## References

- Alpha Forge v4.9.0 validation feedback (2025-12-03)
- [EIP-4844 Dencun upgrade](https://eips.ethereum.org/EIPS/eip-4844) - blob gas introduction
