"""
Message model for secure patient-doctor communication.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class MessageStatus(str, enum.Enum):
    """Message delivery status."""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class Message(Base):
    """
    Secure messaging between patients and healthcare professionals.
    Messages are encrypted at rest using AES-256-GCM.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    
    # Sender and receiver
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Encrypted message content
    encrypted_content = Column(Text, nullable=False)
    
    # Message metadata
    subject = Column(String(255))
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.SENT, nullable=False)
    is_urgent = Column(Boolean, default=False)
    
    # Attachments (file references)
    attachment_ids = Column(Text)  # JSON array of document IDs
    
    # Thread management
    thread_id = Column(String(255), index=True)  # Group messages in conversations
    reply_to_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    
    # Multi-tenancy
    tenant_id = Column(String(255), nullable=False, index=True)
    
    # Audit fields
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    read_at = Column(DateTime, nullable=True)
    deleted_by_sender = Column(Boolean, default=False)
    deleted_by_receiver = Column(Boolean, default=False)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], backref="received_messages")
    replies = relationship("Message", backref="parent_message", remote_side=[id])

    def __repr__(self):
        return f"<Message {self.id} from User {self.sender_id} to User {self.receiver_id}>"
