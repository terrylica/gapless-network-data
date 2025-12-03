---
version: "1.0.0"
last_updated: "2025-12-02"
supersedes: []
---

# Design Spec: Schema-First Data Contract Architecture

**ADR**: [Adopt Schema-First Data Contract Architecture](/docs/adr/2025-12-02-schema-first-data-contract.md)

## Problem

Schema definitions are scattered across 4+ locations with drift:

- `CLAUDE.md` - inline SQL DDL (had UInt64 vs Int64 mismatch)
- `llms.txt` - pandas dtype annotations
- `scripts/clickhouse/create_schema.py` - Python code generating DDL
- ClickHouse Cloud - live production schema

No automated validation exists to catch drift before it causes bugs.

---

## Solution: JSON Schema (YAML) as Single Source of Truth

**Design Decision**: Use JSON Schema (Draft 2020-12) written as YAML with custom `x-` extensions for ClickHouse types, pandas dtypes, and alpha feature rankings.

### Architecture

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
└───────┬───────┘    └────────┬───────┘    └───────┬───────┘
        │                     │                    │
        ▼                     ▼                    ▼
┌───────────────┐    ┌────────────────┐    ┌───────────────┐
│ src/.../      │    │ ClickHouse     │    │ docs/schema/  │
│ schema/       │    │ Cloud          │    │ *.md          │
│ models.py     │    │ (apply DDL)    │    │               │
└───────────────┘    └────────────────┘    └───────────────┘
```

---

## Directory Structure

```
schema/
└── clickhouse/
    ├── ethereum_mainnet.yaml     # SSoT - JSON Schema
    └── _generated/
        └── ethereum_mainnet.sql  # Generated DDL

src/gapless_network_data/
├── schema/
│   ├── __init__.py
│   ├── _generated/
│   │   └── ethereum_mainnet.py   # Generated Pydantic models
│   ├── loader.py                 # Load & parse YAML schema
│   └── validators.py             # DataFrame validation helpers
└── cli/
    └── schema/
        ├── __init__.py
        ├── commands.py           # CLI entry points
        ├── generators/
        │   ├── __init__.py
        │   ├── python_types.py   # YAML → Pydantic
        │   ├── clickhouse_ddl.py # YAML → DDL
        │   └── markdown_doc.py   # YAML → Docs
        └── introspector.py       # Query live ClickHouse

docs/schema/
└── ethereum_mainnet.md           # Generated documentation
```

---

## The Single Source of Truth

`schema/clickhouse/ethereum_mainnet.yaml`:

```yaml
# JSON Schema (Draft 2020-12) as YAML
# SINGLE SOURCE OF TRUTH for ethereum_mainnet.blocks

$schema: "https://json-schema.org/draft/2020-12/schema"
$id: "https://gapless-network-data/schema/ethereum_mainnet/blocks"

title: "Ethereum Mainnet Blocks"
description: |
  Block-level data for ML feature engineering.
  Contains gas metrics, transaction counts, and EIP-4844 blob data.

x-clickhouse:
  database: ethereum_mainnet
  table: blocks
  engine: ReplacingMergeTree()
  order_by: [number]
  partition_by: "toYYYYMM(timestamp)"
  settings:
    index_granularity: 8192

type: object

required:
  - timestamp
  - number
  - gas_limit
  - gas_used
  - base_fee_per_gas
  - transaction_count
  - difficulty
  - total_difficulty
  - size

properties:
  timestamp:
    type: string
    format: date-time
    description: "Block timestamp with millisecond precision"
    x-clickhouse:
      type: "DateTime64(3)"
      not_null: true
    x-pandas:
      dtype: "datetime64[ns, UTC]"
    x-alpha-feature:
      rank: 4
      importance: high

  number:
    type: integer
    minimum: 0
    description: "Block number - used as deduplication key"
    x-clickhouse:
      type: "Int64"
      not_null: true
    x-pandas:
      dtype: "int64"
    x-alpha-feature:
      rank: 5
      importance: high

  # ... remaining columns with same structure
```

---

## CLI Commands

### 1. `schema generate-types`

Generate Python types from YAML schema.

```bash
uv run gapless-network-data schema generate-types
```

**Output** (`src/gapless_network_data/schema/_generated/ethereum_mainnet.py`):

```python
# AUTO-GENERATED from schema/clickhouse/ethereum_mainnet.yaml
# DO NOT EDIT - regenerate with: uv run gapless-network-data schema generate-types

from datetime import datetime
from typing import TypedDict
from pydantic import BaseModel, Field

class EthereumBlockRow(TypedDict):
    """Ethereum Mainnet Blocks - typed dict for DataFrame rows."""
    timestamp: datetime
    number: int
    gas_limit: int
    gas_used: int
    base_fee_per_gas: int
    transaction_count: int
    difficulty: int
    total_difficulty: int
    size: int
    blob_gas_used: int | None
    excess_blob_gas: int | None

class EthereumBlock(BaseModel):
    """Ethereum Mainnet Blocks - Pydantic model for validation."""
    timestamp: datetime = Field(description="Block timestamp with millisecond precision")
    number: int = Field(ge=0, description="Block number - used as deduplication key")
    # ... all fields with validation
```

### 2. `schema generate-ddl`

Generate ClickHouse DDL from YAML schema.

```bash
uv run gapless-network-data schema generate-ddl
```

**Output** (`schema/clickhouse/_generated/ethereum_mainnet.sql`):

```sql
-- AUTO-GENERATED from schema/clickhouse/ethereum_mainnet.yaml
-- DO NOT EDIT - regenerate with: uv run gapless-network-data schema generate-ddl

CREATE TABLE IF NOT EXISTS ethereum_mainnet.blocks (
    timestamp DateTime64(3) NOT NULL COMMENT 'Block timestamp with millisecond precision',
    number Int64 NOT NULL COMMENT 'Block number - used as deduplication key',
    gas_limit Int64 NOT NULL COMMENT 'Maximum gas allowed in block',
    gas_used Int64 NOT NULL COMMENT 'Total gas consumed by transactions',
    base_fee_per_gas Int64 NOT NULL COMMENT 'EIP-1559 base fee per gas unit (wei)',
    transaction_count Int64 NOT NULL COMMENT 'Number of transactions in block',
    difficulty UInt256 NOT NULL COMMENT 'Mining difficulty (0 post-Merge, Sep 2022)',
    total_difficulty UInt256 NOT NULL COMMENT 'Cumulative difficulty (frozen post-Merge)',
    size Int64 NOT NULL COMMENT 'Block size in bytes',
    blob_gas_used Nullable(Int64) COMMENT 'EIP-4844 blob gas used (null pre-Dencun, Mar 2024)',
    excess_blob_gas Nullable(Int64) COMMENT 'EIP-4844 excess blob gas (null pre-Dencun)'
)
ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY number
SETTINGS index_granularity = 8192;
```

### 3. `schema validate`

Validate live ClickHouse schema matches YAML contract.

```bash
uv run gapless-network-data schema validate
```

**Process**:

1. Load YAML schema
2. Query `system.columns` + `system.tables`
3. Compare types, nullability, comments
4. Exit 0 if match, exit 1 with diff

### 4. `schema apply`

Apply generated DDL to ClickHouse.

```bash
# Dry run (default)
uv run gapless-network-data schema apply

# Execute
uv run gapless-network-data schema apply --execute
```

### 5. `schema doc`

Generate Markdown documentation.

```bash
uv run gapless-network-data schema doc
```

---

## Implementation Phases

### Phase 1: Schema File & Core Infrastructure

| Task | File                                              | Action                      |
| ---- | ------------------------------------------------- | --------------------------- |
| 1.1  | `schema/clickhouse/ethereum_mainnet.yaml`         | Create JSON Schema (YAML)   |
| 1.2  | `src/gapless_network_data/schema/loader.py`       | YAML loader with validation |
| 1.3  | `src/gapless_network_data/cli/schema/commands.py` | CLI skeleton                |

### Phase 2: Generators

| Task | File                                              | Action                    |
| ---- | ------------------------------------------------- | ------------------------- |
| 2.1  | `src/.../cli/schema/generators/python_types.py`   | YAML → Pydantic/TypedDict |
| 2.2  | `src/.../cli/schema/generators/clickhouse_ddl.py` | YAML → DDL                |
| 2.3  | `src/.../cli/schema/generators/markdown_doc.py`   | YAML → Markdown           |

### Phase 3: Validation & Apply

| Task | File                                 | Action               |
| ---- | ------------------------------------ | -------------------- |
| 3.1  | `src/.../cli/schema/introspector.py` | Query system.columns |
| 3.2  | `src/.../cli/schema/commands.py`     | `validate` command   |
| 3.3  | `src/.../cli/schema/commands.py`     | `apply` command      |

### Phase 4: Integration

| Task | File                              | Action                                      |
| ---- | --------------------------------- | ------------------------------------------- |
| 4.1  | `src/gapless_network_data/api.py` | Use generated types for validation          |
| 4.2  | `CLAUDE.md`                       | Reference generated docs, remove inline DDL |
| 4.3  | `llms.txt`                        | Reference schema path                       |

---

## Files to Create

### Phase 1

1. `schema/clickhouse/ethereum_mainnet.yaml` - The single source of truth
2. `src/gapless_network_data/schema/__init__.py` - Package init
3. `src/gapless_network_data/schema/loader.py` - YAML parser with JSON Schema validation

### Phase 2

4. `src/gapless_network_data/cli/schema/__init__.py` - Package init
5. `src/gapless_network_data/cli/schema/commands.py` - CLI entry points
6. `src/gapless_network_data/cli/schema/generators/__init__.py` - Package init
7. `src/gapless_network_data/cli/schema/generators/python_types.py` - Type generator
8. `src/gapless_network_data/cli/schema/generators/clickhouse_ddl.py` - DDL generator
9. `src/gapless_network_data/cli/schema/generators/markdown_doc.py` - Doc generator

### Phase 3

10. `src/gapless_network_data/cli/schema/introspector.py` - ClickHouse queries

---

## Test Verification

```bash
# After Phase 1 - schema loads
uv run python -c "from gapless_network_data.schema import load_schema; print(load_schema())"

# After Phase 2 - generators work
uv run gapless-network-data schema generate-types
uv run gapless-network-data schema generate-ddl
uv run gapless-network-data schema doc

# After Phase 3 - validation works
uv run gapless-network-data schema validate
```

---

## Success Criteria

| Criterion             | Validation                                              |
| --------------------- | ------------------------------------------------------- |
| **YAML is SSoT**      | All other files are generated from it                   |
| **Python types work** | `from gapless_network_data.schema import EthereumBlock` |
| **DDL matches**       | `schema validate` passes                                |
| **Docs current**      | `schema doc` output matches YAML                        |
| **CI integration**    | `schema validate` in CI fails on drift                  |

---

## Risk Assessment

| Risk                   | Likelihood | Impact | Mitigation                             |
| ---------------------- | ---------- | ------ | -------------------------------------- |
| Generator bugs         | Medium     | High   | Comprehensive tests for each generator |
| JSON Schema complexity | Low        | Medium | Start simple, add extensions as needed |
| CI integration         | Low        | Low    | Add to existing test workflow          |

---

## Release

- Version bump: 4.7.1 → 4.8.0 (minor - new feature)
- Changelog: "feat: add schema-first data contract architecture with CLI commands"

## References

- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12/schema)
- [OpenAPI 3.1 Specification](https://spec.openapis.org/oas/v3.1.0)
- [ClickHouse Data Types](https://clickhouse.com/docs/en/sql-reference/data-types)
