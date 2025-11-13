#!/usr/bin/env python3
# /// script
# dependencies = ["duckdb", "google-cloud-secret-manager", "requests"]
# ///
"""
MotherDuck Data Quality Checker

Queries MotherDuck for latest block timestamp and verifies data freshness.
Designed to run as a Cloud Run Job triggered by Cloud Scheduler every 5 minutes.

Environment Variables:
    GCP_PROJECT: GCP project ID (default: eonlabs-ethereum-bq)
    MD_DATABASE: MotherDuck database name (default: ethereum_mainnet)
    MD_TABLE: MotherDuck table name (default: blocks)
    STALE_THRESHOLD_SECONDS: Maximum age before alert (default: 600)

Exit Codes:
    0: Data is fresh (<600s old)
    1: Data is stale (>600s old) or query failed
"""

import os
import sys
from datetime import datetime, timezone
from google.cloud import secretmanager
import duckdb
import requests


# Configuration
GCP_PROJECT = os.environ.get('GCP_PROJECT', 'eonlabs-ethereum-bq')
MD_DATABASE = os.environ.get('MD_DATABASE', 'ethereum_mainnet')
MD_TABLE = os.environ.get('MD_TABLE', 'blocks')
STALE_THRESHOLD_SECONDS = int(os.environ.get('STALE_THRESHOLD_SECONDS', '600'))


def get_secret(secret_id: str, project_id: str = GCP_PROJECT) -> str:
    """Fetch secret from Google Secret Manager.

    Args:
        secret_id: Secret name (e.g., 'motherduck-token')
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


def check_data_freshness():
    """Query MotherDuck and verify data freshness.

    Returns:
        Tuple of (is_fresh: bool, diagnostic_message: str, healthcheck_url: str)

    Raises:
        Exception: If query fails or data is invalid
    """
    print("[1/3] Fetching secrets from Secret Manager...")
    motherduck_token = get_secret('motherduck-token')
    healthcheck_url = get_secret('healthchecks-data-quality-url')

    print(f"[2/3] Querying MotherDuck: {MD_DATABASE}.{MD_TABLE}")
    conn = duckdb.connect(
        f'md:{MD_DATABASE}?motherduck_token={motherduck_token}',
        config={'connect_timeout': 30000}  # 30 seconds
    )

    result = conn.execute(f"""
        SELECT MAX(number), MAX(timestamp), COUNT(*)
        FROM {MD_TABLE}
    """).fetchone()

    if result is None or result[0] is None:
        raise ValueError(f"No blocks found in {MD_DATABASE}.{MD_TABLE}")

    latest_block = result[0]
    latest_timestamp = result[1]
    total_blocks = result[2]

    # Calculate staleness
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    age_seconds = (now - latest_timestamp).total_seconds()

    print(f"   Latest block: {latest_block:,}")
    print(f"   Latest timestamp: {latest_timestamp}")
    print(f"   Total blocks: {total_blocks:,}")
    print(f"   Age: {age_seconds:.1f} seconds")

    # Determine freshness
    is_fresh = age_seconds <= STALE_THRESHOLD_SECONDS

    if is_fresh:
        diagnostic_msg = f"✅ FRESH: Block {latest_block:,}, {age_seconds:.0f}s old"
    else:
        diagnostic_msg = f"❌ STALE: Block {latest_block:,}, {age_seconds/60:.1f} min old (threshold: {STALE_THRESHOLD_SECONDS}s)"

    return is_fresh, diagnostic_msg, healthcheck_url


def ping_healthcheck(url: str, diagnostic_msg: str, is_fresh: bool):
    """Ping Healthchecks.io with diagnostic data.

    Args:
        url: Healthchecks.io ping URL
        diagnostic_msg: Diagnostic message to send
        is_fresh: Whether data is fresh

    Raises:
        requests.HTTPError: If ping fails
    """
    print("[3/3] Pinging Healthchecks.io...")

    # Use /fail endpoint if data is stale
    ping_url = f"{url}/fail" if not is_fresh else url

    response = requests.post(ping_url, data=diagnostic_msg, timeout=10)
    response.raise_for_status()

    print(f"   ✅ Pinged {ping_url}")
    print(f"   {diagnostic_msg}")


def main():
    """Entry point."""
    print("=" * 80)
    print("MotherDuck Data Quality Checker")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}")
    print(f"Database: {MD_DATABASE}.{MD_TABLE}")
    print(f"Stale threshold: {STALE_THRESHOLD_SECONDS}s")
    print("=" * 80)
    print()

    try:
        is_fresh, diagnostic_msg, healthcheck_url = check_data_freshness()
        ping_healthcheck(healthcheck_url, diagnostic_msg, is_fresh)

        if is_fresh:
            print("\n✅ Data quality check PASSED")
            return 0
        else:
            print("\n❌ Data quality check FAILED (stale data)")
            return 1

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
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
            print(f"   ✅ Pinged Healthchecks.io /fail")
        except Exception as ping_error:
            print(f"   ⚠️  Failed to ping Healthchecks.io: {ping_error}")
            pass  # Don't mask original error

        return 1


if __name__ == "__main__":
    sys.exit(main())
