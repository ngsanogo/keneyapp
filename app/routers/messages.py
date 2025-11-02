"""
API routes for secure messaging between patients and healthcare professionals.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
    MessageStats,
)
from app.services import messaging_service

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def send_message(
    request: Request,
    message: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Send a secure encrypted message to another user.

    **Access:** All authenticated users

    **Rate limit:** 30 requests per minute

    **Security:**
    - Messages are encrypted at rest with AES-256-GCM
    - Only sender and receiver can access the message
    - All sends are audit logged
    """
    # Verify receiver exists and is in same tenant
    receiver = (
        db.query(User)
        .filter(
            User.id == message.receiver_id, User.tenant_id == current_user.tenant_id
        )
        .first()
    )

    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receiver not found or not in your organization",
        )

    # Create encrypted message
    db_message = messaging_service.create_message(
        db=db,
        message_data=message,
        sender_id=current_user.id,
        tenant_id=str(current_user.tenant_id),
        request=request,
    )

    # Return decrypted response
    return messaging_service.serialize_message(db_message, str(current_user.tenant_id))


@router.get("/", response_model=List[MessageResponse])
@limiter.limit("60/minute")
async def get_messages(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get all messages for current user (inbox + sent).

    **Access:** All authenticated users

    **Rate limit:** 60 requests per minute

    **Query Parameters:**
    - `skip`: Number of messages to skip (pagination)
    - `limit`: Maximum number of messages to return (max 100)
    - `unread_only`: If true, only return unread messages
    """
    if limit > 100:
        limit = 100

    messages = messaging_service.get_user_messages(
        db=db,
        user_id=current_user.id,
        tenant_id=str(current_user.tenant_id),
        skip=skip,
        limit=limit,
        unread_only=unread_only,
    )

    return [
        messaging_service.serialize_message(msg, str(current_user.tenant_id))
        for msg in messages
    ]


@router.get("/stats", response_model=MessageStats)
@limiter.limit("60/minute")
async def get_message_statistics(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get messaging statistics for current user.

    **Access:** All authenticated users

    **Rate limit:** 60 requests per minute

    **Returns:**
    - Total messages count
    - Unread messages count
    - Urgent unread messages count
    - Number of active conversations
    """
    return messaging_service.get_message_stats(
        db=db, user_id=current_user.id, tenant_id=str(current_user.tenant_id)
    )


@router.get("/conversation/{other_user_id}", response_model=List[MessageResponse])
@limiter.limit("60/minute")
async def get_conversation(
    request: Request,
    other_user_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get full conversation with another user.

    **Access:** All authenticated users

    **Rate limit:** 60 requests per minute

    **Query Parameters:**
    - `skip`: Number of messages to skip
    - `limit`: Maximum number of messages (max 100)
    """
    if limit > 100:
        limit = 100

    # Verify other user exists in same tenant
    other_user = (
        db.query(User)
        .filter(User.id == other_user_id, User.tenant_id == current_user.tenant_id)
        .first()
    )

    if not other_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or not in your organization",
        )

    messages = messaging_service.get_conversation(
        db=db,
        user_id=current_user.id,
        other_user_id=other_user_id,
        tenant_id=str(current_user.tenant_id),
        skip=skip,
        limit=limit,
    )

    return [
        messaging_service.serialize_message(msg, str(current_user.tenant_id))
        for msg in messages
    ]


@router.get("/{message_id}", response_model=MessageResponse)
@limiter.limit("60/minute")
async def get_message(
    request: Request,
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific message by ID.

    **Access:** All authenticated users (must be sender or receiver)

    **Rate limit:** 60 requests per minute

    **Security:** Automatically marks message as read if accessed by receiver
    """
    message = messaging_service.get_message(
        db=db,
        message_id=message_id,
        user_id=current_user.id,
        tenant_id=str(current_user.tenant_id),
    )

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or access denied",
        )

    # Auto-mark as read if receiver is accessing
    if message.receiver_id == current_user.id and not message.read_at:
        message = messaging_service.mark_message_as_read(
            db=db,
            message_id=message_id,
            user_id=current_user.id,
            tenant_id=str(current_user.tenant_id),
            request=request,
        )

    return messaging_service.serialize_message(message, str(current_user.tenant_id))


@router.post("/{message_id}/read", response_model=MessageResponse)
@limiter.limit("60/minute")
async def mark_as_read(
    request: Request,
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Mark a message as read.

    **Access:** Message receiver only

    **Rate limit:** 60 requests per minute
    """
    message = messaging_service.mark_message_as_read(
        db=db,
        message_id=message_id,
        user_id=current_user.id,
        tenant_id=str(current_user.tenant_id),
        request=request,
    )

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or access denied",
        )

    return messaging_service.serialize_message(message, str(current_user.tenant_id))


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("60/minute")
async def delete_message(
    request: Request,
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Delete a message (soft delete).

    **Access:** Message sender or receiver

    **Rate limit:** 60 requests per minute

    **Note:** This is a soft delete. The message remains in the database but is hidden from the user's view.
    """
    success = messaging_service.delete_message(
        db=db,
        message_id=message_id,
        user_id=current_user.id,
        tenant_id=str(current_user.tenant_id),
        request=request,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found or access denied",
        )

    return None
