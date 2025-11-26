# MotherDuck Documentation

Local navigation hub for MotherDuck cloud database integration, credentials, and operational procedures.

## Files

- [INDEX.md](./INDEX.md) - MotherDuck integration overview and navigation hub
- [Credentials Management](./credentials.md) - MotherDuck token storage, Secret Manager integration, IAM permissions
- [BigQuery Integration](./bigquery-integration.md) - PyArrow zero-copy transfer, batch loading, performance tuning

## Architecture Documentation

> **DEPRECATED**: MotherDuck was replaced by ClickHouse Cloud on 2025-11-25. See [MADR-0013](../decisions/0013-motherduck-clickhouse-migration.md) for the current architecture.

Comprehensive MotherDuck architecture (archived) is documented in:

- [MotherDuck Dual Pipeline](../architecture/_archive/motherduck-dual-pipeline.md) - Complete architecture, failure modes, monitoring (DEPRECATED)
- [BigQuery-MotherDuck Integration](../architecture/_archive/bigquery-motherduck-integration.md) - PyArrow zero-copy transfer details (DEPRECATED)

## Operational Skills

> **Note**: MotherDuck skills have been deprecated. See ClickHouse-based monitoring via `clickhouse-gap-detector` Cloud Function.

Archived MotherDuck skills:

- [MotherDuck Pipeline Operations](../../.claude/skills/archive/motherduck-pipeline-operations/SKILL.md) - Database verification, gap detection (DEPRECATED)
- [Historical Backfill Execution](../../.claude/skills/historical-backfill-execution/SKILL.md) - 1-year chunked backfill, memory-safe execution
- [Data Pipeline Monitoring](../../.claude/skills/data-pipeline-monitoring/SKILL.md) - Cloud Run Jobs, VM services, alert systems

## Database Access

**Production Database**: `md:ethereum_mainnet.blocks`

- **Blocks**: 23.8M (2015-2025, Genesis → present)
- **Storage**: ~2.5 GB (within 10 GB free tier)
- **Access**: SDK queries MotherDuck cloud directly (no local DuckDB needed)
- **Deduplication**: Automatic via `INSERT OR REPLACE` on block number PRIMARY KEY

**Verification**:

```bash
uv run .claude/skills/motherduck-pipeline-operations/scripts/verify_motherduck.py
```

## Related Documentation

- [Root CLAUDE.md](../../CLAUDE.md) - Project overview and operational status
- [Architecture Documentation](../architecture/) - System architecture and design
- [Deployment Guides](../deployment/) - Infrastructure deployment procedures
