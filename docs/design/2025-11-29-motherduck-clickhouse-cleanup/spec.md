# Design Spec: MotherDuck to ClickHouse Cleanup

**Status**: Complete
**Last Updated**: 2025-11-29
**ADR**: [MotherDuck to ClickHouse Cleanup](/docs/adr/2025-11-29-motherduck-clickhouse-cleanup.md)

## Executive Summary

66 files contain MotherDuck references. The code already uses ClickHouse - only **naming and documentation** need cleanup. GCP resources retain legacy names (renaming requires recreation with downtime risk).

## Success Criteria

### Phase 1: Safe Changes

- [x] `deployment/gcp-functions/motherduck-monitor/` directory deleted
- [x] `motherduck-token` GCP secret deleted
- [x] Historical note in `gap-monitor/README.md` updated
- [x] Service account display name updated

### Phase 2: Documentation Updates

- [x] 9 files with substantial MotherDuck content fully rewritten
- [x] 15 files with simple terminology swaps updated
- [x] Broken ADR link in `docs/architecture/README.md` fixed

### Phase 3: Deployment

- [x] Gap monitor deployed to Cloud Functions with two-tier alerting
- [x] All changes committed and pushed

## Recommended Approach: Phased Cleanup

### Phase 1: Safe Changes (No GCP Impact)

**1.1 Delete Duplicate Directory**

```bash
git rm -rf deployment/gcp-functions/motherduck-monitor/
```

- Identical to `gap-monitor/` (verified via diff)
- Risk: None

**1.2 Delete Unused GCP Secret**

```bash
gcloud secrets delete motherduck-token --project=eonlabs-ethereum-bq
```

- Not referenced by any code (verified)
- Risk: Low

**1.3 Fix Historical Note in README**

Update `/deployment/gcp-functions/gap-monitor/README.md` lines 3-5:

```markdown
> **Historical Note**: GCP resources retain legacy "motherduck" names from the pre-ClickHouse
> migration (2025-11-25). These include: `motherduck-gap-detector` (Cloud Function),
> `motherduck-monitor-sa` (Service Account), `motherduck-monitor-trigger` (Cloud Scheduler).
> Renaming GCP resources requires recreation with associated downtime risk.
> See MADR-0013 for migration details.
```

**1.4 Update Service Account Display Name**

```bash
gcloud iam service-accounts update motherduck-monitor-sa@eonlabs-ethereum-bq.iam.gserviceaccount.com \
  --display-name="ClickHouse Gap Monitor Service Account (historical: motherduck-monitor-sa)"
```

### Phase 2: Documentation Updates

**2.1 Critical Rewrites (9 files)**

| File                                                    | Issue                                          |
| ------------------------------------------------------- | ---------------------------------------------- |
| `docs/research/data-sources.md`                         | States MotherDuck is current storage           |
| `docs/deployment/realtime-collector.md`                 | 442 lines of obsolete MotherDuck instructions  |
| `docs/deployment/backfill-options.md`                   | References `/tmp/probe/motherduck/` paths      |
| `.claude/skills/data-pipeline-monitoring/SKILL.md`      | MotherDuck verification scripts                |
| `.claude/skills/vm-infrastructure-ops/SKILL.md`         | MotherDuck in operational history              |
| `.claude/skills/historical-backfill-execution/SKILL.md` | 17 MotherDuck occurrences                      |
| `.claude/skills/CATALOG.md`                             | Broken motherduck-pipeline-operations refs     |
| `deployment/vm/deploy.sh`                               | motherduck-token in secrets loop               |
| `deployment/vm/eth-collector.service`                   | Description says "Dual-Write: MotherDuck + CH" |

**2.2 Find-Replace Updates (15 files)**

Simple terminology swaps (MotherDuck to ClickHouse):

- `scripts/clickhouse/create_schema.py` (comments)
- `scripts/verify-documentation-accuracy.sh`
- `docs/deployment/CLAUDE.md`
- `.claude/skills/bigquery-ethereum-data-acquisition/SKILL.md`
- `.claude/skills/README.md`
- Various skill reference files and troubleshooting docs

**2.3 Fix Broken Link**

`docs/architecture/README.md` line 198:

- Current: `../decisions/0013-motherduck-clickhouse-migration.md`
- Correct: `../decisions/2025-11-25-motherduck-clickhouse-migration.md`

### Phase 3: GCP Resource Renaming (NOT RECOMMENDED)

**Why Skip This Phase:**

- Cloud Functions, Scheduler Jobs, Service Accounts cannot be renamed in-place
- Requires recreation with downtime risk
- Current names are internal identifiers with no user-facing impact
- Code already works correctly with ClickHouse

**If Required Later:**

1. Deploy new Cloud Function `clickhouse-gap-detector`
2. Update Scheduler to new URL
3. Verify execution
4. Delete old resources

## Files to Preserve (No Changes)

These files correctly reference MotherDuck as historical context:

- All ADR files (`docs/architecture/decisions/2025-11-*`)
- `CHANGELOG.md` (historical entries)
- `specifications/archive/motherduck-integration.yaml`
- `docs/architecture/_archive/` files (already have deprecation headers)
- Development plan files (`docs/development/plan/*/`)

## Implementation Order

```
1. Phase 1.1: Delete motherduck-monitor/ directory
2. Phase 1.2: Delete motherduck-token secret
3. Phase 1.3: Fix README historical note
4. Phase 1.4: Update service account display name
5. Phase 2.3: Fix broken link
6. Phase 2.2: Find-replace updates (15 files)
7. Phase 2.1: Critical rewrites (9 files)
8. Deploy gap monitor to Cloud Functions
9. Commit all changes
```

## Estimated Effort

| Phase         | Effort    | Risk |
| ------------- | --------- | ---- |
| Phase 1       | 15 min    | None |
| Phase 2.2-2.3 | 30 min    | None |
| Phase 2.1     | 2-3 hours | None |
| Phase 3       | Skip      | N/A  |

## User Decision

**Documentation Strategy**: Full rewrites (not deprecation notices) for all 9 files requiring substantial changes.

## Critical Files for Modification

1. `/deployment/gcp-functions/motherduck-monitor/` - DELETE
2. `/deployment/gcp-functions/gap-monitor/README.md` - Update historical note
3. `/docs/research/data-sources.md` - Rewrite storage section
4. `/docs/deployment/realtime-collector.md` - Full rewrite
5. `/.claude/skills/CATALOG.md` - Remove broken skill references
6. `/.claude/skills/historical-backfill-execution/SKILL.md` - Update 17 references
7. `/deployment/vm/deploy.sh` - Remove motherduck-token
8. `/deployment/vm/eth-collector.service` - Update description

## Rollback Plan

All changes are git-tracked:

```bash
git revert <sha>  # Code/doc changes (2 min)
```

GCP secret can be recreated from 1Password backup if needed.

## Comprehensive Audit (2025-11-29)

A 9-agent audit was performed to validate all changes:

### Audit Findings

| Agent              | Scope                         | Result                                         |
| ------------------ | ----------------------------- | ---------------------------------------------- |
| Naming Consistency | 66 files with MotherDuck refs | 9 CRITICAL (fixed), 46 HISTORICAL (preserved)  |
| Code Logic         | 14 potential issues           | Verified: gap_tracking table correct, SQL safe |
| Doc-Code Mismatch  | 5 inconsistencies             | Fixed: deploy.sh, README.md, CLAUDE.md         |
| Skills & Scripts   | 35 broken refs                | Fixed: 8 files updated to use ClickHouse       |
| Config & Secrets   | 6 active secrets              | Clean: all secrets correctly configured        |
| Deployment Scripts | 3 dependency issues           | Fixed: duckdb → clickhouse-connect             |
| Gap Tracking Table | Schema validation             | Verified: ethereum_mainnet.gap_tracking exists |
| Dependencies       | 3 files with wrong deps       | Fixed: Dockerfile, requirements.txt, deploy.sh |
| Documentation      | 3 README inconsistencies      | Fixed: gap-monitor, vm, CLAUDE.md              |

### New Scripts Created

- `scripts/clickhouse/verify_blocks.py` - Block verification with gap detection

### Files Modified

Phase 1 (audit fixes):

- `CLAUDE.md` - Fixed ADR path
- `deployment/cloud-run/Dockerfile.data-quality` - duckdb → clickhouse-connect
- `deployment/cloud-run/requirements.txt` - Removed duckdb/pyarrow
- `deployment/gcp-functions/gap-monitor/README.md` - Added --set-secrets flag
- `deployment/vm/README.md` - Updated dependency list
- `deployment/vm/deploy.sh` - Updated dependencies

Phase 2 (skill refs):

- `.claude/skills/README.md` - Updated examples and database ops
- `.claude/skills/bigquery-ethereum-data-acquisition/SKILL.md` - ClickHouse workflow
- `.claude/skills/data-pipeline-monitoring/SKILL.md` - Cross-reference section
- `.claude/skills/historical-backfill-execution/references/troubleshooting.md` - Gap detection
- `.claude/skills/historical-backfill-execution/scripts/chunked_executor.sh` - Verification
- `.claude/skills/vm-infrastructure-ops/references/vm-failure-modes.md` - Data flow
- `.claude/skills/vm-infrastructure-ops/scripts/restart_collector.sh` - Next steps
- `specifications/cloud-local-alignment-phase.yaml` - Examples section
