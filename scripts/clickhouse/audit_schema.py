# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "clickhouse-connect>=0.7.0",
# ]
# ///
"""
Audit ClickHouse schema for compression metrics and storage statistics.

ADR: 2025-12-10-clickhouse-codec-optimization

Usage:
    # Baseline (before migration)
    doppler run --project aws-credentials --config prd -- \
        uv run scripts/clickhouse/audit_schema.py --output tmp/clickhouse-audit-baseline.json

    # Post-migration
    doppler run --project aws-credentials --config prd -- \
        uv run scripts/clickhouse/audit_schema.py --output tmp/clickhouse-audit-post.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def audit_schema(output_path: str | None = None) -> dict:
    """Audit ClickHouse schema and collect metrics."""
    import clickhouse_connect

    host = os.environ.get("CLICKHOUSE_HOST")
    port = int(os.environ.get("CLICKHOUSE_PORT", "8443"))
    user = os.environ.get("CLICKHOUSE_USER", "default")
    password = os.environ.get("CLICKHOUSE_PASSWORD")

    if not host or not password:
        print("ERROR: Missing CLICKHOUSE_HOST or CLICKHOUSE_PASSWORD")
        sys.exit(1)

    print(f"Connecting to ClickHouse Cloud...")
    print(f"  Host: {host}")
    print()

    client = clickhouse_connect.get_client(
        host=host,
        port=port,
        username=user,
        password=password,
        secure=True,
        connect_timeout=30,
    )

    audit_result = {
        "timestamp": datetime.now().isoformat(),
        "host": host,
        "database": "ethereum_mainnet",
        "table": "blocks",
    }

    # 1. Row count
    print("Fetching row count...")
    result = client.query("SELECT COUNT(*) FROM ethereum_mainnet.blocks FINAL")
    row_count = result.result_rows[0][0]
    audit_result["row_count"] = row_count
    print(f"  Row count: {row_count:,}")

    # 2. Table size (compressed and uncompressed)
    print("\nFetching table size...")
    size_query = """
    SELECT
        formatReadableSize(sum(data_compressed_bytes)) AS compressed_size,
        formatReadableSize(sum(data_uncompressed_bytes)) AS uncompressed_size,
        sum(data_compressed_bytes) AS compressed_bytes,
        sum(data_uncompressed_bytes) AS uncompressed_bytes,
        round(sum(data_uncompressed_bytes) / sum(data_compressed_bytes), 2) AS compression_ratio
    FROM system.parts
    WHERE database = 'ethereum_mainnet' AND table = 'blocks' AND active = 1
    """
    result = client.query(size_query)
    row = result.result_rows[0]
    audit_result["storage"] = {
        "compressed_size": row[0],
        "uncompressed_size": row[1],
        "compressed_bytes": row[2],
        "uncompressed_bytes": row[3],
        "compression_ratio": row[4],
    }
    print(f"  Compressed: {row[0]}")
    print(f"  Uncompressed: {row[1]}")
    print(f"  Compression ratio: {row[4]}x")

    # 3. Column-level compression stats
    print("\nFetching column compression stats...")
    column_query = """
    SELECT
        column,
        type,
        formatReadableSize(sum(column_data_compressed_bytes)) AS compressed,
        formatReadableSize(sum(column_data_uncompressed_bytes)) AS uncompressed,
        sum(column_data_compressed_bytes) AS compressed_bytes,
        sum(column_data_uncompressed_bytes) AS uncompressed_bytes,
        round(sum(column_data_uncompressed_bytes) / nullIf(sum(column_data_compressed_bytes), 0), 2) AS ratio
    FROM system.parts_columns
    WHERE database = 'ethereum_mainnet' AND table = 'blocks' AND active = 1
    GROUP BY column, type
    ORDER BY compressed_bytes DESC
    """
    result = client.query(column_query)
    columns = []
    print(f"\n  {'Column':<22} {'Type':<20} {'Compressed':<12} {'Ratio':<8}")
    print("  " + "-" * 65)
    for row in result.result_rows:
        col_info = {
            "name": row[0],
            "type": row[1],
            "compressed": row[2],
            "uncompressed": row[3],
            "compressed_bytes": row[4],
            "uncompressed_bytes": row[5],
            "ratio": row[6],
        }
        columns.append(col_info)
        print(f"  {row[0]:<22} {row[1]:<20} {row[2]:<12} {row[6] or 0:.1f}x")
    audit_result["columns"] = columns

    # 4. Projections
    print("\nFetching projections...")
    proj_query = """
    SELECT name
    FROM system.projections
    WHERE database = 'ethereum_mainnet' AND table = 'blocks'
    """
    try:
        result = client.query(proj_query)
        projections = []
        if result.result_rows:
            for row in result.result_rows:
                projections.append({"name": row[0]})
                print(f"  {row[0]}")
        else:
            print("  (none)")
        audit_result["projections"] = projections
    except Exception:
        # system.projections may not exist in all versions
        print("  (query failed - no projections table)")
        audit_result["projections"] = []

    # 5. Sample query latencies
    print("\nBenchmarking queries...")
    queries = [
        ("limit_10000", "SELECT * FROM ethereum_mainnet.blocks FINAL ORDER BY number DESC LIMIT 10000"),
        ("date_range_jan_2024", "SELECT * FROM ethereum_mainnet.blocks FINAL WHERE timestamp >= '2024-01-01' AND timestamp < '2024-02-01'"),
        ("count_all", "SELECT COUNT(*) FROM ethereum_mainnet.blocks FINAL"),
    ]

    latencies = {}
    for name, query in queries:
        # Warmup
        client.query(query)
        # Measure
        import time
        start = time.time()
        client.query(query)
        elapsed = time.time() - start
        latencies[name] = round(elapsed, 3)
        print(f"  {name}: {elapsed:.3f}s")

    audit_result["query_latencies_seconds"] = latencies

    # 6. Engine and settings
    print("\nFetching table settings...")
    settings_query = """
    SELECT
        engine_full,
        sorting_key,
        partition_key
    FROM system.tables
    WHERE database = 'ethereum_mainnet' AND name = 'blocks'
    """
    result = client.query(settings_query)
    if result.result_rows:
        row = result.result_rows[0]
        audit_result["engine"] = {
            "engine_full": row[0],
            "sorting_key": row[1],
            "partition_key": row[2],
        }
        print(f"  Engine: {row[0][:50]}...")
        print(f"  Sorting key: {row[1]}")
        print(f"  Partition key: {row[2]}")

    # Save to file
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(audit_result, f, indent=2)
        print(f"\n✅ Audit saved to: {output_file}")

    print("\n" + "=" * 50)
    print("AUDIT COMPLETE")
    print("=" * 50)

    return audit_result


def main():
    parser = argparse.ArgumentParser(description="Audit ClickHouse schema")
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path (e.g., tmp/clickhouse-audit-baseline.json)"
    )
    args = parser.parse_args()

    audit_schema(args.output)


if __name__ == "__main__":
    main()
