#!/usr/bin/env python3
# /// script
# dependencies = ["websockets", "duckdb", "pyarrow", "google-cloud-secret-manager", "requests"]
# ///
"""
Alchemy WebSocket → MotherDuck Real-Time Ethereum Block Collector

Subscribes to Alchemy's newHeads WebSocket stream for real-time block updates.
Designed to run as a long-lived systemd service on VM.

Environment Variables:
    GCP_PROJECT: GCP project ID (default: eonlabs-ethereum-bq)
    MD_DATABASE: MotherDuck database name (default: ethereum_mainnet)
    MD_TABLE: MotherDuck table name (default: blocks)
    BATCH_INTERVAL_SECONDS: Batch write interval in seconds (default: 300 = 5 minutes)
                            Set to 0 for immediate writes (real-time mode)

Secrets (Google Secret Manager):
    alchemy-api-key: Alchemy API key (fetched via get_secret())
    motherduck-token: MotherDuck authentication token (fetched via get_secret())
"""

import os
import sys
import json
import time
import asyncio
import threading
from datetime import datetime, timezone
from google.cloud import secretmanager
import websockets
import duckdb
import requests

# Configuration
GCP_PROJECT = os.environ.get('GCP_PROJECT', 'eonlabs-ethereum-bq')
MD_DATABASE = os.environ.get('MD_DATABASE', 'ethereum_mainnet')
MD_TABLE = os.environ.get('MD_TABLE', 'blocks')
BATCH_INTERVAL_SECONDS = int(os.environ.get('BATCH_INTERVAL_SECONDS', '300'))  # Default: 5 minutes
ALCHEMY_WS_URL = None  # Will be set by validate_config() from Secret Manager
HEALTHCHECK_URL = 'https://hc-ping.com/d73a71f2-9457-4e58-9ed6-8a31db5bbed1'  # Healthchecks.io heartbeat

# Block buffer for batching (thread-safe)
block_buffer = []
buffer_lock = threading.Lock()

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
        secret_id: Secret name (e.g., 'motherduck-token')
        project_id: GCP project ID

    Returns:
        Secret value as string
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8').strip()


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
            print(f"[{now}] [HEARTBEAT] ✅ Pinged Healthchecks.io")
        except Exception as e:
            now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{now}] [HEARTBEAT] ⚠️  Failed to ping: {e}")

        # Sleep for 5 minutes
        time.sleep(300)


def validate_config():
    """Fetch secrets from Secret Manager and validate configuration."""
    print("[INIT] Fetching secrets from Secret Manager...")

    # Fetch secrets
    alchemy_key = get_secret('alchemy-api-key')
    motherduck_token = get_secret('motherduck-token')

    # Set for DuckDB connection
    os.environ['motherduck_token'] = motherduck_token

    # Build Alchemy WebSocket URL
    global ALCHEMY_WS_URL
    ALCHEMY_WS_URL = f"wss://eth-mainnet.g.alchemy.com/v2/{alchemy_key}"

    print("[INIT] ✅ Secrets loaded")


def init_motherduck():
    """Initialize MotherDuck connection and ensure table exists."""
    print(f"[INIT] Connecting to MotherDuck database: {MD_DATABASE}")

    conn = duckdb.connect('md:', config={'connect_timeout': 30000})  # 30 seconds

    # Create database if needed
    conn.execute(f"CREATE DATABASE IF NOT EXISTS {MD_DATABASE}")
    conn.execute(f"USE {MD_DATABASE}")

    # Create table with same schema as BigQuery pipeline
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {MD_TABLE} (
            timestamp TIMESTAMP NOT NULL,
            number BIGINT PRIMARY KEY,
            gas_limit BIGINT,
            gas_used BIGINT,
            base_fee_per_gas BIGINT,
            transaction_count BIGINT,
            difficulty HUGEINT,
            total_difficulty HUGEINT,
            size BIGINT,
            blob_gas_used BIGINT,
            excess_blob_gas BIGINT
        )
    """)

    print(f"✅ MotherDuck connected: {MD_DATABASE}.{MD_TABLE}")
    return conn


def parse_block(block_data):
    """Parse block data from WebSocket into database row format.

    Args:
        block_data: Block object from eth_subscribe newHeads

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


def flush_buffer(conn):
    """Flush buffered blocks to MotherDuck in a single batch INSERT.

    Args:
        conn: DuckDB connection

    Returns:
        Number of blocks flushed
    """
    global block_buffer

    with buffer_lock:
        if not block_buffer:
            return 0

        # Copy buffer and clear
        blocks_to_insert = block_buffer[:]
        block_buffer.clear()

    # Batch insert all blocks
    try:
        conn.executemany(f"""
            INSERT OR REPLACE INTO {MD_TABLE} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, blocks_to_insert)

        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{now}] [BATCH] ✅ Flushed {len(blocks_to_insert)} blocks to MotherDuck")
        return len(blocks_to_insert)
    except Exception as e:
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{now}] [BATCH] ❌ Failed to flush: {e}")
        # Re-add blocks to buffer for retry
        with buffer_lock:
            block_buffer.extend(blocks_to_insert)
        raise


def batch_flush_worker(conn):
    """Background thread that flushes buffer every BATCH_INTERVAL_SECONDS.

    Args:
        conn: DuckDB connection
    """
    while True:
        time.sleep(BATCH_INTERVAL_SECONDS)
        try:
            flush_buffer(conn)
        except Exception as e:
            now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{now}] [BATCH] ⚠️  Flush error: {e}")


def insert_block(conn, block_tuple):
    """Insert or replace block in MotherDuck.

    Behavior depends on BATCH_INTERVAL_SECONDS:
    - If 0: Immediate write (real-time mode)
    - If >0: Buffer block for batch write

    Args:
        conn: DuckDB connection
        block_tuple: Tuple of block data
    """
    if BATCH_INTERVAL_SECONDS == 0:
        # Immediate write mode (real-time)
        conn.execute(f"""
            INSERT OR REPLACE INTO {MD_TABLE} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, block_tuple)
    else:
        # Batch mode: add to buffer
        with buffer_lock:
            block_buffer.append(block_tuple)


async def subscribe_to_blocks(conn):
    """Subscribe to Alchemy newHeads WebSocket stream.

    Args:
        conn: DuckDB connection for inserting blocks
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
        print("✅ Subscribed to eth_subscribe newHeads")

        # Wait for subscription confirmation
        response = await ws.recv()
        sub_response = json.loads(response)

        if 'result' in sub_response:
            subscription_id = sub_response['result']
            print(f"✅ Subscription ID: {subscription_id}")
        else:
            raise Exception(f"Subscription failed: {sub_response}")

        # Listen for new blocks
        block_count = 0
        print("\n" + "=" * 80)
        if BATCH_INTERVAL_SECONDS == 0:
            print("🔴 REAL-TIME STREAMING ACTIVE (Immediate Writes)")
        else:
            print(f"🔴 BATCH STREAMING ACTIVE (Flush every {BATCH_INTERVAL_SECONDS}s)")
        print("=" * 80)
        print()

        try:
            async for message in ws:
                data = json.loads(message)

                # Check if it's a block notification
                if 'params' in data and 'result' in data['params']:
                    block_data = data['params']['result']

                    # Parse and insert block
                    block_tuple = parse_block(block_data)
                    block_number = block_tuple[1]

                    insert_block(conn, block_tuple)
                    block_count += 1

                    # Print status
                    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    if BATCH_INTERVAL_SECONDS == 0:
                        print(f"[{now}] ✅ Block {block_number:,} inserted (total: {block_count:,})")
                    else:
                        with buffer_lock:
                            buffer_size = len(block_buffer)
                        print(f"[{now}] ✅ Block {block_number:,} buffered (buffer: {buffer_size}, total: {block_count:,})")

        except websockets.exceptions.ConnectionClosed:
            print("\n⚠️  WebSocket connection closed. Reconnecting...")
            raise  # Will trigger reconnect in main()


async def main_loop(conn):
    """Main loop with automatic reconnection.

    Args:
        conn: DuckDB connection (passed from main())
    """
    # Subscribe to blocks with automatic reconnection
    retry_count = 0
    max_retries = 3

    while True:
        try:
            await subscribe_to_blocks(conn)
        except Exception as e:
            retry_count += 1
            print(f"\n❌ Error: {e}")

            if retry_count >= max_retries:
                print(f"❌ Max retries ({max_retries}) reached. Exiting.")
                return 1

            wait_time = min(2 ** retry_count, 60)  # Exponential backoff, max 60s
            print(f"⏳ Retrying in {wait_time} seconds... (attempt {retry_count}/{max_retries})")
            await asyncio.sleep(wait_time)
        else:
            # Reset retry count on successful connection
            retry_count = 0


def main():
    """Entry point."""
    print("=" * 80)
    print("Alchemy WebSocket → MotherDuck Real-Time Collector")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}")
    print(f"Database: {MD_DATABASE}.{MD_TABLE}")
    if BATCH_INTERVAL_SECONDS == 0:
        print(f"Mode: Real-time (immediate writes)")
    else:
        print(f"Mode: Batch (flush every {BATCH_INTERVAL_SECONDS}s)")
    print("=" * 80)
    print()

    # Validate configuration
    validate_config()

    # Initialize MotherDuck
    conn = init_motherduck()
    print()

    # Start background heartbeat thread for Healthchecks.io monitoring
    print("[INIT] Starting Healthchecks.io heartbeat thread...")
    heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
    heartbeat_thread.start()
    print("✅ Heartbeat thread started (pings every 5 minutes)")
    print()

    # Start batch flush worker thread if batching enabled
    if BATCH_INTERVAL_SECONDS > 0:
        print(f"[INIT] Starting batch flush worker (interval: {BATCH_INTERVAL_SECONDS}s)...")
        batch_thread = threading.Thread(target=batch_flush_worker, args=(conn,), daemon=True)
        batch_thread.start()
        print("✅ Batch flush worker started")
        print()

    try:
        asyncio.run(main_loop(conn))
        return 0
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user (Ctrl+C)")
        # Flush any remaining buffered blocks before exit
        if BATCH_INTERVAL_SECONDS > 0:
            print("\n[SHUTDOWN] Flushing remaining buffered blocks...")
            try:
                flushed = flush_buffer(conn)
                print(f"✅ Flushed {flushed} blocks")
            except Exception as e:
                print(f"⚠️  Flush failed: {e}")
        return 0
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
