# Phase 1 Implementation Plan - READY TO START

## Option A: Ethereum PRIMARY + Bitcoin SECONDARY (Multi-Chain v0.2.0)

**Decision Date**: 2025-11-04  
**Status**: ✅ All prerequisites complete - READY TO BEGIN IMPLEMENTATION  
**Duration**: 2 weeks (20-30 hours)  
**Target Version**: v0.2.0

---

## ✅ PREPARATION COMPLETE

All 8 preparation tasks finished:

1. ✅ **SSoT Audit Complete** - 993-line comprehensive report identified 13 issues
2. ✅ **Decision Documented** - Option A chosen and logged in master-project-roadmap.yaml
3. ✅ **Ethereum Specification Created** - ethereum-collector-phase1.yaml (466 lines, P0 priority)
4. ✅ **Multi-Chain API Designed** - Chain parameter architecture defined
5. ✅ **CLAUDE.md Updated** - Phase 1 scope, version milestones aligned
6. ✅ **Legacy Spec Archived** - core-collection-phase1.yaml moved to archive/
7. ✅ **Coverage Baseline Established** - Current: 20%, Target: 70%+
8. ✅ **All SSoT Conflicts Resolved** - Single authoritative specification

---

## 📊 CURRENT STATE

**Test Coverage (Baseline)**:

```
Module                          Coverage    Target
-----------------------------------------------
api.py                             60%  →   85%+
cli.py                              0%  →   70%+
collectors/mempool_collector       16%  →   70%+
exceptions.py                      32%  →   70%+
validation/models.py                0%  →   70%+
-----------------------------------------------
TOTAL                              20%  →   70%+
```

**Gap Analysis**: Need +50 percentage points coverage

---

## 🎯 PHASE 1 DELIVERABLES (v0.2.0)

### Ethereum Collection (PRIMARY - 12s intervals)

- EthereumCollector class (web3.py + LlamaRPC)
- 6-field minimal schema (number, timestamp, baseFeePerGas, gasUsed, gasLimit, transactions_count)
- Basic validation (Layer 1-2: RPC + schema)
- Retry logic (exponential backoff, max 3 retries)
- DuckDB storage: ethereum_blocks table in data.duckdb

### Bitcoin Collection (SECONDARY - 5min intervals)

- Complete Bitcoin collector testing (70%+ coverage)
- Integration test (12 snapshots = 1 hour)
- DuckDB storage: bitcoin_mempool table in data.duckdb

### Multi-Chain Architecture

- API: `fetch_snapshots(chain='ethereum'|'bitcoin', start, end, interval, db_path)`
- Chain-specific dispatch logic
- Chain-specific defaults (12s Ethereum, 300s Bitcoin)
- Single database: data.duckdb with ethereum_blocks and bitcoin_mempool tables

### Testing & Quality

- 70%+ test coverage
- Integration tests (10 blocks Ethereum, 12 snapshots Bitcoin)
- No silent failures (all errors raise structured exceptions)

### CLI & Documentation

- CLI with --chain parameter
- Ethereum schema docs (DATA_FORMAT.md)

---

## 📋 IMPLEMENTATION TASKS

### Week 1: Ethereum Collector (14 hours)

**Task 1: EthereumCollector Implementation (4 hours)**

- File: `src/gapless_network_data/collectors/ethereum_collector.py`
- Web3 client with LlamaRPC endpoint
- collect_block() method (single block with retry)
- collect_range() method (continuous polling every 12s)
- DuckDB output: INSERT INTO ethereum_blocks

**Task 2: Ethereum Validation (2 hours)**

- Layer 1: RPC validation (connection errors, timeouts)
- Layer 2: Schema validation (Pydantic)
- Sanity checks (gasUsed <= gasLimit, monotonic block numbers)
- Structured exceptions with context

**Task 3: Ethereum Retry Logic (1 hour)**

- Reuse tenacity pattern from Bitcoin collector
- Max 3 retries with exponential backoff (1s, 2s, 4s)
- Retry on connection errors only
- No retry on 4xx client errors

**Task 4: Multi-Chain API Integration (2 hours)**

- Update api.py with chain parameter
- Dispatcher logic (if chain == "ethereum" / elif chain == "bitcoin")
- Chain-specific intervals and DuckDB table targets
- Both collectors write to same data.duckdb
- ValueError for unsupported chains

**Task 5: Ethereum Tests (3 hours)**

- Unit tests (mocked web3.py responses)
- Test retry logic (connection errors, success after retry)
- Test validation (schema, sanity checks)
- Integration test (collect 10 real blocks from LlamaRPC)
- Target: 70%+ coverage on ethereum_collector.py

**Task 6: CLI Multi-Chain Support (2 hours)**

- Add --chain parameter (choices: ethereum, bitcoin)
- Update collect command
- Update stream command
- Help text for both chains

---

### Week 2: Testing, Documentation, Release (6-10 hours)

**Task 7: Bitcoin Collector Completion (2 hours)**

- Write comprehensive Bitcoin tests
- Integration test (12 snapshots)
- Verify 70%+ coverage on mempool_collector.py

**Task 8: Expand API Tests (2 hours)**

- Test fetch_snapshots() for both chains
- Test unsupported chain error
- Test chain-specific intervals
- Target: API coverage 60% → 90%+

**Task 9: Ethereum Schema Documentation (1 hour)**

- Document DuckDB schema in duckdb-schema-specification.yaml (already created)
- Update docs/architecture/DATA_FORMAT.md with DuckDB table schemas
- Include example SQL queries for common operations
- Note future 26-field expansion (Phase 4)

**Task 10: Integration Testing & Release (2-4 hours)**

- End-to-end tests for both chains
- CLI smoke tests
- Update CHANGELOG.md
- Git commit + tag v0.2.0
- GitHub Release

---

## 📈 SUCCESS GATES

### Gate 1: Ethereum Collector Works

- Collect 10 blocks from LlamaRPC successfully
- All 6 fields present and valid
- Data written to DuckDB ethereum_blocks table
- No silent failures

### Gate 2: Multi-Chain API Works

- `fetch_snapshots(chain="ethereum")` works
- `fetch_snapshots(chain="bitcoin")` works
- ValueError for unsupported chains

### Gate 3: Test Coverage 70%+

- ethereum_collector.py: 70%+
- mempool_collector.py: 16% → 70%+
- api.py: 60% → 85%+
- exceptions.py: 32% → 70%+

### Gate 4: No Silent Failures

- All error paths raise structured exceptions
- No `try/except: pass` patterns
- Exception context includes chain, timestamp, method

---

## 🚀 GETTING STARTED

### Immediate Next Steps

1. **Create Ethereum collector file**:

   ```bash
   touch src/gapless_network_data/collectors/ethereum_collector.py
   ```

2. **Create Ethereum exceptions**:
   Add to `src/gapless_network_data/exceptions.py`:
   - EthereumRPCException
   - EthereumValidationException
   - EthereumRateLimitException

3. **Create Ethereum schema**:
   Add to `src/gapless_network_data/validation/models.py`:
   - EthereumBlockSchema (Pydantic model with 6 fields)

4. **Start Task 1**: Implement EthereumCollector class

---

## 📚 REFERENCE DOCUMENTS

**Specifications**:

- Master Plan: `/Users/terryli/eon/gapless-network-data/specifications/master-project-roadmap.yaml`
- Ethereum Spec: `/Users/terryli/eon/gapless-network-data/specifications/ethereum-collector-phase1.yaml`
- Archived Bitcoin: `/Users/terryli/eon/gapless-network-data/specifications/archive/core-collection-phase1.yaml`

**Research**:

- LlamaRPC Index: `/Users/terryli/eon/gapless-network-data/docs/llamarpc/INDEX.md`
- web3.py SDK: `/Users/terryli/eon/gapless-network-data/docs/llamarpc/sdk/`
- Block Schema: `/Users/terryli/eon/gapless-network-data/docs/llamarpc/schema/`

---

## 💡 REUSABLE PATTERNS

### From Bitcoin Collector

1. ✅ Retry logic (tenacity library)
2. ✅ Structured exceptions (timestamp, endpoint, context)
3. ✅ Forward-collection enforcement
4. ✅ DuckDB storage (INSERT statements)

**Adaptation for Ethereum**:

- REST API → RPC calls
- httpx → web3.py
- Mempool endpoint → eth_getBlockByNumber
- Same DuckDB pattern: INSERT INTO ethereum_blocks

---

## ⏱️ TIME ESTIMATES

| Week      | Phase                   | Hours     | Tasks        |
| --------- | ----------------------- | --------- | ------------ |
| 1         | Ethereum Implementation | 14        | Tasks 1-6    |
| 2         | Testing & Polish        | 6-10      | Tasks 7-10   |
| **Total** | **v0.2.0 Release**      | **20-24** | **10 tasks** |

Buffer: +6 hours for unexpected issues (30 hours max)

---

## 🎯 DEFINITION OF DONE (v0.2.0)

Phase 1 complete when:

- ✅ Ethereum collector operational (12s intervals)
- ✅ Bitcoin collector operational (5min intervals)
- ✅ Multi-chain API works (chain parameter)
- ✅ 70%+ test coverage achieved
- ✅ All integration tests pass
- ✅ CLI supports both chains
- ✅ Documentation updated
- ✅ No silent failures
- ✅ CHANGELOG.md updated
- ✅ Git tag v0.2.0 created
- ✅ GitHub Release published

**You'll have a bulletproof multi-chain blockchain network data collector!** 🎉

---

**Ready to begin?** Start with Task 1 (EthereumCollector implementation).
