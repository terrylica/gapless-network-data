# MADR-0012: Build Artifact Cleanup Policy

**Status**: Proposed

**Date**: 2025-11-20

**Related**: Plan 0012 (`docs/development/plan/0012-build-artifact-cleanup/plan.md`)

## Context

Build artifacts consuming 497 MB in working directory:

**Current State**:

- `dist/` (71 MB): PyPI build artifacts (wheels, tarballs)
- `.venv/` (342 MB): Python virtual environment dependencies
- `scratch/*.duckdb` (84 MB): Test database files from POC work
- `node_modules/` (0 MB currently, but pattern should be blocked)

**Root Cause**:

- Incomplete .gitignore (missing patterns: `dist/`, `.venv/`, `*.duckdb`)
- Local testing without cleanup procedures
- No CI validation to prevent artifact commits

**Impact**:

- **Performance**: Slow git operations (status, diff, add)
- **Risk**: Accidental binary commits (leak secrets, bloat repository)
- **Disk**: Wasted space on reproducible build artifacts
- **CI/CD**: Potential artifact conflicts in containerized builds

## Decision

1. **Enforce .gitignore**: Add missing patterns

   ```gitignore
   # Build artifacts
   dist/
   build/
   *.egg-info/

   # Virtual environments
   .venv/
   venv/
   env/

   # Dependencies
   node_modules/

   # Database files
   *.duckdb
   *.db
   *.db-shm
   *.db-wal

   # Temporary files
   scratch/*.duckdb
   /tmp/
   ```

2. **One-time Cleanup**: Remove all ignored files from working directory

   ```bash
   git clean -fdX  # Delete all ignored files
   ```

3. **Documentation**: Update development guide with cleanup procedures
   - Standard cleanup: `git clean -fdX`
   - Rebuild environment: `uv sync`
   - Pre-build cleanup: `rm -rf dist/ build/`

4. **CI Validation**: Fail builds if artifact directories exist in commits
   ```yaml
   # .github/workflows/artifact-check.yml
   - run: |
       git ls-files | grep -E '^(dist|\.venv|node_modules)/' && exit 1 || exit 0
   ```

## Consequences

**Positive**:

- Fast git operations (clean working directory)
- No binary commits (prevented by .gitignore + CI)
- Clear working directory (only source code tracked)
- Disk space recovered (497 MB)

**Negative**:

- Developers must rebuild .venv after cleanup: `uv sync`
- One-time download cost for dependencies

**Risks**:

- Accidental deletion of non-ignored DuckDB files with important data (Mitigation: Backup `scratch/*.duckdb` before cleanup, document critical files with KEEP comments)

## Alternatives Considered

### Alternative 1: `git clean -fdx` (Clean Everything)

**Rejected**: Too aggressive, deletes untracked code files

### Alternative 2: Leave Artifacts

**Rejected**: Continues wasting space, risks accidental commits

### Alternative 3: Git LFS

**Rejected**: Overkill for files that should never be committed

## Validation

**No Ignored Files in Working Directory**:

```bash
git status --ignored | grep -q "^!!" && echo "FAIL" || echo "PASS"
```

**.gitignore Patterns Complete**:

```bash
for pattern in "dist/" ".venv/" "*.duckdb" "node_modules/"; do
    git check-ignore "$pattern" || echo "MISSING: $pattern"
done
```

**Disk Space Recovered**:

```bash
# Before cleanup: ~497 MB
# After cleanup: ~0 MB
du -sh dist/ .venv/ scratch/*.duckdb 2>/dev/null || echo "Cleanup successful"
```

**Environment Rebuildable**:

```bash
uv sync && uv run pytest && echo "PASS"
```

## Implementation

See Plan 0012 for detailed task breakdown (10 tasks, 3 hours estimated).

**Dependency**: Requires stable .gitignore (Phase 3 link conversion complete).
