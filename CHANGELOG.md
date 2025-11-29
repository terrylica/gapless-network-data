# [4.0.0](https://github.com/terrylica/gapless-network-data/compare/v3.1.2...v4.0.0) (2025-11-29)


### Bug Fixes

* **collector:** add graceful shutdown and buffer flush for gap prevention ([11715dd](https://github.com/terrylica/gapless-network-data/commit/11715dd5f8c26a588cb13c7d817a2b888d5112c6))
* **collector:** fetch full block data for accurate transaction_count ([ac1cec0](https://github.com/terrylica/gapless-network-data/commit/ac1cec0f83ed215f0b46cddf0d6e51791f301f96))
* **gap-detector:** migrate to ClickHouse-native queries ([a713c09](https://github.com/terrylica/gapless-network-data/commit/a713c09f25e6088634d8585e639d4bfc54ece567))
* **skills:** add YAML frontmatter to vm-infrastructure-ops and historical-backfill-execution ([dc3af41](https://github.com/terrylica/gapless-network-data/commit/dc3af41496cef7e2fa765a4b021519b3f0605d7c))
* **tests:** improve test coverage and fix package exports ([6fef94b](https://github.com/terrylica/gapless-network-data/commit/6fef94b435d495044bdb26da32f1b24e054e7cf4))
* **verify:** use max block as primary dual-write health metric ([9ed9d09](https://github.com/terrylica/gapless-network-data/commit/9ed9d09c95b4db2b56bff98432483df2c6b6fa28))


### Code Refactoring

* remove DuckDB/MotherDuck code post-ClickHouse migration ([3a93deb](https://github.com/terrylica/gapless-network-data/commit/3a93deb55bf3b1095b990181ffbb8d41528064ec))


### Features

* add probe module for AI-discoverable alpha features ([668aeb9](https://github.com/terrylica/gapless-network-data/commit/668aeb9c08a2c0c30080c68bbd9ef30343254009))
* **clickhouse:** complete Phase 2 code with Cloud Console deployment guide ([ebdef60](https://github.com/terrylica/gapless-network-data/commit/ebdef60076d06cefd27a7e28b1f166031bb0e89a))
* **clickhouse:** deploy dual-write to production ([944c9de](https://github.com/terrylica/gapless-network-data/commit/944c9dee563372853970bf0c9ca64cbce2f6741d))
* **migration:** complete ClickHouse gap backfill from MotherDuck ([20c53f1](https://github.com/terrylica/gapless-network-data/commit/20c53f14ea5980996e6c5e58426863000c521f2a))
* **migration:** implement MotherDuck to ClickHouse dual-write (MADR-0013) ([85de8ac](https://github.com/terrylica/gapless-network-data/commit/85de8ac000757cd90cdc474dcb62be9e7f098402))
* **skills:** extract VM ops and historical backfill workflows (Phase 2) ([e2bc107](https://github.com/terrylica/gapless-network-data/commit/e2bc1076274f6036532d5c225ab8da5c7ee4b500))


### BREAKING CHANGES

* DuckDB/MotherDuck integrations no longer available.
Use ClickHouse Cloud for all data operations.
* **skills:** .claude/skills/bigquery-ethereum-data-acquisition/CLAUDE.md renamed to DECISION_RATIONALE.md

- Create vm-infrastructure-ops skill (systemd, gcloud, troubleshooting)
- Create historical-backfill-execution skill (1-year chunks, memory-safe)
- Rename bigquery CLAUDE.md → DECISION_RATIONALE.md (enforces zero child CLAUDE.md)
- Update Skills Catalog (5 → 7 skills)
- Update root CLAUDE.md to reference new skills

Implements: MADR-0007 (Skills Extraction Criteria)
Related: specifications/doc-normalization-phase.yaml Phase 2 (N2-1, N2-2, N2-3)
SLO: Observability (100% discoverability via Skill tool), Maintainability (atomic skill workflows)

## [3.1.2](https://github.com/terrylica/gapless-network-data/compare/v3.1.1...v3.1.2) (2025-11-13)


### Bug Fixes

* **monitoring:** P0 critical issues - grace periods, fatal paths, timeouts ([e038b01](https://github.com/terrylica/gapless-network-data/commit/e038b0111534bb51392da889c18d0340e452ac16))

## [3.1.1](https://github.com/terrylica/gapless-network-data/compare/v3.1.0...v3.1.1) (2025-11-13)

### Bug Fixes

- **monitoring:** restore Healthchecks.io monitoring for motherduck-gap-detector ([b826013](https://github.com/terrylica/gapless-network-data/commit/b8260139a048514bba31e8e87ca47151ad3b3b7f))

# [3.1.0](https://github.com/terrylica/gapless-network-data/compare/v3.0.0...v3.1.0) (2025-11-12)

### Features

- **monitoring:** add gap analysis utility scripts ([dc21b35](https://github.com/terrylica/gapless-network-data/commit/dc21b356066fe47e13f04dce0cb4e7c92162a899))
- **monitoring:** increase staleness threshold to 960s (16 min) for batch mode compatibility ([eb8145f](https://github.com/terrylica/gapless-network-data/commit/eb8145f11e931613da4e961de4fe8e3ed3b3bd19))
- **monitoring:** replace timestamp-based gap detection with deterministic block number validation ([0b836a4](https://github.com/terrylica/gapless-network-data/commit/0b836a425d077ff98c5181de0fad324b023083b7))
- **oracle:** add automatic retry script for ARM instance provisioning ([444bf06](https://github.com/terrylica/gapless-network-data/commit/444bf0657991c5ab060876db66aac15f07fdae36))
- **vm:** add batch write mode to reduce MotherDuck compute units by 25x ([21d4506](https://github.com/terrylica/gapless-network-data/commit/21d4506d838637e2fc98559999b258378bdef01e))

# [3.0.0](https://github.com/terrylica/gapless-network-data/compare/v2.7.0...v3.0.0) (2025-11-11)

### Features

- **monitoring:** deploy MotherDuck gap detection to GCP Cloud Functions ([1eac100](https://github.com/terrylica/gapless-network-data/commit/1eac100adf153642360be2a13a3afb182cb1b158))

### BREAKING CHANGES

- **monitoring:** Oracle Cloud deployment superseded by GCP Cloud Functions

# [2.7.0](https://github.com/terrylica/gapless-network-data/compare/v2.6.0...v2.7.0) (2025-11-11)

### Features

- **monitoring:** add ULID unique identifiers to Pushover notifications ([bf60077](https://github.com/terrylica/gapless-network-data/commit/bf600776d12eea9d180246fc3442f947c414139e))

# [2.6.0](https://github.com/terrylica/gapless-network-data/compare/v2.5.0...v2.6.0) (2025-11-11)

### Features

- **monitoring:** add oracle cloud motherduck gap detection ([5abe058](https://github.com/terrylica/gapless-network-data/commit/5abe0588c892fb39a3d94c2f4d0ea5c932b2139d))

# [2.5.0](https://github.com/terrylica/gapless-network-data/compare/v2.4.0...v2.5.0) (2025-11-11)

### Features

- **gap-detection:** implement automated gap detection system (Phase 2) ([7d9e035](https://github.com/terrylica/gapless-network-data/commit/7d9e03520531cd3ba8f674fa91370090f73777bb)), closes [#2](https://github.com/terrylica/gapless-network-data/issues/2)

# [2.4.0](https://github.com/terrylica/gapless-network-data/compare/v2.3.0...v2.4.0) (2025-11-10)

### Features

- add motherduck data quality monitoring ([7f0e518](https://github.com/terrylica/gapless-network-data/commit/7f0e518e179e69528bb85a93a397746d03fcaf4d))

# [2.3.0](https://github.com/terrylica/gapless-network-data/compare/v2.2.1...v2.3.0) (2025-11-10)

### Features

- add Healthchecks.io heartbeat monitoring to VM real-time collector ([94bda3b](https://github.com/terrylica/gapless-network-data/commit/94bda3b713b3c05f1cff3f90e699d095238a843d))

## [2.2.1](https://github.com/terrylica/gapless-network-data/compare/v2.2.0...v2.2.1) (2025-11-10)

### Bug Fixes

- **monitoring:** correct Cloud Run Job monitoring (Healthchecks.io) ([8df2232](https://github.com/terrylica/gapless-network-data/commit/8df223275b141122689a25d39808fac37134140c)), closes [#monitoring-false-positive](https://github.com/terrylica/gapless-network-data/issues/monitoring-false-positive)

# [2.2.0](https://github.com/terrylica/gapless-network-data/compare/v2.1.0...v2.2.0) (2025-11-10)

### Features

- **monitoring:** implement Pushover and Healthchecks.io integrations ([58df1aa](https://github.com/terrylica/gapless-network-data/commit/58df1aaba7a3dc41c5a66a9d06f33a198647ec3e))

# [2.1.0](https://github.com/terrylica/gapless-network-data/compare/v2.0.1...v2.1.0) (2025-11-10)

### Features

- **skills:** add motherduck-pipeline-operations skill and chunked backfill pattern ([7c23528](https://github.com/terrylica/gapless-network-data/commit/7c235280060bdaaf8d3ed1b3671e33b13b74a09f))

## [2.0.1](https://github.com/terrylica/gapless-network-data/compare/v2.0.0...v2.0.1) (2025-11-10)

### Bug Fixes

- **skills:** sync monitoring skill docs with Pushover API clients ([6115cc5](https://github.com/terrylica/gapless-network-data/commit/6115cc5479fcb346400e4f4ec30d9c3505a6323e))

# [2.0.0](https://github.com/terrylica/gapless-network-data/compare/v1.1.1...v2.0.0) (2025-11-10)

### Features

- add MotherDuck integration with dual pipeline architecture ([d46259c](https://github.com/terrylica/gapless-network-data/commit/d46259c35b3d429777fc31679b7bdd49b42146e1))
- **skills:** validate monitoring APIs with Pushover integration ([10672ed](https://github.com/terrylica/gapless-network-data/commit/10672edb6ebdb8a94e809d32451ce821a544b9f4))

### BREAKING CHANGES

- **skills:** Replaced Telegram methods with Pushover methods in API clients

## [1.1.1](https://github.com/terrylica/gapless-network-data/compare/v1.1.0...v1.1.1) (2025-11-09)

### Bug Fixes

- deploy .strip() fix to VM collector, resolve crash-loop ([8f820e7](https://github.com/terrylica/gapless-network-data/commit/8f820e786d1d56ffc04be09b765a1c93a4757091))

# [1.1.0](https://github.com/terrylica/gapless-network-data/compare/v1.0.0...v1.1.0) (2025-11-09)

### Bug Fixes

- update Node.js engine requirement to v22.14.0 minimum ([81f0281](https://github.com/terrylica/gapless-network-data/commit/81f02814f1c46182964b1f2b076df10037fa7b0f))

### Features

- add DuckDB integration for Phase 1 historical collection ([e32dc48](https://github.com/terrylica/gapless-network-data/commit/e32dc48b0b95e1b207a82f2e96bfebfb1bbd661a))
- add MotherDuck integration with dual-pipeline architecture ([c0b8fd3](https://github.com/terrylica/gapless-network-data/commit/c0b8fd3293408a5cd5386cdf90932e89a8fc627b))

# 1.0.0 (2025-11-08)

### Bug Fixes

- **ci:** include package-lock.json for reproducible semantic-release builds ([d03d8be](https://github.com/terrylica/gapless-network-data/commit/d03d8be0da1c714e5ad7326d9041c4380da3a9c1))

### Features

- add GitHub Actions workflow for automated releases ([8b7af4c](https://github.com/terrylica/gapless-network-data/commit/8b7af4c9c125870a17a2e89680e0e37fefaa6f93))
- migrate to semantic-release v25 (Node.js) for future-proofing ([bb1164e](https://github.com/terrylica/gapless-network-data/commit/bb1164e96f040ac961faabc73ee014b50fa3651e))
- **refactor:** achieve 100% REFACTOR.md compliance across all skills ([17e867d](https://github.com/terrylica/gapless-network-data/commit/17e867dd9f200439571d3732cee9dfa0bf940367))

### BREAKING CHANGES

- **refactor:** None (backward compatible, pure extraction)
- Switched from python-semantic-release to semantic-release (Node.js) v25.0.2

Rationale:

- 23.5x larger community (22,900 vs 975 GitHub stars)
- 100x+ more adoption (1.9M weekly npm downloads)
- Used by 126,000 projects (vs unknown for python-semantic-release)
- Better future-proofing with larger maintainer team
- More robust plugin ecosystem (35+ official plugins)
- Multi-language support for potential monorepo expansion

Changes:

- Remove python-semantic-release from pyproject.toml dependencies
- Remove [tool.semantic_release] configuration from pyproject.toml
- Add package.json with semantic-release v25.0.2 and plugins
- Add .releaserc.yml configuration for Python project
- Update GitHub Actions workflow to use Node.js semantic-release
- Add .gitignore for node_modules/

Configuration:

- @semantic-release/commit-analyzer: Analyze conventional commits
- @semantic-release/release-notes-generator: Generate release notes
- @semantic-release/changelog: Update CHANGELOG.md
- @semantic-release/exec: Update pyproject.toml version and build with uv
- @semantic-release/git: Commit version changes
- @semantic-release/github: Create GitHub releases with wheel/tarball assets

Verified working locally with dry-run mode.

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
