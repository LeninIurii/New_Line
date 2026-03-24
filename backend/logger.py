"""Centralized logger for New_Line project."""

import logging
import sys
from typing import Optional


LOG_FORMAT: str = (
    "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s"
)
DATE_FORMAT: str = "%H:%M:%S"


def get_logger(
    name: str,
    level: Optional[int] = None,
) -> logging.Logger:
    """Create and configure a named logger.

    Args:
        name: Logger name (usually __name__).
        level: Logging level. Defaults to INFO.

    Returns:
        Configured Logger instance.
    """
    if level is None:
        level = logging.INFO

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    )
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False

    return logger
