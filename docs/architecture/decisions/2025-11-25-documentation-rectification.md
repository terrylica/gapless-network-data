# Post-Migration Documentation Rectification

## Status

In Progress

## Date

2025-11-25

## Context

MADR-0013 (MotherDuck to ClickHouse Migration) completed operationally on 2025-11-25, but documentation remains in a hybrid state with ~200+ stale MotherDuck references across 40+ files.

**Scope**: Documentation-only changes. No infrastructure or code modifications.

**Categories Requiring Updates**:

| Category           | Files                           | Issue                                 |
| ------------------ | ------------------------------- | ------------------------------------- |
| Root Documentation | README.md, CLAUDE.md            | Outdated architecture description     |
| Architecture Docs  | OVERVIEW.md, dual-pipeline docs | Describe deprecated MotherDuck system |
| Skills             | motherduck-pipeline-operations  | Hardcoded MotherDuck references       |
| Decision Records   | MADR-0003, 0004                 | Missing supersession notes            |
| Specifications     | motherduck-\*.yaml              | Need archival                         |

**Constraints**:

- Documentation must remain accurate for operational infrastructure
- No backward-compatibility needed (clean migration)
- Skills must function with ClickHouse (not MotherDuck)

## Decision

Systematically rectify all documentation to reflect ClickHouse as the production database:

1. **Archive deprecated content** (not delete) - preserve historical context
2. **Update active documentation** - replace MotherDuck references with ClickHouse
3. **Rename skills** - `motherduck-pipeline-operations` → archived, create new ClickHouse-focused skill
4. **Add supersession notes** - link old decisions to MADR-0013

## Consequences

**Positive**:

- Documentation accurately reflects operational infrastructure
- Skills function correctly with ClickHouse
- Clear audit trail via archived files

**Negative**:

- One-time effort required (~6-7 hours)
- Some external links may break (mitigated by redirects in archived files)

## Implementation

**Plan**: [Documentation Rectification Plan](/docs/development/plan/2025-11-25-documentation-rectification/plan.md)

**Phases**:

1. CRITICAL: README.md, OVERVIEW.md, skill refactoring
2. Architecture: Archive deprecated files, create ClickHouse docs
3. Deployment: Fix scripts and folder naming
4. Decision Records: Add supersession notes
5. Cleanup: Archive specifications, add deprecation notices

## Related

- [MotherDuck to ClickHouse Migration](/docs/architecture/decisions/2025-11-25-motherduck-clickhouse-migration.md)
- [Documentation Rectification Plan](/docs/development/plan/2025-11-25-documentation-rectification/plan.md)
