"""Active order list manager for New_Line project."""

from datetime import datetime
from typing import Callable, Coroutine, Optional

from logger import get_logger
from models import LimitOrder, OrderHistory, RemovalReason, Stats

log = get_logger(__name__)


class OrderManager:
    """Manages active limit orders and removal history."""

    def __init__(
        self,
        on_update: Optional[Callable[[], Coroutine]] = None,
    ) -> None:
        """Initialize manager with optional update callback.

        Args:
            on_update: Async callback called on list change.
        """
        self._active: dict[str, LimitOrder] = {}
        self._history: list[OrderHistory] = []
        self._stats = Stats()
        self._on_update = on_update

    def get_active(self) -> list[LimitOrder]:
        """Return snapshot of active orders."""
        return list(self._active.values())

    def get_history(self) -> list[OrderHistory]:
        """Return full removal history."""
        return list(self._history)

    def get_stats(self) -> Stats:
        """Return current stats snapshot."""
        return self._stats

    def add_order(self, order: LimitOrder) -> bool:
        """Add order to active list if not already present.

        Returns:
            True if added, False if duplicate.
        """
        key = self._order_key(order)
        if key in self._active:
            return False
        self._active[key] = order
        self._stats.active_count = len(self._active)
        self._stats.new_in_period.append(order)
        log.info(
            "NEW order token=%s side=%s px=%.4f sz=%.4f "
            "usdc=%.2f hash=%s",
            order.token, order.side, order.px,
            order.sz, order.usdc, order.tx_hash,
        )
        return True

    def remove_order(
        self,
        key: str,
        reason: RemovalReason,
    ) -> Optional[OrderHistory]:
        """Remove order and record history entry.

        Args:
            key: Order identifier string.
            reason: Why the order was removed.

        Returns:
            OrderHistory record or None if not found.
        """
        order = self._active.pop(key, None)
        if order is None:
            return None
        record = OrderHistory(
            order=order,
            appeared_at=order.time,
            disappeared_at=datetime.utcnow(),
            reason=reason,
        )
        self._history.append(record)
        self._stats.active_count = len(self._active)
        self._stats.removed_in_period.append(record)
        self._update_removal_stats(reason)
        log.info(
            "REMOVED order token=%s side=%s px=%.4f "
            "hash=%s reason=%s",
            order.token, order.side, order.px,
            order.tx_hash, reason,
        )
        return record

    def reset_period_stats(self) -> None:
        """Reset per-interval counters."""
        self._stats.new_in_period = []
        self._stats.removed_in_period = []
        self._stats.total_received = 0
        self._stats.passed_filter = 0
        self._stats.failed_filter = 0

    def increment_received(self) -> None:
        """Increment total received counter."""
        self._stats.total_received += 1

    def increment_passed(self) -> None:
        """Increment passed filter counter."""
        self._stats.passed_filter += 1

    def increment_failed(self) -> None:
        """Increment failed filter counter."""
        self._stats.failed_filter += 1

    def has_active(self, key: str) -> bool:
        """Check if key exists in active orders."""
        return key in self._active

    def active_keys(self) -> set[str]:
        """Return set of active order keys."""
        return set(self._active.keys())

    @staticmethod
    def make_key(order: LimitOrder) -> str:
        """Generate stable key for a LimitOrder."""
        return OrderManager._order_key_from(order)

    def _order_key(self, order: LimitOrder) -> str:
        return self._order_key_from(order)

    @staticmethod
    def _order_key_from(order: LimitOrder) -> str:
        if order.oid is not None:
            return f"{order.addr}:{order.oid}"
        return f"{order.addr}:{order.token}:{order.px}:{order.sz}"

    def _update_removal_stats(self, reason: RemovalReason) -> None:
        if reason == RemovalReason.FILLED:
            self._stats.removed_filled += 1
        elif reason == RemovalReason.CANCELED:
            self._stats.removed_canceled += 1
        else:
            self._stats.removed_unknown += 1
