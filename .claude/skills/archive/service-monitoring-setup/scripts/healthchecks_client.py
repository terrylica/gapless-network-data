#!/usr/bin/env python3
"""
Phase 5: Idiomatic Healthchecks.io patterns
Demonstrate best practices and common patterns
"""
# /// script
# dependencies = ["requests"]
# ///

import os
import json
import requests
from typing import Dict, Optional, List


class HealthchecksClient:
    """Idiomatic Healthchecks.io API client."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://healthchecks.io/api/v3"
        self.headers = {
            "X-Api-Key": api_key,
            "Content-Type": "application/json"
        }

    def get_checks(self) -> List[Dict]:
        """Get all checks."""
        response = requests.get(
            f"{self.base_url}/checks/",
            headers={"X-Api-Key": self.api_key}
        )
        response.raise_for_status()
        return response.json().get("checks", [])

    def get_channels(self) -> List[Dict]:
        """Get all integration channels."""
        response = requests.get(
            f"{self.base_url}/channels/",
            headers={"X-Api-Key": self.api_key}
        )
        response.raise_for_status()
        return response.json().get("channels", [])

    def get_pushover_channel_id(self) -> Optional[str]:
        """Get first Pushover channel ID.

        Note: API uses 'po' as abbreviated kind code, not 'pushover'.
        """
        channels = self.get_channels()
        for channel in channels:
            if channel.get('kind') in ['pushover', 'po']:
                return channel['id']
        return None

    def create_check(
        self,
        name: str,
        timeout: int,
        grace: int = 600,
        tags: str = "",
        channels: Optional[str] = None
    ) -> Dict:
        """Create a new check."""
        data = {
            "name": name,
            "timeout": timeout,
            "grace": grace,
            "tags": tags
        }

        if channels:
            data["channels"] = channels
        else:
            data["channels"] = "*"  # All channels

        response = requests.post(
            f"{self.base_url}/checks/",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

    def delete_check(self, check_uuid: str) -> None:
        """Delete a check."""
        response = requests.delete(
            f"{self.base_url}/checks/{check_uuid}",
            headers={"X-Api-Key": self.api_key}
        )
        response.raise_for_status()

    def ping_check(self, ping_url: str) -> None:
        """Send a success ping."""
        response = requests.get(ping_url)
        response.raise_for_status()

    def ping_fail(self, ping_url: str) -> None:
        """Report a failure."""
        response = requests.get(f"{ping_url}/fail")
        response.raise_for_status()


def main():
    """Demonstrate idiomatic patterns."""
    # Get API key from Doppler
    api_key = os.popen(
        "doppler secrets get HEALTHCHECKS_API_KEY --project claude-config --config dev --plain"
    ).read().strip()

    print("=" * 60)
    print("  IDIOMATIC HEALTHCHECKS.IO PATTERNS")
    print("=" * 60)
    print()

    # Initialize client
    client = HealthchecksClient(api_key)

    # Pattern 1: List checks
    print("1️⃣  List checks:")
    checks = client.get_checks()
    print(f"   Total: {len(checks)} check(s)")
    print()

    # Pattern 2: Get Telegram integration
    print("2️⃣  Get Telegram integration:")
    telegram_id = client.get_telegram_channel_id()
    if telegram_id:
        print(f"   ✅ Telegram ID: {telegram_id}")
    else:
        print("   ⚠️  No Telegram integration found")
    print()

    # Pattern 3: Check lifecycle
    print("3️⃣  Check lifecycle (create → ping → verify → delete):")

    # Create
    result = client.create_check(
        name="[IDIOMATIC TEST] Health Check",
        timeout=3600,  # 1 hour
        grace=600,     # 10 minutes
        tags="test probe",
        channels=telegram_id
    )
    check_uuid = result["unique_key"]
    ping_url = result["ping_url"]
    print(f"   ✓ Created: {check_uuid}")

    # Ping
    client.ping_check(ping_url)
    print(f"   ✓ Pinged: {ping_url}")

    # Verify
    checks = client.get_checks()
    found = any(c['unique_key'] == check_uuid for c in checks)
    print(f"   ✓ Verified: {found}")

    # Delete
    client.delete_check(check_uuid)
    print(f"   ✓ Deleted: {check_uuid}")
    print()

    # Save patterns
    patterns = {
        "initialization": {
            "description": "Initialize client with Doppler",
            "code": """
from healthchecks_client import HealthchecksClient
import os

api_key = os.popen('doppler secrets get HEALTHCHECKS_API_KEY --plain').read().strip()
client = HealthchecksClient(api_key)
"""
        },
        "create_check": {
            "description": "Create check with Telegram alerts",
            "code": """
telegram_id = client.get_telegram_channel_id()
result = client.create_check(
    name="My Job",
    timeout=7200,  # 2 hours
    grace=600,     # 10 minutes
    channels=telegram_id
)
ping_url = result["ping_url"]
"""
        },
        "ping_from_job": {
            "description": "Ping from job execution",
            "code": """
import requests

# At end of successful job
ping_url = os.getenv("HEALTHCHECK_PING_URL")
requests.get(ping_url)

# On failure
requests.get(f"{ping_url}/fail")
"""
        },
        "error_handling": {
            "description": "Robust error handling",
            "code": """
try:
    checks = client.get_checks()
except Exception as e:
    print(f"API error: {e}")
    # Handle gracefully
"""
        }
    }

    with open("/tmp/probe/healthchecks-io/idiomatic_patterns.json", "w") as f:
        json.dump(patterns, f, indent=2)

    print("✅ All patterns demonstrated successfully!")
    print()
    print("✓ Patterns saved to: /tmp/probe/healthchecks-io/idiomatic_patterns.json")


if __name__ == "__main__":
    main()
