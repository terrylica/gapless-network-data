# MADR-0009: Version Alignment Strategy

**Status**: Proposed

**Date**: 2025-11-20

**Related**: Plan 0009 (`docs/development/plan/0009-version-alignment/plan.md`)

## Context

Version misalignment across documentation:

**Current State**:

- pyproject.toml: `v3.1.1` (source of truth, controlled by semantic-release)
- CLAUDE.md: Claims `v3.0.0` (7 releases behind)
- README.md: Claims `v2.4.0` (10 releases behind)
- master-project-roadmap.yaml: Claims `v3.0.0` (7 releases behind)

**Gap**: 7 releases undocumented (v2.5.0 → v3.1.1)

**Impact**:

- **Blocks PyPI publishing**: `twine upload` will fail due to README.md/pyproject.toml version mismatch
- **User confusion**: Features available in v3.1.1 not documented in v3.0.0 guides
- **Trust erosion**: Version inconsistency signals poor maintenance

## Decision

Synchronize v3.1.1 across all documentation files using **git history as source of truth**:

1. Extract authoritative version timeline from git tags
2. Update CLAUDE.md: `v3.0.0` → `v3.1.1` (3 locations)
3. Update README.md: `v2.4.0` → `v3.1.1`
4. Update master-project-roadmap.yaml: `v3.0.0` → `v3.1.1`
5. Backfill CHANGELOG.md with 7 missing releases (v2.5.0 through v3.1.1)
6. Implement pre-commit hook: Enforce version consistency (all refs must match pyproject.toml)

**Source of Truth Hierarchy**:

1. Git tags (canonical versioning)
2. pyproject.toml (package metadata)
3. All other files derive from these

## Consequences

**Positive**:

- Single source of truth for version (git tags)
- Enables PyPI publishing (version consistency restored)
- Clear feature tracking (CHANGELOG documents all releases)
- Prevents future drift (pre-commit hook)

**Negative**:

- Requires backfilling CHANGELOG.md for 7 releases
- One-time synchronization effort across 4 files

**Risks**:

- If git tags are incorrect, documentation will reflect incorrect versions (Mitigation: Verify git tags match actual releases via semantic-release commit history)

## Alternatives Considered

### Alternative 1: Bump to v4.0.0

**Rejected**: Hides version drift problem, loses historical accuracy

### Alternative 2: Leave As-Is

**Rejected**: Blocks PyPI publishing, confuses users

### Alternative 3: Sync to v3.0.0

**Rejected**: Ignores 7 actual releases in git history

## Validation

**Version Consistency Check**:

```bash
# All files must report v3.1.1
grep -r "version.*3\.[0-9]\.[0-9]" CLAUDE.md README.md pyproject.toml specifications/master-project-roadmap.yaml | \
  grep -v "3.1.1" && echo "FAIL" || echo "PASS"
```

**CHANGELOG Completeness**:

```bash
# All 7 versions documented
for version in v2.5.0 v2.6.0 v2.7.0 v2.8.0 v2.9.0 v3.0.0 v3.1.0 v3.1.1; do
    grep -q "$version" CHANGELOG.md || echo "MISSING: $version"
done
```

**Pre-commit Hook Active**:

```bash
# Hook blocks mismatched versions
git commit --allow-empty -m "test: version check" --no-verify && \
    echo "FAIL: Hook not enforcing" || echo "PASS: Hook active"
```

## Implementation

See Plan 0009 for detailed task breakdown (7 tasks, 4 hours estimated).

**Dependency**: Requires Phase 2 (Documentation Accuracy) completion first - verified dates needed for CHANGELOG.
