"""Order filtering logic for New_Line project."""

from datetime import datetime
from typing import Optional

from config import PRICE_DEVIATION_THRESHOLD, TOKENS_CONFIG
from logger import get_logger
from models import LimitOrder

log = get_logger(__name__)


def normalize_order(raw: dict) -> Optional[LimitOrder]:
    """Normalize raw Hyperliquid order to LimitOrder.

    Args:
        raw: Raw order dict from Hyperliquid WS.

    Returns:
        LimitOrder or None if fields are missing.
    """
    try:
        token = raw.get("coin", "").replace("-PERP", "")
        px = float(raw.get("limitPx", 0))
        sz = float(raw.get("sz", 0))
        addr = raw.get("user", "")
        side_raw = raw.get("side", "")
        side = "buy" if side_raw == "B" else "sell"
        tx_hash = raw.get("hash", None)
        oid = raw.get("oid", None)
        return LimitOrder(
            token=token,
            px=px,
            sz=sz,
            usdc=round(px * sz, 2),
            addr=addr,
            side=side,
            time=datetime.utcnow(),
            tx_hash=tx_hash,
            oid=oid,
        )
    except Exception as exc:
        log.warning("normalize_order failed: %s | raw=%s", exc, raw)
        return None


def passes_token_filter(order: LimitOrder) -> bool:
    """Check if token is in TOKENS_CONFIG."""
    return order.token in TOKENS_CONFIG


def passes_volume_filter(order: LimitOrder) -> bool:
    """Check if usdc volume meets minimum threshold."""
    min_usdc = TOKENS_CONFIG[order.token]["min_usdc"]
    return order.usdc >= min_usdc


def passes_deviation_filter(
    order: LimitOrder,
    mid_price: float,
) -> bool:
    """Check if price deviates >= 5% from mid_price.

    Args:
        order: Normalized limit order.
        mid_price: Current mid market price for token.

    Returns:
        True if deviation is sufficient.
    """
    if mid_price <= 0:
        return False
    deviation = abs(order.px - mid_price) / mid_price
    return deviation >= PRICE_DEVIATION_THRESHOLD


def is_valid_order(
    order: LimitOrder,
    mid_price: float,
) -> bool:
    """Run all three filters. Log reason if rejected."""
    if not passes_token_filter(order):
        log.debug("REJECT token=%s not in config", order.token)
        return False
    if not passes_volume_filter(order):
        log.debug(
            "REJECT token=%s usdc=%.2f < min",
            order.token,
            order.usdc,
        )
        return False
    if not passes_deviation_filter(order, mid_price):
        log.debug(
            "REJECT token=%s deviation too small mid=%.4f px=%.4f",
            order.token,
            mid_price,
            order.px,
        )
        return False
    return True
