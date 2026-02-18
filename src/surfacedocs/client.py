"""HTTP client for saving documents."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import httpx

from surfacedocs.exceptions import (
    AuthenticationError,
    DocumentNotFoundError,
    FolderNotFoundError,
    SurfaceDocsError,
    ValidationError,
    VersionNotFoundError,
)


@dataclass
class SaveResult:
    """Result from saving a document."""

    id: str
    url: str
    folder_id: str


@dataclass
class Block:
    """A content block within a document."""

    id: str
    order: int
    type: str
    content: str
    metadata: dict | None = None


@dataclass
class Document:
    """A SurfaceDocs document."""

    id: str
    url: str
    folder_id: str
    title: str
    content_type: str
    visibility: str
    blocks: list[Block]
    metadata: dict | None = None
    created_at: str | None = None
    updated_at: str | None = None
    current_version: int | None = None
    version_count: int | None = None


@dataclass
class VersionResult:
    """Result from pushing or restoring a version."""

    id: str
    url: str
    version: int
    version_count: int


@dataclass
class VersionSummary:
    """Summary of a document version."""

    version: int
    title: str
    block_count: int
    created_at: str | None = None


@dataclass
class Folder:
    """A SurfaceDocs folder."""

    id: str
    name: str
    parent_id: str | None = None
    path: str = ""
    depth: int = 0
    created_at: str | None = None


@dataclass
class SearchResult:
    """A document search result."""

    id: str
    url: str
    folder_id: str
    title: str
    content_type: str
    block_count: int
    visibility: str
    metadata: dict | None = None
    current_version: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SurfaceDocs:
    """SurfaceDocs API client."""

    PROD_URL = "https://ingress.surfacedocs.dev"
    DEV_URL = "https://ingress.dev.surfacedocs.dev"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        """
        Initialize the SurfaceDocs client.

        Args:
            api_key: API key (sd_live_xxx or sd_test_xxx).
                     Falls back to SURFACEDOCS_API_KEY env var.
            base_url: Override API URL. Auto-detected from key prefix if not set.
        """
        self.api_key = api_key or os.environ.get("SURFACEDOCS_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key required. Pass api_key or set SURFACEDOCS_API_KEY."
            )

        if base_url:
            self.base_url = base_url.rstrip("/")
        else:
            self.base_url = self._detect_base_url(self.api_key)

        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def _detect_base_url(self, api_key: str) -> str:
        """Detect base URL from API key prefix."""
        if api_key.startswith("sd_test_"):
            return self.DEV_URL
        return self.PROD_URL

    def save(
        self,
        content: str | dict[str, Any],
        folder_id: str | None = None,
    ) -> SaveResult:
        """
        Save a document from LLM output.

        Args:
            content: JSON string or dict from LLM response
            folder_id: Target folder (defaults to user's root folder)

        Returns:
            SaveResult with document ID and URL
        """
        # Parse content if string
        if isinstance(content, str):
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid JSON: {e}")
        else:
            data = content

        # Extract fields
        title = data.get("title")
        blocks = data.get("blocks")
        metadata = data.get("metadata")

        if not title:
            raise ValidationError("Document must have a title")
        if not blocks:
            raise ValidationError("Document must have blocks")

        return self.save_raw(
            title=title,
            blocks=blocks,
            folder_id=folder_id,
            metadata=metadata,
        )

    @staticmethod
    def detect_document_type(content: str) -> str:
        """
        Detect if content is a slidev deck or regular markdown.

        Looks for slidev indicators: frontmatter with slidev-specific keys
        (theme, class, layout, background, transition, etc.) and multiple
        slide separators (---).

        Args:
            content: Raw text content to analyze.

        Returns:
            "slidev" if content looks like a slidev deck, "markdown" otherwise.
        """
        lines = content.strip().split("\n")
        if not lines:
            return "markdown"

        # Check for frontmatter with slidev-specific keys
        if lines[0].strip() == "---":
            slidev_keys = {
                "theme",
                "class",
                "layout",
                "background",
                "transition",
                "mdc",
                "fonts",
                "drawings",
                "highlighter",
                "lineNumbers",
                "info",
                "download",
                "exportFilename",
                "monaco",
                "remoteAssets",
            }
            in_frontmatter = True
            has_slidev_frontmatter = False
            for line in lines[1:]:
                if line.strip() == "---":
                    in_frontmatter = False
                    break
                key = line.split(":")[0].strip() if ":" in line else ""
                if key in slidev_keys:
                    has_slidev_frontmatter = True
            if has_slidev_frontmatter and not in_frontmatter:
                return "slidev"

        # Count standalone --- lines (slide separators)
        separator_count = sum(1 for line in lines if line.strip() == "---")
        if separator_count >= 3:
            return "slidev"

        return "markdown"

    def save_raw(
        self,
        title: str,
        blocks: list[dict[str, Any]],
        folder_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        content_type: str = "markdown",
    ) -> SaveResult:
        """
        Save a document with explicit parameters.

        Args:
            title: Document title
            blocks: List of block dicts
            folder_id: Target folder (defaults to user's root folder)
            metadata: Optional metadata dict
            content_type: Document content type (default: "markdown").
                          Use "slidev" for Slidev presentation decks.

        Returns:
            SaveResult with document ID and URL
        """
        payload: dict[str, Any] = {
            "title": title,
            "blocks": blocks,
            "content_type": content_type,
        }

        if folder_id:
            payload["folder_id"] = folder_id
        if metadata:
            payload["metadata"] = metadata

        response = self._client.post("/v1/documents", json=payload)
        data = self._handle_response(response)
        return SaveResult(
            id=data["id"],
            url=data["url"],
            folder_id=data["folder_id"],
        )

    def _handle_response(
        self,
        response: httpx.Response,
        not_found_error: type[SurfaceDocsError] = FolderNotFoundError,
        not_found_message: str = "Folder not found",
    ) -> Any:
        """Handle API response and map errors."""
        if response.status_code in (200, 201):
            return response.json()

        if response.status_code == 204:
            return None

        # Error handling
        try:
            error_data = response.json()
            error_obj = error_data.get("error", {})
            detail = error_obj.get("message", str(error_data))
        except Exception:
            detail = response.text or f"HTTP {response.status_code}"

        if response.status_code == 401:
            raise AuthenticationError(f"Authentication failed: {detail}")
        elif response.status_code == 403:
            raise AuthenticationError(f"Access denied: {detail}")
        elif response.status_code == 404:
            raise not_found_error(f"{not_found_message}: {detail}")
        elif response.status_code == 422:
            raise ValidationError(f"Validation error: {detail}")
        else:
            raise SurfaceDocsError(f"API error ({response.status_code}): {detail}")

    def get_document(self, document_id: str) -> Document:
        """
        Get a document by ID.

        Args:
            document_id: The document ID

        Returns:
            Document with all fields and blocks

        Raises:
            DocumentNotFoundError: If the document doesn't exist
        """
        response = self._client.get(f"/v1/documents/{document_id}")
        data = self._handle_response(
            response,
            not_found_error=DocumentNotFoundError,
            not_found_message="Document not found",
        )
        return Document(
            id=data["id"],
            url=data["url"],
            folder_id=data["folder_id"],
            title=data["title"],
            content_type=data["content_type"],
            visibility=data["visibility"],
            blocks=[
                Block(
                    id=b["id"],
                    order=b["order"],
                    type=b["type"],
                    content=b["content"],
                    metadata=b.get("metadata"),
                )
                for b in data.get("blocks", [])
            ],
            metadata=data.get("metadata"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            current_version=data.get("current_version"),
            version_count=data.get("version_count"),
        )

    def delete_document(self, document_id: str) -> None:
        """
        Delete a document by ID.

        Args:
            document_id: The document ID

        Raises:
            DocumentNotFoundError: If the document doesn't exist
        """
        response = self._client.delete(f"/v1/documents/{document_id}")
        self._handle_response(
            response,
            not_found_error=DocumentNotFoundError,
            not_found_message="Document not found",
        )

    def create_folder(self, name: str, parent_id: str | None = None) -> Folder:
        """
        Create a new folder.

        Args:
            name: Folder name
            parent_id: Parent folder ID (defaults to root)

        Returns:
            Folder with ID and metadata

        Raises:
            FolderNotFoundError: If the parent folder doesn't exist
        """
        payload: dict[str, Any] = {"name": name}
        if parent_id:
            payload["parent_id"] = parent_id

        response = self._client.post("/v1/folders", json=payload)
        data = self._handle_response(response)
        return Folder(
            id=data["id"],
            name=data["name"],
            parent_id=data.get("parent_id"),
            path=data.get("path", ""),
            depth=data.get("depth", 0),
            created_at=data.get("created_at"),
        )

    def list_folders(self, parent_id: str | None = None) -> list[Folder]:
        """
        List folders.

        Args:
            parent_id: Filter by parent folder ID

        Returns:
            List of Folder objects
        """
        params: dict[str, str] = {}
        if parent_id:
            params["parent_id"] = parent_id

        response = self._client.get("/v1/folders", params=params)
        data = self._handle_response(response)
        return [
            Folder(
                id=f["id"],
                name=f["name"],
                parent_id=f.get("parent_id"),
                path=f.get("path", ""),
                depth=f.get("depth", 0),
                created_at=f.get("created_at"),
            )
            for f in data
        ]

    def push_version(
        self,
        document_id: str,
        content: str | dict[str, Any],
    ) -> VersionResult:
        """
        Push a new version from LLM output.

        Args:
            document_id: The document ID to version
            content: JSON string or dict from LLM response

        Returns:
            VersionResult with document ID, URL, and version info
        """
        if isinstance(content, str):
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                raise ValidationError(f"Invalid JSON: {e}")
        else:
            data = content

        title = data.get("title")
        blocks = data.get("blocks")
        metadata = data.get("metadata")

        if not title:
            raise ValidationError("Document must have a title")
        if not blocks:
            raise ValidationError("Document must have blocks")

        return self.push_version_raw(
            document_id=document_id,
            title=title,
            blocks=blocks,
            metadata=metadata,
        )

    def save_slidev(
        self,
        title: str,
        slidev_markdown: str,
        folder_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SaveResult:
        """
        Save a Slidev presentation deck.

        Packages the raw slidev markdown as a single ``slide_deck`` block
        with ``content_type="slidev"``.

        Args:
            title: Document title
            slidev_markdown: Raw slidev markdown (with --- separators)
            folder_id: Target folder (defaults to user's root folder)
            metadata: Optional metadata dict

        Returns:
            SaveResult with document ID and URL
        """
        blocks = [{"type": "slide_deck", "content": slidev_markdown}]
        return self.save_raw(
            title=title,
            blocks=blocks,
            folder_id=folder_id,
            metadata=metadata,
            content_type="slidev",
        )

    def push_version_raw(
        self,
        document_id: str,
        title: str,
        blocks: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
        content_type: str = "markdown",
    ) -> VersionResult:
        """
        Push a new version with explicit parameters.

        Args:
            document_id: The document ID to version
            title: Document title
            blocks: List of block dicts
            metadata: Optional metadata dict
            content_type: Document content type (default: "markdown").
                          Use "slidev" for Slidev presentation decks.

        Returns:
            VersionResult with document ID, URL, and version info
        """
        payload: dict[str, Any] = {
            "title": title,
            "blocks": blocks,
            "content_type": content_type,
        }
        if metadata:
            payload["metadata"] = metadata

        response = self._client.post(
            f"/v1/documents/{document_id}/versions", json=payload
        )
        data = self._handle_response(
            response,
            not_found_error=DocumentNotFoundError,
            not_found_message="Document not found",
        )
        return VersionResult(
            id=data["id"],
            url=data["url"],
            version=data["version"],
            version_count=data["version_count"],
        )

    def list_versions(self, document_id: str) -> list[VersionSummary]:
        """
        List all versions of a document.

        Args:
            document_id: The document ID

        Returns:
            List of VersionSummary objects
        """
        response = self._client.get(
            f"/v1/documents/{document_id}/versions"
        )
        data = self._handle_response(
            response,
            not_found_error=DocumentNotFoundError,
            not_found_message="Document not found",
        )
        return [
            VersionSummary(
                version=v["version"],
                title=v["title"],
                block_count=v["block_count"],
                created_at=v.get("created_at"),
            )
            for v in data.get("versions", [])
        ]

    def get_version(self, document_id: str, version: int) -> Document:
        """
        Get a specific version of a document with its blocks.

        Args:
            document_id: The document ID
            version: The version number

        Returns:
            Document with the version's blocks

        Raises:
            VersionNotFoundError: If the version doesn't exist
        """
        response = self._client.get(
            f"/v1/documents/{document_id}/versions/{version}"
        )
        data = self._handle_response(
            response,
            not_found_error=VersionNotFoundError,
            not_found_message="Version not found",
        )
        return Document(
            id=document_id,
            url="",
            folder_id="",
            title=data["title"],
            content_type=data.get("content_type", "markdown"),
            visibility="",
            blocks=[
                Block(
                    id=b["id"],
                    order=b["order"],
                    type=b["type"],
                    content=b["content"],
                    metadata=b.get("metadata"),
                )
                for b in data.get("blocks", [])
            ],
            metadata=data.get("metadata"),
            created_at=data.get("created_at"),
        )

    def restore_version(self, document_id: str, version: int) -> VersionResult:
        """
        Restore an old version as the new latest.

        Args:
            document_id: The document ID
            version: The version number to restore

        Returns:
            VersionResult with the new version info

        Raises:
            VersionNotFoundError: If the version doesn't exist
        """
        response = self._client.post(
            f"/v1/documents/{document_id}/versions/{version}/restore"
        )
        data = self._handle_response(
            response,
            not_found_error=VersionNotFoundError,
            not_found_message="Version not found",
        )
        return VersionResult(
            id=data["id"],
            url=data["url"],
            version=data["version"],
            version_count=data["version_count"],
        )

    def search_documents(
        self,
        query: str | None = None,
        tag: str | None = None,
        folder_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[SearchResult]:
        """
        Search documents by title prefix and/or tag.

        Args:
            query: Title prefix to search for (case-insensitive)
            tag: Exact tag to match
            folder_id: Optional folder ID to scope search
            limit: Maximum results (default 20, max 50)
            offset: Number of results to skip

        Returns:
            List of SearchResult objects

        Raises:
            ValidationError: If neither query nor tag is provided
        """
        if not query and not tag:
            raise ValidationError("At least one of 'query' or 'tag' is required")

        params: dict[str, str | int] = {}
        if query:
            params["q"] = query
        if tag:
            params["tag"] = tag
        if folder_id:
            params["folder_id"] = folder_id
        params["limit"] = limit
        params["offset"] = offset

        response = self._client.get("/v1/documents/search", params=params)
        data = self._handle_response(response)
        return [
            SearchResult(
                id=r["id"],
                url=r["url"],
                folder_id=r["folder_id"],
                title=r["title"],
                content_type=r["content_type"],
                block_count=r["block_count"],
                visibility=r["visibility"],
                metadata=r.get("metadata"),
                current_version=r.get("current_version"),
                created_at=r.get("created_at"),
                updated_at=r.get("updated_at"),
            )
            for r in data.get("results", [])
        ]

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> SurfaceDocs:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
