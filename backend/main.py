"""Entry point for New_Line backend."""

import asyncio
import sys

from hyperliquid_client import HyperliquidClient
from logger import get_logger
from order_manager import OrderManager
from stats_reporter import StatsReporter
from ws_server import MiniAppServer

log = get_logger(__name__)


async def check_open_orders(
    manager: OrderManager,
    client: HyperliquidClient,
) -> None:
    """Periodically verify active orders are still open.

    Removes orders no longer in exchange open list.
    """
    from config import ORDERS_CHECK_INTERVAL_SECONDS
    from models import RemovalReason

    while True:
        await asyncio.sleep(ORDERS_CHECK_INTERVAL_SECONDS)
        active_keys = manager.active_keys()
        if not active_keys:
            continue
        addrs = {
            order.addr
            for order in manager.get_active()
        }
        open_oids: set[int] = set()
        for addr in addrs:
            try:
                raw_orders = await client.fetch_open_orders(addr)
                for ro in raw_orders:
                    oid = ro.get("oid")
                    if oid is not None:
                        open_oids.add(int(oid))
            except Exception as exc:
                log.warning("fetch_open_orders failed: %s", exc)
        for key in list(active_keys):
            parts = key.split(":")
            if len(parts) >= 2:
                try:
                    oid = int(parts[1])
                    if oid not in open_oids:
                        manager.remove_order(
                            key, RemovalReason.UNKNOWN
                        )
                except ValueError:
                    pass


async def main() -> None:
    """Bootstrap and run all services concurrently."""
    log.info("New_Line backend starting...")

    manager = OrderManager()
    server = MiniAppServer(manager)
    hl_client = HyperliquidClient(manager)
    reporter = StatsReporter(manager, server)

    try:
        await asyncio.gather(
            server.run(),
            hl_client.run(),
            reporter.run(),
            check_open_orders(manager, hl_client),
        )
    except KeyboardInterrupt:
        log.info("Shutting down...")
        await hl_client.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Bye!")
        sys.exit(0)
