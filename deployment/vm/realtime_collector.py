#!/usr/bin/env python3
# /// script
# dependencies = ["websockets", "pyarrow", "google-cloud-secret-manager", "requests", "clickhouse-connect", "tenacity"]
# ///
"""
Alchemy WebSocket Real-Time Ethereum Block Collector

Subscribes to Alchemy's newHeads WebSocket stream for real-time block notifications.
On each new block, fetches full block data via eth_getBlockByNumber to get accurate
transaction_count (newHeads only returns headers without transactions array).
Writes to ClickHouse Cloud. Designed to run as a long-lived systemd service on VM.

Environment Variables:
    GCP_PROJECT: GCP project ID (default: eonlabs-ethereum-bq)
    BATCH_INTERVAL_SECONDS: Batch write interval in seconds (default: 300 = 5 minutes)
                            Set to 0 for immediate writes (real-time mode)
    CLICKHOUSE_HOST: ClickHouse Cloud hostname (required)
    CLICKHOUSE_PORT: ClickHouse port (default: 8443)
    CLICKHOUSE_USER: ClickHouse username (default: default)
    CLICKHOUSE_PASSWORD: ClickHouse password (required)

Secrets (Google Secret Manager):
    alchemy-api-key: Alchemy API key (fetched via get_secret())

Error Policy: Fail-fast. If ClickHouse write fails, raise exception immediately.
"""

import asyncio
import json
import os
import signal
import sys
import threading
import time
from datetime import datetime, timezone

import requests
import websockets
from google.cloud import secretmanager
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configuration
GCP_PROJECT = os.environ.get('GCP_PROJECT', 'eonlabs-ethereum-bq')
BATCH_INTERVAL_SECONDS = int(os.environ.get('BATCH_INTERVAL_SECONDS', '300'))  # Default: 5 minutes
ALCHEMY_WS_URL = None  # Will be set by validate_config() from Secret Manager
ALCHEMY_HTTP_URL = None  # HTTP endpoint for JSON-RPC calls (eth_getBlockByNumber)
HEALTHCHECK_URL = 'https://hc-ping.com/d73a71f2-9457-4e58-9ed6-8a31db5bbed1'  # Healthchecks.io heartbeat

# ClickHouse configuration
CLICKHOUSE_HOST = os.environ.get('CLICKHOUSE_HOST')
CLICKHOUSE_PORT = int(os.environ.get('CLICKHOUSE_PORT', '8443'))
CLICKHOUSE_USER = os.environ.get('CLICKHOUSE_USER', 'default')
CLICKHOUSE_PASSWORD = os.environ.get('CLICKHOUSE_PASSWORD')
CLICKHOUSE_DATABASE = 'ethereum_mainnet'
CLICKHOUSE_TABLE = 'blocks'

# Global ClickHouse client (initialized in main())
clickhouse_client = None

# Block buffer for batching (thread-safe)
block_buffer = []
buffer_lock = threading.Lock()

# Shutdown flag for graceful termination
shutdown_requested = False

# Resilience constants (ADR: 2025-11-28-gap-collector-resilience)
MAX_RETRY_ATTEMPTS = 3           # Max retries for fetch_full_block
RETRY_WAIT_MIN = 1               # Minimum backoff in seconds
RETRY_WAIT_MAX = 10              # Maximum backoff in seconds
INLINE_BACKFILL_THRESHOLD = 5    # Max blocks to backfill synchronously
MAX_CONSECUTIVE_FAILURES = 10    # Alert threshold for batch flush

# Self-healing gap detection state
expected_next_block = None
missed_blocks = []  # Track blocks that failed fetch for later backfill
missed_blocks_lock = threading.Lock()


def graceful_shutdown(signum, frame):
    """Handle SIGTERM/SIGINT for graceful shutdown with buffer flush.

    This is CRITICAL for systemd service management - without this,
    `systemctl restart` will lose any buffered blocks.
    """
    global shutdown_requested
    shutdown_requested = True

    sig_name = signal.Signals(signum).name
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{now}] [SHUTDOWN] Received {sig_name}, initiating graceful shutdown...")

    # Flush any remaining buffered blocks
    if BATCH_INTERVAL_SECONDS > 0:
        print(f"[{now}] [SHUTDOWN] Flushing remaining buffered blocks...")
        try:
            flushed = flush_buffer()
            print(f"[{now}] [SHUTDOWN] ✅ Flushed {flushed} blocks before exit")
        except Exception as e:
            print(f"[{now}] [SHUTDOWN] ❌ Flush failed: {e}")

    print(f"[{now}] [SHUTDOWN] Exiting cleanly")
    sys.exit(0)


def track_missed_block(block_number: int) -> None:
    """Track a block that couldn't be fetched for later backfill."""
    global missed_blocks
    with missed_blocks_lock:
        if block_number not in missed_blocks:
            missed_blocks.append(block_number)
            now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{now}] [GAP] Tracked missed block {block_number:,} for backfill")


def update_expected_block(received_block: int) -> None:
    """Update expected block and detect gaps inline."""
    global expected_next_block

    if expected_next_block is None:
        expected_next_block = received_block + 1
        return

    # Check for gap
    if received_block > expected_next_block:
        gap_size = received_block - expected_next_block
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{now}] [GAP] Detected gap: expected {expected_next_block:,}, got {received_block:,} ({gap_size} blocks)")

        # Small gap: backfill inline (≤INLINE_BACKFILL_THRESHOLD blocks)
        if gap_size <= INLINE_BACKFILL_THRESHOLD:
            backfill_inline(expected_next_block, received_block - 1)
        else:
            # Large gap: track for async backfill
            for block_num in range(expected_next_block, received_block):
                track_missed_block(block_num)

    expected_next_block = received_block + 1


def backfill_inline(start_block: int, end_block: int) -> None:
    """Backfill small gaps inline (synchronous, ≤INLINE_BACKFILL_THRESHOLD blocks)."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}] [BACKFILL] Inline backfill: blocks {start_block:,} to {end_block:,}")

    for block_num in range(start_block, end_block + 1):
        try:
            block_hex = hex(block_num)
            block_data = fetch_full_block(block_hex)
            if block_data:
                block_tuple = parse_block(block_data)
                insert_block(block_tuple)
                print(f"[{now}] [BACKFILL] Block {block_num:,} backfilled")
        except Exception as e:
            print(f"[{now}] [BACKFILL] Failed to backfill block {block_num:,}: {e}")
            track_missed_block(block_num)


# Block fields to collect (matches BigQuery schema)
BLOCK_FIELDS = [
    'timestamp',
    'number',
    'gasLimit',
    'gasUsed',
    'baseFeePerGas',
    'transactions',  # Will count length
    'difficulty',
    'totalDifficulty',
    'size',
    'blobGasUsed',
    'excessBlobGas'
]


def get_secret(secret_id: str, project_id: str = GCP_PROJECT) -> str:
    """Fetch secret from Google Secret Manager.

    Args:
        secret_id: Secret name (e.g., 'alchemy-api-key')
        project_id: GCP project ID

    Returns:
        Secret value as string
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8').strip()


@retry(
    stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=RETRY_WAIT_MIN, max=RETRY_WAIT_MAX),
    retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout)),
    reraise=True
)
def fetch_full_block(block_number_hex: str) -> dict | None:
    """Fetch full block data via eth_getBlockByNumber JSON-RPC with retry.

    The newHeads subscription only returns block headers (no transactions).
    We need to call eth_getBlockByNumber to get the transaction count.

    Args:
        block_number_hex: Block number in hex format (e.g., '0x1234567')

    Returns:
        Full block data including transactions array, or None if RPC returns null

    Raises:
        Exception: If RPC call fails after MAX_RETRY_ATTEMPTS retries
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_getBlockByNumber",
        "params": [block_number_hex, False]  # False = don't include full tx objects
    }

    response = requests.post(
        ALCHEMY_HTTP_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    response.raise_for_status()

    result = response.json()
    if 'error' in result:
        raise Exception(f"RPC error: {result['error']}")

    return result['result']


def heartbeat_worker():
    """Background thread that pings Healthchecks.io every 5 minutes.

    This provides a Dead Man's Switch monitoring pattern - if the VM or service
    stops running, Healthchecks.io will detect the missing pings and send alerts.
    """
    while True:
        try:
            response = requests.get(HEALTHCHECK_URL, timeout=10)
            response.raise_for_status()
            now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{now}] [HEARTBEAT] Pinged Healthchecks.io")
        except Exception as e:
            now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{now}] [HEARTBEAT] Failed to ping: {e}")

        # Sleep for 5 minutes
        time.sleep(300)


def validate_config():
    """Fetch secrets from Secret Manager and validate configuration."""
    global CLICKHOUSE_HOST, CLICKHOUSE_PASSWORD

    print("[INIT] Fetching secrets from Secret Manager...")

    # Fetch Alchemy API key
    alchemy_key = get_secret('alchemy-api-key')

    # Build Alchemy URLs (WebSocket for subscriptions, HTTP for JSON-RPC)
    global ALCHEMY_WS_URL, ALCHEMY_HTTP_URL
    ALCHEMY_WS_URL = f"wss://eth-mainnet.g.alchemy.com/v2/{alchemy_key}"
    ALCHEMY_HTTP_URL = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_key}"

    # Fetch ClickHouse credentials
    print("[INIT] Fetching ClickHouse credentials...")
    try:
        CLICKHOUSE_HOST = get_secret('clickhouse-host')
        CLICKHOUSE_PASSWORD = get_secret('clickhouse-password')
        print(f"[INIT] ClickHouse credentials loaded (host: {CLICKHOUSE_HOST})")
    except Exception as e:
        raise ValueError(f"ClickHouse secrets required: {e}")

    print("[INIT] Secrets loaded")


def init_clickhouse():
    """Initialize ClickHouse Cloud connection.

    Returns:
        ClickHouse client instance

    Raises:
        ValueError: If required credentials are missing
        Exception: If connection fails (fail-fast policy)
    """
    import clickhouse_connect

    if not CLICKHOUSE_HOST or not CLICKHOUSE_PASSWORD:
        raise ValueError(
            "Missing CLICKHOUSE_HOST or CLICKHOUSE_PASSWORD. "
            "Set via environment variables or Doppler."
        )

    print(f"[INIT] Connecting to ClickHouse Cloud: {CLICKHOUSE_HOST}")

    client = clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        secure=True,
        connect_timeout=30,
    )

    # Verify connection
    version = client.server_version
    print(f"[INIT] ClickHouse connected: {CLICKHOUSE_DATABASE}.{CLICKHOUSE_TABLE} (server {version})")

    return client


def parse_block(block_data):
    """Parse block data from JSON-RPC into database row format.

    Args:
        block_data: Full block object from eth_getBlockByNumber
                   (includes transactions array for accurate count)

    Returns:
        Tuple of values matching table schema
    """
    # Convert hex timestamp to TIMESTAMP
    timestamp_unix = int(block_data['timestamp'], 16)
    timestamp = datetime.fromtimestamp(timestamp_unix, tz=timezone.utc).replace(tzinfo=None)

    # Convert hex fields to integers
    number = int(block_data['number'], 16)
    gas_limit = int(block_data['gasLimit'], 16)
    gas_used = int(block_data['gasUsed'], 16)
    base_fee_per_gas = int(block_data.get('baseFeePerGas', '0x0'), 16)
    transaction_count = len(block_data.get('transactions', []))
    difficulty = int(block_data.get('difficulty', '0x0'), 16)
    total_difficulty = int(block_data.get('totalDifficulty', '0x0'), 16) if block_data.get('totalDifficulty') else None
    size = int(block_data.get('size', '0x0'), 16)
    blob_gas_used = int(block_data.get('blobGasUsed', '0x0'), 16) if block_data.get('blobGasUsed') else None
    excess_blob_gas = int(block_data.get('excessBlobGas', '0x0'), 16) if block_data.get('excessBlobGas') else None

    return (
        timestamp,
        number,
        gas_limit,
        gas_used,
        base_fee_per_gas,
        transaction_count,
        difficulty,
        total_difficulty,
        size,
        blob_gas_used,
        excess_blob_gas
    )


def flush_to_clickhouse(blocks):
    """Flush blocks to ClickHouse (fail-fast on error).

    Args:
        blocks: List of block tuples

    Raises:
        Exception: If ClickHouse insert fails (fail-fast policy)
    """
    global clickhouse_client

    if not clickhouse_client or not blocks:
        return

    # Prepare data for ClickHouse insert
    # Column order: timestamp, number, gas_limit, gas_used, base_fee_per_gas,
    #               transaction_count, difficulty, total_difficulty, size,
    #               blob_gas_used, excess_blob_gas
    column_names = [
        'timestamp', 'number', 'gas_limit', 'gas_used', 'base_fee_per_gas',
        'transaction_count', 'difficulty', 'total_difficulty', 'size',
        'blob_gas_used', 'excess_blob_gas'
    ]

    # Convert tuples to list of lists, handling large integers for UInt256
    rows = []
    for block in blocks:
        row = list(block)
        # Convert difficulty (index 6) and total_difficulty (index 7) to strings
        # ClickHouse UInt256 accepts string representation of large numbers
        row[6] = str(row[6]) if row[6] is not None else '0'
        row[7] = str(row[7]) if row[7] is not None else '0'
        rows.append(row)

    # Insert to ClickHouse (fail-fast: no try/except, let exception propagate)
    clickhouse_client.insert(
        f'{CLICKHOUSE_DATABASE}.{CLICKHOUSE_TABLE}',
        rows,
        column_names=column_names,
    )


def flush_buffer():
    """Flush buffered blocks to ClickHouse.

    Returns:
        Number of blocks flushed

    Error Policy:
        Fail-fast - if ClickHouse write fails, raise exception immediately.
    """
    global block_buffer

    with buffer_lock:
        if not block_buffer:
            return 0

        # Copy buffer and clear
        blocks_to_insert = block_buffer[:]
        block_buffer.clear()

    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    try:
        flush_to_clickhouse(blocks_to_insert)
        print(f"[{now}] [BATCH] Flushed {len(blocks_to_insert)} blocks to ClickHouse")
    except Exception as e:
        print(f"[{now}] [BATCH] ClickHouse flush FAILED: {e}")
        # Re-add blocks to buffer before raising
        with buffer_lock:
            block_buffer.extend(blocks_to_insert)
        raise  # Fail-fast: propagate exception

    return len(blocks_to_insert)


def batch_flush_worker():
    """Background thread that flushes buffer every BATCH_INTERVAL_SECONDS.

    Error Policy: Log errors but continue - service should not crash due to
    temporary ClickHouse issues. Blocks remain in buffer for next flush attempt.
    """
    consecutive_failures = 0

    while not shutdown_requested:
        time.sleep(BATCH_INTERVAL_SECONDS)
        try:
            flushed = flush_buffer()
            if flushed > 0:
                consecutive_failures = 0  # Reset on success
        except Exception as e:
            consecutive_failures += 1
            now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{now}] [BATCH] Flush error ({consecutive_failures}x): {e}")

            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                print(f"[{now}] [BATCH] CRITICAL: {consecutive_failures} consecutive flush failures!")
                # Blocks are still in buffer, will retry next interval


def insert_block(block_tuple):
    """Insert block to ClickHouse.

    Behavior depends on BATCH_INTERVAL_SECONDS:
    - If 0: Immediate write (real-time mode)
    - If >0: Buffer block for batch write

    Args:
        block_tuple: Tuple of block data

    Error Policy:
        Fail-fast - if ClickHouse write fails in immediate mode, raise exception.
    """
    if BATCH_INTERVAL_SECONDS == 0:
        # Immediate write mode (real-time)
        flush_to_clickhouse([block_tuple])
    else:
        # Batch mode: add to buffer
        with buffer_lock:
            block_buffer.append(block_tuple)


async def subscribe_to_blocks():
    """Subscribe to Alchemy newHeads WebSocket stream.

    Flow: newHeads notification -> eth_getBlockByNumber -> parse -> insert
    """
    print(f"[WEBSOCKET] Connecting to Alchemy: {ALCHEMY_WS_URL[:50]}...")

    async with websockets.connect(ALCHEMY_WS_URL) as ws:
        # Subscribe to newHeads
        subscribe_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_subscribe",
            "params": ["newHeads"]
        }

        await ws.send(json.dumps(subscribe_msg))
        print("[WEBSOCKET] Subscribed to eth_subscribe newHeads")

        # Wait for subscription confirmation
        response = await ws.recv()
        sub_response = json.loads(response)

        if 'result' in sub_response:
            subscription_id = sub_response['result']
            print(f"[WEBSOCKET] Subscription ID: {subscription_id}")
        else:
            raise Exception(f"Subscription failed: {sub_response}")

        # Listen for new blocks
        block_count = 0
        print("\n" + "=" * 80)
        if BATCH_INTERVAL_SECONDS == 0:
            print("REAL-TIME STREAMING ACTIVE (Immediate Writes)")
        else:
            print(f"BATCH STREAMING ACTIVE (Flush every {BATCH_INTERVAL_SECONDS}s)")
        print("=" * 80)
        print()

        try:
            async for message in ws:
                # Parse JSON with error handling
                try:
                    data = json.loads(message)
                except json.JSONDecodeError as e:
                    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[{now}] [ERROR] Invalid JSON from WebSocket: {e}")
                    continue  # Skip malformed message, don't crash

                # Check if it's a block notification (safe access)
                if 'params' not in data or 'result' not in data.get('params', {}):
                    continue  # Not a block notification

                block_header = data['params']['result']

                # Defensive check: Ensure block_header is valid
                if block_header is None:
                    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[{now}] [WARN] Received null block header, skipping...")
                    continue

                block_number_hex = block_header.get('number')
                if block_number_hex is None:
                    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[{now}] [WARN] Block header missing 'number' field, skipping...")
                    continue

                # Fetch full block data with retry logic
                try:
                    block_data = fetch_full_block(block_number_hex)
                except Exception as e:
                    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    block_num = int(block_number_hex, 16)
                    print(f"[{now}] [ERROR] Failed to fetch block {block_num:,} after {MAX_RETRY_ATTEMPTS} retries: {e}")
                    track_missed_block(block_num)
                    continue  # Don't crash, continue with next block

                # Defensive check: Ensure block_data is valid
                if block_data is None:
                    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[{now}] [WARN] eth_getBlockByNumber returned null for {block_number_hex}, skipping...")
                    continue

                # Parse and insert block
                block_tuple = parse_block(block_data)
                block_number = block_tuple[1]

                insert_block(block_tuple)
                block_count += 1

                # Update expected block tracking for self-healing gap detection
                update_expected_block(block_number)

                # Print status
                now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                if BATCH_INTERVAL_SECONDS == 0:
                    print(f"[{now}] Block {block_number:,} inserted (total: {block_count:,})")
                else:
                    with buffer_lock:
                        buffer_size = len(block_buffer)
                    print(f"[{now}] Block {block_number:,} buffered (buffer: {buffer_size}, total: {block_count:,})")

        except websockets.exceptions.ConnectionClosed:
            print("\n[WEBSOCKET] Connection closed. Reconnecting...")
            raise  # Will trigger reconnect in main()
        except Exception as e:
            now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{now}] [ERROR] WebSocket loop exception: {e}")
            import traceback
            traceback.print_exc()
            raise  # Trigger reconnect


async def main_loop():
    """Main loop with automatic reconnection."""
    # Subscribe to blocks with automatic reconnection
    retry_count = 0
    max_retries = 3

    while True:
        try:
            await subscribe_to_blocks()
        except Exception as e:
            retry_count += 1
            print(f"\nError: {e}")

            if retry_count >= max_retries:
                print(f"Max retries ({max_retries}) reached. Exiting.")
                # CRITICAL: Flush buffer before exit to prevent data loss
                if BATCH_INTERVAL_SECONDS > 0:
                    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[{now}] [EXIT] Flushing remaining buffered blocks before exit...")
                    try:
                        flushed = flush_buffer()
                        print(f"[{now}] [EXIT] ✅ Flushed {flushed} blocks before exit")
                    except Exception as flush_error:
                        print(f"[{now}] [EXIT] ❌ Flush failed: {flush_error}")
                return 1

            wait_time = min(2 ** retry_count, 60)  # Exponential backoff, max 60s
            print(f"Retrying in {wait_time} seconds... (attempt {retry_count}/{max_retries})")
            await asyncio.sleep(wait_time)
        else:
            # Reset retry count on successful connection
            retry_count = 0


def main():
    """Entry point."""
    global clickhouse_client

    # Register signal handlers for graceful shutdown (CRITICAL for systemd)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    signal.signal(signal.SIGINT, graceful_shutdown)

    print("=" * 80)
    print("Alchemy WebSocket Real-Time Collector (ClickHouse)")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}")
    print(f"ClickHouse: {CLICKHOUSE_DATABASE}.{CLICKHOUSE_TABLE}")
    batch_mode = 'Real-time (immediate writes)' if BATCH_INTERVAL_SECONDS == 0 else f'Batch (flush every {BATCH_INTERVAL_SECONDS}s)'
    print(f"Batch Mode: {batch_mode}")
    print("Signal handlers: SIGTERM/SIGINT → graceful shutdown with buffer flush")
    print("=" * 80)
    print()

    # Validate configuration
    validate_config()

    # Initialize ClickHouse (fail-fast if connection fails)
    clickhouse_client = init_clickhouse()
    print()

    # Start background heartbeat thread for Healthchecks.io monitoring
    print("[INIT] Starting Healthchecks.io heartbeat thread...")
    heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
    heartbeat_thread.start()
    print("[INIT] Heartbeat thread started (pings every 5 minutes)")
    print()

    # Start batch flush worker thread if batching enabled
    if BATCH_INTERVAL_SECONDS > 0:
        print(f"[INIT] Starting batch flush worker (interval: {BATCH_INTERVAL_SECONDS}s)...")
        batch_thread = threading.Thread(target=batch_flush_worker, daemon=True)
        batch_thread.start()
        print("[INIT] Batch flush worker started")
        print()

    try:
        asyncio.run(main_loop())
        return 0
    except SystemExit:
        # Raised by graceful_shutdown signal handler - this is expected
        return 0
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
