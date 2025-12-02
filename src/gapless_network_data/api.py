"""
Public API for gapless-network-data.

This module provides the main programmatic interface for:
- Ethereum block data (via ClickHouse) with alpha feature rankings
- Bitcoin mempool pressure data (via mempool.space) - forward-only collection

Alpha Feature Rankings (for AI agents):
    #1 base_fee_per_gas - Fee prediction (most valuable)
    #2 gas_used/gas_limit - Congestion leading indicator
    #3 transaction_count - Network activity proxy
    #4-6 timestamp, number, size - Temporal alignment
    #7-8 blob_gas_used, excess_blob_gas - L2 metrics (post-Mar 2024)

Deprecated (excluded by default):
    - difficulty: Always 0 post-Merge (Sep 2022)
    - total_difficulty: Frozen post-Merge

For detailed rankings, call probe.get_alpha_features().
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from typing import TYPE_CHECKING

import pandas as pd
from dotenv import load_dotenv

from gapless_network_data.collectors.mempool_collector import MempoolCollector
from gapless_network_data.exceptions import CredentialException, DatabaseException

if TYPE_CHECKING:
    import clickhouse_connect


# Protocol era block boundaries (semantic constants)
EIP_1559_BLOCK = 12_965_000  # Aug 2021 - base_fee_per_gas introduced
MERGE_BLOCK = 15_537_394  # Sep 2022 - PoW→PoS, difficulty=0 forever
EIP_4844_BLOCK = 19_426_587  # Mar 2024 - blob_gas introduced


def _get_clickhouse_credentials() -> tuple[str, str, str]:
    """
    Resolve ClickHouse credentials from multiple sources.

    Resolution order:
    1. .env file (auto-loaded via python-dotenv)
    2. Doppler CLI (if configured) - gapless-network-data/prd
    3. Environment variables (CLICKHOUSE_HOST_READONLY, etc.)
    4. Raise CredentialException with setup instructions

    Returns:
        Tuple of (host, user, password)

    Raises:
        CredentialException: If credentials cannot be resolved
    """
    # Load .env file if present (populates os.environ)
    # ADR: 2025-12-01-dotenv-credential-loading
    load_dotenv()

    # Try Doppler first
    try:
        result = subprocess.run(
            [
                "doppler",
                "secrets",
                "get",
                "CLICKHOUSE_HOST_READONLY",
                "CLICKHOUSE_USER_READONLY",
                "CLICKHOUSE_PASSWORD_READONLY",
                "--json",
                "--project",
                "gapless-network-data",
                "--config",
                "prd",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            secrets = json.loads(result.stdout)
            return (
                secrets["CLICKHOUSE_HOST_READONLY"]["computed"],
                secrets["CLICKHOUSE_USER_READONLY"]["computed"],
                secrets["CLICKHOUSE_PASSWORD_READONLY"]["computed"],
            )
    except (FileNotFoundError, json.JSONDecodeError, subprocess.TimeoutExpired, KeyError):
        pass

    # Fall back to env vars
    host = os.environ.get("CLICKHOUSE_HOST_READONLY")
    user = os.environ.get("CLICKHOUSE_USER_READONLY")
    password = os.environ.get("CLICKHOUSE_PASSWORD_READONLY")

    if host and user and password:
        return host, user, password

    # Clear error with setup instructions
    raise CredentialException(
        "ClickHouse credentials not found.\n\n"
        "Option 1: Use .env file (simplest for small teams)\n"
        "  Create .env in your project root with:\n"
        "    CLICKHOUSE_HOST_READONLY=<host>\n"
        "    CLICKHOUSE_USER_READONLY=<user>\n"
        "    CLICKHOUSE_PASSWORD_READONLY=<password>\n\n"
        "Option 2 (Recommended for production): Use Doppler service token\n"
        "  1. Get token from 1Password: Engineering vault → 'gapless-network-data Doppler Service Token'\n"
        "  2. doppler configure set token <token_from_1password>\n"
        "  3. doppler setup --project gapless-network-data --config prd\n\n"
        "Option 3: Set environment variables directly\n"
        "  export CLICKHOUSE_HOST_READONLY=<host>\n"
        "  export CLICKHOUSE_USER_READONLY=<user>\n"
        "  export CLICKHOUSE_PASSWORD_READONLY=<password>\n\n"
        "Contact your team lead for credentials."
    )


def _get_clickhouse_client() -> clickhouse_connect.driver.Client:
    """
    Get authenticated ClickHouse client.

    Returns:
        Configured ClickHouse client

    Raises:
        CredentialException: If credentials cannot be resolved
        DatabaseException: If connection fails
    """
    import clickhouse_connect

    host, user, password = _get_clickhouse_credentials()

    try:
        return clickhouse_connect.get_client(
            host=host,
            port=8443,
            username=user,
            password=password,
            secure=True,
        )
    except Exception as e:
        raise DatabaseException(
            f"Failed to connect to ClickHouse: {e}",
            context={"host": host, "user": user},
        ) from e


def fetch_blocks(
    start: str | None = None,
    end: str | None = None,
    limit: int | None = None,
    include_deprecated: bool = False,
) -> pd.DataFrame:
    """
    Fetch Ethereum block data optimized for alpha feature engineering.

    Alpha Feature Rankings (for AI agents):
        #1 base_fee_per_gas - Fee prediction (most valuable)
        #2 gas_used/gas_limit - Congestion leading indicator
        #3 transaction_count - Network activity proxy
        #4-6 timestamp, number, size - Temporal alignment
        #7-8 blob_gas_used, excess_blob_gas - L2 metrics (post-Mar 2024)

    Deprecated (excluded by default):
        - difficulty: Always 0 post-Merge (Sep 2022)
        - total_difficulty: Frozen post-Merge

    Args:
        start: Start date (ISO 8601 or 'YYYY-MM-DD'), defaults to all data
        end: End date (ISO 8601 or 'YYYY-MM-DD'), defaults to latest
        limit: Max blocks to return (default: None = all matching)
        include_deprecated: Include difficulty/total_difficulty (default: False)

    Returns:
        pd.DataFrame with standard time-series column order:
        - timestamp (datetime64[ns, UTC])
        - number (uint64)
        - gas_limit (uint64)
        - gas_used (uint64)
        - base_fee_per_gas (uint64)
        - transaction_count (uint64)
        - size (uint64)
        - blob_gas_used (uint64, nullable) - Post-EIP4844
        - excess_blob_gas (uint64, nullable) - Post-EIP4844
        - [difficulty, total_difficulty if include_deprecated=True]

    Note:
        For alpha feature rankings, call probe.get_alpha_features() first.

    Raises:
        CredentialException: If ClickHouse credentials not found
        DatabaseException: If query fails

    Examples:
        # Fetch last 1000 blocks (recommended for live trading)
        >>> df = fetch_blocks(limit=1000)

        # Compute block utilization (#2 alpha feature)
        >>> df['utilization'] = df['gas_used'] / df['gas_limit']

        # Date range query
        >>> df = fetch_blocks(start='2024-01-01', end='2024-01-31')
    """
    client = _get_clickhouse_client()

    # Build column list
    columns = [
        "timestamp",
        "number",
        "gas_limit",
        "gas_used",
        "base_fee_per_gas",
        "transaction_count",
        "size",
        "blob_gas_used",
        "excess_blob_gas",
    ]
    if include_deprecated:
        columns.extend(["difficulty", "total_difficulty"])

    columns_str = ", ".join(columns)

    # Build query with conditions
    conditions = []
    if start:
        conditions.append(f"timestamp >= '{start}'")
    if end:
        conditions.append(f"timestamp <= '{end}'")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    limit_clause = f"LIMIT {limit}" if limit else ""

    query = f"""
        SELECT {columns_str}
        FROM ethereum_mainnet.blocks FINAL
        {where_clause}
        ORDER BY number DESC
        {limit_clause}
    """

    try:
        result = client.query(query)
        df = pd.DataFrame(result.result_rows, columns=result.column_names)

        # Convert timestamp to datetime
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

        return df.sort_values("number").reset_index(drop=True)

    except Exception as e:
        raise DatabaseException(
            f"Failed to query blocks: {e}",
            context={"start": start, "end": end, "limit": limit},
        ) from e


def fetch_snapshots(
    start: str,
    end: str,
    interval: int = 60,
    output_dir: str | None = None,
) -> pd.DataFrame:
    """
    Fetch mempool snapshots for a time range (forward-collection only).

    IMPORTANT: This function only supports forward collection (real-time).
    Historical data collection is not supported as mempool.space does not
    provide historical snapshot APIs. Start time must be within 5 minutes
    of current time.

    Args:
        start: Start timestamp (ISO 8601 format, e.g., "2024-01-01 00:00:00")
               Must be within 5 minutes of current time.
        end: End timestamp (ISO 8601 format) - typically in the future
        interval: Collection interval in seconds (default: 60)
        output_dir: Optional output directory for Parquet files

    Returns:
        DataFrame with mempool snapshots indexed by timestamp

    Raises:
        ValueError: If start/end are invalid, start >= end, or start is too far in past
        MempoolHTTPException: If API requests fail
        MempoolRateLimitException: If rate limit exceeded
        MempoolValidationException: If data quality checks fail

    Example:
        >>> import gapless_network_data as gmd
        >>> from datetime import datetime, timedelta, timezone
        >>> now = datetime.now(timezone.utc)
        >>> # Collect next 5 minutes of data
        >>> df = gmd.fetch_snapshots(
        ...     start=now.isoformat(),
        ...     end=(now + timedelta(minutes=5)).isoformat()
        ... )
        >>> print(df.head())
    """
    collector = MempoolCollector(output_dir=output_dir)
    return collector.collect_range(
        start=datetime.fromisoformat(start),
        end=datetime.fromisoformat(end),
        interval=interval,
    )


def get_latest_snapshot() -> dict[str, float | int | str]:
    """
    Get the most recent mempool snapshot.

    Returns:
        Dictionary with current mempool state:
        - timestamp: ISO 8601 timestamp
        - unconfirmed_count: Number of unconfirmed transactions
        - vsize_mb: Total mempool size in MB
        - total_fee_btc: Total fees in mempool (BTC)
        - fastest_fee: Fee rate for next block (sat/vB)
        - half_hour_fee: Fee rate for ~30min confirmation (sat/vB)
        - hour_fee: Fee rate for ~1hr confirmation (sat/vB)
        - economy_fee: Fee rate for low-priority tx (sat/vB)
        - minimum_fee: Minimum relay fee (sat/vB)

    Raises:
        MempoolHTTPException: If API request fails
        MempoolRateLimitException: If rate limit exceeded

    Example:
        >>> import gapless_network_data as gmd
        >>> snapshot = gmd.get_latest_snapshot()
        >>> print(f"Unconfirmed: {snapshot['unconfirmed_count']} txs")
        >>> print(f"Fastest fee: {snapshot['fastest_fee']} sat/vB")
    """
    collector = MempoolCollector()
    return collector.collect_snapshot()
