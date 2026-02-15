"""SurfaceDocs Python SDK - Save LLM-generated documents."""

from surfacedocs.schema import DOCUMENT_SCHEMA, GEMINI_DOCUMENT_SCHEMA, OPENAI_DOCUMENT_SCHEMA
from surfacedocs.prompt import SYSTEM_PROMPT
from surfacedocs.client import Block, Document, Folder, SaveResult, SurfaceDocs, VersionResult, VersionSummary
from surfacedocs.exceptions import (
    SurfaceDocsError,
    AuthenticationError,
    DocumentNotFoundError,
    ValidationError,
    FolderNotFoundError,
    VersionNotFoundError,
)

__version__ = "0.1.0"

__all__ = [
    "DOCUMENT_SCHEMA",
    "GEMINI_DOCUMENT_SCHEMA",
    "OPENAI_DOCUMENT_SCHEMA",
    "SYSTEM_PROMPT",
    "Block",
    "Document",
    "Folder",
    "SaveResult",
    "SurfaceDocs",
    "VersionResult",
    "VersionSummary",
    "SurfaceDocsError",
    "AuthenticationError",
    "DocumentNotFoundError",
    "ValidationError",
    "FolderNotFoundError",
    "VersionNotFoundError",
    "__version__",
]
