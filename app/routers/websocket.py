import asyncio
import os
from typing import Annotated

from fastapi import (APIRouter, Depends, Query, WebSocket, WebSocketDisconnect,
                     WebSocketException, status)
from fastapi.logger import logger

from app.core.connection_manager import manager
from app.core.token_manager import decode_access_token
from app.services.occupancy_detection import get_occupancy

router = APIRouter()

async def get_token_from_query(websocket: WebSocket, token: Annotated[str | None, Query()] = None):
    if token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return token

@router.websocket("/ws")
async def websocket_endpoint(socket: WebSocket, token: Annotated[str, Depends(get_token_from_query)]):
    await manager.connect(socket)
    user = await decode_access_token(token)

    if user is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    try:
        occupancy = await get_occupancy()
        manager.send_personal_message(occupancy, socket)
        while True:
            data = await socket.receive_text()
            await manager.broadcast(f"Client #{user.email} says: {data}")
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(socket)
        # await manager.broadcast(f"Client #{username} left the chat")
    except Exception as e:
        manager.disconnect(socket)
        logger.error(f"Error during websocket endpoint: {e}")
