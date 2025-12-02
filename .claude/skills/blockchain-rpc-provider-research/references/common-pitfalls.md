# Common Pitfalls to Avoid

Anti-patterns discovered through empirical validation of blockchain RPC providers.

---

## Pitfall 1: Trusting Documented Burst Limits as Sustained Rates

**Problem**: Provider documentation says "50 RPS maximum" → assume 50 RPS is safe for sustained use

**Reality**: Documented limits are often **burst limits**, not sustained limits

**Example**: LlamaRPC case study

```
Documented: 50 RPS maximum
Empirical sustained: 1.37 RPS (2.7% of documented max)
Failure mode: 429 rate limit errors after ~50 blocks at 10 RPS
```

**Solution**:

- Always empirically validate over 50+ requests minimum
- Test at documented limit first, reduce if failures occur
- Look for degradation over time (sliding window rate limiting)
- Document actual sustainable rate in comparison matrix

---

## Pitfall 2: Testing with Too Few Blocks

**Problem**: Test with 10-20 blocks, all succeed → assume rate is safe

**Reality**: Sliding window rate limiting causes failures at 50+ blocks

**Example**: Parallel fetch case study

```
Blocks 1-20: 100% success rate (3 workers, optimistic)
Blocks 21-50: 95% success rate (429 errors start appearing)
Blocks 51-100: 72% success rate (cumulative throttling)
```

**Solution**:

- Test minimum 50 blocks, ideally 100+
- Monitor success rate over time, not just initial blocks
- Look for degradation patterns (first 20 succeed, then failures)
- Validate both short bursts and sustained requests

---

## Pitfall 3: Parallel Fetching on Free Tiers

**Problem**: "3 workers is conservative" → assume parallel fetching is safe

**Reality**: Even 3 workers trigger rate limits on strict free tiers

**Example**: Parallel fetch validation

```
Configuration: 3 workers, 10 concurrent requests
Result: 429 errors after 50 blocks
Cause: Cumulative RPS = 3 * (1 req / delay) > provider limit
```

**Solution**:

- Default to sequential with delays unless proven otherwise
- Test parallel fetching explicitly (workers=1, 2, 3, 5, 10)
- Measure actual RPS with parallel workers: `workers * (1 / delay_per_worker)`
- Use parallel only if empirically validated (100% success over 100+ blocks)

---

## Pitfall 4: Ignoring Compute Unit Costs Per Method

**Problem**: Calculate timeline using average CU cost across all methods

**Reality**: Different RPC methods have different CU costs

**Example**: Alchemy compute unit costs

```
eth_blockNumber: 10 CU (cheap, quick check)
eth_getBlockByNumber: 20 CU (actual data fetch)
eth_getLogs: 75 CU (expensive, log queries)
```

**Impact on timeline**:

```
Using eth_blockNumber cost (10 CU):
  300M CU / 10 CU = 30M blocks/month (WRONG)

Using actual method eth_getBlockByNumber (20 CU):
  300M CU / 20 CU = 15M blocks/month (CORRECT)

Difference: 2x timeline error
```

**Solution**:

- Calculate based on actual method being used, not averages
- Verify CU cost in provider documentation for specific method
- Test with small batch to measure actual CU consumption
- Monitor daily CU usage to validate calculations

---

## Pitfall 5: Forgetting Archive Access Restrictions

**Problem**: Provider offers "100K requests/day" → assume all 100K can be archive requests

**Reality**: Some providers limit archive requests separately

**Example**: Infura tiered limits

```
Total requests: 100K/day
Standard requests: 75K/day (recent blocks)
Archive requests: 25K/day (historical blocks)
```

**Impact on historical collection**:

```
Theoretical (100K/day total):
  100K / 86,400 = 1.16 RPS → 129 days for 13M blocks

Actual (25K/day archive):
  25K / 86,400 = 0.29 RPS → 519 days for 13M blocks

Difference: 4x timeline error
```

**Solution**:

- Verify archive access is truly "unlimited" or "full"
- Check if archive requests have separate quota
- Test with actual historical block numbers (not recent blocks)
- Document archive vs standard limits in comparison matrix
