# Claude Code Skills - Operational Helpers

This directory contains validated workflows for operating and monitoring the gapless-network-data infrastructure.

## Execution Model

**These scripts run LOCALLY** (on developer laptops) but may query cloud resources:

```
Local Execution → Cloud API Query → Local Analysis
```

**Examples**:
- `data-pipeline-monitoring/scripts/check_pipeline_health.py`: Runs locally, queries `gcloud` APIs
- `scripts/clickhouse/verify_blocks.py`: Runs locally, queries ClickHouse Cloud
- `bigquery-ethereum-data-acquisition/scripts/estimate_query_cost.py`: Runs locally, queries BigQuery

## Distinction from deployment/

| Directory | Purpose | Execution | Provisioning |
|-----------|---------|-----------|--------------|
| `deployment/` | Infrastructure code that **runs ON cloud** (Cloud Run, VM) | Cloud services | Provisions cloud resources |
| `.claude/skills/` | Operational helpers that **run locally** (monitoring, verification) | Local laptop | Queries cloud APIs |

**Key difference**: `deployment/` scripts are deployed to cloud infrastructure. Skills scripts run locally for operational tasks.

## Authentication

Skills scripts use local credentials:
- `gcloud auth login` (for GCP APIs)
- `doppler login` or Secret Manager (for third-party APIs)
- ClickHouse credentials via Doppler (`aws-credentials/prd`)

No deployment or cloud execution required.

## Skills Categories

### 1. Infrastructure Monitoring
- **data-pipeline-monitoring**: Check pipeline health, view logs, send alerts
- Queries: Cloud Run Jobs, Compute Engine VMs, Cloud Logging

### 2. Database Operations
- **historical-backfill-execution**: Execute chunked backfills, verify completeness
- Queries: ClickHouse Cloud database (`ethereum_mainnet.blocks`)

### 3. Data Source Research
- **blockchain-rpc-provider-research**: Evaluate RPC providers, validate rate limits
- **blockchain-data-collection-validation**: Build POC collectors, test pipelines
- **bigquery-ethereum-data-acquisition**: Query cost estimation, column selection

### 4. System Validation
- **mlflow-query**: Query MLflow experiments (if integrated)
- **code-clone-assistant**: Detect code duplication

## Usage Pattern

All skills follow this pattern:

1. **Run locally** on developer machine
2. **Query cloud APIs** for data/status
3. **Analyze results locally** and present findings

No cloud deployment, no infrastructure changes, no production impact.

## Adding New Skills

Skills should:
- Document execution environment (local)
- Specify cloud resources queried (if any)
- Include authentication requirements
- Provide clear usage examples

See existing skills for patterns.
