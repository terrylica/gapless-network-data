"""
Gapless Network Data - Ethereum blockchain network metrics collection infrastructure.

Dual-pipeline architecture (BigQuery batch + Alchemy real-time) for collecting
Ethereum block data with automatic deduplication via ClickHouse Cloud.
"""

__version__ = "2.4.0"

from gapless_network_data.api import fetch_snapshots, get_latest_snapshot
from gapless_network_data.exceptions import (
    DatabaseException,
    MempoolException,
    MempoolHTTPException,
    MempoolRateLimitException,
    MempoolValidationException,
)

__all__ = [
    "fetch_snapshots",
    "get_latest_snapshot",
    "__version__",
    "MempoolException",
    "MempoolHTTPException",
    "MempoolValidationException",
    "MempoolRateLimitException",
    "DatabaseException",
]
