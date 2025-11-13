# MADR-0005: Root CLAUDE.md Scope and Essential Context Strategy

## Status

Proposed

## Context

Root CLAUDE.md has grown to 1,256 lines with 850 lines of duplication (68%). Research identified significant content overlap with docs/architecture/, deployment guides, and skills descriptions.

### Current Problems

**Duplication**:
- MotherDuck Integration: 340 lines in CLAUDE.md duplicate docs/architecture/motherduck-dual-pipeline.md
- DuckDB Architecture: 225 lines duplicate concepts spread across multiple architecture docs
- Project Skills: 82 lines duplicate skill descriptions that should be in skill directories
- Data Sources: 70 lines repeated across 3 different sections

**Maintenance burden**:
- MotherDuck updates require editing 2-3 files
- Architecture changes need synchronization across documents
- Skills updates miss CLAUDE.md references

**Navigation challenges**:
- 1,256 lines too long for quick reference
- Essential information buried in detailed content
- Users scroll through duplicates to find commands

### User Requirements

From clarification questions (2025-11-13):
- **Target size**: 500-600 lines (essential context + navigation index)
- **Essential content**: Project status, navigation index, critical commands
- **Remove**: Detailed architecture, workflow guides, duplicate descriptions

## Decision

Reduce root CLAUDE.md to **essential context + navigation hub** (500-600 lines) while preserving quick-reference operational value.

### What Stays in Root

1. **Project Status Snapshot** (~30 lines)
   - Current version (v3.1.1)
   - Operational state (23.8M blocks, production)
   - Key metrics (SLOs, data loaded)

2. **Quick Navigation Index** (~150 lines)
   - 2-3 line summaries per topic
   - Relative links to detailed docs
   - Hub-and-spoke structure

3. **Critical Copy-Paste Commands** (~100 lines)
   - Deployment: `gcloud run jobs execute ...`
   - Monitoring: `systemctl status eth-collector`
   - Verification: `uv run verify_motherduck.py`
   - Frequently-used operations only

4. **Minimal Context** (~300 lines)
   - Project overview (what/why/how)
   - Quick architecture overview (1 paragraph)
   - Key design principles (exception-only failures, DRY)
   - Related projects references

### What Moves to docs/

**MotherDuck Integration** (340 → 20 lines):
- Detailed architecture → docs/architecture/motherduck-dual-pipeline.md
- Service management → .claude/skills/vm-infrastructure-ops/
- Cost analysis → docs/architecture/motherduck-integration.md
- Keep: 2-3 line summary + link

**DuckDB Architecture** (225 → 15 lines):
- Create: docs/architecture/duckdb-strategy.md
- Move: 23 features table, benchmarks, alternatives analysis
- Keep: "DuckDB PRIMARY for analytics (10-100x)" + link

**Project Skills** (82 → 5 lines):
- Create: .claude/skills/README.md
- Move: All skill descriptions, when-to-use guidance
- Keep: Count (7 skills) + link

**Data Sources** (70 lines → consolidated):
- Create: docs/research/data-sources.md
- Move: All RPC provider research, rejection rationale
- Keep: "Primary: BigQuery + Alchemy" + link

## Consequences

### Positive

- **Readability**: 60% reduction (1,256 → 600 lines) improves scanability
- **Maintainability**: DRY principle enforced, single-location updates
- **Navigation**: Hub structure makes all docs discoverable in ≤2 hops
- **Operational efficiency**: Critical commands remain accessible for copy-paste

### Negative

- **Context switching**: Users must follow links for detailed information
- **Multi-file views**: Full understanding requires opening 2-3 files
- **Migration effort**: Existing workflows referencing specific sections need updates

### Mitigation

- Keep most-used commands in root (gcloud, systemctl, verification)
- Child CLAUDE.md spokes provide local navigation within subdirectories
- Relative links ensure portability and GitHub preview compatibility

## Alternatives Considered

### Alternative 1: Minimal index only (300-400 lines)

**Rejected**: Too aggressive. Removes operational commands, forcing users into docs/ for routine tasks. Sacrifices convenience for purity.

### Alternative 2: Moderate reduction (700-800 lines)

**Rejected**: Insufficient. Keeps significant duplication, doesn't solve DRY problem. Maintenance burden only slightly reduced.

### Alternative 3: Split into multiple root files (CLAUDE-ARCH.md, CLAUDE-OPS.md)

**Rejected**: Violates hub-and-spoke principle. Creates ambiguity about canonical file. Fragments navigation.

## Implementation

### Extraction Pattern

For each content section being moved:

1. **Create destination file** under docs/ hierarchy
2. **Move content** preserving all detail and context
3. **Replace in root** with:
   ```markdown
   ## Topic Name

   Brief summary (2-3 lines explaining what it is).

   See [detailed documentation](./docs/path/to/file.md) for:
   - Detailed architecture
   - Configuration options
   - Troubleshooting guides
   ```
4. **Verify links** using existing link checker

### Content Priority

**Must keep in root**:
- Version numbers and operational status
- Navigation links to all major docs
- Commands used >1x per week

**Must move to docs/**:
- Architecture rationale (>2 paragraphs)
- Historical decisions and alternatives
- Detailed troubleshooting guides
- Reference tables and benchmarks

## Validation

### Line Count Verification

```bash
wc -l CLAUDE.md
# Expected: 500-600 lines
```

### Duplication Check

```bash
# Check for paragraphs >3 lines appearing in multiple files
grep -A 3 "MotherDuck Integration" CLAUDE.md docs/architecture/*.md
# Expected: Only brief mention in CLAUDE.md
```

### Link Coverage

```bash
# Verify all docs/*.md files are linked from root
find docs/ -name "*.md" | while read f; do
  grep -q "$(basename $f)" CLAUDE.md || echo "Missing: $f"
done
```

## SLO Impact

### Before

- **Correctness**: 68% duplication rate (850/1,256 lines)
- **Maintainability**: MotherDuck changes require 2-3 file edits
- **Observability**: Long file hides essential information

### After

- **Correctness**: 0% duplication (DRY enforced)
- **Maintainability**: Single-location updates for all topics
- **Observability**: Essential context visible in <600 lines

## References

- Research: `/tmp/doc-normalization-research/EXECUTIVE_SUMMARY.md`
- Specification: `specifications/doc-normalization-phase.yaml` (tasks N1-1 through N1-5)
- Duplication analysis: 850 duplicate lines identified across 4 major sections

## Decision Date

2025-11-13

## Decision Makers

- Documentation Infrastructure Team
- User clarification (essential context + index, 500-600 lines)

## Related ADRs

- MADR-0006: Child CLAUDE.md Spoke Architecture (local navigation)
- MADR-0007: Skills Extraction Criteria (workflow documentation)
- MADR-0008: Link Format Standardization (relative paths)
