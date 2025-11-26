# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "duckdb",
#     "google-cloud-storage>=2.14.0",
#     "google-cloud-secret-manager>=2.21.0",
# ]
# ///
"""
Archive MotherDuck Data to GCS (Phase 4.3)

Exports all MotherDuck data to Parquet files in Google Cloud Storage
before deprecating MotherDuck. This provides a 30-day backup for emergency recovery.

Usage:
    doppler run --project aws-credentials --config prd -- uv run scripts/clickhouse/archive_motherduck_to_gcs.py

Output:
    gs://eonlabs-ethereum-backups/motherduck-archive/YYYY-MM-DD/blocks.parquet
"""

import os
import sys
from datetime import datetime, timezone

import duckdb
from google.cloud import storage


def get_secret(secret_id: str, project_id: str = "eonlabs-ethereum-bq") -> str:
    """Fetch secret from Google Secret Manager."""
    from google.cloud import secretmanager
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8').strip()


def main():
    print("=" * 70)
    print("MotherDuck → GCS Archive (Phase 4.3)")
    print("=" * 70)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()

    # Configuration
    bucket_name = "eonlabs-ethereum-backups"
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    archive_prefix = f"motherduck-archive/{date_str}"

    # Connect to MotherDuck
    print("[1/4] Connecting to MotherDuck...")
    token = os.environ.get("motherduck_token")
    if not token:
        token = get_secret("motherduck-token")
    conn = duckdb.connect(f"md:ethereum_mainnet?motherduck_token={token}")
    print("  ✅ Connected to MotherDuck")

    # Get row count
    print("[2/4] Querying data stats...")
    result = conn.execute("""
        SELECT COUNT(*) as total, MIN(number) as min_block, MAX(number) as max_block
        FROM blocks
    """).fetchone()
    total_rows, min_block, max_block = result
    print(f"  Total rows: {total_rows:,}")
    print(f"  Block range: {min_block:,} - {max_block:,}")

    # Export to local Parquet file (temporary)
    print("[3/4] Exporting to Parquet...")
    local_file = f"/tmp/motherduck_blocks_{date_str}.parquet"
    conn.execute(f"""
        COPY (SELECT * FROM blocks ORDER BY number)
        TO '{local_file}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)

    import os as os_module
    file_size = os_module.path.getsize(local_file)
    print(f"  ✅ Exported to {local_file}")
    print(f"  File size: {file_size / (1024 * 1024):.1f} MB")

    # Upload to GCS
    print(f"[4/4] Uploading to gs://{bucket_name}/{archive_prefix}/blocks.parquet...")

    # Initialize GCS client
    gcs_client = storage.Client(project="eonlabs-ethereum-bq")

    # Check if bucket exists, create if not
    try:
        bucket = gcs_client.get_bucket(bucket_name)
    except Exception:
        print(f"  Creating bucket {bucket_name}...")
        bucket = gcs_client.create_bucket(bucket_name, location="US")

    # Upload file
    blob = bucket.blob(f"{archive_prefix}/blocks.parquet")
    blob.upload_from_filename(local_file)

    print(f"  ✅ Uploaded to gs://{bucket_name}/{archive_prefix}/blocks.parquet")

    # Cleanup local file
    os_module.remove(local_file)
    print(f"  ✅ Cleaned up local file")

    # Create metadata file
    metadata = f"""# MotherDuck Archive Metadata
Date: {datetime.now(timezone.utc).isoformat()}
Total Rows: {total_rows:,}
Block Range: {min_block:,} - {max_block:,}
Format: Parquet (ZSTD compression)
Retention: 30 days
Purpose: Emergency recovery backup before MotherDuck deprecation
"""
    metadata_blob = bucket.blob(f"{archive_prefix}/METADATA.txt")
    metadata_blob.upload_from_string(metadata)
    print(f"  ✅ Created metadata file")

    print()
    print("=" * 70)
    print("✅ ARCHIVE COMPLETE")
    print("=" * 70)
    print(f"Location: gs://{bucket_name}/{archive_prefix}/")
    print(f"Files: blocks.parquet, METADATA.txt")
    print(f"Retention: 30 days")
    print()
    print("Next steps:")
    print("  1. Deploy cutover (MOTHERDUCK_WRITE_ENABLED=false)")
    print("  2. Verify ClickHouse is receiving new blocks")
    print("  3. Delete MotherDuck database after trial ends")

    return 0


if __name__ == "__main__":
    sys.exit(main())
