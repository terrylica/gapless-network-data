# REFACTOR SSoT System

**Single Source of Truth**: `/specifications/refactor-compliance-implementation.yaml `

TodoWrite-managed workflow synchronized with OpenAPI 3.1.1 specification for achieving 100% REFACTOR.md compliance.

---

## Architecture

```
specifications/refactor-compliance-implementation.yaml (SSoT)
    ↓ defines phases, SLOs, verification commands
TodoWrite todos (execution state)
    ↓ tracks current task, phase progress
REFACTOR_CHANGELOG.md (version history)
    ↓ records completed phases, findings
```

**Principles**:

- **Abstractions Over Details**: OpenAPI spec defines phases, not implementation
- **Intent Over Implementation**: SLOs define correctness/observability/maintainability, not how to achieve them
- **Raise and Propagate**: All SLO failures raise errors immediately (no fallbacks, defaults, retries, silent handling)
- **Off-the-shelf OSS**: Use wc -l, grep, find for verification (no custom code)

---

## Current State

### Phase Status

| Phase                  | Status       | SLOs                                               | Deliverables                                    |
| ---------------------- | ------------ | -------------------------------------------------- | ----------------------------------------------- |
| **Analysis**           | ✅ Completed | PASS (correctness, observability, maintainability) | 6 documents (~18,000 words)                     |
| **Extraction Skill-1** | ⏸️ Pending   | Pending                                            | 5 files (4 new references, 1 modified SKILL.md) |
| **Extraction Skill-2** | ⏸️ Pending   | Pending                                            | 4 files (3 new references, 1 modified SKILL.md) |
| **Extraction Skill-3** | ⏸️ Pending   | Pending                                            | 4 files (3 new references, 1 modified SKILL.md) |
| **Verification**       | ⏸️ Pending   | Pending                                            | 1 verification report                           |

### TodoWrite Sync

**Current todos** (8 tasks):

1. Extract blockchain-rpc-provider-research to references/ (4 files, 287→185 lines)
2. Verify skill-1 SLOs: SKILL.md ≤200 lines, references linked, navigation map complete
3. Extract blockchain-data-collection-validation to references/ (3 files, 513→195 lines)
4. Verify skill-2 SLOs: SKILL.md ≤200 lines, no duckdb duplication, navigation complete
5. Extract bigquery-ethereum-data-acquisition to references/ (3 files, 225→190 lines)
6. Verify skill-3 SLOs: SKILL.md ≤200 lines, version history removed, navigation complete
7. Run comprehensive verification: 12 acceptance criteria, portfolio ≤600 lines
8. Generate verification report and commit with semantic-release

**Dependencies**:

- Tasks 1-2: No dependencies (Phase 1)
- Tasks 3-6: Depend on task 2 passing (Phase 2)
- Task 7: Depends on tasks 2, 4, 6 passing (Phase 3)
- Task 8: Depends on task 7 passing (semantic-release)

---

## SLOs (Service Level Objectives)

Defined per phase in SSoT specification. **Excludes** speed/performance/security per requirement.

### Included SLOs

1. **Correctness**:
   - Data integrity: All content preserved during extraction
   - Schema compliance: SKILL.md ≤200 lines (strict)
   - Validation success: All acceptance criteria pass

2. **Observability**:
   - Metrics logged: Line counts verified via `wc -l`
   - Verification commands available: Automated checks in SSoT spec
   - Results documented: SLO status in phase responses

3. **Maintainability**:
   - Clear structure: Three-tier architecture (metadata → entry → references)
   - Navigation links: All references linked from SKILL.md
   - Verification checklists: Acceptance criteria defined per phase

### Excluded (per requirement)

- ❌ Speed/Performance
- ❌ Security

---

## Error Handling Strategy

**Strategy**: Raise and propagate (no fallbacks, defaults, retries, silent handling)

**Implementation**:

```yaml
x-error-handling:
  strategy: raise-and-propagate
  no-fallbacks: true
  no-defaults: true
  no-retries: true
  no-silent-handling: true
  validation:
    - All SLO failures raise error immediately
    - Line count >200 raises error before file write
    - Missing reference file raises error on link validation
    - Duplicate content raises error on verification
```

**Example**:

```bash
# SLO validation for skill-1
wc -l .claude/skills/blockchain-rpc-provider-research/SKILL.md | awk '$1 > 200 {exit 1}'
# If SKILL.md >200 lines, command exits with status 1 (error raised)
# No fallback, no retry, execution stops
```

---

## Semantic Release Integration

**Enabled**: Yes
**Trigger**: On phase completion
**Commit format**: Conventional Commits

### Phase Commits

| Phase              | Type   | Scope      | Message                                                       |
| ------------------ | ------ | ---------- | ------------------------------------------------------------- |
| Skill-1 extraction | `feat` | `skill-1`  | "extract blockchain-rpc-provider-research to references"      |
| Skill-2 extraction | `feat` | `skill-2`  | "extract blockchain-data-collection-validation to references" |
| Skill-3 extraction | `feat` | `skill-3`  | "extract bigquery-ethereum-data-acquisition to references"    |
| Verification       | `feat` | `refactor` | "achieve 100% REFACTOR.md compliance across 3 skills"         |

**Version progression**:

- Current: v0.1.0 (analysis phase)
- Next: v0.2.0 (after skill-1 extraction)
- Target: v1.0.0 (after verification passes)

---

## Verification Commands

**From SSoT specification** (`x-phases[].verification_commands`):

### Phase 1: Skill-1 Extraction

```bash
# AC1.1: SKILL.md ≤200 lines
wc -l .claude/skills/blockchain-rpc-provider-research/SKILL.md | \
  awk '$1 <= 200 {print "PASS"} $1 > 200 {print "FAIL"}'

# Reference files created
ls .claude/skills/blockchain-rpc-provider-research/references/*.md | wc -l
# Expected: 6 (2 existing + 4 new)
```

### Phase 2A: Skill-2 Extraction

```bash
# AC1.1: SKILL.md ≤200 lines
wc -l .claude/skills/blockchain-data-collection-validation/SKILL.md | \
  awk '$1 <= 200 {print "PASS"} $1 > 200 {print "FAIL"}'

# AC1.3: No duckdb-patterns.md duplication
! grep -q 'CHECKPOINT' .claude/skills/blockchain-data-collection-validation/SKILL.md || \
  echo 'WARN: Possible duckdb-patterns.md duplication'
```

### Phase 2B: Skill-3 Extraction

```bash
# AC1.1: SKILL.md ≤200 lines
wc -l .claude/skills/bigquery-ethereum-data-acquisition/SKILL.md | \
  awk '$1 <= 200 {print "PASS"} $1 > 200 {print "FAIL"}'

# Version history removed
! grep -q 'Version History' .claude/skills/bigquery-ethereum-data-acquisition/SKILL.md && \
  echo 'PASS: Version history removed' || \
  echo 'FAIL: Version history still present'
```

### Phase 3: Comprehensive Verification

```bash
# AC1.1: All SKILL.md files ≤200 lines, total ≤600
wc -l .claude/skills/*/SKILL.md | tail -1 | \
  awk '$1 <= 600 {print "PASS: Total portfolio ≤600"} $1 > 600 {print "FAIL: Total portfolio >600"}'

# AC1.2: Reference files exist (≥20)
find .claude/skills/*/references/ -name "*.md" | wc -l | \
  awk '$1 >= 20 {print "PASS: ≥20 reference files"} $1 < 20 {print "FAIL: <20 reference files"}'

# AC2.2: Scripts documented
ls .claude/skills/*/scripts/README.md 2>/dev/null | wc -l | \
  awk '$1 == 3 {print "PASS: 3 scripts/README.md"} $1 != 3 {print "FAIL: Missing scripts/README.md"}'
```

---

## Todo Rectification Rules

**Sync frequency**: On every phase transition (completion or failure)

**Rectification actions**:

1. **Prune**: Remove completed todos after phase SLOs pass

   ```
   Phase 1 SLOs pass → Remove tasks 1-2 from todo list → Mark phase complete in SSoT
   ```

2. **Grow**: Add new todos when phase fails and needs retry

   ```
   Phase 1 SLO fails → Add "Fix skill-1 <SLO-failure-reason>" todo → Mark phase failed in SSoT
   ```

3. **Rectify**: Update todo status when dependencies change
   ```
   Phase 1 completes → Update tasks 3-6 status from "blocked" to "pending"
   ```

**Version tracking**:

- On phase completion: Update `x-phases[].status` to "completed" in SSoT spec
- On phase completion: Add entry to `REFACTOR_CHANGELOG.md`
- On phase completion: Create conventional commit for semantic-release
- On phase failure: Update `x-phases[].status` to "failed", add `x-implementation-findings[]` entry

---

## Usage

### Check current status

```bash
# View SSoT plan
cat specifications/refactor-compliance-implementation.yaml | \
  grep -A 20 'x-phases:'

# View current todos
# (shown in Claude Code UI)

# View changelog
cat REFACTOR_CHANGELOG.md
```

### Execute next phase

```bash
# Phase 1 is current (task 1 in todo list)
# Execute extraction per PATCH_1_blockchain_rpc_provider_research.md
# On completion, verify SLOs
# If pass: commit with semantic-release, update SSoT, prune todos
# If fail: add finding to SSoT, grow todos with fix task
```

### Verify SLOs manually

```bash
# Run verification commands from SSoT spec
# Example for Phase 1:
wc -l .claude/skills/blockchain-rpc-provider-research/SKILL.md
ls .claude/skills/blockchain-rpc-provider-research/references/*.md
```

---

## Files

| File                                                       | Purpose           | Type                    |
| ---------------------------------------------------------- | ----------------- | ----------------------- |
| `/specifications/refactor-compliance-implementation.yaml ` | SSoT plan         | OpenAPI 3.1.1 spec      |
| `REFACTOR_CHANGELOG.md `                                   | Version history   | Keep a Changelog format |
| `REFACTOR_EXECUTIVE_SUMMARY.md `                           | Overview          | Markdown                |
| `REFACTOR_CONFORMANCE_REPORT.md `                          | Analysis results  | Markdown                |
| `PATCH_1_blockchain_rpc_provider_research.md `             | Phase 1 guide     | Markdown                |
| `PATCH_2_blockchain_data_collection_validation.md `        | Phase 2A guide    | Markdown                |
| `PATCH_3_bigquery_ethereum_data_acquisition.md `           | Phase 2B guide    | Markdown                |
| `REFACTOR_COMPLIANCE_PLAN.md `                             | Execution roadmap | Markdown                |

---

## Next Actions

1. **Execute Phase 1** (tasks 1-2 in todo list):
   - Extract skill-1 per `PATCH_1_blockchain_rpc_provider_research.md `
   - Verify SLOs using commands from SSoT spec
   - If pass: commit, update SSoT, prune todos 1-2, proceed to Phase 2
   - If fail: add finding to SSoT, grow todos with fix task, halt

2. **Semantic release** (after each phase):
   - Create conventional commit: `feat(skill-1): extract blockchain-rpc-provider-research to references`
   - Tag: `v0.2.0` (or next version per semantic-release)
   - Update changelog: Add phase completion entry

3. **Update SSoT** (after each phase):
   - Change phase status: `pending` → `completed` or `failed`
   - Update SLOs: `pending` → `PASS` or `FAIL`
   - Add findings if failed: `x-implementation-findings[]`

---

## SSoT Principles Applied

| Principle                      | Implementation                                                                     |
| ------------------------------ | ---------------------------------------------------------------------------------- |
| **Abstractions Over Details**  | SSoT defines phases (what), not extraction steps (how)                             |
| **Intent Over Implementation** | SLOs define success criteria (correctness), not specific line counts               |
| **Raise and Propagate**        | All verification commands exit 1 on failure, no error handling                     |
| **Off-the-shelf OSS**          | Use wc, grep, find, awk (no custom code)                                           |
| **Version tracking**           | OpenAPI spec version, changelog, semantic-release commits                          |
| **No promotional language**    | Neutral terminology (extract, verify, complete), no "enhanced"/"production-graded" |

---

## Maintainers

See `/Users/terryli/.claude/CLAUDE.md ` for project conventions and planning standards.
