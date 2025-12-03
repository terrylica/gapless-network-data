---
status: implemented
date: 2025-12-02
decision-maker: Terry Li
consulted: []
research-method: plan-mode
clarification-iterations: 3
perspectives: [SingleSourceOfTruth, UtilitarianDesign, LanguageAgnostic]
---

# ADR: Adopt Schema-First Data Contract Architecture

**Design Spec**: [Implementation Spec](/docs/design/2025-12-02-schema-first-data-contract/spec.md)

## Context and Problem Statement

The project has schema definitions scattered across 4+ locations with drift between them:

- `CLAUDE.md` - inline SQL DDL (had UInt64 vs Int64 mismatch)
- `llms.txt` - pandas dtype annotations
- `scripts/clickhouse/create_schema.py` - Python code generating DDL
- ClickHouse Cloud - live production schema

This causes:

1. **Documentation drift**: CLAUDE.md said `DateTime` but production uses `DateTime64(3)`
2. **Type mismatches**: CLAUDE.md had `UInt64` but production uses `Int64`
3. **No single source of truth**: Changes require updating 4+ files manually
4. **No validation**: Drift detected only when bugs surface

### Before/After

```
     Before / After: Schema Management

 Before (Scattered):                After (Schema-First):

 ┌────────────────────┐             ┌─────────────────────────────────┐
 │ CLAUDE.md          │             │ schema/clickhouse/              │
 │ (inline DDL)       │             │   ethereum_mainnet.yaml         │
 ├────────────────────┤             │                                 │
 │ llms.txt           │             │   SINGLE SOURCE OF TRUTH        │
 │ (dtype notes)      │             │   (JSON Schema + x-clickhouse)  │
 ├────────────────────┤  migrate    └─────────────────────────────────┘
 │ create_schema.py   │  ───────>                  │
 │ (Python DDL gen)   │             ┌──────────────┼──────────────┐
 ├────────────────────┤             ▼              ▼              ▼
 │ ClickHouse Cloud   │        ┌─────────┐   ┌──────────┐   ┌─────────┐
 │ (live schema)      │        │ Python  │   │ DDL      │   │ Docs    │
 └────────────────────┘        │ types   │   │ (SQL)    │   │ (MD)    │
                               └─────────┘   └──────────┘   └─────────┘
        4 sources                        1 source → 3 outputs
        (manual sync)                    (generated)
```

## Decision Drivers

- **Eliminate drift**: Single source prevents inconsistencies
- **Utilitarian design**: Schema must be actively consumed by code, not just documentation
- **Language agnostic**: Future Rust/Go code can read same YAML
- **Industry alignment**: JSON Schema is widely supported with tooling ecosystem
- **Validation**: Catch drift before it causes bugs in production

## Research Summary

| Approach           | Pros                          | Cons                                         |
| ------------------ | ----------------------------- | -------------------------------------------- |
| ClickHouse as SSoT | Live, accurate                | Not version controlled, no semantic metadata |
| Git DDL as SSoT    | Version controlled            | SQL only, no type hints for Python/Rust      |
| JSON Schema (YAML) | Language agnostic, extensible | Requires generators                          |
| Protobuf/Avro      | Strong typing                 | Overkill for single table, learning curve    |

## Considered Options

**Option A**: Keep ClickHouse as SSoT with introspection

- Query `system.columns` to generate docs
- No semantic metadata (alpha rankings, deprecation info)
- Cannot generate Python types with full context

**Option B**: Git-managed DDL as SSoT

- Version controlled
- SQL only - need separate files for Python types, pandas dtypes
- Comments not parsed for semantic meaning

**Option C**: JSON Schema (YAML) as SSoT <- Selected

- Language agnostic with custom extensions
- Generates: Python types, DDL, Markdown docs
- Extensible: `x-clickhouse`, `x-pandas`, `x-alpha-feature`, `x-deprecated`
- Industry standard format with tooling ecosystem

## Decision Outcome

Chosen option: **Option C (JSON Schema as YAML)**, because:

1. **Utilitarian**: Schema actively consumed by generators (not passive documentation)
2. **Language agnostic**: YAML readable by Python, Rust, Go, TypeScript
3. **Extensible**: Custom `x-` extensions for ClickHouse types, pandas dtypes, alpha rankings
4. **Version controlled**: Full Git history with semantic diffs
5. **Validated**: `schema validate` command catches drift before production

## Architecture

```
               schema/clickhouse/ethereum_mainnet.yaml
                      (SINGLE SOURCE OF TRUTH)

   JSON Schema (Draft 2020-12) + Custom Extensions:
   - x-clickhouse: {type: "DateTime64(3)", not_null: true}
   - x-pandas: {dtype: "datetime64[ns, UTC]"}
   - x-alpha-feature: {rank: 1, importance: "critical"}
   - x-deprecated: {since: "2022-09-15", reason: "..."}

                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌────────────────┐    ┌───────────────┐
│ generate-types│    │  generate-ddl  │    │  generate-doc │
│               │    │                │    │               │
│ Pydantic/     │    │ CREATE TABLE   │    │ Markdown      │
│ TypedDict     │    │ ClickHouse DDL │    │ Documentation │
└───────────────┘    └────────────────┘    └───────────────┘
```

## CLI Commands

| Command                 | Action                            |
| ----------------------- | --------------------------------- |
| `schema generate-types` | YAML → Python Pydantic/TypedDict  |
| `schema generate-ddl`   | YAML → ClickHouse DDL             |
| `schema validate`       | Compare YAML vs live ClickHouse   |
| `schema apply`          | Apply generated DDL to ClickHouse |
| `schema doc`            | YAML → Markdown documentation     |

## Consequences

### Positive

- Single source of truth eliminates drift
- Python types generated with full context (descriptions, constraints)
- DDL generated with comments from descriptions
- Documentation always matches schema
- `schema validate` catches drift in CI

### Negative

- Initial setup overhead (generators, CLI commands)
- Developers must update YAML, not individual files
- Generated files should not be manually edited

## Implementation Phases

| Phase                 | Deliverables                                              |
| --------------------- | --------------------------------------------------------- |
| 1: Schema File & Core | `ethereum_mainnet.yaml`, `loader.py`, CLI skeleton        |
| 2: Generators         | `python_types.py`, `clickhouse_ddl.py`, `markdown_doc.py` |
| 3: Validation & Apply | `introspector.py`, `validate` command, `apply` command    |
| 4: Integration        | Update api.py to use generated types, update docs         |

## Success Criteria

| Criterion         | Validation                                              |
| ----------------- | ------------------------------------------------------- |
| YAML is SSoT      | All other files are generated from it                   |
| Python types work | `from gapless_network_data.schema import EthereumBlock` |
| DDL matches       | `schema validate` passes                                |
| Docs current      | `schema doc` output matches YAML                        |
| CI integration    | `schema validate` in CI fails on drift                  |

## References

- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12/schema)
- [OpenAPI 3.1 Specification](https://spec.openapis.org/oas/v3.1.0) (uses JSON Schema)
- [Global Plan](/Users/terryli/.claude/plans/toasty-crafting-willow.md) (ephemeral)
