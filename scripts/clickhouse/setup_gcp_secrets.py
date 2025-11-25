# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "google-cloud-secret-manager>=2.21.0",
# ]
# ///
"""
Create ClickHouse secrets in GCP Secret Manager using Python SDK.

Does not require gcloud CLI - uses Application Default Credentials.

Usage:
    doppler run --project aws-credentials --config prd -- uv run scripts/clickhouse/setup_gcp_secrets.py

Prerequisites:
    - GOOGLE_APPLICATION_CREDENTIALS env var set, OR
    - Running on GCP with default credentials, OR
    - gcloud auth application-default login completed
"""

import os
import sys
from google.cloud import secretmanager
from google.api_core import exceptions


PROJECT_ID = "eonlabs-ethereum-bq"


def create_or_update_secret(client, secret_id: str, value: str) -> bool:
    """Create secret or add new version if exists.

    Args:
        client: SecretManagerServiceClient
        secret_id: Secret name
        value: Secret value

    Returns:
        True if successful
    """
    parent = f"projects/{PROJECT_ID}"
    secret_path = f"{parent}/secrets/{secret_id}"

    # Check if secret exists
    try:
        client.get_secret(request={"name": secret_path})
        print(f"  {secret_id}: exists, adding new version...")
    except exceptions.NotFound:
        # Create new secret
        print(f"  {secret_id}: creating...")
        client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )

    # Add version with the value
    client.add_secret_version(
        request={
            "parent": secret_path,
            "payload": {"data": value.encode("UTF-8")},
        }
    )
    print(f"  ✅ {secret_id}: version added")
    return True


def main():
    """Create ClickHouse secrets in GCP Secret Manager."""
    print("=" * 60)
    print("ClickHouse → GCP Secret Manager Setup (Python SDK)")
    print("=" * 60)
    print(f"Project: {PROJECT_ID}")
    print()

    # Get credentials from environment (set by Doppler)
    ch_host = os.environ.get("CLICKHOUSE_HOST")
    ch_password = os.environ.get("CLICKHOUSE_PASSWORD")

    if not ch_host or not ch_password:
        print("❌ ERROR: Missing CLICKHOUSE_HOST or CLICKHOUSE_PASSWORD")
        print("   Run with: doppler run --project aws-credentials --config prd -- uv run scripts/clickhouse/setup_gcp_secrets.py")
        return 1

    print(f"[1/2] Credentials loaded from Doppler")
    print(f"  CLICKHOUSE_HOST: {ch_host}")
    print(f"  CLICKHOUSE_PASSWORD: {'*' * 8} (hidden)")
    print()

    # Create Secret Manager client
    print("[2/2] Creating secrets in GCP Secret Manager...")
    try:
        client = secretmanager.SecretManagerServiceClient()

        create_or_update_secret(client, "clickhouse-host", ch_host)
        create_or_update_secret(client, "clickhouse-password", ch_password)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure GOOGLE_APPLICATION_CREDENTIALS is set, OR")
        print("2. Run: gcloud auth application-default login")
        print("3. Ensure account has secretmanager.admin role")
        return 1

    print()
    print("=" * 60)
    print("✅ GCP SECRETS SETUP COMPLETE")
    print("=" * 60)
    print()
    print("Secrets created:")
    print("  - clickhouse-host")
    print("  - clickhouse-password")
    print()
    print("Next steps:")
    print("  1. Deploy VM collector: cd deployment/vm && ./deploy.sh")
    print("  2. Deploy Cloud Run: see DEPLOYMENT.md")
    print("  3. Deploy Cloud Function: see DEPLOYMENT.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
