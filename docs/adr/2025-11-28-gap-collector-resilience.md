# ADR: Gap Collector Resilience

**Date**: 2025-11-28
**Status**: Accepted
**Design Spec**: [Gap Collector Resilience Spec](/docs/design/2025-11-28-gap-collector-resilience/spec.md)

## Context

The Ethereum real-time block collector (`deployment/vm/realtime_collector.py`) has been experiencing recurring data gaps despite multiple previous fixes. Gap alerts show missing blocks at irregular intervals, indicating systematic failure modes in the collection pipeline.

### Defense-in-Depth Architecture

```
┌──────────┐     ┌───────────────┐     ┌──────────────┐     ┌─────────────┐
│ L1 Retry │ ──> │ L2 Exceptions │ ──> │ L3 Gap Track │ ──> │ L4 Backfill │
└──────────┘     └───────────────┘     └──────────────┘     └─────────────┘
```

### Data Flow with Self-Healing

```
                                ┌───────────────────┐
                                │ Alchemy WebSocket │
                                └───────────────────┘
                                  │
                                  ∨
                                ┌───────────────────┐
                                │    JSON Parse     │
                                └───────────────────┘
                                  │
                                  ∨
                                ┌───────────────────┐
                                │   Block Process   │ ─┐
                                └───────────────────┘  │
                                  │                    │
                                  ∨                    │
┌────────────────┐  large gap   ┌───────────────────┐  │
│ External Alert │ <─────────── │   Gap Detector    │  │
└────────────────┘              └───────────────────┘  │
                                  │                    │
                                  │ small gap          │
                                  ∨                    │
                                ┌───────────────────┐  │
                                │  Inline Backfill  │  │
                                └───────────────────┘  │
                                  │                    │
                                  ∨                    │
                                ┌───────────────────┐  │
                                │    ClickHouse     │ <┘
                                └───────────────────┘
```

<details>
<summary>graph-easy source</summary>

```
# Defense layers
graph { flow: east; }
[L1 Retry] -> [L2 Exceptions] -> [L3 Gap Track] -> [L4 Backfill]

# Data flow
graph { flow: south; }
[Alchemy WebSocket] -> [JSON Parse] -> [Block Process] -> [ClickHouse]
[Block Process] -> [Gap Detector]
[Gap Detector] -- small gap --> [Inline Backfill]
[Inline Backfill] -> [ClickHouse]
[Gap Detector] -- large gap --> [External Alert]
```

</details>

### Failure Points Identified

Sub-agent investigation identified **5 critical data loss points** where exceptions cause permanent block loss:

| Location                                 | Issue                           | Impact                                |
| ---------------------------------------- | ------------------------------- | ------------------------------------- |
| `fetch_full_block()` lines 146-150       | 10s timeout, no retry           | Single timeout = permanent block loss |
| `json.loads()` line 434                  | No JSONDecodeError handling     | Malformed message crashes loop        |
| `data['params']['result']` lines 437-438 | KeyError unhandled              | Missing key crashes loop              |
| `batch_flush_worker()` lines 360-368     | Prints error, doesn't re-raise  | Silent data loss                      |
| WebSocket loop lines 477-479             | Only catches `ConnectionClosed` | Other exceptions crash loop           |

## Decision

Implement a **defense-in-depth resilience strategy** with four layers:

1. **Retry Logic**: Add tenacity library with exponential backoff to `fetch_full_block()`
2. **Comprehensive Exception Handling**: Catch all exception types in WebSocket loop
3. **Self-Healing Gap Detection**: Track expected vs received block numbers in-memory
4. **Inline Backfill**: Automatically backfill small gaps (≤5 blocks) synchronously

## Consequences

### Positive

- Eliminates permanent block loss from transient network failures
- Self-healing reduces dependency on external gap detector
- Inline backfill minimizes gap duration (seconds vs hours)
- Better observability with gap tracking logs

### Negative

- Slight increase in code complexity (~100 lines)
- tenacity dependency added to script
- Inline backfill adds ~1-2s latency for small gaps

### Risks

- Large gaps (>5 blocks) still require external backfill
- In-memory tracking lost on service restart (acceptable - gap detector catches)

## Alternatives Considered

1. **Async backfill queue**: Too complex for single-file deployment
2. **Database-backed gap tracking**: Over-engineering for edge case
3. **Increase timeout only**: Doesn't address other failure modes

## Implementation

See [Design Spec](/docs/design/2025-11-28-gap-collector-resilience/spec.md) for detailed implementation.
