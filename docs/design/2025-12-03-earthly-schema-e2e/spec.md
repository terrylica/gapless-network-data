---
version: "1.0.0"
status: completed
last_updated: "2025-12-03"
supersedes: []
---

# Design Spec: Earthly E2E Validation for Schema-First Data Contracts

**ADR**: [Earthly E2E Validation](/docs/adr/2025-12-03-earthly-schema-e2e.md)

## Problem

The schema-first data contract implementation (ADR 2025-12-02-schema-first-data-contract) introduced CLI commands for generating Python types, DDL, and documentation from a YAML schema. However, there is no automated end-to-end validation to ensure:

1. Generators produce correct output
2. Generated DDL matches live ClickHouse Cloud schema
3. Full workflow executes without errors

**Current State**: Manual CLI invocations without reproducible validation pipeline.

---

## Solution: Earthly Pipeline with Doppler Secrets

**Design Decision**: Use Earthly for reproducible, cached builds with Doppler secret injection for ClickHouse Cloud validation.

### Architecture

```
                    +deps
                      │
                      │ uv sync --frozen
                      │ (cached layer)
                      ▼
                   +build
                      │
                      │ mypy + ruff
                      │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
    +test-unit          +test-schema-generate
          │                     │
          │ pytest              │ generate-types
          │                     │ generate-ddl
          │                     │ doc
          │                     │
          └──────────┬──────────┘
                     │
                     ▼
            +test-schema-validate
                     │
                     │ --secret CLICKHOUSE_*
                     │ schema validate
                     │
                     ▼
             +test-schema-e2e
                     │
                     │ Full workflow
                     │ Save artifacts
                     ▼
             earthly-artifacts/
```

---

## Files to Create

| File                                              | Purpose                        |
| ------------------------------------------------- | ------------------------------ |
| `Earthfile`                                       | Main build file with 6 targets |
| `scripts/earthly-with-doppler.sh`                 | Wrapper for secret injection   |
| `~/.claude/skills/schema-e2e-validation/SKILL.md` | On-demand invocation skill     |

---

## Implementation Tasks

### Task 1: Create Earthfile

**File**: `/Earthfile`

```earthfile
VERSION 0.8

FROM python:3.11-slim
WORKDIR /app

# Cached dependency layer
deps:
    RUN pip install uv
    COPY pyproject.toml uv.lock README.md ./
    RUN uv sync --frozen
    SAVE IMAGE --cache-hint

# Build - copy source files
build:
    FROM +deps
    COPY --dir src schema tests ./
    COPY docs/schema docs/schema
    SAVE ARTIFACT src /src
    SAVE ARTIFACT schema /schema

# Unit tests (no secrets)
test-unit:
    FROM +build
    RUN uv run pytest tests/ -v

# Schema generation (no secrets)
test-schema-generate:
    FROM +build
    RUN uv run gapless-network-data schema generate-types
    RUN uv run gapless-network-data schema generate-ddl
    RUN uv run gapless-network-data schema doc
    RUN test -f src/gapless_network_data/schema/_generated/blocks.py
    RUN test -f schema/clickhouse/_generated/ethereum_mainnet.sql
    RUN test -f docs/schema/ethereum_mainnet.md
    SAVE ARTIFACT src/gapless_network_data/schema/_generated AS LOCAL ./earthly-artifacts/types
    SAVE ARTIFACT schema/clickhouse/_generated AS LOCAL ./earthly-artifacts/ddl
    SAVE ARTIFACT docs/schema AS LOCAL ./earthly-artifacts/docs

# Schema validation (requires secrets)
test-schema-validate:
    FROM +build
    RUN --secret CLICKHOUSE_HOST_READONLY \
        --secret CLICKHOUSE_USER_READONLY \
        --secret CLICKHOUSE_PASSWORD_READONLY \
        uv run gapless-network-data schema validate

# Full E2E workflow (requires secrets)
test-schema-e2e:
    FROM +build
    RUN uv run gapless-network-data schema generate-types
    RUN uv run gapless-network-data schema generate-ddl
    RUN uv run gapless-network-data schema doc
    RUN --secret CLICKHOUSE_HOST_READONLY \
        --secret CLICKHOUSE_USER_READONLY \
        --secret CLICKHOUSE_PASSWORD_READONLY \
        uv run gapless-network-data schema validate
    SAVE ARTIFACT src/gapless_network_data/schema/_generated AS LOCAL ./earthly-artifacts/e2e/types
    SAVE ARTIFACT schema/clickhouse/_generated AS LOCAL ./earthly-artifacts/e2e/ddl
    SAVE ARTIFACT docs/schema AS LOCAL ./earthly-artifacts/e2e/docs

# All non-secret targets
all:
    BUILD +test-unit
    BUILD +test-schema-generate
```

### Task 2: Create Doppler Wrapper Script

**File**: `/scripts/earthly-with-doppler.sh`

```bash
#!/bin/bash
set -euo pipefail

DOPPLER_PROJECT="gapless-network-data"
DOPPLER_CONFIG="prd"

SECRETS_FILE=$(mktemp)
trap "rm -f $SECRETS_FILE" EXIT

echo "Fetching ClickHouse secrets from Doppler..."
# Earthly --secret-file-path expects KEY=value format without quotes
doppler secrets download \
    --project "$DOPPLER_PROJECT" \
    --config "$DOPPLER_CONFIG" \
    --format env \
    --no-file | grep -E '^CLICKHOUSE_' | sed 's/"//g' > "$SECRETS_FILE"

echo "Running: earthly $*"
earthly --secret-file-path="$SECRETS_FILE" "$@"
```

### Task 3: Update .gitignore

Add to `.gitignore`:

```gitignore
# Earthly
earthly-artifacts/
```

### Task 4: Create Claude Code Skill

**File**: `~/.claude/skills/schema-e2e-validation/SKILL.md`

```yaml
---
name: schema-e2e-validation
description: Run Earthly E2E validation for schema-first data contracts. Use when validating schema changes, testing YAML against live ClickHouse, or regenerating types/DDL/docs.
allowed-tools: Read, Bash, Grep
---
```

````markdown
# Schema E2E Validation

## When to Use

- Validating schema changes before commit
- Verifying YAML schema matches live ClickHouse Cloud
- Regenerating Python types, DDL, or docs
- Running full schema workflow validation

## Quick Commands

### Generation only (no secrets)

```bash
cd /Users/terryli/eon/gapless-network-data
earthly +test-schema-generate
```
````

### Full E2E with validation (requires Doppler)

```bash
cd /Users/terryli/eon/gapless-network-data
./scripts/earthly-with-doppler.sh +test-schema-e2e
```

### All targets (no secrets)

```bash
earthly +all
```

## Artifacts

Check `./earthly-artifacts/` for generated files:

- `types/blocks.py` - Pydantic + TypedDict
- `ddl/ethereum_mainnet.sql` - ClickHouse DDL
- `docs/ethereum_mainnet.md` - Markdown documentation

## Troubleshooting

### Secret Errors

If validation fails with "missing secret", ensure Doppler is configured:

```bash
doppler configure set token <token_from_1password>
doppler setup --project gapless-network-data --config prd
```

### Cache Issues

Force rebuild without cache:

```bash
earthly --no-cache +test-schema-e2e
```

## Earthfile Targets Reference

| Target                  | Secrets | Purpose                     |
| ----------------------- | ------- | --------------------------- |
| `+deps`                 | No      | Install uv + dependencies   |
| `+build`                | No      | Copy source, run mypy/ruff  |
| `+test-unit`            | No      | Run pytest                  |
| `+test-schema-generate` | No      | Generate types/DDL/docs     |
| `+test-schema-validate` | Yes     | Validate vs live ClickHouse |
| `+test-schema-e2e`      | Yes     | Full workflow + artifacts   |
| `+all`                  | No      | Run all non-secret targets  |

````

---

## Test Verification

```bash
# After Task 1 - Earthfile works
earthly +deps

# After Task 2 - wrapper script works
./scripts/earthly-with-doppler.sh +test-schema-validate

# After Task 3 - full E2E
./scripts/earthly-with-doppler.sh +test-schema-e2e
ls -la earthly-artifacts/
````

---

## Success Criteria

| Criterion             | Validation                                         |
| --------------------- | -------------------------------------------------- |
| **Earthfile runs**    | `earthly +test-schema-generate` succeeds           |
| **Secrets injected**  | `./scripts/earthly-with-doppler.sh` passes secrets |
| **Validation passes** | `+test-schema-validate` exits 0                    |
| **Artifacts saved**   | `earthly-artifacts/` contains generated files      |
| **Skill invokable**   | Claude Code can run E2E validation on-demand       |

---

## Risk Assessment

| Risk                    | Likelihood | Impact | Mitigation                      |
| ----------------------- | ---------- | ------ | ------------------------------- |
| Doppler access required | Low        | Medium | Document setup in skill         |
| Earthly not installed   | Low        | Medium | `brew install earthly` in skill |
| Secret exposure         | Low        | High   | Temp file with trap cleanup     |

---

## Release

- Version bump: 4.7.0 → 4.8.0 (minor - new feature)
- Changelog: "feat: add Earthly E2E validation for schema-first data contracts"

## References

- [Schema-First Data Contract ADR](/docs/adr/2025-12-02-schema-first-data-contract.md)
- [Earthly Secrets Documentation](https://docs.earthly.dev/docs/guides/secrets)
- [Doppler CLI Reference](https://docs.doppler.com/docs/cli)
