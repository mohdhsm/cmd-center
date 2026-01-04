"""Tests for document tools."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch

from cmd_center.agent.tools.document_tools import (
    GetExpiringDocuments,
    GetExpiringDocumentsParams,
)
from cmd_center.agent.tools.base import ToolResult


class TestGetExpiringDocuments:
    """Tests for GetExpiringDocuments tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = GetExpiringDocuments()
        assert tool.name == "get_expiring_documents"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = GetExpiringDocuments()
        assert len(tool.description) > 20

    def test_params_have_days_field(self):
        """Parameters accept days_until_expiry field."""
        params = GetExpiringDocumentsParams(days_until_expiry=30)
        assert params.days_until_expiry == 30

    def test_params_have_defaults(self):
        """Parameters have sensible defaults."""
        params = GetExpiringDocumentsParams()
        assert params.days_until_expiry == 30
        assert params.limit == 50

    def test_schema_has_days_param(self):
        """Schema includes days_until_expiry parameter."""
        tool = GetExpiringDocuments()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "days_until_expiry" in props

    def test_schema_has_limit_param(self):
        """Schema includes limit parameter."""
        tool = GetExpiringDocuments()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "limit" in props

    @patch("cmd_center.agent.tools.document_tools.get_document_service")
    def test_execute_returns_expiring_documents(self, mock_get_service):
        """Execute returns expiring documents."""
        # Create mock document objects matching DocumentResponse structure
        expiry_date = datetime.now(timezone.utc) + timedelta(days=15)

        mock_doc1 = Mock()
        mock_doc1.id = 1
        mock_doc1.title = "Safety Certificate"
        mock_doc1.document_type = "certificate"
        mock_doc1.expiry_date = expiry_date
        mock_doc1.status = "active"
        mock_doc1.responsible_employee_id = 101
        mock_doc1.reference_number = "CERT-001"
        mock_doc1.issuing_authority = "Safety Authority"

        mock_doc2 = Mock()
        mock_doc2.id = 2
        mock_doc2.title = "Business License"
        mock_doc2.document_type = "license"
        mock_doc2.expiry_date = expiry_date + timedelta(days=5)
        mock_doc2.status = "active"
        mock_doc2.responsible_employee_id = 102
        mock_doc2.reference_number = "LIC-002"
        mock_doc2.issuing_authority = "City Hall"

        mock_service = Mock()
        mock_service.get_expiring_documents.return_value = [mock_doc1, mock_doc2]
        mock_get_service.return_value = mock_service

        tool = GetExpiringDocuments()
        result = tool.parse_and_execute({"days_until_expiry": 30})

        assert result.success is True
        assert "documents" in result.data
        assert len(result.data["documents"]) == 2
        assert result.data["count"] == 2
        assert result.data["days_checked"] == 30
        assert result.data["documents"][0]["title"] == "Safety Certificate"
        assert result.data["documents"][0]["document_type"] == "certificate"

    @patch("cmd_center.agent.tools.document_tools.get_document_service")
    def test_execute_with_custom_days(self, mock_get_service):
        """Execute uses custom days parameter."""
        mock_service = Mock()
        mock_service.get_expiring_documents.return_value = []
        mock_get_service.return_value = mock_service

        tool = GetExpiringDocuments()
        result = tool.parse_and_execute({"days_until_expiry": 7})

        assert result.success is True
        assert result.data["days_checked"] == 7
        # Verify service was called with within_days parameter
        mock_service.get_expiring_documents.assert_called_once()
        call_kwargs = mock_service.get_expiring_documents.call_args.kwargs
        assert call_kwargs.get("within_days") == 7

    @patch("cmd_center.agent.tools.document_tools.get_document_service")
    def test_execute_with_limit(self, mock_get_service):
        """Execute uses limit parameter."""
        mock_service = Mock()
        mock_service.get_expiring_documents.return_value = []
        mock_get_service.return_value = mock_service

        tool = GetExpiringDocuments()
        result = tool.parse_and_execute({"limit": 10})

        assert result.success is True
        # Verify service was called with limit parameter
        mock_service.get_expiring_documents.assert_called_once()
        call_kwargs = mock_service.get_expiring_documents.call_args.kwargs
        assert call_kwargs.get("limit") == 10

    @patch("cmd_center.agent.tools.document_tools.get_document_service")
    def test_execute_calculates_days_until_expiry(self, mock_get_service):
        """Execute calculates days until expiry for each document."""
        expiry_date = datetime.now(timezone.utc) + timedelta(days=10)

        mock_doc = Mock()
        mock_doc.id = 1
        mock_doc.title = "Permit"
        mock_doc.document_type = "permit"
        mock_doc.expiry_date = expiry_date
        mock_doc.status = "active"
        mock_doc.responsible_employee_id = None
        mock_doc.reference_number = None
        mock_doc.issuing_authority = None

        mock_service = Mock()
        mock_service.get_expiring_documents.return_value = [mock_doc]
        mock_get_service.return_value = mock_service

        tool = GetExpiringDocuments()
        result = tool.parse_and_execute({})

        assert result.success is True
        # Should have calculated days_until_expiry (approximately 10)
        assert "days_until_expiry" in result.data["documents"][0]
        days = result.data["documents"][0]["days_until_expiry"]
        assert 9 <= days <= 11  # Allow for test timing variance

    @patch("cmd_center.agent.tools.document_tools.get_document_service")
    def test_execute_handles_service_error(self, mock_get_service):
        """Execute handles service errors gracefully."""
        mock_service = Mock()
        mock_service.get_expiring_documents.side_effect = Exception("Database error")
        mock_get_service.return_value = mock_service

        tool = GetExpiringDocuments()
        result = tool.parse_and_execute({"days_until_expiry": 30})

        assert result.success is False
        assert "Database error" in result.error

    @patch("cmd_center.agent.tools.document_tools.get_document_service")
    def test_execute_returns_empty_list_when_no_expiring_docs(self, mock_get_service):
        """Execute returns empty list when no documents are expiring."""
        mock_service = Mock()
        mock_service.get_expiring_documents.return_value = []
        mock_get_service.return_value = mock_service

        tool = GetExpiringDocuments()
        result = tool.parse_and_execute({})

        assert result.success is True
        assert result.data["documents"] == []
        assert result.data["count"] == 0
