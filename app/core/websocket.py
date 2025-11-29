"""
WebSocket manager for real-time features
Handles WebSocket connections, rooms, and broadcasting
"""

from datetime import datetime
from typing import Dict, List, Optional, Set

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from app.core.logging_middleware import logger


class ConnectionManager:
    """
    WebSocket connection manager

    Features:
    - Connection lifecycle management
    - Room-based messaging
    - User-specific channels
    - Broadcast capabilities
    - Connection monitoring
    """

    def __init__(self):
        # Active connections: user_id -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}

        # Room memberships: room_id -> Set[user_id]
        self.rooms: Dict[str, Set[str]] = {}

        # User -> rooms mapping for cleanup
        self.user_rooms: Dict[str, Set[str]] = {}

        # Connection metadata
        self.connection_metadata: Dict[str, Dict] = {}

        # Stats
        self.stats = {"total_connections": 0, "messages_sent": 0, "broadcasts_sent": 0}

    async def connect(self, websocket: WebSocket, user_id: str, metadata: Optional[Dict] = None):
        """
        Accept and register a new WebSocket connection

        Args:
            websocket: WebSocket connection
            user_id: User identifier
            metadata: Optional connection metadata (tenant_id, role, etc.)
        """
        await websocket.accept()

        # Add to active connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)

        # Store metadata
        conn_id = f"{user_id}_{id(websocket)}"
        self.connection_metadata[conn_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
            **(metadata or {}),
        }

        self.stats["total_connections"] += 1

        total_conns = len(self.get_all_connections())
        logger.info(f"WebSocket connected: user={user_id}, " f"total_connections={total_conns}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        """
        Remove WebSocket connection and clean up

        Args:
            websocket: WebSocket connection to remove
            user_id: User identifier
        """
        # Remove from active connections
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)

            # Remove user if no more connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

                # Remove from all rooms
                if user_id in self.user_rooms:
                    for room_id in self.user_rooms[user_id]:
                        if room_id in self.rooms:
                            self.rooms[room_id].discard(user_id)
                            if not self.rooms[room_id]:
                                del self.rooms[room_id]
                    del self.user_rooms[user_id]

        # Remove metadata
        conn_id = f"{user_id}_{id(websocket)}"
        if conn_id in self.connection_metadata:
            del self.connection_metadata[conn_id]

        remaining_conns = len(self.get_all_connections())
        logger.info(
            f"WebSocket disconnected: user={user_id}, " f"remaining_connections={remaining_conns}"
        )

    async def send_personal_message(
        self, message: str, user_id: str, message_type: str = "message"
    ):
        """
        Send message to a specific user (all their connections)

        Args:
            message: Message content
            user_id: Target user identifier
            message_type: Message type for client routing
        """
        if user_id in self.active_connections:
            payload = {
                "type": message_type,
                "data": message,
                "timestamp": datetime.utcnow().isoformat(),
            }

            dead_connections = []
            for connection in self.active_connections[user_id]:
                try:
                    if connection.client_state == WebSocketState.CONNECTED:
                        await connection.send_json(payload)
                        self.stats["messages_sent"] += 1
                    else:
                        dead_connections.append(connection)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    dead_connections.append(connection)

            # Clean up dead connections
            for conn in dead_connections:
                self.disconnect(conn, user_id)

    async def send_json_message(self, data: Dict, user_id: str, message_type: str = "message"):
        """
        Send JSON message to a specific user

        Args:
            data: Message data (dict)
            user_id: Target user identifier
            message_type: Message type for client routing
        """
        payload = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if user_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[user_id]:
                try:
                    if connection.client_state == WebSocketState.CONNECTED:
                        await connection.send_json(payload)
                        self.stats["messages_sent"] += 1
                    else:
                        dead_connections.append(connection)
                except Exception as e:
                    logger.error(f"Error sending JSON to user {user_id}: {e}")
                    dead_connections.append(connection)

            for conn in dead_connections:
                self.disconnect(conn, user_id)

    async def broadcast(
        self,
        message: str,
        message_type: str = "broadcast",
        exclude_user: Optional[str] = None,
    ):
        """
        Broadcast message to all connected users

        Args:
            message: Message content
            message_type: Message type for client routing
            exclude_user: Optional user ID to exclude from broadcast
        """
        payload = {
            "type": message_type,
            "data": message,
            "timestamp": datetime.utcnow().isoformat(),
        }

        for user_id, connections in list(self.active_connections.items()):
            if exclude_user and user_id == exclude_user:
                continue

            dead_connections = []
            for connection in connections:
                try:
                    if connection.client_state == WebSocketState.CONNECTED:
                        await connection.send_json(payload)
                    else:
                        dead_connections.append(connection)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")
                    dead_connections.append(connection)

            for conn in dead_connections:
                self.disconnect(conn, user_id)

        self.stats["broadcasts_sent"] += 1

    def join_room(self, room_id: str, user_id: str):
        """
        Add user to a room

        Args:
            room_id: Room identifier
            user_id: User identifier
        """
        if room_id not in self.rooms:
            self.rooms[room_id] = set()

        self.rooms[room_id].add(user_id)

        # Track user's rooms
        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = set()
        self.user_rooms[user_id].add(room_id)

        logger.debug(f"User {user_id} joined room {room_id}")

    def leave_room(self, room_id: str, user_id: str):
        """
        Remove user from a room

        Args:
            room_id: Room identifier
            user_id: User identifier
        """
        if room_id in self.rooms:
            self.rooms[room_id].discard(user_id)
            if not self.rooms[room_id]:
                del self.rooms[room_id]

        if user_id in self.user_rooms:
            self.user_rooms[user_id].discard(room_id)

        logger.debug(f"User {user_id} left room {room_id}")

    async def broadcast_to_room(
        self,
        room_id: str,
        message: str,
        message_type: str = "room_message",
        exclude_user: Optional[str] = None,
    ):
        """
        Broadcast message to all users in a room

        Args:
            room_id: Room identifier
            message: Message content
            message_type: Message type for client routing
            exclude_user: Optional user ID to exclude from broadcast
        """
        if room_id not in self.rooms:
            logger.warning(f"Room {room_id} does not exist")
            return

        payload = {
            "type": message_type,
            "room_id": room_id,
            "data": message,
            "timestamp": datetime.utcnow().isoformat(),
        }

        for user_id in self.rooms[room_id]:
            if exclude_user and user_id == exclude_user:
                continue

            if user_id in self.active_connections:
                dead_connections = []
                for connection in self.active_connections[user_id]:
                    try:
                        if connection.client_state == WebSocketState.CONNECTED:
                            await connection.send_json(payload)
                        else:
                            dead_connections.append(connection)
                    except Exception as e:
                        logger.error(f"Error sending to room {room_id}, user {user_id}: {e}")
                        dead_connections.append(connection)

                for conn in dead_connections:
                    self.disconnect(conn, user_id)

    def get_all_connections(self) -> List[str]:
        """Get list of all connected user IDs"""
        return list(self.active_connections.keys())

    def get_room_members(self, room_id: str) -> List[str]:
        """Get list of user IDs in a room"""
        return list(self.rooms.get(room_id, set()))

    def get_user_rooms(self, user_id: str) -> List[str]:
        """Get list of rooms a user is in"""
        return list(self.user_rooms.get(user_id, set()))

    def is_user_online(self, user_id: str) -> bool:
        """Check if user has any active connections"""
        return user_id in self.active_connections

    def get_stats(self) -> Dict:
        """Get connection statistics"""
        total_websockets = sum(len(conns) for conns in self.active_connections.values())
        return {
            **self.stats,
            "active_users": len(self.active_connections),
            "total_websockets": total_websockets,
            "active_rooms": len(self.rooms),
        }


# Global connection manager instance
manager = ConnectionManager()
