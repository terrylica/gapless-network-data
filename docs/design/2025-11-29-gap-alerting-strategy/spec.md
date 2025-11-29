# Design Spec: Two-Tier Gap Alerting Strategy

**Status**: Complete
**Last Updated**: 2025-11-29
**Release**: Pending deployment

## Problem Statement

Current gap detector alerts immediately on any gap, creating noise because:
1. Deployment restarts cause expected gaps (self-healing will fill)
2. Transient network issues cause gaps that resolve automatically
3. Only persistent gaps (>30 min unfilled) indicate real problems

## Solution: Two-Tier Alerting

### Tier 1: Grace Period (No Alert)

- Gap detected but within grace period (default: 30 minutes)
- Gap stored in `gap_tracking` table with `first_seen` timestamp
- No notification sent
- Self-healing mechanisms have time to resolve

### Tier 2: Persistent Gap (Emergency Alert)

- Gap persists beyond grace period
- Emergency notification (priority=2)
- Requires manual investigation

### Bonus: Gap Resolved Notification

- When previously-tracked gap is filled
- Normal priority notification (priority=0)
- Positive feedback that system is working

## ClickHouse Schema

```sql
CREATE TABLE ethereum_mainnet.gap_tracking (
    gap_start UInt64,           -- First missing block number
    gap_end UInt64,             -- Last missing block number
    gap_size UInt64,            -- Number of missing blocks
    first_seen DateTime,        -- When gap was first detected
    last_seen DateTime,         -- When gap was last confirmed
    notified Bool DEFAULT false -- Whether emergency alert sent
) ENGINE = ReplacingMergeTree(last_seen)
ORDER BY (gap_start, gap_end)
```

## Alert Logic

```python
GRACE_PERIOD_SECONDS = 1800  # 30 minutes

for gap in current_gaps:
    existing = lookup_in_tracking_table(gap)

    if existing is None:
        # New gap - store but don't alert
        insert_gap_tracking(gap, first_seen=now)
    else:
        age_seconds = now - existing.first_seen

        if age_seconds > GRACE_PERIOD_SECONDS and not existing.notified:
            # Persistent gap - ALERT!
            send_emergency_alert(gap)
            mark_as_notified(gap)
        else:
            # Update last_seen
            update_last_seen(gap, now)

# Check for resolved gaps
for tracked_gap in all_tracked_gaps:
    if tracked_gap not in current_gaps:
        send_resolution_alert(tracked_gap)
        delete_from_tracking(tracked_gap)
```

## Configuration Constants

| Constant | Value | Rationale |
|----------|-------|-----------|
| `GRACE_PERIOD_SECONDS` | 1800 | 30 min for self-healing |
| `STALE_TRACKING_HOURS` | 24 | Auto-delete very old tracked gaps |

## Alert Messages

### New Gap (No Alert)
```
(silent - stored for tracking only)
```

### Persistent Gap (Emergency)
```
Title: PERSISTENT GAP
Message:
Gap persists for >30 minutes - requires investigation

Gap: blocks 23,902,714 to 23,902,716 (3 blocks)
First detected: 2025-11-29 07:04:52 UTC
Duration: 45 minutes

ULID: 01KB7...
```

### Gap Resolved (Info)
```
Title: GAP RESOLVED
Message:
Previously tracked gap has been filled (self-healed)

Gap: blocks 23,902,714 to 23,902,716 (3 blocks)
First detected: 2025-11-29 07:04:52 UTC
Resolved after: 12 minutes

ULID: 01KB7...
```

## Implementation Checklist

- [x] Create `gap_tracking` table in ClickHouse
- [x] Add gap persistence logic to monitor
- [x] Add gap resolution detection
- [x] Add tiered notification logic
- [ ] Test with simulated gaps
- [ ] Deploy to Cloud Functions
