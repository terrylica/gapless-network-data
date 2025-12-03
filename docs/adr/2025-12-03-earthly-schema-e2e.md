---
status: accepted
date: 2025-12-03
decision-maker: Terry Li
consulted: [Explore-Earthly, Explore-Schema, Plan-Earthfile]
research-method: multi-agent
clarification-iterations: 1
perspectives: [BuildInfrastructure, TestingStrategy, SecretManagement]
---

# ADR: Earthly E2E Validation for Schema-First Data Contracts

**Design Spec**: [Implementation Spec](/docs/design/2025-12-03-earthly-schema-e2e/spec.md)

## Context and Problem Statement

The schema-first data contract implementation (ADR 2025-12-02-schema-first-data-contract) introduced CLI commands for generating Python types, DDL, and documentation from a YAML schema. However, there is no automated end-to-end validation to ensure:

1. Generators produce correct output
2. Generated DDL matches live ClickHouse Cloud schema
3. Full workflow executes without errors

**Current State**: Manual CLI invocations without reproducible validation pipeline.

### Before/After

```
     Before / After: Schema Validation Workflow

 Before (Manual):                    After (Earthly E2E):

 ┌─────────────────────────┐         ┌─────────────────────────┐
 │ Developer runs CLI      │         │ Developer runs:         │
 │ commands manually:      │         │                         │
 │                         │         │ earthly +test-schema-e2e│
 │ $ schema generate-types │         │                         │
 │ $ schema generate-ddl   │  ────>  │ Automated pipeline:     │
 │ $ schema validate       │         │ deps → build → generate │
 │ $ schema doc            │         │ → validate → artifacts  │
 │                         │         │                         │
 │ No reproducibility      │         │ Reproducible, cached    │
 │ No artifact tracking    │         │ Artifacts saved locally │
 └─────────────────────────┘         └─────────────────────────┘
```

<details>
<summary>graph-easy source</summary>

```
graph { label: "Before / After: Schema Validation Workflow"; flow: east; }

( Before (Manual):
  [manual] { label: "Developer runs CLI\ncommands manually:\n\n$ schema generate-types\n$ schema generate-ddl\n$ schema validate\n$ schema doc\n\nNo reproducibility\nNo artifact tracking"; }
)

( After (Earthly E2E):
  [earthly] { label: "Developer runs:\n\nearthly +test-schema-e2e\n\nAutomated pipeline:\ndeps → build → generate\n→ validate → artifacts\n\nReproducible, cached\nArtifacts saved locally"; }
)

[manual] --> [earthly]
```

</details>

## Research Summary

| Agent Perspective | Key Finding                                               | Confidence |
| ----------------- | --------------------------------------------------------- | ---------- |
| Explore-Earthly   | No Earthfile exists; Docker infrastructure present        | High       |
| Explore-Schema    | 5 CLI commands available; requires Doppler for validation | High       |
| Plan-Earthfile    | uv + secrets pattern documented for Earthly               | High       |

**User Requirements** (from clarification):

1. **ClickHouse**: Live ClickHouse Cloud via Doppler secrets
2. **Test Scope**: Full workflow (YAML → types → DDL → validate → docs)
3. **Integration**: On-demand only via Claude Code skill

## Decision Drivers

- **Reproducibility**: Same results locally and in CI
- **Caching**: Dependency layer cached until uv.lock changes
- **Secret isolation**: Doppler secrets injected at runtime, not stored in layers
- **Local-first philosophy**: No GitHub Actions testing per project standards

## Considered Options

**Option A**: Shell script wrapper

- Simple bash script calling CLI commands
- No caching, no isolation, no artifact management

**Option B**: Earthly pipeline <- Selected

- Reproducible builds with layer caching
- Secret injection via `--secret-file`
- Artifact saving for inspection
- Aligns with project's Earthly mention in CLAUDE.md

**Option C**: pytest integration tests

- Embedded in test suite
- Less isolation, harder to run standalone
- Would require mocking ClickHouse for CI

## Decision Outcome

Chosen option: **Option B (Earthly pipeline)**, because:

1. Aligns with local-first development philosophy
2. Provides reproducible, isolated build environment
3. Supports secret injection without exposure
4. Generates inspectable artifacts

## Architecture

```
               Earthfile Target Structure

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

<details>
<summary>graph-easy source</summary>

```
graph { label: "Earthfile Target Structure"; flow: south; }

[deps] { label: "+deps\nuv sync --frozen\n(cached layer)"; }
[build] { label: "+build\nmypy + ruff"; }
[unit] { label: "+test-unit\npytest"; }
[generate] { label: "+test-schema-generate\ngenerate-types\ngenerate-ddl\ndoc"; }
[validate] { label: "+test-schema-validate\n--secret CLICKHOUSE_*\nschema validate"; }
[e2e] { label: "+test-schema-e2e\nFull workflow\nSave artifacts"; }
[artifacts] { label: "earthly-artifacts/"; shape: rounded; }

[deps] -> [build]
[build] -> [unit]
[build] -> [generate]
[unit] -> [validate]
[generate] -> [validate]
[validate] -> [e2e]
[e2e] -> [artifacts]
```

</details>

## Consequences

### Positive

- Reproducible E2E validation across developer machines
- Cached dependencies reduce build time on subsequent runs
- Artifacts saved for inspection without polluting source tree
- On-demand invocation via Claude Code skill

### Negative

- Requires Earthly installation (`brew install earthly`)
- Doppler wrapper script adds one indirection layer
- Secrets targets cannot run without Doppler access

## Implementation

### Files to Create

| File                                              | Purpose                        |
| ------------------------------------------------- | ------------------------------ |
| `Earthfile`                                       | Main build file with 6 targets |
| `scripts/earthly-with-doppler.sh`                 | Wrapper for secret injection   |
| `~/.claude/skills/schema-e2e-validation/SKILL.md` | On-demand invocation skill     |

### Earthfile Targets

| Target                  | Secrets | Purpose                     |
| ----------------------- | ------- | --------------------------- |
| `+deps`                 | No      | Install uv + dependencies   |
| `+build`                | No      | Copy source, run mypy/ruff  |
| `+test-unit`            | No      | Run pytest                  |
| `+test-schema-generate` | No      | Generate types/DDL/docs     |
| `+test-schema-validate` | Yes     | Validate vs live ClickHouse |
| `+test-schema-e2e`      | Yes     | Full workflow + artifacts   |

## References

- [Schema-First Data Contract ADR](/docs/adr/2025-12-02-schema-first-data-contract.md)
- [Earthly Integration Guide](https://docs.earthly.dev/docs/guides/integration)
- [Global Plan](/Users/terryli/.claude/plans/toasty-crafting-willow.md) (ephemeral)
