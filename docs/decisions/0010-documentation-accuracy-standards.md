# MADR-0010: Documentation Accuracy Standards

**Status**: Accepted

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

## Empirical Findings

**Verification Date**: 2025-11-20
**Methods**: MotherDuck SQL queries, Git commit history analysis

### Verified Block Count

**Source**: MotherDuck `SELECT COUNT(*) FROM ethereum_mainnet.blocks`
**Result**: 23,843,490 blocks

**Discrepancies**:

- CLAUDE.md claimed: 23.8M ✅ ACCURATE (within rounding, actual: 23.84M)
- master-roadmap.yaml claimed: 14.57M ❌ INCORRECT (off by 9,273,490 blocks, 63% error)
- master-roadmap.yaml date range: 2020-2025 ❌ INCORRECT (missing 2015-2020, 5 years)

**Correction Applied**: master-roadmap.yaml updated to 23.84M Ethereum blocks (2015-2025)

### Verified Phase 1 Completion Date

**Source**: Git commit history `git log --all --format="%ai | %h | %s" --since="2025-11-08"`
**Result**: 2025-11-11 18:35:32 (commit 84a0f23: "align documentation with operational production state (23.8M blocks)")

**Discrepancies**:

- CLAUDE.md claimed: 2025-11-12 ❌ INCORRECT (1 day late)
- master-roadmap.yaml claimed: 2025-11-10 ❌ INCORRECT (1 day early)
- Git authoritative commit: 2025-11-11 ✅ CORRECT

**Correction Applied**: Both files updated to 2025-11-11 with git verification comment

### Verified Operational Deployment Date

**Source**: Git commit history `git log --all --format="%ai | %s" --since="2025-11-01" | grep -iE "operational|production"`
**Result**: 2025-11-09 15:51:29 (commit 8f820e7: "fix: deploy .strip() fix to VM collector, resolve crash-loop")

**Evidence**: Real-time pipeline became operational on 2025-11-09, monitoring deployed 2025-11-11

### Verification Outputs

**Files Created**:

- `/tmp/block-count-verification.txt` - MotherDuck query result (23,843,490 blocks)
- `/tmp/motherduck-verification.txt` - Discrepancy analysis
- `/tmp/phase1-verification.txt` - Git history for Phase 1 completion
- `/tmp/operational-dates.txt` - Git history for operational deployment
- `/tmp/git-history-verification.txt` - Consolidated git evidence

**Documentation Updated**:

- `CLAUDE.md` - Added 3 verification comments, corrected Phase 1 date (2025-11-12 → 2025-11-11)
- `specifications/master-project-roadmap.yaml` - Corrected block count (14.57M → 23.84M), Phase 1 date (2025-11-10 → 2025-11-11), date range (2020-2025 → 2015-2025)

### Root Cause Analysis

**Why Discrepancies Occurred**:

1. **Block Count Error (63% undercount)**: master-roadmap.yaml manually updated without querying MotherDuck, likely copied from earlier partial backfill state (2020-2025 snapshot)
2. **Phase 1 Date Conflict**: Both files updated independently without git verification, CLAUDE.md used documentation normalization date (2025-11-13), master-roadmap.yaml used earlier reference
3. **Date Range Error**: master-roadmap.yaml assumed 2020 start, didn't verify Ethereum genesis block (2015-07-30) actually loaded

**Mitigation**: Verification script `scripts/verify-documentation-accuracy.sh` will prevent future drift

## Implementation

See Plan 0010 for detailed task breakdown (10 tasks, 6 hours estimated).

**Critical Path**: Execute verification BEFORE any other housekeeping phases (Version Alignment depends on verified dates).

**Status**: Implementation complete (2025-11-20), all discrepancies resolved.
