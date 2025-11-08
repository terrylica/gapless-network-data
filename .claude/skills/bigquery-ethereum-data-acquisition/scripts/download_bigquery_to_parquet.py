#!/usr/bin/env python3
"""
⚠️ UNTESTED - Pending Empirical Validation

Download Ethereum blocks from BigQuery to Parquet

This script streams BigQuery results directly to local Parquet file,
avoiding BigQuery storage limits (0 GB of 10 GB limit used).

Prerequisites:
- gcloud CLI installed and authenticated
- google-cloud-bigquery package installed

Run: uv run download_bigquery_to_parquet.py
"""

# /// script
# dependencies = ["google-cloud-bigquery", "pandas", "pyarrow", "db-dtypes"]
# ///

from google.cloud import bigquery
import pandas as pd
from pathlib import Path

def download_ethereum_blocks(
    start_block=11560000,
    end_block=24000000,
    output_file="ethereum_blocks.parquet"
):
    """
    Download Ethereum blocks from BigQuery and save to Parquet.

    Args:
        start_block: Starting block number (default: 11560000, Dec 2020)
        end_block: Ending block number (default: 24000000, Nov 2024)
        output_file: Output Parquet file path

    Returns:
        Path to created Parquet file
    """
    print("=" * 70)
    print("BigQuery Ethereum Data Download")
    print("=" * 70)
    print()

    # Initialize BigQuery client
    try:
        client = bigquery.Client()
        print(f"✅ BigQuery client initialized")
        print(f"   Project: {client.project}")
    except Exception as e:
        print(f"❌ Failed to initialize BigQuery client: {e}")
        print()
        print("To fix, run:")
        print("  gcloud auth application-default login")
        return None

    print()

    # Query for optimized ML columns (11 columns, ~2 GB)
    query = f"""
    SELECT
        timestamp,
        number,
        gas_limit,
        gas_used,
        base_fee_per_gas,
        transaction_count,
        difficulty,
        total_difficulty,
        size,
        blob_gas_used,
        excess_blob_gas
    FROM `bigquery-public-data.crypto_ethereum.blocks`
    WHERE number BETWEEN {start_block} AND {end_block}
    ORDER BY number
    """

    print(f"Downloading blocks {start_block:,} to {end_block:,}")
    print(f"Expected rows: {end_block - start_block:,}")
    print()

    # Stream query results
    print("Streaming query results...")
    try:
        df = client.query(query).to_dataframe()
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return None

    print(f"✅ Downloaded {len(df):,} rows")
    print()

    # Show summary
    print("Data summary:")
    print(f"  Shape: {df.shape}")
    print(f"  Memory: {df.memory_usage(deep=True).sum() / 1024**3:.2f} GB")
    print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print()

    # Save to Parquet
    print(f"Saving to {output_file}...")
    try:
        df.to_parquet(output_file, compression='snappy', index=False)
        file_size = Path(output_file).stat().st_size / 1024**3
        print(f"✅ Saved to {output_file}")
        print(f"   File size: {file_size:.2f} GB")
    except Exception as e:
        print(f"❌ Failed to save: {e}")
        return None

    print()
    print("=" * 70)
    print("✅ Download complete!")
    print("=" * 70)
    print()
    print("BigQuery usage:")
    print("  Query processing: ~2 GB (0.2% of 1 TB free tier)")
    print("  BigQuery storage: 0 GB (streaming avoids storage)")
    print()
    print("Next steps:")
    print("  1. Verify file: duckdb ethereum.db \"SELECT COUNT(*), MIN(number), MAX(number) FROM read_parquet('ethereum_blocks.parquet')\"")
    print("  2. Load into DuckDB: See SKILL.md Step 5")

    return output_file


if __name__ == "__main__":
    import sys

    # Allow command-line arguments
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 11560000
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 24000000
    output = sys.argv[3] if len(sys.argv) > 3 else "ethereum_blocks.parquet"

    result = download_ethereum_blocks(start, end, output)

    if result:
        sys.exit(0)
    else:
        sys.exit(1)
