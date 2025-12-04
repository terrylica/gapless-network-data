---
status: implemented
date: 2025-12-03
decision-maker: Terry Li
consulted: [Explore-Agent]
research-method: single-agent
clarification-iterations: 2
perspectives: [Documentation, Consistency]
---

# ADR: Standardize ADR Diagrams with graph-easy

**Design Spec**: [Implementation Spec](/docs/design/2025-12-03-adr-graph-easy-standardization/spec.md)

## Context and Problem Statement

ADR files in this repository have inconsistent diagram formats:

| File                        | Current State                | Issue                                      |
| --------------------------- | ---------------------------- | ------------------------------------------ |
| sdk-user-feedback-v451.md   | Incomplete graph-easy source | Source block doesn't match ASCII output    |
| alpha-features-doc-fixes.md | Simple ASCII (`+`/`-`/`\|`)  | Uses HTML comments, not `<details>` blocks |
| 7 other ADRs                | Proper graph-easy            | Already standardized                       |

This inconsistency makes diagrams harder to maintain and regenerate.

### Before/After

```
 ⏮️ Before / ⏭️ After: ADR Diagram Formats

        ┌─────────────────────────┐
        │ Before: Incomplete src  │
        └─────────────────────────┘
          │
          │ fix
          ∨
        ┌─────────────────────────┐
        │  After: <details> src   │
        └─────────────────────────┘
        ┌─────────────────────────┐
        │   Before: +--+ ASCII    │
        └─────────────────────────┘
          │
          │ convert
          ∨
        ┌─────────────────────────┐
        │ After: ┌──┐ Box-drawing │
        └─────────────────────────┘
```

<details>
<summary>graph-easy source</summary>

```
graph { label: "⏮️ Before / ⏭️ After: ADR Diagram Formats"; flow: south; }

[before_simple] { label: "Before: +--+ ASCII"; }
[before_incomplete] { label: "Before: Incomplete src"; }

[after_boxart] { label: "After: ┌──┐ Box-drawing"; }
[after_complete] { label: "After: <details> src"; }

[before_simple] -- convert --> [after_boxart]
[before_incomplete] -- fix --> [after_complete]
```

</details>

## Research Summary

| Agent Perspective | Key Finding                                              | Confidence |
| ----------------- | -------------------------------------------------------- | ---------- |
| Explore-Agent     | 7/10 ADRs already use graph-easy with `<details>` blocks | High       |
| Explore-Agent     | 2 ADRs need conversion to standard format                | High       |
| Explore-Agent     | Existing pattern uses box-drawing chars (┌ ┐ └ ┘ │ ─)    | High       |

## Decision Drivers

- Consistency across all ADR documentation
- Maintainability (diagrams can be regenerated from source)
- GitHub rendering compatibility
- Progressive disclosure via `<details>` blocks

## Considered Options

- **Option A**: Leave as-is (inconsistent formats)
- **Option B**: Convert all to graph-easy format <- Selected

## Decision Outcome

Chosen option: **Option B (Standardize to graph-easy)**, because:

1. 70% of ADRs already use this format (established pattern)
2. `<details>` blocks provide source for regeneration
3. Box-drawing characters render consistently across platforms
4. Aligns with existing adr-graph-easy-architect skill

## Consequences

### Positive

- All diagrams have regenerable source
- Consistent visual style across ADRs
- Easier to update diagrams in the future

### Negative

- One-time migration effort (minimal)

## Architecture

```
 🏗️ ADR Diagram Standardization Flow

      ╭───────────────────────╮
      │       ADR File        │
      ╰───────────────────────╯
        │
        │
        ∨
      ┌───────────────────────┐
      │ Detect diagram format │
      └───────────────────────┘
        │
        │
        ∨
      ┏━━━━━━━━━━━━━━━━━━━━━━━┓
      ┃      graph-easy       ┃
      ┃      --as=boxart      ┃
      ┗━━━━━━━━━━━━━━━━━━━━━━━┛
        │
        │
        ∨
      ┌───────────────────────┐
      │     Embed ASCII +     │
      │   <details> source    │
      └───────────────────────┘
        │
        │
        ∨
      ╭───────────────────────╮
      │   Standardized ADR    │
      ╰───────────────────────╯
```

<details>
<summary>graph-easy source</summary>

```
graph { label: "🏗️ ADR Diagram Standardization Flow"; flow: south; }

[adr] { label: "ADR File"; shape: rounded; }
[detect] { label: "Detect diagram format"; }
[grapheasy] { label: "graph-easy\n--as=boxart"; border: bold; }
[embed] { label: "Embed ASCII +\n<details> source"; }
[done] { label: "Standardized ADR"; shape: rounded; }

[adr] -> [detect]
[detect] -> [grapheasy]
[grapheasy] -> [embed]
[embed] -> [done]
```

</details>

## References

- [Global Plan](/Users/terryli/.claude/plans/tranquil-questing-quiche.md) (ephemeral)
- Existing graph-easy ADRs as reference patterns
