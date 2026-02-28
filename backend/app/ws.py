"""WebSocket ConnectionManager — per-org real-time event broadcasting."""
import json
import logging
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections keyed by org_id."""

    def __init__(self):
        self._connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, org_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        if org_id not in self._connections:
            self._connections[org_id] = []
        self._connections[org_id].append(websocket)
        logger.info("WS connected: org_id=%d, total=%d", org_id, len(self._connections[org_id]))

    def disconnect(self, org_id: int, websocket: WebSocket) -> None:
        if org_id in self._connections:
            try:
                self._connections[org_id].remove(websocket)
            except ValueError:
                pass
            if not self._connections[org_id]:
                del self._connections[org_id]
        logger.info("WS disconnected: org_id=%d", org_id)

    async def send_to_org(self, org_id: int, event: str, data: dict) -> int:
        """Send event to all connections for org_id. Returns number of recipients."""
        if org_id not in self._connections:
            return 0
        message = json.dumps({"event": event, "data": data})
        dead = []
        sent = 0
        for ws in self._connections[org_id]:
            try:
                await ws.send_text(message)
                sent += 1
            except Exception as e:
                logger.warning("WS send failed, removing dead connection: %s", e)
                dead.append(ws)
        for ws in dead:
            try:
                self._connections[org_id].remove(ws)
            except ValueError:
                pass
        return sent

    def connection_count(self, org_id: int) -> int:
        return len(self._connections.get(org_id, []))


# Singleton instance — imported by main.py and routers
manager = ConnectionManager()


async def notify_org(org_id: int, event: str, data: dict) -> None:
    """Convenience helper: send event to org, log if no connections."""
    count = await manager.send_to_org(org_id, event, data)
    if count == 0:
        logger.debug("notify_org: no WS connections for org_id=%d (event=%s)", org_id, event)
