"""
ClickHouse Gap Detection Monitor (GCP Cloud Functions)

Monitors ClickHouse Ethereum database for gaps and staleness.
Triggered by Cloud Scheduler every 3 hours via HTTP.

Two-Tier Alerting Strategy (ADR: 2025-11-29-gap-alerting-strategy):
    - Tier 1: New gaps stored in gap_tracking table, NO immediate alert
    - Tier 2: Gaps persisting >30 min trigger EMERGENCY alert
    - Bonus: Gap resolution triggers INFO notification

Gap Detection:
    - Method: Block number sequence validation
    - Checks: Missing blocks in continuous sequence
    - Uses: ClickHouse lagInFrame() window function with FINAL

Staleness Detection:
    - Threshold: 16 minutes (configurable via STALENESS_THRESHOLD_SECONDS)
    - Rationale: ~80 Ethereum blocks at 12s/block

Monitoring:
    - Healthchecks.io Dead Man's Switch (POST to ping URL)
    - Pushover notifications (emergency for persistent gaps, normal for resolved)

HTTP Response Codes:
    200: Healthy (no persistent gaps, data fresh)
    500: Unhealthy (persistent gaps or data stale)
    503: Fatal error (query failed, database unreachable)

Environment Variables:
    CLICKHOUSE_HOST: ClickHouse Cloud hostname (from Secret Manager)
    CLICKHOUSE_PORT: ClickHouse port (default: 8443)
    CLICKHOUSE_USER: ClickHouse username (default: default)
    CLICKHOUSE_PASSWORD: ClickHouse password (from Secret Manager)
    STALENESS_THRESHOLD_SECONDS: Max age before data considered stale (default: 960)
    GAP_DETECTION_LIMIT: Max gaps to report (default: 20)
    GAP_GRACE_PERIOD_SECONDS: Grace period before alerting on gap (default: 1800)
    HEALTHCHECKS_PING_URL: Healthchecks.io ping URL

Related:
    - Design: /docs/design/2025-11-29-gap-alerting-strategy/spec.md
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

# Two-tier alerting: Grace period before alerting on gaps (default: 30 minutes)
# Rationale: Self-healing mechanisms (inline backfill, BigQuery hourly sync) need time
GAP_GRACE_PERIOD_SECONDS = int(os.environ.get('GAP_GRACE_PERIOD_SECONDS', '1800'))

# Gap tracking table for persistence
GAP_TRACKING_TABLE = 'gap_tracking'

# Healthchecks.io ping URL (from environment)
HEALTHCHECKS_PING_URL = os.environ.get('HEALTHCHECKS_PING_URL', '')

# Pushover priority levels (https://pushover.net/api#priority)
PUSHOVER_PRIORITY_EMERGENCY = 2  # Requires acknowledgment, retry/expire params


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
# Two-Tier Gap Tracking
# ================================================================================

def get_tracked_gaps(client) -> list[dict]:
    """
    Get all currently tracked gaps from gap_tracking table.

    Returns:
        List of gap dictionaries with gap_start, gap_end, first_seen, notified
    """
    result = client.query(f"""
        SELECT gap_start, gap_end, gap_size, first_seen, last_seen, notified
        FROM {CLICKHOUSE_DATABASE}.{GAP_TRACKING_TABLE} FINAL
    """)

    return [
        {
            'gap_start': row[0],
            'gap_end': row[1],
            'gap_size': row[2],
            'first_seen': row[3],
            'last_seen': row[4],
            'notified': row[5],
        }
        for row in result.result_rows
    ]


def upsert_gap_tracking(client, gap_start: int, gap_end: int, gap_size: int, now: datetime):
    """
    Insert or update a gap in the tracking table.
    ReplacingMergeTree will keep the latest version based on last_seen.
    """
    # Check if gap already exists
    existing = client.query(f"""
        SELECT first_seen FROM {CLICKHOUSE_DATABASE}.{GAP_TRACKING_TABLE} FINAL
        WHERE gap_start = {gap_start} AND gap_end = {gap_end}
    """)

    if existing.result_rows:
        # Update last_seen
        first_seen = existing.result_rows[0][0]
        client.command(f"""
            INSERT INTO {CLICKHOUSE_DATABASE}.{GAP_TRACKING_TABLE}
            (gap_start, gap_end, gap_size, first_seen, last_seen, notified)
            VALUES ({gap_start}, {gap_end}, {gap_size}, '{first_seen}', '{now}', false)
        """)
    else:
        # New gap
        client.command(f"""
            INSERT INTO {CLICKHOUSE_DATABASE}.{GAP_TRACKING_TABLE}
            (gap_start, gap_end, gap_size, first_seen, last_seen, notified)
            VALUES ({gap_start}, {gap_end}, {gap_size}, '{now}', '{now}', false)
        """)


def mark_gap_notified(client, gap_start: int, gap_end: int, now: datetime):
    """Mark a gap as having been notified."""
    existing = client.query(f"""
        SELECT first_seen FROM {CLICKHOUSE_DATABASE}.{GAP_TRACKING_TABLE} FINAL
        WHERE gap_start = {gap_start} AND gap_end = {gap_end}
    """)

    if existing.result_rows:
        first_seen = existing.result_rows[0][0]
        client.command(f"""
            INSERT INTO {CLICKHOUSE_DATABASE}.{GAP_TRACKING_TABLE}
            (gap_start, gap_end, gap_size, first_seen, last_seen, notified)
            VALUES ({gap_start}, {gap_end}, {gap_end - gap_start + 1}, '{first_seen}', '{now}', true)
        """)


def delete_gap_tracking(client, gap_start: int, gap_end: int):
    """Remove a resolved gap from tracking."""
    client.command(f"""
        ALTER TABLE {CLICKHOUSE_DATABASE}.{GAP_TRACKING_TABLE}
        DELETE WHERE gap_start = {gap_start} AND gap_end = {gap_end}
    """)


def process_gap_tracking(
    client,
    current_gaps: list[dict],
    secrets: dict,
    now: datetime
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Process gaps with two-tier alerting logic.

    Returns:
        Tuple of (new_gaps, persistent_gaps, resolved_gaps)
    """
    print(f"[GAP TRACKING] Processing two-tier alerting...")

    tracked_gaps = get_tracked_gaps(client)
    print(f"  Previously tracked: {len(tracked_gaps)} gaps")

    # Build sets for comparison
    current_gap_keys = {(g['block_number'], g.get('end_block', g['block_number'])) for g in current_gaps}
    tracked_gap_keys = {(g['gap_start'], g['gap_end']) for g in tracked_gaps}

    new_gaps = []
    persistent_gaps = []
    resolved_gaps = []

    # Process current gaps
    for gap in current_gaps:
        gap_start = gap['block_number']
        # Parse end block from description
        desc = gap['description']
        if 'to' in desc:
            gap_end = int(desc.split('to')[-1].strip().replace(',', ''))
        else:
            gap_end = gap_start
        gap_size = gap_end - gap_start + 1

        key = (gap_start, gap_end)

        # Check if already tracked
        tracked = next((t for t in tracked_gaps if (t['gap_start'], t['gap_end']) == key), None)

        if tracked is None:
            # New gap - store but don't alert
            new_gaps.append({'gap_start': gap_start, 'gap_end': gap_end, 'gap_size': gap_size})
            upsert_gap_tracking(client, gap_start, gap_end, gap_size, now)
            print(f"  NEW: {gap_start:,} to {gap_end:,} (tracking, no alert)")
        else:
            # Existing gap - check age
            age_seconds = (now - tracked['first_seen']).total_seconds()

            if age_seconds > GAP_GRACE_PERIOD_SECONDS and not tracked['notified']:
                # Persistent gap - alert!
                persistent_gaps.append({
                    'gap_start': gap_start,
                    'gap_end': gap_end,
                    'gap_size': gap_size,
                    'first_seen': tracked['first_seen'],
                    'age_seconds': int(age_seconds),
                })
                mark_gap_notified(client, gap_start, gap_end, now)
                print(f"  PERSISTENT: {gap_start:,} to {gap_end:,} (age: {int(age_seconds)}s > {GAP_GRACE_PERIOD_SECONDS}s)")
            else:
                # Still in grace period - update last_seen
                upsert_gap_tracking(client, gap_start, gap_end, gap_size, now)
                print(f"  GRACE: {gap_start:,} to {gap_end:,} (age: {int(age_seconds)}s)")

    # Check for resolved gaps
    for tracked in tracked_gaps:
        key = (tracked['gap_start'], tracked['gap_end'])
        if key not in current_gap_keys:
            resolved_gaps.append(tracked)
            delete_gap_tracking(client, tracked['gap_start'], tracked['gap_end'])
            print(f"  RESOLVED: {tracked['gap_start']:,} to {tracked['gap_end']:,}")

    return new_gaps, persistent_gaps, resolved_gaps


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
    if priority == PUSHOVER_PRIORITY_EMERGENCY:
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
    Cloud Functions HTTP entry point with two-tier gap alerting.

    Triggered by Cloud Scheduler every 3 hours.

    Two-Tier Alerting:
        - New gaps: Stored in gap_tracking, NO immediate alert
        - Persistent gaps (>30 min): Emergency alert
        - Resolved gaps: Info notification

    Args:
        request: Flask request object (unused)

    Returns:
        Tuple of (response_body, http_status_code)
            200: Healthy (no persistent gaps, data fresh)
            500: Unhealthy (persistent gaps or data stale)
            503: Fatal error
    """
    print("=" * 80)
    print("ClickHouse Gap Detection Monitor (Two-Tier Alerting)")
    print("=" * 80)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    print(f"Timestamp: {now.isoformat()}Z")
    print(f"Database: {CLICKHOUSE_DATABASE}.{CLICKHOUSE_TABLE}")
    print(f"Staleness threshold: {STALENESS_THRESHOLD_SECONDS}s")
    print(f"Gap grace period: {GAP_GRACE_PERIOD_SECONDS}s")
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

        # Step 4: Detect current gaps
        gaps, total_blocks, min_block, max_block = detect_gaps_clickhouse(client)
        print()

        # Step 5: Process gaps with two-tier alerting
        new_gaps, persistent_gaps, resolved_gaps = process_gap_tracking(
            client, gaps, secrets, now
        )
        print()

        # Step 6: Determine health status (only persistent gaps count)
        is_healthy = is_fresh and len(persistent_gaps) == 0

        # Step 7: Send notifications based on two-tier logic
        print("[NOTIFICATIONS]")
        notifications_sent = 0

        # Send resolution notifications (normal priority)
        for resolved in resolved_gaps:
            duration_mins = int((now - resolved['first_seen']).total_seconds() / 60)
            message = (
                f"Previously tracked gap has been filled\n\n"
                f"Gap: blocks {resolved['gap_start']:,} to {resolved['gap_end']:,}\n"
                f"Size: {resolved['gap_size']} blocks\n"
                f"First detected: {resolved['first_seen']}\n"
                f"Resolved after: {duration_mins} minutes"
            )
            send_pushover_notification(
                secrets["pushover_token"],
                secrets["pushover_user"],
                message,
                "GAP RESOLVED",
                priority=0  # Normal priority
            )
            notifications_sent += 1

        # Send persistent gap notifications (emergency)
        for persistent in persistent_gaps:
            duration_mins = int(persistent['age_seconds'] / 60)
            message = (
                f"Gap persists for >{GAP_GRACE_PERIOD_SECONDS // 60} minutes\n\n"
                f"Gap: blocks {persistent['gap_start']:,} to {persistent['gap_end']:,}\n"
                f"Size: {persistent['gap_size']} blocks\n"
                f"First detected: {persistent['first_seen']}\n"
                f"Duration: {duration_mins} minutes\n\n"
                f"Action required: Manual backfill needed"
            )
            send_pushover_notification(
                secrets["pushover_token"],
                secrets["pushover_user"],
                message,
                "PERSISTENT GAP",
                priority=2  # Emergency
            )
            notifications_sent += 1

        # Send staleness notification if stale (emergency)
        if not is_fresh:
            message = (
                f"Data is stale (>{STALENESS_THRESHOLD_SECONDS}s old)\n\n"
                f"Latest block: {latest_block:,}\n"
                f"Age: {age_seconds}s\n"
                f"Threshold: {STALENESS_THRESHOLD_SECONDS}s"
            )
            send_pushover_notification(
                secrets["pushover_token"],
                secrets["pushover_user"],
                message,
                "DATA STALE",
                priority=2  # Emergency
            )
            notifications_sent += 1

        # If healthy, send normal status (only if no other notifications)
        # ADR: 2025-12-02-pushover-notification-enhancement - comprehensive dashboard format
        if is_healthy and notifications_sent == 0:
            # Compute additional metrics for operational visibility
            staleness_pct = int((age_seconds / STALENESS_THRESHOLD_SECONDS) * 100)
            time_to_stale = STALENESS_THRESHOLD_SECONDS - age_seconds
            latest_ts_str = latest_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

            message = (
                f"Blocks: {total_blocks:,}\n"
                f"Range: {min_block:,} to {max_block:,}\n"
                f"Latest: #{latest_block:,} @ {latest_ts_str}\n"
                f"Age: {age_seconds}s / {STALENESS_THRESHOLD_SECONDS}s threshold ({staleness_pct}%)\n"
                f"Margin: {time_to_stale}s until stale\n"
                f"Gaps: {len(new_gaps)} new | {len(persistent_gaps)} tracked | {len(resolved_gaps)} resolved\n"
                f"Sequence: Complete"
            )
            send_pushover_notification(
                secrets["pushover_token"],
                secrets["pushover_user"],
                message,
                "HEALTHY",
                priority=0  # Normal priority
            )

        # Ping Healthchecks.io
        diagnostic_data = (
            f"Status: {'HEALTHY' if is_healthy else 'UNHEALTHY'}\n"
            f"Fresh: {is_fresh}\n"
            f"New gaps: {len(new_gaps)}\n"
            f"Persistent gaps: {len(persistent_gaps)}\n"
            f"Resolved gaps: {len(resolved_gaps)}"
        )
        if HEALTHCHECKS_PING_URL:
            ping_healthchecks(HEALTHCHECKS_PING_URL, diagnostic_data, is_healthy)
        else:
            print("  Healthchecks.io not configured (skipping)")

        print()

        # Step 8: Return HTTP response
        response_data = {
            "status": "healthy" if is_healthy else "unhealthy",
            "blocks": total_blocks,
            "latest": latest_block,
            "new_gaps": len(new_gaps),
            "persistent_gaps": len(persistent_gaps),
            "resolved_gaps": len(resolved_gaps),
        }

        if is_healthy:
            print("RESULT: HEALTHY")
            return (response_data, 200)
        else:
            print("RESULT: UNHEALTHY")
            return (response_data, 500)

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
