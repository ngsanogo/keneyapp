"""
Pydantic schemas for secure messaging.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.message import MessageStatus


class MessageBase(BaseModel):
    """Base message schema."""

    receiver_id: int = Field(..., description="ID of the message receiver")
    subject: Optional[str] = Field(None, max_length=255, description="Message subject")
    content: str = Field(
        ..., min_length=1, description="Message content (will be encrypted)"
    )
    is_urgent: bool = Field(False, description="Mark message as urgent")
    attachment_ids: Optional[List[int]] = Field(
        None, description="List of attached document IDs"
    )
    reply_to_id: Optional[int] = Field(
        None, description="ID of message being replied to"
    )


class MessageCreate(MessageBase):
    """Schema for creating a new message."""

    pass


class MessageUpdate(BaseModel):
    """Schema for updating message status."""

    status: Optional[MessageStatus] = None
    read_at: Optional[datetime] = None


class MessageResponse(BaseModel):
    """Schema for message response (decrypted)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_id: int
    receiver_id: int
    subject: Optional[str]
    content: str  # Decrypted content
    status: MessageStatus
    is_urgent: bool
    attachment_ids: Optional[List[int]]
    thread_id: Optional[str]
    reply_to_id: Optional[int]
    tenant_id: str
    created_at: datetime
    read_at: Optional[datetime]
    deleted_by_sender: bool
    deleted_by_receiver: bool


class MessageSummary(BaseModel):
    """Lightweight message summary for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_id: int
    receiver_id: int
    subject: Optional[str]
    preview: str  # First 100 chars of content
    status: MessageStatus
    is_urgent: bool
    has_attachments: bool
    thread_id: Optional[str]
    created_at: datetime
    read_at: Optional[datetime]


class ConversationThread(BaseModel):
    """Grouped conversation thread."""

    thread_id: str
    participant_ids: List[int]
    message_count: int
    last_message: MessageSummary
    unread_count: int


class MessageStats(BaseModel):
    """Messaging statistics for dashboard."""

    total_messages: int
    unread_messages: int
    urgent_messages: int
    conversations: int
