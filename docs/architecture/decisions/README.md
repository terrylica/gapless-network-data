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
|------|--------|
```

## Current ADRs

| Date | Slug | Summary |
|------|------|---------|
| 2025-11-28 | realtime-collector-transaction-count-fix | Fix transaction_count=0 via eth_getBlockByNumber |

## Legacy ADRs

Sequential-numbered MADRs (0001-0016) remain in `/docs/decisions/` for historical reference. New decisions use the date-based format.
