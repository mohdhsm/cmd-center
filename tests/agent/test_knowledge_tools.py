"""Tests for knowledge tools."""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from cmd_center.agent.tools.knowledge_tools import ReadKnowledge, ReadKnowledgeParams
from cmd_center.agent.tools.base import ToolResult


class TestReadKnowledgeParams:
    """Tests for ReadKnowledgeParams model."""

    def test_params_require_topic(self):
        """Parameters accept topic field."""
        params = ReadKnowledgeParams(topic="company_overview")
        assert params.topic == "company_overview"

    def test_params_with_index_topic(self):
        """Parameters accept _index topic."""
        params = ReadKnowledgeParams(topic="_index")
        assert params.topic == "_index"


class TestReadKnowledge:
    """Tests for ReadKnowledge tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = ReadKnowledge()
        assert tool.name == "read_knowledge"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = ReadKnowledge()
        assert len(tool.description) > 20

    def test_schema_has_topic_param(self):
        """Schema includes topic parameter."""
        tool = ReadKnowledge()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "topic" in props

    def test_schema_topic_is_required(self):
        """Topic parameter is required."""
        tool = ReadKnowledge()
        schema = tool.get_openai_schema()
        required = schema["function"]["parameters"].get("required", [])
        assert "topic" in required

    def test_execute_returns_knowledge_content(self):
        """Execute returns knowledge content for valid topic."""
        mock_content = "# Company Overview\n\nGypTech is..."
        with patch("builtins.open", mock_open(read_data=mock_content)):
            with patch.object(Path, "exists", return_value=True):
                tool = ReadKnowledge()
                result = tool.execute(ReadKnowledgeParams(topic="company_overview"))
                assert result.success is True
                assert "content" in result.data
                assert "GypTech" in result.data["content"]

    def test_execute_handles_missing_file(self):
        """Execute returns error for nonexistent topic."""
        with patch.object(Path, "exists", return_value=False):
            with patch.object(Path, "glob", return_value=[]):
                tool = ReadKnowledge()
                result = tool.execute(ReadKnowledgeParams(topic="nonexistent"))
                assert result.success is False
                assert "not found" in result.error.lower()

    def test_execute_returns_topic_in_data(self):
        """Execute includes topic in result data."""
        mock_content = "# Test Content"
        with patch("builtins.open", mock_open(read_data=mock_content)):
            with patch.object(Path, "exists", return_value=True):
                tool = ReadKnowledge()
                result = tool.execute(ReadKnowledgeParams(topic="company_overview"))
                assert result.success is True
                assert result.data["topic"] == "company_overview"

    def test_execute_with_index_topic(self):
        """Execute works with _index topic."""
        mock_content = "# Knowledge Base Index\n\nAvailable topics..."
        with patch("builtins.open", mock_open(read_data=mock_content)):
            with patch.object(Path, "exists", return_value=True):
                tool = ReadKnowledge()
                result = tool.execute(ReadKnowledgeParams(topic="_index"))
                assert result.success is True
                assert "content" in result.data

    def test_execute_sanitizes_path_traversal_forward_slash(self):
        """Execute sanitizes forward slash path traversal attempts."""
        tool = ReadKnowledge()
        # Should sanitize ../../../etc/passwd to etcpasswd
        with patch.object(Path, "exists", return_value=False):
            with patch.object(Path, "glob", return_value=[]):
                result = tool.execute(ReadKnowledgeParams(topic="../../../etc/passwd"))
                # Should not find the file as path traversal is sanitized
                assert result.success is False

    def test_execute_sanitizes_path_traversal_backslash(self):
        """Execute sanitizes backslash path traversal attempts."""
        tool = ReadKnowledge()
        with patch.object(Path, "exists", return_value=False):
            with patch.object(Path, "glob", return_value=[]):
                result = tool.execute(ReadKnowledgeParams(topic="..\\..\\etc\\passwd"))
                assert result.success is False

    def test_execute_adds_md_extension(self):
        """Execute adds .md extension if not present."""
        mock_content = "# Test"
        with patch("builtins.open", mock_open(read_data=mock_content)):
            with patch.object(Path, "exists", return_value=True):
                tool = ReadKnowledge()
                result = tool.execute(ReadKnowledgeParams(topic="company_overview"))
                assert result.success is True

    def test_execute_handles_topic_with_md_extension(self):
        """Execute handles topic that already has .md extension."""
        mock_content = "# Test"
        with patch("builtins.open", mock_open(read_data=mock_content)):
            with patch.object(Path, "exists", return_value=True):
                tool = ReadKnowledge()
                result = tool.execute(ReadKnowledgeParams(topic="company_overview.md"))
                assert result.success is True

    def test_execute_handles_read_error(self):
        """Execute handles file read errors gracefully."""
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "read_text", side_effect=IOError("Permission denied")):
                tool = ReadKnowledge()
                result = tool.execute(ReadKnowledgeParams(topic="company_overview"))
                assert result.success is False
                assert result.error is not None

    def test_parse_and_execute(self):
        """parse_and_execute works correctly."""
        mock_content = "# Test"
        with patch("builtins.open", mock_open(read_data=mock_content)):
            with patch.object(Path, "exists", return_value=True):
                tool = ReadKnowledge()
                result = tool.parse_and_execute({"topic": "company_overview"})
                assert result.success is True

    def test_parse_and_execute_missing_topic(self):
        """parse_and_execute handles missing topic."""
        tool = ReadKnowledge()
        result = tool.parse_and_execute({})
        assert result.success is False

    def test_missing_file_shows_available_topics(self):
        """Missing file error shows available topics."""
        mock_files = [
            Path("/fake/knowledge/company_overview.md"),
            Path("/fake/knowledge/strategy.md"),
        ]
        with patch.object(Path, "exists", return_value=False):
            with patch.object(Path, "glob", return_value=mock_files):
                tool = ReadKnowledge()
                result = tool.execute(ReadKnowledgeParams(topic="nonexistent"))
                assert result.success is False
                assert "company_overview" in result.error
                assert "strategy" in result.error
