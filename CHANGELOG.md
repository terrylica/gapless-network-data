# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- Ethereum block data collection via LlamaRPC (Phase 1)
- ETag caching for mempool.space API
- 5-layer validation pipeline (HTTP/RPC, Schema, Sanity, Gaps, Anomalies)
- Gap detection and automated backfill
- DuckDB query engine integration
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
