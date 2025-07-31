"""Main entry point for iPhoto Downloader Tool."""

import argparse
import codecs
import contextlib
import io
import os
import re
import sys

from auth2fa.pushover_service import PushoverService
from iphoto_downloader.config import BaseConfig, get_config
from iphoto_downloader.continuous_runner import run_execution_mode
from iphoto_downloader.delivery_artifacts import DeliveryArtifactsManager
from iphoto_downloader.instance_manager import InstanceManager
from iphoto_downloader.logger import get_logger, setup_logging
from iphoto_downloader.manage_credentials import (
    icloud_store_credentials,
    pushover_store_credentials,
)
from iphoto_downloader.version import get_version


def main() -> None:
    """Main entry point for the application."""

    # Handle command line arguments before any setup
    parser = argparse.ArgumentParser(
        description="iPhoto Downloader Tool - Sync photos from iCloud to local storage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  iphoto_downloader              Run the sync process
  iphoto_downloader --help       Show this help message

For detailed configuration and usage instructions, visit:
https://github.com/HenningUe/iphoto-downloader/blob/main/USER-GUIDE.md
        """.strip(),
    )

    parser.add_argument(
        "--version", action="version", version=f"iPhoto Downloader Tool v{get_version()}"
    )

    # Parse arguments - this will handle --help and --version automatically
    parser.parse_args()

    # Set UTF-8 encoding for stdout/stderr to handle Unicode characters on Windows
    # This is particularly important for PyInstaller executables
    if sys.platform.startswith("win"):
        # Set environment variable for proper UTF-8 handling
        os.environ["PYTHONIOENCODING"] = "utf-8"
        # Replace stdout and stderr with UTF-8 writers
        try:
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
            sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")
        except Exception:
            # If buffer attribute doesn't exist, create new streams
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="strict")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="strict")

    version = get_version()
    print(f"🌟 iPhoto Downloader Tool v{version}")
    print("=" * 60)
    print(" ")
    print("For help, visit: https://github.com/HenningUe/iphoto-downloader/blob/main/USER-GUIDE.md")

    config = None
    logger = None

    def safe_input(prompt: str = ""):
        # Only prompt if running interactively
        if sys.stdin.isatty():
            with contextlib.suppress(EOFError):
                input(prompt)

    try:
        # Get initial config to determine operating mode
        config = get_config()

        # Set up logging with config (must be before DeliveryArtifactsManager)
        setup_logging(config.get_log_level())
        logger = get_logger()

        # Handle delivery artifacts for 'Delivered' mode
        delivery_manager = DeliveryArtifactsManager()
        should_continue = delivery_manager.handle_delivered_mode_startup()

        if not should_continue:
            # First-time setup completed, user needs to configure settings
            print(
                "\n🎯 Setup complete! Please run the application again after configuring settings."
            )
            safe_input("Press Enter to exit...")
            sys.exit(0)

        # Check multi-instance control before proceeding
        instance_manager = InstanceManager(config.allow_multi_instance)

        # Enforce single instance if required (will exit if another instance is running)
        with instance_manager.instance_context():
            if not config.icloud_has_stored_credentials():
                print("🔑 iCloud credentials not found in keyring.")
                icloud_store_credentials()

            if config.enable_pushover and not config.pushover_has_stored_credentials():
                print("🔑 Pushover credentials not found in keyring.")
                pushover_store_credentials()

            config.validate()

            logger.info("Starting iPhoto Downloader Tool")
            logger.info(f"Configuration: {config}")
            logger.info(f"Execution mode: {config.execution_mode}")
            logger.info(f"Operating mode: {config.operating_mode}")
            logger.info(f"Multi-instance allowed: {config.allow_multi_instance}")

            # Run in the configured execution mode
            success = run_execution_mode(config)

            if success:
                logger.info("✅ Application completed successfully")
                print("\n✅ Application completed successfully!")
            else:
                logger.error("❌ Application failed")
                print("\n❌ Application failed!")
                safe_input("Press Enter to exit...")
                sys.exit(1)

    except KeyboardInterrupt:
        # Handle global keyboard interrupt
        print("\n🛑 Application interrupted by user")
        safe_input("Press Enter to exit...")
        sys.exit(130)
    except Exception as e:
        # Global exception handler - catch any unhandled exceptions
        error_message = f"Critical application error: {e}"
        print(f"❌ {error_message}")

        # Log the error if possible
        if logger:
            logger.critical(f"Unhandled exception in main: {e}", exc_info=True)

        # Send error notification via Pushover if configured
        if config:
            try:
                sanitized_message = sanitize_error_message(e)
                send_error_notification(config, sanitized_message, "Critical Error")
            except Exception as notification_error:
                # Don't let notification failures prevent proper error handling
                if logger:
                    logger.error(f"Failed to send error notification: {notification_error}")

        # Ensure graceful application shutdown
        safe_input("Press Enter to exit...")
        sys.exit(1)


def send_error_notification(
    config: BaseConfig, error_message: str, error_type: str = "Application Error"
) -> None:
    """
    Send an error notification via Pushover if configured.

    Args:
        config: Application configuration
        error_message: Error message to send (sensitive data already filtered)
        error_type: Type of error for the notification title
    """
    try:
        if not config.enable_pushover:
            return

        pushover_config = config.get_pushover_config()
        if not pushover_config:
            return

        pushover_service = PushoverService(pushover_config)
        pushover_service.send_error_notification(error_message, error_type)

    except Exception as e:
        # Don't let error notification failures crash the application
        # Just log it if we have a logger available
        try:
            logger = get_logger()
            logger.error(f"Failed to send error notification: {e}")
        except Exception:
            # If even logging fails, just ignore it to prevent recursive errors
            pass


def sanitize_error_message(error: Exception) -> str:
    """
    Sanitize error message by removing potentially sensitive information.

    Args:
        error: The exception to sanitize

    Returns:
        Sanitized error message safe for notifications
    """
    error_str = str(error)
    error_type = type(error).__name__

    # Remove common sensitive patterns
    sensitive_patterns = [
        # Passwords, tokens, keys
        r"password[=:]\s*[^\s]+",
        r"token[=:]\s*[^\s]+",
        r"key[=:]\s*[^\s]+",
        r"secret[=:]\s*[^\s]+",
        # File paths that might contain usernames
        r"[cC]:\\[uU]sers\\[^\\]+",
        r"/[hH]ome/[^/]+",
        # Email addresses and usernames in URLs
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    ]

    sanitized = error_str
    for pattern in sensitive_patterns:
        sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)

    # Limit message length and add error type
    max_length = 500
    if len(sanitized) > max_length:
        sanitized = sanitized[: max_length - 3] + "..."

    return f"{error_type}: {sanitized}"


if __name__ == "__main__":
    main()
