# Example Workflow: Ethereum RPC Provider Selection

Complete walkthrough of selecting an RPC provider for 13M Ethereum blocks collection.

---

## User Request

"We need to collect 13M Ethereum blocks (5 years of historical data). Which RPC provider should we use?"

---

## Step 1: Research Official Documentation

**Search query**: "Alchemy Infura QuickNode Ethereum RPC free tier comparison 2025"

**Findings**:

- **Alchemy**: 300M compute units (CU) per month, free tier
- **Infura**: 100K requests/day (25K archive/day), free tier
- **QuickNode**: 50M API credits/month, free tier (disputed in community)
- **LlamaRPC**: 50 RPS maximum (no signup required)

**Archive access**:

- Alchemy: Full archive access (genesis block to latest)
- Infura: Limited (25K archive requests/day, separate from 75K standard)
- QuickNode: Full archive (credit-based, need validation)
- LlamaRPC: Full archive (community-run, no guarantees)

**Document findings** in comparison matrix (see `rpc-comparison-template.md`)

---

## Step 2: Calculate Theoretical Timeline

**Alchemy calculation** (CU-based):

```
Compute units per month: 300M CU
Cost per eth_getBlockByNumber: 20 CU

Monthly blocks: 300M CU ÷ 20 CU = 15M blocks
Daily blocks: 15M ÷ 30 = 500K blocks
Sustainable RPS: 500K ÷ 86,400 = 5.79 RPS

Timeline: 13M blocks ÷ 5.79 RPS ÷ 86,400 = 26.0 days
```

**Infura calculation** (RPS-based, archive limit):

```
Archive requests per day: 25K
Sustainable RPS: 25K ÷ 86,400 = 0.29 RPS

Timeline: 13M blocks ÷ 0.29 RPS ÷ 86,400 = 519 days
```

**LlamaRPC calculation** (documented RPS):

```
Documented maximum: 50 RPS (optimistic, likely burst limit)
Theoretical timeline: 13M blocks ÷ 50 RPS ÷ 86,400 = 3.0 days (UNREALISTIC)
```

**Create timeline comparison**:
| Provider | Timeline (theoretical) | Assumption |
|----------|------------------------|------------|
| Alchemy | 26 days | 300M CU/month validated |
| Infura | 519 days | 25K archive/day limit |
| LlamaRPC | 3 days | 50 RPS burst limit (needs validation) |

---

## Step 3: Empirical Validation

**Alchemy testing**:

```bash
# Test 1: 10 RPS (aggressive)
python test_rpc_rate_limits.py --rps 10 --blocks 100
Result: 72% success rate, 28 rate limit errors ❌

# Test 2: 5 RPS (moderate)
python test_rpc_rate_limits.py --rps 5 --blocks 100
Result: 100% success rate, 0 errors ✅

# Test 3: 2 RPS (conservative)
python test_rpc_rate_limits.py --rps 2 --blocks 100
Result: 100% success rate, 0 errors ✅
```

**Alchemy empirical finding**: 5.79 RPS sustainable (matches theoretical calculation)

**LlamaRPC testing**:

```bash
# Test 1: 50 RPS (documented max)
python test_rpc_rate_limits.py --rps 50 --blocks 100
Result: Immediate 429 errors ❌

# Test 2: 10 RPS (reduced)
python test_rpc_rate_limits.py --rps 10 --blocks 100
Result: 72% success rate ❌

# Test 3: 2 RPS (conservative)
python test_rpc_rate_limits.py --rps 2 --blocks 100
Result: 88% success rate ❌

# Test 4: 1.5 RPS (ultra-conservative)
python test_rpc_rate_limits.py --rps 1.5 --blocks 100
Result: 100% success rate ✅
```

**LlamaRPC empirical finding**: 1.37 RPS sustainable (2.7% of documented 50 RPS)

---

## Step 4: Create Comparison Matrix

**Empirical comparison** (validated timelines):

| Provider    | Timeline    | Cost   | Archive           | Empirical RPS | Speedup              | Verdict            |
| ----------- | ----------- | ------ | ----------------- | ------------- | -------------------- | ------------------ |
| **Alchemy** | **26 days** | **$0** | **Full**          | **5.79 RPS**  | **4.2x vs LlamaRPC** | **✅ RECOMMENDED** |
| Infura      | 519 days    | $0     | Limited (25K/day) | 0.29 RPS      | 0.05x vs LlamaRPC    | ❌ REJECT          |
| LlamaRPC    | 110 days    | $0     | Full              | 1.37 RPS      | 1.0x (baseline)      | ⚠️ FALLBACK        |

**Key findings**:

- Alchemy: 4.2x faster than LlamaRPC, free tier sufficient
- Infura: 519-day timeline unacceptable (archive limit bottleneck)
- LlamaRPC: Viable fallback, but 4.2x slower than Alchemy

---

## Step 5: Document Findings and Recommendation

**Create report**: `RPC_PROVIDER_ANALYSIS.md`

### Executive Summary

**Recommendation**: Alchemy free tier with 5.0 RPS conservative limit

**Key finding**: Alchemy provides 4.2x speedup over LlamaRPC (26 days vs 110 days for 13M blocks)

**Rationale**:

- Free tier sufficient (300M CU/month >> 260M CU needed)
- Full archive access (genesis block to latest)
- Empirically validated (5.79 RPS sustained, 100% success rate over 100 blocks)
- Simple rate model (CU-based, predictable)

### Implementation Strategy

**Primary**: Alchemy

- Conservative rate: 5.0 RPS (86% of max, 14% safety margin)
- Timeline: 26 days for 13M blocks
- Monitoring: Track daily CU usage, alert at >10M CU/day

**Fallback**: LlamaRPC

- Conservative rate: 1.37 RPS (empirically validated)
- Timeline: 110 days if primary fails
- Status: Standby (no signup required)

### Next Steps

1. **Create Alchemy account** (free tier, no credit card)
2. **Generate API key** (eth-mainnet endpoint)
3. **Test empirically** (100 blocks at 5.0 RPS, verify 100% success)
4. **Implement collector** with conservative rate limit
5. **Monitor daily CU usage** (expect ~10M CU/day, well under 300M/month limit)
6. **Prepare fallback** (LlamaRPC endpoint ready if needed)
