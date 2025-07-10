"""Core sync logic for iCloud Photo Sync Tool."""

import logging
import hashlib
from pathlib import Path
from typing import Set, Dict, Any, List, Optional
from datetime import datetime

from .config import Config
from .icloud_client import iCloudClient
from .deletion_tracker import DeletionTracker


logger = logging.getLogger(__name__)


class PhotoSyncer:
    """Handles the core photo synchronization logic."""

    def __init__(self, config: Config) -> None:
        """Initialize photo syncer.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.icloud_client = iCloudClient(config)
        
        # Ensure sync directory exists before creating deletion tracker
        self.config.ensure_sync_directory()
        
        self.deletion_tracker = DeletionTracker(
            str(config.sync_directory / "deletion_tracker.db")
        )
        self.stats = {
            'total_photos': 0,
            'new_downloads': 0,
            'already_exists': 0,
            'deleted_skipped': 0,
            'errors': 0,
            'bytes_downloaded': 0
        }
    
    def sync(self) -> bool:
        """Perform photo synchronization.
        
        Returns:
            True if sync completed successfully, False otherwise
        """
        try:
            logger.info("🚀 Starting iCloud photo sync")
            
            # Ensure sync directory exists
            self.config.ensure_sync_directory()
            
            # Authenticate with iCloud
            if not self.icloud_client.authenticate():
                return False
            
            # Handle 2FA if required
            if self.icloud_client.requires_2fa():
                if not self._handle_2fa():
                    return False
            
            # Get local files
            local_files = self._get_local_files()
            logger.info(f"📁 Found {len(local_files)} existing local files")
            
            # Track files that were deleted locally
            self._track_local_deletions(local_files)
            
            # Sync photos
            self._sync_photos(local_files)
            
            # Print summary
            self._print_summary()
            
            logger.info("✅ Photo sync completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Photo sync failed: {e}")
            return False
    
    def _handle_2fa(self) -> bool:
        """Handle two-factor authentication.
        
        Returns:
            True if 2FA handled successfully, False otherwise
        """
        logger.info("🔐 Two-factor authentication required")
        
        # In a real implementation, you might want to:
        # 1. Show a GUI prompt
        # 2. Use a CLI input
        # 3. Read from environment variable
        # For now, we'll log an error
        
        logger.error("❌ 2FA required but not implemented in this version")
        logger.error("Please disable 2FA temporarily or use app-specific password")
        return False
    
    def _get_local_files(self) -> Set[str]:
        """Get set of existing local filenames.
        
        Returns:
            Set of local filenames
        """
        try:
            local_files = set()
            
            if self.config.sync_directory.exists():
                for file_path in self.config.sync_directory.rglob("*"):
                    if file_path.is_file() and not file_path.name.startswith('.'):
                        # Use relative path from sync directory
                        rel_path = file_path.relative_to(self.config.sync_directory)
                        local_files.add(str(rel_path))
            
            return local_files
            
        except Exception as e:
            logger.error(f"❌ Error scanning local files: {e}")
            return set()
    
    def _track_local_deletions(self, local_files: Set[str]) -> None:
        """Track files that were deleted locally.
        
        Args:
            local_files: Set of current local filenames
        """
        try:
            # This is a simplified implementation
            # In a real scenario, you'd need to track which files
            # were previously downloaded but are now missing
            
            logger.debug("🔍 Checking for locally deleted files")
            
            # Get deletion tracker stats
            stats = self.deletion_tracker.get_stats()
            if stats['total_deleted'] > 0:
                logger.info(f"📝 Deletion tracker has {stats['total_deleted']} deleted photos")
            
        except Exception as e:
            logger.error(f"❌ Error tracking local deletions: {e}")
    
    def _sync_photos(self, local_files: Set[str]) -> None:
        """Sync photos from iCloud.
        
        Args:
            local_files: Set of existing local filenames
        """
        download_count = 0
        
        for photo_info in self.icloud_client.list_photos():
            try:
                self.stats['total_photos'] += 1
                filename = photo_info['filename']
                photo_id = photo_info['id']
                
                # Check if we've reached download limit
                if (self.config.max_downloads > 0 and 
                    download_count >= self.config.max_downloads):
                    logger.info(f"📊 Reached download limit ({self.config.max_downloads})")
                    break
                
                # Check if photo was deleted locally
                if self.deletion_tracker.is_deleted(photo_id):
                    logger.debug(f"⏭️ Skipping deleted photo: {filename}")
                    self.stats['deleted_skipped'] += 1
                    continue
                
                # Check if file already exists locally
                if filename in local_files:
                    logger.debug(f"⏭️ Photo already exists: {filename}")
                    self.stats['already_exists'] += 1
                    continue
                
                # Download the photo
                local_path = self.config.sync_directory / filename
                
                # Create subdirectories if needed
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                if self.icloud_client.download_photo(photo_info, str(local_path)):
                    download_count += 1
                    self.stats['new_downloads'] += 1
                    
                    # Update file size stats
                    if not self.config.dry_run and local_path.exists():
                        self.stats['bytes_downloaded'] += local_path.stat().st_size
                    
                    logger.info(f"✅ Downloaded: {filename}")
                else:
                    self.stats['errors'] += 1
                    logger.warning(f"⚠️ Failed to download: {filename}")
                
                # Log progress every 50 photos
                if self.stats['total_photos'] % 50 == 0:
                    self._log_progress()
                    
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"❌ Error processing photo {photo_info.get('filename', 'unknown')}: {e}")
                continue
    
    def _log_progress(self) -> None:
        """Log current sync progress."""
        logger.info(
            f"📊 Progress: {self.stats['total_photos']} processed, "
            f"{self.stats['new_downloads']} downloaded, "
            f"{self.stats['already_exists']} existed, "
            f"{self.stats['deleted_skipped']} deleted, "
            f"{self.stats['errors']} errors"
        )
    
    def _print_summary(self) -> None:
        """Print sync summary."""
        logger.info("=" * 50)
        logger.info("📊 SYNC SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total photos processed: {self.stats['total_photos']}")
        logger.info(f"New downloads: {self.stats['new_downloads']}")
        logger.info(f"Already existed: {self.stats['already_exists']}")
        logger.info(f"Deleted (skipped): {self.stats['deleted_skipped']}")
        logger.info(f"Errors: {self.stats['errors']}")
        
        if self.stats['bytes_downloaded'] > 0:
            mb_downloaded = self.stats['bytes_downloaded'] / (1024 * 1024)
            logger.info(f"Data downloaded: {mb_downloaded:.1f} MB")
        
        if self.config.dry_run:
            logger.info("🔍 DRY RUN MODE - No files were actually downloaded")
        
        logger.info("=" * 50)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get sync statistics.
        
        Returns:
            Dictionary with sync statistics
        """
        return self.stats.copy()
