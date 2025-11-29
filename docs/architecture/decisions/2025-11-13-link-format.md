# MADR-0008: Link Format Standardization (Relative GFM)

## Status

Proposed

## Context

Research identified 47 absolute file paths in CLAUDE.md using user-specific home directory. These links are not portable and fail in different environments.

### Current Link Problems

**Absolute paths with $HOME** (47 occurrences):

```markdown
[Link](/docs/architecture/OVERVIEW.md)
```

Problems:

- **Not portable**: Breaks for other users, CI/CD, containers
- **Lychee incompatible**: Link checker fails on user-specific paths
- **Fragile**: Breaks if repository moves to different directory

**Current patterns observed**:

- Root CLAUDE.md → docs/: 35 absolute links
- Root CLAUDE.md → deployment/: 8 absolute links
- Root CLAUDE.md → .claude/skills/: 4 absolute links

### User Requirements

From clarification (2025-11-13):

- "Relative GFM paths from file location"
- Example: `./docs/architecture/OVERVIEW.md` or `../skills/data-pipeline-monitoring/`
- "Portable, lychee-compatible, works in GitHub and locally"

### GitHub-Flavored Markdown (GFM) Standard

GFM supports relative links:

- **Same directory**: `./filename.md` or `filename.md`
- **Subdirectory**: `./subdir/filename.md`
- **Parent directory**: `../filename.md`
- **Multiple levels**: `../../docs/filename.md`

Benefits:

- Portable across environments
- Works in GitHub web UI preview
- Works in local editors (VS Code, vim)
- Compatible with lychee link checker

## Decision

Standardize all internal documentation links to **relative GFM paths from file location**.

### Link Format Rules

#### 1. From Root CLAUDE.md

**To docs/**:

```markdown
[Architecture Overview](./docs/architecture/OVERVIEW.md)
[Data Format](./docs/architecture/DATA_FORMAT.md)
```

**To deployment/**:

```markdown
[VM Deployment](./deployment/vm/README.md)
[Cloud Run Setup](./deployment/cloud-run/README.md)
```

**To skills/**:

```markdown
[Pipeline Operations](./.claude/skills/motherduck-pipeline-operations/SKILL.md)
[Data Monitoring](./.claude/skills/data-pipeline-monitoring/SKILL.md)
```

#### 2. From Child CLAUDE.md Spokes

**docs/architecture/CLAUDE.md to siblings**:

```markdown
[Overview](./OVERVIEW.md)
[Data Format](./DATA_FORMAT.md)
[MotherDuck Pipeline](./motherduck-dual-pipeline.md)
```

**docs/architecture/CLAUDE.md to parent**:

```markdown
[Root CLAUDE.md](../../CLAUDE.md)
```

**docs/architecture/CLAUDE.md to sibling directories**:

```markdown
[Deployment Guides](../deployment/CLAUDE.md)
[ADRs](../decisions/CLAUDE.md)
```

#### 3. From Skills SKILL.md

**To scripts/ within skill**:

```markdown
[Check VM Status](./scripts/check_vm_status.sh)
[Restart Collector](./scripts/restart_collector.sh)
```

**To references/ within skill**:

```markdown
[VM Failure Modes](./references/vm-failure-modes.md)
[Troubleshooting Guide](./references/troubleshooting.md)
```

**To root or docs/**:

```markdown
[Project Overview](../../../CLAUDE.md)
[Architecture Docs](../../../docs/architecture/CLAUDE.md)
```

### Conversion Pattern

```bash
# From: /docs/architecture/OVERVIEW.md
# To:   ./docs/architecture/OVERVIEW.md

# Regex pattern:
s|/||g
```

### External Links (No Change)

Keep absolute URLs for external references:

- GitHub repositories: `https://github.com/terrylica/gapless-crypto-data`
- Documentation sites: `https://duckdb.org/docs/...`
- Issue trackers: `https://github.com/.../issues/...`

## Consequences

### Positive

- **Portability**: Links work regardless of username or directory location
- **Lychee compatible**: Existing link checker validates internal links
- **GitHub preview**: Links clickable in GitHub web UI
- **Editor support**: VS Code, vim, etc. follow relative links
- **Repository mobility**: Survives directory renames, repository moves

### Negative

- **Verbosity**: Relative paths slightly longer than bare filenames
- **Mental model**: Requires understanding ../../../ navigation
- **Fragile to moves**: If file moves, links must be updated

### Mitigation

- Use existing link checker in CI/CD to catch broken links
- Keep directory structure stable (avoid frequent reorganization)
- Document link format in contribution guide

## Alternatives Considered

### Alternative 1: Repository-root relative paths

Example: `/docs/architecture/OVERVIEW.md`

**Rejected**:

- Requires lychee configuration (`--base `)
- Not portable to CI/CD without custom config
- Doesn't work in GitHub web UI preview

### Alternative 2: Absolute paths with $HOME variable

Example: `$HOME/eon/gapless-network-data/docs/...`

**Rejected**:

- Still user-specific ($HOME differs between users)
- Doesn't expand in markdown renderers
- Lychee doesn't understand environment variables

### Alternative 3: Symbolic links to documentation

Create `docs/DOCS_ROOT` symlink → `/docs`

**Rejected**:

- Adds complexity (symlinks must be maintained)
- Doesn't work on Windows (symlink support limited)
- Over-engineering for simple relative path solution

## Implementation

### Automated Conversion Script

```bash
# File: /tmp/doc-normalization-validation/convert_absolute_to_relative.sh

REPO_ROOT=""

# Find all CLAUDE*.md files
find . -name "CLAUDE*.md" | while read -r file; do
    echo "Converting links in: $file"

    # Replace absolute paths with relative
    sed -i.bak "s|$REPO_ROOT/||g" "$file"

    # Clean up backup
    rm "${file}.bak"
done

echo "✅ Converted absolute → relative paths"
```

### Manual Verification

For each CLAUDE.md file:

1. **Find absolute links**: `grep '/Users/terryli' CLAUDE.md`
2. **Convert to relative**: Calculate path from file location
3. **Verify clickable**: Test in GitHub preview or VS Code

### Link Coverage Validation

```python
# File: /tmp/doc-normalization-validation/verify_link_format.py

import re
from pathlib import Path

REPO_ROOT = Path("")
FORBIDDEN_PATTERN = r""

def check_file(file_path: Path) -> list[str]:
    """Check for absolute paths in file."""
    content = file_path.read_text()
    absolute_links = re.findall(FORBIDDEN_PATTERN, content)
    return absolute_links

def main():
    violations = []

    # Check all CLAUDE*.md files
    for claude_file in REPO_ROOT.rglob("CLAUDE*.md"):
        absolute_links = check_file(claude_file)
        if absolute_links:
            violations.append((claude_file, len(absolute_links)))

    if violations:
        print("❌ Found absolute links:")
        for file, count in violations:
            print(f"   {file}: {count} absolute links")
        return 1
    else:
        print("✅ All links are relative")
        return 0

if __name__ == "__main__":
    exit(main())
```

### Lychee Configuration

```toml
# File: lychee.toml (already exists in repository)

# Accept relative links
include_relative = true

# Check internal links
check_relative_links = true

# Exclude external domains if needed
exclude = ["https://example.com"]
```

## Validation

### Test Cases

**Root CLAUDE.md → docs/**:

```bash
# Link: ./docs/architecture/OVERVIEW.md
test -f "docs/architecture/OVERVIEW.md" && echo "✅ Link resolves"
```

**Child spoke → sibling**:

```bash
cd docs/architecture
# Link: ./OVERVIEW.md
test -f "OVERVIEW.md" && echo "✅ Link resolves"
```

**Child spoke → parent**:

```bash
cd docs/architecture
# Link: ../../CLAUDE.md
test -f "../../CLAUDE.md" && echo "✅ Link resolves"
```

### Lychee Validation

```bash
# Run lychee on all markdown files
lychee --offline --base . **/*.md

# Expected: 0 broken internal links
```

## SLO Impact

### Before

- **Availability**: 47 absolute links break on other machines
- **Maintainability**: Links fail after repository moves

### After

- **Availability**: 100% links work across all environments
- **Maintainability**: Links survive repository restructuring

## References

- Research: `/tmp/doc-normalization-research/absolute-links-sample.txt` (47 absolute links identified)
- Specification: `specifications/doc-normalization-phase.yaml` (task N1-5)
- GFM spec: https://github.github.com/gfm/#links
- User clarification: "Relative GFM paths from file location"

## Decision Date

2025-11-13

## Decision Makers

- Documentation Infrastructure Team
- User clarification (relative GFM paths, lychee-compatible)

## Related ADRs

- MADR-0005: Root CLAUDE.md Scope (navigation links)
- MADR-0006: Child CLAUDE.md Spokes (relative sibling links)
- MADR-0007: Skills Extraction (relative links within skills)
