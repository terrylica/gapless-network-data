"""
ClickHouse Gap Detection Monitor (GCP Cloud Functions)

Monitors ClickHouse Ethereum database for gaps and staleness.
Triggered by Cloud Scheduler every 3 hours via HTTP.

Gap Detection:
    - Method: Block number sequence validation
    - Checks: Missing blocks in continuous sequence
    - Uses: ClickHouse lagInFrame() window function with FINAL

Staleness Detection:
    - Threshold: 16 minutes (configurable via STALENESS_THRESHOLD_SECONDS)
    - Rationale: ~80 Ethereum blocks at 12s/block

Monitoring:
    - Healthchecks.io Dead Man's Switch (POST to ping URL)
    - Pushover notifications (emergency for issues, normal for healthy)

HTTP Response Codes:
    200: Healthy (no gaps, data fresh)
    500: Unhealthy (gaps detected or data stale)
    503: Fatal error (query failed, database unreachable)

Environment Variables:
    CLICKHOUSE_HOST: ClickHouse Cloud hostname (from Secret Manager)
    CLICKHOUSE_PORT: ClickHouse port (default: 8443)
    CLICKHOUSE_USER: ClickHouse username (default: default)
    CLICKHOUSE_PASSWORD: ClickHouse password (from Secret Manager)
    STALENESS_THRESHOLD_SECONDS: Max age before data considered stale (default: 960)
    GAP_DETECTION_LIMIT: Max gaps to report (default: 20)
    HEALTHCHECKS_PING_URL: Healthchecks.io ping URL

Related:
    - MADR-0015: Gap Detector ClickHouse Fix
    - MADR-0013: MotherDuck to ClickHouse Migration
"""

import os
from datetime import datetime, timezone

import clickhouse_connect
import httpx
from google.cloud import secretmanager
from ulid import ULID


# ================================================================================
# Semantic Constants
# ================================================================================

# GCP configuration
GCP_PROJECT = os.environ.get('GCP_PROJECT', 'eonlabs-ethereum-bq')

# ClickHouse configuration
CLICKHOUSE_DATABASE = 'ethereum_mainnet'
CLICKHOUSE_TABLE = 'blocks'
CLICKHOUSE_PORT_HTTPS = int(os.environ.get('CLICKHOUSE_PORT', '8443'))
CLICKHOUSE_USER = os.environ.get('CLICKHOUSE_USER', 'default')
CLICKHOUSE_CONNECT_TIMEOUT = 30  # seconds

# Gap detection configuration
GAP_DETECTION_LIMIT = int(os.environ.get('GAP_DETECTION_LIMIT', '20'))

# Staleness threshold: 16 minutes (~80 Ethereum blocks at 12s/block)
# Rationale: Allows for temporary pipeline delays without false positives
STALENESS_THRESHOLD_SECONDS = int(os.environ.get('STALENESS_THRESHOLD_SECONDS', '960'))

# Healthchecks.io ping URL (from environment)
HEALTHCHECKS_PING_URL = os.environ.get('HEALTHCHECKS_PING_URL', '')


# ================================================================================
# Secret Management (GCP Secret Manager)
# ================================================================================

def get_secret(secret_id: str, project_id: str = GCP_PROJECT) -> str:
    """
    Fetch secret from Google Secret Manager.

    Args:
        secret_id: Secret name (e.g., 'clickhouse-host')
        project_id: GCP project ID

    Returns:
        Secret value as string

    Raises:
        Exception: If secret fetch fails (no fallback, fail-fast)
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8').strip()


def load_secrets() -> dict[str, str]:
    """
    Load required secrets from GCP Secret Manager.

    Returns:
        Dictionary with pushover_token and pushover_user

    Raises:
        Exception: If secret fetch fails (no fallback, fail-fast)
    """
    print("[SECRETS] Loading secrets from GCP Secret Manager...")

    secrets = {
        'pushover_token': get_secret('pushover-token'),
        'pushover_user': get_secret('pushover-user'),
    }

    print(f"  Loaded {len(secrets)} notification secrets")
    return secrets


def get_clickhouse_client():
    """
    Create ClickHouse client using environment variables.

    Environment Variables:
        CLICKHOUSE_HOST: ClickHouse Cloud hostname
        CLICKHOUSE_PASSWORD: ClickHouse password

    Returns:
        clickhouse_connect Client instance

    Raises:
        ValueError: If required environment variables missing
        Exception: If connection fails (no fallback, fail-fast)
    """
    print(f"[CLICKHOUSE] Connecting to {CLICKHOUSE_DATABASE}.{CLICKHOUSE_TABLE}...")

    # Use environment variables (set in Cloud Function config)
    host = os.environ.get('CLICKHOUSE_HOST')
    password = os.environ.get('CLICKHOUSE_PASSWORD')

    if not host or not password:
        raise ValueError("CLICKHOUSE_HOST and CLICKHOUSE_PASSWORD environment variables required")

    client = clickhouse_connect.get_client(
        host=host,
        port=CLICKHOUSE_PORT_HTTPS,
        username=CLICKHOUSE_USER,
        password=password,
        secure=True,
        connect_timeout=CLICKHOUSE_CONNECT_TIMEOUT,
    )

    print(f"  Connected (server {client.server_version})")
    return client


# ================================================================================
# Gap Detection (ClickHouse-Native)
# ================================================================================

def detect_gaps_clickhouse(client) -> tuple[list[dict], int, int, int]:
    """
    Detect data collection gaps using block number sequence validation.

    Uses ClickHouse FINAL modifier for accurate counts with ReplacingMergeTree.
    Uses lagInFrame() window function for gap detection.

    Args:
        client: ClickHouse client

    Returns:
        Tuple of (gap_list, total_blocks, min_block, max_block)

    Raises:
        Exception: If query fails (no fallback, fail-fast)
    """
    print(f"[GAP DETECTION] Analyzing block sequence...")

    # Get block statistics with FINAL for deduplication
    result = client.query(f"""
        SELECT
            COUNT(*) as total,
            MIN(number) as min_block,
            MAX(number) as max_block
        FROM {CLICKHOUSE_DATABASE}.{CLICKHOUSE_TABLE} FINAL
    """)

    total, min_block, max_block = result.result_rows[0]
    # Handle block 0 (genesis) - check for None, not truthiness
    expected = (max_block - min_block + 1) if min_block is not None else 0
    missing = expected - total

    print(f"  Block range: {min_block:,} to {max_block:,}")
    print(f"  Expected: {expected:,} blocks")
    print(f"  Actual: {total:,} blocks")
    print(f"  Missing: {missing:,} blocks")

    gaps = []

    if missing > 0:
        print(f"  Searching for gap locations...")

        # Find gaps using window function
        gap_result = client.query(f"""
            WITH block_gaps AS (
                SELECT
                    number,
                    lagInFrame(number, 1) OVER (ORDER BY number
                        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                    ) as prev_block,
                    number - lagInFrame(number, 1) OVER (ORDER BY number
                        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                    ) - 1 as gap_size
                FROM {CLICKHOUSE_DATABASE}.{CLICKHOUSE_TABLE} FINAL
            )
            SELECT
                prev_block + 1 as start_missing,
                number - 1 as end_missing,
                gap_size
            FROM block_gaps
            WHERE gap_size > 0
            ORDER BY gap_size DESC
            LIMIT {GAP_DETECTION_LIMIT}
        """)

        for row in gap_result.result_rows:
            start_missing, end_missing, gap_size = row
            gaps.append({
                'block_number': start_missing,
                'gap_type': 'missing_block',
                'description': f'{gap_size} blocks missing: {start_missing:,} to {end_missing:,}',
            })

        print(f"  Found {len(gaps)} gap regions")
        if gaps:
            print(f"  Largest gap: {gaps[0]['description']}")
    else:
        print(f"  Block sequence complete")

    return gaps, total, min_block, max_block


def check_staleness_clickhouse(client) -> tuple[bool, int, datetime, int]:
    """
    Check if latest block data is stale.

    Args:
        client: ClickHouse client

    Returns:
        Tuple of (is_fresh, age_seconds, latest_timestamp, latest_block)

    Raises:
        ValueError: If no blocks found
        Exception: If query fails (no fallback, fail-fast)
    """
    print(f"[STALENESS] Checking data freshness...")

    result = client.query(f"""
        SELECT MAX(number), MAX(timestamp)
        FROM {CLICKHOUSE_DATABASE}.{CLICKHOUSE_TABLE} FINAL
    """)

    row = result.result_rows[0]
    latest_block = row[0]
    latest_timestamp = row[1]

    if latest_block is None:
        raise ValueError(f"No blocks found in {CLICKHOUSE_DATABASE}.{CLICKHOUSE_TABLE}")

    # Calculate age
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    age_seconds = int((now - latest_timestamp).total_seconds())
    is_fresh = age_seconds <= STALENESS_THRESHOLD_SECONDS

    print(f"  Latest block: {latest_block:,}")
    print(f"  Latest timestamp: {latest_timestamp}")
    print(f"  Age: {age_seconds}s")
    print(f"  Fresh: {is_fresh} (threshold: {STALENESS_THRESHOLD_SECONDS}s)")

    return is_fresh, age_seconds, latest_timestamp, latest_block


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
    Send Pushover notification with unique ULID identifier.

    Args:
        token: Pushover application token
        user: Pushover user key
        message: Notification message
        title: Notification title
        priority: Priority level (0=normal, 2=emergency)

    Raises:
        httpx.HTTPError: If request fails (no fallback, fail-fast)
    """
    print(f"[PUSHOVER] Sending notification (priority={priority})...")

    # Generate ULID for traceability
    ulid = str(ULID())

    # Append ULID to message
    message_with_id = f"{message}\n\nULID: {ulid}"

    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": token,
        "user": user,
        "message": message_with_id,
        "title": title,
        "priority": priority,
    }

    # Emergency priority requires retry/expire
    if priority == 2:
        data["retry"] = 60      # Retry every 60 seconds
        data["expire"] = 3600   # Give up after 1 hour

    with httpx.Client() as http_client:
        response = http_client.post(url, data=data, timeout=10)
        response.raise_for_status()

    print(f"  Sent (ULID: {ulid})")


def ping_healthchecks(ping_url: str, diagnostic_data: str, is_healthy: bool):
    """
    Ping Healthchecks.io Dead Man's Switch.

    Args:
        ping_url: Healthchecks.io ping URL
        diagnostic_data: Diagnostic message to include
        is_healthy: Whether system is healthy (False uses /fail endpoint)

    Raises:
        httpx.HTTPError: If ping fails (no fallback, fail-fast)
    """
    print(f"[HEALTHCHECKS] Pinging...")

    # Use /fail endpoint if unhealthy
    url = f"{ping_url}/fail" if not is_healthy else ping_url

    with httpx.Client() as http_client:
        response = http_client.post(url, content=diagnostic_data, timeout=10)
        response.raise_for_status()

    endpoint = "/fail" if not is_healthy else ""
    print(f"  Pinged Healthchecks.io{endpoint}")


# ================================================================================
# Cloud Functions Entry Point
# ================================================================================

def monitor(request):
    """
    Cloud Functions HTTP entry point.

    Triggered by Cloud Scheduler every 3 hours.

    Args:
        request: Flask request object (unused)

    Returns:
        Tuple of (response_body, http_status_code)
            200: Healthy (no gaps, data fresh)
            500: Unhealthy (gaps detected or data stale)
            503: Fatal error
    """
    print("=" * 80)
    print("ClickHouse Gap Detection Monitor")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}")
    print(f"Database: {CLICKHOUSE_DATABASE}.{CLICKHOUSE_TABLE}")
    print(f"Staleness threshold: {STALENESS_THRESHOLD_SECONDS}s")
    print("=" * 80)
    print()

    try:
        # Step 1: Load notification secrets
        secrets = load_secrets()
        print()

        # Step 2: Connect to ClickHouse
        client = get_clickhouse_client()
        print()

        # Step 3: Check staleness
        is_fresh, age_seconds, latest_timestamp, latest_block = check_staleness_clickhouse(client)
        print()

        # Step 4: Detect gaps
        gaps, total_blocks, min_block, max_block = detect_gaps_clickhouse(client)
        print()

        # Step 5: Determine health status
        is_healthy = is_fresh and len(gaps) == 0

        # Step 6: Build notification message
        if is_healthy:
            title = "HEALTHY"
            message = (
                f"Blocks: {total_blocks:,}\n"
                f"Range: {min_block:,} to {max_block:,}\n"
                f"Age: {age_seconds}s\n"
                f"Gaps: None\n"
                f"Sequence: Complete"
            )
            notification_priority = 0  # Normal priority when healthy
        else:
            issues = []
            if not is_fresh:
                issues.append(f"STALE ({age_seconds}s)")
            if gaps:
                issues.append(f"GAPS ({len(gaps)} regions)")

            title = "UNHEALTHY"
            gap_detail = ""
            if gaps:
                if len(gaps) <= 3:
                    gap_detail = "\n\nGaps:\n" + "\n".join(
                        [f"  {g['description']}" for g in gaps]
                    )
                else:
                    gap_detail = f"\n\nLargest gap: {gaps[0]['description']}"

            message = (
                f"Issues: {', '.join(issues)}\n\n"
                f"Blocks: {total_blocks:,}\n"
                f"Range: {min_block:,} to {max_block:,}\n"
                f"Age: {age_seconds}s"
                f"{gap_detail}"
            )
            notification_priority = 2  # Emergency priority for issues

        diagnostic_data = f"{title}\n\n{message}"

        # Step 7: Send notifications
        print("[NOTIFICATIONS]")
        send_pushover_notification(
            secrets["pushover_token"],
            secrets["pushover_user"],
            message,
            title,
            priority=notification_priority
        )

        if HEALTHCHECKS_PING_URL:
            ping_healthchecks(HEALTHCHECKS_PING_URL, diagnostic_data, is_healthy)
        else:
            print("  Healthchecks.io not configured (skipping)")

        print()

        # Step 8: Return HTTP response
        if is_healthy:
            print("RESULT: HEALTHY")
            return ({"status": "healthy", "blocks": total_blocks, "latest": latest_block}, 200)
        else:
            print("RESULT: UNHEALTHY")
            return ({"status": "unhealthy", "message": message}, 500)

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

        # Best-effort Healthchecks /fail ping
        if HEALTHCHECKS_PING_URL:
            try:
                error_msg = f"FATAL ERROR\n\n{e.__class__.__name__}: {e}"
                with httpx.Client() as http_client:
                    http_client.post(
                        f"{HEALTHCHECKS_PING_URL}/fail",
                        content=error_msg,
                        timeout=10
                    )
                print(f"  Pinged Healthchecks.io/fail")
            except Exception:
                pass  # Don't mask original error

        return ({"status": "fatal_error", "error": str(e)}, 503)
