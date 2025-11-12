# Free Ethereum RPC Provider Comparison (2024)

## Overview of Major Providers

### LlamaRPC/LlamaNodes

- **URL**: https://llamanodes.com/
- **Endpoint**: https://eth.llamarpc.com
- **Features**:
  - Low-cost RPC provider
  - Dynamic load-balancing, autoscaling
  - Globally redundant infrastructure
  - Intelligent caching for speed optimization
  - Privacy-conscious
  - Crypto payments accepted
  - No contracts required
- **Market Position**: Smaller specialized provider vs major players
- **Free Tier**: Not explicitly documented in search results

### Alchemy

- **Market Position**: Advanced RPC with focus on developer tools
- **Features**:
  - Real-time analytics
  - Debugging tools
  - Enhanced developer productivity
  - Advanced compute unit model
- **Free Tier**: 40 requests/minute (~0.67 RPS)
- **Paid Plans**: Start at $49/month for 5M compute units
- **Performance**: 207ms global average response time (3rd place)
- **Regional**: 115ms US average
- **Developer Tools**: 10x more computing resources for overlapping JSON-RPC calls vs QuickNode free tier

### Infura

- **Market Position**: Leading provider with extensive infrastructure
- **Features**:
  - High availability
  - Robust and scalable solutions
  - Developer-friendly tools
  - IPFS network support
- **Free Tier**: 100,000 requests/day (~1.15 RPS)
- **Paid Plans**: Start at $225/month (3M requests/day, ~34.7 RPS)
- **Performance**: 133ms US average response time
- **Reliability**: 99.9% uptime, 7 failed calls in benchmark

### QuickNode

- **Market Position**: Performance leader
- **Features**:
  - Fast and reliable services
  - User-friendly dashboard
  - Multi-blockchain support (Ethereum, BSC, Polygon)
- **Free Tier**: 100,000 requests/day (~1.15 RPS)
- **Paid Plans**: Start at $150/month (2M requests/day, ~23.15 RPS)
- **Performance**: **86ms global average** (FASTEST - 2x faster than 2nd place)
- **Regional**: 45ms US, 74ms EU, 155ms AP
- **Reliability**: 99.9% uptime, only 2 failed calls (BEST)

### Chainstack

- **Free Tier**: 3M requests/month (~25 RPS) - MOST GENEROUS
- **Description**: "Rock-solid endpoint"
- **Setup**: Zero maintenance, quick setup

### GetBlock

- **Free Tier**: 50k CU/day, 20 RPS

### Chainnodes

- **Developer Plan**: 50 RPS
- **Free Core Plan**: No guaranteed rate limits, may prioritize paid customers during load

### Ankr

- **Features**: Globally distributed network across 30+ regions
- **Archive Access**: Available
- **Performance**: 164ms global average (2nd place)
- **Regional Winner**: Best public Ethereum RPC in South America

### bloXroute

- **Performance Winner**: Best overall public Ethereum RPC on mainnet (2024)
- **Regional Winners**: Europe, Asia, Middle East, Africa

### Tenderly

- **Regional Winner**: Best public Ethereum RPC in North America

## Performance Benchmarks (2024)

### Methodology

- **Test Locations**: 27 locations across 6 continents
- **Test Method**: eth_blockNumber, max 1 req/region/second
- **Test Duration**: 15 minutes typical
- **Request Volume**: 1-5 million RPC requests per run
- **Methods Tested**: Mix of 23-25 popular RPC methods

### Rankings by Speed (Global Average)

1. **QuickNode**: 86ms (Winner)
2. **Ankr**: 164ms
3. **Alchemy**: 207ms

### Rankings by Reliability (Failed Calls)

1. **QuickNode**: 2 failures (Best)
2. **Ankr**: 3 failures
3. **Infura**: 7 failures

### Regional Performance Leaders

- **North America**: Tenderly
- **South America**: Ankr
- **Europe**: bloXroute
- **Asia**: bloXroute
- **Middle East & Africa**: bloXroute

### All Providers Hit 99.9% Uptime SLA

## Rate Limiting Details

### Compute Unit (CU) Model

- **Alchemy**: Uses CU model - different RPC calls consume different amounts
- **GetBlock**: 50k CU/day
- **Challenge**: Makes cost/rate limit predictions complex

### Request-Based Model

- **Infura**: 100k req/day free
- **QuickNode**: 100k req/day free
- **Chainstack**: 3M req/month free (MOST GENEROUS)
- **Chainnodes**: 50 RPS on developer plan

### Rate Limit Caveats

⚠️ **"Raw throughput means nothing if a single wallet read takes 15 seconds during a gas spike"**

Key insight: Advertised rate limits don't always translate to consistent performance during network congestion.

## Free Tier Comparison Summary

| Provider   | Free Tier       | RPS   | Speed (Global) | Reliability | Best For              |
| ---------- | --------------- | ----- | -------------- | ----------- | --------------------- |
| Chainstack | 3M req/month    | ~25   | Not benchm.    | High        | Generous free tier    |
| QuickNode  | 100k req/day    | ~1.15 | 86ms (BEST)    | 99.9% (2F)  | Performance           |
| Infura     | 100k req/day    | ~1.15 | 133ms US       | 99.9% (7F)  | Reliability, IPFS     |
| Alchemy    | 40 req/min      | ~0.67 | 207ms          | 99.9%       | Developer tools       |
| GetBlock   | 50k CU/day      | 20    | Not benchm.    | Unknown     | High RPS              |
| Chainnodes | Developer: 50   | 50    | Not benchm.    | Variable    | High RPS (paid prior) |
| Ankr       | Not specified   | ?     | 164ms          | 99.9% (3F)  | Global distribution   |
| LlamaRPC   | Not specified   | ?     | Not benchm.    | Unknown     | Privacy, crypto pay   |
| bloXroute  | Public endpoint | ?     | Best (regions) | Unknown     | Regional performance  |
| Tenderly   | Public endpoint | ?     | Best (NA)      | Unknown     | North America         |

**Legend**: F = Failed calls in benchmark

## Reliability Warnings

### Free Tier Limitations

⚠️ **"Community-hosted Ethereum RPC gateways are free but notorious for rate-limits and surprise outages"**

### Scaling Challenges

⚠️ **"Pricing with most node providers quickly deteriorates once your project starts getting traction"**

### Production Requirements

- Free tiers suitable for **development and testing only**
- Reliability guarantees typically require **paid plans**
- No guaranteed rate limits on many free tiers

## Best Practices from Community

### 1. Use Multiple Endpoints (Critical)

- **Backup endpoints essential** to avoid downtime
- Free tiers prioritize paid customers during load
- Single endpoint = single point of failure

### 2. Monitor Rate Limits

- Plan for 429 errors
- Implement exponential backoff
- Track usage to avoid surprises

### 3. Library Recommendations

- ✅ **Ethers.js** - Modern, actively maintained
- ✅ **Viem** - Modern, TypeScript-first
- ✅ **web3.py** - Python standard
- ❌ **Web3.js** - No longer actively maintained (deprecated)

### 4. Security

- Never commit API keys (even for free tiers)
- Use environment variables
- Whitelist IPs when possible
- Authenticate endpoints

### 5. Testing Tools

- **CompareNodes RPC Performance Inspector**: Interactive latency profiling
- **Eden Network RPC Speed Test**: Open source speed measurement
- **Custom Benchmarks**: eth_blockNumber from multiple regions

## LlamaRPC Position in Market

### Strengths

✅ Privacy-conscious (no tracking)
✅ Crypto payments accepted
✅ No contracts required
✅ Dynamic load-balancing
✅ Intelligent caching
✅ Trusted by major projects (Uniswap, DefiLlama)

### Weaknesses

⚠️ Limited public documentation vs major providers
⚠️ No performance benchmarks available
⚠️ Free tier details not clearly specified
⚠️ Smaller provider = less redundancy?

### Use Cases

- **Privacy-focused applications**: Main differentiator
- **Crypto-native projects**: Accept crypto payments
- **Testing/Development**: Used by major projects as default
- **Backup endpoint**: Trusted by production systems

## Recommendations for gapless-network-data

### Primary Choice: Chainstack

- **Reason**: 3M req/month most generous for historical backfill
- **RPS**: ~25 RPS sufficient for 1-minute interval collection
- **Reliability**: "Rock-solid" reputation
- **Cost**: Best free tier value

### Backup Choice: QuickNode

- **Reason**: Best performance (86ms) and reliability (2 failures)
- **RPS**: ~1.15 RPS sufficient for steady-state
- **Reliability**: 99.9% uptime with fewest failures

### Alternative: LlamaRPC

- **Reason**: Privacy-focused, trusted by Uniswap/DefiLlama
- **Use Case**: If privacy matters or crypto payment preferred
- **Caveat**: Less documentation, unknown rate limits

### Architecture Recommendation

```python
RPC_ENDPOINTS = [
    "https://eth.llamarpc.com",           # Primary (privacy + trusted)
    "https://chainstack.com/...",         # Backup (generous limits)
    "https://eth.public-rpc.com",         # Fallback (public)
]
```

### Implementation Pattern

1. **Round-robin with health checks**: Rotate through endpoints
2. **Exponential backoff**: On 429 errors
3. **Circuit breaker**: Skip failing endpoints
4. **Monitoring**: Track success rate per endpoint

## Key Insights

1. **No clear winner**: Each provider excels in different areas
2. **Performance != Reliability**: QuickNode fastest but check during gas spikes
3. **Free tiers are testing-only**: Production needs paid plans
4. **Multiple endpoints essential**: All free tiers have limitations
5. **LlamaRPC under-documented**: But trusted by major projects
6. **Benchmark your use case**: Synthetic benchmarks != real-world usage
