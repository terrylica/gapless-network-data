# MADR-0007: Skills Extraction Criteria and Structure

## Status

Proposed

## Context

Root CLAUDE.md contains highly prescriptive operational workflows embedded as documentation. These workflows are candidates for extraction as atomic skills following Skill Architecture pattern.

### Current Workflow Documentation

**VM Infrastructure Operations** (~40 lines in CLAUDE.md):
- Check service status: `systemctl status eth-collector`
- View logs: `journalctl -u eth-collector -f`
- Restart service: `systemctl restart eth-collector`
- VM reset: `gcloud compute instances reset`
- Scattered across "Service Management" and "MotherDuck Integration" sections

**Historical Backfill Execution** (~35 lines in CLAUDE.md + deployment/backfill/):
- Canonical pattern: 1-year chunks (established 2025-11-10)
- Execution: `./chunked_backfill.sh 2015 2025`
- Memory safe: <4GB (prevents OOM on Cloud Run)
- Idempotent: INSERT OR REPLACE allows re-runs

**Monitoring Alert Response** (scattered across CLAUDE.md):
- Healthchecks.io alert response
- Pushover notification handling
- Reference to MADR-0001 through MADR-0004
- No consolidated workflow

**Gap Detection** (already a skill):
- motherduck-pipeline-operations skill exists
- detect_gaps.py script operational
- May need documentation enhancement

### User Requirements

From clarification (2025-11-13):
- "Extract to new skills (following Skill Architecture)"
- Prioritize: VM troubleshooting + Historical backfill
- Defer: Monitoring alert response, Gap detection (already exists)

### Skill Architecture Pattern

From ~/.claude/CLAUDE.md skill-architecture skill:
```
.claude/skills/skill-name/
├── SKILL.md           # Main entry point (when-to-use, workflows)
├── scripts/           # Executable scripts
├── references/        # Supporting documentation
└── [NO CLAUDE.md]     # Enforced: zero child CLAUDE.md in skills
```

## Decision

Extract **2 highly prescriptive workflows as atomic skills**: VM infrastructure operations and historical backfill execution.

### Extraction Criteria

A workflow qualifies for skills extraction if it meets ≥3 of these:

1. **Highly prescriptive**: Step-by-step commands, not just concepts
2. **Frequently invoked**: Used >1x per month in operations
3. **Automation potential**: Could be wrapped in scripts/tools
4. **Self-contained**: Doesn't require deep project context
5. **Reusable pattern**: Applies to similar scenarios (e.g., all VM restarts)

### Skills to Create

#### 1. vm-infrastructure-ops

**Location**: `.claude/skills/vm-infrastructure-ops/`

**SKILL.md content** (~150 lines):
```markdown
# VM Infrastructure Operations

Troubleshoot and manage GCP e2-micro VM running eth-realtime-collector.

## When to Use

- VM service down, "eth-collector" systemd failures
- Real-time data stream stopped (MotherDuck not receiving blocks)
- VM network issues, DNS resolution failures
- Keywords: systemd, journalctl, eth-collector, gcloud compute

## Workflows

### 1. Check Service Status
\`\`\`bash
gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
  --command='sudo systemctl status eth-collector'
\`\`\`

### 2. View Logs (Live Tail)
\`\`\`bash
gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
  --command='sudo journalctl -u eth-collector -f'
\`\`\`

### 3. Restart Service
\`\`\`bash
gcloud compute ssh eth-realtime-collector --zone=us-east1-b \
  --command='sudo systemctl restart eth-collector'
\`\`\`

### 4. VM Hard Reset
\`\`\`bash
gcloud compute instances reset eth-realtime-collector --zone=us-east1-b
\`\`\`

### 5. Verify Data Flow
\`\`\`bash
uv run .claude/skills/motherduck-pipeline-operations/scripts/verify_motherduck.py
# Check latest block timestamp
\`\`\`

## Common Failure Modes

See references/vm-failure-modes.md for troubleshooting guide.
```

**scripts/**:
- `check_vm_status.sh` - Automated status check via gcloud
- `restart_collector.sh` - Safe restart with pre-checks (verify no ongoing write operations)

**references/**:
- `vm-failure-modes.md` - Common issues: network down, metadata server unreachable, gRPC errors
- `systemd-commands.md` - Quick reference for systemd operations

**Source content**: Extract from CLAUDE.md "Service Management" section

#### 2. historical-backfill-execution

**Location**: `.claude/skills/historical-backfill-execution/`

**SKILL.md content** (~120 lines):
```markdown
# Historical Backfill Execution

Execute chunked historical blockchain data backfills using canonical 1-year pattern.

## When to Use

- Loading multi-year historical data (e.g., 2015-2025 Ethereum blocks)
- Gaps detected in MotherDuck requiring backfill
- Preventing OOM failures on Cloud Run (4GB limit)
- Keywords: chunked_backfill.sh, BigQuery historical, gap filling

## Canonical Pattern (Established 2025-11-10)

- **Chunk size**: 1 year (~2.6M blocks)
- **Memory usage**: <4GB (Cloud Run safe)
- **Execution time**: ~1m40s-2m per chunk
- **Idempotency**: INSERT OR REPLACE allows safe re-runs

## Workflow

### 1. Execute Chunked Backfill
\`\`\`bash
cd deployment/backfill
./chunked_backfill.sh 2015 2025
\`\`\`

### 2. Monitor Progress
\`\`\`bash
# Logs show year-by-year progress
# 2015: Loading blocks 1 → 2,600,000
# 2016: Loading blocks 2,600,001 → 5,200,000
# ...
\`\`\`

### 3. Verify Completeness
\`\`\`bash
uv run .claude/skills/motherduck-pipeline-operations/scripts/verify_motherduck.py
# Expected: 23.8M blocks total (2015-2025)
\`\`\`

### 4. Detect Gaps (If Needed)
\`\`\`bash
uv run .claude/skills/motherduck-pipeline-operations/scripts/detect_gaps.py
# Zero-tolerance threshold detects any missing block
\`\`\`

## Why 1-Year Chunks?

See references/backfill-patterns.md for rationale (memory constraints, retry granularity).
```

**scripts/**:
- `validate_chunk_size.py` - Check memory requirements before execution
- `chunked_executor.sh` - Wrapper for deployment/backfill/chunked_backfill.sh with validation

**references/**:
- `backfill-patterns.md` - 1-year chunking rationale, comparison with alternatives (month-level, full-load)
- `troubleshooting.md` - OOM errors, retry strategies, Cloud Run logs analysis

**Source content**: Extract from CLAUDE.md "Historical Backfill" + deployment/backfill/README.md

### Skills NOT Extracted (Rationale)

**Monitoring Alert Response**:
- Deferred to future work
- Requires MADR integration (0001-0004)
- Less prescriptive (more decision-tree than workflow)

**Gap Detection**:
- Already exists as motherduck-pipeline-operations skill
- No duplication needed
- May enhance documentation within existing skill

### bigquery-ethereum-data-acquisition CLAUDE.md

**Current state**: Only skill with child CLAUDE.md file (1/6)

**Decision from clarification**: Rename CLAUDE.md → DECISION_RATIONALE.md

**Rationale**:
- Preserves architectural reasoning (BigQuery vs RPC polling choice)
- Aligns with other 5 skills (enforces zero child CLAUDE.md)
- Makes decision history explicit without breaking skills standard

## Consequences

### Positive

- **Invokability**: Workflows become invokable via Skill tool
- **Discoverability**: Skills show in claude-code skills list
- **Reusability**: Patterns documented for similar scenarios
- **Maintainability**: Operational procedures in dedicated location

### Negative

- **Additional files**: 2 new skill directories (10+ files total)
- **Learning curve**: Users must know skills exist vs embedded in CLAUDE.md
- **Context switching**: Must navigate to skill directory for full documentation

### Mitigation

- Keep brief workflow summary in root CLAUDE.md with link to skill
- Skills README.md provides high-level directory of all skills
- Skill tool auto-discovers skills (no manual invocation needed)

## Alternatives Considered

### Alternative 1: Keep workflows in CLAUDE.md

**Rejected**: Violates DRY (duplicates deployment/ guides), keeps root CLAUDE.md bloated, misses automation opportunity.

### Alternative 2: Link to docs/workflows/ files (no skills)

**Rejected**: Doesn't leverage Skill tool invocation, treats workflows as static documentation vs operational tooling.

### Alternative 3: Merge into existing motherduck-pipeline-operations skill

**Rejected**: VM operations and backfill are distinct concerns. Over-consolidation reduces discoverability.

## Implementation

### File Structure

```
.claude/skills/vm-infrastructure-ops/
├── SKILL.md (~150 lines)
├── scripts/
│   ├── check_vm_status.sh
│   └── restart_collector.sh
└── references/
    ├── vm-failure-modes.md
    └── systemd-commands.md

.claude/skills/historical-backfill-execution/
├── SKILL.md (~120 lines)
├── scripts/
│   ├── validate_chunk_size.py
│   └── chunked_executor.sh
└── references/
    ├── backfill-patterns.md
    └── troubleshooting.md
```

### Validation

```bash
# Verify skills follow architecture
for skill in vm-infrastructure-ops historical-backfill-execution; do
  [ -f ".claude/skills/$skill/SKILL.md" ] || echo "Missing SKILL.md in $skill"
  [ -d ".claude/skills/$skill/scripts" ] || echo "Missing scripts/ in $skill"
  [ -d ".claude/skills/$skill/references" ] || echo "Missing references/ in $skill"
  [ ! -f ".claude/skills/$skill/CLAUDE.md" ] || echo "FORBIDDEN: CLAUDE.md in $skill"
done
```

### Root CLAUDE.md Update

After skills extraction, replace embedded workflows with:

```markdown
## Operational Skills

Workflow automation via Skill tool:

- **VM Infrastructure Ops** (`.claude/skills/vm-infrastructure-ops/`) - Troubleshoot eth-realtime-collector service, VM restarts
- **Historical Backfill** (`.claude/skills/historical-backfill-execution/`) - Execute 1-year chunked backfills, gap filling

See [Skills README](./.claude/skills/README.md) for complete skills directory.
```

## Validation

### Skills Architecture Compliance

```python
# /tmp/doc-normalization-validation/verify_skills_structure.sh

SKILLS=("vm-infrastructure-ops" "historical-backfill-execution")

for skill in "${SKILLS[@]}"; do
    SKILL_DIR=".claude/skills/$skill"

    # Check required files
    test -f "$SKILL_DIR/SKILL.md" || echo "❌ Missing: $SKILL_DIR/SKILL.md"
    test -d "$SKILL_DIR/scripts" || echo "❌ Missing: $SKILL_DIR/scripts/"
    test -d "$SKILL_DIR/references" || echo "❌ Missing: $SKILL_DIR/references/"

    # Check forbidden files
    test ! -f "$SKILL_DIR/CLAUDE.md" || echo "❌ FORBIDDEN: $SKILL_DIR/CLAUDE.md"
done

echo "✅ Skills structure validated"
```

## SLO Impact

### Before

- **Observability**: Workflows embedded in 1,256-line CLAUDE.md
- **Maintainability**: Updates require editing monolithic file

### After

- **Observability**: Workflows invokable via Skill tool, dedicated SKILL.md
- **Maintainability**: Workflow updates isolated to skill directory

## References

- Research: `/tmp/doc-normalization-research/DETAILED_INVENTORY.md` (workflow analysis)
- Specification: `specifications/doc-normalization-phase.yaml` (tasks N2-1 through N2-3)
- Skill Architecture: `~/.claude/CLAUDE.md` skill-architecture skill
- User clarification: "Extract to new skills (following Skill Architecture)"

## Decision Date

2025-11-13

## Decision Makers

- Documentation Infrastructure Team
- User clarification (VM ops + backfill prioritized)

## Related ADRs

- MADR-0005: Root CLAUDE.md Scope (workflow documentation reduction)
- MADR-0006: Child CLAUDE.md Spokes (enforces zero CLAUDE.md in skills)
