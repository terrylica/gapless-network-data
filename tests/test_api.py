"""
Tests for public API.
"""

import pytest

import gapless_network_data as gmd


def test_package_import():
    """Test that package imports successfully."""
    assert gmd.__version__ == "0.1.0"


def test_api_exports():
    """Test that API functions are exported."""
    assert hasattr(gmd, "fetch_snapshots")
    assert hasattr(gmd, "get_latest_snapshot")
    assert callable(gmd.fetch_snapshots)
    assert callable(gmd.get_latest_snapshot)
