"""routers/websocket.py — WebSocket endpoints for real-time features."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import verify_ws_token
from database import get_db
from services.notification_service import manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/notifications/{userId}")
async def initNotificationSocket(
    websocket: WebSocket,
    userId: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Persistent WebSocket for per-user notification delivery."""
    user = await verify_ws_token(token, db)
    if not user:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, userId)
    try:
        while True:
            # Keep connection alive; client sends pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, userId)


@router.websocket("/ws/job-alerts/{workerId}")
async def initJobAlertSocket(
    websocket: WebSocket,
    workerId: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Persistent WebSocket for real-time job alerts pushed to workers."""
    user = await verify_ws_token(token, db)
    if not user:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, workerId)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, workerId)
