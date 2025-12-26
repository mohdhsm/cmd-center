"""Pydantic models for Legal Document API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Document Models
# ============================================================================

class DocumentBase(BaseModel):
    """Base document fields."""
    title: str = Field(..., min_length=1, max_length=500)
    document_type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)
    reference_number: Optional[str] = Field(default=None, max_length=100)
    issuing_authority: Optional[str] = Field(default=None, max_length=200)


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    responsible_employee_id: Optional[int] = None


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    document_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)
    reference_number: Optional[str] = Field(default=None, max_length=100)
    issuing_authority: Optional[str] = Field(default=None, max_length=200)
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    status: Optional[str] = None
    responsible_employee_id: Optional[int] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"active", "expired", "renewal_in_progress", "renewed"}
            if v not in allowed:
                raise ValueError(f"status must be one of: {allowed}")
        return v


class DocumentResponse(BaseModel):
    """Response model for a document."""
    id: int
    title: str
    document_type: str
    description: Optional[str]
    issue_date: Optional[datetime]
    expiry_date: Optional[datetime]
    status: str
    reference_number: Optional[str]
    issuing_authority: Optional[str]
    responsible_employee_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class DocumentWithFiles(DocumentResponse):
    """Document response with attached files."""
    files: list["DocumentFileResponse"] = []
    responsible_employee_name: Optional[str] = None


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Document File Models
# ============================================================================

class DocumentFileCreate(BaseModel):
    """Schema for attaching a file to a document."""
    filename: str = Field(..., min_length=1, max_length=500)
    file_path: str = Field(..., min_length=1, max_length=1000)
    file_type: Optional[str] = Field(default=None, max_length=100)
    file_size: Optional[int] = None


class DocumentFileResponse(BaseModel):
    """Response model for a document file."""
    id: int
    document_id: int
    filename: str
    file_path: str
    file_type: Optional[str]
    file_size: Optional[int]
    version: int
    is_current: bool
    uploaded_by: Optional[str]
    uploaded_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Filter Models
# ============================================================================

class DocumentFilters(BaseModel):
    """Query filters for listing documents."""
    document_type: Optional[str] = None
    status: Optional[str] = None
    responsible_employee_id: Optional[int] = None
    expiring_within_days: Optional[int] = Field(default=None, ge=1)
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


__all__ = [
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentWithFiles",
    "DocumentListResponse",
    "DocumentFileCreate",
    "DocumentFileResponse",
    "DocumentFilters",
]
