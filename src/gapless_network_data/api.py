"""
Public API for mempool data collection.

This module provides the main programmatic interface for collecting Bitcoin mempool
pressure data from mempool.space.
"""

from datetime import datetime
from typing import Optional

import pandas as pd

from gapless_network_data.collectors.mempool_collector import MempoolCollector


def fetch_snapshots(
    start: str,
    end: str,
    interval: int = 60,
    output_dir: Optional[str] = None,
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
        output_dir: Optional database path (default: ~/.cache/gapless-network-data/data.duckdb)

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
