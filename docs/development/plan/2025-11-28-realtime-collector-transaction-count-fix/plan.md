# Plan: Real-Time Collector Transaction Count Fix

**ADR**: [/docs/architecture/decisions/2025-11-28-realtime-collector-transaction-count-fix.md](/docs/architecture/decisions/2025-11-28-realtime-collector-transaction-count-fix.md)

**Created**: 2025-11-28

**Status**: Completed

---

## Context

### Problem Summary

Recent blocks in ClickHouse show `transaction_count = 0` while historical blocks from BigQuery have correct values.

### Root Cause

`eth_subscribe newHeads` WebSocket notifications only return block headers - they do NOT include the `transactions` array.

```python
# deployment/vm/realtime_collector.py:241 (before fix)
transaction_count = len(block_data.get('transactions', []))  # Always 0!
```

### Solution

Standard block indexer pattern:
```
newHeads notification → eth_getBlockByNumber → parse → insert
```

---

## Task List

### Phase 1: Code Fix

- [x] Add `ALCHEMY_HTTP_URL` global variable
- [x] Add `fetch_full_block()` function for `eth_getBlockByNumber` RPC
- [x] Update block processing flow in `subscribe_to_blocks()`
- [x] Update docstrings

### Phase 2: Documentation

- [x] Create MADR document
- [x] Update CLAUDE.md index
- [x] Migrate to YYYY-MM-DD naming format

### Phase 3: Deployment

- [x] Commit changes
- [x] Push to remote
- [x] Deploy to VM via gcloud SSH + SCP
- [x] Restart eth-collector service

### Phase 4: Validation

- [ ] Wait for batch flush (5 minutes)
- [ ] Query ClickHouse to verify `transaction_count > 0` for new blocks

---

## Files Modified

| File | Change |
|------|--------|
| `deployment/vm/realtime_collector.py` | Added `ALCHEMY_HTTP_URL`, `fetch_full_block()`, updated block flow |
| `docs/architecture/decisions/2025-11-28-realtime-collector-transaction-count-fix.md` | New ADR |

---

## Validation Query

```sql
SELECT number, transaction_count
FROM ethereum_mainnet.blocks FINAL
WHERE timestamp > now() - INTERVAL 1 HOUR
ORDER BY number DESC
LIMIT 10
```

Expected: All rows should have `transaction_count > 0` (except possibly empty blocks)

---

## Progress Log

| Date       | Update                                                           |
|------------|------------------------------------------------------------------|
| 2025-11-28 | Root cause identified: newHeads lacks transactions array         |
| 2025-11-28 | Implemented fix with eth_getBlockByNumber pattern               |
| 2025-11-28 | Deployed to VM, service restarted                               |
| 2025-11-28 | Migrated ADR to YYYY-MM-DD format                               |
