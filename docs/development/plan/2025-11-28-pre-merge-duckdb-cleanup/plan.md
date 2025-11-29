# Plan: Pre-Merge DuckDB Elimination & Code Quality Audit

**ADR**: [2025-11-28-pre-merge-duckdb-cleanup](../../architecture/decisions/2025-11-28-pre-merge-duckdb-cleanup.md)
**Branch**: `migrate-to-clickhouse` → `main`
**Created**: 2025-11-28

---

## Context

After completing ClickHouse migration (2025-11-25), the codebase contains extensive DuckDB/MotherDuck legacy code that is no longer used. Before merging `migrate-to-clickhouse` branch to `main`, this technical debt must be eliminated.

**Current State**:

- SDK queries ClickHouse via `api.py` (operational)
- `db.py` module is 100% DuckDB code with no active imports
- Deployment scripts dual-write to both MotherDuck and ClickHouse
- 50+ files contain DuckDB references

**Decision**: Aggressive cleanup - delete all DuckDB code, remove MotherDuck from dual-write scripts, standardize type hints.

---

## Plan

### Phase 1: Core Package Cleanup

#### 1.1 Delete db.py Module (DuckDB-specific)

**File**: `src/gapless_network_data/db.py`

**Action**: DELETE entirely (270 lines)

- 100% DuckDB code (imports, connections, queries)
- SDK now uses ClickHouse via api.py
- No active imports of this module

#### 1.2 Remove DuckDB from pyproject.toml

**File**: `pyproject.toml`

**Changes**:

- DELETE `"duckdb>=1.1.0",` dependency
- DELETE duplicate `[dependency-groups]` section (if present)

#### 1.3 Delete Root Test File

**File**: `test_db_init.py`

**Action**: DELETE (tests DuckDB initialization - no longer needed)

---

### Phase 2: Deployment Script Cleanup

#### 2.1 DELETE Historical Backfill Scripts (Completed 2025-11-11)

| File                                         | Reason                                 |
| -------------------------------------------- | -------------------------------------- |
| `deployment/backfill/historical_backfill.py` | BigQuery→MotherDuck backfill completed |
| `deployment/backfill/chunked_backfill.sh`    | Orchestrator for above                 |

#### 2.2 DELETE MotherDuck Gap Detection (Replaced 2025-11-25)

| File                                                              | Reason                        |
| ----------------------------------------------------------------- | ----------------------------- |
| `deployment/gcp-functions/motherduck-monitor/analyze_all_gaps.py` | Dev tool, MotherDuck-specific |
| `deployment/gcp-functions/motherduck-monitor/investigate_gap.py`  | Dev tool, MotherDuck-specific |

**Note**: Keep `deployment/gcp-functions/gap-detector/` (ClickHouse version) - verify it's the active deployment.

#### 2.3 DELETE Migration Utilities (One-time use completed)

| File                                       | Reason                                |
| ------------------------------------------ | ------------------------------------- |
| `scripts/clickhouse/fill_gap.py`           | Gap filling completed                 |
| `scripts/clickhouse/verify_consistency.py` | Dual-write validation completed       |
| `scripts/clickhouse/deploy_cutover.py`     | Cutover automation (no longer needed) |

#### 2.4 REFACTOR Dual-Write Scripts → ClickHouse-Only

**Cloud Run Job**: `deployment/cloud-run/main.py`

**Remove**:

- All `import duckdb` statements
- All `MOTHERDUCK_*` environment variable handling
- All `duckdb.connect('md:')` connection code
- All MotherDuck write functions

**Keep**:

- BigQuery query logic
- ClickHouse write logic
- Healthchecks.io ping logic

**VM Real-Time Collector**: `deployment/vm/realtime_collector.py`

**Remove**:

- All `import duckdb` statements
- All `MOTHERDUCK_*` environment variable handling
- All `duckdb.connect('md:')` connection code
- Background thread for MotherDuck writes

**Keep**:

- Alchemy WebSocket subscription
- ClickHouse write logic
- Block processing logic

**Data Quality Checker**: `deployment/cloud-run/data_quality_checker.py`

**Remove**:

- All MotherDuck freshness check code
- `import duckdb`

**Keep**:

- ClickHouse freshness check (primary)
- Pushover alerting

---

### Phase 3: Documentation Cleanup

#### 3.1 DELETE Obsolete Documentation Files

| File                                              | Reason                              |
| ------------------------------------------------- | ----------------------------------- |
| `docs/architecture/duckdb-strategy.md`            | DuckDB integration guide - obsolete |
| `specifications/duckdb-schema-specification.yaml` | DuckDB schema - superseded          |
| `specifications/duckdb-integration-strategy.yaml` | DuckDB integration - superseded     |

#### 3.2 UPDATE CLAUDE.md

**File**: `CLAUDE.md`

**Remove sections**:

- "DuckDB Architecture & Strategy"
- "Local Development (Optional)" storage architecture
- References to `~/.cache/gapless-network-data/data.duckdb`

**Update sections**:

- "Data Storage Architecture" - Remove DuckDB local storage option
- "Feature Roadmap" - Remove DuckDB-related items

#### 3.3 DELETE MotherDuck Documentation

| File/Directory                        | Reason                                   |
| ------------------------------------- | ---------------------------------------- |
| `docs/motherduck/` (entire directory) | MotherDuck integration docs - deprecated |

---

### Phase 4: Code Quality Standardization

#### 4.1 Standardize Type Hints to `X | None` (PEP 604)

**Files to update** (change `Optional[X]` → `X | None`):

| File                                                       | Lines to Change |
| ---------------------------------------------------------- | --------------- |
| `src/gapless_network_data/exceptions.py`                   | Multiple lines  |
| `src/gapless_network_data/collectors/mempool_collector.py` | Multiple lines  |
| `src/gapless_network_data/probe.py`                        | Multiple lines  |
| `src/gapless_network_data/validation/models.py`            | Multiple lines  |

**Also update**: Remove `from typing import Optional` imports where no longer needed.

#### 4.2 Fix Deprecated datetime Method

**File**: `src/gapless_network_data/validation/models.py`

**Change**:

```python
# Old
default_factory=lambda: datetime.utcnow()

# New
default_factory=lambda: datetime.now(timezone.utc)
```

---

### Phase 5: Build Artifact Cleanup

#### 5.1 Update .gitignore

**Add these entries**:

```gitignore
# Linting/checking results
.lychee-results.*
.lycheecache
.lint-relative-paths-results.txt

# Coverage (already present but verify)
.coverage
coverage.json
```

**Remove duplicate**:

- `dist/` (if duplicated)

#### 5.2 Delete Build Artifacts at Root

| File                               | Action                   |
| ---------------------------------- | ------------------------ |
| `.coverage`                        | DELETE                   |
| `coverage.json`                    | DELETE                   |
| `.lychee-results.json`             | DELETE                   |
| `.lychee-results.txt`              | DELETE                   |
| `.lycheecache`                     | DELETE                   |
| `.lint-relative-paths-results.txt` | DELETE                   |
| `dist/*.whl`                       | DELETE (outdated wheels) |

---

### Phase 6: Skills & Archive Cleanup

#### 6.1 DELETE Archived MotherDuck Skills

| Directory                                                | Reason                      |
| -------------------------------------------------------- | --------------------------- |
| `.claude/skills/archive/motherduck-pipeline-operations/` | Entirely MotherDuck-focused |

#### 6.2 UPDATE Skills with DuckDB References

| File                                                                                 | Action                              |
| ------------------------------------------------------------------------------------ | ----------------------------------- |
| `.claude/skills/CATALOG.md`                                                          | Remove duckdb-patterns.md reference |
| `.claude/skills/blockchain-data-collection-validation/references/duckdb-patterns.md` | DELETE                              |

---

## Execution Order

Execute in this order to minimize broken state:

1. **Phase 5**: Clean build artifacts first (no code impact)
2. **Phase 1**: Delete db.py, update pyproject.toml, delete test_db_init.py
3. **Phase 2**: Refactor/delete deployment scripts
4. **Phase 4**: Standardize type hints
5. **Phase 3**: Update documentation
6. **Phase 6**: Clean skills directory
7. **Final**: Run tests, commit, merge to main

---

## Task List

- [ ] Phase 5: Clean build artifacts and update .gitignore
- [ ] Phase 1.1: Delete `src/gapless_network_data/db.py`
- [ ] Phase 1.2: Remove duckdb from `pyproject.toml`
- [ ] Phase 1.3: Delete `test_db_init.py`
- [ ] Phase 2.1: Delete historical backfill scripts
- [ ] Phase 2.2: Delete MotherDuck gap detection scripts
- [ ] Phase 2.3: Delete migration utilities
- [ ] Phase 2.4: Refactor `deployment/cloud-run/main.py`
- [ ] Phase 2.4: Refactor `deployment/vm/realtime_collector.py`
- [ ] Phase 2.4: Refactor `deployment/cloud-run/data_quality_checker.py`
- [ ] Phase 4.1: Standardize type hints in exceptions.py
- [ ] Phase 4.1: Standardize type hints in mempool_collector.py
- [ ] Phase 4.1: Standardize type hints in probe.py
- [ ] Phase 4.2: Fix datetime in validation/models.py
- [ ] Phase 3.1: Delete obsolete documentation files
- [ ] Phase 3.2: Update CLAUDE.md
- [ ] Phase 3.3: Delete docs/motherduck/ directory
- [ ] Phase 6.1: Delete archived MotherDuck skills
- [ ] Phase 6.2: Update skills CATALOG.md
- [ ] Verify: `uv sync` succeeds
- [ ] Verify: `uv run pytest` passes
- [ ] Verify: No `duckdb` in `grep -r "duckdb" src/`

---

## Verification Checklist

After cleanup, verify:

- [ ] `uv sync` succeeds (no duckdb dependency)
- [ ] `uv run pytest` passes all tests
- [ ] `uv run python -c "import gapless_network_data"` works
- [ ] `gmd.fetch_blocks(limit=5)` returns data from ClickHouse
- [ ] No `duckdb` in `grep -r "duckdb" src/`
- [ ] No `Optional[` in `grep -r "Optional\[" src/gapless_network_data/`

---

## Files Summary

### DELETE (23 files)

- `src/gapless_network_data/db.py`
- `test_db_init.py`
- `deployment/backfill/historical_backfill.py`
- `deployment/backfill/chunked_backfill.sh`
- `deployment/gcp-functions/motherduck-monitor/analyze_all_gaps.py`
- `deployment/gcp-functions/motherduck-monitor/investigate_gap.py`
- `scripts/clickhouse/fill_gap.py`
- `scripts/clickhouse/verify_consistency.py`
- `scripts/clickhouse/deploy_cutover.py`
- `docs/architecture/duckdb-strategy.md`
- `specifications/duckdb-schema-specification.yaml`
- `specifications/duckdb-integration-strategy.yaml`
- `docs/motherduck/` (entire directory, ~6 files)
- `.claude/skills/archive/motherduck-pipeline-operations/` (entire directory)
- `.claude/skills/blockchain-data-collection-validation/references/duckdb-patterns.md`
- Build artifacts (6 files)

### REFACTOR (3 files)

- `deployment/cloud-run/main.py` - Remove MotherDuck code paths
- `deployment/vm/realtime_collector.py` - Remove MotherDuck code paths
- `deployment/cloud-run/data_quality_checker.py` - Remove MotherDuck checks

### UPDATE (8 files)

- `pyproject.toml` - Remove duckdb dependency
- `CLAUDE.md` - Remove DuckDB sections
- `src/gapless_network_data/exceptions.py` - Type hints
- `src/gapless_network_data/collectors/mempool_collector.py` - Type hints
- `src/gapless_network_data/probe.py` - Type hints
- `src/gapless_network_data/validation/models.py` - Type hints + datetime fix
- `.gitignore` - Add entries, remove duplicate
- `.claude/skills/CATALOG.md` - Remove DuckDB reference
