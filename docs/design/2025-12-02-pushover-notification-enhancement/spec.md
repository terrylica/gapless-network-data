---
adr: 2025-12-02-pushover-notification-enhancement
source: ~/.claude/plans/serene-swimming-gadget.md
implementation-status: in_progress
phase: phase-1
last-updated: 2025-12-02
---

# Design Spec: Pushover Notification Enhancement

**ADR**: [Pushover Notification Enhancement](/docs/adr/2025-12-02-pushover-notification-enhancement.md)

## Problem Statement

Enhance the gap monitor's Pushover "HEALTHY" notification with additional operational context while respecting the 1024 character limit.

## Current State

**File**: `deployment/gcp-functions/gap-monitor/main.py` (lines 655-668)

**Current message** (~123 chars with ULID, 12% of limit):

```
Blocks: 23,928,013
Range: 0 to 23,928,012
Age: 69s
New gaps tracked: 0
Sequence: Complete

ULID: 01KBGAD8XZWJYVJM5C8MQH0534
```

**Available headroom**: ~900 characters

## Target State

**New message format** (~350 chars, 34% of limit):

```
Blocks: 23,928,013 (100% coverage)
Range: 0 to 23,928,012
Latest: #23,928,012 @ 2025-12-02 14:23:45 UTC
Age: 69s / 960s threshold (7%)
Margin: 891s until stale
Gaps: 0 new | 0 tracked | 0 resolved
Sequence: Complete

ULID: 01KBGAD8XZWJYVJM5C8MQH0534
```

## Available Data (Not Currently Shown)

| Variable                      | Description                        | Current Use               |
| ----------------------------- | ---------------------------------- | ------------------------- |
| `latest_timestamp`            | ISO 8601 timestamp of latest block | Available but hidden      |
| `latest_block`                | Block number of latest received    | Same as max_block         |
| `STALENESS_THRESHOLD_SECONDS` | 960s (16 min)                      | Can compute time-to-stale |
| `persistent_gaps`             | Gaps lasting >30 min               | Only in emergency alerts  |
| `resolved_gaps`               | Recently filled gaps               | Only in resolved alerts   |

## Implementation Tasks

- [x] **Task 1**: Compute additional metrics
  - `staleness_pct = int((age_seconds / STALENESS_THRESHOLD_SECONDS) * 100)`
  - `time_to_stale = STALENESS_THRESHOLD_SECONDS - age_seconds`

- [x] **Task 2**: Update message construction (lines 655-668)
  - Add Latest line with block number and timestamp
  - Add threshold percentage to Age line
  - Add Margin line with time-to-stale
  - Update Gaps line with three-way breakdown (new/tracked/resolved)

- [x] **Task 3**: Verify message length stays under 1024 chars (verified: 208 chars, 20.3% of limit)

- [ ] **Task 4**: Test locally with dry-run

- [ ] **Task 5**: Deploy to GCP Cloud Functions

## Code Changes

**File**: `deployment/gcp-functions/gap-monitor/main.py`

**Lines 655-668** - Update message construction:

```python
# Compute additional metrics
# ADR: 2025-12-02-pushover-notification-enhancement
staleness_pct = int((age_seconds / STALENESS_THRESHOLD_SECONDS) * 100)
time_to_stale = STALENESS_THRESHOLD_SECONDS - age_seconds

# Format timestamp for display
latest_ts_str = latest_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

message = (
    f"Blocks: {total_blocks:,}\n"
    f"Range: {min_block:,} to {max_block:,}\n"
    f"Latest: #{latest_block:,} @ {latest_ts_str}\n"
    f"Age: {age_seconds}s / {STALENESS_THRESHOLD_SECONDS}s threshold ({staleness_pct}%)\n"
    f"Margin: {time_to_stale}s until stale\n"
    f"Gaps: {len(new_gaps)} new | {len(persistent_gaps)} tracked | {len(resolved_gaps)} resolved\n"
    f"Sequence: Complete"
)
```

## Pushover Limits Reference

- **Message**: 1,024 characters
- **Title**: 250 characters (current "HEALTHY" = 7 chars)
- **Supplementary URL**: 512 characters (unused)
- **URL title**: 100 characters (unused)

## Success Criteria

- [ ] Message includes all 7 data points from target format
- [ ] Message length < 400 chars (well under 1024 limit)
- [ ] Timestamp formatted in UTC for consistency
- [ ] Staleness percentage calculated correctly
- [ ] Time-to-stale margin displayed
- [ ] Gap breakdown shows all three categories
- [ ] Cloud Function deployed and operational
