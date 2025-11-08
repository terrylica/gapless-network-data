# RPC Provider Research Workflow Steps

Complete step-by-step guide for researching and validating blockchain RPC providers.

---

## Step 1: Research Official Documentation

Research the provider's documented capabilities:

**Key questions to answer**:
- What are the documented rate limits? (RPS or compute units/credits)
- Is archive node access included in the free tier?
- How far back does historical data go? (genesis block or limited?)
- What is the pricing model? (RPS-based, compute units, API credits)
- Are there separate limits for archive vs standard requests?

**Where to search**:
- Provider pricing pages (e.g., alchemy.com/pricing, infura.io/pricing)
- Documentation for compute unit costs or API credit costs
- Archive node documentation
- Community comparisons (search: "alchemy vs infura vs quicknode comparison")

**Common providers to evaluate**:
- **Alchemy**: Compute unit (CU) based, 300M CU/month free tier
- **Infura**: RPS-based, 100K requests/day free tier (25K archive/day)
- **QuickNode**: API credits, 50M credits/month free tier (disputed)
- **LlamaRPC**: RPS-based, 50 RPS documented (burst limit)

**Output**: Document findings in comparison matrix (see `rpc-comparison-template.md`)

---

## Step 2: Calculate Theoretical Timeline

Calculate the theoretical timeline based on documented limits:

**For RPS-based providers** (Infura, LlamaRPC):
```
Timeline (seconds) = Total blocks ÷ RPS
Timeline (days) = Timeline (seconds) ÷ 86,400
```

**For compute unit providers** (Alchemy):
```
1. Find CU cost per method (e.g., eth_getBlockByNumber = 20 CU)
2. Calculate: Monthly requests = Monthly CU ÷ CU per request
3. Calculate: Daily requests = Monthly requests ÷ 30
4. Calculate: Sustainable RPS = Daily requests ÷ 86,400
5. Timeline (days) = Total blocks ÷ Sustainable RPS ÷ 86,400
```

**For API credit providers** (QuickNode):
```
Same as compute units (if credit cost per method is known)
```

**Use the calculator script**:
```bash
python scripts/calculate_timeline.py --blocks 13000000 --rps 5.79
python scripts/calculate_timeline.py --blocks 13000000 --cu-per-month 300000000 --cu-per-request 20
```

**Critical insight**: Documented "maximum RPS" is often a **burst limit**, not sustained rate.

---

## Step 3: Empirical Validation with POC Testing

**MOST CRITICAL STEP**: Validate rate limits empirically with actual RPC calls.

**Why necessary**: Documented limits are often misleading:
- 50 RPS documented → 1.37 RPS sustainable (LlamaRPC case study)
- Burst limits ≠ sustained limits
- Sliding window rate limiting causes throttling over time

**Testing approach**:

Use the `scripts/test_rpc_rate_limits.py` template to test multiple configurations:

1. **Test 1: Single block fetch** - Validate connectivity and schema
2. **Test 2: Parallel fetch (high workers)** - Test burst limits
3. **Test 3: Parallel fetch (low workers)** - Find parallel threshold
4. **Test 4: Sequential with documented limit** - Test documented RPS
5. **Test 5: Ultra-conservative sequential** - Find sustainable rate

**Rate limit testing pattern**:
```python
# Start aggressive, reduce until 100% success rate
test_configs = [
    {"workers": 10, "expected": "likely fail"},
    {"workers": 3, "expected": "may fail"},
    {"rps": 10, "expected": "may fail"},
    {"rps": 5, "expected": "may work"},
    {"rps": 2, "expected": "should work"},
]
```

**Success criteria**: 100% success rate over 50-100 blocks minimum

**Output**: Document actual sustainable rate (not burst rate)

---

## Step 4: Create Comparison Matrix

Build a comparison matrix with empirical findings:

| Provider       | Timeline | Cost  | Archive | Rate Model | Verdict     |
|----------------|----------|-------|---------|------------|-------------|
| Provider A     | X days   | $Y    | Status  | RPS/CU     | Recommended |
| Provider B     | X days   | $Y    | Status  | RPS/CU     | Fallback    |

**Include these metrics**:
- Timeline (empirically validated, not theoretical)
- Speedup vs baseline (e.g., "4.2x faster than LlamaRPC")
- Cost (free tier vs paid)
- Archive access (Full / Limited / None)
- Rate model complexity (Simple RPS vs Complex CU tracking)
- API key requirement (Yes/No)
- Recommendation (Use / Fallback / Reject)

**See template**: `rpc-comparison-template.md`

---

## Step 5: Document Findings and Make Recommendation

Create a comprehensive report documenting:

1. **Executive Summary** - Recommended provider with key finding (e.g., "4.2x faster")
2. **Detailed Analysis** - Each provider with pros/cons
3. **Comparison Matrix** - Side-by-side metrics
4. **Implementation Strategy** - Conservative rate limits, monitoring, fallback plan
5. **Next Steps** - Account creation, empirical POC, timeline updates

**Report structure**: See `validated-providers.md` for example (Alchemy vs LlamaRPC case study)

**Key decisions to document**:
- Primary provider choice
- Conservative rate limit (X% below sustainable for safety margin)
- Fallback provider if primary hits unexpected limits
- Monitoring strategy (track daily usage, alert thresholds)
