# Archived Documentation

This directory contains superseded research and documentation that is no longer relevant to the operational system but preserved for historical context.

## llamarpc-research/

**Status**: Superseded (2025-11-10)

**Original Purpose**: Comprehensive research into LlamaRPC as potential Ethereum block data source

**Why Archived**:
- LlamaRPC rejected due to rate limits (1.37 RPS sustained, 110-day timeline for 5-year backfill)
- Replaced by BigQuery public dataset + Alchemy WebSocket dual-pipeline
- BigQuery provides 624x faster historical data loading (<1 hour vs 26 days)

**Historical Value**:
- Empirical rate limit validation methodology
- RPC provider comparison framework
- Schema mapping between LlamaRPC and production formats
- POC scripts demonstrating fetch-to-storage pipelines

**References**:
- Decision logged in CLAUDE.md: "Data Sources: BigQuery public dataset (historical) + Alchemy WebSocket (real-time) - rejected LlamaRPC due to rate limits"
- Original location: `docs/llamarpc/`
- Archived: 2025-11-12
- Files: 53 (markdown docs, Python scripts, OpenAPI specifications)

---

## Archive Policy

Documentation is archived (not deleted) when:
1. Research was valuable but superseded by alternative approach
2. Historical context may be useful for future architectural decisions
3. Methodology or patterns could apply to similar investigations

Archived content is excluded from active documentation index and search.
