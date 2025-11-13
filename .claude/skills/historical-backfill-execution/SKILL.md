# Historical Backfill Execution

**Version**: 1.0.0
**Last Updated**: 2025-11-13
**Purpose**: Execute chunked historical blockchain data backfills using canonical 1-year pattern

## When to Use

Use this skill when:

- Loading multi-year historical data (e.g., 2015-2025 Ethereum blocks, 23.8M blocks total)
- Gaps detected in MotherDuck requiring backfill
- Preventing OOM (Out of Memory) failures on Cloud Run (4GB memory limit)
- Need to execute complete historical data collection
- Keywords: chunked_backfill.sh, BigQuery historical, gap filling, memory-safe backfill

## Canonical Pattern (Established 2025-11-10)

**Empirically Validated Approach**:

- **Chunk size**: 1 year (~2.6M blocks for Ethereum)
- **Memory usage**: <4GB per chunk (Cloud Run safe, no OOM errors)
- **Execution time**: ~1m40s-2m per chunk (total ~20 minutes for 10 years)
- **Idempotency**: `INSERT OR REPLACE` allows safe re-runs (no duplicates)
- **Cost**: $0/month (within BigQuery 1TB/month free tier, ~10MB per query)

**Why 1-Year Chunks?**

See [Backfill Patterns Reference](./references/backfill-patterns.md) for complete rationale (memory constraints, retry granularity, progress tracking).

## Prerequisites

- GCP project access: `eonlabs-ethereum-bq`
- BigQuery dataset: `bigquery-public-data.crypto_ethereum.blocks`
- MotherDuck database: `md:ethereum_mainnet.blocks`
- MotherDuck token configured (via Secret Manager or environment variable)
- Python dependencies: `google-cloud-bigquery`, `pyarrow`, `duckdb`

## Workflow

### 1. Execute Chunked Backfill

Run the canonical 1-year chunking script:

```bash
cd /Users/terryli/eon/gapless-network-data/deployment/backfill
./chunked_backfill.sh 2015 2025
```

**What This Does**:
- Loads blocks year-by-year from BigQuery
- Uses PyArrow zero-copy transfer → MotherDuck
- Inserts with `INSERT OR REPLACE` (idempotent, prevents duplicates)
- Shows progress for each year: "Loading blocks 1 → 2,600,000"

**Alternative** (use provided validation wrapper):
```bash
.claude/skills/historical-backfill-execution/scripts/chunked_executor.sh 2015 2025
```

### 2. Monitor Progress

Watch the output for year-by-year progress:

```
Loading blocks for year 2015...
Year 2015: Loading blocks 1 → 2,600,000
Completed 2015 in 1m42s

Loading blocks for year 2016...
Year 2016: Loading blocks 2,600,001 → 5,200,000
Completed 2016 in 1m38s

...

All years completed successfully!
Total blocks loaded: 23,800,000
Total time: 18m45s
```

### 3. Verify Completeness

After backfill completes, verify all blocks loaded:

```bash
cd /Users/terryli/eon/gapless-network-data
uv run .claude/skills/motherduck-pipeline-operations/scripts/verify_motherduck.py
```

**Expected Output** (healthy):
```
=== MotherDuck Database Verification ===
Database: md:ethereum_mainnet.blocks

Total blocks: 23,800,000+
Block range: 1 → 23,800,000+
Time range: 2015-07-30 (Genesis) → 2025-11-13

Yearly breakdown:
  2015: 2,600,000 blocks
  2016: 2,600,000 blocks
  2017: 2,600,000 blocks
  ...
  2025: 2,300,000 blocks (partial year)

✅ Database verification complete
```

### 4. Detect Gaps (If Needed)

Run gap detection to ensure zero missing blocks:

```bash
cd /Users/terryli/eon/gapless-network-data
uv run .claude/skills/motherduck-pipeline-operations/scripts/detect_gaps.py
```

**Expected Output** (healthy):
```
=== Gap Detection (Zero-Tolerance) ===
Checking blocks from 1 year ago → 3 minutes ago

✅ No gaps detected (23,800,000 blocks consecutive)
```

**If gaps found**, use auto-fill mode:
```bash
uv run .claude/skills/motherduck-pipeline-operations/scripts/detect_gaps.py --auto-fill
```

### 5. Handle Specific Year Range (Partial Backfill)

Load specific years only:

```bash
# Load only 2023-2024
cd deployment/backfill
./chunked_backfill.sh 2023 2024
```

**Use Cases**:
- Filling detected gaps in specific years
- Testing backfill process on small range
- Recovering from failed backfill (resume from specific year)

## Memory Management

### Cloud Run Limits

**Constraint**: 4GB memory limit per Cloud Run Job execution

**Solution**: 1-year chunks keep memory usage <4GB per execution

**What Happens on OOM**:
- Cloud Run Job exits with code 137 (SIGKILL)
- Error: "Memory limit exceeded"
- Solution: Reduce chunk size or increase Cloud Run memory allocation

### Local Execution

For local testing with memory constraints:

```bash
# Validate memory requirements before execution
.claude/skills/historical-backfill-execution/scripts/validate_chunk_size.py --year 2020
```

**Output**:
```
Estimating memory for 2020 backfill...
Block count: ~2,600,000
Column count: 11 (optimized schema)
Expected memory: ~3.2 GB
Cloud Run safe: ✅ (under 4GB limit)
```

## Troubleshooting

See [Troubleshooting Reference](./references/troubleshooting.md) for complete guide.

**Common Issues**:

| Issue | Cause | Solution |
|-------|-------|----------|
| OOM error (code 137) | Chunk too large | Reduce year range (6 months instead of 1 year) |
| BigQuery quota exceeded | >1TB in 30 days | Wait for quota reset or reduce query frequency |
| "Permission denied" | Missing IAM roles | Grant `roles/bigquery.user` to service account |
| "Table not found" | Wrong dataset | Verify `bigquery-public-data.crypto_ethereum.blocks` |
| Slow execution (>5min/year) | Network issues | Check Cloud Run region (use same as BigQuery: `us`) |

## Backfill Patterns

See [Backfill Patterns Reference](./references/backfill-patterns.md) for alternatives and rationale.

**Pattern Comparison**:

| Pattern | Chunk Size | Memory | Time (10yr) | Retry Granularity | Recommended |
|---------|-----------|--------|-------------|-------------------|-------------|
| **1-Year Chunks** | ~2.6M blocks | <4GB | 20 min | Year-level | ✅ Yes (canonical) |
| Month Chunks | ~220K blocks | <1GB | 35 min | Month-level | ⚠️ Over-chunked (slower) |
| Full Load | 26M blocks | >8GB | N/A | All-or-nothing | ❌ No (OOM errors) |

## Operational History

**Complete Historical Backfill** (2025-11-10):
- **Goal**: Load 23.8M Ethereum blocks (2015-2025)
- **Method**: 1-year chunked backfill via `chunked_backfill.sh`
- **Execution Time**: ~20 minutes total
- **Memory Usage**: <4GB per chunk (no OOM errors)
- **Result**: 100% completeness, zero gaps, zero duplicates
- **Verification**: 23.8M blocks in MotherDuck, latest block within 60 seconds
- **Cost**: $0 (within BigQuery free tier)

**SLO Achievement**: Complete historical data collection (10 years, 23.8M blocks) in <30 minutes with zero manual intervention.

## Related Documentation

- [BigQuery Ethereum Data Acquisition Skill](../bigquery-ethereum-data-acquisition/SKILL.md) - Column selection rationale
- [MotherDuck Pipeline Operations Skill](../motherduck-pipeline-operations/SKILL.md) - Database verification and gap detection
- [MotherDuck Dual Pipeline Architecture](../../../docs/architecture/motherduck-dual-pipeline.md) - Complete architecture
- [BigQuery Integration Guide](../../../docs/architecture/bigquery-motherduck-integration.md) - PyArrow zero-copy transfer

## Scripts

- [`validate_chunk_size.py`](./scripts/validate_chunk_size.py) - Estimate memory requirements before execution
- [`chunked_executor.sh`](./scripts/chunked_executor.sh) - Wrapper for `deployment/backfill/chunked_backfill.sh` with validation

## References

- [`backfill-patterns.md`](./references/backfill-patterns.md) - 1-year chunking rationale, comparison with alternatives
- [`troubleshooting.md`](./references/troubleshooting.md) - OOM errors, retry strategies, Cloud Run logs analysis
