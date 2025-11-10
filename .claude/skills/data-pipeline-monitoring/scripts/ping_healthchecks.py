#!/usr/bin/env python3
"""
Ping Healthchecks.io to signal successful pipeline health check.

Usage:
    python3 ping_healthchecks.py --check-name eth-pipeline
    python3 ping_healthchecks.py --check-name eth-pipeline --fail --message "Service down"

Error handling: Raise and propagate (no fallbacks/defaults/silent handling)
"""

# /// script
# dependencies = ["requests"]
# ///

import argparse
import os
import sys
import requests


def get_healthchecks_api_key() -> str:
    """
    Get Healthchecks.io API key from environment.

    Raises:
        RuntimeError: If API key not found in environment
    """
    api_key = os.environ.get('HEALTHCHECKS_API_KEY')

    if not api_key:
        raise RuntimeError(
            "HEALTHCHECKS_API_KEY must be set in environment. "
            "Run: export HEALTHCHECKS_API_KEY=$(doppler secrets get HEALTHCHECKS_API_KEY --project claude-config --config dev --plain)"
        )

    return api_key


def create_check(api_key: str, name: str, timeout: int = 3600, grace: int = 300) -> dict:
    """
    Create a new check on Healthchecks.io.

    Args:
        api_key: Healthchecks.io API key
        name: Check name
        timeout: Expected period between pings (seconds, default 3600 = 1 hour)
        grace: Grace period (seconds, default 300 = 5 minutes)

    Returns:
        Check details dict with ping_url

    Raises:
        requests.HTTPError: If API request fails
    """
    response = requests.post(
        "https://healthchecks.io/api/v3/checks/",
        headers={"X-Api-Key": api_key},
        json={
            "name": name,
            "timeout": timeout,
            "grace": grace,
            "channels": "*"  # All configured channels
        },
        timeout=10
    )

    response.raise_for_status()
    return response.json()


def list_checks(api_key: str) -> list[dict]:
    """
    List all checks on Healthchecks.io.

    Args:
        api_key: Healthchecks.io API key

    Returns:
        List of check dicts

    Raises:
        requests.HTTPError: If API request fails
    """
    response = requests.get(
        "https://healthchecks.io/api/v3/checks/",
        headers={"X-Api-Key": api_key},
        timeout=10
    )

    response.raise_for_status()
    return response.json()["checks"]


def ping_check(check_name: str, api_key: str, fail: bool = False, message: str | None = None) -> None:
    """
    Ping a Healthchecks.io check (create if not exists).

    Args:
        check_name: Name of the check
        api_key: Healthchecks.io API key
        fail: If True, ping /fail endpoint
        message: Optional message to include with ping

    Raises:
        requests.HTTPError: If API request fails
    """
    # Find or create check
    checks = list_checks(api_key)
    check = next((c for c in checks if c["name"] == check_name), None)

    if not check:
        print(f"Check '{check_name}' not found, creating...")
        check = create_check(api_key, check_name)
        print(f"✅ Created check: {check['name']}")

    # Ping the check
    ping_url = check["ping_url"]

    if fail:
        ping_url += "/fail"

    if message:
        response = requests.post(ping_url, data=message.encode('utf-8'), timeout=10)
    else:
        response = requests.get(ping_url, timeout=10)

    response.raise_for_status()


def main():
    parser = argparse.ArgumentParser(description="Ping Healthchecks.io")
    parser.add_argument("--check-name", required=True, help="Check name")
    parser.add_argument("--fail", action="store_true", help="Signal failure")
    parser.add_argument("--message", help="Optional message")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")

    args = parser.parse_args()

    try:
        api_key = get_healthchecks_api_key()
        ping_check(args.check_name, api_key, args.fail, args.message)

        if not args.quiet:
            status = "❌ FAIL" if args.fail else "✅ OK"
            print(f"{status} Pinged Healthchecks.io: {args.check_name}")

    except requests.HTTPError as e:
        print(f"❌ Healthchecks.io API error: {e}", file=sys.stderr)
        print(f"   Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)

    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
