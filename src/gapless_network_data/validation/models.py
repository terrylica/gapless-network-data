"""
Validation models for mempool data quality checks.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class MempoolValidationReport(BaseModel):
    """
    Validation report for mempool snapshot quality.

    This extends the base validation pattern from gapless-crypto-data
    but with mempool-specific fields.
    """

    # Core metadata
    timestamp: datetime = Field(..., description="Snapshot timestamp (UTC)")
    validation_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When validation was performed",
    )

    # Data quality metrics
    unconfirmed_count: int = Field(..., description="Number of unconfirmed transactions")
    vsize_mb: float = Field(..., description="Total mempool size (MB)")
    total_fee_btc: float = Field(..., description="Total fees in mempool (BTC)")

    # Fee metrics
    fastest_fee: float = Field(..., description="Fee rate for next block (sat/vB)")
    half_hour_fee: float = Field(..., description="Fee rate for ~30min (sat/vB)")
    hour_fee: float = Field(..., description="Fee rate for ~1hr (sat/vB)")
    economy_fee: float = Field(..., description="Fee rate for low-priority (sat/vB)")
    minimum_fee: float = Field(..., description="Minimum relay fee (sat/vB)")

    # Validation results
    is_valid: bool = Field(..., description="Whether snapshot passed all checks")
    validation_errors: list[str] = Field(
        default_factory=list, description="List of validation errors"
    )

    # Gap detection
    has_gap: bool = Field(default=False, description="Whether gap detected before this snapshot")
    gap_duration_seconds: int | None = Field(
        default=None, description="Duration of gap in seconds"
    )

    # Anomaly detection
    is_anomaly: bool = Field(default=False, description="Whether snapshot is anomalous")
    anomaly_score: float | None = Field(
        default=None, description="Anomaly score (0-1, higher = more anomalous)"
    )
    anomaly_reason: str | None = Field(default=None, description="Reason for anomaly flag")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-01T00:00:00Z",
                "validation_time": "2024-01-01T00:00:05Z",
                "unconfirmed_count": 15000,
                "vsize_mb": 75.5,
                "total_fee_btc": 0.5,
                "fastest_fee": 20.0,
                "half_hour_fee": 15.0,
                "hour_fee": 12.0,
                "economy_fee": 8.0,
                "minimum_fee": 1.0,
                "is_valid": True,
                "validation_errors": [],
                "has_gap": False,
                "is_anomaly": False,
            }
        }
