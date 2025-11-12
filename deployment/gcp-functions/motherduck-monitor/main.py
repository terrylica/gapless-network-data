"""
MotherDuck Gap Detection Monitor (GCP Cloud Functions)

Monitors MotherDuck Ethereum database for gaps and staleness.
Triggered by Cloud Scheduler every 3 hours via HTTP.

Gap Detection:
    - Time window: 1 year ago → 3 minutes ago
    - Threshold: >15 seconds (Ethereum ~12s block time + 3s tolerance)
    - Method: DuckDB LAG() window function

Monitoring:
    - Healthchecks.io Dead Man's Switch (POST to ping URL)
    - Pushover emergency notifications (all executions)

HTTP Response Codes:
    200: Healthy (no gaps, data fresh)
    500: Unhealthy (gaps detected or data stale)
    503: Fatal error (query failed, MotherDuck unreachable)
"""

import os
from datetime import datetime, timezone

import duckdb
import httpx
from google.cloud import secretmanager
from ulid import ULID


# ================================================================================
# Configuration
# ================================================================================

# GCP configuration
GCP_PROJECT = os.environ.get('GCP_PROJECT', 'eonlabs-ethereum-bq')

# MotherDuck configuration
MD_DATABASE = os.environ.get('MD_DATABASE', 'ethereum_mainnet')
MD_TABLE = os.environ.get('MD_TABLE', 'blocks')

# Gap detection configuration
GAP_THRESHOLD_SECONDS = int(os.environ.get('GAP_THRESHOLD_SECONDS', '15'))  # Ethereum ~12s + 3s tolerance
TIME_WINDOW_START_DAYS = int(os.environ.get('TIME_WINDOW_START_DAYS', '365'))  # 1 year historical
TIME_WINDOW_END_MINUTES = int(os.environ.get('TIME_WINDOW_END_MINUTES', '3'))  # 3 minutes from now (prevent false positives)

# Staleness threshold
STALE_THRESHOLD_SECONDS = int(os.environ.get('STALE_THRESHOLD_SECONDS', '300'))  # 5 minutes

# Healthchecks.io ping URL (from environment)
HEALTHCHECKS_PING_URL = os.environ.get('HEALTHCHECKS_PING_URL', '')

# Validation method: Deterministic block number continuity checking
# Instead of timestamp gaps (which are normal network behavior), we check:
# - Missing block numbers in sequence
# - Parent hash chain continuity (future enhancement)
# - Transaction index continuity within blocks (future enhancement)


# ================================================================================
# Secret Management (GCP Secret Manager)
# ================================================================================

def get_secret(secret_id: str, project_id: str = GCP_PROJECT) -> str:
    """
    Fetch secret from Google Secret Manager.

    Args:
        secret_id: Secret name (e.g., 'motherduck-token')
        project_id: GCP project ID

    Returns:
        Secret value as string

    Raises:
        Exception: If secret fetch fails
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8').strip()


def load_secrets() -> dict[str, str]:
    """
    Load all secrets from GCP Secret Manager.

    Returns:
        Dictionary of secret values

    Raises:
        Exception: If secret fetch fails
    """
    print("[SECRETS] Loading secrets from GCP Secret Manager...")

    secrets = {
        'motherduck_token': get_secret('motherduck-token'),
        'pushover_token': get_secret('pushover-token'),
        'pushover_user': get_secret('pushover-user'),
    }

    print(f"✅ Loaded {len(secrets)} secrets")
    return secrets


# ================================================================================
# Gap Detection
# ================================================================================

def detect_gaps(conn: duckdb.DuckDBPyConnection) -> tuple[list[dict], int]:
    """
    Detect data collection gaps using deterministic block number validation.

    Uses Ethereum's deterministic counters (block numbers) rather than timestamps
    to detect actual missing data vs normal network timing variations.

    Checks the ENTIRE blockchain history in the database (not just a time window)
    since deterministic validation is computationally efficient.

    Args:
        conn: DuckDB connection

    Returns:
        Tuple of (gap_list, total_blocks_checked)

    Raises:
        Exception: If query fails
    """
    print(f"[GAP DETECTION] Analyzing complete block sequence...")
    print(f"  Method: Block number continuity (deterministic)")
    print(f"  Scope: Entire blockchain history in database")

    # Get block range for entire database
    range_query = f"""
    SELECT MIN(number) as min_block, MAX(number) as max_block, COUNT(*) as total_blocks
    FROM {MD_TABLE}
    """
    range_result = conn.execute(range_query).fetchone()
    min_block = range_result[0]
    max_block = range_result[1]
    total_blocks = range_result[2]

    expected_blocks = (max_block - min_block + 1) if min_block is not None else 0

    print(f"  Block range: {min_block:,} → {max_block:,}")
    print(f"  Expected blocks: {expected_blocks:,}")
    print(f"  Actual blocks: {total_blocks:,}")

    # Check for missing blocks using efficient comparison
    # If expected == actual, no need to search for specific missing blocks
    missing_count = expected_blocks - total_blocks
    gaps = []

    if missing_count > 0:
        # Only search for specific missing blocks if there are gaps
        # Use efficient chunking to avoid memory issues
        print(f"  Searching for {missing_count} missing blocks...")

        # Sample approach: Check gaps between consecutive blocks
        gap_query = f"""
        WITH block_gaps AS (
            SELECT
                number as current_block,
                LAG(number) OVER (ORDER BY number) as prev_block,
                number - LAG(number) OVER (ORDER BY number) - 1 as missing_count
            FROM {MD_TABLE}
            WHERE number BETWEEN {min_block} AND {max_block}
        )
        SELECT current_block, prev_block, missing_count
        FROM block_gaps
        WHERE missing_count > 0
        ORDER BY missing_count DESC
        LIMIT 20
        """

        result = conn.execute(gap_query).fetchall()

        for row in result:
            current_block = row[0]
            prev_block = row[1]
            gap_size = row[2]

            # Report the first missing block in each gap
            first_missing = prev_block + 1
            gaps.append({
                'block_number': first_missing,
                'gap_type': 'missing_block',
                'description': f'{int(gap_size)} blocks missing: {first_missing:,} to {current_block-1:,}',
            })

    print(f"  Missing blocks: {missing_count}")

    if missing_count > 0:
        print(f"  ⚠️  DATA COLLECTION ISSUE: {missing_count} blocks missing from sequence")
        if missing_count <= 10:
            for gap in gaps[:10]:
                print(f"     Missing: Block {gap['block_number']:,}")
        else:
            print(f"     First missing: Block {gaps[0]['block_number']:,}")
            print(f"     Last missing: Block {gaps[-1]['block_number']:,}")
    else:
        print(f"  ✅ All blocks present in sequence (no data gaps)")

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
    Send Pushover notification with unique ULID identifier.

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

    # Generate ULID (26-char timestamped unique identifier)
    ulid = str(ULID())

    # Append ULID to message (at bottom)
    message_with_id = f"{message}\n\nULID: {ulid}"

    url = "https://api.pushover.net/1/messages.json"
    data = {
        "token": token,
        "user": user,
        "message": message_with_id,
        "title": title,
        "priority": priority,
    }

    # Emergency priority (2) requires retry and expire
    if priority == 2:
        data["retry"] = 60  # Retry every 60 seconds
        data["expire"] = 3600  # Give up after 1 hour

    with httpx.Client() as client:
        response = client.post(url, data=data, timeout=10)
        response.raise_for_status()

    print(f"  ✅ Notification sent (ID: {ulid})")


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
# Cloud Functions Entry Point
# ================================================================================

def monitor(request):
    """
    Cloud Functions HTTP entry point.

    Triggered by Cloud Scheduler every 3 hours.

    Args:
        request: Flask request object (unused, Cloud Scheduler POST)

    Returns:
        Tuple of (response_body, http_status_code)
            200: Healthy (no gaps, data fresh)
            500: Unhealthy (gaps detected or data stale)
            503: Fatal error
    """
    print("=" * 80)
    print("MotherDuck Gap Detection Monitor (GCP Cloud Functions)")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}")
    print(f"Database: {MD_DATABASE}.{MD_TABLE}")
    print("=" * 80)
    print()

    try:
        # Step 1: Load secrets from GCP Secret Manager
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
                f"Total blocks: {total_blocks_checked:,}\n"
                f"Latest: {latest_block:,}\n"
                f"Age: {age_seconds}s\n"
                f"Missing blocks: 0\n"
                f"Sequence: Complete\n\n"
                f"Validation: Entire blockchain history"
            )
        else:
            issues = []
            if not is_fresh:
                issues.append(f"STALE: {age_seconds}s ({age_seconds/60:.1f} min)")
            if gaps:
                issues.append(f"MISSING BLOCKS: {len(gaps)} blocks not in database")

            title = "❌ MOTHERDUCK UNHEALTHY"

            # Build gap details for missing blocks
            gap_details = ""
            if gaps:
                if len(gaps) <= 5:
                    # Show all missing blocks if <= 5
                    missing_list = ", ".join([str(g['block_number']) for g in gaps])
                    gap_details = f"\n\nMissing blocks: {missing_list}"
                else:
                    # Show first and last if > 5
                    first_missing = gaps[0]['block_number']
                    last_missing = gaps[-1]['block_number']
                    gap_details = (
                        f"\n\nMissing blocks:\n"
                        f"First: {first_missing:,}\n"
                        f"Last: {last_missing:,}\n"
                        f"Total: {len(gaps)}"
                    )

            message = (
                f"Issues: {', '.join(issues)}\n\n"
                f"Latest block: {latest_block:,}\n"
                f"Age: {age_seconds}s\n"
                f"Missing: {len(gaps)} blocks"
                f"{gap_details}\n\n"
                f"Validation: Entire blockchain history"
            )

        diagnostic_data = f"{title}\n\n{message}"

        # Step 7: Send notifications
        print("[NOTIFICATIONS]")
        # Emergency priority only for actual problems, regular priority when healthy
        notification_priority = 0 if is_healthy else 2
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
            print("  ⚠️  Healthchecks.io ping URL not configured (skipping)")

        print()

        # Step 8: Return HTTP response
        if is_healthy:
            print("✅ HEALTH CHECK PASSED")
            return ({"status": "healthy", "message": message}, 200)
        else:
            print("❌ HEALTH CHECK FAILED")
            return ({"status": "unhealthy", "message": message}, 500)

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return ({"status": "fatal_error", "error": str(e)}, 503)
