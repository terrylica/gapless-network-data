**ADR**: [Add Auto .env File Loading](/docs/adr/2025-12-01-dotenv-credential-loading.md)

# Feature: Auto .env File Loading

**Goal**: Add python-dotenv support so .env files are auto-loaded for credential resolution.

**Requester**: Alpha Forge integration team

**Version**: v4.5.0 (MINOR - new feature, backward compatible)

**Status**: in_progress

---

## Summary

Add `.env` file auto-loading as a credential resolution option, positioned **before** Doppler and environment variables in the resolution chain. This enables zero-friction onboarding for small teams who share credentials via secure IM.

## Current Credential Resolution Flow

```
_get_clickhouse_credentials()
  1. Try Doppler CLI subprocess (10s timeout)
  2. Fall back to os.environ.get() for env vars
  3. Raise CredentialException with setup instructions
```

## New Credential Resolution Flow

```
_get_clickhouse_credentials()
  0. NEW: load_dotenv() - auto-load .env file if present
  1. Try Doppler CLI subprocess (10s timeout)
  2. Fall back to os.environ.get() for env vars (now includes .env values!)
  3. Raise CredentialException with setup instructions (add .env option)
```

**Key Insight**: `load_dotenv()` populates `os.environ`, so it works seamlessly with the existing env var fallback - no changes to the Doppler or env var reading logic needed.

---

## Implementation Tasks

### Task 1: Add python-dotenv Dependency

**File**: `pyproject.toml`

**Change**: Add to dependencies list (line ~47)

```toml
dependencies = [
    # ... existing ...
    "python-dotenv>=1.0.0",
]
```

- [ ] Dependency added
- [ ] `uv sync` runs successfully

### Task 2: Update Credential Loading

**File**: `src/gapless_network_data/api.py`

**Changes**:

1. Add import at top (after existing imports, ~line 12):

```python
from dotenv import load_dotenv
```

2. Call `load_dotenv()` at the START of `_get_clickhouse_credentials()` (line ~46):

```python
def _get_clickhouse_credentials() -> tuple[str, str, str]:
    """
    Resolve ClickHouse credentials from multiple sources.

    Resolution order:
    1. .env file (auto-loaded via python-dotenv)
    2. Doppler CLI (recommended for teams)
    3. Environment variables (direct export)
    """
    # Load .env file if present (populates os.environ)
    load_dotenv()

    # ... rest of existing Doppler logic ...
```

3. Update error message to include .env option (lines ~99-110):

```python
raise CredentialException(
    """ClickHouse credentials not found.

Option 1: Use .env file (simplest for small teams)
  Create .env in your project root with:
    CLICKHOUSE_HOST_READONLY=<host>
    CLICKHOUSE_USER_READONLY=<user>
    CLICKHOUSE_PASSWORD_READONLY=<password>

Option 2 (Recommended for production): Use Doppler service token
  1. Get token from 1Password: Engineering vault → 'gapless-network-data Doppler Service Token'
  2. doppler configure set token <token_from_1password>
  3. doppler setup --project gapless-network-data --config prd

Option 3: Set environment variables directly
  export CLICKHOUSE_HOST_READONLY=<host>
  export CLICKHOUSE_USER_READONLY=<user>
  export CLICKHOUSE_PASSWORD_READONLY=<password>

Contact your team lead for credentials."""
)
```

- [ ] Import added
- [ ] load_dotenv() call added
- [ ] Error message updated

### Task 3: Create .env.example Template

**File**: `.env.example` (NEW - repo root)

```bash
# ClickHouse Cloud Credentials for gapless-network-data
# Copy this file to .env and fill in your values
# DO NOT commit .env to git!

CLICKHOUSE_HOST_READONLY=your-host.clickhouse.cloud
CLICKHOUSE_USER_READONLY=default
CLICKHOUSE_PASSWORD_READONLY=your-password-here
```

- [ ] File created

### Task 4: Update .gitignore

**File**: `.gitignore`

**Add patterns** (at top of file):

```gitignore
# Environment files (contain secrets)
.env
.env.local
.env.*.local
.env.production
.env.development
```

- [ ] Patterns added

### Task 5: Update Documentation

**File**: `llms.txt` (Setup section ~line 258)

Update to include .env option as first choice:

````markdown
## Setup

Credentials via .env file (simplest), Doppler (recommended), or environment variables.

```bash
# Option 1: .env file (simplest for small teams)
# Create .env in your project root:
CLICKHOUSE_HOST_READONLY=<host>
CLICKHOUSE_USER_READONLY=<user>
CLICKHOUSE_PASSWORD_READONLY=<password>

# Option 2: Doppler (recommended for production)
doppler configure set token <token_from_1password>
doppler setup --project gapless-network-data --config prd

# Option 3: Environment variables
export CLICKHOUSE_HOST_READONLY=<host>
export CLICKHOUSE_USER_READONLY=<user>
export CLICKHOUSE_PASSWORD_READONLY=<password>
```
````

````

- [ ] llms.txt updated

**File**: `README.md` (Setup section ~line 105)

Same update as llms.txt.

- [ ] README.md updated

**File**: `src/gapless_network_data/probe.py` (`get_setup_workflow()` ~line 193)

Update to include .env option in the workflow steps.

- [ ] probe.py updated

### Task 6: Verification

- [ ] `uv sync` completes successfully
- [ ] Existing tests pass
- [ ] Manual test: .env file auto-loads credentials

---

## Files to Modify

| File | Change Type | Lines |
|------|-------------|-------|
| `pyproject.toml` | Add dependency | ~1 |
| `src/gapless_network_data/api.py` | Import + load_dotenv() call + error msg | ~15 |
| `.env.example` | NEW FILE | ~6 |
| `.gitignore` | Add patterns | ~6 |
| `llms.txt` | Update setup section | ~10 |
| `README.md` | Update setup section | ~10 |
| `src/gapless_network_data/probe.py` | Update get_setup_workflow() | ~5 |

**Total**: ~7 files, ~53 lines changed

---

## Backward Compatibility

**Fully backward compatible**:

- Existing Doppler users: Unaffected (Doppler still takes precedence if credentials found)
- Existing env var users: Unaffected (env vars still work)
- New .env users: Just works after adding .env file

**Behavior**: `load_dotenv()` only populates `os.environ` if `.env` exists. If no `.env` file, behavior is identical to before.

---

## Testing Verification

After implementation:

```bash
# Create .env in project directory
cat > .env << 'EOF'
CLICKHOUSE_HOST_READONLY=xxx
CLICKHOUSE_USER_READONLY=yyy
CLICKHOUSE_PASSWORD_READONLY=zzz
EOF

# This should auto-load .env and attempt to connect
python -c "import gapless_network_data as gmd; df = gmd.fetch_blocks(limit=1); print('Success!')"

# Clean up
rm .env
````

---

## Success Criteria

- [ ] python-dotenv>=1.0.0 added to dependencies
- [ ] load_dotenv() called at start of credential resolution
- [ ] .env.example template created with all 3 required variables
- [ ] .gitignore includes .env patterns
- [ ] Existing Doppler and direct env var flows still work (backward compatible)
- [ ] Tests pass
- [ ] Release as v4.5.0 (minor version bump - new feature)

---

## Release

- **Version**: v4.5.0 (MINOR bump - new feature)
- **Commit type**: `feat: add auto .env file loading for credential resolution`
- **Release notes**: "Added python-dotenv support for automatic .env file loading. Small teams can now share credentials via .env files without Doppler setup."
