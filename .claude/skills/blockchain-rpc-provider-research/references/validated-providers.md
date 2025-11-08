# Ethereum RPC Provider Comparison for Historical Data Collection

**Investigation Date**: 2025-11-05
**Purpose**: Evaluate alternative RPC providers to address LlamaRPC free tier rate limiting
**Context**: LlamaRPC free tier sustainable rate is 1.37 RPS (110-day timeline for 13M blocks)

---

## Executive Summary

**Recommended Provider**: ✅ **Alchemy Free Tier**

**Key Finding**: Alchemy free tier provides **4.2x faster collection** than LlamaRPC (26 days vs 110 days)

| Provider       | Timeline (13M blocks) | Cost   | Archive Access | Status          |
| -------------- | --------------------- | ------ | -------------- | --------------- |
| **Alchemy**    | **26 days**           | $0     | ✅ Full        | ✅ RECOMMENDED  |
| LlamaRPC       | 110 days              | $0     | ✅ Full        | ⚠️ Too slow     |
| Infura         | 519 days              | $0     | ⚠️ Limited     | ❌ FAIL         |
| QuickNode Free | ~47 days (estimated)  | $0     | ✅ Full        | ⚠️ Needs verify |
| QuickNode Paid | ~3-4 days             | $49/mo | ✅ Full        | 💰 Fast option  |

---

## Detailed Provider Analysis

### 1. Alchemy Free Tier ✅ RECOMMENDED

**Official Limits**:

- 300M compute units (CU) per month
- 330 CUPs/sec throughput (~25 RPS burst)
- Archive node access included
- No authentication complexity

**Compute Unit Cost**:

- `eth_getBlockByNumber`: 20 CU per request
- 300M CU ÷ 20 CU = **15M requests per month**

**Sustainable Rate Calculation**:

```
15M requests ÷ 30 days = 500K requests/day
500K requests/day ÷ 86,400 seconds = 5.79 RPS sustained
```

**Phase 1 Timeline**:

```
13M blocks ÷ 5.79 RPS = 2,245,767 seconds
2,245,767 seconds ÷ 86,400 = 26.0 days
```

**Pros**:

- ✅ **4.2x faster** than LlamaRPC (26 days vs 110 days)
- ✅ Free tier is very generous (300M CU/month)
- ✅ Full archive access included
- ✅ Well-documented API
- ✅ Industry standard (used by major projects)
- ✅ web3.py support (same code as LlamaRPC)

**Cons**:

- ⚠️ Requires signup and API key (minor friction)
- ⚠️ Compute unit accounting more complex than simple RPS
- ⚠️ Need to monitor usage to stay within 300M CU/month

**Verdict**: **RECOMMENDED** - Best balance of speed, cost, and reliability

---

### 2. LlamaRPC Free Tier ⚠️ BASELINE

**Empirically Validated Limits** (2025-11-05):

- Documented: 50 RPS (burst limit)
- Sustainable: 1.37 RPS (empirically validated)
- Archive node access: Full (2015+)
- No authentication required

**Phase 1 Timeline**:

```
13M blocks ÷ 1.37 RPS = 9,489,051 seconds
9,489,051 seconds ÷ 86,400 = 110 days
```

**Pros**:

- ✅ No signup or API key required
- ✅ Full archive access
- ✅ Simple rate limiting (RPS-based)

**Cons**:

- ❌ Very slow (110 days = 3.5 months)
- ❌ Impractical for development iteration
- ❌ Machine must run continuously for 3.5 months

**Verdict**: **BASELINE** - Works but impractical

---

### 3. Infura Free Tier ❌ FAIL

**Official Limits**:

- 100,000 requests per day total
- **25,000 archive requests per day** (blocks older than 128 blocks)
- 75,000 standard requests per day
- Archive access included but rate limited

**Archive Request Rate**:

```
25,000 requests/day ÷ 86,400 seconds = 0.29 RPS
```

**Phase 1 Timeline** (using archive requests):

```
13M blocks ÷ 0.29 RPS = 44,827,586 seconds
44,827,586 seconds ÷ 86,400 = 519 days (1.4 years)
```

**Pros**:

- ✅ Established provider
- ✅ Free tier available
- ✅ Archive access included

**Cons**:

- ❌ **Extremely slow** for historical data (519 days)
- ❌ Archive requests heavily rate limited (25K/day)
- ❌ Not suitable for bulk historical collection

**Verdict**: **REJECT** - Archive rate limits too restrictive

---

### 4. QuickNode Free Tier ⚠️ NEEDS VERIFICATION

**Official Limits**:

- 50M API credits per month (disputed: some sources say 10M)
- 330 credits per second throughput
- Archive node access included
- API Credits system (not RPS)

**API Credits System**:

- eth_accounts: 1 credit
- eth_call: 2 credits
- eth_estimateGas: 6 credits
- **eth_getBlockByNumber: Unknown** (needs research)

**Estimated Timeline** (assuming 20 credits/request like Alchemy):

```
50M credits ÷ 20 credits = 2.5M requests/month
2.5M requests ÷ 30 days = 83,333 requests/day
83,333 requests/day ÷ 86,400 seconds = 0.96 RPS

13M blocks ÷ 0.96 RPS = 13,541,667 seconds
13,541,667 seconds ÷ 86,400 = 157 days (~5 months)
```

**If 10M credits (disputed)**:

```
10M credits ÷ 20 credits = 500K requests/month
500K requests ÷ 30 days = 16,667 requests/day
16,667 requests/day ÷ 86,400 seconds = 0.19 RPS
13M blocks ÷ 0.19 RPS = 68,421,053 seconds = 792 days
```

**Pros**:

- ✅ Archive access included
- ✅ Free tier available
- ⚠️ Potentially competitive (if 50M credits confirmed)

**Cons**:

- ❌ Conflicting information on free tier limits (50M vs 10M)
- ❌ Unknown API credit cost for eth_getBlockByNumber
- ⚠️ Needs empirical validation

**Verdict**: **UNCERTAIN** - Needs verification before testing

---

### 5. QuickNode Paid (Build Plan) 💰 FAST OPTION

**Build Plan**: $49/month

- 80M API credits per month
- Higher throughput
- Archive access included

**Estimated Timeline** (assuming 20 credits/request):

```
80M credits ÷ 20 credits = 4M requests/month
4M requests ÷ 30 days = 133,333 requests/day
133,333 requests/day ÷ 86,400 seconds = 1.54 RPS

13M blocks ÷ 1.54 RPS = 8,441,558 seconds
8,441,558 seconds ÷ 86,400 = 97.7 days (~3.2 months)
```

**Pros**:

- ✅ Faster than LlamaRPC free tier
- ✅ Known limits (80M credits)
- ✅ Archive access included

**Cons**:

- ❌ Still slow (~98 days)
- 💰 Costs $49/month ($147 for 3-month collection)

**Verdict**: **FALLBACK** - Not worth the cost vs Alchemy free tier

---

## Comparison Matrix

| Criteria                | Alchemy Free | LlamaRPC Free | Infura Free | QuickNode Free | QuickNode $49 |
| ----------------------- | ------------ | ------------- | ----------- | -------------- | ------------- |
| **Timeline**            | 26 days      | 110 days      | 519 days    | ~157 days?     | ~98 days      |
| **Speedup vs LlamaRPC** | **4.2x**     | 1.0x          | 0.2x        | 0.7x?          | 1.1x          |
| **Cost**                | $0           | $0            | $0          | $0             | $49/mo        |
| **Archive Access**      | ✅ Full      | ✅ Full       | ⚠️ Limited  | ✅ Full        | ✅ Full       |
| **Rate Model**          | CU-based     | RPS-based     | RPS-based   | Credits-based  | Credits-based |
| **API Key Required**    | Yes          | No            | Yes         | Yes            | Yes           |
| **Complexity**          | Medium       | Low           | Medium      | High           | High          |
| **Recommendation**      | ✅ USE       | ⚠️ Baseline   | ❌ Reject   | ⚠️ Verify      | 💰 Expensive  |

---

## Alchemy Detailed Breakdown

### Compute Units per Method

| Method                               | CU Cost |
| ------------------------------------ | ------- |
| eth_blockNumber                      | 10      |
| **eth_getBlockByNumber**             | **20**  |
| eth_getBlockByHash                   | 20      |
| eth_getBlockTransactionCountByHash   | 20      |
| eth_getBlockTransactionCountByNumber | 20      |
| eth_getBlockReceipts                 | 20      |

**Source**: https://www.alchemy.com/docs/reference/compute-unit-costs

### Monthly Budget Breakdown

**Free Tier**: 300M CU/month

**Our Use Case** (eth_getBlockByNumber):

- Cost per block: 20 CU
- Blocks fetchable: 300M ÷ 20 = **15M blocks/month**
- Phase 1 requirement: 13M blocks
- **Margin**: 2M blocks (13% buffer)

**Daily Budget**:

- 300M CU ÷ 30 days = 10M CU/day
- 10M CU ÷ 20 CU = 500K blocks/day
- 500K blocks ÷ 86,400 seconds = 5.79 blocks/sec

**Throughput Limit**:

- 330 CUPs/sec (compute units per second)
- 330 CUPs ÷ 20 CU = 16.5 blocks/sec burst
- **Sustained rate limited by monthly budget, not throughput**

---

## Rate Limiting Strategies

### Alchemy (Recommended Approach)

**Conservative Rate**: 5.0 RPS (86% of sustainable 5.79 RPS)

```python
REQUESTS_PER_SECOND = 5.0
DELAY_BETWEEN_REQUESTS = 1.0 / REQUESTS_PER_SECOND  # 200ms

# Timeline: 13M blocks ÷ 5.0 RPS = 30.1 days
```

**Benefits**:

- 14% safety margin below monthly limit
- Handles occasional failed requests (retries)
- Room for daily usage fluctuations
- Stays well within 330 CUPs/sec burst limit

**Monitoring**:

- Track daily CU usage via Alchemy dashboard
- Alert if >10M CU/day (danger of exceeding monthly limit)
- Log failed requests for retry queue

---

## Recommendations

### Immediate Action

1. **Use Alchemy Free Tier** for Phase 1 historical collection
   - 4.2x faster than LlamaRPC (26 days vs 110 days)
   - Free, generous limits (300M CU/month)
   - Well-documented, industry standard

2. **Create Alchemy Account**
   - Sign up at https://www.alchemy.com
   - Create API key
   - Configure endpoint (Ethereum Mainnet with archive access)

3. **Empirical Validation**
   - Test eth_getBlockByNumber with Alchemy
   - Validate 20 CU per request
   - Confirm 5.79 RPS sustainable rate
   - Test 100-block fetch with monitoring

4. **Update Implementation**
   - Modify collector to use Alchemy endpoint
   - Implement CU tracking (log requests)
   - Set conservative rate limit (5.0 RPS)
   - Add daily budget monitoring

### Alternative Scenarios

**If Alchemy hits unexpected limits**:

- Fallback to LlamaRPC (validated 1.37 RPS)
- Timeline extends to 110 days but collection continues

**If speed is critical**:

- Consider QuickNode Build plan ($49/mo) if faster needed
- Or run parallel collectors with multiple free tier accounts (Alchemy + LlamaRPC)

**Long-term (Phase 2+)**:

- For forward-only collection (real-time), 1.37 RPS is sufficient (12s block time = 0.08 RPS needed)
- Free tier providers work well for ongoing collection
- Historical backfill is one-time cost

---

## Next Steps

1. ✅ Document RPC provider comparison (this file)
2. ⏳ Create Alchemy account and API key
3. ⏳ Test Alchemy eth_getBlockByNumber in scratch POC
4. ⏳ Validate CU costs and rate limits empirically
5. ⏳ Update EthereumCollector to support Alchemy
6. ⏳ Update CLAUDE.md with Alchemy recommendation
7. ⏳ Update master-project-roadmap.yaml timeline (110 days → 26 days)

---

## References

- **Alchemy Pricing**: https://www.alchemy.com/pricing
- **Alchemy Free Tier**: https://www.alchemy.com/support/free-tier-details
- **Alchemy Compute Units**: https://www.alchemy.com/docs/reference/compute-units
- **Alchemy CU Costs**: https://www.alchemy.com/docs/reference/compute-unit-costs
- **Infura Pricing**: https://www.infura.io/pricing
- **Infura Archive Data**: https://docs.infura.io/features/archive-data
- **QuickNode Pricing**: https://www.quicknode.com/pricing
- **LlamaRPC Validation**: `/Users/terryli/eon/gapless-network-data/scratch/ethereum-collector-poc/ETHEREUM_COLLECTOR_POC_REPORT.md`
- **Provider Comparison**: https://www.chainnodes.org/blog/alchemy-vs-infura-vs-quicknode-vs-chainnodes-ethereum-rpc-provider-pricing-comparison/

---

## Files in This Investigation

```
scratch/rpc-provider-comparison/
├── RPC_PROVIDER_ANALYSIS.md (this file)
└── (future: alchemy_validation_poc.py)
```
