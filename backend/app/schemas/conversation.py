"""Conversation and message schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class MessageBase(BaseModel):
    """Base message schema."""

    role: str
    content: str
    citations: list[dict] = []


class MessageCreate(BaseModel):
    """Schema for message creation."""

    content: str


class MessageResponse(MessageBase):
    """Schema for message response."""

    id: UUID
    conversation_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """Schema for conversation creation."""

    title: Optional[str] = None


class ConversationResponse(BaseModel):
    """Schema for conversation response."""

    id: UUID
    user_id: UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Schema for chat request."""

    message: str
    conversation_id: Optional[UUID] = None
    paper_ids: list[UUID] = []


class ChatResponse(BaseModel):
    """Schema for non-streaming chat response."""

    message: MessageResponse
    conversation_id: UUID
    citations: list[dict] = []
