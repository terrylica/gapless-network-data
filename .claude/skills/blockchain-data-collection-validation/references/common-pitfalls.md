# Common Pitfalls to Avoid

This document describes common mistakes when validating blockchain data collection pipelines, with real-world examples and solutions.

---

## Pitfall 1: Skipping Rate Limit Validation

**Problem**: "Provider says 50 RPS, so we'll use 50 RPS"

**Reality**: Documented limits are often burst limits, not sustained rates. Testing with documented limits leads to production failures when rate limiting kicks in during sustained collection.

**Real-world example**: LlamaRPC case study

- Documented: 50 RPS maximum
- Empirical sustained: 1.37 RPS (2.7% of documented max)
- Impact: 36x longer timeline than expected if using documented limit

**Solution**: Always test empirically over 50+ blocks minimum

- Start at documented limit
- Reduce progressively until 100% success rate
- Document empirical sustainable rate
- Use conservative production rate (80-90% of empirical max)

---

## Pitfall 2: Testing with Too Few Blocks

**Problem**: Test 10 blocks, all succeed → assume rate is safe

**Reality**: Sliding window rate limiting causes failures at 50+ blocks. Short tests don't reveal real rate limiting behavior.

**Real-world example**: Ethereum collector POC

- Parallel fetch worked for first 20 blocks (100% success)
- Failed at block 50 with 429 errors (72% success rate overall)
- Cause: Sliding window rate limiting kicked in after initial burst allowance

**Why this happens**:

- Providers allow burst traffic initially
- Rate limiting applies over sliding time windows (e.g., 1 minute)
- Short tests stay within burst allowance
- Sustained collection hits rate limits

**Solution**: Test minimum 50 blocks, ideally 100+

- 50 blocks: Minimum to detect sliding window effects
- 100 blocks: Confident validation of sustainable rate
- Monitor success rate across entire test (not just first N blocks)

---

## Pitfall 3: Forgetting CHECKPOINT

**Problem**: Data inserted successfully, then crash → all data lost

**Reality**: DuckDB keeps data in-memory until CHECKPOINT is called. Without explicit CHECKPOINT, data is not persisted to disk.

**Crash scenarios tested**:

1. Kill process during collection: ❌ Data loss without CHECKPOINT
2. System crash: ❌ Data loss without CHECKPOINT
3. Python exception: ❌ Data loss without CHECKPOINT
4. Normal exit: ✅ Data persisted (DuckDB auto-checkpoints on clean exit)

**Solution**: Call `conn.execute("CHECKPOINT")` after each batch

```python
# After batch INSERT
conn.execute("INSERT INTO ethereum_blocks SELECT * FROM df")

# CRITICAL: Call CHECKPOINT to persist to disk
conn.execute("CHECKPOINT")
```

**Empirically validated**: 0 data loss across 4 crash scenarios when using CHECKPOINT

**When to CHECKPOINT**:

- After every batch insert (recommended for crash recovery)
- Minimum: every 1000 blocks (balance durability vs performance)
- Critical: before any long-running operation that could fail

---

## Pitfall 4: Ignoring CHECK Constraints

**Problem**: Invalid data silently inserted (e.g., gasUsed > gasLimit)

**Reality**: Data corruption propagates to downstream analysis and is hard to debug later. Invalid data breaks assumptions in feature engineering.

**Example corruption scenarios**:

- `gasUsed > gasLimit`: Violates blockchain invariant, indicates data source error
- `block_number < 0`: Invalid block number
- `transactions_count < 0`: Mathematical impossibility

**Impact**:

- Downstream queries return incorrect results
- Feature engineering produces NaN or infinite values
- Hard to trace root cause (where did corruption enter?)

**Solution**: Define CHECK constraints in schema, verify they work

```sql
CREATE TABLE ethereum_blocks (
    block_number BIGINT PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    baseFeePerGas BIGINT,
    gasUsed BIGINT NOT NULL,
    gasLimit BIGINT NOT NULL,
    transactions_count INTEGER NOT NULL,
    CHECK (gasUsed <= gasLimit),
    CHECK (block_number >= 0),
    CHECK (transactions_count >= 0)
)
```

**Benefits**:

- Catches corruption at insertion time (fail fast)
- Prevents invalid data from entering database
- Exception-only failures (no silent errors)
- Self-documenting schema invariants

**Validation**: Test constraints work by trying to insert invalid data and verifying exception is raised

---

## Pitfall 5: Parallel Fetching on Free Tiers

**Problem**: "3 workers is conservative, should be safe"

**Reality**: Even 3 workers trigger rate limits on strict free tiers. Parallel fetching multiplies request rate beyond sustainable limits.

**Real-world example**: Alchemy parallel fetch test

- Sequential 5 RPS: ✅ 100% success (sustainable)
- 3 workers × 5 RPS = 15 RPS effective: ❌ 429 errors after 50 blocks
- 10 workers × 5 RPS = 50 RPS effective: ❌ 72% failure rate

**Why parallel fails**:

- Free tiers have strict sustained rate limits
- Burst allowance depletes quickly with parallel requests
- Multiple workers create traffic spikes
- Rate limiting based on peak traffic, not average

**Solution**: Default to sequential with delays unless proven otherwise

```python
# Recommended: Sequential with conservative delay
REQUESTS_PER_SECOND = 5.0  # From empirical validation
DELAY_BETWEEN_REQUESTS = 1.0 / REQUESTS_PER_SECOND

for block_num in range(start, end):
    block = fetch_block(block_num)
    time.sleep(DELAY_BETWEEN_REQUESTS)  # Rate limiting
```

**When parallel might work**:

- Paid tiers with higher rate limits
- Empirically validated (test 100+ blocks with workers)
- Provider explicitly supports concurrent requests
- Fallback to sequential on any 429 errors

**Conservative approach**:

1. Start with sequential (1 worker)
2. Test empirically with 100+ blocks
3. If successful, try 2 workers over 100+ blocks
4. Only increase if zero 429 errors observed

---

## Summary

| Pitfall                    | Problem                           | Solution                             | Validation Method                        |
| -------------------------- | --------------------------------- | ------------------------------------ | ---------------------------------------- |
| Skipping rate validation   | Trust documented limits           | Empirical testing over 50+ blocks    | 100% success rate sustained              |
| Testing <50 blocks         | Miss sliding window rate limiting | Test minimum 50 blocks, ideally 100+ | Monitor success across entire test       |
| Forgetting CHECKPOINT      | Data loss on crash                | Call CHECKPOINT after each batch     | Crash test: kill process, verify data    |
| Ignoring CHECK constraints | Silent data corruption            | Define constraints, test they work   | Try inserting invalid data, expect error |
| Parallel on free tiers     | Trigger rate limits               | Default to sequential with delays    | Test 100+ blocks, zero 429 errors        |

All pitfalls validated empirically during ethereum-collector-poc and duckdb-batch-validation investigations.
