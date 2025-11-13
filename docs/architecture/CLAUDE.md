# Architecture Documentation

Local navigation hub for architectural design documents, system diagrams, and technical specifications.

## Files

- [Architecture Overview](./OVERVIEW.md) - Core components, data flow, SLOs, operational infrastructure
- [Data Format Specification](./DATA_FORMAT.md) - Mempool snapshot schema, column definitions, data types
- [DuckDB Strategy](./duckdb-strategy.md) - DuckDB PRIMARY architecture, 23 features, performance benchmarks, use cases
- [MotherDuck Dual Pipeline](./motherduck-dual-pipeline.md) - Dual-pipeline architecture, BigQuery + Alchemy, failure modes, monitoring
- [BigQuery-MotherDuck Integration](./bigquery-motherduck-integration.md) - PyArrow zero-copy transfer, performance analysis, cost optimization

## Related Documentation

- [Root CLAUDE.md](../../CLAUDE.md) - Project overview and quick navigation
- [Deployment Guides](../deployment/) - Infrastructure deployment documentation (future)
- [Decisions (MADRs)](../decisions/) - Architectural Decision Records (future)
- [Skills Catalog](../../.claude/skills/CATALOG.md) - Project skills (7 operational skills)
