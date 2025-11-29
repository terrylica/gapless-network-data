# Design Spec: Gap Collector Resilience

**ADR**: [Gap Collector Resilience ADR](/docs/adr/2025-11-28-gap-collector-resilience.md)
**Status**: Implementation In Progress
**Last Updated**: 2025-11-28

## Overview

Implement bulletproof exception handling and retry logic to eliminate block loss in the Ethereum real-time collector.

## Root Cause Analysis

### 5 Critical Data Loss Points

| # | Location | Issue | Impact |
|---|----------|-------|--------|
| 1 | `fetch_full_block()` L146-150 | 10s timeout, no retry | **PERMANENT LOSS** |
| 2 | `json.loads()` L434 | No JSONDecodeError handling | Loop crashes |
| 3 | `data['params']['result']` L437-438 | KeyError unhandled | Loop crashes |
| 4 | `batch_flush_worker()` L360-368 | Prints error only | Silent loss |
| 5 | WebSocket loop L477-479 | Only catches ConnectionClosed | Other exceptions crash |

## Implementation Plan

### Phase 1: Add tenacity Retry to fetch_full_block()

**File**: `/deployment/vm/realtime_collector.py`

**Changes**:
1. Add `tenacity` to script dependencies (line 3)
2. Add import: `from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type`
3. Wrap `fetch_full_block()` with retry decorator

**Retry Configuration**:
- Max attempts: 3
- Wait: Exponential backoff (1s, 2s, 4s)
- Retry on: `requests.exceptions.RequestException`, `requests.exceptions.Timeout`
- Reraise on final failure

### Phase 2: Comprehensive WebSocket Exception Handling

**Changes to `subscribe_to_blocks()`**:
1. Wrap `json.loads()` in try/except JSONDecodeError
2. Use `.get()` for safe dict access instead of direct indexing
3. Wrap `fetch_full_block()` call in try/except
4. Add catch-all exception handler for WebSocket loop

### Phase 3: Self-Healing Gap Detection

**New Global State**:
```python
expected_next_block = None
missed_blocks = []
missed_blocks_lock = threading.Lock()
```

**New Functions**:
- `track_missed_block(block_number)`: Add to missed_blocks list
- `update_expected_block(received_block)`: Detect gaps, trigger inline backfill
- `backfill_inline(start_block, end_block)`: Sync backfill for ≤5 blocks

**Gap Detection Logic**:
```
if received_block > expected_next_block:
    gap_size = received_block - expected_next_block
    if gap_size <= 5:
        backfill_inline(expected_next_block, received_block - 1)
    else:
        track each missed block for later backfill
```

### Phase 4: Fix batch_flush_worker()

**Changes**:
1. Add `consecutive_failures` counter
2. Check `shutdown_requested` in loop condition
3. Log critical alert after 10 consecutive failures
4. Blocks remain in buffer for retry (no data loss)

## Constants

| Constant | Value | Rationale |
|----------|-------|-----------|
| `MAX_RETRY_ATTEMPTS` | 3 | Balance between resilience and latency |
| `RETRY_WAIT_MIN` | 1 | Minimum backoff in seconds |
| `RETRY_WAIT_MAX` | 10 | Maximum backoff in seconds |
| `INLINE_BACKFILL_THRESHOLD` | 5 | Max blocks to backfill synchronously |
| `MAX_CONSECUTIVE_FAILURES` | 10 | Alert threshold for batch flush |

## Testing Plan

1. **Unit test retry logic**: Mock `requests.post` to fail twice, succeed on 3rd
2. **Integration test**: Run collector, verify no gaps after 1 hour
3. **Chaos test**: Kill network for 30s, verify recovery and backfill

## Deployment Steps

1. Edit `realtime_collector.py` with changes
2. SCP to VM: `gcloud compute scp realtime_collector.py eth-realtime-collector:~/`
3. Restart service: `sudo systemctl restart eth-collector`
4. Monitor logs: `journalctl -u eth-collector -f`
5. Verify no gaps after 1 hour via gap detector

## Verification Checklist

- [ ] tenacity added to script dependencies
- [ ] `fetch_full_block()` retries 3x with exponential backoff
- [ ] WebSocket loop catches all exceptions
- [ ] Gap detection tracks expected vs received blocks
- [ ] Inline backfill for ≤5 block gaps
- [ ] `batch_flush_worker()` handles exceptions without crashing
- [ ] Deployed to VM and running
- [ ] No gaps detected after 1 hour of operation

## Progress Tracking

| Task | Status |
|------|--------|
| Create feature branch | Done |
| Create ADR and spec | Done |
| Add tenacity retry | Done |
| Add exception handling | Done |
| Add self-healing gap detection | Done |
| Fix batch_flush_worker | Done |
| Deploy to VM | Done |
| Create release | In Progress |
