"""Tests for Omnious prompts."""

import pytest
from cmd_center.agent.core.prompts import SYSTEM_PROMPT, build_system_prompt


class TestSystemPrompt:
    """Test system prompt configuration."""

    def test_system_prompt_contains_identity(self):
        """System prompt establishes Omnious identity."""
        assert "Omnious" in SYSTEM_PROMPT
        assert "all-knowing" in SYSTEM_PROMPT.lower()

    def test_system_prompt_contains_personality(self):
        """System prompt includes personality traits."""
        prompt_lower = SYSTEM_PROMPT.lower()
        assert "friendly" in prompt_lower or "witty" in prompt_lower

    def test_system_prompt_contains_boundaries(self):
        """System prompt includes scope boundaries."""
        prompt_lower = SYSTEM_PROMPT.lower()
        assert "delete" in prompt_lower  # Mentions no deletion
        assert "confirm" in prompt_lower  # Mentions confirmation

    def test_build_system_prompt_basic(self):
        """Build system prompt returns valid string."""
        prompt = build_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_build_system_prompt_with_context(self):
        """Build system prompt can include additional context."""
        prompt = build_system_prompt(additional_context="Today is Monday.")
        assert "Monday" in prompt
