"""Centralized logging configuration for iCloud Photo Sync Tool."""

import sys
import logging
from pathlib import Path
from typing import Optional


# Global logger instance
_logger: Optional[logging.Logger] = None


def setup_logging(log_level: int) -> None:
    """Set up logging configuration.

    Args:
        config: Application configuration
    """
    global _logger

    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/icloud-sync.log', mode='a', encoding='utf-8'),
        ]
    )

    # Set up the global logger
    _logger = logging.getLogger("icloud_photo_sync")


def get_logger() -> logging.Logger:
    """Get the global logger instance.

    Returns:
        The configured logger instance

    Raises:
        RuntimeError: If logging has not been set up yet
    """
    if _logger is None:
        raise RuntimeError("Logging has not been set up. Call setup_logging() first.")
    return _logger
