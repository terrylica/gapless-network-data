# BigQuery Ethereum Data Acquisition - Research References

This directory contains detailed research documents from parallel agent investigation (2025-11-06).

## File Locations

**All research files are in `/tmp/` and symlinked here:**

1. **bigquery_cost_comparison.md** → `/tmp/bigquery_cost_comparison.md`
   - Empirical cost analysis comparing 6, 11, and 23 column queries
   - Shows 94% storage waste when including hash fields

2. **ethereum_columns_ml_evaluation.md** → `/tmp/ethereum_columns_ml_evaluation.md`
   - Column-by-column ML/time series forecasting value analysis
   - **Critical reference** for feature engineering decisions

3. **bigquery_complete_ethereum_data.md** → `/tmp/bigquery_complete_ethereum_data.md`
   - Complete catalog of 11 tables in crypto_ethereum dataset
   - Transaction aggregation strategies

4. **bigquery_cost_estimate.md** → `/tmp/bigquery_cost_estimate.md`
   - Free tier limits explanation (1 TB query vs 10 GB storage)
   - Calculation methodology

5. **littleblack-hardware-report.md** → `/tmp/littleblack-hardware-report.md`
   - Local workstation vs cloud comparison
   - Erigon node requirements analysis

## How to Use

Load these references as needed during workflow execution. Key documents:

- **Start here**: `bigquery_cost_comparison.md` (executive summary)
- **For column selection**: `ethereum_columns_ml_evaluation.md`
- **For exploring other tables**: `bigquery_complete_ethereum_data.md`

## Empirical Validation Status

**✅ TESTED**: All cost measurements in these documents were empirically validated with `bq query --dry_run`

**⚠️ UNTESTED**: Download workflows have not been executed yet
