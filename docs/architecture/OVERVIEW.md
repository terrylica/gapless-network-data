---
version: "0.1.0"
last_updated: "2025-11-04"
supersedes: []
status: "pending"
---

# Architecture Overview

**Status**: 🚧 Pending Phase 1 implementation

This document will provide a comprehensive overview of the gapless-network-data architecture, including:

## Planned Content

### Core Components
- Data collectors (Ethereum via web3.py + LlamaRPC, Bitcoin via httpx + mempool.space)
- Validation pipeline (5 layers: HTTP/RPC, Schema, Sanity, Gaps, Anomalies)
- Storage layer (Parquet for data, DuckDB for queries)
- API interface (fetch_snapshots, get_latest_snapshot)
- CLI interface (collect, stream, validate commands)

### Data Flow
- Collection → Validation → Storage → Query → Analysis
- Multi-chain data streams (Ethereum 12s blocks, Bitcoin 5min snapshots)
- Temporal alignment with OHLCV data from gapless-crypto-data
- Gap detection and automated backfill recovery

### Service Level Objectives (SLOs)
- **Correctness**: 100% gap detection, validation accuracy
- **Observability**: DuckDB validation reports, logging, metrics
- **Maintainability**: Type safety (PEP 561), test coverage (70%+), documentation

**Note**: Performance and security are explicitly excluded per gapless-crypto-data convention.

## Current Context

Until this document is completed, refer to:

- [CLAUDE.md](/Users/terryli/eon/gapless-network-data/CLAUDE.md) - Complete architectural context
- [master-project-roadmap.yaml](/Users/terryli/eon/gapless-network-data/specifications/master-project-roadmap.yaml) - Implementation plan
- [duckdb-integration-strategy.yaml](/Users/terryli/eon/gapless-network-data/specifications/duckdb-integration-strategy.yaml) - Query engine architecture

## Key Architectural Decisions

### 1. DuckDB for Queries, Parquet for Data
- **Rationale**: 110x storage savings, 10-100x query speedups
- **Implementation**: DuckDB reads Parquet directly, no persistent tables
- **Benefits**: Zero storage duplication, SQL analytics, ASOF JOIN support

### 2. Separate Packages for OHLCV vs Network Data
- **Rationale**: Incompatible data models (11-column OHLCV vs variable network schemas)
- **Implementation**: gapless-crypto-data (OHLCV) + gapless-network-data (network metrics)
- **Integration**: Temporal alignment via DatetimeIndex + forward-fill

### 3. Ethereum PRIMARY, Bitcoin SECONDARY
- **Rationale**: Ethereum provides TRUE high-frequency data (12s blocks), Bitcoin only M5 (5min)
- **Implementation**: Ethereum collector using web3.py, Bitcoin using httpx
- **Priority**: Phase 1 focuses on Ethereum first (6-8 hours), then Bitcoin (4-6 hours)

### 4. Exception-Only Failures
- **Rationale**: No silent errors, no default values (follows gapless-crypto-data pattern)
- **Implementation**: Structured exceptions (MempoolHTTPException, MempoolValidationException)
- **Benefits**: Machine-parseable errors, explicit failure modes

### 5. Forward-Collection Only (v0.1.0 Limitation)
- **Rationale**: Focus on proving collection works before adding backfill complexity
- **Implementation**: Current API only supports recent data collection
- **Future**: Historical backfill planned for Phase 2 (Data Quality)

---

**Related Documentation**:
- [Data Format Specification](/Users/terryli/eon/gapless-network-data/docs/architecture/DATA_FORMAT.md) - Multi-chain schemas
- [Cross-Package Integration](/Users/terryli/eon/gapless-crypto-data/docs/architecture/cross-package-feature-integration.yaml) - OHLCV + network data fusion

**This document will be completed during Phase 1 implementation.**
