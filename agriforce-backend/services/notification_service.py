"""notification_service.py — WebSocket ConnectionManager + DB Notification helpers."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import WebSocket
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.notifications import Notification, NotificationType


class ConnectionManager:
    """Manages active WebSocket connections keyed by user/worker ID."""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        self.active_connections.setdefault(user_id, []).append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        conns = self.active_connections.get(user_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self.active_connections.pop(user_id, None)

    async def send_to_user(self, user_id: str, message: dict) -> None:
        for ws in list(self.active_connections.get(user_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                self.active_connections[user_id].remove(ws)

    async def broadcast(self, message: dict) -> None:
        for user_id, connections in list(self.active_connections.items()):
            for ws in list(connections):
                try:
                    await ws.send_json(message)
                except Exception:
                    connections.remove(ws)


# Singleton used by all routers
manager = ConnectionManager()


async def createNotification(
    db: AsyncSession,
    user_id: str,
    message: str,
    notif_type: NotificationType,
) -> Notification:
    """Insert notification record AND push via WebSocket."""
    notif = Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        message=message,
        type=notif_type,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)

    # Push real-time update
    unread_count = await getUnreadCount(db, str(user_id))
    await manager.send_to_user(
        str(user_id),
        {"count": unread_count, "message": message, "type": notif_type.value},
    )
    return notif


async def getUnreadCount(db: AsyncSession, user_id: str) -> int:
    result = await db.execute(
        select(func.count()).where(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
        )
    )
    return result.scalar() or 0
