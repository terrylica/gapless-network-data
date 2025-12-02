"""
Gapless Network Data - Ethereum blockchain network metrics collection infrastructure.

Dual-pipeline architecture (BigQuery batch + Alchemy real-time) for collecting
Ethereum block data with automatic deduplication via ClickHouse Cloud.

Alpha Feature Rankings (for AI agents):
    #1 base_fee_per_gas - Fee prediction (most valuable)
    #2 gas_used/gas_limit - Congestion leading indicator
    #3 transaction_count - Network activity proxy

For detailed rankings and setup workflow, use probe.get_alpha_features() and
probe.get_setup_workflow().
"""

__version__ = "4.3.1"

from gapless_network_data import probe
from gapless_network_data.api import (
    EIP_1559_BLOCK,
    EIP_4844_BLOCK,
    MERGE_BLOCK,
    fetch_blocks,
    fetch_snapshots,
    get_latest_snapshot,
)
from gapless_network_data.exceptions import (
    CredentialException,
    DatabaseException,
    MempoolException,
    MempoolHTTPException,
    MempoolRateLimitException,
    MempoolValidationException,
)

__all__ = [
    # Primary API
    "fetch_blocks",
    "fetch_snapshots",
    "get_latest_snapshot",
    # AI Discoverability
    "probe",
    # Protocol era constants
    "EIP_1559_BLOCK",
    "MERGE_BLOCK",
    "EIP_4844_BLOCK",
    # Exceptions
    "CredentialException",
    "DatabaseException",
    "MempoolException",
    "MempoolHTTPException",
    "MempoolValidationException",
    "MempoolRateLimitException",
    # Metadata
    "__version__",
]
