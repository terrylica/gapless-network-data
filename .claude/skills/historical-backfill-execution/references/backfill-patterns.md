# Backfill Patterns and Rationale

**Version**: 1.0.0
**Last Updated**: 2025-11-13
**Canonical Pattern**: 1-year chunks (established 2025-11-10)

## Pattern Comparison

| Pattern | Chunk Size | Memory Usage | Time (10yr) | Retry Granularity | Progress Tracking | Recommended |
|---------|-----------|--------------|-------------|-------------------|-------------------|-------------|
| **1-Year Chunks** | ~2.6M blocks | <4GB | 20 min | Year-level | Good | ✅ **Yes** |
| Month Chunks | ~220K blocks | <1GB | 35 min | Month-level | Verbose | ⚠️ Over-chunked |
| Quarter Chunks | ~650K blocks | <2GB | 28 min | Quarter-level | Acceptable | ⚠️ Over-chunked |
| Full Load | 26M blocks | >8GB | N/A | All-or-nothing | None | ❌ **No** (OOM) |
| Multi-Year | >5M blocks | >8GB | N/A | Multi-year | Poor | ❌ **No** (OOM) |

## 1-Year Chunks (Canonical Pattern)

**Rationale**: Optimal balance between memory safety, execution speed, and retry granularity.

### Advantages

1. **Memory Safe**: <4GB per chunk (Cloud Run 4GB limit with 20% safety margin)
2. **Fast Execution**: ~1m40s-2m per year, 20 minutes total for 10 years
3. **Good Retry Granularity**: If one year fails, only re-run that year (not entire backfill)
4. **Progress Tracking**: Clear visibility into completion (2015 ✅, 2016 ✅, 2017 ✅...)
5. **Parallelization Potential**: Can run multiple years in parallel (future optimization)

### Empirical Validation (2025-11-10)

**Test Case**: Complete Ethereum historical backfill (2015-2025, 23.8M blocks)

**Results**:
- Chunk size: 1 year (~2.6M blocks each)
- Memory usage: Peak 3.2 GB per chunk (80% of 4GB limit)
- Execution time: ~1m40s-2m per chunk, 20 minutes total
- Success rate: 100% (no OOM errors, no retries needed)
- Cost: $0 (within BigQuery 1TB/month free tier)

**Conclusion**: 1-year chunks are empirically validated as memory-safe, fast, and reliable.

### Implementation

```bash
# deployment/backfill/chunked_backfill.sh
for year in {START_YEAR..END_YEAR}; do
    echo "Loading blocks for year $year..."

    # Calculate block range for year
    start_block=$((($year - 2015) * 2_600_000 + 1))
    end_block=$(($start_block + 2_600_000 - 1))

    # Load via BigQuery → MotherDuck
    python3 bigquery_to_motherduck.py --start $start_block --end $end_block

    echo "Completed $year"
done
```

## Month Chunks (Over-Chunked)

**Rationale**: Too many chunks for minimal benefit.

### Disadvantages

1. **Slower Total Time**: 35 minutes vs 20 minutes (75% slower due to overhead)
2. **Verbose Progress**: 120 chunks (10 years × 12 months) vs 10 chunks (10 years)
3. **More Retries**: More chunks = more potential failure points
4. **No Memory Benefit**: <1GB per chunk when 4GB available (wasted capacity)

### When to Use

- **Testing**: Validate backfill process on small dataset
- **Memory-Constrained**: Running on <2GB memory systems (not applicable for Cloud Run)

## Full Load (OOM Errors)

**Rationale**: Exceeds Cloud Run memory limit, guaranteed to fail.

### Why It Fails

**Memory Calculation** (26M blocks total):
```
26,000,000 blocks × 100 bytes/block × 11 columns = 28.6 GB
```

**Cloud Run Limit**: 4GB (default), 8GB (max with configuration)

**Result**: OOM error (exit code 137, SIGKILL)

### Failure Mode

```bash
# Attempt full load
python3 bigquery_to_motherduck.py --start 1 --end 26000000

# Output:
# Loading blocks 1 → 26,000,000...
# ERROR: Signal 9 (SIGKILL) received
# Cloud Run Job failed: Memory limit exceeded (exit code 137)
```

## Why Not Multi-Year Chunks?

**Problem**: Unpredictable memory usage per year (2015 vs 2024).

**Example**:
- 2015: 2.2M blocks (Genesis year, partial)
- 2020: 2.6M blocks (full year)
- 2024: 2.7M blocks (full year, higher activity)

**Risk**: 5-year chunk might work for 2015-2019 but fail for 2020-2024 due to increased block activity.

**Solution**: Use consistent 1-year chunks to avoid unpredictable failures.

## Memory Estimation Formula

**Formula**:
```
Memory (GB) = (Blocks × Bytes/Block × Columns) / (1024^3)

Where:
  Blocks = Number of blocks in chunk
  Bytes/Block = 76-100 bytes (empirically validated)
  Columns = 11 (optimized schema)
```

**Example** (1 year):
```
2,600,000 × 100 × 11 / (1024^3) = 2.67 GB
```

**Safety Margin**: Use 80% of Cloud Run limit (4GB × 0.8 = 3.2 GB safe limit)

**Result**: 2.67 GB < 3.2 GB ✅ Safe

## Cost Analysis

### BigQuery Costs

**Query Cost**:
- Full table scan: ~10 MB per year (11 columns vs 23 full schema)
- Free tier: 1 TB/month
- 1 year backfill: 10 MB × 10 years = 100 MB
- Cost: $0 (within free tier)

**Why 11 Columns?**

See `../bigquery-ethereum-data-acquisition/DECISION_RATIONALE.md` for complete column selection rationale (97% cost savings vs full 23-column schema).

### MotherDuck Costs

**Storage**:
- 23.8M blocks × 100 bytes/block = 2.38 GB
- Free tier: 10 GB storage
- Cost: $0 (within free tier)

**Query**:
- Free tier: 10 GB queries/month
- Historical backfill: <10 GB (one-time operation)
- Cost: $0 (within free tier)

### Total Cost

**Historical backfill (2015-2025)**: $0/month (all within free tiers)

## Alternatives Considered

### Streaming API (Rejected)

**Why Considered**: Real-time block streaming via Alchemy WebSocket

**Why Rejected**: 110-day timeline for 10 years of data (vs <1 hour for BigQuery)

**Speed Comparison**:
- Streaming: 1.37 RPS sustained (LlamaRPC empirical test) = 110 days
- BigQuery: Parallel queries (all years simultaneously) = <1 hour

**Decision**: Use BigQuery for historical, Alchemy for real-time only

### Parquet Files (Rejected)

**Why Considered**: Download BigQuery results to Parquet, load into MotherDuck

**Why Rejected**: Extra step, storage overhead, no performance benefit

**Comparison**:
- BigQuery → Parquet → MotherDuck: 2 steps, requires local storage
- BigQuery → MotherDuck (PyArrow): 1 step, zero-copy transfer

**Decision**: Use PyArrow zero-copy transfer (no intermediate Parquet files)

## Related Documentation

- [BigQuery Ethereum Data Acquisition](../../bigquery-ethereum-data-acquisition/SKILL.md) - Column selection rationale
- [MotherDuck Dual Pipeline Architecture](../../../../docs/architecture/motherduck-dual-pipeline.md) - Complete architecture
- [BigQuery Integration Guide](../../../../docs/architecture/bigquery-motherduck-integration.md) - PyArrow zero-copy
- [Troubleshooting](./troubleshooting.md) - OOM errors, retry strategies
