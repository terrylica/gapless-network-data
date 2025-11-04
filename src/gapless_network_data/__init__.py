"""
Gapless Mempool Data - Bitcoin mempool pressure data collection.

Provides authentic mempool.space data with zero-gap guarantee for feature engineering
in cryptocurrency trading and ML pipelines.
"""

__version__ = "0.1.0"

from gapless_network_data.api import fetch_snapshots, get_latest_snapshot
from gapless_network_data.exceptions import (
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
]
