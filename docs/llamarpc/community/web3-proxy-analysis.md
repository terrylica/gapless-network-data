# web3-proxy Deep Dive Analysis

**Repository**: https://github.com/llamanodes/web3-proxy
**Language**: Rust
**Status**: Under active development (production use but incomplete features)

## Architecture Insights

### Load Balancing Strategy

- **Parallel transactions**: `eth_sendRawTransaction` sent to all configured private RPCs simultaneously
- **Smart routing**: Non-signed requests routed to servers on latest block
- **Prioritization**: By active request count and latency
- **Multi-module design**: Core proxy, CLI tools, supporting libraries

### Key Components

- `web3_proxy` - Core proxy logic
- `web3_proxy_cli` - Administrative tools
- `quick_cache_ttl` - TTL-based caching
- `redis-rate-limiter` - Rate limiting enforcement
- `deferred-rate-limiter` - Deferred rate limiting
- `deduped_broadcast` - Request deduplication
- `latency` - Latency tracking
- Health monitoring via CLI tools

## Rate Limiting Implementation

### Two-Tier System

1. **Soft limit**: Performance degradation threshold
2. **Hard limit**: Rate-limit error threshold

### Infrastructure

- Redis-based enforcement
- User tier management (supports unlimited tier)
- Per-server configurable limits
- CLI commands for user management

## Caching Strategies

### Multi-Layer Caching

1. **Quick cache with TTL**: Fast response serving
2. **Database persistence**: MySQL for user balances/config
3. **Request deduplication**: Avoid duplicate work
4. **InfluxDB metrics**: Performance monitoring

### Database Requirements

- MySQL with `innodb_rollback_on_timeout=1` (critical)
- InfluxDB for metrics (optional but recommended)

## Error Handling & Reliability

### Monitoring

- Health compass CLI tool for RPC endpoint comparison
- Server health tracking
- Fallback routing when servers unavailable

### Limitations

- **No detailed retry logic documented**
- Filter support incomplete ("will be added soon")
- Manual intervention needed for some operations

## Performance Optimizations

### Rust Benefits

- Memory efficiency
- High-performance async handling
- Native speed

### Testing Infrastructure

- wrk scripts for load testing
- ethspam integration
- Flame graph profiling support
- Connection pooling (implied)

## Critical Warnings

### Production Readiness

⚠️ **"Under construction! Please note that the code is currently under active development"**

### Known Issues

1. **Filter functionality incomplete** - "will be added soon"
2. **Testing gaps** - "More tests are always needed"
3. **Clustering requirement**: Must set unique `app.unique_id` per instance (defaults to 0)
4. **MySQL config**: Must set `innodb_rollback_on_timeout=1`
5. **Documentation gaps**: "Contact Discord for deployment details"

## Relevance to gapless-network-data

### Applicable Patterns

✅ **Smart routing by latency** - Could inform our RPC endpoint selection
✅ **Request deduplication** - Useful for backfill operations
✅ **Multi-layer caching** - ETag + local cache strategy
✅ **Health monitoring** - Could add RPC endpoint health checks

### Not Applicable

❌ **Load balancing** - We're a client, not a proxy
❌ **User tiers** - No multi-tenant requirements
❌ **Transaction broadcasting** - We only read, never write

### Key Takeaway

LlamaRPC infrastructure is **production-grade but actively evolving**. The project shows serious investment in reliability (Rust, caching, rate limiting) but acknowledge gaps (filters, testing, docs).

**Trust signal**: Major projects (Uniswap, DefiLlama) use it despite "under construction" status, suggesting core functionality is reliable.
