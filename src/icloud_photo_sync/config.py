"""Configuration management for iCloud Photo Sync Tool."""

import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Configuration manager for the application."""

    def __init__(self, env_file: Optional[str] = None) -> None:
        """Initialize configuration.
        
        Args:
            env_file: Path to .env file. If None, uses default .env
        """
        # Load environment variables from .env file
        env_path = env_file or '.env'
        if Path(env_path).exists():
            load_dotenv(env_path)
        
        # iCloud credentials
        self.icloud_username = os.getenv('ICLOUD_USERNAME')
        self.icloud_password = os.getenv('ICLOUD_PASSWORD')
        
        # Sync settings
        self.sync_directory = Path(os.getenv('SYNC_DIRECTORY', './photos'))
        self.dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # Download limits
        self.max_downloads = int(os.getenv('MAX_DOWNLOADS', '0'))
        self.max_file_size_mb = int(os.getenv('MAX_FILE_SIZE_MB', '0'))
        
        # Validate required settings
        self._validate()
    
    def _validate(self) -> None:
        """Validate configuration settings."""
        errors = []
        
        if not self.icloud_username:
            errors.append("ICLOUD_USERNAME is required")
        
        if not self.icloud_password:
            errors.append("ICLOUD_PASSWORD is required")
        
        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            errors.append(f"Invalid LOG_LEVEL: {self.log_level}")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    def ensure_sync_directory(self) -> None:
        """Create sync directory if it doesn't exist."""
        self.sync_directory.mkdir(parents=True, exist_ok=True)
    
    def get_log_level(self) -> int:
        """Get logging level as integer."""
        return getattr(logging, self.log_level, logging.INFO)
    
    def __str__(self) -> str:
        """String representation of config (without sensitive data)."""
        return (
            f"Config("
            f"username={'***' if self.icloud_username else None}, "
            f"sync_dir={self.sync_directory}, "
            f"dry_run={self.dry_run}, "
            f"log_level={self.log_level}"
            f")"
        )
