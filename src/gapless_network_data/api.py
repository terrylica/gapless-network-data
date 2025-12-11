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


def _normalize_timestamp(ts_str: str, is_end: bool = False) -> str:
    """
    Normalize timestamp string for inclusive date range queries.

    Expands date-only strings to include the full day:
    - Start dates: midnight of that day
    - End dates: midnight of the NEXT day (for exclusive < comparison)
    - Explicit times are preserved with millisecond precision

    This enables inclusive [start, end] semantics for date-only inputs
    while using efficient < comparison internally.

    Args:
        ts_str: Timestamp string (various formats)
        is_end: If True, expand date-only to next day start for < comparison

    Returns:
        Formatted timestamp string with millisecond precision

    Examples:
        >>> _normalize_timestamp('2024-03-13', is_end=False)
        '2024-03-13 00:00:00.000'
        >>> _normalize_timestamp('2024-03-13', is_end=True)
        '2024-03-14 00:00:00.000'  # For < comparison, includes all of Mar 13
        >>> _normalize_timestamp('2024-03-13 12:30:45', is_end=True)
        '2024-03-13 12:30:45.000'  # Explicit time preserved
    """
    ts = pd.to_datetime(ts_str)

    # Detect date-only input (no time component specified)
    # Check both the parsed result and the original string format
    is_date_only = (
        ts.hour == 0
        and ts.minute == 0
        and ts.second == 0
        and ts.microsecond == 0
        and "T" not in str(ts_str)
        and ":" not in str(ts_str)
    )

    if is_date_only and is_end:
        # Expand to next day start for exclusive end
        ts = ts + pd.Timedelta(days=1)

    # Format with milliseconds to match DateTime64(3) schema
    return ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _validate_fetch_blocks_params(
    start: str | None,
    end: str | None,
    limit: int | None,
) -> None:
    """
    Validate fetch_blocks() parameters at function entry.

    Fail-fast validation prevents expensive database operations on invalid inputs.

    ADR: 2025-12-03-fetch-blocks-input-validation

    Args:
        start: Start date parameter
        end: End date parameter
        limit: Limit parameter

    Raises:
        ValueError: If parameters are invalid
    """
    # 1. Empty string detection (must check before truthiness tests)
    if start == "":
        raise ValueError(
            "start date cannot be empty string. "
            "Use None to omit, or provide a valid date like '2024-01-01'."
        )
    if end == "":
        raise ValueError(
            "end date cannot be empty string. "
            "Use None to omit, or provide a valid date like '2024-01-31'."
        )

    # 2. At least one constraint required
    if start is None and end is None and limit is None:
        raise ValueError(
            "Must specify at least one of: start, end, or limit. "
            "Examples:\n"
            "  fetch_blocks(limit=1000)           # Latest 1000 blocks\n"
            "  fetch_blocks(start='2024-01-01')   # All blocks from Jan 1\n"
            "  fetch_blocks(start='2024-01-01', end='2024-01-31')  # Date range"
        )

    # 3. Date ordering validation (only if both dates provided)
    if start is not None and end is not None:
        start_ts = pd.to_datetime(start)
        end_ts = pd.to_datetime(end)
        if start_ts > end_ts:
            raise ValueError(
                f"start date ({start}) must be <= end date ({end}). "
                "Swap the dates or adjust your query range."
            )


def _get_clickhouse_credentials() -> tuple[str, str, str]:
    """
    Resolve ClickHouse credentials from multiple sources.

    Resolution order (env vars first to allow local override):
    1. .env file (auto-loaded via python-dotenv)
    2. Environment variables (CLICKHOUSE_HOST_READONLY, etc.) - checked FIRST
    3. Doppler CLI (if configured) - gapless-network-data/prd
    4. Raise CredentialException with setup instructions

    Local development: Set env vars to override Doppler (localhost uses port 8123, no TLS).

    Returns:
        Tuple of (host, user, password)

    Raises:
        CredentialException: If credentials cannot be resolved
    """
    # Load .env file if present (populates os.environ)
    # ADR: 2025-12-01-dotenv-credential-loading
    load_dotenv()

    # Check env vars FIRST (allows local override of Doppler)
    host = os.environ.get("CLICKHOUSE_HOST_READONLY")
    user = os.environ.get("CLICKHOUSE_USER_READONLY")
    password = os.environ.get("CLICKHOUSE_PASSWORD_READONLY")

    if host and user is not None:
        # For local dev, password can be empty string
        return host, user, password or ""

    # Fall back to Doppler
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

    # Clear error with setup instructions
    raise CredentialException(
        "ClickHouse credentials not found.\n\n"
        "Option 1: Local development\n"
        "  export CLICKHOUSE_HOST_READONLY=localhost\n"
        "  export CLICKHOUSE_USER_READONLY=default\n"
        "  export CLICKHOUSE_PASSWORD_READONLY=''\n\n"
        "Option 2: Use .env file (simplest for small teams)\n"
        "  Create .env in your project root with:\n"
        "    CLICKHOUSE_HOST_READONLY=<host>\n"
        "    CLICKHOUSE_USER_READONLY=<user>\n"
        "    CLICKHOUSE_PASSWORD_READONLY=<password>\n\n"
        "Option 3 (Recommended for production): Use Doppler service token\n"
        "  1. Get token from 1Password: Engineering vault → 'gapless-network-data Doppler Service Token'\n"
        "  2. doppler configure set token <token_from_1password>\n"
        "  3. doppler setup --project gapless-network-data --config prd\n\n"
        "Contact your team lead for credentials."
    )


def _get_clickhouse_client() -> clickhouse_connect.driver.Client:
    """
    Get authenticated ClickHouse client.

    Automatically detects local vs cloud mode:
    - localhost: port 8123, no TLS (local development)
    - Other hosts: port 8443, TLS enabled (ClickHouse Cloud)

    Returns:
        Configured ClickHouse client

    Raises:
        CredentialException: If credentials cannot be resolved
        DatabaseException: If connection fails
    """
    import clickhouse_connect

    host, user, password = _get_clickhouse_credentials()

    # Detect local development mode
    is_local = host in ("localhost", "127.0.0.1", "::1")

    try:
        if is_local:
            # Local ClickHouse: HTTP port, no TLS, no auth for default user
            # Note: clickhouse_connect requires omitting auth params entirely for no-password mode
            if user == "default" and not password:
                return clickhouse_connect.get_client(
                    host=host,
                    port=8123,
                )
            else:
                return clickhouse_connect.get_client(
                    host=host,
                    port=8123,
                    username=user,
                    password=password,
                )
        else:
            # ClickHouse Cloud: HTTPS port, TLS required
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
            context={"host": host, "user": user, "local_mode": is_local},
        ) from e


def fetch_blocks(
    start: str | None = None,
    end: str | None = None,
    limit: int | None = None,
    include_deprecated: bool = False,
) -> pd.DataFrame:
    """
    Fetch Ethereum block data optimized for alpha feature engineering.

    Date Range Semantics (inclusive [start, end]):
        - start: Inclusive (blocks on or after start date)
        - end: Inclusive (blocks on or before end date)
        - Date-only strings include the entire day
        - Example: start='2024-03-13', end='2024-03-13' returns all blocks on March 13
        - Example: start='2024-01-01', end='2024-01-31' returns all January blocks

    Implementation: Date-only end values expand to include the full day
    (e.g., end='2024-03-13' internally becomes < '2024-03-14 00:00:00').

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
        start: Start date (ISO 8601 or 'YYYY-MM-DD'), inclusive. Defaults to all data.
        end: End date (ISO 8601 or 'YYYY-MM-DD'), inclusive. Defaults to latest.
            Date-only values include the full end day.
        limit: Max blocks to return (default: None = all matching)
        include_deprecated: Include difficulty/total_difficulty (default: False)

    Returns:
        pd.DataFrame with standard time-series column order:
        - timestamp (datetime64[ns, UTC])
        - number (int64)
        - gas_limit (int64)
        - gas_used (int64)
        - base_fee_per_gas (int64)
        - transaction_count (int64)
        - size (int64)
        - blob_gas_used (Int64, nullable) - Post-EIP4844 (pd.NA for pre-Dencun)
        - excess_blob_gas (Int64, nullable) - Post-EIP4844 (pd.NA for pre-Dencun)
        - [difficulty, total_difficulty if include_deprecated=True]

    Nullable Int64 Handling:
        blob_gas_used and excess_blob_gas use pandas nullable Int64 dtype.
        Pre-Dencun blocks (before block 19,426,587) have <NA> values (not NaN).
        To convert to standard int64: df['blob_gas_used'].fillna(0).astype('int64')

    Note:
        - limit=0 explicitly returns 0 rows (empty DataFrame)
        - limit=None (default) returns all matching rows
        - For alpha feature rankings, call probe.get_alpha_features() first.

    Raises:
        ValueError: If parameters are invalid:
            - start or end is empty string (use None to omit)
            - No parameters specified (must have at least one of: start, end, limit)
            - start > end (invalid date range)
        CredentialException: If ClickHouse credentials not found
        DatabaseException: If query fails

    Examples:
        # Fetch last 1000 blocks (recommended for live trading)
        >>> df = fetch_blocks(limit=1000)

        # Same-day query (returns all blocks on March 13)
        >>> df = fetch_blocks(start='2024-03-13', end='2024-03-13')

        # Date range query (all January blocks, inclusive)
        >>> df = fetch_blocks(start='2024-01-01', end='2024-01-31')

        # Compute block utilization (#2 alpha feature)
        >>> df['utilization'] = df['gas_used'] / df['gas_limit']

        # Handle nullable blob gas (convert <NA> to 0)
        >>> df['blob_gas'] = df['blob_gas_used'].fillna(0).astype('int64')
    """
    # ADR: 2025-12-03-fetch-blocks-input-validation
    # Validate parameters (fail-fast before database operations)
    _validate_fetch_blocks_params(start, end, limit)

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

    # Build query with half-open interval [start, end)
    # Industry standard: PostgreSQL, BigQuery, yfinance
    # ADR: 2025-12-02-half-open-interval-timestamps
    conditions = []
    if start:
        start_ts = _normalize_timestamp(start, is_end=False)
        conditions.append(f"timestamp >= '{start_ts}'")
    if end:
        end_ts = _normalize_timestamp(end, is_end=True)
        conditions.append(f"timestamp < '{end_ts}'")  # Exclusive end

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    # ADR: 2025-12-03-fetch-blocks-input-validation
    # limit=0 means "return 0 rows" (explicit LIMIT 0)
    # limit=None means "no limit" (return all matching rows)
    limit_clause = f"LIMIT {limit}" if limit is not None else ""

    query = f"""
        SELECT {columns_str}
        FROM ethereum_mainnet.blocks FINAL
        {where_clause}
        ORDER BY number DESC
        {limit_clause}
    """

    try:
        result = client.query(query)

        # Handle clickhouse-connect returning empty column_names when 0 rows
        # This prevents KeyError on sort_values("number")
        if not result.column_names:
            return pd.DataFrame(columns=columns)

        df = pd.DataFrame(result.result_rows, columns=result.column_names)

        # Convert timestamp to datetime
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

        # ADR: 2025-12-02-sdk-user-feedback-v451 - Convert blob gas to nullable Int64
        # Pre-Dencun blocks have NULL (semantically correct: didn't exist, not "zero")
        if "blob_gas_used" in df.columns:
            df["blob_gas_used"] = df["blob_gas_used"].astype("Int64")
        if "excess_blob_gas" in df.columns:
            df["excess_blob_gas"] = df["excess_blob_gas"].astype("Int64")

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
