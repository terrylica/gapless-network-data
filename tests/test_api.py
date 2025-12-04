"""Tests for gapless_network_data public API exports and version compliance."""

import re

import pytest

import gapless_network_data as gmd
from gapless_network_data.api import _normalize_timestamp, _validate_fetch_blocks_params


def test_version_export():
    """Verify __version__ attribute exists and follows semantic versioning."""
    assert hasattr(gmd, "__version__")
    assert isinstance(gmd.__version__, str)
    # Semantic versioning pattern: MAJOR.MINOR.PATCH with optional pre-release
    semver_pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$"
    assert re.match(semver_pattern, gmd.__version__), (
        f"Version '{gmd.__version__}' does not match semantic versioning pattern"
    )


def test_api_function_exports():
    """Verify public API functions are exported and callable."""
    expected_functions = ["fetch_snapshots", "get_latest_snapshot"]
    for func_name in expected_functions:
        assert hasattr(gmd, func_name), f"Missing export: {func_name}"
        assert callable(getattr(gmd, func_name)), f"Not callable: {func_name}"


def test_exception_exports():
    """Verify exception classes are exported for downstream error handling."""
    expected_exceptions = [
        "MempoolException",
        "MempoolHTTPException",
        "MempoolValidationException",
        "MempoolRateLimitException",
        "DatabaseException",
    ]
    for exc_name in expected_exceptions:
        assert hasattr(gmd, exc_name), f"Missing exception export: {exc_name}"
        exc_class = getattr(gmd, exc_name)
        assert isinstance(exc_class, type), f"Not a class: {exc_name}"
        assert issubclass(exc_class, Exception), f"Not an Exception subclass: {exc_name}"


# =============================================================================
# Timestamp Normalization Tests (ADR: 2025-12-02-half-open-interval-timestamps)
# =============================================================================


class TestNormalizeTimestamp:
    """Test half-open interval timestamp normalization helper."""

    def test_date_only_start_preserves_midnight(self):
        """Date-only start should preserve midnight."""
        result = _normalize_timestamp("2024-03-13", is_end=False)
        assert result == "2024-03-13 00:00:00.000"

    def test_date_only_end_expands_to_next_day(self):
        """Date-only end should expand to next day start for exclusive boundary."""
        result = _normalize_timestamp("2024-03-13", is_end=True)
        assert result == "2024-03-14 00:00:00.000"

    def test_datetime_string_preserves_time(self):
        """Datetime with time component should preserve the time."""
        result = _normalize_timestamp("2024-03-13 12:30:45", is_end=False)
        assert result == "2024-03-13 12:30:45.000"

    def test_datetime_with_time_end_no_expansion(self):
        """Datetime with explicit time should NOT expand to next day."""
        result = _normalize_timestamp("2024-03-13 12:30:45", is_end=True)
        assert result == "2024-03-13 12:30:45.000"

    def test_iso_format_with_t_separator(self):
        """ISO format with T separator should preserve time."""
        result = _normalize_timestamp("2024-03-13T12:30:45", is_end=True)
        assert result == "2024-03-13 12:30:45.000"

    def test_midnight_explicit_not_expanded(self):
        """Explicit midnight time should NOT be treated as date-only."""
        result = _normalize_timestamp("2024-03-13 00:00:00", is_end=True)
        assert result == "2024-03-13 00:00:00.000"

    @pytest.mark.parametrize(
        "date_format",
        [
            "2024-03-13",
            "2024/03/13",
            "20240313",
        ],
    )
    def test_various_date_formats(self, date_format):
        """Various date-only formats should all expand correctly."""
        result = _normalize_timestamp(date_format, is_end=True)
        assert result == "2024-03-14 00:00:00.000"

    def test_millisecond_precision_format(self):
        """Output should have exactly millisecond precision (3 decimal places)."""
        result = _normalize_timestamp("2024-03-13 12:30:45.123456", is_end=False)
        # Should truncate to milliseconds
        assert result == "2024-03-13 12:30:45.123"


class TestFetchBlocksExport:
    """Test fetch_blocks is properly exported."""

    def test_fetch_blocks_exported(self):
        """Verify fetch_blocks is exported and callable."""
        assert hasattr(gmd, "fetch_blocks"), "fetch_blocks not exported"
        assert callable(gmd.fetch_blocks), "fetch_blocks not callable"


# =============================================================================
# Input Validation Tests (ADR: 2025-12-03-fetch-blocks-input-validation)
# =============================================================================


class TestFetchBlocksValidation:
    """Test fetch_blocks() input validation for OOM prevention."""

    def test_empty_string_start_raises_valueerror(self):
        """Empty string start should raise ValueError, not be silently ignored."""
        with pytest.raises(ValueError, match="start date cannot be empty string"):
            _validate_fetch_blocks_params(start="", end=None, limit=None)

    def test_empty_string_end_raises_valueerror(self):
        """Empty string end should raise ValueError, not be silently ignored."""
        with pytest.raises(ValueError, match="end date cannot be empty string"):
            _validate_fetch_blocks_params(start=None, end="", limit=None)

    def test_no_params_raises_valueerror(self):
        """No parameters should raise ValueError, not return entire blockchain."""
        with pytest.raises(ValueError, match="Must specify at least one of"):
            _validate_fetch_blocks_params(start=None, end=None, limit=None)

    def test_reversed_dates_raises_valueerror(self):
        """Reversed date range should raise ValueError, not return empty result."""
        with pytest.raises(ValueError, match="must be <="):
            _validate_fetch_blocks_params(start="2024-03-10", end="2024-03-01", limit=None)

    def test_same_day_ok(self):
        """Same-day query should work (start == end)."""
        # Should NOT raise ValueError
        _validate_fetch_blocks_params(start="2024-03-13", end="2024-03-13", limit=None)

    def test_limit_zero_ok(self):
        """limit=0 should be allowed (returns 0 rows, not entire blockchain)."""
        # Should NOT raise ValueError - limit=0 is valid
        _validate_fetch_blocks_params(start=None, end=None, limit=0)

    def test_limit_only_ok(self):
        """limit-only query should work."""
        # Should NOT raise ValueError
        _validate_fetch_blocks_params(start=None, end=None, limit=1000)

    def test_start_only_ok(self):
        """start-only query should work (all blocks from start date)."""
        # Should NOT raise ValueError
        _validate_fetch_blocks_params(start="2024-01-01", end=None, limit=None)

    def test_end_only_ok(self):
        """end-only query should work (all blocks until end date)."""
        # Should NOT raise ValueError
        _validate_fetch_blocks_params(start=None, end="2024-01-31", limit=None)

    def test_valid_date_range_ok(self):
        """Valid date range should not raise ValueError."""
        # Should NOT raise ValueError
        _validate_fetch_blocks_params(start="2024-01-01", end="2024-01-31", limit=None)

    def test_all_params_ok(self):
        """All parameters specified should work."""
        # Should NOT raise ValueError
        _validate_fetch_blocks_params(start="2024-01-01", end="2024-01-31", limit=1000)
