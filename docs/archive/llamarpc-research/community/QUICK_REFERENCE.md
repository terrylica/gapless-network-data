# Quick Reference: Key Findings

**Date**: 2025-01-20
**Project**: gapless-network-data (Bitcoin mempool data collection)

---

## TL;DR

✅ **LlamaRPC is reliable** - Used by Uniswap, DefiLlama, no complaints found
✅ **mempool.space is better for Bitcoin** - Free, reliable, 10 req/sec, no auth
✅ **Use Collector-Merger pattern** - From Flashbots mempool-dumpster
✅ **Parquet + DuckDB storage** - Time-series + validation reports
✅ **Always have backup endpoints** - Universal best practice

---

## GitHub Projects Using LlamaRPC

| Project                | Significance                   |
| ---------------------- | ------------------------------ |
| Uniswap fillanthropist | Largest DEX uses it            |
| DefiLlama chainlist    | Major aggregator lists it      |
| EigenLayer audit       | Security auditors reference it |
| ethereum-rpc-mpc       | Defaults to LlamaRPC           |

**Trust Signal**: Major production projects use LlamaRPC

---

## RPC Provider Rankings (2024)

| Metric              | Winner     | Score            |
| ------------------- | ---------- | ---------------- |
| **Performance**     | QuickNode  | 86ms global avg  |
| **Free Tier**       | Chainstack | 3M req/month     |
| **Reliability**     | QuickNode  | 2 failures only  |
| **Developer Tools** | Alchemy    | 10x optimization |
| **Privacy**         | LlamaRPC   | No tracking      |

---

## Best Collector Patterns

### Collector-Merger (Flashbots mempool-dumpster)

```
Collector → Hourly CSV (no dedup)
    ↓
Merger → Daily Parquet (dedup + validate)
    ↓
Analyzer → Summary stats
```

### ethereum-etl

```
Command-based CLI
Block range processing
Batch sizing
Multiple output formats
```

### ChainStorage (Coinbase)

```
Backfill mode: Historical data
Stream mode: Real-time data
Admin utility: Gap management
```

---

## Common Pitfalls (AVOID THESE)

| Pitfall                   | Impact                  | Fix                         |
| ------------------------- | ----------------------- | --------------------------- |
| Single endpoint           | Total outage            | 3+ backups                  |
| No rate limit handling    | 429 errors              | Exponential backoff         |
| Default timeouts (30-60s) | Slow failures           | 5-10s timeouts              |
| No circuit breaker        | Hammer failing endpoint | Circuit breaker pattern     |
| Only testing happy path   | Prod failures           | Test 429, timeout, failover |
| Ignoring rate headers     | Unnecessary errors      | Check X-RateLimit-\*        |

---

## Free RPC Problems

1. **Rate Limiting** - Most common error, test thoroughly
2. **Limited Methods** - debug\_\*, eth_getLogs often unavailable
3. **Performance Variability** - "15s wallet read during gas spike"
4. **Downtime** - "Notorious for surprise outages"
5. **Scaling Costs** - Free → Paid jump: $50-225/month

---

## Recommended Implementation

### For Bitcoin Mempool Data (gapless-network-data)

**Data Source**: mempool.space REST API (free, reliable, 10 req/sec)

**Architecture**:

```python
# Collector
Poll API every 1 minute → Write hourly CSV (60 snapshots)

# Validator
Read CSV → 5-layer validation → Write Parquet + DuckDB reports

# CLI
gapless-mempool collect  # Historical backfill
gapless-mempool stream   # Real-time polling
gapless-mempool validate # Re-validate data
```

**Storage**:

```
/data/
  ├── raw/mempool_YYYYMMDD_HH.parquet  # Time-series (1 hour = 60 snapshots)
  └── validation/validation.duckdb      # Validation reports
```

**Error Handling**:

```python
# Exponential backoff with jitter
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def fetch_snapshot():
    timeout = httpx.Timeout(connect=5.0, read=10.0)  # Aggressive
    return httpx.get(url, timeout=timeout)
```

**Testing**:

```python
# Unit: Mock API responses
# Integration: Real API (rate-limited)
# Error: Test 429, timeout, network failures
```

**Deployment**:

```dockerfile
FROM python:3.12-slim
RUN pip install uv
COPY . .
RUN uv sync
CMD ["uv", "run", "gapless-mempool", "stream"]
```

---

## If Ethereum Support Added (Future)

**Recommended Endpoints**:

```python
ENDPOINTS = [
    'https://eth.llamarpc.com',        # Primary (privacy + trusted)
    'https://chainstack-endpoint.com', # Backup (3M req/month)
    'https://eth.public-rpc.com'       # Fallback (last resort)
]
```

**Why LlamaRPC Primary**:

- Used by Uniswap, DefiLlama
- Privacy-conscious (no tracking)
- No public complaints found
- Dynamic load-balancing

**Why Backups Essential**:

- Free tiers have surprise outages
- Rate limits unpredictable
- Performance varies during congestion

---

## Monitoring Checklist

**Essential Metrics**:

- [ ] Request success rate per endpoint
- [ ] Latency P50, P95, P99
- [ ] Rate limit errors (429 count)
- [ ] Timeout errors (connection, read)
- [ ] Failover frequency
- [ ] Circuit breaker state

**Alerting Thresholds**:

- Success < 95% → Warning
- Success < 90% → Critical
- P99 latency > 10s → Warning
- Rate limits > 10/hour → Warning
- All endpoints fail → Critical

---

## Next Steps (Priority Order)

1. **Implement retry logic** - Exponential backoff with jitter (tenacity)
2. **Add ETag caching** - Store Last-Modified, send If-None-Match
3. **Rate limiting** - Track req/sec, delay if exceeding 10/sec
4. **Comprehensive tests** - Unit + integration + error handling
5. **Docker deployment** - Dockerfile + docker-compose.yml

---

## Key Resources

**Bitcoin Mempool**:

- mempool.space API: https://mempool.space/docs/api/rest
- mempool.space Repo: https://github.com/mempool/mempool

**Collector Patterns**:

- Flashbots mempool-dumpster: https://github.com/flashbots/mempool-dumpster
- ethereum-etl: https://github.com/blockchain-etl/ethereum-etl

**RPC Comparison**:

- CompareNodes Benchmarks: https://www.comparenodes.com/blog/best-public-ethereum-rpc-endpoints-2024/

**LlamaRPC**:

- Homepage: https://llamanodes.com/
- web3-proxy: https://github.com/llamanodes/web3-proxy

---

## Important Context

⚠️ **gapless-network-data targets Bitcoin mempool data via mempool.space API, not Ethereum via LlamaRPC.**

- **mempool.space**: REST API, Bitcoin, free, reliable, 10 req/sec, no auth
- **LlamaRPC**: JSON-RPC, Ethereum, rate limits, requires testing

**Research Applicability**: Architectural patterns transfer, but RPC provider details (LlamaRPC, Alchemy, etc.) are NOT directly applicable to Bitcoin data collection.

---

## Research Artifacts

All files in `/tmp/llamarpc-community-research/`:

1. `github-projects-found.md` - 12 projects using LlamaRPC
2. `web3-proxy-analysis.md` - LlamaRPC infrastructure deep-dive
3. `tutorials-and-blogs.md` - Tutorials and best practices
4. `rpc-provider-comparison.md` - 10 providers compared
5. `collector-patterns.md` - Architectural patterns from 5 projects
6. `warnings-and-pitfalls.md` - Common problems and solutions
7. `RESEARCH_SUMMARY.md` - Complete 10-section summary
8. `QUICK_REFERENCE.md` - This file

---

**Status**: Research complete, ready for implementation
