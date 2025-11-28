# Architectural Decision Records (MADRs)

Local navigation hub for Markdown Any Decision Records documenting key architectural and operational decisions.

## Production Monitoring & Operations (MADR-0001 to MADR-0004)

- [MADR-0001: Healthchecks Grace Period Calibration](./0001-healthchecks-grace-period-calibration.md) - Dead Man's Switch grace period optimization
- [MADR-0002: Exception Handler Notifications](./0002-exception-handler-notifications.md) - Pushover alert integration for pipeline failures
- [MADR-0003: MotherDuck Timeout Fallback](./0003-motherduck-timeout-fallback.md) - ~~Connection timeout handling~~ **SUPERSEDED** by MADR-0013
- [MADR-0004: Staleness Threshold Calibration](./0004-staleness-threshold-calibration.md) - ~~Data freshness monitoring~~ **SUPERSEDED** by MADR-0013

## Documentation Normalization (MADR-0005 to MADR-0008)

- [MADR-0005: Root CLAUDE.md Scope](./0005-root-claude-scope.md) - Essential context + navigation hub strategy (500-600 lines)
- [MADR-0006: Child CLAUDE.md Spokes](./0006-child-claude-spokes.md) - Local navigation hub pattern for docs/ subdirectories
- [MADR-0007: Skills Extraction](./0007-skills-extraction.md) - Workflow extraction criteria (vm-infrastructure-ops, historical-backfill-execution)
- [MADR-0008: Link Format Standardization](./0008-link-format.md) - Relative GFM paths for portability and lychee compatibility

## Project Standards (MADR-0009 to MADR-0012)

- [MADR-0009: Version Alignment Strategy](./0009-version-alignment-strategy.md) - Package version alignment with data state
- [MADR-0010: Documentation Accuracy Standards](./0010-documentation-accuracy-standards.md) - Verified claims, deprecation process
- [MADR-0011: Link Format Enforcement](./0011-link-format-enforcement.md) - CI/CD link validation via lychee
- [MADR-0012: Build Artifact Cleanup Policy](./0012-build-artifact-cleanup-policy.md) - Scratch directory lifecycle management

## Infrastructure Migrations (MADR-0013 to MADR-0016)

- [MADR-0013: MotherDuck to ClickHouse Migration](./0013-motherduck-clickhouse-migration.md) - Production database migration from MotherDuck to ClickHouse Cloud AWS
- [MADR-0014: Documentation Rectification](./0014-documentation-rectification.md) - Post-migration documentation synchronization
- [MADR-0015: Gap Detector ClickHouse Fix](./0015-gap-detector-clickhouse-fix.md) - Fix gap detector to use ClickHouse after migration
- [MADR-0016: Enable Healthchecks.io for Gap Detector](./0016-healthchecks-gap-detector-enable.md) - Enable Dead Man's Switch monitoring for gap detector

## Date-Based ADRs (2025-11-28+)

> **New Naming Convention**: `YYYY-MM-DD-slug.md` in `/docs/architecture/decisions/`
> See [ADR Standards](/docs/architecture/decisions/README.md) for format requirements.

- [2025-11-28-realtime-collector-transaction-count-fix](/docs/architecture/decisions/2025-11-28-realtime-collector-transaction-count-fix.md) - Fix transaction_count=0 bug via eth_getBlockByNumber

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
