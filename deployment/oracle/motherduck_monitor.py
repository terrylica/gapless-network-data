#!/usr/bin/env python3
"""
MotherDuck Gap Detection Monitor (Oracle Cloud)

Monitors MotherDuck Ethereum database for gaps and staleness.
Designed to run via cron every 3 hours on Oracle Cloud VM.

Gap Detection:
    - Time window: 1 year ago → 3 minutes ago
    - Threshold: >15 seconds (Ethereum ~12s block time + 3s tolerance)
    - Method: DuckDB LAG() window function

Monitoring:
    - Healthchecks.io Dead Man's Switch (POST to ping URL)
    - Pushover emergency notifications (all results)

Exit Codes:
    0: Healthy (no gaps, data fresh)
    1: Unhealthy (gaps detected or data stale)
    2: Fatal error (query failed, MotherDuck unreachable)
"""

# /// script
# dependencies = [
#   "duckdb>=1.4.0",
#   "httpx>=0.27.0",
#   "oci>=2.136.0",
# ]
# ///

import base64
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import httpx
import oci


# ================================================================================
# Configuration
# ================================================================================

# MotherDuck configuration
MD_DATABASE = os.environ.get('MD_DATABASE', 'ethereum_mainnet')
MD_TABLE = os.environ.get('MD_TABLE', 'blocks')

# Gap detection configuration
GAP_THRESHOLD_SECONDS = int(os.environ.get('GAP_THRESHOLD_SECONDS', '15'))  # Ethereum ~12s + 3s tolerance
TIME_WINDOW_START_DAYS = int(os.environ.get('TIME_WINDOW_START_DAYS', '365'))  # 1 year historical
TIME_WINDOW_END_MINUTES = int(os.environ.get('TIME_WINDOW_END_MINUTES', '3'))  # 3 minutes from now (prevent false positives)

# Staleness threshold
STALE_THRESHOLD_SECONDS = int(os.environ.get('STALE_THRESHOLD_SECONDS', '300'))  # 5 minutes

# OCI Secret OCIDs (override via environment if needed)
SECRET_MOTHERDUCK_TOKEN = os.environ.get('SECRET_MOTHERDUCK_TOKEN_OCID', '')
SECRET_HEALTHCHECKS_API_KEY = os.environ.get('SECRET_HEALTHCHECKS_API_KEY_OCID', '')
SECRET_PUSHOVER_TOKEN = os.environ.get('SECRET_PUSHOVER_TOKEN_OCID', '')
SECRET_PUSHOVER_USER = os.environ.get('SECRET_PUSHOVER_USER_OCID', '')

# Healthchecks.io ping URL (from Doppler or environment)
HEALTHCHECKS_PING_URL = os.environ.get('HEALTHCHECKS_PING_URL', '')


# ================================================================================
# Secret Management (OCI Vault)
# ================================================================================

def get_oci_secret(secret_ocid: str) -> str:
    """
    Fetch secret from OCI Vault.

    Args:
        secret_ocid: OCI secret OCID

    Returns:
        Secret value as string

    Raises:
        Exception: If secret fetch fails
    """
    config = oci.config.from_file()
    client = oci.secrets.SecretsClient(config)

    response = client.get_secret_bundle(secret_id=secret_ocid)
    secret_bytes = base64.b64decode(response.data.secret_bundle_content.content)

    return secret_bytes.decode('utf-8')


def load_secrets() -> dict[str, str]:
    """
    Load all secrets from OCI Vault.

    Returns:
        Dictionary of secret values

    Raises:
        ValueError: If required secrets are not configured
        Exception: If secret fetch fails
    """
    print("[SECRETS] Loading secrets from OCI Vault...")

    # Validate secret OCIDs are configured
    required_secrets = {
        'motherduck_token': SECRET_MOTHERDUCK_TOKEN,
        'healthchecks_api_key': SECRET_HEALTHCHECKS_API_KEY,
        'pushover_token': SECRET_PUSHOVER_TOKEN,
        'pushover_user': SECRET_PUSHOVER_USER,
    }

    for name, ocid in required_secrets.items():
        if not ocid:
            raise ValueError(
                f"Secret OCID not configured: {name}\n"
                f"Set environment variable: SECRET_{name.upper()}_OCID"
            )

    # Fetch secrets
    secrets = {}
    for name, ocid in required_secrets.items():
        print(f"  Fetching {name}...")
        secrets[name] = get_oci_secret(ocid)
        print(f"  ✅ {name} ({len(secrets[name])} characters)")

    print(f"✅ Loaded {len(secrets)} secrets")
    return secrets


# ================================================================================
# Gap Detection
# ================================================================================

def detect_gaps(conn: duckdb.DuckDBPyConnection) -> tuple[list[dict], int]:
    """
    Detect gaps in block timestamps using DuckDB LAG() window function.

    Args:
        conn: DuckDB connection

    Returns:
        Tuple of (gap_list, total_blocks_checked)

    Raises:
        Exception: If query fails
    """
    print(f"[GAP DETECTION] Analyzing blocks...")
    print(f"  Time window: {TIME_WINDOW_START_DAYS} days ago → {TIME_WINDOW_END_MINUTES} min ago")
    print(f"  Gap threshold: >{GAP_THRESHOLD_SECONDS}s")

    query = f"""
    WITH gaps AS (
        SELECT
            number AS block_number,
            timestamp,
            LAG(timestamp) OVER (ORDER BY timestamp) AS prev_timestamp,
            EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (ORDER BY timestamp))) AS gap_seconds
        FROM {MD_TABLE}
        WHERE timestamp BETWEEN (CURRENT_TIMESTAMP - INTERVAL '{TIME_WINDOW_START_DAYS} days')
                            AND (CURRENT_TIMESTAMP - INTERVAL '{TIME_WINDOW_END_MINUTES} minutes')
    )
    SELECT
        block_number,
        timestamp,
        prev_timestamp,
        gap_seconds,
        ROUND(gap_seconds / 60.0, 2) AS gap_minutes
    FROM gaps
    WHERE gap_seconds > {GAP_THRESHOLD_SECONDS}
    ORDER BY gap_seconds DESC
    LIMIT 100
    """

    result = conn.execute(query).fetchall()

    # Count total blocks checked
    count_query = f"""
    SELECT COUNT(*)
    FROM {MD_TABLE}
    WHERE timestamp BETWEEN (CURRENT_TIMESTAMP - INTERVAL '{TIME_WINDOW_START_DAYS} days')
                        AND (CURRENT_TIMESTAMP - INTERVAL '{TIME_WINDOW_END_MINUTES} minutes')
    """
    total_blocks = conn.execute(count_query).fetchone()[0]

    # Convert to list of dicts
    gaps = []
    for row in result:
        gaps.append({
            'block_number': row[0],
            'timestamp': row[1],
            'prev_timestamp': row[2],
            'gap_seconds': row[3],
            'gap_minutes': row[4],
        })

    print(f"  Blocks checked: {total_blocks:,}")
    print(f"  Gaps found: {len(gaps)}")

    if gaps:
        max_gap = gaps[0]
        print(f"  ⚠️  Largest gap: {max_gap['gap_seconds']:.0f}s ({max_gap['gap_minutes']:.1f} min)")

    return gaps, total_blocks


def check_staleness(conn: duckdb.DuckDBPyConnection) -> tuple[bool, int, datetime, int]:
    """
    Check if latest block is stale.

    Args:
        conn: DuckDB connection

    Returns:
        Tuple of (is_fresh, age_seconds, latest_timestamp, latest_block)

    Raises:
        ValueError: If no blocks found
        Exception: If query fails
    """
    print(f"[STALENESS] Checking latest block...")

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

    is_fresh = age_seconds <= STALE_THRESHOLD_SECONDS

    print(f"  Latest block: {latest_block:,}")
    print(f"  Latest timestamp: {latest_timestamp}")
    print(f"  Total blocks: {total_blocks:,}")
    print(f"  Age: {age_seconds:.1f}s")
    print(f"  Fresh: {is_fresh} (threshold: {STALE_THRESHOLD_SECONDS}s)")

    return is_fresh, int(age_seconds), latest_timestamp, latest_block


# ================================================================================
# Monitoring Integration
# ================================================================================

def send_pushover_notification(
    token: str,
    user: str,
    message: str,
    title: str,
    priority: int = 2
):
    """
    Send Pushover notification.

    Args:
        token: Pushover application token
        user: Pushover user key
        message: Notification message
        title: Notification title
        priority: Priority level (2 = emergency)

    Raises:
        httpx.HTTPError: If request fails
    """
    print(f"[PUSHOVER] Sending notification...")

    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": token,
        "user": user,
        "message": message,
        "title": title,
        "priority": priority,
    }

    with httpx.Client() as client:
        response = client.post(url, data=data, timeout=10)
        response.raise_for_status()

    print(f"  ✅ Notification sent")


def ping_healthchecks(ping_url: str, diagnostic_data: str, is_healthy: bool):
    """
    Ping Healthchecks.io Dead Man's Switch.

    Args:
        ping_url: Healthchecks.io ping URL
        diagnostic_data: Diagnostic message
        is_healthy: Whether system is healthy

    Raises:
        httpx.HTTPError: If ping fails
    """
    print(f"[HEALTHCHECKS] Pinging...")

    # Use /fail endpoint if unhealthy
    url = f"{ping_url}/fail" if not is_healthy else ping_url

    with httpx.Client() as client:
        response = client.post(url, content=diagnostic_data, timeout=10)
        response.raise_for_status()

    print(f"  ✅ Pinged Healthchecks.io")


# ================================================================================
# Main Logic
# ================================================================================

def main():
    """
    Main entry point.

    Exit codes:
        0: Healthy (no gaps, data fresh)
        1: Unhealthy (gaps detected or data stale)
        2: Fatal error
    """
    print("=" * 80)
    print("MotherDuck Gap Detection Monitor (Oracle Cloud)")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}")
    print(f"Database: {MD_DATABASE}.{MD_TABLE}")
    print("=" * 80)
    print()

    try:
        # Step 1: Load secrets from OCI Vault
        secrets = load_secrets()
        print()

        # Step 2: Connect to MotherDuck
        print(f"[MOTHERDUCK] Connecting to {MD_DATABASE}...")
        conn_string = f'md:{MD_DATABASE}?motherduck_token={secrets["motherduck_token"]}'
        conn = duckdb.connect(conn_string)
        print(f"  ✅ Connected")
        print()

        # Step 3: Check staleness
        is_fresh, age_seconds, latest_timestamp, latest_block = check_staleness(conn)
        print()

        # Step 4: Detect gaps
        gaps, total_blocks_checked = detect_gaps(conn)
        print()

        # Step 5: Determine overall health
        is_healthy = is_fresh and len(gaps) == 0

        # Step 6: Build diagnostic messages
        if is_healthy:
            title = "✅ MOTHERDUCK HEALTHY"
            message = (
                f"Blocks: {total_blocks_checked:,}\n"
                f"Latest: {latest_block:,}\n"
                f"Age: {age_seconds}s ago\n"
                f"Gaps: 0\n\n"
                f"Time window: {TIME_WINDOW_START_DAYS}d → {TIME_WINDOW_END_MINUTES}m ago"
            )
        else:
            issues = []
            if not is_fresh:
                issues.append(f"STALE: {age_seconds}s ({age_seconds/60:.1f} min)")
            if gaps:
                max_gap = gaps[0]
                issues.append(f"GAPS: {len(gaps)} found, largest {max_gap['gap_seconds']:.0f}s")

            title = "❌ MOTHERDUCK UNHEALTHY"
            message = (
                f"Issues: {', '.join(issues)}\n\n"
                f"Latest block: {latest_block:,}\n"
                f"Age: {age_seconds}s\n"
                f"Gaps: {len(gaps)}\n\n"
                f"Time window: {TIME_WINDOW_START_DAYS}d → {TIME_WINDOW_END_MINUTES}m ago"
            )

        diagnostic_data = f"{title}\n\n{message}"

        # Step 7: Send notifications
        print("[NOTIFICATIONS]")
        send_pushover_notification(
            secrets["pushover_token"],
            secrets["pushover_user"],
            message,
            title,
            priority=2  # Emergency
        )

        if HEALTHCHECKS_PING_URL:
            ping_healthchecks(HEALTHCHECKS_PING_URL, diagnostic_data, is_healthy)
        else:
            print("  ⚠️  Healthchecks.io ping URL not configured (skipping)")

        print()

        # Step 8: Exit with appropriate code
        if is_healthy:
            print("✅ HEALTH CHECK PASSED")
            return 0
        else:
            print("❌ HEALTH CHECK FAILED")
            return 1

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
