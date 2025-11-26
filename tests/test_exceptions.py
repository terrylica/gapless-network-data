"""Tests for gapless_network_data structured exception classes.

Verifies exception initialization, to_dict() serialization, __str__() formatting,
and inheritance hierarchy for observability and error handling.
"""

from datetime import datetime, timezone

import pytest

from gapless_network_data.exceptions import (
    DatabaseException,
    MempoolException,
    MempoolHTTPException,
    MempoolRateLimitException,
    MempoolValidationException,
)


class TestMempoolException:
    """Tests for base MempoolException class."""

    def test_init_with_message_only(self):
        """Verify exception initializes with message and auto-generated timestamp."""
        exc = MempoolException("Test error")
        assert exc.message == "Test error"
        assert isinstance(exc.timestamp, datetime)
        assert exc.timestamp.tzinfo == timezone.utc

    def test_init_with_custom_timestamp(self):
        """Verify exception accepts custom timestamp."""
        ts = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        exc = MempoolException("Test error", timestamp=ts)
        assert exc.timestamp == ts

    def test_to_dict_serialization(self):
        """Verify to_dict() produces machine-readable format."""
        ts = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        exc = MempoolException("Test error", timestamp=ts)
        result = exc.to_dict()

        assert result["timestamp"] == "2025-01-15T12:00:00+00:00"
        assert result["error_type"] == "MempoolException"
        assert result["message"] == "Test error"

    def test_exception_inheritance(self):
        """Verify MempoolException is a proper Exception subclass."""
        exc = MempoolException("Test")
        assert isinstance(exc, Exception)

    def test_exception_str(self):
        """Verify str() returns message."""
        exc = MempoolException("Test error message")
        assert str(exc) == "Test error message"


class TestMempoolHTTPException:
    """Tests for MempoolHTTPException class."""

    def test_init_with_all_parameters(self):
        """Verify HTTP exception captures all context."""
        exc = MempoolHTTPException(
            message="Connection failed",
            endpoint="/api/mempool",
            http_status=503,
            retry_count=3,
        )
        assert exc.message == "Connection failed"
        assert exc.endpoint == "/api/mempool"
        assert exc.http_status == 503
        assert exc.retry_count == 3

    def test_init_with_minimal_parameters(self):
        """Verify HTTP exception works with minimal parameters."""
        exc = MempoolHTTPException(message="Error", endpoint="/api/test")
        assert exc.http_status is None
        assert exc.retry_count == 0

    def test_to_dict_serialization(self):
        """Verify to_dict() includes HTTP-specific fields."""
        exc = MempoolHTTPException(
            message="Server error",
            endpoint="/api/fees",
            http_status=500,
            retry_count=2,
        )
        result = exc.to_dict()

        assert result["endpoint"] == "/api/fees"
        assert result["http_status"] == 500
        assert result["retry_count"] == 2
        assert result["error_type"] == "MempoolHTTPException"

    def test_str_format_with_all_context(self):
        """Verify __str__() includes HTTP status and retry count."""
        exc = MempoolHTTPException(
            message="Request failed",
            endpoint="/api/mempool",
            http_status=429,
            retry_count=3,
        )
        result = str(exc)
        assert "Request failed" in result
        assert "/api/mempool" in result
        assert "HTTP 429" in result
        assert "3 retries" in result

    def test_str_format_without_status(self):
        """Verify __str__() handles missing HTTP status."""
        exc = MempoolHTTPException(message="Error", endpoint="/api/test")
        result = str(exc)
        assert "Error" in result
        assert "/api/test" in result
        assert "HTTP" not in result

    def test_inheritance_from_mempool_exception(self):
        """Verify HTTP exception inherits from MempoolException."""
        exc = MempoolHTTPException(message="Test", endpoint="/api")
        assert isinstance(exc, MempoolException)
        assert isinstance(exc, Exception)


class TestMempoolValidationException:
    """Tests for MempoolValidationException class."""

    def test_init_with_all_parameters(self):
        """Verify validation exception captures field context."""
        exc = MempoolValidationException(
            message="Invalid fee rate",
            field="fastest_fee",
            value=-5.0,
            constraint="non-negative",
        )
        assert exc.message == "Invalid fee rate"
        assert exc.field == "fastest_fee"
        assert exc.value == -5.0
        assert exc.constraint == "non-negative"

    def test_init_with_minimal_parameters(self):
        """Verify validation exception works with minimal parameters."""
        exc = MempoolValidationException(message="Schema mismatch")
        assert exc.field is None
        assert exc.value is None
        assert exc.constraint is None

    def test_to_dict_serialization(self):
        """Verify to_dict() includes validation-specific fields."""
        exc = MempoolValidationException(
            message="Constraint violated",
            field="unconfirmed_count",
            value=1000000,
            constraint="max_value",
        )
        result = exc.to_dict()

        assert result["field"] == "unconfirmed_count"
        assert result["value"] == 1000000
        assert result["constraint"] == "max_value"
        assert result["error_type"] == "MempoolValidationException"

    def test_str_format_with_full_context(self):
        """Verify __str__() formats validation context."""
        exc = MempoolValidationException(
            message="Fee ordering violated",
            field="half_hour_fee",
            value=10.0,
            constraint="fastest_fee >= half_hour_fee",
        )
        result = str(exc)
        assert "field: half_hour_fee" in result
        assert "value: 10.0" in result
        assert "constraint:" in result

    def test_str_format_message_only(self):
        """Verify __str__() handles message-only case."""
        exc = MempoolValidationException(message="General validation failure")
        result = str(exc)
        assert result == "General validation failure"

    def test_inheritance_from_mempool_exception(self):
        """Verify validation exception inherits from MempoolException."""
        exc = MempoolValidationException(message="Test")
        assert isinstance(exc, MempoolException)


class TestMempoolRateLimitException:
    """Tests for MempoolRateLimitException class."""

    def test_init_with_retry_after(self):
        """Verify rate limit exception captures retry-after header."""
        exc = MempoolRateLimitException(
            message="Too many requests",
            endpoint="/api/mempool",
            retry_after=60,
        )
        assert exc.http_status == 429  # Always 429 for rate limits
        assert exc.retry_after == 60
        assert exc.endpoint == "/api/mempool"

    def test_init_with_defaults(self):
        """Verify rate limit exception has sensible defaults."""
        exc = MempoolRateLimitException()
        assert exc.message == "Rate limit exceeded"
        assert exc.http_status == 429
        assert exc.retry_after is None

    def test_to_dict_serialization(self):
        """Verify to_dict() includes retry_after field."""
        exc = MempoolRateLimitException(
            endpoint="/api/fees",
            retry_after=30,
        )
        result = exc.to_dict()

        assert result["retry_after"] == 30
        assert result["http_status"] == 429
        assert result["error_type"] == "MempoolRateLimitException"

    def test_inheritance_from_http_exception(self):
        """Verify rate limit exception inherits from HTTP exception."""
        exc = MempoolRateLimitException()
        assert isinstance(exc, MempoolHTTPException)
        assert isinstance(exc, MempoolException)


class TestDatabaseException:
    """Tests for DatabaseException class."""

    def test_init_with_context(self):
        """Verify database exception captures operation context."""
        exc = DatabaseException(
            message="Insert failed",
            context={"operation": "insert", "table": "blocks", "rows": 100},
        )
        assert exc.message == "Insert failed"
        assert exc.context["operation"] == "insert"
        assert exc.context["table"] == "blocks"
        assert exc.context["rows"] == 100

    def test_init_without_context(self):
        """Verify database exception works without context."""
        exc = DatabaseException(message="Connection lost")
        assert exc.context == {}

    def test_to_dict_serialization(self):
        """Verify to_dict() includes context dictionary."""
        exc = DatabaseException(
            message="Query timeout",
            context={"query": "SELECT *", "timeout_ms": 30000},
        )
        result = exc.to_dict()

        assert result["context"]["query"] == "SELECT *"
        assert result["context"]["timeout_ms"] == 30000
        assert result["error_type"] == "DatabaseException"

    def test_str_format_with_context(self):
        """Verify __str__() formats context as key=value pairs."""
        exc = DatabaseException(
            message="Checkpoint failed",
            context={"db_path": "/tmp/test.db", "blocks": 1000},
        )
        result = str(exc)
        assert "Checkpoint failed" in result
        assert "db_path=/tmp/test.db" in result
        assert "blocks=1000" in result

    def test_str_format_without_context(self):
        """Verify __str__() handles empty context."""
        exc = DatabaseException(message="Database error")
        assert str(exc) == "Database error"

    def test_inheritance_from_mempool_exception(self):
        """Verify database exception inherits from MempoolException."""
        exc = DatabaseException(message="Test")
        assert isinstance(exc, MempoolException)


class TestExceptionHierarchy:
    """Tests for exception hierarchy and catching patterns."""

    def test_catch_all_with_mempool_exception(self):
        """Verify MempoolException catches all derived exceptions."""
        exceptions = [
            MempoolException("base"),
            MempoolHTTPException("http", "/api"),
            MempoolValidationException("validation"),
            MempoolRateLimitException(),
            DatabaseException("db"),
        ]
        for exc in exceptions:
            with pytest.raises(MempoolException):
                raise exc

    def test_http_exception_catches_rate_limit(self):
        """Verify MempoolHTTPException catches rate limit exceptions."""
        exc = MempoolRateLimitException(endpoint="/api")
        with pytest.raises(MempoolHTTPException):
            raise exc

    def test_exception_is_raisable(self):
        """Verify all exceptions can be raised and caught properly."""
        try:
            raise MempoolHTTPException(
                message="Test",
                endpoint="/api/test",
                http_status=500,
            )
        except MempoolHTTPException as e:
            assert e.http_status == 500
            assert e.endpoint == "/api/test"
