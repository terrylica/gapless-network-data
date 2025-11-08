# Patch 3: bigquery-ethereum-data-acquisition

**Target**: Reduce from 225 lines → ≤200 lines (-25 minimum, -11% reduction)
**Strategy**: Extract version history, workflow details, and cost analysis to references/

---

## File Operations

### REMOVE: Version History (Lines 22-36)

**Source**: Lines 22-36 from current SKILL.md ("Version History" section)

**Content**:

- v0.2.0 (2025-11-07) - Validated
- v0.1.0 (2025-11-07) - Research

**Action**: REMOVE entirely (violates CLAUDE.md version management standard)

**Rationale**: Per `/Users/terryli/.claude/CLAUDE.md `:

> **Version Locations** (3 only):
>
> - ✅ Git tags - Authoritative release versions
> - ✅ CLAUDE.md - Temporal context for AI agents (project-level only)
> - ✅ CHANGELOG.md - Required by Keep a Changelog standard

Version history belongs in `CHANGELOG.md` or git tags, not skill documentation.

**Savings**: 15 lines → 0 lines (**-15 lines**)

---

### CREATE: references/workflow-steps.md (120 lines)

**Source**: Lines 38-138 from current SKILL.md ("Core Workflow" Steps 1-5)

**Content to extract**:

- Step 1: Understand Free Tier Limits (BigQuery limits, key principle)
- Step 2: Select Columns for ML/Time-Series (recommended columns, discarded columns, rationale)
- Step 3: Validate Query Cost (Dry-Run) (bash commands, validated results, alternative methods)
- Step 4: Stream Results Directly (Method A + Method B with code, validated results)
- Step 5: Load into DuckDB (bash commands, validated results, verification commands)

**Replace in SKILL.md with**:

```markdown
## Core Workflow

This skill follows a 5-step workflow for acquiring Ethereum data from BigQuery:

| Step                    | Purpose                         | Output            | Key Metric                |
| ----------------------- | ------------------------------- | ----------------- | ------------------------- |
| **1. Free Tier Limits** | Understand query/storage limits | Limits documented | 1 TB query, 10 GB storage |
| **2. Column Selection** | Optimize for ML/time-series     | 11 columns chosen | 0.97 GB (97% savings)     |
| **3. Cost Validation**  | Dry-run query cost              | Cost estimate     | 0.1% of free tier         |
| **4. Stream Download**  | Parquet download (no storage)   | .parquet file     | 62 bytes/row              |
| **5. DuckDB Import**    | Load for analysis               | DuckDB database   | <100ms query time         |

**Detailed workflow**: See `references/workflow-steps.md` for complete step-by-step guide with SQL queries, bash commands, and validated results for each step.

**Quick start**: Run `uv run scripts/test_bigquery_cost.py` to validate cost, then `uv run scripts/download_bigquery_to_parquet.py <start> <end> <output>` to download.
```

**Savings**: 101 lines → 16 lines (**-85 lines**)

---

### CREATE: references/cost-analysis.md (80 lines)

**Source**: Lines 139-146 from current SKILL.md ("Cost Analysis" table + context)

**Content to extract**:

- Cost comparison table (11 columns vs 23 columns)
- Free tier utilization calculations
- Column selection rationale (97% cost reduction)
- Recommendation explanation

**Also include from "Key Findings" (lines 182-189)**:

- BigQuery 624x faster than RPC polling
- Hash fields are 97% waste for ML
- Free tier sufficient
- Storage avoidance
- Alternative (1RPC) as fallback

**Replace in SKILL.md with**:

```markdown
## Cost Analysis

**Optimized selection**: 11 columns = 0.97 GB (0.1% of free tier, 97% cost savings vs all 23 columns)

**Key finding**: BigQuery is 624x faster than RPC polling (<1 hour vs 26 days for 12.44M blocks).

**Full analysis**: See `references/cost-analysis.md` for detailed cost comparison, column selection rationale, and RPC provider comparison.
```

**Savings**: 15 lines → 6 lines (**-9 lines**)

---

### CREATE: references/setup-guide.md (50 lines)

**Source**: Lines 191-213 from current SKILL.md ("Prerequisites" section)

**Content to extract**:

- Authentication setup (gcloud auth commands)
- Dependencies (Python packages with versions)
- System requirements (gcloud CLI, DuckDB)
- Verification commands

**Replace in SKILL.md with**:

```markdown
## Prerequisites

**One-time setup**: gcloud auth, Python dependencies (google-cloud-bigquery, pandas, pyarrow, db-dtypes)

**Setup guide**: See `references/setup-guide.md` for complete authentication setup, dependency installation, and verification commands.
```

**Savings**: 23 lines → 4 lines (**-19 lines**)

---

### ENHANCE: scripts/README.md (100 lines)

**Source**: Lines 148-163 from current SKILL.md ("Resources → scripts/" section)

**Content to extract**:

- Script 1: test_bigquery_cost.py (purpose, dependencies, output, usage)
- Script 2: download_bigquery_to_parquet.py (purpose, dependencies, output, usage)
- Validated results for each script
- Expected outputs

**Action**: CREATE or ENHANCE `scripts/README.md` with:

````markdown
# BigQuery Ethereum Data Acquisition Scripts

## test_bigquery_cost.py

**Purpose**: Dry-run cost estimation for BigQuery queries

**Dependencies**:

- google-cloud-bigquery==3.38.0

**Usage**:

```bash
uv run scripts/test_bigquery_cost.py
```
````

**Output** (validated 2025-11-07):

- Bytes processed: 1,036,281,104 (0.97 GB)
- Free tier usage: 0.1% of 1 TB monthly quota
- Runs per month: ~1,061 times
- Cost: $0

## download_bigquery_to_parquet.py

**Purpose**: Stream BigQuery results to Parquet file (no BigQuery storage used)

**Dependencies**:

- google-cloud-bigquery==3.38.0
- pandas==2.3.3
- pyarrow==22.0.0
- db-dtypes==1.4.3

**Usage**:

```bash
uv run scripts/download_bigquery_to_parquet.py <start_block> <end_block> <output_file>

# Example: Download 1,000 blocks
uv run scripts/download_bigquery_to_parquet.py 11560000 11561000 ethereum_blocks.parquet
```

**Output** (validated 2025-11-07, 1,000 block test):

- Rows: 1,001
- File size: 62 KB (62 bytes/row)
- Memory: < 1 MB
- BigQuery storage: 0 GB (streaming confirmed)

## Workflow Integration

1. **Test cost**: Run `test_bigquery_cost.py` to validate query will stay within free tier
2. **Download data**: Run `download_bigquery_to_parquet.py` with block range
3. **Import to DuckDB**: Use DuckDB to load Parquet file
4. **Verify**: Run queries to confirm data integrity

See `references/workflow-steps.md` for complete workflow guide.

````

**Replace in SKILL.md with**:
```markdown
## Scripts

Validated scripts (v0.2.0):

- `test_bigquery_cost.py` - Dry-run cost estimation (0.97 GB for 12.44M blocks)
- `download_bigquery_to_parquet.py` - Streaming Parquet download (62 bytes/row validated)

**Templates and usage**: See `scripts/README.md` for complete usage examples, dependencies, and validated results.
````

**Savings**: 16 lines → 6 lines (**-10 lines**)

---

### MOVE: Next Steps to references/roadmap.md

**Source**: Lines 214-220 from current SKILL.md ("Next Steps")

**Content**:

- Test download (small sample) - ✅ COMPLETED
- Medium test (100,000 blocks)
- Full download (12.44M blocks)
- Documentation update

**Action**: REMOVE from SKILL.md (implementation details, not user-facing)

**Alternative**: If needed, create `references/roadmap.md`, but likely not necessary for skill activation.

**Savings**: 7 lines → 0 lines (**-7 lines**)

---

## SKILL.md Refactored Structure (≤200 lines)

```markdown
---
name: bigquery-ethereum-data-acquisition
description: Workflow for acquiring historical Ethereum blockchain data using Google BigQuery free tier. Empirically validated for cost estimation, streaming downloads, and DuckDB integration. Use when planning bulk historical data acquisition or comparing data source options for blockchain network metrics.
---

# BigQuery Ethereum Data Acquisition

## Overview

Workflow for acquiring 5 years of Ethereum blockchain data (2020-2025, ~12.44M blocks) using Google BigQuery's public dataset within free tier limits. Includes column selection analysis for ML/time-series forecasting, cost optimization, and empirically validated download workflows.

**Status**: ✅ Empirically validated (v0.2.0, 2025-11-07)

## When to Use This Skill

Use when:

- Evaluating BigQuery as a data source for Ethereum historical data
- Planning bulk historical blockchain data acquisition
- Optimizing column selection for feature engineering
- Calculating query costs and free tier utilization
- Comparing BigQuery vs RPC polling approaches
- Streaming downloads without BigQuery storage

## Core Workflow

This skill follows a 5-step workflow for acquiring Ethereum data from BigQuery:

| Step                    | Purpose                         | Output            | Key Metric                |
| ----------------------- | ------------------------------- | ----------------- | ------------------------- |
| **1. Free Tier Limits** | Understand query/storage limits | Limits documented | 1 TB query, 10 GB storage |
| **2. Column Selection** | Optimize for ML/time-series     | 11 columns chosen | 0.97 GB (97% savings)     |
| **3. Cost Validation**  | Dry-run query cost              | Cost estimate     | 0.1% of free tier         |
| **4. Stream Download**  | Parquet download (no storage)   | .parquet file     | 62 bytes/row              |
| **5. DuckDB Import**    | Load for analysis               | DuckDB database   | <100ms query time         |

**Detailed workflow**: See `references/workflow-steps.md` for complete step-by-step guide with SQL queries, bash commands, and validated results for each step.

**Quick start**: Run `uv run scripts/test_bigquery_cost.py` to validate cost, then `uv run scripts/download_bigquery_to_parquet.py <start> <end> <output>` to download.

## Cost Analysis

**Optimized selection**: 11 columns = 0.97 GB (0.1% of free tier, 97% cost savings vs all 23 columns)

**Key finding**: BigQuery is 624x faster than RPC polling (<1 hour vs 26 days for 12.44M blocks).

**Full analysis**: See `references/cost-analysis.md` for detailed cost comparison, column selection rationale, and RPC provider comparison.

## Prerequisites

**One-time setup**: gcloud auth, Python dependencies (google-cloud-bigquery, pandas, pyarrow, db-dtypes)

**Setup guide**: See `references/setup-guide.md` for complete authentication setup, dependency installation, and verification commands.

## Scripts

Validated scripts (v0.2.0):

- `test_bigquery_cost.py` - Dry-run cost estimation (0.97 GB for 12.44M blocks)
- `download_bigquery_to_parquet.py` - Streaming Parquet download (62 bytes/row validated)

**Templates and usage**: See `scripts/README.md` for complete usage examples, dependencies, and validated results.

## References

### Workflow Documentation

- `references/workflow-steps.md` - Complete 5-step workflow with SQL queries, bash commands, and validated results
- `references/cost-analysis.md` - Detailed cost comparison, column selection rationale, RPC provider comparison
- `references/setup-guide.md` - Authentication setup, dependencies, verification commands

### Research Documents

- `references/bigquery_cost_comparison.md` - Empirical cost analysis (6 vs 11 vs 23 columns)
- `references/ethereum_columns_ml_evaluation.md` - Column-by-column ML value analysis
- `references/bigquery_complete_ethereum_data.md` - Complete dataset catalog (11 tables)
- `references/bigquery_cost_estimate.md` - Free tier limits and methodology
- `references/littleblack-hardware-report.md` - Local vs cloud hardware comparison

### Scripts & Validation

- `scripts/README.md` - Complete script usage guide with validated results
- `VALIDATION_STATUS.md` - Empirical test results, testing methodology, dependencies validated

## Related Skills

- `blockchain-rpc-provider-research` - RPC rate limit comparison and provider evaluation
- `blockchain-data-collection-validation` - Empirical validation workflow for data pipelines
```

**Estimated line count**: ~190 lines ✅ COMPLIANT

---

## Summary

| Action                    | Files                  | Lines Extracted | Lines Saved  |
| ------------------------- | ---------------------- | --------------- | ------------ |
| Remove version history    | 0 (deleted)            | -15             | -15          |
| Extract workflow steps    | 1 new                  | 120             | -85          |
| Extract cost analysis     | 1 new                  | 80              | -9           |
| Extract setup guide       | 1 new                  | 50              | -19          |
| Enhance scripts/README.md | 1 enhanced             | 100             | -10          |
| Remove "Next Steps"       | 0 (deleted)            | -7              | -7           |
| **TOTAL**                 | **3 new + 1 enhanced** | **350 lines**   | **-145 net** |

**Before**: 225 lines ❌
**After**: ~190 lines ✅ (16% reduction)
**Compliance**: PASS (10 lines under limit)

---

## Verification Checklist

- [ ] Version history removed from SKILL.md
- [ ] All 3 new reference files created in `references/`
- [ ] `scripts/README.md` enhanced with full script documentation
- [ ] "Next Steps" section removed (internal roadmap, not user-facing)
- [ ] SKILL.md updated with navigation links to all references
- [ ] Line count verified: `wc -l SKILL.md` shows ≤200
- [ ] All reference links functional (no broken paths)
- [ ] Content integrity: All original information preserved in references
- [ ] Quick start still actionable (user can run scripts immediately)
- [ ] Navigation map complete (all references linked from SKILL.md)

---

## Next Steps

1. **Execute Patch 3**: Create 3 new files, enhance 1 file, update SKILL.md
2. **Verify AC1.1**: Run `wc -l SKILL.md` → expect ≤200
3. **Verify AC2.1**: Test workflow navigation (all steps accessible via references)
4. **Generate final compliance report**: All 3 skills at 100% compliance
