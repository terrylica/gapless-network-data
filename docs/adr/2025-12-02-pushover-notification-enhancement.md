---
status: accepted
date: 2025-12-02
decision-maker: Terry Li
consulted: [Explore-Agent]
research-method: single-agent
clarification-iterations: 1
perspectives: [OperationalService, ProductFeature]
---

# ADR: Pushover Notification Enhancement

**Design Spec**: [Implementation Spec](/docs/design/2025-12-02-pushover-notification-enhancement/spec.md)

## Context and Problem Statement

The gap monitor's Pushover "HEALTHY" notification currently provides minimal operational context. The message uses only ~123 characters of the 1024 character limit (12%), leaving significant headroom for additional operational intelligence.

**Current state**: Basic status with block count, range, age, and gap count.

**Problem**: Operators cannot assess system health margins at a glance. Questions like "how close are we to the staleness threshold?" or "were any gaps resolved?" require checking other dashboards.

### Before/After

**Before** (~123 chars):

```
⏮️ Before: Minimal Status

╭───────────────────────╮
│ Pushover Notification │
╰───────────────────────╯
  │
  ∨
┌───────────────────────┐
│      Block Count      │
└───────────────────────┘
  │
  ∨
┌───────────────────────┐
│         Range         │
└───────────────────────┘
  │
  ∨
┌───────────────────────┐
│          Age          │
└───────────────────────┘
  │
  ∨
┌───────────────────────┐
│       Gap Count       │
└───────────────────────┘
  │
  ∨
┌───────────────────────┐
│       Sequence        │
└───────────────────────┘
```

**After** (~350 chars):

```
⏭️ After: Comprehensive Dashboard

    ╭──────────────────────────╮
    │  Pushover Notification   │
    ╰──────────────────────────╯
      │
      ∨
    ┌──────────────────────────┐
    │  Block Count + Coverage  │
    └──────────────────────────┘
      │
      ∨
    ┌──────────────────────────┐
    │          Range           │
    └──────────────────────────┘
      │
      ∨
    ┌──────────────────────────┐
    │ Latest Block + Timestamp │
    └──────────────────────────┘
      │
      ∨
    ┌──────────────────────────┐
    │    Age + Threshold %     │
    └──────────────────────────┘
      │
      ∨
    ┌──────────────────────────┐
    │          Margin          │
    └──────────────────────────┘
      │
      ∨
    ┌──────────────────────────┐
    │      Gap Breakdown       │
    └──────────────────────────┘
      │
      ∨
    ┌──────────────────────────┐
    │         Sequence         │
    └──────────────────────────┘
```

<details>
<summary>graph-easy source (Before)</summary>

```
graph { label: "⏮️ Before: Minimal Status"; flow: south; }
[Pushover Notification] { shape: rounded; }
[Block Count] -> [Range] -> [Age] -> [Gap Count] -> [Sequence]
[Pushover Notification] -> [Block Count]
```

</details>

<details>
<summary>graph-easy source (After)</summary>

```
graph { label: "⏭️ After: Comprehensive Dashboard"; flow: south; }
[Pushover Notification] { shape: rounded; }
[Block Count + Coverage] -> [Range] -> [Latest Block + Timestamp] -> [Age + Threshold %] -> [Margin] -> [Gap Breakdown] -> [Sequence]
[Pushover Notification] -> [Block Count + Coverage]
```

</details>

## Research Summary

| Agent Perspective | Key Finding                                     | Confidence |
| ----------------- | ----------------------------------------------- | ---------- |
| Explore-Agent     | 4 unused variables available in healthy context | High       |
| Explore-Agent     | Pushover limit is 1024 chars (900+ available)   | High       |

**Available but unused data**:

- `latest_timestamp` - ISO 8601 timestamp of latest block
- `STALENESS_THRESHOLD_SECONDS` - 960s threshold for computing margin
- `persistent_gaps` - Gaps lasting >30 min grace period
- `resolved_gaps` - Recently filled gaps

## Decision Log

| Decision Area     | Options Evaluated                            | Chosen            | Rationale                                                        |
| ----------------- | -------------------------------------------- | ----------------- | ---------------------------------------------------------------- |
| Message Format    | A (Minimal), B (Moderate), C (Comprehensive) | C (Comprehensive) | Full operational dashboard at ~350 chars, well within 1024 limit |
| Staleness Display | Absolute only vs Percentage vs Both          | Both              | Percentage shows relative health, absolute shows time margin     |
| Gap Display       | Single count vs Three-way breakdown          | Three-way         | Distinguishes new/tracked/resolved for operational clarity       |

### Trade-offs Accepted

| Trade-off                 | Choice             | Accepted Cost                                     |
| ------------------------- | ------------------ | ------------------------------------------------- |
| Message length vs brevity | Longer (350 chars) | More scrolling on mobile, but still <35% of limit |
| Complexity vs simplicity  | More fields        | Slightly more cognitive load per notification     |

## Decision Drivers

- Maximize operational visibility from Pushover notifications
- Stay well within 1024 character limit
- Enable at-a-glance health assessment
- Surface time-to-stale margin prominently

## Considered Options

- **Option A (Minimal)**: Add threshold context and time-to-stale (~180 chars)
- **Option B (Moderate)**: Add timestamp, percentage, gap breakdown (~250 chars)
- **Option C (Comprehensive)**: Full operational dashboard with all metrics (~350 chars) ← Selected

## Decision Outcome

Chosen option: **Option C (Comprehensive)**, because it provides complete operational context while using only ~35% of the available character budget. The additional information enables operators to assess system health margins without checking secondary dashboards.

**New message format**:

```
Blocks: 23,928,013 (100% coverage)
Range: 0 to 23,928,012
Latest: #23,928,012 @ 2025-12-02 14:23:45 UTC
Age: 69s / 960s threshold (7%)
Margin: 891s until stale
Gaps: 0 new | 0 tracked | 0 resolved
Sequence: Complete ✓
```

## Synthesis

**Convergent findings**: All options agreed on adding staleness threshold context.

**Divergent findings**: Trade-off between message brevity and information density.

**Resolution**: User selected comprehensive format given 900+ chars of headroom.

## Consequences

### Positive

- Operators see time-to-stale margin at a glance
- Three-way gap status provides operational context
- Latest block timestamp enables quick verification
- Percentage shows relative position within threshold

### Negative

- Longer message requires more reading
- More fields to parse on mobile devices
- Slightly higher cognitive load per notification

## Architecture

```
                     📡 Gap Monitor Notification Architecture

╔════════════╗     ┌──────────────────┐     ┌──────────────┐     ╭───────────────╮
║ ClickHouse ║     │   Gap Monitor    │     │ Pushover API │     │ Mobile Device │
║            ║ ──> │ (Cloud Function) │ ──> │              │ ──> │               │
╚════════════╝     └──────────────────┘     └──────────────┘     ╰───────────────╯
                     │
                     │
                     ∨
                   ┌──────────────────┐
                   │ Healthchecks.io  │
                   └──────────────────┘
```

<details>
<summary>graph-easy source</summary>

```
graph { label: "📡 Gap Monitor Notification Architecture"; flow: east; }
[ClickHouse] { border: double; } -> [Gap Monitor\n(Cloud Function)] -> [Pushover API] -> [Mobile Device] { shape: rounded; }
[Gap Monitor\n(Cloud Function)] -> [Healthchecks.io]
```

</details>

## References

- [Gap Monitor README](/deployment/gcp-functions/gap-monitor/README.md)
- [Pushover API Documentation](https://pushover.net/api) (1024 char message limit)
