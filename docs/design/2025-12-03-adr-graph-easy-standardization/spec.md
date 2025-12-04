---
adr: 2025-12-03-adr-graph-easy-standardization
source: ~/.claude/plans/tranquil-questing-quiche.md
implementation-status: in_progress
phase: phase-1
last-updated: 2025-12-03
---

# Implementation Spec: ADR Diagram Standardization

**ADR**: [Standardize ADR Diagrams with graph-easy](/docs/adr/2025-12-03-adr-graph-easy-standardization.md)

## Problem Summary

| File                        | Current State                | Issue                                      |
| --------------------------- | ---------------------------- | ------------------------------------------ |
| sdk-user-feedback-v451.md   | Incomplete graph-easy source | Before/After source doesn't match ASCII    |
| alpha-features-doc-fixes.md | Simple ASCII                 | Uses HTML comments, not `<details>` blocks |

## User Decisions

- **Scope**: Both files (sdk-user-feedback-v451.md + alpha-features-doc-fixes.md)
- **Layout**: Claude decides based on content width

## Implementation Tasks

### Task 1: Fix `2025-12-02-sdk-user-feedback-v451.md` Before/After (lines 29-67)

**Layout**: East-flowing (side-by-side) - content is narrow (2 boxes per side)

**Action**:

1. Create proper graph-easy source for Before/After dtype comparison
2. Render with `graph-easy --as=boxart`
3. Replace existing ASCII (lines 29-45)
4. Replace existing `<details>` block (lines 47-67)

**graph-easy source**:

```
graph { label: "⏮️ Before / ⏭️ After: Blob Gas Column Dtypes"; flow: east; }

[before_blob] { label: "blob_gas_used\nobject dtype"; }
[before_excess] { label: "excess_blob_gas\nobject dtype"; }

[after_blob] { label: "blob_gas_used\nInt64 (nullable)"; }
[after_excess] { label: "excess_blob_gas\nInt64 (nullable)"; }

[before_blob] -- fix --> [after_blob]
[before_excess] -- fix --> [after_excess]
```

### Task 2: Fix `2025-12-03-alpha-features-doc-fixes.md` Before/After (lines 26-38)

**Layout**: East-flowing - simple 2-box diagrams

**Action**:

1. Remove HTML comment `<!-- graph-easy source: ... -->`
2. Create proper graph-easy source
3. Render with `graph-easy --as=boxart`
4. Add proper `<details><summary>graph-easy source</summary>` block

**graph-easy source**:

```
graph { label: "⏮️ Before / ⏭️ After: Documentation Mismatch"; flow: south; }

[docs_interval] { label: "Docs: half-open"; }
[code_interval] { label: "Code: inclusive"; }
[docs_interval] -- mismatch --> [code_interval]

[docs_dtype] { label: "Docs: no dtype"; }
[code_dtype] { label: "Code: Int64 <NA>"; }
[docs_dtype] -- missing --> [code_dtype]
```

### Task 3: Fix `2025-12-03-alpha-features-doc-fixes.md` Architecture (lines 100-116)

**Layout**: South-flowing - shows documentation flow

**Action**:

1. Remove HTML comment `<!-- graph-easy source: ... -->`
2. Create proper graph-easy source
3. Render with `graph-easy --as=boxart`
4. Add proper `<details><summary>graph-easy source</summary>` block

**graph-easy source**:

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

## Files to Modify

| File                                              | Sections             | Changes                             |
| ------------------------------------------------- | -------------------- | ----------------------------------- |
| `docs/adr/2025-12-02-sdk-user-feedback-v451.md`   | Lines 29-67          | Fix Before/After diagram + source   |
| `docs/adr/2025-12-03-alpha-features-doc-fixes.md` | Lines 26-38, 100-116 | Convert both diagrams to graph-easy |

## Success Criteria

- [ ] All diagrams use box-drawing characters (┌ ┐ └ ┘ │ ─)
- [ ] All diagrams have matching `<details>` source blocks
- [ ] `graph-easy` can regenerate ASCII from source blocks
- [ ] Commit as `docs:` type (no version bump)
