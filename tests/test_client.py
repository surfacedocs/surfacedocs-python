"""Tests for SurfaceDocs client."""

import pytest

from surfacedocs import SurfaceDocs
from surfacedocs.client import SurfaceDocs as DirectSurfaceDocs


class TestSurfaceDocsClient:
    """Test the SurfaceDocs client class."""

    def test_client_class_exists(self):
        """SurfaceDocs class should exist."""
        assert SurfaceDocs is not None

    def test_client_is_class(self):
        """SurfaceDocs should be a class."""
        assert isinstance(SurfaceDocs, type)

    def test_client_raises_not_implemented(self):
        """Client should raise NotImplementedError until implemented."""
        with pytest.raises(NotImplementedError):
            SurfaceDocs()

    def test_client_raises_not_implemented_with_api_key(self):
        """Client should raise NotImplementedError with api_key."""
        with pytest.raises(NotImplementedError):
            SurfaceDocs(api_key="sd_test_abc123")

    def test_client_raises_not_implemented_with_base_url(self):
        """Client should raise NotImplementedError with base_url."""
        with pytest.raises(NotImplementedError):
            SurfaceDocs(base_url="https://custom.api.com")

    def test_client_raises_not_implemented_with_both_args(self):
        """Client should raise NotImplementedError with both args."""
        with pytest.raises(NotImplementedError):
            SurfaceDocs(api_key="sd_test_abc123", base_url="https://custom.api.com")


class TestClientImports:
    """Test client import paths."""

    def test_import_from_package(self):
        """SurfaceDocs should be importable from main package."""
        from surfacedocs import SurfaceDocs as PkgClient
        assert PkgClient is not None

    def test_import_from_module(self):
        """SurfaceDocs should be importable from client module."""
        assert DirectSurfaceDocs is not None

    def test_imports_are_same_class(self):
        """Both imports should reference the same class."""
        assert SurfaceDocs is DirectSurfaceDocs


class TestClientDocstring:
    """Test client documentation."""

    def test_client_has_docstring(self):
        """SurfaceDocs class should have a docstring."""
        assert SurfaceDocs.__doc__ is not None

    def test_init_has_signature(self):
        """__init__ should have type annotations."""
        import inspect
        sig = inspect.signature(SurfaceDocs.__init__)
        params = list(sig.parameters.keys())
        assert "api_key" in params
        assert "base_url" in params
