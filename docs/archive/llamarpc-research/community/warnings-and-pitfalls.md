# LlamaRPC Reviews, Warnings, and Common Pitfalls

## LlamaRPC-Specific Findings

### Official Claims

- **URL**: https://llamanodes.com/
- **Reliability Promise**: "Built with performant redundancy in mind, ensuring effectively infinite scalability and no downtime"
- **Features**: Industry-leading features, crypto payments, no contracts
- **Architecture**: Dynamic load-balancing, autoscaling, globally redundant infrastructure

### Community Feedback

**Search Results**: ⚠️ **No specific complaints or downtime reports found**

**Interpretation**:

1. Service may genuinely have good reliability as claimed
2. Issues may be discussed in private Discord/Telegram channels not indexed by search
3. Relatively newer service with smaller user base
4. Any issues may use different terminology

### Trust Signals

✅ **Used by major projects**: Uniswap, DefiLlama, EigenLayer
✅ **Default in ethereum-rpc-mpc**: Phillip-Kemper's TypeScript MCP server
✅ **No public complaints**: Absence of negative reports is positive signal
✅ **Active development**: web3-proxy shows ongoing infrastructure investment

### Red Flags

⚠️ **web3-proxy marked "under construction"**: Core infrastructure still evolving
⚠️ **Limited public documentation**: Less comprehensive than Alchemy/Infura
⚠️ **No published SLAs**: Unlike major providers with explicit guarantees
⚠️ **Unknown rate limits**: Free tier limits not clearly documented

## Free Ethereum RPC Common Problems (All Providers)

### 1. Rate Limiting and Blocking

**Issue**: Rate limits and API key issues are common errors

**Real-World Evidence**:

- POKT Network: Blocked requests from probes
- Node RPC: Rejected users for too many requests
- Gateway.fm: Blocked access
- BlockEden.xyz: Rejected for excessive requests

**Impact**: Unpredictable service availability during development

**Mitigation**:

- Implement exponential backoff with jitter
- Monitor rate limit headers (X-RateLimit-Remaining, etc.)
- Use multiple endpoints with round-robin
- Cache responses aggressively

### 2. Limited Method Support

**Issue**: Free providers often don't provide logs (too expensive)

**Resource-Intensive Methods**:

- `debug_traceBlockByHash`: Multiplier of **50x** against quota
- `eth_getLogs`: Often unavailable on free tiers
- Archive queries: Limited or expensive on free tiers

**Impact**: Missing functionality for full-featured applications

**Workaround**:

- Use minimal RPC methods only
- Check provider documentation for method availability
- Test all required methods before production

### 3. Reliability and Consistency

**Issue**: Free endpoints experience downtime and inconsistency

**Recommended Pattern** (from Stack Exchange):

```python
# Use pool of URLs from different providers
RPC_POOL = [
    "https://eth.llamarpc.com",
    "https://cloudflare-eth.com",
    "https://eth.public-rpc.com",
]

# Discovery process
1. Check for dead URLs (connection timeout)
2. Compare block numbers (sync status)
3. Verify latest sync (not stale)
```

**Impact**: Single endpoint = single point of failure

**Mitigation**:

- Always have 3+ backup endpoints
- Implement health checks before requests
- Track success rate per endpoint
- Automatic failover on errors

### 4. Performance Variability

**Issue**: "Raw throughput means nothing if a single wallet read takes 15 seconds during a gas spike"

**Real-World Behavior**:

- Free tiers deprioritized during load
- Chainnodes: "Free Core Plan does not guarantee rate limits and may prioritize paid customers during extended load"
- Higher latency on shared infrastructure
- Unpredictable during network congestion

**Impact**: Inconsistent response times, especially during high demand

**Mitigation**:

- Set aggressive timeouts (5-10 seconds)
- Implement circuit breakers
- Monitor P95/P99 latencies, not just averages
- Have fallback endpoints ready

### 5. Data Encoding Issues

**Issue**: Ethereum RPC requires special encoding

**Requirements**:

- Values must be **hex-encoded**
- Must be **0x-prefixed**
- Must use **fewest possible hex digits per byte**

**Examples**:

```python
# Correct
"0x1"      # 1
"0xa"      # 10
"0xff"     # 255

# Incorrect
"1"        # Missing 0x prefix
"0x01"     # Unnecessary leading zero
"0x0a"     # Unnecessary leading zero
```

**Impact**: Subtle bugs, request rejections

**Mitigation**:

- Use web3 libraries (ethers.js, web3.py) that handle encoding
- Don't manually construct JSON-RPC requests
- Validate responses against expected format

### 6. P2P Network Misconception

**Issue**: "There is no P2P network for RPC requests"

**Reality**:

- P2P only distributes blocks and transactions to RPC nodes
- Each client needs an RPC node to communicate with
- RPC node is responsible for maintaining latest state

**Impact**: Misunderstanding of how RPC works

**Clarification**:

- RPC endpoints are HTTP/WebSocket servers
- They query local Ethereum node state
- Multiple clients share one RPC endpoint
- Rate limits are per endpoint, not per node

## Production Deployment Pitfalls

### 1. Free Tier Dependency

**Pitfall**: Building production systems on free tiers

**Reality**: "Pricing with most node providers quickly deteriorates once your project starts getting traction"

**Consequence**:

- Free → Paid jump can be $50-225/month
- Rate limits hit during traffic spikes
- Feature limitations discovered late

**Best Practice**:

- Design for paid tier from day one
- Test rate limit handling early
- Budget for RPC costs in projections

### 2. Single Endpoint Failure

**Pitfall**: Relying on single RPC endpoint

**Reality**: "Community-hosted Ethereum RPC gateways are free but notorious for rate-limits and surprise outages"

**Consequence**:

- Complete service outage when endpoint fails
- No warning before downtime
- Recovery requires code deployment

**Best Practice**:

- Always configure 3+ endpoints
- Implement automatic failover
- Monitor endpoint health continuously

### 3. Ignoring Rate Limit Headers

**Pitfall**: Not checking rate limit response headers

**Headers to Monitor**:

- `X-RateLimit-Limit`: Total requests allowed
- `X-RateLimit-Remaining`: Requests left in window
- `X-RateLimit-Reset`: When limit resets (Unix timestamp)
- `Retry-After`: Seconds to wait before retry

**Consequence**:

- Unnecessary 429 errors
- Wasted bandwidth
- IP bans on aggressive providers

**Best Practice**:

```python
response = requests.get(rpc_url, json=payload)

if response.status_code == 429:
    retry_after = int(response.headers.get('Retry-After', 60))
    time.sleep(retry_after)
    # Retry request

remaining = response.headers.get('X-RateLimit-Remaining')
if remaining and int(remaining) < 10:
    # Slow down requests
    time.sleep(1)
```

### 4. No Circuit Breaker

**Pitfall**: Continuing to hammer failing endpoint

**Consequence**:

- Wasted time on known-bad endpoints
- Cascading failures
- Slow recovery after issues

**Best Practice**:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open

    def call(self, func):
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'half-open'
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func()
            if self.state == 'half-open':
                self.state = 'closed'
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = 'open'
            raise
```

### 5. Insufficient Timeout Configuration

**Pitfall**: Using default library timeouts (often 30-60 seconds)

**Consequence**:

- Long waits for failed requests
- Poor user experience
- Resource exhaustion

**Best Practice**:

```python
import httpx

# Aggressive timeouts for public RPC
timeout = httpx.Timeout(
    connect=5.0,   # 5 seconds to establish connection
    read=10.0,     # 10 seconds to read response
    write=5.0,     # 5 seconds to send request
    pool=5.0       # 5 seconds to get connection from pool
)

client = httpx.Client(timeout=timeout)
```

### 6. No Request Deduplication

**Pitfall**: Making duplicate concurrent requests

**Example**: Multiple components requesting same block number simultaneously

**Consequence**:

- Wasted rate limit quota
- Higher latency
- Unnecessary load on RPC

**Best Practice**:

```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=128)
def get_block_with_cache(block_number, cache_time=datetime.now()):
    # cache_time rounds to minute, providing ~1min cache
    return rpc_client.get_block(block_number)

# Usage
block = get_block_with_cache(12345, datetime.now().replace(second=0, microsecond=0))
```

## Testing Pitfalls

### 1. Not Testing Rate Limits

**Pitfall**: Only testing happy path

**Consequence**: Rate limit handling broken in production

**Best Practice**:

```python
def test_rate_limit_handling():
    """Simulate 429 responses and verify retry logic"""
    with mock.patch('httpx.Client.post') as mock_post:
        mock_post.return_value.status_code = 429
        mock_post.return_value.headers = {'Retry-After': '1'}

        result = collector.fetch_with_retry()
        assert mock_post.call_count == 3  # Initial + 2 retries
```

### 2. Not Testing Failover

**Pitfall**: Assuming primary endpoint always works

**Consequence**: Unhandled failures in production

**Best Practice**:

```python
def test_endpoint_failover():
    """Verify fallback to secondary endpoint"""
    endpoints = ['http://primary', 'http://secondary']

    with mock.patch('httpx.Client.post') as mock_post:
        # Primary fails
        mock_post.side_effect = [
            httpx.ConnectTimeout("Primary down"),
            mock.Mock(status_code=200, json=lambda: {'result': 'ok'})
        ]

        result = collector.fetch_with_endpoints(endpoints)
        assert result['result'] == 'ok'
        assert mock_post.call_count == 2
```

### 3. Not Testing Real API

**Pitfall**: Only using mocks, never real endpoints

**Consequence**: Misunderstanding API behavior

**Best Practice**:

```python
@pytest.mark.integration
def test_real_llamarpc_endpoint():
    """Integration test with actual LlamaRPC (rate limited)"""
    response = httpx.post(
        'https://eth.llamarpc.com',
        json={'jsonrpc': '2.0', 'method': 'eth_blockNumber', 'params': [], 'id': 1}
    )
    assert response.status_code == 200
    assert 'result' in response.json()
```

## Monitoring Recommendations

### Essential Metrics

1. **Request success rate** per endpoint
2. **Latency percentiles** (P50, P95, P99)
3. **Rate limit errors** (429 responses)
4. **Timeout errors** (connection, read)
5. **Failover frequency** (primary → backup)
6. **Circuit breaker state** (open/closed/half-open)

### Alerting Thresholds

- Success rate < 95% → Warning
- Success rate < 90% → Critical
- P99 latency > 10s → Warning
- Rate limit errors > 10/hour → Warning
- All endpoints failing → Critical

## LlamaRPC-Specific Recommendations

### Strengths to Leverage

✅ **Privacy-conscious**: No tracking, good for sensitive applications
✅ **Crypto payments**: If you prefer crypto over credit cards
✅ **Load balancing**: Infrastructure designed for reliability
✅ **No contracts**: Easy to cancel if issues arise

### Weaknesses to Mitigate

⚠️ **Unknown rate limits**: Test thoroughly, monitor closely
⚠️ **Limited docs**: Read web3-proxy source code for insights
⚠️ **Smaller provider**: Have backup endpoints ready
⚠️ **Under development**: Expect changes, monitor changelogs

### Recommended Configuration

```python
# Primary: LlamaRPC (privacy + trust from major projects)
# Backup: Chainstack (generous free tier)
# Fallback: Public endpoint (last resort)

RPC_ENDPOINTS = [
    {
        'url': 'https://eth.llamarpc.com',
        'priority': 1,
        'timeout': 10,
        'max_retries': 2
    },
    {
        'url': 'https://chainstack-free-endpoint.com',
        'priority': 2,
        'timeout': 10,
        'max_retries': 2
    },
    {
        'url': 'https://eth.public-rpc.com',
        'priority': 3,
        'timeout': 15,
        'max_retries': 1
    }
]
```

## Key Takeaways

### For Production Use

1. ✅ **LlamaRPC appears reliable** (no complaints found, used by majors)
2. ⚠️ **Always use multiple endpoints** (universal best practice)
3. ⚠️ **Test rate limits early** (before production deployment)
4. ⚠️ **Monitor everything** (success rate, latency, errors)
5. ⚠️ **Design for paid tier** (free tiers are for testing)

### Common Mistakes to Avoid

1. ❌ Single endpoint dependency
2. ❌ Ignoring rate limit headers
3. ❌ No circuit breaker pattern
4. ❌ Default library timeouts (too long)
5. ❌ Only testing happy path
6. ❌ Assuming free tier = production-ready

### Best Practices

1. ✅ 3+ endpoints with automatic failover
2. ✅ Exponential backoff with jitter
3. ✅ Circuit breakers per endpoint
4. ✅ Aggressive timeouts (5-10s)
5. ✅ Comprehensive monitoring
6. ✅ Integration tests with real API
7. ✅ Request deduplication/caching
8. ✅ Rate limit header inspection
