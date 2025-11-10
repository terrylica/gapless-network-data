# Historical Ethereum Data Backfill (2020-2025)

One-time backfill script to load 5 years of historical Ethereum blocks from BigQuery to MotherDuck.

## Files

- `historical_backfill.py` - Python script for bulk historical data loading

## Prerequisites

1. GCP project configured: `eonlabs-ethereum-bq`
2. Secrets stored in Secret Manager:
   - `motherduck-token`
3. Service account has permissions:
   - `roles/secretmanager.secretAccessor`
   - `roles/bigquery.user`
4. BigQuery API enabled
5. MotherDuck database created: `ethereum_mainnet`

## Execution

### Default (2020-2025):

```bash
cd deployment/backfill
uv run historical_backfill.py
```

### Custom date range:

```bash
uv run historical_backfill.py --start-year 2022 --end-year 2024
```

### Dry run (show query without executing):

```bash
uv run historical_backfill.py --dry-run
```

## Expected Performance

**Data volume**:

- 2020-2025: ~14.57M blocks (actual: 14,576,959 as of 2025-11-10)
- Storage size: ~1.5 GB in MotherDuck

**Execution time**: ~30-60 minutes

- BigQuery query: ~30s
- MotherDuck insert: ~30-45 minutes

**Cost**: $0 (within BigQuery and MotherDuck free tiers)

## Data Flow

```
BigQuery Public Dataset (bigquery-public-data.crypto_ethereum.blocks)
    ↓ (PyArrow zero-copy)
MotherDuck (ethereum_mainnet.blocks)
```

**Deduplication**: Uses `INSERT OR REPLACE` based on block number (PRIMARY KEY)

## Configuration

Environment variables (optional):

- `GCP_PROJECT`: GCP project ID (default: `eonlabs-ethereum-bq`)
- `MD_DATABASE`: MotherDuck database name (default: `ethereum_mainnet`)
- `MD_TABLE`: MotherDuck table name (default: `blocks`)
- `START_YEAR`: Start year (default: `2020`)
- `END_YEAR`: End year (default: `2025`)

## Schema

11 columns optimized for ML feature engineering:

- `timestamp` (TIMESTAMP)
- `number` (BIGINT, PRIMARY KEY)
- `gas_limit` (BIGINT)
- `gas_used` (BIGINT)
- `base_fee_per_gas` (BIGINT)
- `transaction_count` (BIGINT)
- `difficulty` (HUGEINT)
- `total_difficulty` (HUGEINT)
- `size` (BIGINT)
- `blob_gas_used` (BIGINT)
- `excess_blob_gas` (BIGINT)

## Monitoring

The script outputs progress to stdout:

1. Fetch phase: Shows block range and count
2. Load phase: Shows insertion rate (blocks/sec)
3. Verification: Shows total blocks and block range in MotherDuck

## Error Handling

The script raises and propagates all errors (exception-only failures):

- BigQuery query errors
- Secret Manager access errors
- MotherDuck connection errors
- Data validation errors

No retries, no fallbacks, no silent failures.

## Security

- No secrets in script or environment variables
- All credentials fetched from Secret Manager at runtime
- `.strip()` applied to secrets to prevent gRPC metadata validation errors

## One-Time Execution

This script is designed for one-time use. After initial backfill:

1. Real-time collector (VM) handles new blocks (~12s intervals)
2. Hourly sync (Cloud Run) handles any gaps
3. Re-running is safe (idempotent due to `INSERT OR REPLACE`)
