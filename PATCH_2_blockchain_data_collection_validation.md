# Patch 2: blockchain-data-collection-validation

**Target**: Reduce from 513 lines → ≤200 lines (-313 minimum, -61% reduction)
**Strategy**: Extract embedded workflow steps, code examples, and patterns to references/

---

## File Operations

### CREATE: references/validation-workflow.md (250 lines)

**Source**: Lines 16-236 from current SKILL.md (Steps 1-5 with full details)

**Content to extract**:

- Step 1: Single Block Connectivity Test (full section with code, success criteria, output examples)
- Step 2: Schema Validation (full section with required_fields dict, constraints, success criteria)
- Step 3: Rate Limit Testing (full section with testing progression, rate testing pattern, code)
- Step 4: Complete Pipeline Test (full section with fetch→transform→insert→verify flow, code examples)
- Step 5: Documentation and Decision (full section with report structure, decision template)

**Replace in SKILL.md with**:

```markdown
## Validation Workflow

This skill follows a 5-step empirical validation workflow:

| Step                | Purpose                      | Output                          | Success Criteria                      |
| ------------------- | ---------------------------- | ------------------------------- | ------------------------------------- |
| **1. Connectivity** | Test basic RPC access        | Block fetch confirmed           | Response <500ms, no errors            |
| **2. Schema**       | Validate all required fields | Field validation report         | All fields present, types correct     |
| **3. Rate Limits**  | Find sustainable RPS         | Empirical rate (e.g., 5.79 RPS) | 100% success over 50+ blocks          |
| **4. Pipeline**     | Test fetch→DuckDB flow       | Complete pipeline working       | Data persisted, constraints pass      |
| **5. Decision**     | Document findings            | Go/No-Go recommendation         | All steps passed, timeline calculated |

**Detailed workflow**: See `references/validation-workflow.md` for complete step-by-step guide with code templates, testing patterns, and success criteria for each step.

**Quick start**: Create `01_single_block_fetch.py` using template in `scripts/`, then iterate through steps 2-5.
```

**Savings**: 221 lines → 18 lines (**-203 lines**)

---

### CREATE: references/common-pitfalls.md (100 lines)

**Source**: Lines 300-348 from current SKILL.md ("Common Pitfalls to Avoid")

**Content to extract**:

- Pitfall 1: Skipping Rate Limit Validation (Problem, Reality, Example, Solution)
- Pitfall 2: Testing with Too Few Blocks (Problem, Reality, Example, Solution)
- Pitfall 3: Forgetting CHECKPOINT (Problem, Reality, Solution)
- Pitfall 4: Ignoring CHECK Constraints (Problem, Reality, Solution)
- Pitfall 5: Parallel Fetching on Free Tiers (Problem, Reality, Example, Solution)

**Replace in SKILL.md with**:

```markdown
## Common Pitfalls

**Critical mistakes to avoid**: Skipping empirical rate validation, testing <50 blocks, forgetting DuckDB CHECKPOINT (data loss), ignoring CHECK constraints, and parallel fetching on free tiers.

**Real-world examples**: LlamaRPC 50 RPS documented → 1.37 RPS sustainable (2.7% of max), parallel fetch worked for 20 blocks → failed at 50.

**Full guide**: See `references/common-pitfalls.md` for detailed anti-patterns with problem/reality/solution format and code examples.
```

**Savings**: 49 lines → 6 lines (**-43 lines**)

---

### CREATE: references/example-workflow.md (120 lines)

**Source**: Lines 471-506 from current SKILL.md ("Example Workflow")

**Content to extract**:

- User request: "Validate Alchemy for Ethereum data collection before implementation"
- Full 5-step walkthrough with specific findings
- Step 1 - Single Block (script creation, testing, results)
- Step 2 - Schema (field validation, constraint checks, results)
- Step 3 - Rate Limits (parallel test fails, sequential tests, empirical finding)
- Step 4 - Pipeline (fetch, insert, verify, performance results)
- Step 5 - Document (report creation, decision, timeline, confidence level)

**Replace in SKILL.md with**:

```markdown
## Example Workflow

**Case study**: Validating Alchemy for Ethereum collection → ✅ GO at 5.79 RPS sustained (26 days for 13M blocks, HIGH confidence).

**Full walkthrough**: See `references/example-workflow.md` for complete step-by-step case study showing all 5 validation steps with actual test results and final decision.
```

**Savings**: 36 lines → 4 lines (**-32 lines**)

---

### ENHANCE: scripts/README.md (150 lines)

**Source**: Lines 351-421 from current SKILL.md ("Scripts" section)

**Content to extract**:

- Template: Single Block Fetch (complete code example, imports, schema validation, sanity checks)
- Template: Complete Pipeline (complete code example, fetch→transform→insert→verify flow)
- Code patterns for each POC script
- Usage examples and expected outputs

**Action**: CREATE or ENHANCE `scripts/README.md` with:

````markdown
# Blockchain Data Collection Validation Scripts

## POC Template Scripts

These scripts follow the 5-step validation workflow. Each builds on the previous.

### poc_single_block.py

**Purpose**: Test connectivity and schema validation (Steps 1-2)

**Usage**:

```bash
python scripts/poc_single_block.py
```
````

**Template**:

```python
#!/usr/bin/env python3
"""Test 1: Single block connectivity and schema validation."""

from datetime import datetime
from web3 import Web3

RPC_ENDPOINT = "https://eth.llamarpc.com"

def test_single_block():
    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))
    latest = w3.eth.block_number
    block = w3.eth.get_block(latest)

    # Validate schema
    block_data = {
        'block_number': block['number'],
        'timestamp': datetime.fromtimestamp(block['timestamp']),
        'baseFeePerGas': block.get('baseFeePerGas'),
        'gasUsed': block['gasUsed'],
        'gasLimit': block['gasLimit'],
        'transactions_count': len(block['transactions']),
    }

    # Sanity checks
    assert block_data['gasUsed'] <= block_data['gasLimit']
    assert block_data['block_number'] >= 0

    print("✅ Connectivity and schema validated")

if __name__ == "__main__":
    test_single_block()
```

### poc_complete_pipeline.py

**Purpose**: Test complete fetch→DuckDB pipeline (Step 4)

**Usage**:

```bash
python scripts/poc_complete_pipeline.py
```

**Template**:

```python
#!/usr/bin/env python3
"""Test 4: Complete fetch → DuckDB pipeline."""

import time
import pandas as pd
from web3 import Web3
from gapless_network_data.db import Database

RPC_ENDPOINT = "https://eth.llamarpc.com"
REQUESTS_PER_SECOND = 1.37  # From Step 3 validation
DELAY = 1.0 / REQUESTS_PER_SECOND

def test_pipeline():
    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))

    # Fetch blocks
    blocks = []
    for i in range(100):
        block = w3.eth.get_block(w3.eth.block_number - i)
        blocks.append({
            'block_number': block['number'],
            'timestamp': datetime.fromtimestamp(block['timestamp']),
            'baseFeePerGas': block.get('baseFeePerGas'),
            'gasUsed': block['gasUsed'],
            'gasLimit': block['gasLimit'],
            'transactions_count': len(block['transactions']),
        })
        time.sleep(DELAY)

    # Transform to DataFrame
    df = pd.DataFrame(blocks)

    # Insert into DuckDB
    db = Database(db_path="./test.duckdb")
    db.initialize()
    db.insert_ethereum_blocks(df)

    # Verify
    conn = db.connect()
    count = conn.execute("SELECT COUNT(*) FROM ethereum_blocks").fetchone()[0]
    assert count == len(df)
    print(f"✅ Pipeline validated: {count} blocks")

if __name__ == "__main__":
    test_pipeline()
```

## Testing Progression

1. **01_single_block_fetch.py** - Connectivity + schema (Steps 1-2)
2. **02_batch_parallel_fetch.py** - Parallel testing (expect failures) (Step 3)
3. **03_rate_limited_fetch.py** - Sequential with delays (find sustainable rate) (Step 3)
4. **04_complete_pipeline.py** - Full fetch→DuckDB flow (Step 4)

See `references/validation-workflow.md` for detailed guidance on each script.

````

**Replace in SKILL.md with**:
```markdown
## Scripts

POC template scripts for empirical validation:

- `poc_single_block.py` - Connectivity and schema validation (Steps 1-2)
- `poc_batch_parallel_fetch.py` - Parallel fetch testing (Step 3, expect failures)
- `poc_rate_limited_fetch.py` - Rate-limited sequential fetch (Step 3, find sustainable rate)
- `poc_complete_pipeline.py` - Complete fetch→DuckDB pipeline (Step 4)

**Templates and usage**: See `scripts/README.md` for complete code templates, usage examples, and testing progression guide.
````

**Savings**: 71 lines → 9 lines (**-62 lines**)

---

### REFERENCE (DO NOT DUPLICATE): references/duckdb-patterns.md

**Source**: Lines 237-299 from current SKILL.md ("DuckDB Integration Patterns")

**Current state**: This content is ALREADY extracted to `references/duckdb-patterns.md` ✅

**Action**: REMOVE from SKILL.md, replace with reference link only

**Replace in SKILL.md with**:

```markdown
## DuckDB Integration Patterns

**Critical patterns for data integrity**:

- CHECKPOINT requirement (crash-tested, prevents data loss)
- Batch INSERT from DataFrame (124K blocks/sec performance)
- CHECK constraints for schema validation
- Storage estimates (76-100 bytes/block empirically validated)

**Full guide**: See `references/duckdb-patterns.md` for complete DuckDB integration guide with code examples, crash test results, and performance benchmarks.
```

**Savings**: 62 lines → 8 lines (**-54 lines**)

---

## SKILL.md Refactored Structure (≤200 lines)

```markdown
---
name: blockchain-data-collection-validation
description: Empirical validation workflow for blockchain data collection pipelines before production implementation. Use when validating data sources, testing DuckDB integration, building POC collectors, or verifying complete fetch-to-storage pipelines for blockchain data.
---

# Blockchain Data Collection Validation

## Overview

This skill provides a systematic, test-driven workflow for validating blockchain data collection pipelines before production implementation. Use when building POC collectors, validating new data sources, testing DuckDB integration, or verifying complete fetch-to-storage workflows.

**Key principle**: Validate every component empirically before implementation—connectivity, schema, rate limits, storage, and complete pipeline.

## Validation Workflow

This skill follows a 5-step empirical validation workflow:

| Step                | Purpose                      | Output                          | Success Criteria                      |
| ------------------- | ---------------------------- | ------------------------------- | ------------------------------------- |
| **1. Connectivity** | Test basic RPC access        | Block fetch confirmed           | Response <500ms, no errors            |
| **2. Schema**       | Validate all required fields | Field validation report         | All fields present, types correct     |
| **3. Rate Limits**  | Find sustainable RPS         | Empirical rate (e.g., 5.79 RPS) | 100% success over 50+ blocks          |
| **4. Pipeline**     | Test fetch→DuckDB flow       | Complete pipeline working       | Data persisted, constraints pass      |
| **5. Decision**     | Document findings            | Go/No-Go recommendation         | All steps passed, timeline calculated |

**Detailed workflow**: See `references/validation-workflow.md` for complete step-by-step guide with code templates, testing patterns, and success criteria for each step.

**Quick start**: Create `01_single_block_fetch.py` using template in `scripts/`, then iterate through steps 2-5.

## DuckDB Integration Patterns

**Critical patterns for data integrity**:

- CHECKPOINT requirement (crash-tested, prevents data loss)
- Batch INSERT from DataFrame (124K blocks/sec performance)
- CHECK constraints for schema validation
- Storage estimates (76-100 bytes/block empirically validated)

**Full guide**: See `references/duckdb-patterns.md` for complete DuckDB integration guide with code examples, crash test results, and performance benchmarks.

## Common Pitfalls

**Critical mistakes to avoid**: Skipping empirical rate validation, testing <50 blocks, forgetting DuckDB CHECKPOINT (data loss), ignoring CHECK constraints, and parallel fetching on free tiers.

**Real-world examples**: LlamaRPC 50 RPS documented → 1.37 RPS sustainable (2.7% of max), parallel fetch worked for 20 blocks → failed at 50.

**Full guide**: See `references/common-pitfalls.md` for detailed anti-patterns with problem/reality/solution format and code examples.

## Scripts

POC template scripts for empirical validation:

- `poc_single_block.py` - Connectivity and schema validation (Steps 1-2)
- `poc_batch_parallel_fetch.py` - Parallel fetch testing (Step 3, expect failures)
- `poc_rate_limited_fetch.py` - Rate-limited sequential fetch (Step 3, find sustainable rate)
- `poc_complete_pipeline.py` - Complete fetch→DuckDB pipeline (Step 4)

**Templates and usage**: See `scripts/README.md` for complete code templates, usage examples, and testing progression guide.

## References

### Workflow Documentation

- `references/validation-workflow.md` - Complete 5-step workflow with detailed guidance, code examples, and success criteria
- `references/common-pitfalls.md` - Anti-patterns to avoid with problem/reality/solution format
- `references/example-workflow.md` - Complete case study: Validating Alchemy for Ethereum collection

### Technical Patterns

- `references/duckdb-patterns.md` - DuckDB integration patterns (CHECKPOINT, batch INSERT, constraints, performance)
- `references/ethereum-collector-poc-findings.md` - Ethereum collector POC case study with rate limit discovery

### Scripts

- `scripts/README.md` - Complete script templates and testing progression guide
- `scripts/poc_single_block.py` - Connectivity and schema validation template
- `scripts/poc_batch_parallel_fetch.py` - Parallel fetch testing template
- `scripts/poc_rate_limited_fetch.py` - Rate-limited fetch template
- `scripts/poc_complete_pipeline.py` - Complete pipeline template

## Example Workflow

**Case study**: Validating Alchemy for Ethereum collection → ✅ GO at 5.79 RPS sustained (26 days for 13M blocks, HIGH confidence).

**Full walkthrough**: See `references/example-workflow.md` for complete step-by-step case study showing all 5 validation steps with actual test results and final decision.

## When to Use This Skill

Invoke this skill when:

- Validating a new blockchain RPC provider before implementation
- Testing DuckDB integration for blockchain data
- Building POC collector for new blockchain
- Verifying complete fetch-to-storage pipeline
- Investigating data quality issues
- Planning production collector implementation
- Need empirical validation before committing to architecture

## Related Patterns

This skill pairs well with:

- `blockchain-rpc-provider-research` - For comparing multiple providers before validation
- Project scratch investigations in `scratch/ethereum-collector-poc/` and `scratch/duckdb-batch-validation/`
```

**Estimated line count**: ~195 lines ✅ COMPLIANT

---

## Summary

| Action                                  | Files                  | Lines Extracted | Lines Saved  |
| --------------------------------------- | ---------------------- | --------------- | ------------ |
| Extract validation workflow (Steps 1-5) | 1 new                  | 250             | -203         |
| Extract common pitfalls                 | 1 new                  | 100             | -43          |
| Extract example workflow                | 1 new                  | 120             | -32          |
| Enhance scripts/README.md               | 1 enhanced             | 150             | -62          |
| Remove DuckDB duplication               | 0 (reference only)     | 0               | -54          |
| **TOTAL**                               | **3 new + 1 enhanced** | **620 lines**   | **-394 net** |

**Before**: 513 lines ❌
**After**: ~195 lines ✅ (62% reduction)
**Compliance**: PASS (5 lines under limit)

---

## Verification Checklist

- [ ] All 3 new reference files created in `references/`
- [ ] `scripts/README.md` enhanced with full script templates
- [ ] SKILL.md updated with navigation links to all references
- [ ] Line count verified: `wc -l SKILL.md` shows ≤200
- [ ] All reference links functional (no broken paths)
- [ ] Content integrity: All original information preserved in references
- [ ] DuckDB patterns not duplicated (reference link only)
- [ ] Quick start still actionable (user can begin workflow immediately)
- [ ] Navigation map complete (all references linked from SKILL.md)

---

## Next Steps

1. **Execute Patch 2**: Create 3 new files, enhance 1 file, update SKILL.md
2. **Verify AC1.1**: Run `wc -l SKILL.md` → expect ≤200
3. **Verify AC2.1**: Test workflow navigation (all steps accessible via references)
4. **Proceed to Patch 3**: Apply same pattern to bigquery-ethereum-data-acquisition
