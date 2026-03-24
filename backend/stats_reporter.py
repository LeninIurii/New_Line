"""Periodic stats logging for New_Line project."""

import asyncio

from config import STATS_INTERVAL_SECONDS
from logger import get_logger
from order_manager import OrderManager
from ws_server import MiniAppServer

log = get_logger(__name__)


class StatsReporter:
    """Logs stats every N seconds and broadcasts updates."""

    def __init__(
        self,
        manager: OrderManager,
        server: MiniAppServer,
    ) -> None:
        """Initialize reporter.

        Args:
            manager: Shared order manager.
            server: Mini App WS server for broadcasts.
        """
        self._manager = manager
        self._server = server

    async def run(self) -> None:
        """Run periodic reporting loop forever."""
        while True:
            await asyncio.sleep(STATS_INTERVAL_SECONDS)
            await self._report()
            await self._server.broadcast()
            self._manager.reset_period_stats()

    async def _report(self) -> None:
        """Log full stats snapshot to stdout."""
        s = self._manager.get_stats()
        new_orders = s.new_in_period
        removed_orders = s.removed_in_period

        log.info("=" * 50)
        log.info("[STATS] Received:    %d", s.total_received)
        log.info("[STATS] Passed:      %d", s.passed_filter)
        log.info("[STATS] Failed:      %d", s.failed_filter)
        log.info("[STATS] Active now:  %d", s.active_count)
        log.info(
            "[STATS] Removed: filled=%d canceled=%d unknown=%d",
            s.removed_filled,
            s.removed_canceled,
            s.removed_unknown,
        )
        log.info("-" * 50)
        self._log_new_orders(new_orders)
        self._log_removed_orders(removed_orders)
        log.info("=" * 50)

    def _log_new_orders(self, orders: list) -> None:
        """Log orders that appeared in this period."""
        if not orders:
            log.info("[NEW] No new orders this period.")
            return
        for o in orders:
            log.info(
                "[NEW] + token=%s side=%s px=%.4f sz=%.4f "
                "usdc=%.2f hash=%s",
                o.token, o.side, o.px, o.sz, o.usdc, o.tx_hash,
            )

    def _log_removed_orders(self, records: list) -> None:
        """Log orders that disappeared in this period."""
        if not records:
            log.info("[REMOVED] No orders removed this period.")
            return
        for rec in records:
            o = rec.order
            log.info(
                "[REMOVED] - token=%s side=%s px=%.4f "
                "hash=%s reason=%s",
                o.token, o.side, o.px, o.tx_hash, rec.reason,
            )
