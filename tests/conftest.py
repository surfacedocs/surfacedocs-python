"""Pytest fixtures for SurfaceDocs SDK tests."""

import pytest


@pytest.fixture
def api_key() -> str:
    """Test API key."""
    return "sd_test_abc123"
