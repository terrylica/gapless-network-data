#!/usr/bin/env python3
"""
Automated Doppler → OCI Vault secret migration script.

Migrates secrets from Doppler to Oracle Cloud Infrastructure Vault.
Uses off-the-shelf tools: doppler CLI, oci CLI.

Error handling: Exception-only (raise and propagate, no fallbacks).
"""

# /// script
# dependencies = [
#   "oci>=2.136.0",
# ]
# ///

import base64
import json
import subprocess
import sys
from pathlib import Path


# ================================================================================
# Configuration
# ================================================================================

# OCI Configuration (from ~/.oci/config)
OCI_CONFIG_FILE = Path.home() / ".oci" / "config"
OCI_COMPARTMENT_OCID = "ocid1.tenancy.oc1..aaaaaaaagwuvqhu7f2jdnruyt7yikkx4oiigbfxhr4b4rljvcclibpt7qwtq"  # Root compartment (tenancy)
OCI_REGION = "us-ashburn-1"
VAULT_NAME = "motherduck-monitoring-secrets"

# Secrets to migrate from Doppler
SECRETS_TO_MIGRATE = [
    "MOTHERDUCK_TOKEN",
    "HEALTHCHECKS_API_KEY",
    "PUSHOVER_TOKEN",
    "PUSHOVER_USER",
]

# Doppler configuration
DOPPLER_PROJECT = "claude-config"
DOPPLER_CONFIG = "dev"


# ================================================================================
# Helper Functions
# ================================================================================

def run_command(cmd: list[str], description: str) -> str:
    """
    Execute shell command and return output.

    Raises CalledProcessError on failure (exception-only error handling).
    """
    print(f"[EXEC] {description}")
    print(f"  Command: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,  # Raises CalledProcessError on non-zero exit
    )

    return result.stdout.strip()


def get_doppler_secret(secret_name: str) -> str:
    """
    Fetch secret from Doppler using CLI.

    Raises CalledProcessError if secret doesn't exist.
    """
    print(f"\n[DOPPLER] Fetching secret: {secret_name}")

    cmd = [
        "doppler", "secrets", "get",
        secret_name,
        "--plain",
        "--project", DOPPLER_PROJECT,
        "--config", DOPPLER_CONFIG,
    ]

    value = run_command(cmd, f"Fetch {secret_name} from Doppler")

    if not value:
        raise ValueError(f"Secret {secret_name} is empty in Doppler")

    print(f"  ✅ Retrieved {secret_name} ({len(value)} characters)")
    return value


def create_oci_vault() -> str:
    """
    Create OCI Vault if it doesn't exist.

    Returns vault OCID.
    """
    print(f"\n[OCI VAULT] Creating vault: {VAULT_NAME}")

    # Check if vault already exists
    try:
        list_cmd = [
            "oci", "kms", "management", "vault", "list",
            "--compartment-id", OCI_COMPARTMENT_OCID,
            "--region", OCI_REGION,
            "--all",
        ]

        output = run_command(list_cmd, "List existing vaults")
        vaults = json.loads(output)

        # Find vault by name
        for vault in vaults.get("data", []):
            if vault["display-name"] == VAULT_NAME and vault["lifecycle-state"] == "ACTIVE":
                vault_ocid = vault["id"]
                print(f"  ✅ Vault already exists: {vault_ocid}")
                return vault_ocid

    except subprocess.CalledProcessError:
        # Vault doesn't exist, create it
        pass

    # Create new vault
    create_cmd = [
        "oci", "kms", "management", "vault", "create",
        "--compartment-id", OCI_COMPARTMENT_OCID,
        "--display-name", VAULT_NAME,
        "--vault-type", "DEFAULT",
        "--region", OCI_REGION,
        "--wait-for-state", "ACTIVE",
    ]

    output = run_command(create_cmd, f"Create vault {VAULT_NAME}")
    vault_data = json.loads(output)
    vault_ocid = vault_data["data"]["id"]

    print(f"  ✅ Created vault: {vault_ocid}")
    return vault_ocid


def get_vault_management_endpoint(vault_ocid: str) -> str:
    """
    Get vault management endpoint from vault OCID.
    """
    cmd = [
        "oci", "kms", "management", "vault", "get",
        "--vault-id", vault_ocid,
        "--region", OCI_REGION,
    ]

    output = run_command(cmd, "Get vault details")
    vault_data = json.loads(output)
    management_endpoint = vault_data["data"]["management-endpoint"]

    print(f"  Management endpoint: {management_endpoint}")
    return management_endpoint


def create_master_encryption_key(vault_ocid: str, management_endpoint: str) -> str:
    """
    Create master encryption key for vault.

    Returns key OCID.
    """
    print(f"\n[OCI KEY] Creating master encryption key")

    # Check if key already exists
    list_cmd = [
        "oci", "kms", "management", "key", "list",
        "--compartment-id", OCI_COMPARTMENT_OCID,
        "--endpoint", management_endpoint,
        "--all",
    ]

    try:
        output = run_command(list_cmd, "List existing keys")
        keys = json.loads(output)

        # Find active key
        for key in keys.get("data", []):
            if key["lifecycle-state"] == "ENABLED":
                key_ocid = key["id"]
                print(f"  ✅ Key already exists: {key_ocid}")
                return key_ocid

    except subprocess.CalledProcessError:
        pass

    # Create new key
    create_cmd = [
        "oci", "kms", "management", "key", "create",
        "--compartment-id", OCI_COMPARTMENT_OCID,
        "--display-name", "motherduck-monitor-master-key",
        "--key-shape", '{"algorithm":"AES","length":32}',
        "--endpoint", management_endpoint,
        "--wait-for-state", "ENABLED",
    ]

    output = run_command(create_cmd, "Create master encryption key")
    key_data = json.loads(output)
    key_ocid = key_data["data"]["id"]

    print(f"  ✅ Created key: {key_ocid}")
    return key_ocid


def create_oci_secret(secret_name: str, secret_value: str, vault_ocid: str, key_ocid: str) -> str:
    """
    Create secret in OCI Vault.

    Returns secret OCID.
    """
    print(f"\n[OCI SECRET] Creating secret: {secret_name}")

    # Base64 encode secret value
    secret_content_base64 = base64.b64encode(secret_value.encode('utf-8')).decode('utf-8')

    # Check if secret already exists
    list_cmd = [
        "oci", "vault", "secret", "list",
        "--compartment-id", OCI_COMPARTMENT_OCID,
        "--vault-id", vault_ocid,
        "--all",
    ]

    try:
        output = run_command(list_cmd, f"List secrets in vault")
        secrets = json.loads(output)

        # Find secret by name
        for secret in secrets.get("data", []):
            if secret["secret-name"] == secret_name and secret["lifecycle-state"] == "ACTIVE":
                secret_ocid = secret["id"]
                print(f"  ⚠️  Secret already exists: {secret_ocid}")
                print(f"  Updating secret value...")

                # Update secret
                update_cmd = [
                    "oci", "vault", "secret", "update-base64",
                    "--secret-id", secret_ocid,
                    "--secret-content-content", secret_content_base64,
                ]

                run_command(update_cmd, f"Update secret {secret_name}")
                print(f"  ✅ Updated secret: {secret_ocid}")
                return secret_ocid

    except subprocess.CalledProcessError:
        pass

    # Create new secret
    create_cmd = [
        "oci", "vault", "secret", "create-base64",
        "--compartment-id", OCI_COMPARTMENT_OCID,
        "--secret-name", secret_name,
        "--vault-id", vault_ocid,
        "--key-id", key_ocid,
        "--secret-content-content", secret_content_base64,
    ]

    output = run_command(create_cmd, f"Create secret {secret_name}")
    secret_data = json.loads(output)
    secret_ocid = secret_data["data"]["id"]

    print(f"  ✅ Created secret: {secret_ocid}")
    return secret_ocid


def validate_oci_secret(secret_ocid: str, expected_value: str) -> bool:
    """
    Validate secret in OCI Vault matches expected value.

    Raises ValueError on mismatch.
    """
    print(f"\n[VALIDATE] Validating secret: {secret_ocid}")

    # Get secret bundle
    cmd = [
        "oci", "secrets", "secret-bundle", "get",
        "--secret-id", secret_ocid,
        "--stage", "CURRENT",
    ]

    output = run_command(cmd, "Fetch secret bundle")
    bundle_data = json.loads(output)

    # Decode secret content
    secret_content_base64 = bundle_data["data"]["secret-bundle-content"]["content"]
    actual_value = base64.b64decode(secret_content_base64).decode('utf-8')

    if actual_value != expected_value:
        raise ValueError(
            f"Secret validation failed: value mismatch\n"
            f"Expected length: {len(expected_value)}\n"
            f"Actual length: {len(actual_value)}"
        )

    print(f"  ✅ Secret validated (value matches)")
    return True


# ================================================================================
# Main Migration Logic
# ================================================================================

def main():
    """
    Main migration flow.

    Exception-only error handling: Any failure raises exception and exits.
    """
    print("=" * 80)
    print("Doppler → OCI Vault Secret Migration")
    print("=" * 80)

    # Step 1: Verify OCI CLI configured
    if not OCI_CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"OCI CLI not configured: {OCI_CONFIG_FILE} not found\n"
            f"Run: oci setup config"
        )

    print(f"\n[CONFIG] OCI CLI configured: {OCI_CONFIG_FILE}")

    # Step 2: Fetch secrets from Doppler
    doppler_secrets = {}
    for secret_name in SECRETS_TO_MIGRATE:
        doppler_secrets[secret_name] = get_doppler_secret(secret_name)

    print(f"\n✅ Retrieved {len(doppler_secrets)} secrets from Doppler")

    # Step 3: Create OCI Vault
    vault_ocid = create_oci_vault()
    management_endpoint = get_vault_management_endpoint(vault_ocid)

    # Step 4: Create master encryption key
    key_ocid = create_master_encryption_key(vault_ocid, management_endpoint)

    # Step 5: Create secrets in OCI Vault
    oci_secret_ocids = {}
    for secret_name, secret_value in doppler_secrets.items():
        secret_ocid = create_oci_secret(secret_name, secret_value, vault_ocid, key_ocid)
        oci_secret_ocids[secret_name] = secret_ocid

    print(f"\n✅ Created {len(oci_secret_ocids)} secrets in OCI Vault")

    # Step 6: Validate all secrets
    print("\n" + "=" * 80)
    print("Validation")
    print("=" * 80)

    for secret_name, secret_ocid in oci_secret_ocids.items():
        expected_value = doppler_secrets[secret_name]
        validate_oci_secret(secret_ocid, expected_value)

    # Step 7: Print summary
    print("\n" + "=" * 80)
    print("Migration Summary")
    print("=" * 80)
    print(f"\nVault OCID: {vault_ocid}")
    print(f"Key OCID: {key_ocid}")
    print(f"\nSecrets migrated:")

    for secret_name, secret_ocid in oci_secret_ocids.items():
        print(f"  {secret_name}: {secret_ocid}")

    print("\n✅ Migration completed successfully")
    print("\nNext steps:")
    print("  1. Grant IAM permissions to VM principal:")
    print(f"     oci iam policy create --name motherduck-monitor-secrets \\")
    print(f"       --compartment-id {OCI_COMPARTMENT_OCID} \\")
    print(f"       --statements '[\"Allow any-user to read secret-bundles in compartment id {OCI_COMPARTMENT_OCID} where request.principal.type='instance'\"]'")
    print("\n  2. Test secret fetch from VM:")
    print(f"     ssh motherduck-monitor 'python3 test_secret_fetch.py'")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Command failed: {' '.join(e.cmd)}", file=sys.stderr)
        print(f"Exit code: {e.returncode}", file=sys.stderr)
        print(f"STDOUT: {e.stdout}", file=sys.stderr)
        print(f"STDERR: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}", file=sys.stderr)
        sys.exit(1)
