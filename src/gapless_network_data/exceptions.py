"""
Structured exception classes for gapless-network-data.

All exceptions include context (timestamp, endpoint, etc.) for observability.
Follows exception-only failure pattern - no fallbacks, no defaults, no silent errors.
"""

from datetime import datetime, timezone
from http import HTTPStatus


class MempoolException(Exception):
    """
    Base exception for all gapless-network-data errors.

    All exceptions include ISO 8601 timestamp for observability.
    """

    def __init__(self, message: str, timestamp: datetime | None = None) -> None:
        """
        Initialize base exception.

        Args:
            message: Human-readable error description
            timestamp: When error occurred (defaults to current UTC time)
        """
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.message = message
        super().__init__(message)

    def to_dict(self) -> dict[str, str]:
        """
        Convert exception to dictionary for logging/serialization.

        Returns:
            Dictionary with exception details
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "error_type": self.__class__.__name__,
            "message": self.message,
        }


class MempoolHTTPException(MempoolException):
    """
    HTTP request failure from mempool.space API.

    Includes endpoint, HTTP status code, and retry count for debugging.
    """

    def __init__(
        self,
        message: str,
        endpoint: str,
        http_status: int | None = None,
        retry_count: int = 0,
        timestamp: datetime | None = None,
    ) -> None:
        """
        Initialize HTTP exception.

        Args:
            message: Human-readable error description
            endpoint: API endpoint that failed (e.g., "/api/mempool")
            http_status: HTTP status code (if applicable)
            retry_count: Number of retries attempted
            timestamp: When error occurred (defaults to current UTC time)
        """
        super().__init__(message, timestamp)
        self.endpoint = endpoint
        self.http_status = http_status
        self.retry_count = retry_count

    def to_dict(self) -> dict[str, str | int | None]:
        """
        Convert exception to dictionary for logging/serialization.

        Returns:
            Dictionary with exception details
        """
        base = super().to_dict()
        base.update(
            {
                "endpoint": self.endpoint,
                "http_status": self.http_status,
                "retry_count": self.retry_count,
            }
        )
        return base

    def __str__(self) -> str:
        """String representation with context."""
        status_str = f" (HTTP {self.http_status})" if self.http_status else ""
        retry_str = f" after {self.retry_count} retries" if self.retry_count > 0 else ""
        return f"{self.message} [endpoint: {self.endpoint}{status_str}{retry_str}]"


class MempoolValidationException(MempoolException):
    """
    Data quality validation failure.

    Raised when snapshot fails schema validation, sanity checks, or constraints.
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: float | int | str | None = None,
        constraint: str | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """
        Initialize validation exception.

        Args:
            message: Human-readable error description
            field: Field name that failed validation
            value: Invalid value that caused failure
            constraint: Constraint that was violated
            timestamp: When error occurred (defaults to current UTC time)
        """
        super().__init__(message, timestamp)
        self.field = field
        self.value = value
        self.constraint = constraint

    def to_dict(self) -> dict[str, str | float | int | None]:
        """
        Convert exception to dictionary for logging/serialization.

        Returns:
            Dictionary with exception details
        """
        base = super().to_dict()
        base.update(
            {
                "field": self.field,
                "value": self.value,
                "constraint": self.constraint,
            }
        )
        return base

    def __str__(self) -> str:
        """String representation with context."""
        parts = [self.message]
        if self.field:
            parts.append(f"field: {self.field}")
        if self.value is not None:
            parts.append(f"value: {self.value}")
        if self.constraint:
            parts.append(f"constraint: {self.constraint}")
        return " [" + ", ".join(parts[1:]) + "]" if len(parts) > 1 else parts[0]


class MempoolRateLimitException(MempoolHTTPException):
    """
    Rate limit exceeded on mempool.space API.

    Raised when API returns 429 Too Many Requests.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        endpoint: str = "",
        retry_after: int | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """
        Initialize rate limit exception.

        Args:
            message: Human-readable error description
            endpoint: API endpoint that failed
            retry_after: Seconds to wait before retry (from Retry-After header)
            timestamp: When error occurred (defaults to current UTC time)
        """
        super().__init__(
            message=message,
            endpoint=endpoint,
            http_status=HTTPStatus.TOO_MANY_REQUESTS.value,
            timestamp=timestamp,
        )
        self.retry_after = retry_after

    def to_dict(self) -> dict[str, str | int | None]:
        """
        Convert exception to dictionary for logging/serialization.

        Returns:
            Dictionary with exception details
        """
        base = super().to_dict()
        base.update({"retry_after": self.retry_after})
        return base


class CredentialException(MempoolException):
    """
    Credential resolution failure.

    Raised when ClickHouse credentials cannot be resolved from Doppler or env vars.
    """

    def __init__(
        self,
        message: str,
        timestamp: datetime | None = None,
    ) -> None:
        """
        Initialize credential exception with setup instructions.

        Args:
            message: Human-readable error description with setup instructions
            timestamp: When error occurred (defaults to current UTC time)
        """
        super().__init__(message, timestamp)

    def __str__(self) -> str:
        """String representation with setup instructions."""
        return self.message


class DatabaseException(MempoolException):
    """
    Database operation failure (ClickHouse).

    Raised when database connection, insert, or query fails.
    Includes operation context for debugging.
    """

    def __init__(
        self,
        message: str,
        context: dict[str, str | int] | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        """
        Initialize database exception.

        Args:
            message: Human-readable error description
            context: Additional context (operation, db_path, num_blocks, etc.)
            timestamp: When error occurred (defaults to current UTC time)
        """
        super().__init__(message, timestamp)
        self.context = context or {}

    def to_dict(self) -> dict[str, str | dict | None]:
        """
        Convert exception to dictionary for logging/serialization.

        Returns:
            Dictionary with exception details
        """
        base = super().to_dict()
        base.update({"context": self.context})
        return base

    def __str__(self) -> str:
        """String representation with context."""
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} [{context_str}]"
        return self.message
