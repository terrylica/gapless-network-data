---
adr: 2025-12-03-fetch-blocks-input-validation
source: ~/.claude/plans/tranquil-questing-quiche.md
implementation-status: completed
phase: released
last-updated: 2025-12-03
---

# Implementation Spec: Input Validation for `fetch_blocks()` API

**ADR**: [fetch_blocks() Input Validation](/docs/adr/2025-12-03-fetch-blocks-input-validation.md)

## Problem Summary

| Issue         | Current Behavior        | Risk            |
| ------------- | ----------------------- | --------------- |
| `limit=0`     | Returns 23M+ rows       | OOM crash       |
| `start=""`    | Silently ignored        | Unexpected data |
| No params     | Returns full blockchain | OOM crash       |
| `start > end` | Returns 0 rows silently | Silent failure  |

## User-Confirmed Decisions

1. **`limit=0`** → Return 0 rows (literal LIMIT 0)
2. **Empty strings** → Raise `ValueError`
3. **No params** → Raise `ValueError`
4. **Reversed dates** → Raise `ValueError`

## Implementation Tasks

### Task 1: Add Validation Helper Function

**File**: `src/gapless_network_data/api.py` (after line 91)

- [ ] Add `_validate_fetch_blocks_params()` function
- [ ] Validate empty strings
- [ ] Validate at least one constraint
- [ ] Validate date ordering

```python
def _validate_fetch_blocks_params(
    start: str | None,
    end: str | None,
    limit: int | None,
) -> None:
    """Validate fetch_blocks() parameters at function entry."""
    # 1. Empty string detection
    if start == "":
        raise ValueError(
            "start date cannot be empty string. "
            "Use None to omit, or provide a valid date like '2024-01-01'."
        )
    if end == "":
        raise ValueError(
            "end date cannot be empty string. "
            "Use None to omit, or provide a valid date like '2024-01-31'."
        )

    # 2. At least one constraint required
    if start is None and end is None and limit is None:
        raise ValueError(
            "Must specify at least one of: start, end, or limit. "
            "Examples:\n"
            "  fetch_blocks(limit=1000)           # Latest 1000 blocks\n"
            "  fetch_blocks(start='2024-01-01')   # All blocks from Jan 1\n"
            "  fetch_blocks(start='2024-01-01', end='2024-01-31')  # Date range"
        )

    # 3. Date ordering validation
    if start is not None and end is not None:
        start_ts = pd.to_datetime(start)
        end_ts = pd.to_datetime(end)
        if start_ts > end_ts:
            raise ValueError(
                f"start date ({start}) must be <= end date ({end}). "
                "Swap the dates or adjust your query range."
            )
```

### Task 2: Add Validation Call to `fetch_blocks()`

**File**: `src/gapless_network_data/api.py` (line ~280)

- [ ] Add validation call immediately after docstring

```python
# Validate parameters (fail-fast before database operations)
# ADR: 2025-12-03-fetch-blocks-input-validation
_validate_fetch_blocks_params(start, end, limit)
```

### Task 3: Fix `limit=0` Query Building

**File**: `src/gapless_network_data/api.py` (line 311)

- [ ] Change truthy check to `is not None` check

Replace:

```python
limit_clause = f"LIMIT {limit}" if limit else ""
```

With:

```python
# limit=0 means "return 0 rows" (explicit LIMIT 0)
# limit=None means "no limit" (return all matching rows)
# ADR: 2025-12-03-fetch-blocks-input-validation
limit_clause = f"LIMIT {limit}" if limit is not None else ""
```

### Task 4: Update Docstring

**File**: `src/gapless_network_data/api.py`

- [ ] Add ValueError to Raises section
- [ ] Add note about limit=0 behavior

### Task 5: Update llms.txt

**File**: `llms.txt`

- [ ] Add validation note to `fetch_blocks` section

### Task 6: Add Unit Tests

**File**: `tests/test_api.py`

- [ ] Add `TestFetchBlocksValidation` class
- [ ] Test empty string start raises ValueError
- [ ] Test empty string end raises ValueError
- [ ] Test no params raises ValueError
- [ ] Test reversed dates raises ValueError
- [ ] Test same day OK
- [ ] Test limit=0 OK (doesn't raise)
- [ ] Test limit-only OK
- [ ] Test start-only OK

## Files to Modify

| File                              | Change                                           |
| --------------------------------- | ------------------------------------------------ |
| `src/gapless_network_data/api.py` | Add validation function, modify `fetch_blocks()` |
| `tests/test_api.py`               | Add validation tests                             |
| `llms.txt`                        | Update API documentation                         |

## Breaking Changes (Intentional)

| Before                                               | After        |
| ---------------------------------------------------- | ------------ |
| `fetch_blocks()` → 23M rows                          | `ValueError` |
| `fetch_blocks(start="")` → 23M rows                  | `ValueError` |
| `fetch_blocks(limit=0)` → 23M rows                   | 0 rows       |
| `fetch_blocks(start='Mar 10', end='Mar 1')` → 0 rows | `ValueError` |

## Success Criteria

- [ ] All 4 edge cases now raise appropriate errors or return expected results
- [ ] `limit=0` returns empty DataFrame (0 rows)
- [ ] Existing valid use cases still work
- [ ] Unit tests pass
- [ ] `ruff check` passes
- [ ] `mypy` passes
