"""Data models for New_Line project."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Literal, Optional


class RemovalReason(StrEnum):
    """Reason why a limit order was removed."""

    FILLED = "filled"
    CANCELED = "canceled"
    UNKNOWN = "unknown"


@dataclass
class LimitOrder:
    """Active limit order displayed in Mini App."""

    token: str
    px: float
    sz: float
    usdc: float
    addr: str
    side: Literal["buy", "sell"]
    time: datetime
    tx_hash: Optional[str] = None
    oid: Optional[int] = None

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "token": self.token,
            "px": self.px,
            "sz": self.sz,
            "usdc": self.usdc,
            "addr": self.addr,
            "side": self.side,
            "time": self.time.isoformat(),
            "tx_hash": self.tx_hash,
            "oid": self.oid,
        }


@dataclass
class OrderHistory:
    """Record of a removed limit order."""

    order: LimitOrder
    appeared_at: datetime
    disappeared_at: datetime
    reason: RemovalReason

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "order": self.order.to_dict(),
            "appeared_at": self.appeared_at.isoformat(),
            "disappeared_at": self.disappeared_at.isoformat(),
            "reason": self.reason,
        }


@dataclass
class Stats:
    """Stats snapshot for periodic reporting."""

    total_received: int = 0
    passed_filter: int = 0
    failed_filter: int = 0
    active_count: int = 0
    removed_filled: int = 0
    removed_canceled: int = 0
    removed_unknown: int = 0
    new_in_period: list = field(default_factory=list)
    removed_in_period: list = field(default_factory=list)
