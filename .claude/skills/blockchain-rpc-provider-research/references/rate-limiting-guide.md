# Rate Limiting Best Practices

When implementing the selected RPC provider, follow these best practices for rate limiting, monitoring, and fallback strategies.

---

## Conservative Rate Targeting

**Guideline**: Use 80-90% of empirically validated sustainable rate

**Rationale**: Leaves room for retries, daily fluctuations, and unexpected spikes

**Example**:
```
Empirical sustainable rate: 5.79 RPS
Conservative target: 5.0 RPS (86% of max)
Safety margin: 14%
```

**Why this matters**:
- Network conditions vary throughout the day
- Retries consume additional rate limit quota
- Burst traffic from parallel operations can trigger throttling
- Provider limits may change without notice

---

## Monitoring Requirements

**Track daily usage**:
- RPS (requests per second) - measure actual vs target
- CU (compute units) - track daily consumption vs monthly quota
- API credits - monitor credit burn rate

**Alert thresholds**:
- Approaching daily limits: Alert at 80% of daily quota
- Approaching monthly limits: Alert at >10M CU/day for 300M/month limit
- Success rate degradation: Alert if success rate drops below 99%
- Rate limit errors: Alert on any 429 (rate limit) responses

**Logging requirements**:
- Log failed requests for retry queue
- Track error types (429, 5xx, timeout, connection errors)
- Monitor response times (detect degradation before hard limits)
- Record daily/hourly RPS for capacity planning

**Example monitoring dashboard**:
```
Daily Usage:
  - Requests: 450,000 / 500,000 (90% ⚠️)
  - Success rate: 99.8% ✅
  - Avg response time: 245ms ✅
  - 429 errors: 0 ✅
  - 5xx errors: 12 (0.003%) ✅

Monthly Quota:
  - Compute units: 285M / 300M (95% ⚠️)
  - Estimated days remaining: 2 days
```

---

## Fallback Strategy

**Always have a validated fallback provider** to ensure collection continues if primary fails.

**Example configuration**:
```
Primary: Alchemy
  - Rate: 5.0 RPS (conservative)
  - Timeline: 26 days for 13M blocks
  - Status: Active

Fallback: LlamaRPC
  - Rate: 1.37 RPS (empirically validated)
  - Timeline: 110 days for 13M blocks
  - Status: Standby
```

**Failover triggers**:
- Primary provider sustained 429 errors (>5% failure rate)
- Primary provider downtime (>5 minutes of 5xx errors)
- Monthly quota exhausted
- API key revoked or rate limit changes

**Failover process**:
1. Detect primary failure condition
2. Log failover event with reason
3. Switch to fallback provider endpoint
4. Adjust rate limit to fallback sustainable rate
5. Update timeline estimates
6. Alert team of extended timeline

**Timeline impact**:
```
Primary failure at 50% completion (6.5M blocks collected):
  - Remaining blocks: 6.5M
  - Fallback rate: 1.37 RPS
  - Extended timeline: +55 days
  - Total timeline: 13 days (primary) + 55 days (fallback) = 68 days
```

**Cost of no fallback**: Collection halts, manual intervention required, potential data gaps.
