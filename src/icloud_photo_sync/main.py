"""Main entry point for iCloud Photo Sync Tool."""

import sys
import logging
from pathlib import Path


def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/icloud-sync.log', mode='a'),
        ]
    )


def main() -> None:
    """Main entry point for the application."""
    print("🌟 iCloud Photo Sync Tool v0.1.0")
    print("==================================")
    
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting iCloud Photo Sync Tool")
    
    try:
        # TODO: Implement actual sync logic
        print("✅ Sync logic will be implemented in the next phase")
        logger.info("Application completed successfully")
        
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
