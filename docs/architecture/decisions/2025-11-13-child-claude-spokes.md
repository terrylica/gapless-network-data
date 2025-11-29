# MADR-0006: Child CLAUDE.md Spoke Architecture

## Status

Proposed

## Context

Research revealed docs/ subdirectories lack local navigation hubs. Users must return to root CLAUDE.md to discover related documentation within the same category (architecture, deployment, decisions).

### Current State

**Existing hub files** (working well):

- docs/INDEX.md - Master hub for all documentation
- docs/research/INDEX.md - Research materials hub
- docs/archive/README.md - Archived documentation hub

**Missing local navigation**:

- docs/architecture/ (5 files) - No index, users browse directory
- docs/deployment/ (4 files) - No index, scattered references
- docs/decisions/ (8 files after MADR-0005 through MADR-0008) - No index for ADRs
- docs/motherduck/ (3 files) - No index, unclear relationship to architecture

### User Requirements

From clarification (2025-11-13):

- "CLAUDE.md in each docs/\* subdirectory"
- Child CLAUDE.md acts as "hub link farm"
- "No need to have INDEX.md" (INDEX.md → CLAUDE.md naming)

### Industry Standards

**ADR (Architectural Decision Records)** best practice:

- MADR format used (Markdown Any Decision Records)
- Standard practice: INDEX.md or README.md listing all ADRs
- Chronological order with 0000-title.md naming

## Decision

Create **child CLAUDE.md files as local navigation spokes** in docs/ subdirectories. Each acts as a link farm for files in that directory.

### Structure Pattern

```markdown
# [Category] Documentation

Local navigation hub for [category] documents.

## Files

- [File Name](./filename.md) - Brief description
- [File Name 2](./filename2.md) - Brief description
  ...

## Related

- Parent hub: [Root CLAUDE.md](../../CLAUDE.md)
- Sibling categories: [Other Category](../other-category/CLAUDE.md)
```

### Locations

1. **docs/architecture/CLAUDE.md** (~80 lines)
   - Lists: OVERVIEW.md, DATA_FORMAT.md, motherduck-dual-pipeline.md, bigquery-integration.md, duckdb-strategy.md
   - Purpose: Architecture decisions and system design

2. **docs/deployment/CLAUDE.md** (~60 lines)
   - Lists: realtime-collector.md, secret-manager-migration.md, oracle/
   - Links to: ../deployment/cloud-run/, ../deployment/vm/ (outside docs/)
   - Purpose: Deployment guides and operational setup

3. **docs/decisions/CLAUDE.md** (~50 lines)
   - Lists: MADR-0001 through MADR-0008 (chronological)
   - Purpose: Architectural decision log (ADR index)

4. **docs/motherduck/CLAUDE.md** (~40 lines)
   - Lists: dual-pipeline.md, bigquery-integration.md, integration.md
   - Purpose: MotherDuck-specific documentation
   - Alternative: Merge into docs/architecture/ (only 3 files)

### Naming Rationale

**Why CLAUDE.md instead of INDEX.md**:

- Consistency with root CLAUDE.md pattern
- "Link farm" metaphor suggests CLAUDE-branded navigation
- Matches user's existing mental model
- Claude Code tool reads CLAUDE.md files preferentially

**Why not README.md**:

- README.md is GitHub's default display
- CLAUDE.md signals "for Claude Code AI agent"
- Separation of concerns: README for GitHub users, CLAUDE for AI

## Consequences

### Positive

- **Local discoverability**: Navigate within category without returning to root
- **2-hop navigation**: Root → Category CLAUDE.md → Specific doc
- **Maintenance locality**: Adding new file requires only 1 local edit
- **Consistent pattern**: All docs/ subdirectories follow same spoke structure

### Negative

- **Proliferation**: 4 new CLAUDE.md files (root + 4 spokes = 5 total)
- **Duplication risk**: Links could drift out of sync with files
- **Naming confusion**: Multiple CLAUDE.md files with different purposes

### Mitigation

- Keep child CLAUDE.md files under 100 lines (pure link farms)
- Use relative links (./filename.md) to prevent breakage
- Validate link coverage in CI/CD (all \*.md files linked)

## Alternatives Considered

### Alternative 1: No child CLAUDE.md (pure hub-and-spoke from root)

**Rejected**: Root CLAUDE.md becomes too long linking all 30+ docs/\* files. Violates goal of 500-600 lines. Forces users to scroll through unrelated categories.

### Alternative 2: INDEX.md instead of CLAUDE.md

**Rejected**: User explicitly requested CLAUDE.md naming. INDEX.md conflicts with existing docs/INDEX.md (master hub). Less consistent with root file naming.

### Alternative 3: README.md in each subdirectory

**Rejected**: README.md is for GitHub web display. CLAUDE.md signals "AI agent navigation". Separation of concerns improves clarity.

### Alternative 4: Merge all MotherDuck docs into docs/architecture/

**Considered**: docs/motherduck/ only has 3 files. Could simplify to single architecture category. User can decide during implementation if consolidation makes sense.

## Implementation

### Template for Child CLAUDE.md

```markdown
# [Category] Documentation

Local navigation hub for [category]-related documents.

## Overview

Brief 1-2 sentence description of what this category covers.

## Documents

### Core Files

- [File Name](./filename.md) - One-line description
- [File Name 2](./filename2.md) - One-line description

### Related Locations

- Root hub: [CLAUDE.md](../../CLAUDE.md)
- Related category: [Other Category](../other-category/CLAUDE.md)

## External References

Links to non-docs/ locations (deployment/, .claude/skills/) if relevant.
```

### Link Coverage Validation

```bash
# For each child CLAUDE.md, verify all sibling *.md files are linked
cd docs/architecture
for f in *.md; do
  [[ "$f" == "CLAUDE.md" ]] && continue
  grep -q "$f" CLAUDE.md || echo "Missing link: $f"
done
```

### Line Count Enforcement

```bash
# Verify child CLAUDE.md files stay minimal (<100 lines)
find docs/ -name "CLAUDE.md" | xargs wc -l | awk '$1 > 100 {print "Too long: " $2 " (" $1 " lines)"}'
```

## Validation

### Criteria

1. **Link coverage**: 100% of \*.md files linked from local CLAUDE.md
2. **Brevity**: Each child CLAUDE.md <100 lines
3. **Consistency**: All follow same template structure
4. **Relative paths**: No absolute links
5. **Two-way navigation**: Links to parent (root) and siblings

### Test Script

```python
# File: /tmp/doc-normalization-validation/verify_hub_coverage.py

import os
from pathlib import Path

DOCS_ROOT = Path("docs/")
EXPECTED_SPOKES = ["architecture", "deployment", "decisions", "motherduck"]

for spoke in EXPECTED_SPOKES:
    spoke_path = DOCS_ROOT / spoke
    claude_file = spoke_path / "CLAUDE.md"

    # Check CLAUDE.md exists
    assert claude_file.exists(), f"Missing: {claude_file}"

    # Check all *.md files are linked
    md_files = [f for f in spoke_path.glob("*.md") if f.name != "CLAUDE.md"]
    claude_content = claude_file.read_text()

    for md_file in md_files:
        assert md_file.name in claude_content, f"Not linked in {claude_file}: {md_file.name}"

    # Check line count
    line_count = len(claude_content.splitlines())
    assert line_count < 100, f"Too long: {claude_file} ({line_count} lines)"

print("✅ All child CLAUDE.md spokes validated")
```

## SLO Impact

### Before

- **Observability**: No local navigation, users must return to root for discovery
- **Maintainability**: New files in docs/ subdirectories not easily discoverable

### After

- **Observability**: 100% docs/\* files discoverable via local navigation
- **Maintainability**: Adding file requires only local CLAUDE.md edit

## References

- Research: `/tmp/doc-normalization-research/DETAILED_INVENTORY.md` (hub files analysis)
- Specification: `specifications/doc-normalization-phase.yaml` (tasks N3-1 through N3-4)
- User clarification: "CLAUDE.md in each docs/\* subdirectory"

## Decision Date

2025-11-13

## Decision Makers

- Documentation Infrastructure Team
- User clarification (child CLAUDE.md as hub link farm)

## Related ADRs

- MADR-0005: Root CLAUDE.md Scope (parent hub structure)
- MADR-0008: Link Format Standardization (relative paths)
