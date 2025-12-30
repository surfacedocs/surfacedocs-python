"""Tests for SYSTEM_PROMPT."""

import pytest

from surfacedocs import SYSTEM_PROMPT
from surfacedocs.prompt import SYSTEM_PROMPT as PROMPT_DIRECT


class TestSystemPrompt:
    """Test the SYSTEM_PROMPT constant."""

    def test_prompt_exists(self):
        """SYSTEM_PROMPT should exist."""
        assert SYSTEM_PROMPT is not None

    def test_prompt_is_string(self):
        """SYSTEM_PROMPT should be a string."""
        assert isinstance(SYSTEM_PROMPT, str)


class TestPromptImports:
    """Test prompt import paths."""

    def test_import_from_package(self):
        """SYSTEM_PROMPT should be importable from main package."""
        from surfacedocs import SYSTEM_PROMPT as PkgPrompt
        assert PkgPrompt is not None

    def test_import_from_module(self):
        """SYSTEM_PROMPT should be importable from prompt module."""
        assert PROMPT_DIRECT is not None

    def test_imports_are_same_object(self):
        """Both imports should reference the same object."""
        assert SYSTEM_PROMPT is PROMPT_DIRECT


class TestPromptModuleDocstring:
    """Test prompt module documentation."""

    def test_module_has_docstring(self):
        """Prompt module should have a docstring."""
        from surfacedocs import prompt
        assert prompt.__doc__ is not None
