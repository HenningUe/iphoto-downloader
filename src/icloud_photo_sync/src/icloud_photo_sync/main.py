"""Main entry point for iCloud Photo Sync Tool."""

import sys

from icloud_photo_sync.config import get_config
from icloud_photo_sync.sync import PhotoSyncer
from icloud_photo_sync.logger import setup_logging, get_logger
from icloud_photo_sync import manage_credentials


def main() -> None:
    """Main entry point for the application."""
    print("🌟 iCloud Photo Sync Tool v0.1.0")
    print("==================================")

    logger = None

    config = get_config()

    if not config.icloud_has_stored_credentials:
        print("🔑 iCloud credentials not found in keyring.")
        manage_credentials.icloud_store_credentials()

    if not config.pushover_has_stored_credentials:
        print("🔑 Pushover credentials not found in keyring.")
        manage_credentials.pushover_store_credentials()

    try:
        config.validate()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("💡 Please check your .env file and ensure all required settings are configured.")
        sys.exit(1)

    try:
        # Set up logging with config
        setup_logging(config.get_log_level())
        logger = get_logger()

        logger.info("Starting iCloud Photo Sync Tool")
        logger.info(f"Configuration: {config}")

        # Initialize and run syncer
        syncer = PhotoSyncer(config)
        success = syncer.sync()

        if success:
            logger.info("✅ Sync completed successfully")
            print("\n✅ Sync completed successfully!")
        else:
            logger.error("❌ Sync failed")
            print("\n❌ Sync failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Sync interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if logger:
            logger.error(f"Application failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
