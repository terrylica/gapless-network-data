---
version: "1.0.0"
last_updated: "2025-11-04"
supersedes: []
---

# Gapless Network Data Documentation

Hub-and-spoke documentation architecture for multi-chain blockchain network metrics collection.

**Architecture**: Link Farm + Hub-and-Spoke with Progressive Disclosure

**Current Version**: v0.1.0 (alpha - foundation complete, Phase 1 planned)

**Next Milestone**: v0.2.0 (Ethereum PRIMARY + Bitcoin SECONDARY collection operational)

---

## Quick Navigation

### Research & Data Sources ✅ COMPLETE

- [Research Index](/docs/research/INDEX.md) - Free on-chain network metrics sources (2025-11-03)
- [LlamaRPC Deep Dive](/docs/llamarpc/INDEX.md) - Comprehensive Ethereum RPC research (PRIMARY source, 27 files, 10,546 lines)
- [Bitcoin Research](/docs/research/bitcoin/COMPREHENSIVE_FINDINGS.md) - mempool.space findings (SECONDARY source)
- [Ethereum Research](/docs/research/ethereum/SUMMARY.md) - LlamaRPC validation
- [Alt-L1 Research](/docs/research/alt-l1/EXECUTIVE_SUMMARY.md) - Solana, Avalanche, Polygon expansion targets
- [DeFi Research](/docs/research/defi/FINDINGS_SUMMARY.md) - Protocol-level network metrics

**Status**: Research phase complete. All data source investigations finished.

---

### Architecture 🚧 PHASE 1 (Pending)

- [Architecture Overview](./architecture/README.md) - Core components, data flow, SLOs
- [Data Format Specification](/docs/architecture/DATA_FORMAT.md) - Multi-chain schemas (Ethereum 6 fields, Bitcoin 9 fields)

**Status**: Documentation pending Phase 1 implementation. See [CLAUDE.md](/CLAUDE.md) for current architectural context.

---

### Usage Guides 🚧 PHASE 1 (Pending)

- [Data Collection Guide](/docs/guides/DATA_COLLECTION.md) - CLI usage, collection modes
- [Python API Reference](/docs/guides/python-api.md) - `fetch_snapshots()`, `get_latest_snapshot()`
- [Feature Engineering Guide](/docs/guides/FEATURE_ENGINEERING.md) - Temporal alignment, cross-domain features

**Status**: Documentation pending Phase 1 implementation. See [README.md](/README.md) for quick start examples.

---

### Validation System 🚧 PHASE 2 (Pending)

- [Validation Overview](/docs/validation/OVERVIEW.md) - 5-layer validation pipeline (HTTP/RPC, Schema, Sanity, Gaps, Anomalies)
- [ValidationStorage Specification](/docs/validation/STORAGE.md) - Parquet-backed validation reports

**Status**: Documentation pending Phase 2 (Data Quality) implementation.

---

### Development 🚧 PHASE 6 (Pending)

- [Development Setup](/docs/development/SETUP.md) - Environment setup with uv
- [Development Commands](/docs/development/COMMANDS.md) - Testing, linting, type checking
- [Publishing Guide](/docs/development/PUBLISHING.md) - PyPI trusted publishing workflow

**Status**: Documentation pending Phase 6 (Release) implementation.

---

## Specifications (Machine-Readable) ✅ COMPLETE

### Planning & Coordination

- [Master Project Roadmap](/specifications/master-project-roadmap.yaml) - **SSoT for project planning** (6 phases, feature-driven)
- [Core Collection Phase 1](/specifications/core-collection-phase1.yaml) - Ethereum + Bitcoin implementation spec

### Architecture & Strategy

- [DuckDB Integration Strategy](/specifications/duckdb-integration-strategy.yaml) - 23 features, performance benchmarks (110x storage savings, 10-100x speedups)
- [Documentation Audit](/specifications/documentation-audit-phase.yaml) - Completed 2025-11-03, 6 findings resolved

### Cross-Package Integration

- [Cross-Package Feature Integration](/Users/terryli/eon/gapless-crypto-data/docs/architecture/cross-package-feature-integration.yaml) - How to combine network data + OHLCV data
- [Mempool Probe Adversarial Audit](/Users/terryli/eon/gapless-crypto-data/docs/audit/mempool-probe-adversarial-audit.yaml) - 22 violations preventing integration into gapless-crypto-data

**Status**: All machine-readable planning documents complete and current.

---

## Quick Reference

### Data Granularity Comparison

| Chain    | Granularity | Snapshots/Hour | Historical Depth | Status        |
| -------- | ----------- | -------------- | ---------------- | ------------- |
| Ethereum | ~12 seconds | 300 blocks     | 2015+ (Genesis)  | **PRIMARY**   |
| Bitcoin  | 5 minutes   | 12 snapshots   | 2016+            | **SECONDARY** |

### Phase Progression

**Current Phase**: Phase 0 (Foundation) - ✅ Complete

**Next Phase**: Phase 1 (Basic Collection) - 🚧 Planned

- Ethereum block data collection (6-8 hours, P0)
- Bitcoin mempool collection (4-6 hours, P1)

**Roadmap**: Collection → Quality → Features → Expansion → Production → Release

See [master-project-roadmap.yaml](/specifications/master-project-roadmap.yaml) for complete 6-phase plan.

---

## LlamaRPC Research (PRIMARY Data Source)

### Official Documentation ✅

- [Executive Summary](/docs/llamarpc/official/00-EXECUTIVE-SUMMARY.md) - Key capabilities, pricing, rate limits
- [Initial Discovery](/docs/llamarpc/official/01-initial-discovery.md) - Block-level data, 12s intervals
- [GitHub web3-proxy Analysis](/docs/llamarpc/official/02-github-web3-proxy-analysis.md) - Production RPC load balancing
- [Empirical Testing](/docs/llamarpc/official/03-empirical-testing.md) - API validation results
- [Pricing and Features](/docs/llamarpc/official/04-pricing-and-features.md) - Free tier limits
- [Supported Chains](/docs/llamarpc/official/05-supported-chains.md) - Multi-chain endpoints
- [Method Reference](/docs/llamarpc/official/06-method-reference.md) - JSON-RPC method list

### Python SDK ✅

- [SDK Research Report](/docs/llamarpc/sdk/RESEARCH_REPORT.md) - **web3.py RECOMMENDED** (39 packages, industry standard)
- [Quick Reference](/docs/llamarpc/sdk/QUICK_REFERENCE.md) - Installation, usage examples

### Data Schema ✅

- [Ethereum Block Schema](/docs/llamarpc/schema/ETHEREUM_BLOCK_SCHEMA.md) - 26 block fields, 20+ metrics
- [Metric Mapping](/docs/llamarpc/schema/METRIC_MAPPING.md) - Feature engineering guidance
- [Quick Reference](/docs/llamarpc/schema/QUICK_REFERENCE.md) - Core 6 fields for Phase 1

### Historical Data Access ✅

- [Historical README](/docs/llamarpc/historical/README.md) - Backfill strategies
- [Research Summary](/docs/llamarpc/historical/RESEARCH_SUMMARY.md) - Performance considerations

### Community Resources ✅

- [Collector Patterns](/docs/llamarpc/community/collector-patterns.md) - 24 production-ready patterns
- [RPC Provider Comparison](/docs/llamarpc/community/rpc-provider-comparison.md) - LlamaRPC vs Alchemy vs Infura
- [Warnings and Pitfalls](/docs/llamarpc/community/warnings-and-pitfalls.md) - Common mistakes
- [Tutorials and Blogs](/docs/llamarpc/community/tutorials-and-blogs.md) - Learning resources
- [GitHub Projects](/docs/llamarpc/community/github-projects-found.md) - Open-source tools
- [web3-proxy Analysis](/docs/llamarpc/community/web3-proxy-analysis.md) - Production load balancing

---

## Project Context

### Essential Files

- [CLAUDE.md](/CLAUDE.md) - **Complete project memory** (800+ lines, architectural context)
- [README.md](/README.md) - Public-facing documentation
- [CHANGELOG.md](/CHANGELOG.md) - Version history (Keep a Changelog format)
- [pyproject.toml](/pyproject.toml) - Package configuration

### Key Concepts

**Data Scope**: On-chain network metrics ONLY

- ✅ Ethereum gas prices, block data, network congestion
- ✅ Bitcoin mempool pressure, fee rates, transaction counts
- ❌ Exchange OHLCV (Binance, Coinbase, Kraken) - Use [gapless-crypto-data](https://github.com/terrylica/gapless-crypto-data) instead

**Architecture Principles**:

- **DuckDB for Queries, Parquet for Data**: 110x storage savings, 10-100x query speedups
- **Zero-Gap Guarantee**: Automated gap detection and backfill recovery
- **Feature Engineering First**: All data designed for temporal alignment with OHLCV
- **Exception-Only Failures**: No silent errors, no default values
- **PEP 561 Compliance**: Complete type safety throughout

**Referential Implementation**: Follows [gapless-crypto-data](https://github.com/terrylica/gapless-crypto-data) patterns for SDK quality, validation pipeline, documentation structure.

---

## Status Legend

- ✅ **COMPLETE**: Documentation/implementation finished
- 🚧 **PENDING**: Placeholder exists, implementation planned
- ⚠️ **BLOCKED**: Waiting on dependencies
- ❌ **NOT STARTED**: No file exists yet

---

## Version Tracking

**Current Version**: v0.1.0 (2025-11-04)

**Version History**:

- v0.1.0: Foundation phase complete (package structure, research, planning)
- v0.2.0 (planned): Basic collection operational (Ethereum + Bitcoin)
- v1.0.0 (target): Production release (full validation, multi-chain, PyPI published)

See [CHANGELOG.md](/CHANGELOG.md) for complete version history.

---

## Related Projects

- [gapless-crypto-data](https://github.com/terrylica/gapless-crypto-data) - OHLCV data collection (referential implementation)
- [mempool.space](https://mempool.space) - Bitcoin data source
- [LlamaRPC](https://llamarpc.com) - Ethereum data source
- [gapless-features](https://github.com/terrylica/gapless-features) - Feature engineering toolkit (future)

---

**Last Updated**: 2025-11-04
**Maintained By**: Terry Li (terry@eonlabs.com)
**License**: MIT
