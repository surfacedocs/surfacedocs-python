"""Tests for Slidev support in SurfaceDocs SDK."""

import json

import httpx
import pytest
import respx

from surfacedocs import SurfaceDocs


DEV_BASE = "https://ingress.dev.surfacedocs.dev"

MOCK_SAVE_RESPONSE = {
    "id": "doc_slidev_1",
    "url": "https://app.surfacedocs.dev/d/doc_slidev_1",
    "folder_id": "folder_root",
    "title": "My Slides",
    "block_count": 1,
    "created_at": "2024-01-01T00:00:00Z",
}

MOCK_VERSION_RESPONSE = {
    "id": "doc_slidev_1",
    "url": "https://app.surfacedocs.dev/d/doc_slidev_1",
    "version": 2,
    "version_count": 2,
}

SAMPLE_SLIDEV = """\
---
theme: seriph
class: text-center
---

# Welcome

Hello world

---

# Slide 2

More content
"""

SAMPLE_MARKDOWN = """\
# My Document

Some paragraph text.

## Section 2

More text here.
"""


class TestDetectDocumentType:
    """Test the detect_document_type() static method."""

    def test_detects_slidev_with_theme_frontmatter(self):
        content = "---\ntheme: seriph\n---\n\n# Slide 1\n\n---\n\n# Slide 2\n"
        assert SurfaceDocs.detect_document_type(content) == "slidev"

    def test_detects_slidev_with_class_frontmatter(self):
        content = "---\nclass: text-center\n---\n\n# Hello\n\n---\n\n# World\n"
        assert SurfaceDocs.detect_document_type(content) == "slidev"

    def test_detects_slidev_with_layout_frontmatter(self):
        content = "---\nlayout: cover\n---\n\n# Title\n\n---\n\n# Body\n"
        assert SurfaceDocs.detect_document_type(content) == "slidev"

    def test_detects_slidev_with_transition_frontmatter(self):
        content = "---\ntransition: slide-left\n---\n\n# Slide 1\n\n---\n\n# Slide 2\n"
        assert SurfaceDocs.detect_document_type(content) == "slidev"

    def test_detects_slidev_with_multiple_slidev_keys(self):
        content = SAMPLE_SLIDEV
        assert SurfaceDocs.detect_document_type(content) == "slidev"

    def test_detects_slidev_by_separator_count(self):
        """Three or more --- lines → slidev even without known frontmatter keys."""
        content = "---\ntitle: Deck\n---\n\n# Slide 1\n\n---\n\n# Slide 2\n"
        assert SurfaceDocs.detect_document_type(content) == "slidev"

    def test_detects_markdown_for_regular_doc(self):
        assert SurfaceDocs.detect_document_type(SAMPLE_MARKDOWN) == "markdown"

    def test_detects_markdown_for_empty_content(self):
        assert SurfaceDocs.detect_document_type("") == "markdown"

    def test_detects_markdown_for_single_hr(self):
        """A single --- (horizontal rule) should not be slidev."""
        content = "# Title\n\nSome text\n\n---\n\nMore text\n"
        assert SurfaceDocs.detect_document_type(content) == "markdown"

    def test_detects_markdown_for_frontmatter_only(self):
        """YAML frontmatter without slidev keys and only 2 separators → markdown."""
        content = "---\ntitle: My Doc\nauthor: Sam\n---\n\n# Hello\n"
        assert SurfaceDocs.detect_document_type(content) == "markdown"

    def test_detects_slidev_with_background_key(self):
        content = "---\nbackground: /image.jpg\n---\n\n# Slide\n\n---\n\n# Next\n"
        assert SurfaceDocs.detect_document_type(content) == "slidev"

    def test_detects_slidev_with_highlighter_key(self):
        content = "---\nhighlighter: shiki\n---\n\n# Code\n\n---\n\n# Demo\n"
        assert SurfaceDocs.detect_document_type(content) == "slidev"

    def test_callable_as_static_method(self):
        """Should be callable without an instance."""
        result = SurfaceDocs.detect_document_type("# Just markdown")
        assert result == "markdown"


class TestSaveSlidev:
    """Test the save_slidev() convenience method."""

    @pytest.fixture
    def client(self):
        c = SurfaceDocs(api_key="sd_test_abc123")
        yield c
        c.close()

    @respx.mock
    def test_save_slidev_sends_correct_payload(self, client):
        route = respx.post(f"{DEV_BASE}/v1/documents").mock(
            return_value=httpx.Response(201, json=MOCK_SAVE_RESPONSE)
        )
        result = client.save_slidev(title="My Slides", slidev_markdown=SAMPLE_SLIDEV)

        assert result.id == "doc_slidev_1"
        request = route.calls.last.request
        body = json.loads(request.content)
        assert body["content_type"] == "slidev"
        assert len(body["blocks"]) == 1
        assert body["blocks"][0]["type"] == "slide_deck"
        assert body["blocks"][0]["content"] == SAMPLE_SLIDEV

    @respx.mock
    def test_save_slidev_with_folder_id(self, client):
        route = respx.post(f"{DEV_BASE}/v1/documents").mock(
            return_value=httpx.Response(201, json=MOCK_SAVE_RESPONSE)
        )
        client.save_slidev(
            title="My Slides",
            slidev_markdown=SAMPLE_SLIDEV,
            folder_id="folder_custom",
        )
        body = json.loads(route.calls.last.request.content)
        assert body["folder_id"] == "folder_custom"

    @respx.mock
    def test_save_slidev_with_metadata(self, client):
        route = respx.post(f"{DEV_BASE}/v1/documents").mock(
            return_value=httpx.Response(201, json=MOCK_SAVE_RESPONSE)
        )
        client.save_slidev(
            title="My Slides",
            slidev_markdown=SAMPLE_SLIDEV,
            metadata={"source": "test"},
        )
        body = json.loads(route.calls.last.request.content)
        assert body["metadata"] == {"source": "test"}


class TestSaveRawWithContentType:
    """Test that save_raw() properly forwards content_type."""

    @pytest.fixture
    def client(self):
        c = SurfaceDocs(api_key="sd_test_abc123")
        yield c
        c.close()

    @respx.mock
    def test_save_raw_defaults_to_markdown(self, client):
        route = respx.post(f"{DEV_BASE}/v1/documents").mock(
            return_value=httpx.Response(201, json=MOCK_SAVE_RESPONSE)
        )
        client.save_raw(title="Doc", blocks=[{"type": "paragraph", "content": "Hi"}])
        body = json.loads(route.calls.last.request.content)
        assert body["content_type"] == "markdown"

    @respx.mock
    def test_save_raw_with_slidev_content_type(self, client):
        route = respx.post(f"{DEV_BASE}/v1/documents").mock(
            return_value=httpx.Response(201, json=MOCK_SAVE_RESPONSE)
        )
        client.save_raw(
            title="Slides",
            blocks=[{"type": "slide_deck", "content": SAMPLE_SLIDEV}],
            content_type="slidev",
        )
        body = json.loads(route.calls.last.request.content)
        assert body["content_type"] == "slidev"


class TestPushVersionRawWithContentType:
    """Test that push_version_raw() properly forwards content_type."""

    @pytest.fixture
    def client(self):
        c = SurfaceDocs(api_key="sd_test_abc123")
        yield c
        c.close()

    @respx.mock
    def test_push_version_raw_defaults_to_markdown(self, client):
        route = respx.post(f"{DEV_BASE}/v1/documents/doc_123/versions").mock(
            return_value=httpx.Response(201, json=MOCK_VERSION_RESPONSE)
        )
        client.push_version_raw(
            document_id="doc_123",
            title="V2",
            blocks=[{"type": "paragraph", "content": "Updated"}],
        )
        body = json.loads(route.calls.last.request.content)
        assert body["content_type"] == "markdown"

    @respx.mock
    def test_push_version_raw_with_slidev(self, client):
        route = respx.post(f"{DEV_BASE}/v1/documents/doc_123/versions").mock(
            return_value=httpx.Response(201, json=MOCK_VERSION_RESPONSE)
        )
        client.push_version_raw(
            document_id="doc_123",
            title="V2 Slides",
            blocks=[{"type": "slide_deck", "content": SAMPLE_SLIDEV}],
            content_type="slidev",
        )
        body = json.loads(route.calls.last.request.content)
        assert body["content_type"] == "slidev"
        assert body["blocks"][0]["type"] == "slide_deck"
