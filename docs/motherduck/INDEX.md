---
version: "1.0.0"
last_updated: "2025-11-08"
---

# MotherDuck Integration Documentation

MotherDuck is a serverless cloud analytics platform built on DuckDB. It enables collaborative analytics with cloud storage while maintaining DuckDB's performance characteristics.

## Overview

MotherDuck provides:
- **Cloud DuckDB**: Serverless analytics without managing infrastructure
- **Data Sharing**: Collaborate with team members on shared databases
- **Hybrid Execution**: Combine local and cloud compute
- **Zero ETL**: Direct queries against cloud data sources

## Documentation

### Integration Guides

- [BigQuery Integration](bigquery-integration.md) - Load data from Google BigQuery to MotherDuck
  - Using `duckdb-bigquery` community extension
  - Using Google Cloud BigQuery Python SDK
  - Python end-to-end pipeline example

## Use Cases for gapless-network-data

### Cloud Storage Alternative

Instead of storing 760 MB Ethereum block data locally or in S3:

**Traditional approach**:
```
BigQuery → Local Parquet → DuckDB (local)
         ↓
      760 MB local storage required
```

**MotherDuck approach**:
```
BigQuery → MotherDuck (cloud DuckDB)
         ↓
      0 MB local storage required
      Query from anywhere
```

### Benefits

1. **No Local Storage**: 760 MB Parquet file → 0 MB (data lives in MotherDuck)
2. **Multi-Machine Access**: Query from any machine with internet
3. **Team Collaboration**: Share databases with collaborators
4. **Automatic Backups**: MotherDuck handles redundancy
5. **DuckDB Performance**: Same SQL queries, cloud execution

### Pricing

- **Free Tier**: Available for individual use
- **Storage**: Pay for what you store (competitive with S3/GCS)
- **Compute**: Pay for query execution time

See [MotherDuck Pricing](https://motherduck.com/pricing) for current rates.

## Getting Started

### 1. Sign Up

Create a MotherDuck account at [motherduck.com](https://motherduck.com)

### 2. Get Token

```bash
# Set environment variable
export motherduck_token='your_token_here'
```

### 3. Connect from DuckDB

```python
import duckdb

# Connect to MotherDuck
conn = duckdb.connect('md:')

# Create database
conn.sql("CREATE DATABASE IF NOT EXISTS gapless_network_data")
conn.sql("USE gapless_network_data")
```

### 4. Load Data from BigQuery

See [BigQuery Integration](bigquery-integration.md) for complete workflow.

## Related Resources

- [MotherDuck Official Docs](https://motherduck.com/docs)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [BigQuery Public Datasets](https://cloud.google.com/bigquery/public-data)

## Project Integration

**Master Roadmap**: Phase 1 can optionally use MotherDuck instead of local DuckDB:

```yaml
# Option 1: Local DuckDB (current plan)
storage: ~/.cache/gapless-network-data/data.duckdb
size: ~1.5 GB local

# Option 2: MotherDuck (cloud alternative)
storage: md:gapless_network_data
size: 0 GB local (data in cloud)
```

Both options support the same SQL queries and DuckDB features (ASOF JOIN, window functions, time_bucket).
