#!/usr/bin/env python3
import pytest
"""
Test script for Pushover notification configuration.

This script allows you to test your Pushover notification setup
without running the full iPhoto Downloader.
"""

from iphoto_downloader.logger import setup_logging
from auth2fa.pushover_service import PushoverService as PushoverNotificationService
from iphoto_downloader.config import KeyringConfig, get_config
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


@pytest.mark.manual
def test_pushover_config():
    """Test Pushover notification configuration."""
    # Setup logging
    try:
        # Load configuration
        config = get_config()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("💡 Please check your .env file and ensure all required settings are configured.")
        sys.exit(1)

    setup_logging(config.get_log_level())
    logger = logging.getLogger(__name__)

    # Load configuration
    logger.info("Loading configuration...")
    config = KeyringConfig()

    # Check if Pushover is enabled
    if not config.enable_pushover:
        logger.warning(
            "Pushover notifications are disabled. Set ENABLE_PUSHOVER=true in your .env file.")
        return False

    # Get Pushover configuration
    pushover_config = config.get_pushover_config()
    if not pushover_config:
        msg = ("Pushover configuration is incomplete. Check PUSHOVER_API_TOKEN and "
               "PUSHOVER_USER_KEY in your .env file.")
        raise ValueError(msg)

    logger.info("Pushover configuration found:")
    logger.info(f"  API Token: {'*' * len(pushover_config.api_token)}")
    logger.info(f"  User Key: {'*' * len(pushover_config.user_key)}")
    logger.info(f"  Device: {pushover_config.device or 'All devices'}")

    # Create notification service
    notification_service = PushoverNotificationService(pushover_config)

    # Test connection
    logger.info("Testing Pushover connection...")
    if notification_service.test_connection():
        logger.info("✅ Pushover test notification sent successfully!")
        logger.info("Check your Pushover app to verify you received the test notification.")
        return True
    else:
        logger.error("❌ Failed to send Pushover test notification.")
        logger.error("Check your API token and user key in the .env file.")
        return False


def main():
    """Main function."""
    print("iPhoto Downloader - Pushover Configuration Test")
    print("=" * 50)
    print()

    if test_pushover_config():
        print("\n✅ Pushover configuration test completed successfully!")
        print("Your notification setup is ready for 2FA authentication.")


if __name__ == "__main__":
    main()
