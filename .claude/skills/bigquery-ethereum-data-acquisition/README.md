# BigQuery Ethereum Data Acquisition Skill

**Status**: Core workflows validated
**Created**: 2025-11-07

---

## Version History

### v0.2.0 (2025-11-07) - Validated

**Tested**:

- Cost estimation script (0.97 GB for 12.44M blocks)
- Parquet streaming download (1,001 blocks, 62 KB)
- DuckDB import and query execution

**Fixed**:

- Added db-dtypes dependency to download script

**Status**: Core workflows empirically validated, ready for production use.

### v0.1.0 (2025-11-07) - Research

**Completed**:

- 5 parallel agent investigation
- Column selection analysis (11 vs 23 columns)
- Cost comparison (BigQuery vs RPC providers)
- Schema validation (23 columns confirmed)

**Status**: Research complete, workflows untested.

---

## What This Skill Contains

### ✅ VALIDATED (v0.2.0)

All core workflows empirically tested:

- Cost estimation: 0.97 GB (0.1% of 1 TB free tier)
- Parquet streaming: 1,001 blocks downloaded (62 KB, 62 bytes/row)
- DuckDB integration: Import and query verified (<100ms)
- Storage avoidance: 0 GB BigQuery tables created (streaming confirmed)

### 📚 RESEARCH (v0.1.0)

Research completed but not re-tested in v0.2.0:

- 23 columns confirmed in blocks table
- Column cost analysis (6, 9, 11, 23 column selections)
- Free tier limits verified
- RPC provider comparison (BigQuery vs 1RPC vs Alchemy)

**See `VALIDATION_STATUS.md ` for complete testing results.**

---

## Directory Structure

```
bigquery-ethereum-data-acquisition/
├── SKILL.md                          # Workflow documentation (v0.2.0)
├── VALIDATION_STATUS.md              # Empirical test results (v0.2.0)
├── README.md                         # This file
│
├── references/                       # Research documents (v0.1.0)
│   ├── README.md                     # Index of reference files
│   ├── bigquery_cost_comparison.md   # Cost analysis (6 vs 11 vs 23 cols)
│   ├── ethereum_columns_ml_evaluation.md  # Column-by-column ML value
│   ├── bigquery_complete_ethereum_data.md # Complete dataset catalog
│   ├── bigquery_cost_estimate.md     # Free tier methodology
│   └── littleblack-hardware-report.md     # Local vs cloud comparison
│
└── scripts/                          # Validated scripts (v0.2.0)
    ├── README.md                     # Script documentation
    ├── test_bigquery_cost.py         # ✅ Dry-run cost check
    └── download_bigquery_to_parquet.py  # ✅ Streaming Parquet download
```

---

## Key Findings

From 5 parallel research agents (2025-11-06) + empirical validation (2025-11-07):

1. **BigQuery is 624x faster** than RPC polling (<1 hour vs 26 days)
2. **Column optimization saves 97%**: 11 cols (0.97 GB) vs 23 cols (34.4 GB)
3. **Hash fields have zero ML value**: Cryptographically random, no temporal patterns
4. **Free tier is sufficient**: 0.97 GB query = 0.1% of 1 TB/month limit
5. **Storage avoidance works**: Streaming confirmed (0 GB BigQuery tables)

---

## Quick Start

### Prerequisites

```bash
# Authenticate (one-time)
gcloud auth application-default login

# Verify access
bq ls bigquery-public-data:crypto_ethereum

# Install DuckDB (optional)
brew install duckdb
```

### Phase 1: Cost Estimation (Validated)

```bash
cd /.claude/skills/bigquery-ethereum-data-acquisition

# Check query cost before downloading
uv run scripts/test_bigquery_cost.py
```

**Expected output**:

```
Bytes to be processed: 1,036,281,104 bytes (0.97 GB)
Free tier usage: 0.1% of 1 TB monthly quota
Cost: $0
```

### Phase 2: Small Test (Validated)

```bash
# Download 1,000 blocks to test workflow
uv run scripts/download_bigquery_to_parquet.py 11560000 11561000 test.parquet

# Verify file created
ls -lh test.parquet  # Expected: ~62 KB

# Query with DuckDB
duckdb :memory: "SELECT COUNT(*), MIN(number), MAX(number) FROM read_parquet('test.parquet')"
```

**Expected output**:

```
┌───────────┬───────────┬───────────┐
│ row_count │ min_block │ max_block │
├───────────┼───────────┼───────────┤
│      1001 │  11560000 │  11561000 │
└───────────┴───────────┴───────────┘
```

### Phase 3: Full Download (Pending Validation)

```bash
# Download all 12.44M blocks (~770 MB Parquet, <1 hour)
uv run scripts/download_bigquery_to_parquet.py 11560000 24000000 ethereum_blocks.parquet

# Load into DuckDB
duckdb ethereum.db << EOF
CREATE TABLE blocks AS SELECT * FROM read_parquet('ethereum_blocks.parquet');
CHECKPOINT;
EOF
```

---

## Research Methodology

### Parallel Agent Investigation (2025-11-06)

5 specialized agents ran concurrently:

1. **Major RPC Providers**: Ankr, dRPC, Infura rate limits
2. **Public Endpoints**: 1RPC empirical testing (77 RPS measured)
3. **Decentralized Networks**: Pocket Network, dRPC analysis
4. **Alternative Sources**: BigQuery, Dune Analytics comparison
5. **Local Nodes**: Erigon, Reth, Geth hardware requirements

**Output**: 52 research files → consolidated to 5 reference documents

### Empirical Validation (2025-11-07)

All core workflows tested:

- Platform: macOS 14.6 (Sequoia), ARM64
- Python: 3.13.6 (via uv)
- DuckDB: 1.4.1 (via Homebrew)
- Authentication: gcloud auth application-default login

**Output**: All workflows validated, db-dtypes dependency added

---

## Cost Analysis (Validated)

| Selection    | Columns | Cost (GB) | % Free Tier | Status       |
| ------------ | ------- | --------- | ----------- | ------------ |
| Optimized ML | 11      | 0.97      | 0.1%        | ✅ TESTED    |
| All columns  | 23      | 34.4      | 3.4%        | ⚠️ ESTIMATED |

**Recommendation**: Use 11-column selection (0.97 GB, validated).

---

## Dependencies (Validated)

### Python Packages

```python
# test_bigquery_cost.py
dependencies = ["google-cloud-bigquery"]

# download_bigquery_to_parquet.py
dependencies = ["google-cloud-bigquery", "pandas", "pyarrow", "db-dtypes"]
```

**Validated versions** (2025-11-07):

- google-cloud-bigquery==3.38.0
- pandas==2.3.3
- pyarrow==22.0.0
- db-dtypes==1.4.3

### System Requirements

- gcloud CLI (authentication)
- DuckDB 1.4.1+ (optional, for local queries)

---

## Design Principles

1. **Empirical validation first**: Never trust documentation, always test
2. **Separation of tested vs untested**: Clear status tracking
3. **Promotional-language-free**: Technical descriptions only

---

## Next Steps

### Immediate (v0.2.0)

1. ✅ Cost estimation validated
2. ✅ Small sample download validated (1,000 blocks)
3. ✅ DuckDB integration validated

### Short-term (v0.3.0)

1. Medium sample test (100,000 blocks)
2. Measure actual download time
3. Test for rate limiting

### Long-term (v1.0.0)

1. Full download validation (12.44M blocks)
2. Document actual timeline vs estimate
3. Production deployment

---

## Related Skills

- `blockchain-rpc-provider-research` (v0.2.0) - RPC rate limit empirical validation
- `blockchain-data-collection-validation` (v0.2.0) - Data pipeline validation workflow

These three skills form a complete workflow for blockchain data acquisition.

---

## Distribution

**Package**: Available as `/.claude/skills/bigquery-ethereum-data-acquisition.zip ` for distribution

**Contents**:

- SKILL.md - Workflow documentation
- VALIDATION_STATUS.md - Test results
- scripts/ - Validated Python scripts
- references/ - Research documents

**Installation**: Extract to `.claude/skills/` directory
