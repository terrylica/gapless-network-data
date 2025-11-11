#!/usr/bin/env python3
"""
Send Pushover alerts based on pipeline health check results.

Usage:
    python3 send_pushover_alert.py --title "Pipeline Alert" --message "eth-collector down" --priority 1
    python3 send_pushover_alert.py --health-check-json health_results.json

Error handling: Raise and propagate (no fallbacks/defaults/silent handling)
"""

# /// script
# dependencies = ["requests", "python-ulid", "typing-extensions"]
# ///

import argparse
import json
import os
import sys
from typing import Dict, List
import requests
from ulid import ULID


def get_pushover_credentials() -> tuple[str, str]:
    """
    Get Pushover credentials from environment.

    Raises:
        RuntimeError: If credentials not found in environment
    """
    token = os.environ.get('PUSHOVER_TOKEN')
    user = os.environ.get('PUSHOVER_USER')

    if not token or not user:
        raise RuntimeError(
            "PUSHOVER_TOKEN and PUSHOVER_USER must be set in environment. "
            "Run: export PUSHOVER_TOKEN=$(doppler secrets get PUSHOVER_TOKEN --project claude-config --config dev --plain) && "
            "export PUSHOVER_USER=$(doppler secrets get PUSHOVER_USER --project claude-config --config dev --plain)"
        )

    return token, user


def send_pushover_notification(
    message: str,
    title: str | None = None,
    priority: int = 0,
    sound: str = "pushover"
) -> Dict:
    """
    Send Pushover notification with unique ULID identifier.

    Args:
        message: Notification message (required, max 1024 characters)
        title: Notification title (optional, max 250 characters)
        priority: Priority level (-2 to 2, default 0)
                 -2: Silent, -1: Quiet, 0: Normal, 1: High, 2: Emergency
        sound: Notification sound (default: "pushover")

    Returns:
        API response dict with status, request ID, and ULID

    Raises:
        requests.HTTPError: If API request fails
        RuntimeError: If credentials not found
    """
    token, user = get_pushover_credentials()

    # Generate ULID (26-char timestamped unique identifier)
    ulid = str(ULID())

    # Append ULID to message (at bottom)
    message_with_id = f"{message}\n\nID: {ulid}"

    payload = {
        "token": token,
        "user": user,
        "message": message_with_id,
        "priority": priority,
        "sound": sound
    }

    if title:
        payload["title"] = title

    response = requests.post(
        "https://api.pushover.net/1/messages.json",
        data=payload,
        timeout=10
    )

    # Raise exception on HTTP error (no silent failures)
    response.raise_for_status()

    result = response.json()
    result["ulid"] = ulid  # Include ULID in response for logging
    return result


def format_health_check_alert(results: List[Dict]) -> tuple[str, str, int]:
    """
    Format health check results into Pushover alert.

    Args:
        results: List of health check result dicts

    Returns:
        Tuple of (title, message, priority)
    """
    critical_count = sum(1 for r in results if r["status"] == "CRITICAL")
    warning_count = sum(1 for r in results if r["status"] == "WARNING")
    ok_count = sum(1 for r in results if r["status"] == "OK")

    if critical_count > 0:
        title = f"🚨 Pipeline CRITICAL ({critical_count} failures)"
        priority = 1  # High priority for critical failures

        # List critical components
        critical_components = [r["component"] for r in results if r["status"] == "CRITICAL"]
        message = f"CRITICAL failures:\n" + "\n".join(f"❌ {c}" for c in critical_components)

        # Add first critical message details
        for r in results:
            if r["status"] == "CRITICAL":
                message += f"\n\nDetails: {r['message']}"
                break

    elif warning_count > 0:
        title = f"⚠️ Pipeline WARNING ({warning_count} warnings)"
        priority = 0  # Normal priority for warnings

        warning_components = [r["component"] for r in results if r["status"] == "WARNING"]
        message = f"Warnings:\n" + "\n".join(f"⚠️ {c}" for c in warning_components)

    else:
        title = f"✅ Pipeline OK ({ok_count} components healthy)"
        priority = -1  # Quiet priority for OK status
        message = "All pipeline components operational"

    return title, message, priority


def main():
    parser = argparse.ArgumentParser(description="Send Pushover alerts for pipeline health")
    parser.add_argument("--title", help="Alert title")
    parser.add_argument("--message", help="Alert message")
    parser.add_argument("--priority", type=int, default=0, help="Priority (-2 to 2)")
    parser.add_argument("--health-check-json", help="Health check results JSON file")
    parser.add_argument("--quiet", action="store_true", help="Suppress success output")

    args = parser.parse_args()

    try:
        if args.health_check_json:
            # Read health check results and format alert
            with open(args.health_check_json, 'r') as f:
                results = json.load(f)

            title, message, priority = format_health_check_alert(results)

            # Only send alert if there are issues (not OK status)
            if any(r["status"] in ["CRITICAL", "WARNING"] for r in results):
                response = send_pushover_notification(message, title, priority)

                if not args.quiet:
                    print(f"✅ Pushover alert sent: {title}")
                    print(f"   Request ID: {response.get('request')}")
                    print(f"   ULID: {response.get('ulid')}")
                    print(f"   Status: {response.get('status')}")
            else:
                if not args.quiet:
                    print("ℹ️  All checks OK, no alert sent (use --quiet to suppress)")

        elif args.message:
            # Send custom alert
            response = send_pushover_notification(args.message, args.title, args.priority)

            if not args.quiet:
                print(f"✅ Pushover alert sent")
                print(f"   Request ID: {response.get('request')}")
                print(f"   ULID: {response.get('ulid')}")
                print(f"   Status: {response.get('status')}")

        else:
            print("Error: Either --message or --health-check-json required", file=sys.stderr)
            sys.exit(1)

    except requests.HTTPError as e:
        print(f"❌ Pushover API error: {e}", file=sys.stderr)
        print(f"   Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)

    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        raise  # Re-raise to preserve stack trace


if __name__ == "__main__":
    main()
