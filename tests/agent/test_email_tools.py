"""Tests for email tools."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock

from cmd_center.agent.tools.email_tools import (
    SearchEmails, SearchEmailsParams,
    GetEmails, GetEmailsParams,
)
from cmd_center.agent.tools.base import ToolResult


class TestSearchEmails:
    """Tests for SearchEmails tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = SearchEmails()
        assert tool.name == "search_emails"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = SearchEmails()
        assert len(tool.description) > 20

    def test_params_require_subject(self):
        """Parameters accept subject field."""
        params = SearchEmailsParams(subject="project update")
        assert params.subject == "project update"

    def test_params_have_defaults(self):
        """Parameters have sensible defaults."""
        params = SearchEmailsParams()
        assert params.limit == 10
        assert params.folder == "inbox"
        assert params.subject is None
        assert params.sender is None

    def test_schema_has_subject_param(self):
        """Schema includes subject parameter."""
        tool = SearchEmails()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "subject" in props

    def test_schema_has_sender_param(self):
        """Schema includes sender parameter."""
        tool = SearchEmails()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "sender" in props

    def test_schema_has_limit_param(self):
        """Schema includes limit parameter."""
        tool = SearchEmails()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "limit" in props

    @patch("cmd_center.agent.tools.email_tools.get_msgraph_email_service")
    def test_execute_returns_email_results(self, mock_get_service):
        """Execute returns email search results."""
        # Create mock email objects matching EmailMessage structure
        mock_email1 = Mock()
        mock_email1.id = "email-id-1"
        mock_email1.subject = "Project Update Q1"
        mock_email1.body_preview = "Here is the Q1 update..."
        mock_email1.sender = Mock(address="alice@example.com", name="Alice")
        mock_email1.received_at = datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)
        mock_email1.is_read = False
        mock_email1.has_attachments = True

        mock_email2 = Mock()
        mock_email2.id = "email-id-2"
        mock_email2.subject = "Project Update Q2"
        mock_email2.body_preview = "Here is the Q2 update..."
        mock_email2.sender = Mock(address="bob@example.com", name="Bob")
        mock_email2.received_at = datetime(2024, 4, 15, 14, 0, tzinfo=timezone.utc)
        mock_email2.is_read = True
        mock_email2.has_attachments = False

        mock_service = Mock()
        mock_service.search_emails = AsyncMock(return_value=[mock_email1, mock_email2])
        mock_get_service.return_value = mock_service

        tool = SearchEmails()
        result = tool.parse_and_execute({"subject": "project", "limit": 10})

        assert result.success is True
        assert "emails" in result.data
        assert len(result.data["emails"]) == 2
        assert result.data["count"] == 2
        assert result.data["emails"][0]["subject"] == "Project Update Q1"
        assert result.data["emails"][0]["sender_address"] == "alice@example.com"

    @patch("cmd_center.agent.tools.email_tools.get_msgraph_email_service")
    def test_execute_with_sender_filter(self, mock_get_service):
        """Execute filters by sender."""
        mock_service = Mock()
        mock_service.search_emails = AsyncMock(return_value=[])
        mock_get_service.return_value = mock_service

        tool = SearchEmails()
        result = tool.parse_and_execute({"sender": "alice@example.com"})

        assert result.success is True
        # Verify service was called with sender parameter
        mock_service.search_emails.assert_called_once()
        call_kwargs = mock_service.search_emails.call_args.kwargs
        assert call_kwargs.get("sender") == "alice@example.com"

    @patch("cmd_center.agent.tools.email_tools.get_msgraph_email_service")
    def test_execute_handles_service_error(self, mock_get_service):
        """Execute handles service errors gracefully."""
        mock_service = Mock()
        mock_service.search_emails = AsyncMock(side_effect=Exception("Service unavailable"))
        mock_get_service.return_value = mock_service

        tool = SearchEmails()
        result = tool.parse_and_execute({"subject": "test"})

        assert result.success is False
        assert "Service unavailable" in result.error


class TestGetEmails:
    """Tests for GetEmails tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = GetEmails()
        assert tool.name == "get_emails"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = GetEmails()
        assert len(tool.description) > 20

    def test_params_have_defaults(self):
        """Parameters have sensible defaults."""
        params = GetEmailsParams()
        assert params.limit == 20
        assert params.folder == "inbox"
        assert params.unread_only is False

    def test_schema_has_limit_param(self):
        """Schema includes limit parameter."""
        tool = GetEmails()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "limit" in props

    def test_schema_has_folder_param(self):
        """Schema includes folder parameter."""
        tool = GetEmails()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "folder" in props

    def test_schema_has_unread_only_param(self):
        """Schema includes unread_only parameter."""
        tool = GetEmails()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "unread_only" in props

    @patch("cmd_center.agent.tools.email_tools.get_msgraph_email_service")
    def test_execute_returns_recent_emails(self, mock_get_service):
        """Execute returns recent emails."""
        mock_email = Mock()
        mock_email.id = "email-id-1"
        mock_email.subject = "Weekly Report"
        mock_email.body_preview = "This week's highlights..."
        mock_email.sender = Mock(address="reports@company.com", name="Reports")
        mock_email.received_at = datetime(2024, 1, 20, 9, 0, tzinfo=timezone.utc)
        mock_email.is_read = False
        mock_email.has_attachments = True

        mock_service = Mock()
        mock_service.get_emails = AsyncMock(return_value=[mock_email])
        mock_get_service.return_value = mock_service

        tool = GetEmails()
        result = tool.parse_and_execute({"limit": 20})

        assert result.success is True
        assert "emails" in result.data
        assert len(result.data["emails"]) == 1
        assert result.data["count"] == 1
        assert result.data["folder"] == "inbox"
        assert result.data["emails"][0]["subject"] == "Weekly Report"

    @patch("cmd_center.agent.tools.email_tools.get_msgraph_email_service")
    def test_execute_with_unread_only(self, mock_get_service):
        """Execute filters unread only."""
        mock_service = Mock()
        mock_service.get_emails = AsyncMock(return_value=[])
        mock_get_service.return_value = mock_service

        tool = GetEmails()
        result = tool.parse_and_execute({"unread_only": True})

        assert result.success is True
        # Verify service was called with unread_only parameter
        mock_service.get_emails.assert_called_once()
        call_kwargs = mock_service.get_emails.call_args.kwargs
        assert call_kwargs.get("unread_only") is True

    @patch("cmd_center.agent.tools.email_tools.get_msgraph_email_service")
    def test_execute_with_different_folder(self, mock_get_service):
        """Execute reads from specified folder."""
        mock_service = Mock()
        mock_service.get_emails = AsyncMock(return_value=[])
        mock_get_service.return_value = mock_service

        tool = GetEmails()
        result = tool.parse_and_execute({"folder": "sentitems"})

        assert result.success is True
        # Verify service was called with folder parameter
        mock_service.get_emails.assert_called_once()
        call_kwargs = mock_service.get_emails.call_args.kwargs
        assert call_kwargs.get("folder") == "sentitems"

    @patch("cmd_center.agent.tools.email_tools.get_msgraph_email_service")
    def test_execute_handles_service_error(self, mock_get_service):
        """Execute handles service errors gracefully."""
        mock_service = Mock()
        mock_service.get_emails = AsyncMock(side_effect=Exception("Network error"))
        mock_get_service.return_value = mock_service

        tool = GetEmails()
        result = tool.parse_and_execute({})

        assert result.success is False
        assert "Network error" in result.error
