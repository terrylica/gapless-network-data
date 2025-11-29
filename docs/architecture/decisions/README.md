# Architectural Decision Records

Date-based ADRs documenting key architectural and operational decisions.

## Naming Convention

```
YYYY-MM-DD-slug.md
```

- **Date**: Decision date (not creation date)
- **Slug**: Lowercase, hyphen-separated description
- **No sequential numbers**: Avoids git merge conflicts

## Directory Structure

```
docs/
├── architecture/
│   └── decisions/           # ADR documents (YYYY-MM-DD-slug.md)
└── development/
    └── plan/
        └── YYYY-MM-DD-slug/ # Implementation plans
            └── plan.md
```

## ADR Format

```markdown
# Title (no date prefix in heading)

## Status

Accepted | Proposed | Deprecated | Superseded

## Date

YYYY-MM-DD

## Context

Problem statement and background.

## Decision

Chosen solution with rationale.
Include Mermaid diagrams where helpful.

## Consequences

### Positive

### Negative

### Mitigation

## Validation

Test cases and verification criteria.

## Related

Links to related ADRs using repository-relative paths.
```

## Plan Format

Each ADR should have a corresponding plan in `/docs/development/plan/YYYY-MM-DD-slug/plan.md`:

```markdown
# Plan: Title

**ADR**: [/docs/architecture/decisions/YYYY-MM-DD-slug.md](/docs/architecture/decisions/YYYY-MM-DD-slug.md)

**Created**: YYYY-MM-DD

**Status**: In Progress | Completed

---

## Task List

- [x] Completed task
- [ ] Pending task

## Progress Log

| Date | Update |
| ---- | ------ |
```

## ADR Index

### November 2025

| Date       | Slug                                     | Summary                                                   |
| ---------- | ---------------------------------------- | --------------------------------------------------------- |
| 2025-11-28 | realtime-collector-transaction-count-fix | Fix transaction_count=0 via eth_getBlockByNumber          |
| 2025-11-28 | healthchecks-gap-detector-enable         | Enable Dead Man's Switch for gap detector                 |
| 2025-11-26 | gap-detector-clickhouse-fix              | Migrate gap detector to ClickHouse-native queries         |
| 2025-11-25 | motherduck-clickhouse-migration          | Migrate production database from MotherDuck to ClickHouse |
| 2025-11-25 | documentation-rectification              | Post-migration documentation synchronization              |
| 2025-11-20 | version-alignment-strategy               | Package version alignment with data state                 |
| 2025-11-20 | documentation-accuracy-standards         | Verified claims, deprecation process                      |
| 2025-11-20 | link-format-enforcement                  | CI/CD link validation via lychee                          |
| 2025-11-20 | build-artifact-cleanup-policy            | Scratch directory lifecycle management                    |
| 2025-11-13 | healthchecks-grace-period-calibration    | Dead Man's Switch grace period optimization               |
| 2025-11-13 | exception-handler-notifications          | Pushover alert integration for pipeline failures          |
| 2025-11-13 | motherduck-timeout-fallback              | Connection timeout handling (SUPERSEDED)                  |
| 2025-11-13 | staleness-threshold-calibration          | Data freshness monitoring (SUPERSEDED)                    |
| 2025-11-13 | root-claude-scope                        | Essential context + navigation hub strategy               |
| 2025-11-13 | child-claude-spokes                      | Local navigation hub pattern                              |
| 2025-11-13 | skills-extraction                        | Workflow extraction criteria                              |
| 2025-11-13 | link-format                              | Relative GFM paths for portability                        |
