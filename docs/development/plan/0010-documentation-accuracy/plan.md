# Plan 0010: Documentation Accuracy

**ADR ID**: 0010
**Status**: In Progress
**Created**: 2025-11-20
**Related MADR**: `docs/decisions/0010-documentation-accuracy-standards.md`

## (a) Context

**Why This Plan Exists**:

Parallel agent investigation discovered critical documentation discrepancies:

**Block Count Conflict**:

- CLAUDE.md claims: 23.8M Ethereum blocks (2015-2025)
- master-roadmap.yaml claims: 14.57M blocks (2020-2025)
- Difference: 9.23M blocks (63% discrepancy)

**Date Conflicts**:

- Phase 1 completion: 2025-11-12 (CLAUDE.md) vs 2025-11-10 (master-roadmap.yaml)
- Operational deployment: Multiple conflicting claims across commits

**Root Cause**: Manual documentation updates without empirical verification from primary sources (MotherDuck database, git history).

**Impact**: Trust erosion, wrong architectural decisions, debugging hindrance.

## (b) Plan

**Objective**: Establish ground truth via empirical verification, update all documentation with verified data only.

**Verification Sources**:

1. **MotherDuck Database** (Primary for metrics):
   - Block count: `SELECT COUNT(*) FROM ethereum_mainnet.blocks`
   - Date range: `SELECT MIN(timestamp), MAX(timestamp), MIN(number), MAX(number)`
   - Data freshness: `SELECT MAX(timestamp), CURRENT_TIMESTAMP - MAX(timestamp)`

2. **Git History** (Primary for dates):
   - Phase 1 completion: `git log --grep="Phase 1.*COMPLETED"`
   - Operational deployment: `git log --grep="operational\|production"`
   - Version releases: `git log --tags`

**Implementation Approach**:

1. Execute all verification queries → Save results to `/tmp/*-verification.txt`
2. Analyze discrepancies → Document in MADR-0010
3. Update CLAUDE.md with verified block count (23.84M actual from MotherDuck)
4. Update master-roadmap.yaml with verified dates and block count
5. Add verification comments: `<!-- Verified YYYY-MM-DD via {source} -->`
6. Create `scripts/verify-documentation-accuracy.sh` for ongoing verification

**Rollback Strategy**: Keep backup of original claims in MADR-0010, git revert if verified data proves incorrect.

## (c) Task List

**2.1 Set up MotherDuck connection** ✅ COMPLETED

- Command: `duckdb -c "SELECT 1" md:`
- Validation: Query returns result
- Status: Connection established, database `ethereum_mainnet` confirmed

**2.2 Execute block count verification query** ✅ COMPLETED

- Command: `SELECT COUNT(*) FROM ethereum_mainnet.blocks`
- Result: **23,843,490 blocks** (23.84M)
- Validation: CLAUDE.md claim (23.8M) is ACCURATE, master-roadmap.yaml (14.57M) is INCORRECT
- Output saved: `/tmp/block-count-verification.txt`

**2.3 Execute date range verification query** 🔄 IN PROGRESS

- Command: `SELECT MIN(timestamp), MAX(timestamp), MIN(number), MAX(number) FROM ethereum_mainnet.blocks`
- Expected: Earliest ~2015-07-30 (Ethereum genesis), Latest ~2025-11-20
- Output: `/tmp/date-range-verification.txt`

**2.4 Execute data freshness verification query** ⏳ PENDING

- Command: `SELECT MAX(timestamp), CURRENT_TIMESTAMP - MAX(timestamp) FROM ethereum_mainnet.blocks`
- Expected: Staleness < 24 hours (if real-time pipeline operational)
- Output: `/tmp/freshness-verification.txt`
- Dependency: Task 2.3

**2.5 Verify Phase 1 completion date from git history** ⏳ PENDING

- Command: `git log --grep="Phase 1" --format="%ai | %s" --since="2025-11-01"`
- Candidates: 2025-11-10 (master-roadmap) vs 2025-11-12 (CLAUDE.md)
- Output: `/tmp/phase1-dates.txt`
- Dependency: None

**2.6 Verify operational deployment date from git** ⏳ PENDING

- Command: `git log --grep="operational\|production" --format="%ai | %s"`
- Cross-reference: MotherDuck latest block timestamp with git commits
- Output: `/tmp/operational-dates.txt`
- Dependency: Task 2.3 (need latest block timestamp)

**2.7 Update CLAUDE.md with verified block count** ⏳ PENDING

- Find: `23.8M` (already accurate, but add verification comment)
- Add: `<!-- Verified 2025-11-20 via MotherDuck: 23,843,490 blocks -->`
- Validation: Verification comment present
- Dependency: Tasks 2.2 (completed), 2.3, 2.4

**2.8 Update master-roadmap.yaml with verified dates and metrics** ⏳ PENDING

- Update: `data_loaded: "14.57M"` → `"23.84M Ethereum blocks (2015-2025)"`
- Update: `completion_date: "2025-11-10"` → verified date from git
- Update: `last_updated:` to current timestamp
- Validation: All metrics match MotherDuck + git history
- Dependency: ALL verification tasks (2.2-2.6)

**2.9 Document discrepancies in MADR-0010** ⏳ PENDING

- Record: Original incorrect values (14.57M, dates)
- Record: Verified correct values (23.84M, git dates)
- Record: Verification methodology
- Update: MADR-0010 Status from Proposed → Accepted
- Dependency: Tasks 2.2-2.6 (all verification complete)

**2.10 Create verification script** ⏳ PENDING

- Script: `scripts/verify-documentation-accuracy.sh`
- Contents: All MotherDuck queries + git history checks
- Output: Pass/fail with specific discrepancies
- Validation: Script executable, runs without errors
- Dependency: Task 2.9 (verification methodology documented)

## Empirical Findings (In Progress)

### Verified Data

**Block Count** (Source: MotherDuck, Verified: 2025-11-20):

- Actual: 23,843,490 blocks
- CLAUDE.md claim: 23.8M ✅ ACCURATE
- master-roadmap.yaml claim: 14.57M ❌ INCORRECT (off by 9.27M blocks, 63% error)

**Date Range** (Source: MotherDuck, Pending):

- Earliest block: [Pending query result]
- Latest block: [Pending query result]
- Expected: 2015-07-30 to 2025-11-20

**Data Freshness** (Source: MotherDuck, Pending):

- Latest timestamp: [Pending query result]
- Staleness: [Pending query result]
- Operational threshold: < 24 hours

**Phase 1 Completion Date** (Source: Git, Pending):

- CLAUDE.md claim: 2025-11-12
- master-roadmap.yaml claim: 2025-11-10
- Git evidence: [Pending analysis]

### Discrepancies to Document

1. **Block Count**: master-roadmap.yaml 63% undercount (14.57M vs 23.84M actual)
2. **Phase 1 Date**: 2-day discrepancy (pending git verification)
3. **Data Range**: CLAUDE (2015-2025) vs master-roadmap (2020-2025) - pending verification

## Next Actions

1. ⏳ Wait for date range query completion (Task 2.3)
2. ⏳ Execute freshness query (Task 2.4)
3. ⏳ Analyze git history for authoritative dates (Tasks 2.5-2.6)
4. ⏳ Update all documentation with verified data (Tasks 2.7-2.8)
5. ⏳ Create ongoing verification script (Task 2.10)

## Success Criteria

- ✅ MotherDuck connection established
- ✅ Block count verified: 23.84M actual
- ⏳ Date range verified (in progress)
- ⏳ Freshness verified
- ⏳ Phase 1 date verified from git
- ⏳ All documentation updated with verified data
- ⏳ Zero discrepancies between CLAUDE.md and master-roadmap.yaml
- ⏳ Verification script functional
