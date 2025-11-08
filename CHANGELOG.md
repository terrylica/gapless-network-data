# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### In Progress (v0.2.0 - Historical Data Collection)

**Phase 1: 5-Year Historical Backfill (2020-2025)**

**Ethereum Historical Backfill (PRIMARY)**:

- LlamaRPC integration with archive node access (web3.py)
- 5-year Ethereum block collection (~13M blocks, 2020-2025)
- Batch fetching with checkpoint/resume capability
- Block number resolution (timestamp → block number via binary search)
- Progress tracking UI (CLI with ETA, blocks/sec)
- DuckDB storage: ethereum_blocks table (~500 MB)

**Bitcoin Historical Collection (SECONDARY)**:

- mempool.space historical API integration
- 5-year Bitcoin mempool data (H12 granularity, 3,650 snapshots)
- DuckDB storage: bitcoin_mempool table (~5 MB)

**Multi-Chain Architecture**:

- Multi-chain API: fetch_snapshots(chain='ethereum'|'bitcoin', mode='historical')
- Single DuckDB database: data.duckdb with separate tables per chain
- Chain-specific collectors with dispatch logic

**Data Quality**:

- Basic validation (Layer 1-2: RPC/HTTP + schema validation)
- DuckDB CHECK constraints (fee ordering, non-negative values)
- Retry & error handling (exponential backoff, skip failed blocks)

**Testing & Documentation**:

- 70%+ test coverage for both Ethereum and Bitcoin collectors
- Integration tests (10 blocks Ethereum, 100 snapshots Bitcoin)
- Schema documentation (duckdb-schema-specification.yaml)
- Updated DATA_FORMAT.md with DuckDB tables

**Timeline**: 3-4 weeks development + 7 days machine runtime (150 hours for Ethereum at 1 req/sec)

### Deferred to Phase 2+

- Forward-only collection (real-time block/mempool streaming)
- Complete 5-layer validation pipeline (Layers 3-5: sanity, gaps, anomalies)
- Gap detection for real-time mode
- ETag caching for mempool.space API
- Multi-chain expansion (Solana, Avalanche, Polygon)

## [0.1.0] - 2025-11-04

### Added

- Initial package structure with PEP 561 compliance (`py.typed` marker)
- API interface: `fetch_snapshots()` and `get_latest_snapshot()` functions
- Bitcoin mempool.space collector (forward-collection only)
- Structured exceptions: `MempoolHTTPException`, `MempoolValidationException`, `MempoolRateLimitException`
- Retry logic with exponential backoff (tenacity library, max 3 retries)
- LlamaRPC research documentation (52 files, comprehensive Ethereum RPC analysis)
- DuckDB investigation (23 features identified, 110x storage savings, 10-100x query speedups)
- Documentation audit (6 findings resolved)
- Master project roadmap (6-phase feature-driven planning)
- web3.py dependency for Ethereum RPC integration
- Multi-chain package structure (renamed from gapless-mempool-data)

### Known Limitations

- Forward-collection only (no historical backfill yet)
- Bitcoin collection only (Ethereum collector pending Phase 1 implementation)
- Validation pipeline incomplete (2/5 layers implemented: HTTP and basic schema)
- No gap detection or anomaly detection yet
- No ETag caching for API bandwidth optimization
- No CLI implementation (entry point exists but commands pending)
- Test coverage minimal (SDK entry points only, core engines pending)

### Documentation

- Project memory: CLAUDE.md with complete architectural context
- Single Source of Truth: master-project-roadmap.yaml (6 phases, feature-driven)
- Research completed: Ethereum LlamaRPC (PRIMARY), Bitcoin mempool.space (SECONDARY)
- Data scope defined: On-chain network metrics only (NOT exchange OHLCV)
- Referential implementation: Follows gapless-crypto-data patterns

### Changed

- Renamed project from "gapless-mempool-data" to "gapless-network-data" (2025-11-04)
- Shifted focus from Bitcoin-centric to Ethereum PRIMARY + Bitcoin SECONDARY
- Reorganized roadmap from architecture-driven to feature-driven
- Package name: `gapless_mempool_data` → `gapless_network_data`

### Migration Notes

- Fresh git repository initialized with clean history
- All file references updated (Python imports, YAML, Markdown)
- GitHub repository: https://github.com/terrylica/gapless-network-data

---

## Version History

- **v0.1.0** (2025-11-04): Foundation phase complete, ready for Phase 1 (Basic Collection)
- **Next: v0.2.0**: Ethereum + Bitcoin data collection operational
- **Target: v1.0.0**: Production release with full validation pipeline, multi-chain support
