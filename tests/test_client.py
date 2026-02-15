"""Tests for SurfaceDocs client."""

import json
import os

import httpx
import pytest
import respx

from surfacedocs import (
    Block,
    Document,
    DocumentNotFoundError,
    Folder,
    SaveResult,
    SearchResult,
    SurfaceDocs,
    AuthenticationError,
    FolderNotFoundError,
    SurfaceDocsError,
    ValidationError,
)
from surfacedocs.client import SaveResult as DirectSaveResult
from surfacedocs.client import SurfaceDocs as DirectSurfaceDocs


class TestSurfaceDocsClient:
    """Test the SurfaceDocs client class."""

    def test_client_class_exists(self):
        """SurfaceDocs class should exist."""
        assert SurfaceDocs is not None

    def test_client_is_class(self):
        """SurfaceDocs should be a class."""
        assert isinstance(SurfaceDocs, type)

    def test_client_raises_without_api_key(self):
        """Client should raise AuthenticationError without API key."""
        # Clear env var if set
        env_key = os.environ.pop("SURFACEDOCS_API_KEY", None)
        try:
            with pytest.raises(AuthenticationError):
                SurfaceDocs()
        finally:
            if env_key:
                os.environ["SURFACEDOCS_API_KEY"] = env_key

    def test_client_accepts_api_key(self):
        """Client should accept api_key parameter."""
        client = SurfaceDocs(api_key="sd_test_abc123")
        assert client.api_key == "sd_test_abc123"
        client.close()

    def test_client_reads_env_var(self):
        """Client should read API key from environment."""
        old_val = os.environ.get("SURFACEDOCS_API_KEY")
        os.environ["SURFACEDOCS_API_KEY"] = "sd_test_from_env"
        try:
            client = SurfaceDocs()
            assert client.api_key == "sd_test_from_env"
            client.close()
        finally:
            if old_val:
                os.environ["SURFACEDOCS_API_KEY"] = old_val
            else:
                os.environ.pop("SURFACEDOCS_API_KEY", None)


class TestBaseUrlDetection:
    """Test base URL auto-detection from API key prefix."""

    def test_dev_url_for_test_key(self):
        """Should use dev URL for sd_test_ prefixed keys."""
        client = SurfaceDocs(api_key="sd_test_abc123")
        assert client.base_url == SurfaceDocs.DEV_URL
        client.close()

    def test_prod_url_for_live_key(self):
        """Should use prod URL for sd_live_ prefixed keys."""
        client = SurfaceDocs(api_key="sd_live_abc123")
        assert client.base_url == SurfaceDocs.PROD_URL
        client.close()

    def test_prod_url_for_unknown_prefix(self):
        """Should default to prod URL for unknown prefixes."""
        client = SurfaceDocs(api_key="some_other_key")
        assert client.base_url == SurfaceDocs.PROD_URL
        client.close()

    def test_custom_base_url(self):
        """Should use custom base URL when provided."""
        client = SurfaceDocs(api_key="sd_test_abc", base_url="https://custom.api.com")
        assert client.base_url == "https://custom.api.com"
        client.close()

    def test_custom_base_url_strips_trailing_slash(self):
        """Should strip trailing slash from custom base URL."""
        client = SurfaceDocs(api_key="sd_test_abc", base_url="https://custom.api.com/")
        assert client.base_url == "https://custom.api.com"
        client.close()


class TestContextManager:
    """Test context manager support."""

    def test_context_manager_returns_client(self):
        """Context manager should return client instance."""
        with SurfaceDocs(api_key="sd_test_abc123") as client:
            assert isinstance(client, SurfaceDocs)
            assert client.api_key == "sd_test_abc123"

    def test_context_manager_closes_client(self):
        """Context manager should close client on exit."""
        with SurfaceDocs(api_key="sd_test_abc123") as client:
            # Client is open
            assert client._client is not None
        # After context, client should be closed (no error thrown)


class TestSaveResult:
    """Test the SaveResult dataclass."""

    def test_save_result_exists(self):
        """SaveResult class should exist."""
        assert SaveResult is not None

    def test_save_result_is_dataclass(self):
        """SaveResult should be a dataclass."""
        from dataclasses import is_dataclass
        assert is_dataclass(SaveResult)

    def test_save_result_has_fields(self):
        """SaveResult should have id, url, folder_id fields."""
        result = SaveResult(id="doc_123", url="https://example.com/d/doc_123", folder_id="folder_456")
        assert result.id == "doc_123"
        assert result.url == "https://example.com/d/doc_123"
        assert result.folder_id == "folder_456"


class TestSaveMethod:
    """Test the save() method."""

    @pytest.fixture
    def client(self):
        """Create a client for testing."""
        c = SurfaceDocs(api_key="sd_test_abc123")
        yield c
        c.close()

    def test_save_raises_on_invalid_json_string(self, client):
        """save() should raise ValidationError on invalid JSON string."""
        with pytest.raises(ValidationError) as exc_info:
            client.save("not valid json")
        assert "Invalid JSON" in str(exc_info.value)

    def test_save_raises_on_missing_title(self, client):
        """save() should raise ValidationError when title is missing."""
        with pytest.raises(ValidationError) as exc_info:
            client.save({"blocks": [{"type": "paragraph", "content": "test"}]})
        assert "title" in str(exc_info.value)

    def test_save_raises_on_missing_blocks(self, client):
        """save() should raise ValidationError when blocks is missing."""
        with pytest.raises(ValidationError) as exc_info:
            client.save({"title": "Test"})
        assert "blocks" in str(exc_info.value)

    def test_save_raises_on_empty_blocks(self, client):
        """save() should raise ValidationError when blocks is empty."""
        with pytest.raises(ValidationError) as exc_info:
            client.save({"title": "Test", "blocks": []})
        assert "blocks" in str(exc_info.value)

    @respx.mock
    def test_save_with_dict(self, client):
        """save() should accept dict content."""
        respx.post("https://ingress.dev.surfacedocs.dev/v1/documents").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": "doc_123",
                    "url": "https://app.surfacedocs.dev/d/doc_123",
                    "folder_id": "folder_456",
                    "title": "Test Doc",
                    "block_count": 1,
                    "created_at": "2024-01-01T00:00:00Z",
                },
            )
        )
        result = client.save({
            "title": "Test Doc",
            "blocks": [{"type": "paragraph", "content": "Hello"}],
        })
        assert result.id == "doc_123"
        assert result.url == "https://app.surfacedocs.dev/d/doc_123"

    @respx.mock
    def test_save_with_json_string(self, client):
        """save() should accept JSON string content."""
        respx.post("https://ingress.dev.surfacedocs.dev/v1/documents").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": "doc_123",
                    "url": "https://app.surfacedocs.dev/d/doc_123",
                    "folder_id": "folder_456",
                    "title": "Test Doc",
                    "block_count": 1,
                    "created_at": "2024-01-01T00:00:00Z",
                },
            )
        )
        content = json.dumps({
            "title": "Test Doc",
            "blocks": [{"type": "paragraph", "content": "Hello"}],
        })
        result = client.save(content)
        assert result.id == "doc_123"


class TestSaveRawMethod:
    """Test the save_raw() method."""

    @pytest.fixture
    def client(self):
        """Create a client for testing."""
        c = SurfaceDocs(api_key="sd_test_abc123")
        yield c
        c.close()

    @respx.mock
    def test_save_raw_basic(self, client):
        """save_raw() should save document with basic params."""
        route = respx.post("https://ingress.dev.surfacedocs.dev/v1/documents").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": "doc_123",
                    "url": "https://app.surfacedocs.dev/d/doc_123",
                    "folder_id": "folder_root",
                    "title": "Test Doc",
                    "block_count": 1,
                    "created_at": "2024-01-01T00:00:00Z",
                },
            )
        )
        result = client.save_raw(
            title="Test Doc",
            blocks=[{"type": "paragraph", "content": "Hello"}],
        )
        assert result.id == "doc_123"
        assert result.folder_id == "folder_root"

        # Verify request payload
        request = route.calls.last.request
        body = json.loads(request.content)
        assert body["title"] == "Test Doc"
        assert body["blocks"] == [{"type": "paragraph", "content": "Hello"}]
        assert body["content_type"] == "markdown"
        assert "folder_id" not in body

    @respx.mock
    def test_save_raw_with_folder_id(self, client):
        """save_raw() should include folder_id when provided."""
        route = respx.post("https://ingress.dev.surfacedocs.dev/v1/documents").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": "doc_123",
                    "url": "https://app.surfacedocs.dev/d/doc_123",
                    "folder_id": "folder_custom",
                    "title": "Test Doc",
                    "block_count": 1,
                    "created_at": "2024-01-01T00:00:00Z",
                },
            )
        )
        result = client.save_raw(
            title="Test Doc",
            blocks=[{"type": "paragraph", "content": "Hello"}],
            folder_id="folder_custom",
        )
        assert result.folder_id == "folder_custom"

        request = route.calls.last.request
        body = json.loads(request.content)
        assert body["folder_id"] == "folder_custom"

    @respx.mock
    def test_save_raw_with_metadata(self, client):
        """save_raw() should include metadata when provided."""
        route = respx.post("https://ingress.dev.surfacedocs.dev/v1/documents").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": "doc_123",
                    "url": "https://app.surfacedocs.dev/d/doc_123",
                    "folder_id": "folder_root",
                    "title": "Test Doc",
                    "block_count": 1,
                    "created_at": "2024-01-01T00:00:00Z",
                },
            )
        )
        client.save_raw(
            title="Test Doc",
            blocks=[{"type": "paragraph", "content": "Hello"}],
            metadata={"source": "test-agent", "tags": ["test"]},
        )

        request = route.calls.last.request
        body = json.loads(request.content)
        assert body["metadata"] == {"source": "test-agent", "tags": ["test"]}


class TestErrorHandling:
    """Test API error handling."""

    @pytest.fixture
    def client(self):
        """Create a client for testing."""
        c = SurfaceDocs(api_key="sd_test_abc123")
        yield c
        c.close()

    @respx.mock
    def test_401_raises_authentication_error(self, client):
        """401 response should raise AuthenticationError."""
        respx.post("https://ingress.dev.surfacedocs.dev/v1/documents").mock(
            return_value=httpx.Response(
                401,
                json={"error": {"code": "unauthorized", "message": "Invalid API key"}},
            )
        )
        with pytest.raises(AuthenticationError) as exc_info:
            client.save_raw(title="Test", blocks=[{"type": "paragraph", "content": "x"}])
        assert "Authentication failed" in str(exc_info.value)

    @respx.mock
    def test_403_raises_authentication_error(self, client):
        """403 response should raise AuthenticationError."""
        respx.post("https://ingress.dev.surfacedocs.dev/v1/documents").mock(
            return_value=httpx.Response(
                403,
                json={"error": {"code": "forbidden", "message": "Access denied"}},
            )
        )
        with pytest.raises(AuthenticationError) as exc_info:
            client.save_raw(title="Test", blocks=[{"type": "paragraph", "content": "x"}])
        assert "Access denied" in str(exc_info.value)

    @respx.mock
    def test_404_raises_folder_not_found_error(self, client):
        """404 response should raise FolderNotFoundError."""
        respx.post("https://ingress.dev.surfacedocs.dev/v1/documents").mock(
            return_value=httpx.Response(
                404,
                json={"error": {"code": "not_found", "message": "Folder not found"}},
            )
        )
        with pytest.raises(FolderNotFoundError) as exc_info:
            client.save_raw(
                title="Test",
                blocks=[{"type": "paragraph", "content": "x"}],
                folder_id="nonexistent",
            )
        assert "Folder not found" in str(exc_info.value)

    @respx.mock
    def test_422_raises_validation_error(self, client):
        """422 response should raise ValidationError."""
        respx.post("https://ingress.dev.surfacedocs.dev/v1/documents").mock(
            return_value=httpx.Response(
                422,
                json={"error": {"code": "validation_error", "message": "Invalid block type"}},
            )
        )
        with pytest.raises(ValidationError) as exc_info:
            client.save_raw(title="Test", blocks=[{"type": "invalid", "content": "x"}])
        assert "Validation error" in str(exc_info.value)

    @respx.mock
    def test_500_raises_surfacedocs_error(self, client):
        """500 response should raise SurfaceDocsError."""
        respx.post("https://ingress.dev.surfacedocs.dev/v1/documents").mock(
            return_value=httpx.Response(
                500,
                json={"error": {"code": "internal_error", "message": "Server error"}},
            )
        )
        with pytest.raises(SurfaceDocsError) as exc_info:
            client.save_raw(title="Test", blocks=[{"type": "paragraph", "content": "x"}])
        assert "API error (500)" in str(exc_info.value)

    @respx.mock
    def test_non_json_error_response(self, client):
        """Should handle non-JSON error responses."""
        respx.post("https://ingress.dev.surfacedocs.dev/v1/documents").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        with pytest.raises(SurfaceDocsError) as exc_info:
            client.save_raw(title="Test", blocks=[{"type": "paragraph", "content": "x"}])
        assert "Internal Server Error" in str(exc_info.value)


class TestClientImports:
    """Test client import paths."""

    def test_import_surfacedocs_from_package(self):
        """SurfaceDocs should be importable from main package."""
        from surfacedocs import SurfaceDocs as PkgClient
        assert PkgClient is not None

    def test_import_surfacedocs_from_module(self):
        """SurfaceDocs should be importable from client module."""
        assert DirectSurfaceDocs is not None

    def test_surfacedocs_imports_are_same_class(self):
        """Both SurfaceDocs imports should reference the same class."""
        assert SurfaceDocs is DirectSurfaceDocs

    def test_import_save_result_from_package(self):
        """SaveResult should be importable from main package."""
        from surfacedocs import SaveResult as PkgResult
        assert PkgResult is not None

    def test_import_save_result_from_module(self):
        """SaveResult should be importable from client module."""
        assert DirectSaveResult is not None

    def test_save_result_imports_are_same_class(self):
        """Both SaveResult imports should reference the same class."""
        assert SaveResult is DirectSaveResult


class TestClientDocstring:
    """Test client documentation."""

    def test_client_has_docstring(self):
        """SurfaceDocs class should have a docstring."""
        assert SurfaceDocs.__doc__ is not None

    def test_init_has_docstring(self):
        """__init__ should have a docstring."""
        assert SurfaceDocs.__init__.__doc__ is not None

    def test_save_has_docstring(self):
        """save() should have a docstring."""
        assert SurfaceDocs.save.__doc__ is not None

    def test_save_raw_has_docstring(self):
        """save_raw() should have a docstring."""
        assert SurfaceDocs.save_raw.__doc__ is not None

    def test_init_has_signature(self):
        """__init__ should have type annotations."""
        import inspect
        sig = inspect.signature(SurfaceDocs.__init__)
        params = list(sig.parameters.keys())
        assert "api_key" in params
        assert "base_url" in params


DEV_BASE = "https://ingress.dev.surfacedocs.dev"

MOCK_DOCUMENT_RESPONSE = {
    "id": "doc_123",
    "url": "https://app.surfacedocs.dev/d/doc_123",
    "folder_id": "folder_456",
    "title": "Test Doc",
    "content_type": "markdown",
    "visibility": "private",
    "blocks": [
        {
            "id": "blk_1",
            "order": 0,
            "type": "heading",
            "content": "Introduction",
            "metadata": {"level": 1},
        },
        {
            "id": "blk_2",
            "order": 1,
            "type": "paragraph",
            "content": "Hello world",
        },
    ],
    "metadata": {"source": "test"},
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-02T00:00:00Z",
}


class TestGetDocument:
    """Test the get_document() method."""

    @pytest.fixture
    def client(self):
        c = SurfaceDocs(api_key="sd_test_abc123")
        yield c
        c.close()

    @respx.mock
    def test_get_document(self, client):
        """get_document() should return a Document with all fields."""
        respx.get(f"{DEV_BASE}/v1/documents/doc_123").mock(
            return_value=httpx.Response(200, json=MOCK_DOCUMENT_RESPONSE)
        )
        doc = client.get_document("doc_123")
        assert isinstance(doc, Document)
        assert doc.id == "doc_123"
        assert doc.title == "Test Doc"
        assert doc.content_type == "markdown"
        assert doc.visibility == "private"
        assert doc.metadata == {"source": "test"}
        assert doc.created_at == "2024-01-01T00:00:00Z"
        assert doc.updated_at == "2024-01-02T00:00:00Z"
        assert len(doc.blocks) == 2
        assert isinstance(doc.blocks[0], Block)
        assert doc.blocks[0].id == "blk_1"
        assert doc.blocks[0].type == "heading"
        assert doc.blocks[0].content == "Introduction"
        assert doc.blocks[0].metadata == {"level": 1}
        assert doc.blocks[1].metadata is None

    @respx.mock
    def test_get_document_not_found(self, client):
        """get_document() should raise DocumentNotFoundError on 404."""
        respx.get(f"{DEV_BASE}/v1/documents/doc_missing").mock(
            return_value=httpx.Response(
                404,
                json={"error": {"code": "not_found", "message": "Document not found"}},
            )
        )
        with pytest.raises(DocumentNotFoundError) as exc_info:
            client.get_document("doc_missing")
        assert "Document not found" in str(exc_info.value)


class TestDeleteDocument:
    """Test the delete_document() method."""

    @pytest.fixture
    def client(self):
        c = SurfaceDocs(api_key="sd_test_abc123")
        yield c
        c.close()

    @respx.mock
    def test_delete_document(self, client):
        """delete_document() should return None on 204."""
        respx.delete(f"{DEV_BASE}/v1/documents/doc_123").mock(
            return_value=httpx.Response(204)
        )
        result = client.delete_document("doc_123")
        assert result is None

    @respx.mock
    def test_delete_document_not_found(self, client):
        """delete_document() should raise DocumentNotFoundError on 404."""
        respx.delete(f"{DEV_BASE}/v1/documents/doc_missing").mock(
            return_value=httpx.Response(
                404,
                json={"error": {"code": "not_found", "message": "Document not found"}},
            )
        )
        with pytest.raises(DocumentNotFoundError) as exc_info:
            client.delete_document("doc_missing")
        assert "Document not found" in str(exc_info.value)


class TestCreateFolder:
    """Test the create_folder() method."""

    @pytest.fixture
    def client(self):
        c = SurfaceDocs(api_key="sd_test_abc123")
        yield c
        c.close()

    @respx.mock
    def test_create_folder(self, client):
        """create_folder() should return a Folder."""
        route = respx.post(f"{DEV_BASE}/v1/folders").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": "fld_abc",
                    "name": "My Folder",
                    "parent_id": None,
                    "path": "/My Folder",
                    "depth": 0,
                    "created_at": "2024-01-01T00:00:00Z",
                },
            )
        )
        folder = client.create_folder("My Folder")
        assert isinstance(folder, Folder)
        assert folder.id == "fld_abc"
        assert folder.name == "My Folder"
        assert folder.parent_id is None
        assert folder.path == "/My Folder"
        assert folder.depth == 0

        request = route.calls.last.request
        body = json.loads(request.content)
        assert body["name"] == "My Folder"
        assert "parent_id" not in body

    @respx.mock
    def test_create_folder_with_parent(self, client):
        """create_folder() should send parent_id in request body."""
        route = respx.post(f"{DEV_BASE}/v1/folders").mock(
            return_value=httpx.Response(
                201,
                json={
                    "id": "fld_child",
                    "name": "Sub Folder",
                    "parent_id": "fld_parent",
                    "path": "/Parent/Sub Folder",
                    "depth": 1,
                    "created_at": "2024-01-01T00:00:00Z",
                },
            )
        )
        folder = client.create_folder("Sub Folder", parent_id="fld_parent")
        assert folder.parent_id == "fld_parent"
        assert folder.depth == 1

        request = route.calls.last.request
        body = json.loads(request.content)
        assert body["parent_id"] == "fld_parent"

    @respx.mock
    def test_create_folder_parent_not_found(self, client):
        """create_folder() should raise FolderNotFoundError when parent doesn't exist."""
        respx.post(f"{DEV_BASE}/v1/folders").mock(
            return_value=httpx.Response(
                404,
                json={"error": {"code": "not_found", "message": "Folder not found"}},
            )
        )
        with pytest.raises(FolderNotFoundError) as exc_info:
            client.create_folder("Child", parent_id="fld_nonexistent")
        assert "Folder not found" in str(exc_info.value)


class TestListFolders:
    """Test the list_folders() method."""

    @pytest.fixture
    def client(self):
        c = SurfaceDocs(api_key="sd_test_abc123")
        yield c
        c.close()

    @respx.mock
    def test_list_folders(self, client):
        """list_folders() should return a list of Folder objects."""
        respx.get(f"{DEV_BASE}/v1/folders").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": "fld_1",
                        "name": "Docs",
                        "parent_id": None,
                        "path": "/Docs",
                        "depth": 0,
                        "created_at": "2024-01-01T00:00:00Z",
                    },
                    {
                        "id": "fld_2",
                        "name": "Notes",
                        "parent_id": None,
                        "path": "/Notes",
                        "depth": 0,
                        "created_at": "2024-01-02T00:00:00Z",
                    },
                ],
            )
        )
        folders = client.list_folders()
        assert len(folders) == 2
        assert all(isinstance(f, Folder) for f in folders)
        assert folders[0].id == "fld_1"
        assert folders[0].name == "Docs"
        assert folders[1].id == "fld_2"

    @respx.mock
    def test_list_folders_with_parent_filter(self, client):
        """list_folders() should send parent_id as query param."""
        route = respx.get(f"{DEV_BASE}/v1/folders").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": "fld_child",
                        "name": "Sub",
                        "parent_id": "fld_parent",
                        "path": "/Parent/Sub",
                        "depth": 1,
                        "created_at": "2024-01-01T00:00:00Z",
                    },
                ],
            )
        )
        folders = client.list_folders(parent_id="fld_parent")
        assert len(folders) == 1
        assert folders[0].parent_id == "fld_parent"

        request = route.calls.last.request
        assert "parent_id=fld_parent" in str(request.url)

    @respx.mock
    def test_list_folders_empty(self, client):
        """list_folders() should return empty list when no folders exist."""
        respx.get(f"{DEV_BASE}/v1/folders").mock(
            return_value=httpx.Response(200, json=[])
        )
        folders = client.list_folders()
        assert folders == []


# --- Version Tests ---

from surfacedocs import VersionResult, VersionSummary, VersionNotFoundError


MOCK_VERSION_RESPONSE = {
    "id": "doc_123",
    "url": "https://app.surfacedocs.dev/d/doc_123",
    "version": 2,
    "version_count": 2,
    "title": "Updated Doc",
    "block_count": 1,
    "created_at": "2024-01-02T00:00:00Z",
}

MOCK_VERSION_LIST_RESPONSE = {
    "versions": [
        {"version": 2, "title": "V2", "block_count": 1, "created_at": "2024-01-02T00:00:00Z"},
        {"version": 1, "title": "V1", "block_count": 1, "created_at": "2024-01-01T00:00:00Z"},
    ],
    "current_version": 3,
}

MOCK_VERSION_DETAIL_RESPONSE = {
    "version": 1,
    "title": "V1",
    "metadata": None,
    "blocks": [
        {"id": "blk_1", "order": 0, "type": "paragraph", "content": "Old content"},
    ],
    "created_at": "2024-01-01T00:00:00Z",
}


class TestPushVersion:
    """Test push_version() and push_version_raw()."""

    @pytest.fixture
    def client(self):
        c = SurfaceDocs(api_key="sd_test_abc123")
        yield c
        c.close()

    @respx.mock
    def test_push_version_raw(self, client):
        """push_version_raw() should push a new version."""
        route = respx.post(f"{DEV_BASE}/v1/documents/doc_123/versions").mock(
            return_value=httpx.Response(201, json=MOCK_VERSION_RESPONSE)
        )
        result = client.push_version_raw(
            document_id="doc_123",
            title="Updated Doc",
            blocks=[{"type": "paragraph", "content": "New content"}],
        )
        assert isinstance(result, VersionResult)
        assert result.id == "doc_123"
        assert result.version == 2
        assert result.version_count == 2

        request = route.calls.last.request
        body = json.loads(request.content)
        assert body["title"] == "Updated Doc"
        assert body["content_type"] == "markdown"

    @respx.mock
    def test_push_version_with_dict(self, client):
        """push_version() should accept dict content."""
        respx.post(f"{DEV_BASE}/v1/documents/doc_123/versions").mock(
            return_value=httpx.Response(201, json=MOCK_VERSION_RESPONSE)
        )
        result = client.push_version(
            "doc_123",
            {"title": "Updated Doc", "blocks": [{"type": "paragraph", "content": "New"}]},
        )
        assert result.version == 2

    @respx.mock
    def test_push_version_with_json_string(self, client):
        """push_version() should accept JSON string content."""
        respx.post(f"{DEV_BASE}/v1/documents/doc_123/versions").mock(
            return_value=httpx.Response(201, json=MOCK_VERSION_RESPONSE)
        )
        content = json.dumps({
            "title": "Updated Doc",
            "blocks": [{"type": "paragraph", "content": "New"}],
        })
        result = client.push_version("doc_123", content)
        assert result.version == 2

    def test_push_version_invalid_json(self, client):
        """push_version() should raise on invalid JSON."""
        with pytest.raises(ValidationError):
            client.push_version("doc_123", "not json")

    def test_push_version_missing_title(self, client):
        """push_version() should raise when title is missing."""
        with pytest.raises(ValidationError):
            client.push_version("doc_123", {"blocks": [{"type": "paragraph", "content": "x"}]})

    @respx.mock
    def test_push_version_not_found(self, client):
        """push_version_raw() should raise on 404."""
        respx.post(f"{DEV_BASE}/v1/documents/doc_missing/versions").mock(
            return_value=httpx.Response(
                404,
                json={"error": {"code": "not_found", "message": "Document not found"}},
            )
        )
        with pytest.raises(DocumentNotFoundError):
            client.push_version_raw("doc_missing", "T", [{"type": "paragraph", "content": "x"}])


class TestListVersions:
    """Test list_versions()."""

    @pytest.fixture
    def client(self):
        c = SurfaceDocs(api_key="sd_test_abc123")
        yield c
        c.close()

    @respx.mock
    def test_list_versions(self, client):
        """list_versions() should return a list of VersionSummary."""
        respx.get(f"{DEV_BASE}/v1/documents/doc_123/versions").mock(
            return_value=httpx.Response(200, json=MOCK_VERSION_LIST_RESPONSE)
        )
        versions = client.list_versions("doc_123")
        assert len(versions) == 2
        assert all(isinstance(v, VersionSummary) for v in versions)
        assert versions[0].version == 2
        assert versions[1].version == 1

    @respx.mock
    def test_list_versions_not_found(self, client):
        """list_versions() should raise on 404."""
        respx.get(f"{DEV_BASE}/v1/documents/doc_missing/versions").mock(
            return_value=httpx.Response(
                404,
                json={"error": {"code": "not_found", "message": "Document not found"}},
            )
        )
        with pytest.raises(DocumentNotFoundError):
            client.list_versions("doc_missing")


class TestGetVersion:
    """Test get_version()."""

    @pytest.fixture
    def client(self):
        c = SurfaceDocs(api_key="sd_test_abc123")
        yield c
        c.close()

    @respx.mock
    def test_get_version(self, client):
        """get_version() should return a Document with version blocks."""
        respx.get(f"{DEV_BASE}/v1/documents/doc_123/versions/1").mock(
            return_value=httpx.Response(200, json=MOCK_VERSION_DETAIL_RESPONSE)
        )
        doc = client.get_version("doc_123", 1)
        assert isinstance(doc, Document)
        assert doc.title == "V1"
        assert len(doc.blocks) == 1
        assert doc.blocks[0].content == "Old content"

    @respx.mock
    def test_get_version_not_found(self, client):
        """get_version() should raise VersionNotFoundError on 404."""
        respx.get(f"{DEV_BASE}/v1/documents/doc_123/versions/99").mock(
            return_value=httpx.Response(
                404,
                json={"error": {"code": "not_found", "message": "Version not found"}},
            )
        )
        with pytest.raises(VersionNotFoundError):
            client.get_version("doc_123", 99)


class TestRestoreVersion:
    """Test restore_version()."""

    @pytest.fixture
    def client(self):
        c = SurfaceDocs(api_key="sd_test_abc123")
        yield c
        c.close()

    @respx.mock
    def test_restore_version(self, client):
        """restore_version() should return VersionResult."""
        restore_response = {**MOCK_VERSION_RESPONSE, "version": 3, "version_count": 3}
        respx.post(f"{DEV_BASE}/v1/documents/doc_123/versions/1/restore").mock(
            return_value=httpx.Response(200, json=restore_response)
        )
        result = client.restore_version("doc_123", 1)
        assert isinstance(result, VersionResult)
        assert result.version == 3

    @respx.mock
    def test_restore_version_not_found(self, client):
        """restore_version() should raise VersionNotFoundError on 404."""
        respx.post(f"{DEV_BASE}/v1/documents/doc_123/versions/99/restore").mock(
            return_value=httpx.Response(
                404,
                json={"error": {"code": "not_found", "message": "Version not found"}},
            )
        )
        with pytest.raises(VersionNotFoundError):
            client.restore_version("doc_123", 99)


class TestDocumentVersionFields:
    """Test that Document includes version fields."""

    @pytest.fixture
    def client(self):
        c = SurfaceDocs(api_key="sd_test_abc123")
        yield c
        c.close()

    @respx.mock
    def test_get_document_with_version_fields(self, client):
        """get_document() should parse current_version and version_count."""
        response_data = {
            **MOCK_DOCUMENT_RESPONSE,
            "current_version": 3,
            "version_count": 3,
        }
        respx.get(f"{DEV_BASE}/v1/documents/doc_123").mock(
            return_value=httpx.Response(200, json=response_data)
        )
        doc = client.get_document("doc_123")
        assert doc.current_version == 3
        assert doc.version_count == 3

    @respx.mock
    def test_get_document_without_version_fields(self, client):
        """get_document() should handle missing version fields (legacy docs)."""
        respx.get(f"{DEV_BASE}/v1/documents/doc_123").mock(
            return_value=httpx.Response(200, json=MOCK_DOCUMENT_RESPONSE)
        )
        doc = client.get_document("doc_123")
        assert doc.current_version is None
        assert doc.version_count is None


MOCK_SEARCH_RESPONSE = {
    "results": [
        {
            "id": "doc_123",
            "url": "https://app.surfacedocs.dev/d/doc_123",
            "folder_id": "folder_456",
            "title": "Test Doc",
            "content_type": "markdown",
            "block_count": 2,
            "metadata": {"tags": ["python"]},
            "visibility": "private",
            "current_version": 1,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
    ],
    "count": 1,
    "query": "test",
    "tag": None,
    "folder_id": None,
}


class TestSearchDocuments:
    """Test search_documents()."""

    @pytest.fixture
    def client(self):
        c = SurfaceDocs(api_key="sd_test_abc123")
        yield c
        c.close()

    @respx.mock
    def test_search_by_query(self, client):
        """search_documents() should return SearchResult list for query."""
        respx.get(f"{DEV_BASE}/v1/documents/search").mock(
            return_value=httpx.Response(200, json=MOCK_SEARCH_RESPONSE)
        )
        results = client.search_documents(query="test")
        assert len(results) == 1
        assert isinstance(results[0], SearchResult)
        assert results[0].id == "doc_123"
        assert results[0].title == "Test Doc"
        assert results[0].url == "https://app.surfacedocs.dev/d/doc_123"

    @respx.mock
    def test_search_by_tag(self, client):
        """search_documents() should search by tag."""
        tag_response = {**MOCK_SEARCH_RESPONSE, "query": None, "tag": "python"}
        respx.get(f"{DEV_BASE}/v1/documents/search").mock(
            return_value=httpx.Response(200, json=tag_response)
        )
        results = client.search_documents(tag="python")
        assert len(results) == 1
        assert results[0].metadata == {"tags": ["python"]}

    @respx.mock
    def test_search_with_folder_id(self, client):
        """search_documents() should pass folder_id parameter."""
        folder_response = {**MOCK_SEARCH_RESPONSE, "folder_id": "folder_456"}
        respx.get(f"{DEV_BASE}/v1/documents/search").mock(
            return_value=httpx.Response(200, json=folder_response)
        )
        results = client.search_documents(query="test", folder_id="folder_456")
        assert len(results) == 1

    @respx.mock
    def test_search_empty_results(self, client):
        """search_documents() should handle empty results."""
        empty_response = {
            "results": [],
            "count": 0,
            "query": "nonexistent",
            "tag": None,
            "folder_id": None,
        }
        respx.get(f"{DEV_BASE}/v1/documents/search").mock(
            return_value=httpx.Response(200, json=empty_response)
        )
        results = client.search_documents(query="nonexistent")
        assert results == []

    def test_search_requires_query_or_tag(self, client):
        """search_documents() should raise ValidationError without query or tag."""
        with pytest.raises(ValidationError):
            client.search_documents()
