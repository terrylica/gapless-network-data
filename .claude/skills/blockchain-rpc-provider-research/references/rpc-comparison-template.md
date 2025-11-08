# RPC Provider Comparison - [Project Name]

**Investigation Date**: YYYY-MM-DD
**Purpose**: [Brief description of why RPC provider research is needed]
**Requirements**: [Number of blocks, historical range, special needs]

---

## Executive Summary

**Recommended Provider**: ✅ **[Provider Name]**

**Key Finding**: [One-sentence summary, e.g., "Alchemy free tier provides 4.2x faster collection than LlamaRPC"]

| Provider       | Timeline (blocks) | Cost  | Archive Access | Status       |
|----------------|-------------------|-------|----------------|--------------|
| **Provider A** | X days            | $Y    | ✅ Full        | ✅ RECOMMENDED |
| Provider B     | X days            | $Y    | ⚠️ Limited     | ⚠️ Fallback   |
| Provider C     | X days            | $Y    | ❌ None        | ❌ REJECT     |

---

## Detailed Provider Analysis

### 1. [Provider Name] ✅ RECOMMENDED

**Official Limits**:
- [Rate limit specification]
- [Archive access specification]
- [Cost structure]

**Compute Unit / Credit Cost**:
- `[method_name]`: [X] CU/credits per request
- [Monthly/daily calculation]

**Sustainable Rate Calculation**:
```
[Show calculation steps]
Result: X.XX RPS sustained
```

**Phase 1 Timeline**:
```
[Total blocks] ÷ [RPS] = [seconds]
[seconds] ÷ 86,400 = [days]
```

**Pros**:
- ✅ [Advantage 1]
- ✅ [Advantage 2]
- ✅ [Advantage 3]

**Cons**:
- ⚠️ [Limitation 1]
- ⚠️ [Limitation 2]

**Verdict**: **[RECOMMENDED / FALLBACK / REJECT]** - [One-sentence rationale]

---

### 2. [Provider Name] ⚠️ FALLBACK

[Repeat same structure as above]

---

### 3. [Provider Name] ❌ REJECT

[Repeat same structure as above]

---

## Comparison Matrix

| Criteria               | Provider A | Provider B | Provider C |
|------------------------|------------|------------|------------|
| **Timeline**           | X days     | X days     | X days     |
| **Speedup vs Baseline**| Xx         | Xx         | Xx         |
| **Cost**               | $X         | $X         | $X         |
| **Archive Access**     | Status     | Status     | Status     |
| **Rate Model**         | Type       | Type       | Type       |
| **API Key Required**   | Yes/No     | Yes/No     | Yes/No     |
| **Complexity**         | Low/Med/High | Low/Med/High | Low/Med/High |
| **Recommendation**     | ✅ USE     | ⚠️ Fallback | ❌ Reject   |

---

## Rate Limiting Strategies

### [Provider Name] (Recommended Approach)

**Conservative Rate**: [X.X] RPS ([XX]% of sustainable [Y.Y] RPS)

```python
REQUESTS_PER_SECOND = [X.X]
DELAY_BETWEEN_REQUESTS = 1.0 / REQUESTS_PER_SECOND  # [XXX]ms

# Timeline: [Total blocks] ÷ [X.X] RPS = [X.X] days
```

**Benefits**:
- [XX]% safety margin below monthly limit
- Handles occasional failed requests (retries)
- Room for daily usage fluctuations
- Stays well within burst limit

**Monitoring**:
- Track daily usage ([metric])
- Alert if >[threshold] ([danger zone])
- Log failed requests for retry queue
- Monitor success rate (should stay >99%)

---

## Recommendations

### Immediate Actions

1. **Use [Provider Name]** for [project phase]
   - [Specific configuration]
   - [Timeline estimate]
   - [Cost estimate]

2. **Create Account**
   - Sign up at [provider URL]
   - Create API key
   - Configure endpoint ([specific endpoint])

3. **Empirical Validation**
   - Test [method] with [provider]
   - Validate [X] CU/credits per request
   - Confirm [X.X] RPS sustainable rate
   - Test [N]-block fetch with monitoring

4. **Update Implementation**
   - Modify collector to use [provider] endpoint
   - Implement [tracking metric] tracking
   - Set conservative rate limit ([X.X] RPS)
   - Add daily budget monitoring

### Alternative Scenarios

**If [primary provider] hits unexpected limits**:
- Fallback to [backup provider] (validated [X.X] RPS)
- Timeline extends to [X] days but collection continues

**If speed is critical**:
- Consider [paid option] ($X/month)
- Or run parallel collectors with multiple free tier accounts

**Long-term (Phase 2+)**:
- For real-time collection, [X.X] RPS is sufficient ([block time])
- Free tier providers work well for ongoing collection
- Historical backfill is one-time cost

---

## Next Steps

1. ✅ Document RPC provider comparison (this file)
2. ⏳ Create [provider] account and API key
3. ⏳ Test [provider] [method] in scratch POC
4. ⏳ Validate CU costs and rate limits empirically
5. ⏳ Update collector to support [provider]
6. ⏳ Update project documentation with recommendation
7. ⏳ Update timeline estimates ([old] → [new])

---

## References

- **[Provider A] Pricing**: [URL]
- **[Provider A] Documentation**: [URL]
- **[Provider B] Pricing**: [URL]
- **Comparison Article**: [URL]
- **Community Discussion**: [URL]
- **Local POC Validation**: [Path to scratch investigation]

---

## Files in This Investigation

```
[directory structure showing where artifacts live]
```
