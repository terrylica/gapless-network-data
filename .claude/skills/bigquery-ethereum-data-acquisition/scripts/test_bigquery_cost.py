#!/usr/bin/env python3
"""
Test BigQuery Cost for 13M Ethereum Blocks

This script estimates how much data will be processed (scanned) for our query
WITHOUT actually running it or downloading anything.

BigQuery Free Tier: 1 TB query processing per month
"""

# /// script
# dependencies = ["google-cloud-bigquery"]
# ///

from google.cloud import bigquery

def estimate_query_cost():
    """Estimate bytes processed for our Ethereum blocks query."""

    print("=" * 70)
    print("BigQuery Cost Estimation for 13M Ethereum Blocks")
    print("=" * 70)
    print()

    # Initialize client (will use your gcloud credentials)
    try:
        client = bigquery.Client()
        print("✅ BigQuery client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize BigQuery client: {e}")
        print()
        print("To fix, run:")
        print("  1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install")
        print("  2. Run: gcloud auth application-default login")
        print("  3. Run this script again")
        return

    print(f"   Project: {client.project}")
    print()

    # Our query for 13M blocks (11.56M to 24M)
    # Only selecting the 6 fields we need
    query = """
    SELECT
        number AS block_number,
        timestamp,
        base_fee_per_gas AS baseFeePerGas,
        gas_used AS gasUsed,
        gas_limit AS gasLimit,
        transaction_count
    FROM `bigquery-public-data.crypto_ethereum.blocks`
    WHERE number BETWEEN 11560000 AND 24000000
    ORDER BY number
    """

    print("Query:")
    print("-" * 70)
    print(query)
    print("-" * 70)
    print()

    # Configure job to do a dry run (estimate only, don't execute)
    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)

    print("Running dry-run to estimate cost...")
    try:
        query_job = client.query(query, job_config=job_config)

        # Get the estimated bytes processed
        bytes_processed = query_job.total_bytes_processed

        # Convert to human-readable formats
        gb_processed = bytes_processed / (1024**3)
        tb_processed = bytes_processed / (1024**4)

        print()
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        print()
        print(f"Bytes to be processed: {bytes_processed:,} bytes")
        print(f"                      = {gb_processed:.2f} GB")
        print(f"                      = {tb_processed:.4f} TB")
        print()

        # Calculate cost
        FREE_TIER_TB = 1.0
        COST_PER_TB = 5.0  # $5 per TB after free tier

        print("BigQuery Free Tier Analysis:")
        print(f"  Free tier limit:  {FREE_TIER_TB} TB/month")
        print(f"  Query will use:   {tb_processed:.4f} TB")
        print(f"  Remaining quota:  {FREE_TIER_TB - tb_processed:.4f} TB")
        print()

        if tb_processed <= FREE_TIER_TB:
            print(f"✅ FITS IN FREE TIER")
            print(f"   You can run this query for FREE!")
            print(f"   Uses {tb_processed / FREE_TIER_TB * 100:.1f}% of monthly free quota")
            print()

            # Estimate how many times can run in a month
            times_per_month = int(FREE_TIER_TB / tb_processed)
            print(f"   You could run this query ~{times_per_month} times/month on free tier")
        else:
            overage = tb_processed - FREE_TIER_TB
            cost = overage * COST_PER_TB
            print(f"⚠️  EXCEEDS FREE TIER")
            print(f"   Overage: {overage:.4f} TB")
            print(f"   Cost: ${cost:.2f} (one-time)")
            print()
            print(f"   Still very cheap compared to alternatives!")

        print()
        print("=" * 70)
        print("COMPARISON WITH ALTERNATIVES")
        print("=" * 70)
        print()

        # Comparison table
        comparisons = [
            ("BigQuery", "<1 hour", f"${0 if tb_processed <= FREE_TIER_TB else (tb_processed - FREE_TIER_TB) * COST_PER_TB:.2f}", "1 TB free/month"),
            ("1RPC + Cryo", "1.9 days", "$0", "~77 RPS rate limit"),
            ("Alchemy", "26 days", "$0", "5.79 RPS rate limit"),
            ("Erigon (2TB NVMe)", "18h sync", "$200 HW", "Unlimited after sync"),
        ]

        print(f"{'Method':<20} {'Timeline':<12} {'Cost':<12} {'Notes':<25}")
        print("-" * 70)
        for method, timeline, cost, notes in comparisons:
            print(f"{method:<20} {timeline:<12} {cost:<12} {notes:<25}")

        print()
        print("=" * 70)
        print("NEXT STEPS")
        print("=" * 70)
        print()

        if tb_processed <= FREE_TIER_TB:
            print("✅ You can download 13M blocks for FREE using BigQuery!")
            print()
            print("To run the actual query:")
            print()
            print("  # Export to Parquet (recommended for DuckDB)")
            print("  bq extract --destination_format PARQUET \\")
            print("    'mydataset.ethereum_blocks' \\")
            print("    'gs://my-bucket/ethereum_blocks_*.parquet'")
            print()
            print("  # Or download directly as CSV:")
            print("  bq query --format=csv --max_rows=13000000 \\")
            print("    \"$(cat query.sql)\" > ethereum_blocks.csv")
        else:
            print(f"Query costs ${(tb_processed - FREE_TIER_TB) * COST_PER_TB:.2f}")
            print("Still much cheaper than running compute for 1.9 days!")
            print()
            print("Alternative: Use 1RPC + Cryo for completely free (but 1.9 days)")

    except Exception as e:
        print(f"❌ Error running dry-run: {e}")
        print()
        print("Common issues:")
        print("  1. Not authenticated: Run 'gcloud auth application-default login'")
        print("  2. No billing account: BigQuery requires billing enabled (but free tier is $0)")
        print("  3. API not enabled: Enable BigQuery API in console")

if __name__ == "__main__":
    estimate_query_cost()
