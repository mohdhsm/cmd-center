"""Document tools for the agent."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult
from ...backend.services.document_service import get_document_service


class GetExpiringDocumentsParams(BaseModel):
    """Parameters for get_expiring_documents tool."""

    days_until_expiry: int = Field(
        default=30,
        description="Find documents expiring within this many days",
    )
    limit: int = Field(
        default=50,
        description="Maximum number of documents to return",
    )


class GetExpiringDocuments(BaseTool):
    """Get documents that are expiring soon."""

    name = "get_expiring_documents"
    description = (
        "Get documents (certificates, IDs, permits) that are expiring within a "
        "specified number of days. Use to track compliance and upcoming renewals."
    )
    parameters_model = GetExpiringDocumentsParams

    def execute(self, params: GetExpiringDocumentsParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_document_service()
            documents = service.get_expiring_documents(
                within_days=params.days_until_expiry,
                limit=params.limit,
            )

            now = datetime.now(timezone.utc)

            documents_data = [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "document_type": doc.document_type,
                    "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
                    "days_until_expiry": (doc.expiry_date - now).days if doc.expiry_date else None,
                    "status": doc.status,
                    "responsible_employee_id": doc.responsible_employee_id,
                    "reference_number": doc.reference_number,
                    "issuing_authority": doc.issuing_authority,
                }
                for doc in documents
            ]

            return ToolResult(
                success=True,
                data={
                    "documents": documents_data,
                    "count": len(documents_data),
                    "days_checked": params.days_until_expiry,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
