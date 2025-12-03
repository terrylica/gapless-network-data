# AUTO-GENERATED from schema/clickhouse/ethereum_mainnet.yaml
# DO NOT EDIT - regenerate with: uv run gapless-network-data schema generate-types
# Generated at: 2025-12-02T20:01:47.649444

from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict

from pydantic import BaseModel, Field

class BlockRow(TypedDict):
    """Ethereum Mainnet Blocks - typed dict for DataFrame rows."""

    timestamp: datetime
    number: int
    gas_limit: int
    gas_used: int
    base_fee_per_gas: int
    transaction_count: int
    difficulty: int
    total_difficulty: int
    size: int
    blob_gas_used: int | None
    excess_blob_gas: int | None

class Block(BaseModel):
    """
    Ethereum Mainnet Blocks - Pydantic model for validation.

    Block-level data for ML feature engineering.
    Contains gas metrics, transaction counts, and EIP-4844 blob data.
    Used by Alpha Features API for financial time series forecasting.
    """

    timestamp: datetime = Field(description="Block timestamp with millisecond precision")
    number: int = Field(ge=0, description="Block number - used as deduplication key")
    gas_limit: int = Field(ge=0, description="Maximum gas allowed in block")
    gas_used: int = Field(ge=0, description="Total gas consumed by transactions")
    base_fee_per_gas: int = Field(ge=0, description="EIP-1559 base fee per gas unit (wei)")
    transaction_count: int = Field(ge=0, description="Number of transactions in block")
    difficulty: int = Field(ge=0, description="Mining difficulty (0 post-Merge, Sep 2022)")
    total_difficulty: int = Field(ge=0, description="Cumulative difficulty (frozen post-Merge)")
    size: int = Field(ge=0, description="Block size in bytes")
    blob_gas_used: int | None = Field(ge=0, description="EIP-4844 blob gas used (null pre-Dencun, Mar 2024)")
    excess_blob_gas: int | None = Field(ge=0, description="EIP-4844 excess blob gas (null pre-Dencun)")
