#!/usr/bin/env python3
"""
Phase 5: Idiomatic UptimeRobot patterns
Demonstrate best practices and common patterns
"""
# /// script
# dependencies = ["requests"]
# ///

import os
import json
import requests
from typing import Dict, Optional, List


class UptimeRobotClient:
    """Idiomatic UptimeRobot API client."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.uptimerobot.com/v2"

    def _request(self, endpoint: str, data: Dict) -> Dict:
        """Make API request with error handling."""
        data["api_key"] = self.api_key
        data["format"] = "json"

        response = requests.post(f"{self.base_url}/{endpoint}", data=data)
        response.raise_for_status()

        result = response.json()

        if result.get("stat") != "ok":
            raise Exception(f"UptimeRobot API error: {result}")

        return result

    def get_account_details(self) -> Dict:
        """Get account information."""
        return self._request("getAccountDetails", {})

    def get_monitors(self) -> List[Dict]:
        """Get all monitors."""
        result = self._request("getMonitors", {})
        return result.get("monitors", [])

    def get_alert_contacts(self) -> List[Dict]:
        """Get all alert contacts."""
        result = self._request("getAlertContacts", {})
        return result.get("alert_contacts", [])

    def get_pushover_contact_id(self) -> Optional[str]:
        """Get first Pushover alert contact ID.

        Note: Pushover type code is 9 (empirically validated).
        May also search by name containing 'pushover' as fallback.
        """
        contacts = self.get_alert_contacts()
        # Method 1: Search by type code
        for contact in contacts:
            if str(contact['type']) == "9":
                return contact['id']
        # Method 2: Search by name (fallback)
        for contact in contacts:
            if 'pushover' in contact.get('friendly_name', '').lower():
                return contact['id']
        return None

    def create_http_monitor(
        self,
        name: str,
        url: str,
        interval: int = 300,
        telegram_contact_id: Optional[str] = None
    ) -> Dict:
        """Create HTTP(S) monitor."""
        data = {
            "friendly_name": name,
            "url": url,
            "type": 1,  # HTTP(S)
            "interval": interval
        }

        if telegram_contact_id:
            data["alert_contacts"] = telegram_contact_id

        return self._request("newMonitor", data)

    def delete_monitor(self, monitor_id: str) -> Dict:
        """Delete monitor."""
        return self._request("deleteMonitor", {"id": monitor_id})


def main():
    """Demonstrate idiomatic patterns."""
    # Get API key from Doppler
    api_key = os.popen(
        "doppler secrets get UPTIMEROBOT_API_KEY --project claude-config --config dev --plain"
    ).read().strip()

    print("=" * 60)
    print("  IDIOMATIC UPTIMEROBOT PATTERNS")
    print("=" * 60)
    print()

    # Initialize client
    client = UptimeRobotClient(api_key)

    # Pattern 1: Account details
    print("1️⃣  Get account details:")
    account = client.get_account_details()
    print(f"   Email: {account['account']['email']}")
    print(f"   Monitors: {account['account']['monitor_limit']}")
    print()

    # Pattern 2: List monitors
    print("2️⃣  List monitors:")
    monitors = client.get_monitors()
    print(f"   Total: {len(monitors)} monitor(s)")
    print()

    # Pattern 3: Get Telegram integration
    print("3️⃣  Get Telegram integration:")
    telegram_id = client.get_telegram_contact_id()
    if telegram_id:
        print(f"   ✅ Telegram ID: {telegram_id}")
    else:
        print("   ⚠️  No Telegram integration found")
    print()

    # Pattern 4: Monitor lifecycle
    print("4️⃣  Monitor lifecycle (create → verify → delete):")

    # Create
    result = client.create_http_monitor(
        name="[IDIOMATIC TEST] Health Check",
        url="https://httpbin.org/status/200",
        interval=300,
        telegram_contact_id=telegram_id
    )
    monitor_id = result["monitor"]["id"]
    print(f"   ✓ Created: {monitor_id}")

    # Verify
    monitors = client.get_monitors()
    found = any(m['id'] == monitor_id for m in monitors)
    print(f"   ✓ Verified: {found}")

    # Delete
    client.delete_monitor(monitor_id)
    print(f"   ✓ Deleted: {monitor_id}")
    print()

    # Save patterns
    patterns = {
        "initialization": {
            "description": "Initialize client with Doppler",
            "code": """
from uptimerobot_client import UptimeRobotClient
import os

api_key = os.popen('doppler secrets get UPTIMEROBOT_API_KEY --plain').read().strip()
client = UptimeRobotClient(api_key)
"""
        },
        "create_monitor": {
            "description": "Create HTTP monitor with Telegram alerts",
            "code": """
telegram_id = client.get_telegram_contact_id()
result = client.create_http_monitor(
    name="My Service",
    url="https://myservice.com/health",
    interval=300,  # 5 minutes
    telegram_contact_id=telegram_id
)
"""
        },
        "error_handling": {
            "description": "Robust error handling",
            "code": """
try:
    monitors = client.get_monitors()
except Exception as e:
    print(f"API error: {e}")
    # Handle gracefully
"""
        }
    }

    with open("/tmp/probe/uptimerobot/idiomatic_patterns.json", "w") as f:
        json.dump(patterns, f, indent=2)

    print("✅ All patterns demonstrated successfully!")
    print()
    print("✓ Patterns saved to: /tmp/probe/uptimerobot/idiomatic_patterns.json")


if __name__ == "__main__":
    main()
