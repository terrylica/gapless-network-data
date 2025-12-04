---
status: implemented
date: 2025-12-03
decision-maker: Terry Li
consulted: [Explore-Agent, Plan-Agent]
research-method: single-agent
clarification-iterations: 4
perspectives: [BoundaryInterface, ProductFeature]
---

# ADR: fetch_blocks() Input Validation

**Design Spec**: [Implementation Spec](/docs/design/2025-12-03-fetch-blocks-input-validation/spec.md)

## Context and Problem Statement

Alpha Forge v4.9.0 validation identified 4 critical edge cases in the `fetch_blocks()` API that can cause OOM crashes or silent failures:

| Issue         | Current Behavior        | Risk            |
| ------------- | ----------------------- | --------------- |
| `limit=0`     | Returns 23M+ rows       | OOM crash       |
| `start=""`    | Silently ignored        | Unexpected data |
| No params     | Returns full blockchain | OOM crash       |
| `start > end` | Returns 0 rows silently | Silent failure  |

These behaviors violate the principle of least surprise and can crash production applications.

### Before/After

**Before**: Dangerous edge cases return full blockchain (23M+ rows)

```
🏗️ Validation Architecture

              ValueError
  ┌────────────────────────────────────────┐
  ∨                                        │
╭───────────╮     ┌────────────────┐     ┏━━━━━━━━━━━━━━━━━━━━┓  OK   ┌───────────────┐     ┌────────────┐     ╭───────────╮
│ User Code │ ──> │ fetch_blocks() │ ──> ┃ _validate_params() ┃ ────> │ Query Builder │ ──> │ ClickHouse │ ──> │ DataFrame │
╰───────────╯     └────────────────┘     ┗━━━━━━━━━━━━━━━━━━━━┛       └───────────────┘     └────────────┘     ╰───────────╯
```

**After**: Validation layer prevents OOM with fail-fast ValueError

```
          ⏭️ After: Strict Validation

                          ╭────────────────────╮
                          │   fetch_blocks()   │
                          ╰────────────────────╯
                            │
                            │
                            ∨
╔════════════╗  invalid   ┏━━━━━━━━━━━━━━━━━━━━┓
║ ValueError ║ <───────── ┃ _validate_params() ┃
╚════════════╝            ┗━━━━━━━━━━━━━━━━━━━━┛
                            │
                            │ valid
                            ∨
                          ┌────────────────────┐
                          │   Query Builder    │
                          └────────────────────┘
                            │
                            │
                            ∨
                          ┌────────────────────┐
                          │     ClickHouse     │
                          └────────────────────┘
                            │
                            │
                            ∨
                          ╭────────────────────╮
                          │     DataFrame      │
                          ╰────────────────────╯
```

<details>
<summary>graph-easy source (Before/After)</summary>

```
graph { label: "⏭️ After: Strict Validation"; flow: south; }

[ fetch_blocks() ] { shape: rounded; }
[ fetch_blocks() ] -> [ _validate_params() ] { border: bold; }
[ _validate_params() ] -- invalid --> [ ValueError ] { border: double; }
[ _validate_params() ] -- valid --> [ Query Builder ]
[ Query Builder ] -> [ ClickHouse ]
[ ClickHouse ] -> [ DataFrame ] { shape: rounded; }
```

</details>

## Research Summary

| Agent Perspective | Key Finding                                              | Confidence |
| ----------------- | -------------------------------------------------------- | ---------- |
| Explore-Agent     | `limit=0` is falsy in Python, triggers no LIMIT clause   | High       |
| Explore-Agent     | Empty strings are falsy, skip WHERE conditions           | High       |
| Plan-Agent        | Validation should use ValueError (not DatabaseException) | High       |

## Decision Log

| Decision Area  | Options Evaluated                         | Chosen        | Rationale                         |
| -------------- | ----------------------------------------- | ------------- | --------------------------------- |
| `limit=0`      | Return 0 rows, Raise error, Treat as None | Return 0 rows | Literal interpretation of LIMIT 0 |
| Empty strings  | Raise error, Treat as None                | Raise error   | Prevent silent failures           |
| No params      | Default limit, Raise error, Document only | Raise error   | Force explicit constraints        |
| Reversed dates | Raise error, Return empty                 | Raise error   | Prevent silent failures           |

### Trade-offs Accepted

| Trade-off                  | Choice | Accepted Cost                         |
| -------------------------- | ------ | ------------------------------------- |
| Backwards compat vs Safety | Safety | Breaking change for invalid inputs    |
| Strict vs Lenient          | Strict | More validation errors for edge cases |

## Decision Drivers

- **OOM Prevention**: Unconstrained queries can crash applications
- **Principle of Least Surprise**: `limit=0` should mean 0 rows, not all rows
- **Fail-Fast**: Invalid inputs should error immediately, not silently succeed
- **Clear Error Messages**: Users should know exactly what went wrong

## Considered Options

- **Option A**: Documentation only — Add warnings to docstring, no code changes
- **Option B**: Defensive defaults — Add default `limit=1000` when no constraints
- **Option C**: Strict validation with ValueError — Fail-fast on invalid inputs ← Selected

## Decision Outcome

Chosen option: **Option C (Strict validation)**, because:

1. Fail-fast prevents expensive mistakes (23M row queries cost time and money)
2. ValueError is the standard Python exception for invalid arguments
3. Clear error messages guide users to correct usage
4. Breaking changes are intentional safety improvements

## Synthesis

**Convergent findings**: All perspectives agreed that current behavior is dangerous and counterintuitive.

**Divergent findings**: Plan agent considered defensive defaults vs strict validation.

**Resolution**: User explicitly chose strict validation via AskUserQuestion (4 questions answered).

## Consequences

### Positive

- OOM crashes prevented for accidental full-blockchain queries
- Clear error messages for invalid inputs
- API behaves as expected (`limit=0` returns 0 rows)
- Fail-fast validation catches errors at function entry

### Negative

- Breaking change for users relying on current edge case behavior
- Additional validation overhead (negligible: single function call)

## Architecture

```
🏗️ Validation Architecture

              ValueError
  ┌────────────────────────────────────────┐
  ∨                                        │
╭───────────╮     ┌────────────────┐     ┏━━━━━━━━━━━━━━━━━━━━┓  OK   ┌───────────────┐     ┌────────────┐     ╭───────────╮
│ User Code │ ──> │ fetch_blocks() │ ──> ┃ _validate_params() ┃ ────> │ Query Builder │ ──> │ ClickHouse │ ──> │ DataFrame │
╰───────────╯     └────────────────┘     ┗━━━━━━━━━━━━━━━━━━━━┛       └───────────────┘     └────────────┘     ╰───────────╯
```

<details>
<summary>graph-easy source (Architecture)</summary>

```
graph { label: "🏗️ Validation Architecture"; flow: east; }

[ User Code ] { shape: rounded; }
[ User Code ] -> [ fetch_blocks() ]
[ fetch_blocks() ] -> [ _validate_params() ] { border: bold; }
[ _validate_params() ] -- ValueError --> [ User Code ]
[ _validate_params() ] -- OK --> [ Query Builder ]
[ Query Builder ] -> [ ClickHouse ]
[ ClickHouse ] -> [ DataFrame ] { shape: rounded; }
```

</details>

## References

- [Alpha Forge v4.9.0 Validation Report](/tmp/gapless-network-data-validation/MASTER_REPORT.md)
- [Edge Case Report](/tmp/gapless-network-data-validation/edge-cases/edge-case-report.md)
