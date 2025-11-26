"""Tests for gapless_network_data public API exports and version compliance."""

import re

import gapless_network_data as gmd


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
