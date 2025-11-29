#!/usr/bin/env python3
# /// script
# dependencies = ["google-cloud-secret-manager", "requests", "clickhouse-connect"]
# ///
"""
Data Quality Checker (ClickHouse)

Queries ClickHouse for latest block timestamp and verifies data freshness.
Designed to run as a Cloud Run Job triggered by Cloud Scheduler every 5 minutes.

Environment Variables:
    GCP_PROJECT: GCP project ID (default: eonlabs-ethereum-bq)
    STALE_THRESHOLD_SECONDS: Maximum age before alert (default: 600)
    CLICKHOUSE_HOST: ClickHouse Cloud host (from Secret Manager if not set)
    CLICKHOUSE_PASSWORD: ClickHouse password (from Secret Manager if not set)

Exit Codes:
    0: Data is fresh (<600s old)
    1: Data is stale (>600s old) or query failed
"""

import os
import sys
from datetime import datetime, timezone

import clickhouse_connect
import requests
from google.cloud import secretmanager


# Configuration
GCP_PROJECT = os.environ.get('GCP_PROJECT', 'eonlabs-ethereum-bq')
STALE_THRESHOLD_SECONDS = int(os.environ.get('STALE_THRESHOLD_SECONDS', '600'))

# ClickHouse configuration
CLICKHOUSE_DATABASE = 'ethereum_mainnet'
CLICKHOUSE_TABLE = 'blocks'


def get_secret(secret_id: str, project_id: str = GCP_PROJECT) -> str:
    """Fetch secret from Google Secret Manager.

    Args:
        secret_id: Secret name (e.g., 'clickhouse-host')
        project_id: GCP project ID

    Returns:
        Secret value as string

    Raises:
        Exception: If secret fetch fails
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8').strip()


def check_clickhouse_freshness():
    """Query ClickHouse and verify data freshness.

    Returns:
        Tuple of (is_fresh: bool, diagnostic_message: str)

    Raises:
        Exception: If query fails
    """
    # Get credentials from env or Secret Manager
    host = os.environ.get('CLICKHOUSE_HOST')
    password = os.environ.get('CLICKHOUSE_PASSWORD')

    if not host:
        host = get_secret('clickhouse-host')
    if not password:
        password = get_secret('clickhouse-password')

    print(f"[1/3] Connecting to ClickHouse: {host}")

    client = clickhouse_connect.get_client(
        host=host,
        port=8443,
        username='default',
        password=password,
        secure=True,
        connect_timeout=30,
    )

    print(f"[2/3] Querying {CLICKHOUSE_DATABASE}.{CLICKHOUSE_TABLE}")

    result = client.query("""
        SELECT MAX(number), MAX(timestamp), COUNT(*)
        FROM ethereum_mainnet.blocks FINAL
    """)

    row = result.result_rows[0]
    if row[0] is None:
        raise ValueError("No blocks found in ClickHouse")

    latest_block = row[0]
    latest_timestamp = row[1]
    total_blocks = row[2]

    # Calculate staleness
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    age_seconds = (now - latest_timestamp).total_seconds()

    print(f"   Latest block: {latest_block:,}")
    print(f"   Latest timestamp: {latest_timestamp}")
    print(f"   Total blocks: {total_blocks:,}")
    print(f"   Age: {age_seconds:.1f} seconds")

    is_fresh = age_seconds <= STALE_THRESHOLD_SECONDS

    if is_fresh:
        diagnostic_msg = f"FRESH: Block {latest_block:,}, {age_seconds:.0f}s old"
    else:
        diagnostic_msg = f"STALE: Block {latest_block:,}, {age_seconds/60:.1f} min old (threshold: {STALE_THRESHOLD_SECONDS}s)"

    return is_fresh, diagnostic_msg


def ping_healthcheck(diagnostic_msg: str, is_fresh: bool):
    """Ping Healthchecks.io with diagnostic data.

    Args:
        diagnostic_msg: Diagnostic message to send
        is_fresh: Whether data is fresh

    Raises:
        requests.HTTPError: If ping fails
    """
    print("[3/3] Pinging Healthchecks.io...")

    healthcheck_url = get_secret('healthchecks-data-quality-url')

    # Use /fail endpoint if data is stale
    ping_url = f"{healthcheck_url}/fail" if not is_fresh else healthcheck_url

    response = requests.post(ping_url, data=diagnostic_msg, timeout=10)
    response.raise_for_status()

    print(f"   Pinged {ping_url}")
    print(f"   {diagnostic_msg}")


def main():
    """Entry point."""
    print("=" * 80)
    print("Data Quality Checker (ClickHouse)")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}")
    print(f"Database: {CLICKHOUSE_DATABASE}.{CLICKHOUSE_TABLE}")
    print(f"Stale threshold: {STALE_THRESHOLD_SECONDS}s")
    print("=" * 80)
    print()

    try:
        # Check ClickHouse freshness
        is_fresh, diagnostic_msg = check_clickhouse_freshness()
        ping_healthcheck(diagnostic_msg, is_fresh)

        if is_fresh:
            print("\nData quality check PASSED")
            return 0
        else:
            print("\nData quality check FAILED (stale data)")
            return 1

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

        # Ping Healthchecks.io /fail (best-effort)
        try:
            healthcheck_url = get_secret('healthchecks-data-quality-url')
            requests.post(
                f"{healthcheck_url}/fail",
                data=f"Fatal error: {e.__class__.__name__}: {e}",
                timeout=10
            )
            print(f"   Pinged Healthchecks.io /fail")
        except Exception as ping_error:
            print(f"   Failed to ping Healthchecks.io: {ping_error}")

        return 1


if __name__ == "__main__":
    sys.exit(main())
