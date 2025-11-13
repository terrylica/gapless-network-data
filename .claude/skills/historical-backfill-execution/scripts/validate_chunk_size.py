#!/usr/bin/env python3
"""
/// script
/// dependencies = []
///

Validate memory requirements for historical backfill chunk execution.

Usage:
    python validate_chunk_size.py --year 2020
    python validate_chunk_size.py --start 2015 --end 2025
"""

import argparse
import sys

# Constants
BLOCKS_PER_YEAR_AVG = 2_600_000  # Ethereum average blocks per year
BYTES_PER_BLOCK = 100  # Conservative estimate (76-100 bytes empirically validated)
COLUMNS = 11  # Optimized schema (vs 23 columns in full BigQuery table)
CLOUD_RUN_MEMORY_LIMIT_GB = 4  # Default Cloud Run memory limit
SAFETY_MARGIN = 0.8  # Use 80% of limit to account for overhead


def estimate_memory_gb(block_count: int) -> float:
    """Estimate memory usage in GB for given block count."""
    bytes_total = block_count * BYTES_PER_BLOCK * COLUMNS
    gb = bytes_total / (1024 ** 3)
    return gb


def validate_chunk(start_year: int, end_year: int) -> dict:
    """Validate memory requirements for year range."""
    year_count = end_year - start_year + 1
    block_count = BLOCKS_PER_YEAR_AVG * year_count
    memory_gb = estimate_memory_gb(block_count)
    safe_limit = CLOUD_RUN_MEMORY_LIMIT_GB * SAFETY_MARGIN

    return {
        "start_year": start_year,
        "end_year": end_year,
        "year_count": year_count,
        "block_count": block_count,
        "memory_gb": memory_gb,
        "safe_limit_gb": safe_limit,
        "cloud_run_safe": memory_gb <= safe_limit,
        "memory_percentage": (memory_gb / CLOUD_RUN_MEMORY_LIMIT_GB) * 100
    }


def main():
    parser = argparse.ArgumentParser(description="Validate historical backfill chunk size")
    parser.add_argument("--year", type=int, help="Single year to validate")
    parser.add_argument("--start", type=int, help="Start year (inclusive)")
    parser.add_argument("--end", type=int, help="End year (inclusive)")

    args = parser.parse_args()

    # Determine year range
    if args.year:
        start_year = args.year
        end_year = args.year
    elif args.start and args.end:
        start_year = args.start
        end_year = args.end
    else:
        print("Error: Specify either --year or --start and --end")
        sys.exit(1)

    # Validate inputs
    if start_year > end_year:
        print(f"Error: Start year ({start_year}) must be <= end year ({end_year})")
        sys.exit(1)

    # Estimate memory
    print(f"=== Memory Validation for {start_year}-{end_year} ===")
    print()

    result = validate_chunk(start_year, end_year)

    print(f"Year range: {result['start_year']} → {result['end_year']} ({result['year_count']} years)")
    print(f"Estimated blocks: ~{result['block_count']:,}")
    print(f"Column count: {COLUMNS} (optimized schema)")
    print()
    print(f"Expected memory: {result['memory_gb']:.2f} GB")
    print(f"Cloud Run limit: {CLOUD_RUN_MEMORY_LIMIT_GB} GB")
    print(f"Safe limit (80%): {result['safe_limit_gb']:.2f} GB")
    print(f"Memory usage: {result['memory_percentage']:.1f}%")
    print()

    if result['cloud_run_safe']:
        print("✅ Cloud Run safe (under safety margin)")
        print()
        print("Recommended action: Proceed with backfill")
        sys.exit(0)
    else:
        print("❌ Cloud Run unsafe (exceeds safety margin)")
        print()
        print("Recommended actions:")
        print("1. Reduce chunk size (use smaller year range)")
        print("2. Increase Cloud Run memory allocation (8GB)")
        print("3. Use 6-month chunks instead of 1-year")
        print()

        # Calculate recommended chunk size
        years_recommended = int(result['safe_limit_gb'] / estimate_memory_gb(BLOCKS_PER_YEAR_AVG))
        print(f"Recommended chunk size: {years_recommended} year(s)")
        sys.exit(1)


if __name__ == "__main__":
    main()
