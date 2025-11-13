# Architectural Decision Records (MADRs)

Local navigation hub for Markdown Any Decision Records documenting key architectural and operational decisions.

## Production Monitoring & Operations (MADR-0001 to MADR-0004)

- [MADR-0001: Healthchecks Grace Period Calibration](./0001-healthchecks-grace-period-calibration.md) - Dead Man's Switch grace period optimization
- [MADR-0002: Exception Handler Notifications](./0002-exception-handler-notifications.md) - Pushover alert integration for pipeline failures
- [MADR-0003: MotherDuck Timeout Fallback](./0003-motherduck-timeout-fallback.md) - Connection timeout handling and retry strategy
- [MADR-0004: Staleness Threshold Calibration](./0004-staleness-threshold-calibration.md) - Data freshness monitoring threshold (960s batch mode)

## Documentation Normalization (MADR-0005 to MADR-0008)

- [MADR-0005: Root CLAUDE.md Scope](./0005-root-claude-scope.md) - Essential context + navigation hub strategy (500-600 lines)
- [MADR-0006: Child CLAUDE.md Spokes](./0006-child-claude-spokes.md) - Local navigation hub pattern for docs/ subdirectories
- [MADR-0007: Skills Extraction](./0007-skills-extraction.md) - Workflow extraction criteria (vm-infrastructure-ops, historical-backfill-execution)
- [MADR-0008: Link Format Standardization](./0008-link-format.md) - Relative GFM paths for portability and lychee compatibility

## MADR Format

All MADRs follow the Markdown Any Decision Records format:

- **Status**: Proposed, Accepted, Deprecated, Superseded
- **Context**: Problem statement and background
- **Decision**: Chosen solution with rationale
- **Consequences**: Positive, negative, and mitigation strategies
- **Alternatives Considered**: Rejected options with reasons
- **Validation**: Test cases and verification criteria
- **SLO Impact**: Before/after metrics for observability

## Related Documentation

- [Root CLAUDE.md](../../CLAUDE.md) - Project overview and quick navigation
- [Architecture Documentation](../architecture/) - System architecture and design
- [Specifications Directory](../../specifications/) - OpenAPI 3.x machine-readable specifications
