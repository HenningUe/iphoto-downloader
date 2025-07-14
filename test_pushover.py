#!/usr/bin/env python3
"""
Test script for Pushover notification configuration.

This script allows you to test your Pushover notification setup
without running the full iCloud Photo Sync.
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from icloud_photo_sync.config import KeyringConfig, get_config
from icloud_photo_sync.pushover_service import PushoverNotificationService
from icloud_photo_sync.logger import setup_logging


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
    
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = KeyringConfig()
        
        # Check if Pushover is enabled
        if not config.enable_pushover:
            logger.warning("Pushover notifications are disabled. Set ENABLE_PUSHOVER=true in your .env file.")
            return False
        
        # Get Pushover configuration
        pushover_config = config.get_pushover_config()
        if not pushover_config:
            logger.error("Pushover configuration is incomplete. Check PUSHOVER_API_TOKEN and PUSHOVER_USER_KEY in your .env file.")
            return False
        
        logger.info(f"Pushover configuration found:")
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
            
    except Exception as e:
        logger.error(f"Error testing Pushover configuration: {e}")
        return False


def main():
    """Main function."""
    print("iCloud Photo Sync - Pushover Configuration Test")
    print("=" * 50)
    print()
    
    if test_pushover_config():
        print("\n✅ Pushover configuration test completed successfully!")
        print("Your notification setup is ready for 2FA authentication.")
    else:
        print("\n❌ Pushover configuration test failed.")
        print("Please check your .env file and ensure you have:")
        print("  - ENABLE_PUSHOVER=true")
        print("  - Valid PUSHOVER_API_TOKEN")
        print("  - Valid PUSHOVER_USER_KEY")
        print()
        print("Get your Pushover credentials at:")
        print("  - API Token: https://pushover.net/apps/build")
        print("  - User Key: https://pushover.net")
        sys.exit(1)


if __name__ == "__main__":
    main()
