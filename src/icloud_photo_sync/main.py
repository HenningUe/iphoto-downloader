"""Main entry point for iCloud Photo Sync Tool."""

import sys
import logging
from pathlib import Path

from .config import Config
from .sync import PhotoSyncer


def setup_logging(config: Config) -> None:
    """Set up logging configuration.
    
    Args:
        config: Application configuration
    """
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=config.get_log_level(),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/icloud-sync.log', mode='a', encoding='utf-8'),
        ]
    )


def main() -> None:
    """Main entry point for the application."""
    print("🌟 iCloud Photo Sync Tool v0.1.0")
    print("==================================")
    
    logger = None
    
    try:
        # Load configuration
        config = Config()
        
        # Set up logging with config
        setup_logging(config)
        logger = logging.getLogger(__name__)
        
        logger.info("Starting iCloud Photo Sync Tool")
        logger.info(f"Configuration: {config}")
        
        # Initialize and run syncer
        syncer = PhotoSyncer(config)
        
        if syncer.sync():
            logger.info("Application completed successfully")
            sys.exit(0)
        else:
            logger.error("Application failed")
            sys.exit(1)
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("💡 Please check your .env file and ensure all required settings are configured.")
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
