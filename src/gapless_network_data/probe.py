"""
AI-discoverable probe module for alpha feature rankings and setup workflow.

Designed for Claude Code CLI consumption - structured output with rankings,
derived formulas, and protocol era context for intelligent API usage.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AlphaFeature:
    """Alpha feature with ranking context for AI agents."""

    rank: int
    name: str
    importance: str  # "critical" | "high" | "medium" | "low"
    description: str
    derived_formula: str | None
    available_from: str  # Block number or "genesis"
    notes: str | None = None


@dataclass(frozen=True)
class ProtocolEra:
    """Ethereum protocol era boundary."""

    name: str
    block: int
    date: str
    description: str


def get_alpha_features() -> list[AlphaFeature]:
    """
    Get ranked list of alpha features for financial time series forecasting.

    Returns features optimized for ML pipeline consumption, ranked by
    importance for predicting gas prices, network congestion, and
    transaction success probability.

    Returns:
        List of AlphaFeature objects ordered by rank (1=most important).

    Example:
        >>> import gapless_network_data as gmd
        >>> features = gmd.probe.get_alpha_features()
        >>> for f in features[:3]:
        ...     print(f"{f.rank}. {f.name} ({f.importance})")
        1. base_fee_per_gas (critical)
        2. block_utilization (critical)
        3. transaction_count (high)
    """
    return [
        AlphaFeature(
            rank=1,
            name="base_fee_per_gas",
            importance="critical",
            description="EIP-1559 base fee - most predictive feature for gas optimization",
            derived_formula=None,
            available_from="12965000 (EIP-1559, Aug 2021)",
            notes="Raw value in wei. Null before EIP-1559.",
        ),
        AlphaFeature(
            rank=2,
            name="block_utilization",
            importance="critical",
            description="Gas used / gas limit ratio - leading indicator of congestion",
            derived_formula="gas_used / gas_limit",
            available_from="genesis",
            notes="Range 0.0-1.0. Values >0.5 indicate congestion. Compute client-side.",
        ),
        AlphaFeature(
            rank=3,
            name="transaction_count",
            importance="high",
            description="Number of transactions per block - network activity proxy",
            derived_formula=None,
            available_from="genesis",
            notes="Higher counts correlate with congestion and fee pressure.",
        ),
        AlphaFeature(
            rank=4,
            name="timestamp",
            importance="high",
            description="Block timestamp - temporal alignment with OHLCV data",
            derived_formula=None,
            available_from="genesis",
            notes="UTC datetime. Use for ASOF JOIN with price data.",
        ),
        AlphaFeature(
            rank=5,
            name="number",
            importance="high",
            description="Block number - unique identifier and ordering key",
            derived_formula=None,
            available_from="genesis",
            notes="Monotonically increasing. Use for deduplication.",
        ),
        AlphaFeature(
            rank=6,
            name="size",
            importance="medium",
            description="Block size in bytes - data throughput indicator",
            derived_formula=None,
            available_from="genesis",
            notes="Correlates with transaction complexity and network load.",
        ),
        AlphaFeature(
            rank=7,
            name="blob_gas_used",
            importance="medium",
            description="EIP-4844 blob gas - L2 rollup data indicator",
            derived_formula=None,
            available_from="19426587 (EIP-4844, Mar 2024)",
            notes="Nullable. Non-zero indicates L2 batch submissions.",
        ),
        AlphaFeature(
            rank=8,
            name="excess_blob_gas",
            importance="low",
            description="EIP-4844 excess blob gas - blob fee market state",
            derived_formula=None,
            available_from="19426587 (EIP-4844, Mar 2024)",
            notes="Nullable. Used to compute blob base fee.",
        ),
        AlphaFeature(
            rank=9,
            name="gas_limit",
            importance="low",
            description="Block gas limit - network capacity ceiling",
            derived_formula=None,
            available_from="genesis",
            notes="Rarely changes. Useful for utilization denominator.",
        ),
        AlphaFeature(
            rank=10,
            name="gas_used",
            importance="low",
            description="Total gas consumed - absolute congestion measure",
            derived_formula=None,
            available_from="genesis",
            notes="Use block_utilization (rank #2) for relative measure.",
        ),
    ]


def get_protocol_eras() -> list[ProtocolEra]:
    """
    Get Ethereum protocol era boundaries.

    These boundaries mark significant changes in block data semantics.
    AI agents should use these to filter data appropriately.

    Returns:
        List of ProtocolEra objects ordered chronologically.

    Example:
        >>> import gapless_network_data as gmd
        >>> eras = gmd.probe.get_protocol_eras()
        >>> for era in eras:
        ...     print(f"{era.name}: block {era.block}")
        EIP-1559: block 12965000
        The Merge: block 15537394
        EIP-4844: block 19426587
    """
    return [
        ProtocolEra(
            name="EIP-1559",
            block=12_965_000,
            date="2021-08-05",
            description="base_fee_per_gas introduced. Null before this block.",
        ),
        ProtocolEra(
            name="The Merge",
            block=15_537_394,
            date="2022-09-15",
            description="PoW→PoS transition. difficulty=0 forever after. "
            "Exclude difficulty/total_difficulty from post-Merge analysis.",
        ),
        ProtocolEra(
            name="EIP-4844",
            block=19_426_587,
            date="2024-03-13",
            description="Blob transactions enabled. blob_gas_used, excess_blob_gas "
            "introduced. Null before this block.",
        ),
    ]


def get_setup_workflow() -> dict[str, object]:
    """
    Get setup instructions for ClickHouse credentials.

    Returns step-by-step workflow for configuring access to the
    Ethereum block data stored in ClickHouse Cloud.

    Returns:
        Dictionary with setup steps and context.

    Example:
        >>> import gapless_network_data as gmd
        >>> workflow = gmd.probe.get_setup_workflow()
        >>> print(workflow['summary'])
        Three credential options: .env file, Doppler, or environment variables
    """
    return {
        "summary": "Three credential options: .env file, Doppler, or environment variables",
        "options": {
            "dotenv": {
                "description": ".env file (simplest for small teams)",
                "steps": [
                    "1. Copy .env.example to .env in project root",
                    "2. Fill in CLICKHOUSE_HOST_READONLY, CLICKHOUSE_USER_READONLY, CLICKHOUSE_PASSWORD_READONLY",
                    "3. Credentials auto-load on import",
                ],
            },
            "doppler": {
                "description": "Doppler service token (recommended for production)",
                "credential_source": "1Password: Engineering vault → 'gapless-network-data Doppler Service Token'",
                "steps": [
                    "1. Get service token from 1Password Engineering vault",
                    "2. Configure Doppler: doppler configure set token <token>",
                    "3. Set project: doppler setup --project gapless-network-data --config prd",
                    "4. Verify: doppler secrets get CLICKHOUSE_HOST_READONLY --plain",
                ],
            },
            "env_vars": {
                "description": "Environment variables (direct export)",
                "steps": [
                    "export CLICKHOUSE_HOST_READONLY=<host>",
                    "export CLICKHOUSE_USER_READONLY=<user>",
                    "export CLICKHOUSE_PASSWORD_READONLY=<password>",
                ],
            },
        },
        "data_available": "23.87M Ethereum blocks (2015-2025)",
        "update_frequency": "Real-time (~12 second block intervals)",
    }


def get_quick_start() -> str:
    """
    Get quick start code snippet for AI agents.

    Returns ready-to-run Python code demonstrating the API.

    Returns:
        Multi-line string with example code.

    Example:
        >>> import gapless_network_data as gmd
        >>> print(gmd.probe.get_quick_start())
    """
    return '''
# Fetch latest 1000 blocks (recommended for live trading)
import gapless_network_data as gmd

df = gmd.fetch_blocks(limit=1000)

# Compute block utilization (alpha feature #2)
df['utilization'] = df['gas_used'] / df['gas_limit']

# Fee pressure indicator
df['fee_change'] = df['base_fee_per_gas'].pct_change()

# Date range query for historical analysis
df_hist = gmd.fetch_blocks(start='2024-01-01', end='2024-01-31')

# Include deprecated fields (pre-Merge analysis only)
df_legacy = gmd.fetch_blocks(
    start='2021-01-01',
    end='2022-09-15',  # Before The Merge
    include_deprecated=True
)
'''.strip()
