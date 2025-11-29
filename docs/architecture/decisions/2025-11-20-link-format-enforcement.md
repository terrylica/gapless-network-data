# MADR-0011: Link Format Enforcement

**Status**: Proposed

**Date**: 2025-11-20

**Related**: Plan 0011 (`docs/development/plan/0011-link-format-compliance/plan.md`)

**Extends**: MADR-0008 (Link Format Standardization)

## Context

MADR-0008 established the standard: All links must be relative markdown format.

**Current Reality**: 123 absolute path violations across 14 files

**Violation Pattern**:

```markdown
❌ [File](/docs/file.md)
✅ [File](../docs/file.md)
```

**Top Violators**:

- docs/INDEX.md: 50 violations
- docs/research/INDEX.md: 14 violations
- docs/archive/llamarpc-research/INDEX.md: 10 violations

**Impact**:

- **GitHub rendering**: Links display but don't navigate
- **Portability**: Documentation unusable on other machines, containers, CI/CD
- **lychee incompatibility**: Link checker cannot validate absolute paths with user-specific paths

## Decision

1. **Automated Conversion**: Replace `/` with calculated relative paths
   - Preserve anchor links: `file.md#section` → `../file.md#section`
   - Handle edge cases: root CLAUDE.md, nested subdirectories

2. **CI Enforcement**: Add `lychee` link checker to GitHub Actions
   - Fail on: Absolute paths, broken links, 404s
   - Run on: Every PR, every push to main

3. **Pre-commit Hook**: Block commits containing `/Users/` or `/tmp/` in markdown links
   - Regex check on staged files
   - Helpful error message with conversion instructions

**Conversion Algorithm**:

```python
def convert_link(markdown_file, absolute_link):
    # Extract target path and optional anchor
    target_path, anchor = parse_link(absolute_link)

    # Calculate relative path from current file to target
    current_dir = os.path.dirname(markdown_file)
    relative_path = os.path.relpath(target_path, current_dir)

    # Reconstruct link with anchor
    return f"{relative_path}{anchor}"
```

## Consequences

**Positive**:

- Portable documentation (works on any machine, GitHub, containers)
- GitHub-compatible links (proper navigation)
- CI/CD ready (lychee validates all links)
- Prevents future violations (pre-commit hook)

**Negative**:

- One-time conversion effort (123 violations)
- Requires path calculation logic

**Risks**:

- Incorrect relative path calculation breaks working links (Mitigation: Backup all files, dry-run on single file first, lychee validation before commit)

## Alternatives Considered

### Alternative 1: Manual Conversion

**Rejected**: Error-prone, 123 violations too many for manual editing

### Alternative 2: Allow Absolute Paths

**Rejected**: Violates MADR-0008, breaks portability and GitHub rendering

### Alternative 3: Symlink Workaround

**Rejected**: Doesn't solve GitHub rendering issue, adds complexity

## Validation

**Zero Absolute Paths**:

```bash
! grep -r '\[.*\](/Users/' docs/ CLAUDE.md README.md specifications/
```

**All Links Valid**:

```bash
lychee --offline docs/ CLAUDE.md README.md specifications/
```

**Pre-commit Hook Blocks Violations**:

```bash
echo "[test](/Users/test)" >> test.md && \
    git add test.md && \
    git commit -m "test" && \
    echo "FAIL" || echo "PASS"
```

## Implementation

See Plan 0011 for detailed task breakdown (10 tasks, 8 hours estimated).

**Dependency**: Requires stable documentation (Phase 1 version updates complete).
