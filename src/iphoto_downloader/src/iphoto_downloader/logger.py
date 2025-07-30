"""Centralized logging configuration for iPhoto Downloader Tool."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import get_app_data_folder_path

# Global logger instance
_logger: logging.Logger | None = None


def setup_logging(log_level: int = logging.INFO) -> None:
    """Set up logging configuration.

    Args:
        config: Application configuration
    """

    # Create logs directory if it doesn't exist
    get_log_dir_path().mkdir(exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            RotatingFileHandler(
                get_log_dir_path() / "icloud-sync.log",
                mode="a",
                encoding="utf-8",
                maxBytes=50 * 1024,  # 50KB
                backupCount=5,
            ),
        ],
    )

    # Set up the global logger
    _logger = logging.getLogger("iphoto_downloader")


def get_log_dir_path() -> Path:
    """Get the path to the logs directory.

    Returns:
        Path to the logs directory
    """
    base_dir = get_app_data_folder_path()
    return base_dir / "logs" if base_dir else Path("logs")


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
