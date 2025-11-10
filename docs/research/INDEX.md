---
version: "1.0.0"
last_updated: "2025-11-03"
supersedes: []
research_date: "2025-11-03"
---

# Free High-Frequency On-Chain Data Research

> **⚠️ Research Artifact**: This documentation describes data source evaluation (2025-11-03).
> **Production uses BigQuery + Alchemy** (LlamaRPC rejected after empirical testing: 1.37 RPS sustained vs 50 RPS documented).
> See [Ethereum Collector POC Report](../../scratch/ethereum-collector-poc/ETHEREUM_COLLECTOR_POC_REPORT.md) for rate limit findings.

Comprehensive research on free data sources with M1/M5/M15+ frequency and 3+ years historical depth (2022+).

## Executive Summary

**Research Scope**: Free on-chain **network metrics** (gas prices, mempool congestion, block data, transaction counts) with M5-M15 or better granularity going back 3-5+ years.

**Finding**: Free high-granularity on-chain network data IS available going back to 2015-2022 across Bitcoin and Ethereum.

**PRIMARY DISCOVERY**: LlamaRPC Ethereum RPC (block-level ~12s, 2015+, no auth required)

**Data Type Distinction**:

- ✅ **In Scope**: Network metrics (gas prices, mempool pressure, block times, transaction counts)
- ❌ **Out of Scope**: Exchange OHLCV price data (Binance, Coinbase, Kraken) - covered by gapless-crypto-data package

## Research Coverage

| Ecosystem       | Chains Covered | M1/M5/M15    | Back to 2022 | Auth Required |
| --------------- | -------------- | ------------ | ------------ | ------------- |
| **Bitcoin**     | 1              | M5/M15       | ✅ 2009+     | ❌ No         |
| **Ethereum**    | 1              | Block (~12s) | ✅ 2015+     | ❌ No         |
| **Alt-L1**      | 8              | M1/M5/M15    | ✅ 2021+     | ❌ No         |
| **Multi-Chain** | All            | M1/M5/M15    | ✅ 2017+     | ❌ No         |
| **DEX/DeFi**    | Ethereum       | M1 (SQL)     | ✅ 2020+     | 🔑 Free key   |

## Quick Access by Ecosystem

### Bitcoin On-Chain Data

**Location**: [`/Users/terryli/eon/gapless-network-data/docs/research/bitcoin/COMPREHENSIVE_FINDINGS.md`](/Users/terryli/eon/gapless-network-data/docs/research/bitcoin/COMPREHENSIVE_FINDINGS.md)

**Top Sources**:

- mempool.space: M5 statistics (2016+, no auth)
- blockchain.info: M15 mempool/TPS (2009+, no auth)

**Quick Start**: [`/Users/terryli/eon/gapless-network-data/docs/research/bitcoin/QUICK_REFERENCE.md`](/Users/terryli/eon/gapless-network-data/docs/research/bitcoin/QUICK_REFERENCE.md)

### Ethereum On-Chain Data

**Location**: [`/Users/terryli/eon/gapless-network-data/docs/research/ethereum/FINDINGS.md`](/Users/terryli/eon/gapless-network-data/docs/research/ethereum/FINDINGS.md)

**Top Sources**:

- LlamaRPC: Block-level (~12s, 2015+, no auth)
- Alchemy: Block-level (300M CU/month free tier)
- Dune Analytics: Custom SQL aggregation (free signup)

**Quick Start**: [`/Users/terryli/eon/gapless-network-data/docs/research/ethereum/QUICKSTART.md`](/Users/terryli/eon/gapless-network-data/docs/research/ethereum/QUICKSTART.md)

### Alternative L1 Blockchains

**Location**: [`/Users/terryli/eon/gapless-network-data/docs/research/alt-l1/COMPREHENSIVE_FINDINGS.md`](/Users/terryli/eon/gapless-network-data/docs/research/alt-l1/COMPREHENSIVE_FINDINGS.md)

**Chains**: Solana, Avalanche, Cardano, Polkadot, Cosmos, Near, Algorand, Tezos

**Top Source**:

- Binance API: M1/M5/M15 OHLCV for all 8 chains (2021+, no auth)

**Quick Start**: [`/Users/terryli/eon/gapless-network-data/docs/research/alt-l1/QUICK_REFERENCE.md`](/Users/terryli/eon/gapless-network-data/docs/research/alt-l1/QUICK_REFERENCE.md)

### Multi-Chain Aggregators

**Location**: [`/Users/terryli/eon/gapless-network-data/docs/research/aggregators/RESEARCH_FINDINGS.md`](/Users/terryli/eon/gapless-network-data/docs/research/aggregators/RESEARCH_FINDINGS.md)

**Top Sources**:

- Binance API: M1/M5/M15 (3,370+ pairs, 2017+, no auth)
- Coinbase API: M1/M5/M15 (2015+, no auth)
- CryptoDataDownload: CSV archives (5+ years, no auth)

### DEX/DeFi Data

**Location**: [`/Users/terryli/eon/gapless-network-data/docs/research/defi/FINDINGS_SUMMARY.md`](/Users/terryli/eon/gapless-network-data/docs/research/defi/FINDINGS_SUMMARY.md)

**Top Sources**:

- Dune Analytics: SQL aggregation (full history, free signup)
- GeckoTerminal: M1 OHLCV (6 months, no auth)
- CryptoCompare: H1 historical (3+ years, free key)

**API Reference**: [`/Users/terryli/eon/gapless-network-data/docs/research/defi/API_ENDPOINTS_REFERENCE.md`](/Users/terryli/eon/gapless-network-data/docs/research/defi/API_ENDPOINTS_REFERENCE.md)

## Recommended Data Sources (Network Metrics)

### For Ethereum Network Metrics (PRIMARY) ⭐

**Primary**: LlamaRPC

- Frequency: Block-level (~12 seconds)
- Historical: 2015+ (Ethereum genesis)
- Rate Limit: Generous (undocumented)
- Authentication: None
- Data: Gas prices, block timestamps, transaction counts, base fee, block utilization

**Example - Get Block Data**:

```bash
curl -X POST https://eth.llamarpc.com \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x8c4991",false],"id":1}' \
  | jq '.result | {number, timestamp, gasUsed, baseFeePerGas}'
```

**Example - Get Fee History**:

```bash
curl -X POST https://eth.llamarpc.com \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_feeHistory","params":["0x64","latest",[25,50,75]],"id":1}'
```

### For Bitcoin Network Metrics

**Primary**: mempool.space API

- Frequency: M5 (1-week data), H12 (3-year data)
- Historical: 2016+
- Rate Limit: 10 req/sec
- Authentication: None

**Example**:

```bash
curl "https://mempool.space/api/v1/statistics/1w"
```

### For Ethereum Network Metrics

**Primary**: LlamaRPC

- Frequency: Block-level (~12 seconds)
- Historical: 2015+ (genesis)
- Rate Limit: Generous (undocumented)
- Authentication: None

**Example**:

```bash
curl -X POST https://eth.llamarpc.com \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["latest",false],"id":1}'
```

### For DEX/DeFi Data

**Primary**: Dune Analytics

- Frequency: Custom SQL (M1/M5/M15 via aggregation)
- Historical: Full blockchain history
- Rate Limit: 30 req/min
- Authentication: Free API key (signup required)

## Data Limitations

### What Works (Network Metrics)

✅ **Ethereum block data** (~12s) back to 2015 (LlamaRPC, Alchemy) - PRIMARY ⭐
✅ **Bitcoin mempool metrics** (M5 recent, H12 historical) back to 2016 (mempool.space)
✅ **Bitcoin mempool size** (~H29 granularity) back to 2009 (blockchain.info)
✅ **Ethereum gas history** via eth_feeHistory (last 1024 blocks)
✅ **DEX transaction data** via SQL aggregation back to 2020 (Dune Analytics)

### What Works (Price Data - Not Network Metrics)

ℹ️ OHLCV price data (M1/M5/M15) back to 2017 available from Binance/Coinbase but **out of scope** for this package (use gapless-crypto-data instead)

### What Doesn't Work

❌ **Historical mempool at M5**: Only recent data is M5, 2020 data is H12 (mempool.space)
❌ **CoinGecko free tier**: Limited to 365 days
❌ **Glassnode**: No free API access
❌ **The Graph Hosted Service**: Deprecated

## Implementation Strategy

### Phase 1: Ethereum Block-Level Collection (PRIMARY)

Use LlamaRPC to collect Ethereum blocks (~12s intervals) back to 2015

- Rate: 1 req/sec (conservative)
- Storage: Parquet with snappy compression
- Metrics: gasUsed, baseFeePerGas, timestamp, transactionCount, blockUtilization

### Phase 2: Bitcoin Mempool Collection

- Bitcoin: mempool.space for network congestion (M5 recent, H12 historical)
- Metrics: fee rates, transaction counts, mempool size, vbytes_per_second

### Phase 3: Real-Time Updates

Continuous polling at 1-5 minute intervals to maintain gapless dataset

## Research Artifacts

All test scripts, detailed findings, and API examples available in subdirectories:

- **Bitcoin**: `/Users/terryli/eon/gapless-network-data/docs/research/bitcoin/` (70KB, 15 files)
- **Ethereum**: `/Users/terryli/eon/gapless-network-data/docs/research/ethereum/` (88KB, 9 files)
- **Alt-L1**: `/Users/terryli/eon/gapless-network-data/docs/research/alt-l1/` (70KB, 32 files)
- **Aggregators**: `/Users/terryli/eon/gapless-network-data/docs/research/aggregators/` (40KB, 8 files)
- **DEX/DeFi**: `/Users/terryli/eon/gapless-network-data/docs/research/defi/` (104KB, 18 files)

**Total**: 372KB of research documentation and test scripts

## Version History

- **v1.0.0** (2025-11-03): Initial research completion
  - 5 parallel research agents deployed
  - 35+ data sources empirically tested
  - Coverage: Bitcoin, Ethereum, 8 Alt-L1s, DEX/DeFi
  - Result: Confirmed free M1/M5/M15 data available back to 2017-2022
