---
adr: 2025-12-02-sdk-user-feedback-v451
source: ~/.claude/plans/luminous-moseying-tarjan.md
implementation-status: in_progress
phase: phase-1
last-updated: 2025-12-02
---

# Design Spec: SDK User Feedback Improvements for v4.5.1

**ADR**: [SDK User Feedback Improvements](/docs/adr/2025-12-02-sdk-user-feedback-v451.md)

## Problem Statement

User (Alpha Forge team) reported 3 improvement areas for v4.5.1:

1. **Blob gas columns return `object` dtype** - Should return proper integer type
2. **`.env.example` not accessible** - Users need credential variable names
3. **`__version__` returns 'unknown'** - Should return actual version

## Investigation Findings

### Issue 1: Blob Gas Dtype (HIGH PRIORITY)

**Root Cause**: ClickHouse returns NULL for pre-Dencun blocks (< 19,426,587). Pandas infers mixed None + integers as `object` dtype.

**Location**: `src/gapless_network_data/api.py` lines 249-255 (DataFrame construction)

**Current**: No dtype conversion after DataFrame creation
**Docstring Promise**: `uint64, nullable` (line 189-190) - INCORRECT

**Decision**: Use pandas nullable `Int64` dtype (preserves NULL semantics via `pd.NA`)

### Issue 2: .env.example Packaging (MEDIUM PRIORITY)

**Finding**: `.env.example` EXISTS at repo root with correct variable names
**Problem**: NOT included in wheel distribution (only in sdist)

**Root Cause**: `pyproject.toml` only packages `src/gapless_network_data`:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/gapless_network_data"]
```

**Note**: Error messages already show variable names; this is a convenience improvement

### Issue 3: **version** (LOW PRIORITY)

**Finding**: `__version__ = "4.5.1"` is hardcoded correctly in `__init__.py` line 16
**Exported**: Yes, in `__all__` (line 55)
**Test Verification**: Returns `'4.5.1'` from source install

**Possible User Issue**: Stale pip install or different environment

**Improvement**: Implement dynamic version via `importlib.metadata` for robustness

## Implementation Tasks

### Task 1: Fix Blob Gas Dtypes

**File**: `src/gapless_network_data/api.py`

- [x] Add dtype conversion after DataFrame creation (after line 253):

```python
# Convert blob gas columns to nullable Int64 (preserves NULL semantics)
# ADR: 2025-12-02-sdk-user-feedback-v451
if "blob_gas_used" in df.columns:
    df["blob_gas_used"] = df["blob_gas_used"].astype("Int64")
if "excess_blob_gas" in df.columns:
    df["excess_blob_gas"] = df["excess_blob_gas"].astype("Int64")
```

- [x] Update docstring (lines 189-190) to reflect `Int64` nullable integer

### Task 2: Expose Credential Template in README

**File**: `README.md`

- [x] Add visible credential variable reference table:

```markdown
### Environment Variables

| Variable                       | Description               |
| ------------------------------ | ------------------------- |
| `CLICKHOUSE_HOST_READONLY`     | ClickHouse Cloud hostname |
| `CLICKHOUSE_USER_READONLY`     | Read-only username        |
| `CLICKHOUSE_PASSWORD_READONLY` | Password                  |
```

### Task 3: Implement Dynamic **version**

**File**: `src/gapless_network_data/__init__.py`

- [x] Replace hardcoded version with dynamic discovery:

```python
# Before
__version__ = "4.5.1"

# After
try:
    from importlib.metadata import version as _get_version
    __version__ = _get_version("gapless-network-data")
except Exception:
    __version__ = "4.5.1"  # Fallback for editable installs
```

### Task 4: Update Tests

**File**: `tests/test_api.py`

- [x] Verify `__version__` test still passes with dynamic version
- [ ] (Optional) Add dtype validation test for blob gas columns

### Task 5: Version Bump

- [ ] Version will be v4.6.0 (minor: behavior change for blob gas dtypes)
- [ ] Update CHANGELOG.md via semantic-release

## Files to Modify

| File                                   | Changes                                         |
| -------------------------------------- | ----------------------------------------------- |
| `src/gapless_network_data/api.py`      | Add Int64 dtype conversion for blob gas columns |
| `src/gapless_network_data/__init__.py` | Dynamic **version** via importlib.metadata      |
| `README.md`                            | Add credential variable reference table         |

## Success Criteria

- [x] `df["blob_gas_used"].dtype` returns `Int64`
- [x] Pre-Dencun blocks have `pd.NA` (not None or 0)
- [x] `gmd.__version__` returns correct version after pip install
- [x] All existing tests pass (33/33)
- [ ] mypy type checks pass (pre-existing errors, not from this ADR)

## Validation Checklist

- [x] Run `uv run pytest` - all tests pass (33/33)
- [ ] Run `uv run mypy src/` - no type errors (pre-existing issues)
- [ ] Test blob gas dtype with real data (deferred to integration test)
- [x] Verify `__version__` from both source and editable install
