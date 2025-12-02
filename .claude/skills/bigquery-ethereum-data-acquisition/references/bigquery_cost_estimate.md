# BigQuery Free Tier Analysis for 13M Ethereum Blocks

## What We Know

### BigQuery Free Tier Limits (2025)

```
1 TB query processing per month (FREE)
10 GB storage per month (FREE)
$5 per TB after free tier
```

**Key Point**: The limit is on "query processing" (bytes scanned), NOT download size.

## How BigQuery Pricing Works

### What Gets Charged?

```
✅ Bytes SCANNED (columns you SELECT × rows you filter)
❌ NOT the download size
❌ NOT the result size
❌ NOT network egress (within GCP regions)
```

### Example from Research:

```sql
-- Querying crypto_ethereum.blocks with 5 columns
SELECT number, timestamp, gas_used, gas_limit, transaction_count
FROM `bigquery-public-data.crypto_ethereum.blocks`
WHERE ...

Result: 5 GB processed
```

## Our Query Analysis

### What We're Asking For:

```sql
SELECT
    number,                  -- Column 1
    timestamp,               -- Column 2
    base_fee_per_gas,       -- Column 3
    gas_used,               -- Column 4
    gas_limit,              -- Column 5
    transaction_count       -- Column 6
FROM `bigquery-public-data.crypto_ethereum.blocks`
WHERE number BETWEEN 11560000 AND 24000000  -- 12.44M blocks
```

- **Columns**: 6 (vs full table has ~25 columns)
- **Rows**: 12.44M blocks (vs ~20M total in table = 62%)

### Estimated Processing Cost

**Conservative Estimate (Worst Case)**:

```
If full table with all columns = ~100 GB
Selecting 6/25 columns = ~24 GB
For 62% of rows = ~15 GB processed

Result: ~15 GB ≪ 1 TB free tier ✅
```

**Optimistic Estimate (Best Case)**:

```
BigQuery is columnar (only scans selected columns)
6 columns × 12.44M rows × ~100 bytes/field = ~7.5 GB

Result: ~7.5 GB ≪ 1 TB free tier ✅
```

**Most Likely**: 10-20 GB processed

## Free Tier Verdict

### Fits in Free Tier? ✅ YES

```
Free tier:           1,000 GB/month
Estimated usage:     10-20 GB
Remaining:           980-990 GB

You can run this query ~50-100 times per month for FREE
```

## Comparison with Alternatives

| Method       | Timeline      | Data Processing  | Cost    | Rate Limits                         |
| ------------ | ------------- | ---------------- | ------- | ----------------------------------- |
| **BigQuery** | **<1 hour**   | Google's servers | **$0**  | 1 TB/month (enough for 50-100 runs) |
| 1RPC + Cryo  | 1.9 days      | Your machine     | $0      | 77 RPS (may change)                 |
| Alchemy      | 26 days       | Your machine     | $0      | 5.79 RPS                            |
| Erigon       | 18h + instant | Your machine     | $200 HW | Unlimited (after sync)              |

## The Key Insight

**BigQuery's "free tier" is about PROCESSING, not RESULTS**:

```
What matters: How much data BigQuery SCANS
What doesn't: How much data YOU download

Analogy:
- You ask a librarian to find 13M specific pages (BigQuery scans ~15 GB)
- Librarian photocopies them for you (~100 GB download)
- You pay for librarian's WORK (scanning), not paper (download)
- First 1 TB of librarian's work is FREE
```

## To Confirm Empirically

Run this to get EXACT cost BEFORE executing:

```bash
# Install BigQuery CLI (if needed)
curl https://sdk.cloud.google.com | bash
gcloud init

# Dry-run query (no data downloaded, just estimates cost)
bq query --dry_run --use_legacy_sql=false \
  'SELECT number, timestamp, base_fee_per_gas, gas_used, gas_limit, transaction_count
   FROM `bigquery-public-data.crypto_ethereum.blocks`
   WHERE number BETWEEN 11560000 AND 24000000'

# Output will show: "Query will process X bytes"
```

**Or use Python script**: `/tmp/test_bigquery_cost.py`

## Expected Output

```
Query will process: 15,234,567,890 bytes
                  = 14.19 GB
                  = 0.0139 TB

✅ FITS IN FREE TIER (1 TB/month)
Uses 1.4% of monthly free quota
You can run this query ~70 times/month for FREE
```

## Bottom Line

**Q**: "Does BigQuery free tier support downloading 13M blocks?"

**A**: **YES** - with high confidence:

- Estimated: 10-20 GB processing ≪ 1,000 GB free tier
- You can run this query 50-100 times per month on free tier
- Processing is what matters, not download size
- Google pre-indexed everything, you just query + download

**The constraint is PROCESSING (1 TB/month), not download bandwidth.**

---

## Next Step: Empirical Validation

Run the test script to get EXACT number:

```bash
# On littleblack or your Mac
cd /tmp
uv run test_bigquery_cost.py

# This will show exact GB processed WITHOUT running query
# Takes <5 seconds, downloads nothing
```

If you don't have gcloud set up:

```bash
# Option 1: Quick setup
curl https://sdk.cloud.google.com | bash
gcloud init  # Follow prompts (free account)
gcloud auth application-default login

# Option 2: Use web console
# Go to: console.cloud.google.com/bigquery
# Paste query → Click "Validate" button
# Shows "This query will process X GB"
```
