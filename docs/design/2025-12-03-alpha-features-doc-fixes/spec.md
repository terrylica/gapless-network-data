---
adr: 2025-12-03-alpha-features-doc-fixes
source: ~/.claude/plans/toasty-crafting-willow.md
implementation-status: in_progress
phase: phase-1
last-updated: 2025-12-03
---

# Implementation Spec: Alpha Features Documentation Fixes

**ADR**: [Alpha Features Documentation Fixes](/docs/adr/2025-12-03-alpha-features-doc-fixes.md)

## Problem

Alpha Forge v4.9.0 validation identified two documentation inaccuracies:

| Issue              | Current Docs             | Actual Behavior                |
| ------------------ | ------------------------ | ------------------------------ |
| Interval semantics | Half-open `[start, end)` | **Inclusive `[start, end]`**   |
| Blob gas dtype     | Not fully documented     | **Nullable Int64 with `<NA>`** |

## Implementation Tasks

### Task 1: Fix Interval Semantics in api.py

**File**: `src/gapless_network_data/api.py`

Update the `fetch_blocks()` docstring:

- [x] Change `half-open interval [start, end)` → `inclusive [start, end]`
- [x] Change `end: Exclusive` → `end: Inclusive`
- [x] Update example comments to reflect inclusive behavior

### Task 2: Fix Interval Semantics in llms.txt

**File**: `llms.txt`

- [x] Change `end: ... (exclusive, half-open interval)` → `end: ... (inclusive)`
- [x] Change `Half-open interval [start, end)` → `Inclusive interval [start, end]`

### Task 3: Fix Interval Semantics in CLAUDE.md

**File**: `CLAUDE.md`

- [x] Change example comment `(half-open interval [start, end))` → `(inclusive [start, end])`
- [x] Fix example: `end='2024-02-01'` → `end='2024-01-31'` for January-only data

### Task 4: Add Blob Gas Dtype Documentation to api.py

**File**: `src/gapless_network_data/api.py`

- [x] Add note about nullable Int64 dtype for blob_gas_used and excess_blob_gas
- [x] Add conversion pattern: `.fillna(0).astype('int64')`
- [x] Clarify: `<NA>` is pandas NA, not NaN

### Task 5: Add Blob Gas Dtype Documentation to llms.txt

**File**: `llms.txt`

- [x] Add dtype info: `Int64` (pandas nullable integer)
- [x] Add: Pre-Dencun values are `<NA>` (pandas NA)
- [x] Add: Conversion pattern for non-nullable usage

## Success Criteria

- [x] All interval references updated to "inclusive [start, end]"
- [x] Blob gas dtype documented with conversion pattern
- [x] Examples corrected to reflect actual behavior
- [x] No breaking changes (documentation only)

## Commit Message

```
docs: clarify interval semantics and blob gas dtype

- Interval is inclusive [start, end], not half-open
- Blob gas uses nullable Int64 with <NA> for pre-Dencun

Addresses Alpha Forge v4.9.0 feedback
```
