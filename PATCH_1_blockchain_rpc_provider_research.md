# Patch 1: blockchain-rpc-provider-research

**Target**: Reduce from 287 lines → ≤200 lines (-87 minimum, -30% reduction)
**Strategy**: Extract embedded content to references/, preserve navigation structure

---

## File Operations

### CREATE: references/workflow-steps.md (140 lines)

**Source**: Lines 18-157 from current SKILL.md (Steps 1-5 with details)

**Content to extract**:

- Step 1: Research Official Documentation (full section)
- Step 2: Calculate Theoretical Timeline (full section)
- Step 3: Empirical Validation with POC Testing (full section)
- Step 4: Create Comparison Matrix (full section)
- Step 5: Document Findings and Make Recommendation (full section)

**Replace in SKILL.md with**:

```markdown
## Investigation Workflow

This skill follows a 5-step workflow. Each step builds on the previous:

1. **Research Official Documentation** - Survey provider docs, pricing, archive access
2. **Calculate Theoretical Timeline** - Compute expected collection time from documented limits
3. **Empirical Validation with POC Testing** - Test actual rate limits (CRITICAL STEP)
4. **Create Comparison Matrix** - Build side-by-side provider comparison
5. **Document Findings and Make Recommendation** - Write comprehensive analysis report

**Detailed workflow**: See `references/workflow-steps.md` for complete step-by-step guide with code examples, questions to answer, and success criteria.

**Quick start**: For immediate testing, jump to Step 3 (Empirical Validation) using `scripts/test_rpc_rate_limits.py`.
```

**Savings**: 140 lines → 15 lines (**-125 lines**)

---

### CREATE: references/rate-limiting-guide.md (50 lines)

**Source**: Lines 148-165 from current SKILL.md ("Rate Limiting Best Practices")

**Content to extract**:

- Conservative rate targeting (80-90% of empirical limit)
- Monitoring requirements (track daily usage, alert thresholds)
- Fallback strategy (always have backup provider)
- Examples with calculations

**Replace in SKILL.md with**:

```markdown
## Rate Limiting Best Practices

When implementing the selected provider, use conservative targeting (80-90% of empirically validated rate) with monitoring and fallback strategy.

**Full guide**: See `references/rate-limiting-guide.md` for detailed monitoring requirements, fallback strategies, and safety margins.
```

**Savings**: 18 lines → 4 lines (**-14 lines**)

---

### CREATE: references/common-pitfalls.md (80 lines)

**Source**: Lines 168-189 from current SKILL.md ("Common Pitfalls to Avoid")

**Content to extract**:

- Pitfall 1: Trusting documented burst limits as sustained rates
- Pitfall 2: Testing with too few blocks
- Pitfall 3: Parallel fetching on free tiers
- Pitfall 4: Ignoring compute unit costs per method
- Pitfall 5: Forgetting archive access restrictions
- Each with explanation, example, and solution

**Replace in SKILL.md with**:

```markdown
## Common Pitfalls

**Critical mistakes to avoid**: Trusting documented burst limits (always validate empirically), testing with <50 blocks, parallel fetching on free tiers, ignoring compute unit costs, and forgetting archive access restrictions.

**Full guide**: See `references/common-pitfalls.md` for detailed anti-patterns with real-world examples (e.g., LlamaRPC 50 RPS → 1.37 RPS case).
```

**Savings**: 22 lines → 4 lines (**-18 lines**)

---

### CREATE: references/example-workflow.md (120 lines)

**Source**: Lines 241-273 from current SKILL.md ("Example Workflow")

**Content to extract**:

- User request: "We need to collect 13M Ethereum blocks. Which RPC provider should we use?"
- Full 5-step walkthrough with specific findings
- Step 1 - Research (search queries, findings documented)
- Step 2 - Calculate (Alchemy, Infura timeline calculations)
- Step 3 - Validate (testing progression, empirical findings)
- Step 4 - Compare (comparison matrix with verdict)
- Step 5 - Document (report structure, recommendation, next steps)

**Replace in SKILL.md with**:

```markdown
## Example Workflow

**Case study**: Selecting RPC provider for 13M Ethereum blocks → Alchemy chosen at 5.79 RPS (26 days timeline, 4.2x faster than LlamaRPC).

**Full walkthrough**: See `references/example-workflow.md` for complete step-by-step case study showing research, calculation, validation, comparison, and final recommendation.
```

**Savings**: 33 lines → 4 lines (**-29 lines**)

---

### ENHANCE: scripts/README.md

**Source**: Lines 190-220 from current SKILL.md ("Scripts" section)

**Content to extract**:

- calculate_timeline.py usage examples (RPS-based, compute unit calculations)
- test_rpc_rate_limits.py template explanation
- Configuration examples with code snippets
- Success criteria explanations

**Current scripts/README.md**: May not exist or may be minimal

**Action**: CREATE or ENHANCE `scripts/README.md` with:

````markdown
# RPC Provider Research Scripts

## calculate_timeline.py

Calculate collection timeline given rate limits.

**Usage (RPS-based)**:

```bash
python scripts/calculate_timeline.py --blocks 13000000 --rps 5.79
# Output: 26.0 days
```
````

**Usage (Compute unit calculation)**:

```bash
python scripts/calculate_timeline.py --blocks 13000000 --cu-per-month 300000000 --cu-per-request 20
# Output: 26.0 days (5.79 RPS sustained)
```

## test_rpc_rate_limits.py

Template for empirical rate limit testing. Copy and customize for each provider.

**Key configuration**:

```python
RPC_ENDPOINT = "https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY"
REQUESTS_PER_SECOND = 5.0  # Test different rates
DELAY_BETWEEN_REQUESTS = 1.0 / REQUESTS_PER_SECOND
```

**Success criteria**:

```python
assert success_rate >= 0.99  # 99%+ success
assert rate_limited_count == 0  # Zero 429 errors
```

**Testing approach**:
Start aggressive, reduce until 100% success rate over 50-100 blocks minimum.

````

**Replace in SKILL.md with**:
```markdown
## Scripts

- `calculate_timeline.py` - Calculate collection timeline from rate limits (RPS or compute units)
- `test_rpc_rate_limits.py` - Empirical rate limit testing template

**Usage guide**: See `scripts/README.md` for detailed usage examples, configuration options, and success criteria.
````

**Savings**: 31 lines → 6 lines (**-25 lines**)

---

## SKILL.md Refactored Structure (≤200 lines)

```markdown
---
name: blockchain-rpc-provider-research
description: Systematic workflow for researching and validating blockchain RPC providers. Use when evaluating RPC providers for historical data collection, rate limits, archive access, compute unit costs, or timeline estimation for large-scale blockchain data backfills.
---

# Blockchain RPC Provider Research

## Overview

This skill provides a systematic, empirically-validated workflow for researching blockchain RPC providers before committing to large-scale data collection projects. Use when selecting an RPC provider for historical blockchain data backfill, evaluating rate limits, comparing free tier options, or estimating collection timelines.

**Key principle**: Never trust documented rate limits—always validate empirically with POC testing.

## Investigation Workflow

This skill follows a 5-step workflow. Each step builds on the previous:

1. **Research Official Documentation** - Survey provider docs, pricing, archive access
2. **Calculate Theoretical Timeline** - Compute expected collection time from documented limits
3. **Empirical Validation with POC Testing** - Test actual rate limits (CRITICAL STEP)
4. **Create Comparison Matrix** - Build side-by-side provider comparison
5. **Document Findings and Make Recommendation** - Write comprehensive analysis report

**Detailed workflow**: See `references/workflow-steps.md` for complete step-by-step guide with code examples, questions to answer, and success criteria.

**Quick start**: For immediate testing, jump to Step 3 (Empirical Validation) using `scripts/test_rpc_rate_limits.py`.

## Rate Limiting Best Practices

When implementing the selected provider, use conservative targeting (80-90% of empirically validated rate) with monitoring and fallback strategy.

**Full guide**: See `references/rate-limiting-guide.md` for detailed monitoring requirements, fallback strategies, and safety margins.

## Common Pitfalls

**Critical mistakes to avoid**: Trusting documented burst limits (always validate empirically), testing with <50 blocks, parallel fetching on free tiers, ignoring compute unit costs, and forgetting archive access restrictions.

**Full guide**: See `references/common-pitfalls.md` for detailed anti-patterns with real-world examples (e.g., LlamaRPC 50 RPS → 1.37 RPS case).

## Scripts

- `calculate_timeline.py` - Calculate collection timeline from rate limits (RPS or compute units)
- `test_rpc_rate_limits.py` - Empirical rate limit testing template

**Usage guide**: See `scripts/README.md` for detailed usage examples, configuration options, and success criteria.

## References

### Workflow Documentation

- `references/workflow-steps.md` - Complete 5-step workflow with detailed guidance for each step
- `references/rate-limiting-guide.md` - Best practices for conservative rate targeting and monitoring
- `references/common-pitfalls.md` - Anti-patterns to avoid with real-world examples
- `references/example-workflow.md` - Complete case study: 13M Ethereum blocks RPC selection

### Data References

- `references/validated-providers.md` - Alchemy vs LlamaRPC vs Infura vs QuickNode empirical comparison
- `references/rpc-comparison-template.md` - Template for creating provider comparison matrices

### Scripts

- `scripts/README.md` - Complete usage guide for all scripts
- `scripts/calculate_timeline.py` - Timeline calculator (RPS and compute unit modes)
- `scripts/test_rpc_rate_limits.py` - Empirical rate limit testing template

## Example Workflow

**Case study**: Selecting RPC provider for 13M Ethereum blocks → Alchemy chosen at 5.79 RPS (26 days timeline, 4.2x faster than LlamaRPC).

**Full walkthrough**: See `references/example-workflow.md` for complete step-by-step case study showing research, calculation, validation, comparison, and final recommendation.

## When to Use This Skill

Invoke this skill when:

- Evaluating blockchain RPC providers for a new project
- Planning historical data backfill timelines
- Comparing free tier vs paid provider options
- Investigating rate limiting issues with current provider
- Estimating collection timelines for multi-million block datasets
- Validating archive node access for historical queries
- Researching compute unit or API credit costs
- Building POC before production implementation

## Related Patterns

This skill pairs well with:

- `blockchain-data-collection-validation` - For validating the complete data pipeline after provider selection
- Project scratch investigations in `scratch/ethereum-collector-poc/` and `scratch/rpc-provider-comparison/`
```

**Estimated line count**: ~185 lines ✅ COMPLIANT

---

## Summary

| Action                      | Files       | Lines Extracted | Lines Saved  |
| --------------------------- | ----------- | --------------- | ------------ |
| Extract workflow steps      | 1 new       | 140             | -125         |
| Extract rate limiting guide | 1 new       | 50              | -14          |
| Extract common pitfalls     | 1 new       | 80              | -18          |
| Extract example workflow    | 1 new       | 120             | -29          |
| Enhance scripts/README.md   | 1 enhanced  | 100             | -25          |
| **TOTAL**                   | **5 files** | **490 lines**   | **-211 net** |

**Before**: 287 lines ❌
**After**: ~185 lines ✅ (35% reduction)
**Compliance**: PASS (15 lines under limit)

---

## Verification Checklist

- [ ] All 4 new reference files created in `references/`
- [ ] `scripts/README.md` enhanced with full script documentation
- [ ] SKILL.md updated with navigation links to all references
- [ ] Line count verified: `wc -l SKILL.md` shows ≤200
- [ ] All reference links functional (no broken paths)
- [ ] Content integrity: All original information preserved in references
- [ ] Quick start still actionable (user can begin workflow immediately)
- [ ] Navigation map complete (all references linked from SKILL.md)

---

## Next Steps

1. **Execute Patch 1**: Create 5 files, update SKILL.md
2. **Verify AC1.1**: Run `wc -l SKILL.md` → expect ≤200
3. **Verify AC2.1**: Test workflow navigation (all steps accessible via references)
4. **Proceed to Patch 2**: Apply same pattern to blockchain-data-collection-validation
