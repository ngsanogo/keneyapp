"""
WebSocket router for real-time notifications and updates
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging_middleware import logger
from app.core.security import decode_access_token
from app.core.websocket import manager
from app.models.user import User

router = APIRouter(tags=["websocket"])


async def get_current_user_ws(
    websocket: WebSocket,
    token: Optional[str] = None,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Authenticate WebSocket connection using JWT token

    Args:
        websocket: WebSocket connection
        token: JWT access token (from query params)
        db: Database session

    Returns:
        Authenticated user or None
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")

        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        user = db.query(User).filter(User.id == int(user_id)).first()

        if not user or not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        return user

    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Main WebSocket endpoint for real-time updates

    Connection URL: ws://localhost:8000/ws?token=<jwt_token>

    Message Types:
    - ping: Keep-alive ping
    - join_room: Join a notification room
    - leave_room: Leave a notification room
    - message: Send message to room

    Server pushes:
    - notification: General notifications
    - appointment: Appointment updates
    - message: New messages
    - lab_result: Lab result updates
    - document: Document updates
    """
    # Authenticate user
    user = await get_current_user_ws(websocket, token, db)
    if not user:
        return

    user_id = str(user.id)

    # Connect user
    await manager.connect(
        websocket,
        user_id,
        metadata={
            "tenant_id": user.tenant_id,
            "role": user.role.value,
            "username": user.username,
        },
    )

    # Join user's personal room (for targeted notifications)
    manager.join_room(f"user:{user_id}", user_id)

    # Join tenant room (for tenant-wide broadcasts)
    manager.join_room(f"tenant:{user.tenant_id}", user_id)

    # Send welcome message
    await manager.send_json_message(
        {
            "message": "Connected to real-time notifications",
            "user_id": user_id,
            "stats": manager.get_stats(),
        },
        user_id,
        message_type="welcome",
    )

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type")

                # Handle ping
                if message_type == "ping":
                    await manager.send_json_message(
                        {"pong": True}, user_id, message_type="pong"
                    )

                # Handle join room
                elif message_type == "join_room":
                    room_id = message.get("room_id")
                    if room_id:
                        manager.join_room(room_id, user_id)
                        await manager.send_json_message(
                            {"joined": room_id}, user_id, message_type="room_joined"
                        )
                        logger.info(f"User {user_id} joined room {room_id}")

                # Handle leave room
                elif message_type == "leave_room":
                    room_id = message.get("room_id")
                    if room_id:
                        manager.leave_room(room_id, user_id)
                        await manager.send_json_message(
                            {"left": room_id}, user_id, message_type="room_left"
                        )
                        logger.info(f"User {user_id} left room {room_id}")

                # Handle room message
                elif message_type == "message":
                    room_id = message.get("room_id")
                    content = message.get("content")

                    if room_id and content:
                        await manager.broadcast_to_room(
                            room_id,
                            {
                                "sender_id": user_id,
                                "sender": user.username,
                                "content": content,
                            },
                            message_type="room_message",
                            exclude_user=user_id,  # Don't echo back to sender
                        )

                # Unknown message type
                else:
                    await manager.send_json_message(
                        {"error": f"Unknown message type: {message_type}"},
                        user_id,
                        message_type="error",
                    )

            except json.JSONDecodeError:
                await manager.send_json_message(
                    {"error": "Invalid JSON"}, user_id, message_type="error"
                )
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await manager.send_json_message(
                    {"error": "Internal server error"}, user_id, message_type="error"
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket disconnected: user={user_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)


@router.websocket("/ws/notifications/{user_id}")
async def user_notifications_endpoint(
    websocket: WebSocket,
    user_id: int,
    token: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Dedicated WebSocket endpoint for user notifications

    Connection URL: ws://localhost:8000/ws/notifications/{user_id}?token=<jwt_token>

    Receives only:
    - notification: General notifications for this user
    - alert: High-priority alerts
    """
    # Authenticate user
    user = await get_current_user_ws(websocket, token, db)
    if not user or user.id != user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id_str = str(user.id)

    # Connect user
    await manager.connect(
        websocket,
        user_id_str,
        metadata={
            "tenant_id": user.tenant_id,
            "role": user.role.value,
            "connection_type": "notifications_only",
        },
    )

    # Join notification room
    room_id = f"notifications:user:{user_id_str}"
    manager.join_room(room_id, user_id_str)

    try:
        while True:
            # Just keep connection alive, server pushes notifications
            data = await websocket.receive_text()

            # Handle ping
            if data == "ping":
                await manager.send_personal_message("pong", user_id_str, "pong")

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id_str)
        logger.info(f"Notification WebSocket disconnected: user={user_id_str}")
