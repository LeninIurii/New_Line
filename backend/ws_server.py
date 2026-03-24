"""WebSocket server that pushes data to Mini App."""

import asyncio
import json
from typing import Set

import websockets
from websockets.server import WebSocketServerProtocol

from config import WS_PORT
from logger import get_logger
from order_manager import OrderManager

log = get_logger(__name__)


class MiniAppServer:
    """WebSocket server for Telegram Mini App clients."""

    def __init__(self, manager: OrderManager) -> None:
        """Initialize with shared OrderManager.

        Args:
            manager: Shared active order manager.
        """
        self._manager = manager
        self._clients: Set[WebSocketServerProtocol] = set()

    async def run(self) -> None:
        """Start WebSocket server on configured port."""
        log.info("Mini App WS server starting on port %d", WS_PORT)
        async with websockets.serve(self._handler, "0.0.0.0", WS_PORT):
            await asyncio.Future()

    async def broadcast(self) -> None:
        """Send current state to all connected clients."""
        if not self._clients:
            return
        payload = self._build_payload()
        msg = json.dumps(payload)
        dead: Set[WebSocketServerProtocol] = set()
        for client in self._clients:
            try:
                await client.send(msg)
            except Exception:
                dead.add(client)
        self._clients -= dead

    async def _handler(
        self,
        ws: WebSocketServerProtocol,
    ) -> None:
        """Handle new Mini App client connection."""
        self._clients.add(ws)
        addr = ws.remote_address
        log.info("Mini App client connected: %s", addr)
        try:
            await ws.send(json.dumps(self._build_payload()))
            async for _ in ws:
                pass
        except Exception as exc:
            log.debug("Client %s disconnected: %s", addr, exc)
        finally:
            self._clients.discard(ws)
            log.info("Mini App client disconnected: %s", addr)

    def _build_payload(self) -> dict:
        """Build JSON payload from current manager state."""
        active = self._manager.get_active()
        history = self._manager.get_history()
        stats = self._manager.get_stats()
        return {
            "type": "state",
            "active": [o.to_dict() for o in active],
            "history": [h.to_dict() for h in history[-50:]],
            "stats": {
                "active_count": stats.active_count,
                "removed_filled": stats.removed_filled,
                "removed_canceled": stats.removed_canceled,
                "removed_unknown": stats.removed_unknown,
            },
        }

    def client_count(self) -> int:
        """Return number of connected clients."""
        return len(self._clients)
