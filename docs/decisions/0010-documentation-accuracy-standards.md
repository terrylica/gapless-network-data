# MADR-0010: Documentation Accuracy Standards

**Status**: Proposed

**Date**: 2025-11-20

**Related**: Plan 0010 (`docs/development/plan/0010-documentation-accuracy/plan.md`)

## Context

Documentation accuracy crisis discovered via parallel agent investigation:

**Data Discrepancies**:

- Block count: 23.8M (CLAUDE.md) vs 14.57M (master-roadmap.yaml) - 9.23M difference
- Phase 1 completion: 2025-11-12 (CLAUDE.md) vs 2025-11-10 (master-roadmap.yaml)
- Status claims: "Operational" without verification proof

**Root Cause**:

- Manual documentation updates without empirical verification
- Copy-paste from outdated sources
- No verification queries documented

**Impact**:

- Trust erosion: Cannot trust any quantitative claim
- Wrong architectural decisions: Incorrect data leads to poor choices
- Debugging hindrance: Wrong block counts obstruct troubleshooting
- Inaccurate stakeholder reporting

## Decision

All quantitative claims (block counts, dates, performance metrics, status assertions) require empirical verification from primary sources:

**Primary Sources**:

1. **Block counts**: MotherDuck `SELECT COUNT(*) FROM ethereum_mainnet.blocks`
2. **Dates**: Git commit history `git log --grep="..." --format="%ai %s"`
3. **Performance metrics**: Actual measurements, not estimates
4. **Status**: Healthchecks.io API queries, not manual assertions

**Verification Protocol**:

1. Query primary source
2. Record raw result in `/tmp/*-verification.txt`
3. Update documentation with verified value only
4. Add verification note: `<!-- Verified YYYY-MM-DD via {source} -->`
5. Document discrepancies in MADRs

**Ongoing Verification**:

- Create `scripts/verify-documentation-accuracy.sh` with all verification queries
- Schedule weekly verification (optional CI job)
- Pre-commit hook: Warn on quantitative claims without verification comments

## Consequences

**Positive**:

- Trustworthy documentation with reproducible verification
- Catches drift early (automated verification)
- Audit trail for all data claims
- Reproducible for stakeholders

**Negative**:

- Slower documentation updates (requires database/API access)
- Dependency on MotherDuck availability
- Initial investigation overhead

**Risks**:

- MotherDuck connection failures block documentation updates (Mitigation: Offline verification with local DuckDB cache)
- Git history incomplete for early commits (Mitigation: Mark as "estimated" when git evidence unclear)

## Alternatives Considered

### Alternative 1: Trust Existing Numbers

**Rejected**: Already proven inaccurate (23.8M vs 14.57M discrepancy)

### Alternative 2: Round to Nearest Million

**Rejected**: Hides precision, masks underlying issues (e.g., gap in data collection)

### Alternative 3: Remove Quantitative Claims

**Rejected**: Documentation becomes vague and unusable ("many blocks loaded")

## Validation

**Block Count Verification**:

```sql
-- MotherDuck
SELECT COUNT(*) as total_blocks FROM ethereum_mainnet.blocks;
-- Record result, update CLAUDE.md only with verified count
```

**Date Verification**:

```bash
# Git history
git log --all --format="%ai | %s" --grep="Phase 1\|COMPLETED\|operational"
-- Identify authoritative completion date, update docs
```

**Success Criteria**:

- Zero discrepancies between CLAUDE.md and master-roadmap.yaml
- All quantitative claims have verification comments
- `scripts/verify-documentation-accuracy.sh` executes without errors

## Implementation

See Plan 0010 for detailed task breakdown (10 tasks, 6 hours estimated).

**Critical Path**: Execute verification BEFORE any other housekeeping phases (Version Alignment depends on verified dates).
