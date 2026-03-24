"""Hyperliquid WebSocket and REST client."""

import asyncio
import json
from typing import Callable, Coroutine, Optional

import aiohttp
import websockets

from config import HL_REST_URL, HL_WS_URL, TOKENS_CONFIG
from logger import get_logger
from models import RemovalReason
from order_manager import OrderManager

log = get_logger(__name__)

Handler = Callable[[dict], Coroutine]


class HyperliquidClient:
    """Connects to Hyperliquid WS and REST API."""

    def __init__(self, manager: OrderManager) -> None:
        """Initialize with shared OrderManager."""
        self._manager = manager
        self._mid_prices: dict[str, float] = {}
        self._running = False

    async def run(self) -> None:
        """Start WS listener with auto-reconnect."""
        self._running = True
        while self._running:
            try:
                await self._connect()
            except Exception as exc:
                log.warning("WS disconnected: %s. Reconnecting...", exc)
                await asyncio.sleep(3)

    async def stop(self) -> None:
        """Stop the client loop."""
        self._running = False

    def get_mid_price(self, token: str) -> float:
        """Return latest mid price for token."""
        return self._mid_prices.get(token, 0.0)

    async def fetch_open_orders(self, addr: str) -> list[dict]:
        """Fetch open orders from REST API.

        Args:
            addr: Wallet address to query.

        Returns:
            List of raw open order dicts.
        """
        payload = {"type": "openOrders", "user": addr}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                HL_REST_URL, json=payload
            ) as resp:
                data = await resp.json()
                return data if isinstance(data, list) else []

    async def _connect(self) -> None:
        """Open WS connection and subscribe to channels."""
        async with websockets.connect(HL_WS_URL) as ws:
            log.info("Connected to Hyperliquid WS")
            await self._subscribe_all_mids(ws)
            await self._subscribe_order_updates(ws)
            async for raw in ws:
                await self._handle_message(raw)

    async def _subscribe_all_mids(self, ws) -> None:
        """Subscribe to allMids price feed."""
        msg = {"method": "subscribe", "subscription": {"type": "allMids"}}
        await ws.send(json.dumps(msg))

    async def _subscribe_order_updates(self, ws) -> None:
        """Subscribe to orderUpdates for tracked addresses."""
        for token in TOKENS_CONFIG:
            msg = {
                "method": "subscribe",
                "subscription": {"type": "orderUpdates", "coin": token},
            }
            await ws.send(json.dumps(msg))

    async def _handle_message(self, raw: str) -> None:
        """Route incoming WS message to correct handler."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return
        channel = data.get("channel", "")
        if channel == "allMids":
            self._update_mids(data.get("data", {}))
        elif channel == "orderUpdates":
            await self._handle_order_update(data.get("data", []))

    def _update_mids(self, mids: dict) -> None:
        """Update mid prices from allMids payload."""
        for coin, price in mids.items():
            token = coin.replace("-PERP", "")
            try:
                self._mid_prices[token] = float(price)
            except (ValueError, TypeError):
                pass

    async def _handle_order_update(self, updates: list) -> None:
        """Process orderUpdates and remove stale orders."""
        from filters import normalize_order, is_valid_order
        for update in updates:
            status = update.get("status", "")
            order_data = update.get("order", update)
            order = normalize_order(order_data)
            if order is None:
                continue
            from order_manager import OrderManager as OM
            key = OM.make_key(order)
            if status == "filled":
                self._manager.remove_order(key, RemovalReason.FILLED)
            elif status == "canceled":
                self._manager.remove_order(key, RemovalReason.CANCELED)
            elif status == "open":
                mid = self.get_mid_price(order.token)
                self._manager.increment_received()
                if is_valid_order(order, mid):
                    self._manager.increment_passed()
                    self._manager.add_order(order)
                else:
                    self._manager.increment_failed()
