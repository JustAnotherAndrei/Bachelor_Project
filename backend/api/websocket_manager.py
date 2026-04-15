"""
WebSocket session manager for real-time Alice-Bob BB84 protocol streaming.

Each session streams individual qubit exchange events to the connected client.
"""

import asyncio
import json
from fastapi import WebSocket
from typing import Dict


class SessionManager:
    """Manages active WebSocket sessions keyed by session_id."""

    def __init__(self):
        self.active_sessions: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_sessions[session_id] = websocket

    def disconnect(self, session_id: str):
        self.active_sessions.pop(session_id, None)

    async def send_event(self, session_id: str, event: dict):
        ws = self.active_sessions.get(session_id)
        if ws:
            await ws.send_text(json.dumps(event))


session_manager = SessionManager()
