"""Paper schemas for API validation."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class PaperBase(BaseModel):
    """Base paper schema."""

    title: str
    authors: list[str] = []
    year: Optional[int] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None


class PaperCreate(PaperBase):
    """Schema for paper creation (metadata update)."""

    pass


class PaperResponse(PaperBase):
    """Schema for paper response."""

    id: UUID
    user_id: UUID
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    uploaded_at: datetime
    metadata: dict = {}

    class Config:
        from_attributes = True


class PaperList(BaseModel):
    """Schema for paginated paper list."""

    papers: list[PaperResponse]
    total: int
    page: int
    page_size: int
