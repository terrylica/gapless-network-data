#!/usr/bin/env python3
"""
Autonomous monitoring setup for dual-pipeline infrastructure.

Sets up:
- Healthchecks.io: Heartbeat monitoring for Cloud Run Job
- UptimeRobot: HTTP monitoring for VM systemd service
- Telegram alerts on both services

Usage:
    # Set API keys in environment or Doppler
    export HEALTHCHECKS_API_KEY="your-healthchecks-key"
    export UPTIMEROBOT_API_KEY="your-uptimerobot-key"

    # Run setup
    python3 setup_monitoring.py
"""

import os
import sys
import json
import requests
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class MonitorConfig:
    """Configuration for monitoring setup."""
    # GCP Infrastructure
    gcp_project: str = "eonlabs-ethereum-bq"
    cloud_run_job: str = "eth-md-updater"
    vm_name: str = "eth-realtime-collector"
    vm_zone: str = "us-east1-b"
    vm_http_port: int = 8000

    # API Keys (from environment or Doppler)
    healthchecks_api_key: str = ""
    uptimerobot_api_key: str = ""

    # Monitoring Settings
    cloud_run_timeout: int = 7200  # 2 hours (hourly job + buffer)
    cloud_run_grace: int = 600     # 10 minutes grace period
    vm_http_interval: int = 300    # 5 minutes


class HealthchecksManager:
    """Manage Healthchecks.io checks via API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://healthchecks.io/api/v3"
        self.headers = {
            "X-Api-Key": api_key,
            "Content-Type": "application/json"
        }

    def list_channels(self) -> Dict:
        """List all integrations/channels."""
        response = requests.get(
            f"{self.base_url}/channels/",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_telegram_channel_id(self) -> Optional[str]:
        """Get the first Telegram channel UUID."""
        channels = self.list_channels()
        for channel in channels.get("channels", []):
            if channel["kind"] == "telegram":
                return channel["id"]
        return None

    def create_check(
        self,
        name: str,
        timeout: int,
        grace: int,
        tags: str = "",
        telegram_channel_id: Optional[str] = None
    ) -> Dict:
        """Create a new heartbeat check."""
        data = {
            "name": name,
            "timeout": timeout,
            "grace": grace,
            "tags": tags,
            "desc": f"Monitors {name} execution"
        }

        if telegram_channel_id:
            data["channels"] = telegram_channel_id
        else:
            # Assign all integrations
            data["channels"] = "*"

        response = requests.post(
            f"{self.base_url}/checks/",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

    def list_checks(self) -> Dict:
        """List all existing checks."""
        response = requests.get(
            f"{self.base_url}/checks/",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()


class UptimeRobotManager:
    """Manage UptimeRobot monitors via API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.uptimerobot.com/v2"

    def _request(self, endpoint: str, data: Dict) -> Dict:
        """Make API request."""
        data["api_key"] = self.api_key
        data["format"] = "json"

        response = requests.post(
            f"{self.base_url}/{endpoint}",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        result = response.json()

        if result.get("stat") != "ok":
            raise Exception(f"UptimeRobot API error: {result}")

        return result

    def get_alert_contacts(self) -> Dict:
        """Get all alert contacts."""
        return self._request("getAlertContacts", {})

    def get_telegram_contact_id(self) -> Optional[str]:
        """Get the first Telegram alert contact ID."""
        contacts = self.get_alert_contacts()
        for contact in contacts.get("alert_contacts", []):
            if contact["type"] == "11":  # 11 = Telegram
                return contact["id"]
        return None

    def create_monitor(
        self,
        friendly_name: str,
        url: str,
        type: int = 1,  # 1 = HTTP(S)
        interval: int = 300,  # 5 minutes
        alert_contacts: Optional[str] = None
    ) -> Dict:
        """Create a new HTTP monitor."""
        data = {
            "friendly_name": friendly_name,
            "url": url,
            "type": type,
            "interval": interval
        }

        if alert_contacts:
            data["alert_contacts"] = alert_contacts

        return self._request("newMonitor", data)

    def get_monitors(self) -> Dict:
        """Get all monitors."""
        return self._request("getMonitors", {})


def get_api_keys_from_doppler() -> Dict[str, str]:
    """Fetch API keys from Doppler."""
    try:
        import subprocess

        healthchecks_key = subprocess.check_output(
            ["doppler", "secrets", "get", "HEALTHCHECKS_API_KEY",
             "--project", "claude-config", "--config", "dev", "--plain"],
            text=True
        ).strip()

        uptimerobot_key = subprocess.check_output(
            ["doppler", "secrets", "get", "UPTIMEROBOT_API_KEY",
             "--project", "claude-config", "--config", "dev", "--plain"],
            text=True
        ).strip()

        return {
            "healthchecks": healthchecks_key,
            "uptimerobot": uptimerobot_key
        }
    except Exception as e:
        print(f"⚠️  Could not fetch from Doppler: {e}")
        print("⚠️  Falling back to environment variables")
        return {}


def setup_monitoring(config: MonitorConfig) -> Dict:
    """
    Set up complete monitoring infrastructure.

    Returns:
        Dict with ping URLs and monitor IDs
    """
    results = {
        "healthchecks": {},
        "uptimerobot": {},
        "integration_code": {}
    }

    print("🚀 Starting autonomous monitoring setup...\n")

    # ========================================
    # 1. Healthchecks.io - Cloud Run Job
    # ========================================
    print("📋 [1/2] Setting up Healthchecks.io for Cloud Run Job...")

    try:
        hc = HealthchecksManager(config.healthchecks_api_key)

        # Get Telegram integration
        telegram_id = hc.get_telegram_channel_id()
        if telegram_id:
            print(f"  ✓ Found Telegram integration: {telegram_id}")
        else:
            print("  ⚠️  No Telegram integration found (will use all integrations)")

        # Create heartbeat check
        check = hc.create_check(
            name=f"{config.cloud_run_job} (Cloud Run Job)",
            timeout=config.cloud_run_timeout,
            grace=config.cloud_run_grace,
            tags="gcp cloud-run ethereum",
            telegram_channel_id=telegram_id
        )

        results["healthchecks"] = {
            "check_id": check["id"],
            "ping_url": check["ping_url"],
            "name": check["name"]
        }

        print(f"  ✓ Created check: {check['name']}")
        print(f"  ✓ Ping URL: {check['ping_url']}\n")

    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        results["healthchecks"]["error"] = str(e)

    # ========================================
    # 2. UptimeRobot - VM HTTP Monitoring
    # ========================================
    print("📋 [2/2] Setting up UptimeRobot for VM systemd service...")

    try:
        ur = UptimeRobotManager(config.uptimerobot_api_key)

        # Get Telegram alert contact
        telegram_contact_id = ur.get_telegram_contact_id()
        if telegram_contact_id:
            print(f"  ✓ Found Telegram contact: {telegram_contact_id}")
        else:
            print("  ⚠️  No Telegram contact found")

        # Get VM external IP
        import subprocess
        vm_ip = subprocess.check_output([
            "gcloud", "compute", "instances", "describe", config.vm_name,
            "--zone", config.vm_zone,
            "--project", config.gcp_project,
            "--format", "value(networkInterfaces[0].accessConfigs[0].natIP)"
        ], text=True).strip()

        print(f"  ✓ Detected VM IP: {vm_ip}")

        # Create HTTP monitor
        monitor_url = f"http://{vm_ip}:{config.vm_http_port}/health"
        monitor = ur.create_monitor(
            friendly_name=f"{config.vm_name} - eth-collector",
            url=monitor_url,
            interval=config.vm_http_interval,
            alert_contacts=telegram_contact_id
        )

        results["uptimerobot"] = {
            "monitor_id": monitor["monitor"]["id"],
            "url": monitor_url,
            "status": monitor["monitor"]["status"]
        }

        print(f"  ✓ Created monitor: {monitor_url}")
        print(f"  ✓ Monitor ID: {monitor['monitor']['id']}\n")

    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        results["uptimerobot"]["error"] = str(e)

    # ========================================
    # 3. Generate Integration Code
    # ========================================
    print("📝 Generating integration code snippets...\n")

    if "ping_url" in results["healthchecks"]:
        ping_url = results["healthchecks"]["ping_url"]
        results["integration_code"]["cloud_run_job"] = f'''
# Add to deployment/cloud-run/main.py (end of run_updater function)

import requests

def notify_healthcheck(status="success"):
    """Notify Healthchecks.io of job completion."""
    ping_url = "{ping_url}"
    if status == "success":
        requests.get(f"{{ping_url}}")
    else:
        requests.get(f"{{ping_url}}/fail")

# Call at end of successful execution
notify_healthcheck("success")

# Call in exception handler
# notify_healthcheck("fail")
'''

    if "url" in results["uptimerobot"]:
        results["integration_code"]["vm_http_endpoint"] = '''
# Add to deployment/vm/realtime_collector.py

from flask import Flask, jsonify
import threading

app = Flask(__name__)

@app.route('/health')
def health():
    """Health check endpoint for UptimeRobot."""
    return jsonify({
        'status': 'ok',
        'service': 'eth-collector',
        'blocks_collected': block_count  # Global variable
    }), 200

# Start Flask server in background thread
def start_health_server():
    app.run(host='0.0.0.0', port=8000)

if __name__ == '__main__':
    threading.Thread(target=start_health_server, daemon=True).start()
    # ... existing collector code ...
'''

    return results


def main():
    """Main execution."""
    print("=" * 60)
    print("  AUTONOMOUS MONITORING SETUP")
    print("  Healthchecks.io + UptimeRobot + Telegram")
    print("=" * 60)
    print()

    # Get API keys
    api_keys = get_api_keys_from_doppler()

    config = MonitorConfig(
        healthchecks_api_key=api_keys.get("healthchecks") or os.getenv("HEALTHCHECKS_API_KEY", ""),
        uptimerobot_api_key=api_keys.get("uptimerobot") or os.getenv("UPTIMEROBOT_API_KEY", "")
    )

    # Validate API keys
    if not config.healthchecks_api_key:
        print("❌ HEALTHCHECKS_API_KEY not found")
        print("   Set via: export HEALTHCHECKS_API_KEY=your-key")
        print("   Or store in Doppler: doppler secrets set HEALTHCHECKS_API_KEY")
        sys.exit(1)

    if not config.uptimerobot_api_key:
        print("❌ UPTIMEROBOT_API_KEY not found")
        print("   Set via: export UPTIMEROBOT_API_KEY=your-key")
        print("   Or store in Doppler: doppler secrets set UPTIMEROBOT_API_KEY")
        sys.exit(1)

    print(f"✓ API keys loaded")
    print(f"✓ GCP Project: {config.gcp_project}")
    print(f"✓ Cloud Run Job: {config.cloud_run_job}")
    print(f"✓ VM: {config.vm_name}\n")

    # Run setup
    results = setup_monitoring(config)

    # Save results
    output_file = "monitoring_setup_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print("=" * 60)
    print("✅ SETUP COMPLETE!")
    print("=" * 60)
    print(f"\n📄 Results saved to: {output_file}")
    print("\n📋 Next Steps:")
    print("  1. Review integration code snippets in results file")
    print("  2. Add ping URL to Cloud Run Job script")
    print("  3. Add /health endpoint to VM collector")
    print("  4. Verify Telegram notifications are working\n")

    # Print integration code
    if "cloud_run_job" in results["integration_code"]:
        print("🔧 Cloud Run Job Integration:")
        print(results["integration_code"]["cloud_run_job"])

    if "vm_http_endpoint" in results["integration_code"]:
        print("🔧 VM HTTP Endpoint Integration:")
        print(results["integration_code"]["vm_http_endpoint"])


if __name__ == "__main__":
    main()
