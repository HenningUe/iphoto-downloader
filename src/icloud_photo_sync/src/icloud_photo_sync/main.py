"""Main entry point for iCloud Photo Sync Tool."""

import sys

from auth2fa.pushover_service import PushoverService
from icloud_photo_sync.config import get_config, BaseConfig
from icloud_photo_sync.continuous_runner import run_execution_mode
from icloud_photo_sync.logger import setup_logging, get_logger
from icloud_photo_sync import manage_credentials


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
        r'password[=:]\s*[^\s]+',
        r'token[=:]\s*[^\s]+',
        r'key[=:]\s*[^\s]+',
        r'secret[=:]\s*[^\s]+',
        # File paths that might contain usernames
        r'[cC]:\\[uU]sers\\[^\\]+',
        r'/[hH]ome/[^/]+',
        # Email addresses and usernames in URLs
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    ]

    import re
    sanitized = error_str
    for pattern in sensitive_patterns:
        sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)

    # Limit message length and add error type
    max_length = 500
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length - 3] + "..."

    return f"{error_type}: {sanitized}"


def main() -> None:
    """Main entry point for the application."""
    print("🌟 iCloud Photo Sync Tool v0.1.0")
    print("==================================")

    config = None
    logger = None

    try:
        config = get_config()

        if not config.icloud_has_stored_credentials():
            print("🔑 iCloud credentials not found in keyring.")
            manage_credentials.icloud_store_credentials()

        if config.enable_pushover and not config.pushover_has_stored_credentials():
            print("🔑 Pushover credentials not found in keyring.")
            manage_credentials.pushover_store_credentials()

        config.validate()

        # Set up logging with config
        setup_logging(config.get_log_level())
        logger = get_logger()

        logger.info("Starting iCloud Photo Sync Tool")
        logger.info(f"Configuration: {config}")
        logger.info(f"Execution mode: {config.execution_mode}")

        # Run in the configured execution mode
        success = run_execution_mode(config)

        if success:
            logger.info("✅ Application completed successfully")
            print("\n✅ Application completed successfully!")
        else:
            logger.error("❌ Application failed")
            print("\n❌ Application failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        # Handle global keyboard interrupt
        print("\n🛑 Application interrupted by user")
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
        sys.exit(1)


if __name__ == "__main__":
    main()
