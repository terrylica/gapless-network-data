# Production Data Sources

**Version**: 1.1.0
**Last Updated**: 2025-11-30
**Status**: Production operational (Ethereum v4.3.1), Bitcoin deferred to Phase 2+

## Overview

This document describes **production data sources** for gapless-network-data. For comprehensive research on all evaluated sources, see [Research Index](/docs/research/INDEX.md).

## Scope

**What This Package IS For**: On-chain network metrics

- Bitcoin mempool pressure (fee rates, transaction counts, mempool size)
- Ethereum gas prices (base fee, priority fee, gas used, block utilization)
- Blockchain block-level data (timestamps, transaction counts, network congestion)
- Network health metrics (TPS, block times, resource utilization)

**What This Package IS NOT For**: Exchange price data

- ❌ OHLCV candles (Open, High, Low, Close, Volume)
- ❌ Exchange order book data
- ❌ Trading pair prices from centralized exchanges (Binance, Coinbase, Kraken)
- ❌ DEX token prices (unless coupled with network metrics like gas spent)

**Rationale**: Network metrics measure blockchain health and congestion, which directly impacts transaction success rates, confirmation times, and operational costs. Price data alone does not capture these operational characteristics.

## Active Data Sources (Production)

### Ethereum (PRIMARY) - OPERATIONAL

**Status**: Production operational (v4.3.1, 23.87M blocks 2015-2025)

#### Ethereum Historical Data

**Source**: BigQuery public dataset `bigquery-public-data.crypto_ethereum.blocks`

- **Coverage**: 2015-2025 (23.87M blocks from genesis)
- **Granularity**: Block-level (~12 second intervals)
- **Cost**: $0/month (within 1 TB/month free tier, ~10 MB/query)
- **Access**: No authentication required (public dataset)
- **Integration**: PyArrow zero-copy transfer → ClickHouse Cloud

**Why Chosen**: 624x faster than RPC polling (<1 hour vs 26 days for 5 years). Empirically validated 11-column selection (97% cost savings vs full 23-column schema).

**Documentation**: See `.claude/skills/bigquery-ethereum-data-acquisition/` for column selection rationale and cost analysis.

#### Ethereum Real-Time Data

**Source**: Alchemy WebSocket API

- **Coverage**: Real-time blocks (~12 second intervals)
- **Cost**: $0/month (300M compute units/month free tier)
- **Latency**: <1 second from block creation
- **Integration**: WebSocket `eth_subscribe` → ClickHouse Cloud

**Why Chosen**: Low latency for real-time monitoring, generous free tier, reliable WebSocket stream.

**Documentation**: See `docs/architecture/README.md` for current dual-pipeline architecture with ClickHouse Cloud.

### Storage

**Database**: ClickHouse Cloud (AWS us-west-2) `ethereum_mainnet.blocks`

- **Deduplication**: Automatic via ReplacingMergeTree ORDER BY `number`
- **Cost**: $0/month (within 10 GB storage, 100 GB egress free tier)
- **Access**: SDK queries ClickHouse Cloud directly (credentials via Doppler)

**Architecture**: Dual-pipeline (BigQuery hourly + Alchemy real-time) with ReplacingMergeTree deduplication ensures no gaps, no duplicates, and <1s latency for recent blocks.

**Migration Note**: Migrated from MotherDuck to ClickHouse Cloud 2025-11-25 (trial expiration). See ADR-0013.

## Researched Sources (Not Used in Production)

### LlamaRPC (Rejected)

**Status**: Rejected after empirical testing (2025-11-05)

**Why Researched**: Public Ethereum RPC provider, no authentication required, advertised 50 RPS rate limit.

**Why Rejected**: Empirical testing revealed 1.37 RPS sustained throughput (vs 50 RPS documented). Would require 110 days for complete historical backfill (2015-2025).

**Evidence**: See `scratch/ethereum-collector-poc/ETHEREUM_COLLECTOR_POC_REPORT.md` for complete rate limit validation (5-script POC progression).

**Documentation Archived**: See `docs/archive/llamarpc-research/INDEX.md` for comprehensive Ethereum RPC research (52 files, archived 2025-11-12).

**Key Lesson**: Never trust documented rate limits—always validate empirically with POC testing.

### Bitcoin (Future Work)

**Status**: Deferred to Phase 2+ (Bitcoin is SECONDARY vs Ethereum PRIMARY)

**Planned Source**: mempool.space REST API

- **Coverage**: 2016+ (M5 granularity for recent, H12 for historical)
- **Cost**: $0/month (10 req/sec, no authentication required)
- **Granularity**: 5-minute intervals (vs Ethereum 12-second)

**Why Deferred**: Ethereum provides 12-second granularity vs Bitcoin 5-minute. Ethereum prioritized for higher frequency network metrics.

**Rationale**: Phase 1 focused on complete historical coverage for PRIMARY blockchain (Ethereum 23.8M blocks operational).

### Multi-Chain (Future Work)

**Status**: Extensible architecture, not yet implemented

**Potential Sources**:

- **Solana**: Solana RPC API (block-level, ~400ms intervals)
- **Avalanche**: Avalanche C-Chain RPC (block-level, ~2s intervals)
- **Polygon**: Polygon RPC (block-level, ~2s intervals)
- **Dune Analytics**: SQL aggregation for cross-chain analytics (free signup)

**Research**: See `docs/research/INDEX.md` for comprehensive multi-chain research (372KB, 35+ sources evaluated).

## Implementation Timeline

### Phase 1: Historical Data Collection (COMPLETED 2025-11-12)

**Goal**: Collect complete historical blockchain data (2015-2025) for Ethereum ✅

**Achieved**:

- ✅ BigQuery public dataset integration (replaced LlamaRPC due to rate limits)
- ✅ Complete Ethereum block collection (23.8M blocks loaded)
- ✅ Dual-pipeline architecture (BigQuery hourly + Alchemy real-time)
- ✅ Production monitoring (Healthchecks.io + Pushover)
- ✅ Cost optimization ($0/month, all free tiers)
- ✅ SLO compliance (Availability, Correctness, Observability, Maintainability)

### Phase 2+: Future Work

**Bitcoin Integration**:

- mempool.space historical API integration
- 5-year Bitcoin mempool data (H12 granularity, ~3,650 snapshots)
- Multi-chain API: `fetch_snapshots(chain='bitcoin')`

**Multi-Chain Expansion**:

- Solana, Avalanche, Polygon network metrics
- Cross-chain analytics via DuckDB queries

## Key Architectural Decisions

### Decision 1: BigQuery vs LlamaRPC (2025-11-10)

**Chosen**: BigQuery public dataset

**Rationale**: 624x faster (empirically validated), $0/month cost, complete history without rate limit concerns.

**Evidence**: `scratch/ethereum-collector-poc/` POC testing revealed LlamaRPC sustained 1.37 RPS (110-day timeline vs <1 hour for BigQuery).

### Decision 2: Ethereum PRIMARY, Bitcoin SECONDARY (2025-11-04)

**Chosen**: Ethereum prioritized for Phase 1

**Rationale**: 12-second granularity (vs 5-minute for Bitcoin), larger ecosystem, more ML features available from higher frequency data.

**Score**: 12s vs 5min granularity (16x higher frequency)

### Decision 3: ClickHouse Cloud Storage (2025-11-25)

**Chosen**: ClickHouse Cloud (AWS us-west-2) - migrated from MotherDuck 2025-11-25

**Rationale**: Dual-pipeline automatic deduplication via ReplacingMergeTree, no local storage setup, $0/month cost (10GB free tier), always up-to-date production data, cloud-native monitoring.

**Architecture**: Both pipelines write to same cloud table with ReplacingMergeTree ORDER BY deduplication (idempotent, no coordination required).

**Migration Note**: Migrated from MotherDuck due to trial expiration. See ADR-0013 for complete rationale.

### Decision 4: Dual-Pipeline Architecture (2025-11-09)

**Chosen**: BigQuery hourly batch + Alchemy real-time stream

**Rationale**:

- **Reliability**: Single pipeline failure doesn't stop data collection
- **Latency**: Real-time pipeline provides <1s latency for recent blocks
- **Completeness**: Batch pipeline ensures no gaps in historical data
- **Cost**: Both pipelines fit within free tiers

**Evidence**: 30-minute maintainability SLO met during VM network failure (2025-11-10).

## Related Documentation

- [Architecture Overview](/docs/architecture/README.md) - Core components, data flow, SLOs with ClickHouse Cloud
- [ClickHouse Migration ADR](/docs/architecture/decisions/2025-11-25-clickhouse-cloud-migration.md) - Migration rationale
- [Research Index](/docs/research/INDEX.md) - Comprehensive data source research (35+ sources)
- [LlamaRPC Research Archive](/docs/archive/llamarpc-research/INDEX.md) - Ethereum RPC deep dive (archived)
- [Archived: MotherDuck Pipeline](/docs/architecture/_archive/motherduck-dual-pipeline.md) - Historical reference (DEPRECATED)
