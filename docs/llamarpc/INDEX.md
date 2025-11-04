---
version: "1.0.0"
last_updated: "2025-11-03"
research_date: "2025-11-03"
supersedes: []
---

# LlamaRPC Ethereum Network Metrics Research

Comprehensive research on LlamaRPC as a free Ethereum RPC provider for collecting network metrics (gas prices, block data, transaction counts) with high granularity going back to 2015.

## Executive Summary

**Finding**: LlamaRPC provides **free archive access** to full Ethereum history (2015+) at block-level granularity (~12 seconds), with no authentication required.

**Primary Use Case**: Ethereum network metrics collection (gas prices, block utilization, transaction counts, base fees)

**Recommendation**: ✅ Suitable for prototyping and research; ⚠️ Strict rate limits make it less suitable for production bulk historical ingestion

## Quick Access by Research Area

### Official Documentation & Capabilities

**Location**: [`/Users/terryli/eon/gapless-network-data/docs/llamarpc/official/`](/Users/terryli/eon/gapless-network-data/docs/llamarpc/official/)

**Key Findings**:

- Provider: LlamaCorp (DefiLlama ecosystem)
- Supported Chains: Ethereum, Base, BNB Chain, Polygon
- Rate Limit: 50 RPS documented (~30-35 RPS observed)
- Archive Access: ✅ Full (2015+) on free tier
- Authentication: ❌ None required
- Pricing: Free tier + premium ($0.04 per 100K requests)

**Quick Start**: [`/Users/terryli/eon/gapless-network-data/docs/llamarpc/official/README.md`](/Users/terryli/eon/gapless-network-data/docs/llamarpc/official/README.md)

### Python SDK Recommendations

**Location**: [`/Users/terryli/eon/gapless-network-data/docs/llamarpc/sdk/`](/Users/terryli/eon/gapless-network-data/docs/llamarpc/sdk/)

**Recommendation**: **web3.py** (industry standard, Ethereum Foundation maintained)

**Alternatives Tested**:

- ✅ web3.py: Recommended (excellent LlamaRPC compatibility)
- ⚠️ pythereum: WebSocket-only (LlamaRPC HTTP preferred)
- ✅ httpx: Minimal alternative (manual hex encoding required)

**Quick Start**: [`/Users/terryli/eon/gapless-network-data/docs/llamarpc/sdk/QUICK_REFERENCE.md`](/Users/terryli/eon/gapless-network-data/docs/llamarpc/sdk/QUICK_REFERENCE.md)

### Ethereum Block Data Schema

**Location**: [`/Users/terryli/eon/gapless-network-data/docs/llamarpc/schema/`](/Users/terryli/eon/gapless-network-data/docs/llamarpc/schema/)

**Schema Coverage**:

- Block fields: 26 total (gasUsed, baseFeePerGas, timestamp, transactions, etc.)
- Transaction fields: 24 total (type, maxFeePerGas, maxPriorityFeePerGas, etc.)
- Fee history: 6 fields (baseFeePerGas, gasUsedRatio, reward percentiles)

**Derivable Metrics**: 20+ network metrics (gas utilization, base fee trends, congestion classification, recommended gas prices)

**Quick Start**: [`/Users/terryli/eon/gapless-network-data/docs/llamarpc/schema/QUICK_REFERENCE.md`](/Users/terryli/eon/gapless-network-data/docs/llamarpc/schema/QUICK_REFERENCE.md)

### Historical Data Access Patterns

**Location**: [`/Users/terryli/eon/gapless-network-data/docs/llamarpc/historical/`](/Users/terryli/eon/gapless-network-data/docs/llamarpc/historical/)

**Key Findings**:

- Historical Depth: ✅ Genesis block (2015) verified
- Optimal Batch Size: 20 blocks per request
- Rate Limit: Very strict (~15 blocks/sec sustained, 1s delay between batches)
- Performance: 1M blocks = ~18.5 hours

**Recommendation**: For production bulk ingestion, use Alchemy/Infura instead (more generous rate limits)

**Quick Start**: [`/Users/terryli/eon/gapless-network-data/docs/llamarpc/historical/README.md`](/Users/terryli/eon/gapless-network-data/docs/llamarpc/historical/README.md)

### Community Resources & Patterns

**Location**: [`/Users/terryli/eon/gapless-network-data/docs/llamarpc/community/`](/Users/terryli/eon/gapless-network-data/docs/llamarpc/community/)

**GitHub Projects**: 12 projects analyzed (Uniswap, DefiLlama, ethereum-rpc-mpc)

**RPC Providers Compared**: 10 providers (QuickNode, Chainstack, Alchemy, Infura, bloXroute, LlamaRPC, etc.)

**Collector Patterns**: 5 major projects analyzed (Flashbots mempool-dumpster, ethereum-etl, ChainStorage, etc.)

**Quick Start**: [`/Users/terryli/eon/gapless-network-data/docs/llamarpc/community/QUICK_REFERENCE.md`](/Users/terryli/eon/gapless-network-data/docs/llamarpc/community/QUICK_REFERENCE.md)

## Getting Started

### Test LlamaRPC (No Authentication Required)

```bash
# Get latest Ethereum block
curl -X POST https://eth.llamarpc.com \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# Get block details
curl -X POST https://eth.llamarpc.com \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x1",false],"id":1}'
```

### Python with web3.py

```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://eth.llamarpc.com'))

# Get latest block
latest = w3.eth.block_number
print(f"Latest block: {latest}")

# Get block data
block = w3.eth.get_block(15000000)
print(f"Gas used: {block['gasUsed']}")
print(f"Base fee: {block['baseFeePerGas'] / 1e9:.2f} gwei")
```

## Key Capabilities

### What LlamaRPC Provides

✅ **Free archive access** - Full Ethereum history from 2015 genesis
✅ **Block-level data** - ~12 second granularity (5x more granular than M1)
✅ **No authentication** - No signup, no API keys required
✅ **Standard JSON-RPC** - All eth\_\* methods supported
✅ **Batch requests** - Up to 20 blocks per batch
✅ **Multi-chain** - Ethereum, Base, BNB Chain, Polygon

### What LlamaRPC Does NOT Provide

❌ **Generous rate limits** - ~30-35 RPS burst, ~15 blocks/sec sustained
❌ **Debug/trace methods** - Premium only (debug_traceTransaction, etc.)
❌ **Unrestricted bulk fetching** - Strict rate limits for large historical ingestion

## Comparison with Bitcoin mempool.space

This research focused on **Ethereum network metrics via LlamaRPC**, but gapless-network-data targets **Bitcoin mempool metrics via mempool.space**:

| Aspect      | LlamaRPC (Ethereum)        | mempool.space (Bitcoin)     |
| ----------- | -------------------------- | --------------------------- |
| Data Type   | Block-level gas/tx metrics | Mempool pressure metrics    |
| Granularity | ~12 seconds (block)        | 1 minute (snapshots)        |
| Historical  | 2015+ (genesis)            | 2016+ (M5 recent / H12 old) |
| Rate Limit  | 30-35 RPS                  | 10 req/sec                  |
| Auth        | None                       | None                        |
| Best For    | Ethereum network metrics   | Bitcoin fee estimation      |

**Conclusion**: Both are valuable for network metrics, but serve different ecosystems. The research patterns (collector architecture, validation pipeline, metric calculations) apply to both.

## Applicability to gapless-network-data

### Directly Applicable Patterns

1. **Collector Architecture** (from Flashbots mempool-dumpster):
   - Collector-Merger pattern
   - Time-based sharding (hourly files)
   - Post-collection deduplication
   - Parquet + CSV dual format

2. **Retry Logic**:
   - Exponential backoff with jitter
   - Max 3 retries per request
   - Circuit breaker on persistent failures
   - Multi-endpoint fallback

3. **Metric Calculations**:
   - Fee trend analysis: `(current - baseline) / baseline`
   - Congestion classification: threshold-based on utilization
   - Percentile-based recommendations
   - Z-score anomaly detection

4. **Validation Pipeline**:
   - Schema validation (Pydantic)
   - Sanity checks (fee ordering, utilization bounds)
   - Gap detection (missing intervals)
   - Anomaly detection (spikes, outliers)

### Ethereum-Specific (Not Applicable)

❌ web3.py library - Ethereum-specific, not applicable to Bitcoin mempool REST API
❌ JSON-RPC 2.0 protocol - mempool.space uses REST, not JSON-RPC
❌ Hex encoding/decoding - mempool.space returns decimal values
❌ Block-level data model - Bitcoin uses mempool snapshots

## Next Steps

1. **Research mempool.space API** - Empirically test Bitcoin mempool API schema
2. **Design Bitcoin collector** - Adapt patterns from LlamaRPC research
3. **Implement retry logic** - Use exponential backoff from community findings
4. **Build validation pipeline** - Apply 5-layer validation from referential implementation
5. **Create metric calculators** - Adapt fee trend and congestion analysis

## Research Artifacts

Total: **52 files** across 5 research areas

- **Official**: 9 files (59KB) - Documentation, pricing, method reference
- **SDK**: 10 files (34KB) - Library comparison, working examples
- **Schema**: 14 files (718KB) - Complete schemas, metric calculations, sample data
- **Historical**: 11 files (68KB) - Performance testing, bulk fetching strategies
- **Community**: 8 files (92KB) - GitHub projects, RPC comparison, collector patterns

## Version History

- **v1.0.0** (2025-11-03): Initial LlamaRPC research completion
  - 5 parallel research agents deployed
  - 52 files generated across 5 perspectives
  - Coverage: Official docs, Python SDKs, data schema, historical access, community resources
  - Result: LlamaRPC confirmed as viable free option for Ethereum network metrics with caveats on rate limits
