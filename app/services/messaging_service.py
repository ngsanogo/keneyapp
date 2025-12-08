"""
Secure messaging service with E2E encryption.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Request
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.audit import log_audit_event
from app.core.encryption import decrypt_data, encrypt_data
from app.models.message import Message, MessageStatus
from app.schemas.message import MessageCreate, MessageStats


def generate_thread_id(user1_id: int, user2_id: int) -> str:
    """Generate consistent thread ID for two users."""
    # Sort IDs to ensure consistency regardless of who initiates
    sorted_ids = sorted([user1_id, user2_id])
    return f"thread_{sorted_ids[0]}_{sorted_ids[1]}_{uuid.uuid4().hex[:8]}"


def get_or_create_thread_id(
    db: Session, sender_id: int, receiver_id: int, reply_to_id: Optional[int] = None
) -> str:
    """Get existing thread ID or create new one."""
    if reply_to_id:
        # Get thread from parent message
        parent = db.query(Message).filter(Message.id == reply_to_id).first()
        if parent and parent.thread_id:
            return str(parent.thread_id)

    # Check for existing thread between users
    existing = (
        db.query(Message)
        .filter(
            or_(
                and_(
                    Message.sender_id == sender_id, Message.receiver_id == receiver_id
                ),
                and_(
                    Message.sender_id == receiver_id, Message.receiver_id == sender_id
                ),
            )
        )
        .first()
    )

    if existing and existing.thread_id:
        return str(existing.thread_id)

    # Create new thread
    return generate_thread_id(sender_id, receiver_id)


def encrypt_message_content(content: str, tenant_id: str) -> str:
    """Encrypt message content."""
    return encrypt_data(content, context={"type": "message", "tenant": tenant_id})


def decrypt_message_content(encrypted_content: str, tenant_id: str) -> str:
    """Decrypt message content."""
    return decrypt_data(
        encrypted_content, context={"type": "message", "tenant": tenant_id}
    )


def create_message(
    db: Session,
    message_data: MessageCreate,
    sender_id: int,
    tenant_id: str,
    request: Optional[Request] = None,
) -> Message:
    """Create a new encrypted message."""
    # Encrypt content
    encrypted_content = encrypt_message_content(message_data.content, tenant_id)

    # Get or create thread ID
    thread_id = get_or_create_thread_id(
        db, sender_id, message_data.receiver_id, message_data.reply_to_id
    )

    # Convert attachment IDs to JSON
    attachment_ids_json = (
        json.dumps(message_data.attachment_ids) if message_data.attachment_ids else None
    )

    # Create message
    message = Message(
        sender_id=sender_id,
        receiver_id=message_data.receiver_id,
        encrypted_content=encrypted_content,
        subject=message_data.subject,
        is_urgent=message_data.is_urgent,
        attachment_ids=attachment_ids_json,
        thread_id=thread_id,
        reply_to_id=message_data.reply_to_id,
        tenant_id=tenant_id,
        status=MessageStatus.SENT,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    # Audit log
    if request:
        log_audit_event(
            db=db,
            user_id=sender_id,
            action="CREATE",
            resource_type="message",
            resource_id=int(message.id) if message.id else None,
            details={
                "receiver_id": message_data.receiver_id,
                "urgent": message_data.is_urgent,
            },
            request=request,
        )

    return message


def get_message(
    db: Session, message_id: int, user_id: int, tenant_id: str
) -> Optional[Message]:
    """Get a message if user is sender or receiver."""
    message = (
        db.query(Message)
        .filter(
            Message.id == message_id,
            Message.tenant_id == tenant_id,
            or_(Message.sender_id == user_id, Message.receiver_id == user_id),
            or_(
                Message.deleted_by_sender.is_(False),
                Message.deleted_by_receiver.is_(False),
            ),
        )
        .first()
    )

    return message


def mark_message_as_read(
    db: Session,
    message_id: int,
    user_id: int,
    tenant_id: str,
    request: Optional[Request] = None,
) -> Optional[Message]:
    """Mark message as read by receiver."""
    message = get_message(db, message_id, user_id, tenant_id)

    if message and message.receiver_id == user_id and not message.read_at:
        setattr(message, "status", MessageStatus.READ)
        setattr(message, "read_at", datetime.now(timezone.utc))
        db.commit()
        db.refresh(message)

        # Audit log
        if request:
            log_audit_event(
                db=db,
                user_id=user_id,
                action="READ",
                resource_type="message",
                resource_id=int(message.id) if message.id else None,
                details={"sender_id": message.sender_id},
                request=request,
            )

    return message


def get_user_messages(
    db: Session,
    user_id: int,
    tenant_id: str,
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
) -> List[Message]:
    """Get messages for a user (inbox + sent)."""
    query = db.query(Message).filter(
        Message.tenant_id == tenant_id,
        or_(Message.sender_id == user_id, Message.receiver_id == user_id),
    )

    # Filter by deleted status
    query = query.filter(
        or_(
            and_(Message.sender_id == user_id, Message.deleted_by_sender.is_(False)),
            and_(
                Message.receiver_id == user_id,
                Message.deleted_by_receiver.is_(False),
            ),
        )
    )

    if unread_only:
        query = query.filter(Message.receiver_id == user_id, Message.read_at.is_(None))

    # Eager load relationships to prevent N+1 queries
    query = query.options(
        joinedload(Message.sender),
        joinedload(Message.receiver)
    )

    return query.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()


def get_conversation(
    db: Session,
    user_id: int,
    other_user_id: int,
    tenant_id: str,
    skip: int = 0,
    limit: int = 100,
) -> List[Message]:
    """Get all messages in a conversation between two users."""
    return (
        db.query(Message)
        .filter(
            Message.tenant_id == tenant_id,
            or_(
                and_(
                    Message.sender_id == user_id, Message.receiver_id == other_user_id
                ),
                and_(
                    Message.sender_id == other_user_id, Message.receiver_id == user_id
                ),
            ),
        )
        .options(
            joinedload(Message.sender),
            joinedload(Message.receiver)
        )
        .order_by(Message.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete_message(
    db: Session,
    message_id: int,
    user_id: int,
    tenant_id: str,
    request: Optional[Request] = None,
) -> bool:
    """Soft delete message for user."""
    message = get_message(db, message_id, user_id, tenant_id)

    if not message:
        return False

    # Soft delete based on user role
    if message.sender_id == user_id:
        setattr(message, "deleted_by_sender", True)
    if message.receiver_id == user_id:
        setattr(message, "deleted_by_receiver", True)

    db.commit()

    # Audit log
    if request:
        log_audit_event(
            db=db,
            user_id=user_id,
            action="DELETE",
            resource_type="message",
            resource_id=int(message.id) if message.id else None,
            details={"soft_delete": True},
            request=request,
        )

    return True


def get_message_stats(db: Session, user_id: int, tenant_id: str) -> MessageStats:
    """Get messaging statistics for user."""
    total = (
        db.query(func.count(Message.id))
        .filter(
            Message.tenant_id == tenant_id,
            or_(Message.sender_id == user_id, Message.receiver_id == user_id),
        )
        .scalar()
        or 0
    )

    total_received = (
        db.query(func.count(Message.id))
        .filter(
            Message.tenant_id == tenant_id,
            Message.receiver_id == user_id,
        )
        .scalar()
        or 0
    )

    total_sent = (
        db.query(func.count(Message.id))
        .filter(
            Message.tenant_id == tenant_id,
            Message.sender_id == user_id,
        )
        .scalar()
        or 0
    )

    unread = (
        db.query(func.count(Message.id))
        .filter(
            Message.tenant_id == tenant_id,
            Message.receiver_id == user_id,
            Message.read_at.is_(None),
            Message.deleted_by_receiver.is_(False),
        )
        .scalar()
        or 0
    )

    urgent = (
        db.query(func.count(Message.id))
        .filter(
            Message.tenant_id == tenant_id,
            Message.receiver_id == user_id,
            Message.is_urgent.is_(True),
            Message.read_at.is_(None),
            Message.deleted_by_receiver.is_(False),
        )
        .scalar()
        or 0
    )

    conversations = (
        db.query(func.count(func.distinct(Message.thread_id)))
        .filter(
            Message.tenant_id == tenant_id,
            or_(Message.sender_id == user_id, Message.receiver_id == user_id),
        )
        .scalar()
        or 0
    )

    return MessageStats(
        total_messages=total,
        total_received=total_received,
        total_sent=total_sent,
        unread_messages=unread,
        unread_count=unread,  # Backwards compatibility
        urgent_messages=urgent,
        urgent_count=urgent,  # Backwards compatibility
        conversations=conversations,
    )


def serialize_message(message: Message, tenant_id: str) -> dict:
    """Serialize message with decrypted content."""
    encrypted_content_str = str(message.encrypted_content)
    decrypted_content = decrypt_message_content(encrypted_content_str, tenant_id)
    attachment_ids_str = str(message.attachment_ids) if message.attachment_ids else None
    attachment_ids = json.loads(attachment_ids_str) if attachment_ids_str else None

    return {
        "id": message.id,
        "sender_id": message.sender_id,
        "receiver_id": message.receiver_id,
        "subject": message.subject,
        "content": decrypted_content,
        "status": message.status,
        "is_urgent": message.is_urgent,
        "attachment_ids": attachment_ids,
        "thread_id": message.thread_id,
        "reply_to_id": message.reply_to_id,
        "tenant_id": message.tenant_id,
        "created_at": message.created_at,
        "read_at": message.read_at,
        "deleted_by_sender": message.deleted_by_sender,
        "deleted_by_receiver": message.deleted_by_receiver,
    }
