"""Configuration for New_Line project."""

from typing import TypedDict


class TokenConfig(TypedDict):
    """Per-token filter settings."""

    min_usdc: float


# Tokens to monitor with minimum volume thresholds
TOKENS_CONFIG: dict[str, TokenConfig] = {
    "BTC": {"min_usdc": 50_000},
    "ETH": {"min_usdc": 20_000},
    "SOL": {"min_usdc": 10_000},
    "ARB": {"min_usdc": 5_000},
    "OP": {"min_usdc": 5_000},
}

# Minimum price deviation from mid-price (5%)
PRICE_DEVIATION_THRESHOLD: float = 0.05

# Stats logging interval in seconds
STATS_INTERVAL_SECONDS: int = 5

# Open orders check interval in seconds
ORDERS_CHECK_INTERVAL_SECONDS: int = 5

# WebSocket server port for Mini App
WS_PORT: int = 8765

# Hyperliquid WebSocket endpoint
HL_WS_URL: str = "wss://api.hyperliquid.xyz/ws"

# Hyperliquid REST API endpoint
HL_REST_URL: str = "https://api.hyperliquid.xyz/info"
