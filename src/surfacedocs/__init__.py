"""SurfaceDocs Python SDK - Save LLM-generated documents."""

from surfacedocs.schema import DOCUMENT_SCHEMA
from surfacedocs.prompt import SYSTEM_PROMPT
from surfacedocs.client import SurfaceDocs
from surfacedocs.exceptions import (
    SurfaceDocsError,
    AuthenticationError,
    ValidationError,
    FolderNotFoundError,
)

__version__ = "0.1.0"

__all__ = [
    "DOCUMENT_SCHEMA",
    "SYSTEM_PROMPT",
    "SurfaceDocs",
    "SurfaceDocsError",
    "AuthenticationError",
    "ValidationError",
    "FolderNotFoundError",
    "__version__",
]
