# Plan: Post-Migration Documentation Rectification

**Status**: In Progress
**Created**: 2025-11-25
**Related ADR**: [Documentation Rectification](/docs/architecture/decisions/2025-11-25-documentation-rectification.md)

## (a) Context

**Why This Plan Exists**:

MADR-0013 (MotherDuck to ClickHouse Migration) completed operationally on 2025-11-25, but documentation remains in a hybrid state. This creates confusion for users and breaks skill functionality.

**Scope Analysis**:

| Category         | Files Affected                     | MotherDuck Refs | Priority |
| ---------------- | ---------------------------------- | --------------- | -------- |
| Skills           | motherduck-pipeline-operations/\*  | 123             | CRITICAL |
| Root README      | /README.md                         | 15              | CRITICAL |
| Architecture     | OVERVIEW.md                        | 25+             | CRITICAL |
| Deprecated Arch  | motherduck-dual-pipeline.md        | ALL             | HIGH     |
| Deprecated Arch  | bigquery-motherduck-integration.md | ALL             | HIGH     |
| Deployment       | deploy.sh, realtime-collector.md   | 47              | HIGH     |
| Decision Records | MADR-0003, 0004                    | N/A             | MEDIUM   |
| Specifications   | motherduck-\*.yaml                 | ALL             | LOW      |

**Constraints**:

- Documentation-only changes (no infrastructure modifications)
- Skills must function with ClickHouse
- Archived files must include deprecation notices with MADR-0013 reference

## (b) Plan

**Objective**: Rectify all documentation to accurately reflect ClickHouse as the production database.

**Strategy**: Archive deprecated content, update active documentation, rename skills.

### Phase 1: CRITICAL Fixes

**1.1 Archive motherduck-pipeline-operations skill**

- Move `.claude/skills/motherduck-pipeline-operations/` to `.claude/skills/archive/motherduck-pipeline-operations/`
- Add deprecation YAML frontmatter to SKILL.md
- Update `.claude/skills/CATALOG.md` to remove deprecated skill

**1.2 Update /README.md**

Replace MotherDuck references with ClickHouse:

- Line 9: Architecture description
- Line 31-36: Database section
- Lines 48-70: Code examples
- Lines 119-140: Feature engineering examples
- Lines 147, 239, 257: Storage/pricing references
- Lines 276, 302: Documentation links

**1.3 Update docs/architecture/OVERVIEW.md**

Replace MotherDuck references:

- Line 25: Storage description
- Line 33: Cloud Function reference
- Lines 44-56: Data flow diagrams
- Line 63: Storage location
- Lines 92-100: Key Decisions section
- Lines 105-110: Batch write rationale
- Line 150: Current limitations
- Lines 155-156: Related documentation links

### Phase 2: Architecture Documentation

**2.1 Archive deprecated architecture files**

Move to `docs/architecture/_archive/`:

- `motherduck-dual-pipeline.md`
- `bigquery-motherduck-integration.md`

Add deprecation frontmatter:

```yaml
---
status: deprecated
deprecated_date: 2025-11-25
reason: "Migrated to ClickHouse Cloud (MADR-0013)"
replacement: "See docs/decisions/0013-motherduck-clickhouse-migration.md"
---
```

**2.2 Update docs/architecture/CLAUDE.md**

Replace MotherDuck links with ClickHouse references.

**2.3 Update docs/architecture/DATA_FORMAT.md**

Update storage section references.

### Phase 3: Deployment & Scripts

**3.1 Fix deployment/vm/deploy.sh**

Remove MotherDuck secret references from comments.

**3.2 Keep folder naming (decision)**

`deployment/gcp-functions/motherduck-monitor/` - Keep with README note explaining historical naming (avoids GCP redeploy).

**3.3 Update docs/deployment/realtime-collector.md**

Replace MotherDuck references with ClickHouse.

### Phase 4: Decision Records & Skills

**4.1 Add supersession notes to MADRs**

Update MADR-0003, 0004 with supersession note referencing MADR-0013.

**4.2 Update docs/decisions/CLAUDE.md**

Add missing MADR-0009 through MADR-0012 to navigation hub.

**4.3 Update skill cross-references**

Update references in:

- `.claude/skills/historical-backfill-execution/SKILL.md`
- `.claude/skills/vm-infrastructure-ops/SKILL.md`
- `.claude/skills/data-pipeline-monitoring/SKILL.md`

### Phase 5: Specifications & Cleanup

**5.1 Archive specifications**

Move to `specifications/archive/`:

- `motherduck-integration.yaml`
- `motherduck-data-quality-monitoring.yaml`

**5.2 Add deprecation notices**

Add YAML frontmatter to:

- `docs/motherduck/INDEX.md`
- `docs/motherduck/credentials.md`

## (c) Task List

### Phase 1: CRITICAL Fixes

- [ ] 1.1 Archive motherduck-pipeline-operations skill
- [ ] 1.2 Update /README.md (15 corrections)
- [ ] 1.3 Update docs/architecture/OVERVIEW.md (25+ corrections)

### Phase 2: Architecture Documentation

- [ ] 2.1 Archive deprecated architecture files
- [ ] 2.2 Update docs/architecture/CLAUDE.md
- [ ] 2.3 Update docs/architecture/DATA_FORMAT.md

### Phase 3: Deployment & Scripts

- [ ] 3.1 Fix deployment/vm/deploy.sh
- [ ] 3.2 Add README note to motherduck-monitor folder
- [ ] 3.3 Update docs/deployment/realtime-collector.md

### Phase 4: Decision Records & Skills

- [ ] 4.1 Add supersession notes to MADR-0003, 0004
- [ ] 4.2 Update docs/decisions/CLAUDE.md navigation hub
- [ ] 4.3 Update skill cross-references

### Phase 5: Specifications & Cleanup

- [ ] 5.1 Archive motherduck specifications
- [ ] 5.2 Add deprecation notices to docs/motherduck/\*

## Success Criteria

- [ ] No active documentation references MotherDuck as production database
- [ ] All deprecated files archived with MADR-0013 reference
- [ ] Skills function correctly with ClickHouse
- [ ] Navigation hubs updated with new structure
- [ ] Link validation passes (lychee)
