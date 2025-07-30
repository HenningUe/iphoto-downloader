"""Core sync logic for iPhoto Downloader Tool."""

import typing as t

from .config import BaseConfig
from .icloud_client import iCloudClient
from .deletion_tracker import DeletionTracker
from .logger import get_logger


class PhotoSyncer:
    """Handles the core photo synchronization logic."""

    def __init__(self, config: BaseConfig) -> None:
        """Initialize photo syncer.

        Args:
            config: Application configuration
        """
        self.config = config
        self.icloud_client = iCloudClient(config)

        # Ensure sync directory exists before creating deletion tracker
        self.config.ensure_sync_directory()

        self.deletion_tracker = DeletionTracker(
            str(self.config.database_path)
        )
        self.stats = {
            'total_photos': 0,
            'new_downloads': 0,
            'already_exists': 0,
            'deleted_skipped': 0,
            'errors': 0,
            'bytes_downloaded': 0
        }

    @property
    def logger(self):
        """Get the global logger instance."""
        return get_logger()

    def sync(self):
        """Perform photo synchronization.

        Returns:
            True if sync completed successfully, False otherwise
        """
        try:
            self.logger.info("🚀 Starting iphoto-downloader")

            # Ensure sync directory exists
            self.config.ensure_sync_directory()

            # Authenticate with iCloud
            if not self.icloud_client.authenticate():
                return False

            # Handle 2FA if required
            if self.icloud_client.requires_2fa():
                if not self._handle_2fa():
                    return False

            # Validate that specified albums exist (if any are specified)
            if (self.config.personal_album_names_to_include or
                    self.config.shared_album_names_to_include):
                self.logger.info("🔍 Validating specified album names...")
                try:
                    self.config.validate_albums_exist(self.icloud_client)
                    self.logger.info("✅ All specified albums found")
                except ValueError as e:
                    self.logger.error(f"❌ Album validation failed: {e}")
                    return False

            # Get local files
            local_files = self._get_local_files()
            self.logger.info(f"📁 Found {len(local_files)} existing local files")

            # Track files that were deleted locally
            self._track_local_deletions(local_files)

            # Sync photos
            self._sync_photos(local_files)

            # Print summary
            self._print_summary()

            self.logger.info("✅ Photo sync completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error during sync: {e}")
            self.stats['errors'] += 1
            return False

    def _handle_2fa(self) -> bool:
        """Handle two-factor authentication.

        Returns:
            True if 2FA handled successfully, False otherwise
        """
        self.logger.info("🔐 Two-factor authentication required")

        # Try to send Pushover notification if configured
        self._send_2fa_notification()

        try:
            # Prompt user for 2FA code
            self.logger.info("📱 Please check your Apple device for a 2FA verification code")

            # Get 2FA code from user input
            code = input("Enter the 6-digit 2FA code: ").strip()

            if not code:
                self.logger.error("❌ No 2FA code provided")
                return False

            if len(code) != 6 or not code.isdigit():
                self.logger.error("❌ Invalid 2FA code format. Please enter a 6-digit number.")
                return False

            self.logger.info("🔄 Validating 2FA code...")

            # Validate the 2FA code
            if self.icloud_client.handle_2fa_validation(code):
                self.logger.info("✅ 2FA verification successful")

                # Send success notification if configured
                self._send_2fa_success_notification()

                # Try to trust the session to avoid future 2FA requirements
                if self.icloud_client.trust_session():
                    self.logger.info("✅ Session trusted - future logins may not require 2FA")

                return True
            else:
                self.logger.error("❌ 2FA verification failed. Please try again.")
                return False

        except KeyboardInterrupt:
            self.logger.info("\n❌ 2FA cancelled by user")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error during 2FA handling: {e}")
            return False

    def _send_2fa_notification(self) -> None:
        """Send Pushover notification for 2FA authentication if configured."""
        try:
            pushover_config = self.config.get_pushover_config()
            if not pushover_config:
                self.logger.debug("Pushover notifications not configured, skipping notification")
                return

            from auth2fa.pushover_service import PushoverService as PushoverNotificationService
            notification_service = PushoverNotificationService(pushover_config)

            # For now, we'll use a placeholder URL since we haven't implemented the web server yet
            # TODO: Replace with actual web server URL once implemented
            web_server_url = "http://localhost:8080/2fa"

            if notification_service.send_2fa_notification(web_server_url):
                self.logger.info("📱 2FA notification sent via Pushover")
            else:
                self.logger.warning("⚠️ Failed to send 2FA notification via Pushover")

        except Exception as e:
            self.logger.warning(f"⚠️ Error sending 2FA notification: {e}")

    def _send_2fa_success_notification(self) -> None:
        """Send Pushover notification for successful 2FA authentication if configured."""
        try:
            pushover_config = self.config.get_pushover_config()
            if not pushover_config:
                return

            from auth2fa.pushover_service import PushoverService as PushoverNotificationService
            notification_service = PushoverNotificationService(pushover_config)

            if notification_service.send_auth_success_notification():
                self.logger.info("📱 2FA success notification sent via Pushover")
            else:
                self.logger.warning("⚠️ Failed to send 2FA success notification via Pushover")

        except Exception as e:
            self.logger.warning(f"⚠️ Error sending 2FA success notification: {e}")

    def _get_local_files(self) -> set[str]:
        """Get set of existing local filenames with their relative paths.

        Returns:
            Set of local image file paths relative to sync directory
        """
        try:
            local_files = set()

            # Define image file extensions
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif',
                                '.bmp', '.tiff', '.tif', '.webp', '.heic', '.heif'}

            if self.config.sync_directory.exists():
                for file_path in self.config.sync_directory.rglob("*"):
                    if (file_path.is_file() and
                        not file_path.name.startswith('.') and
                            file_path.suffix.lower() in image_extensions):
                        # Use relative path from sync directory for album support
                        relative_path = file_path.relative_to(self.config.sync_directory)
                        local_files.add(str(relative_path))

            return local_files

        except Exception as e:
            self.logger.error(f"❌ Error scanning local files: {e}")
            return set()

    def _track_local_deletions(self, local_files: set[str]) -> None:
        """Track files that were deleted locally.

        Args:
            local_files: Set of current local filenames
        """
        self.logger.debug("🔍 Checking for locally deleted files")

        # Detect photos that were downloaded but are now missing locally
        deleted_photos = self.deletion_tracker.detect_locally_deleted_photos(
            self.config.sync_directory
        )

        if deleted_photos:
            self.logger.info(f"🗑️ Found {len(deleted_photos)} locally deleted photos")
            # Mark them as deleted to prevent re-downloading
            self.deletion_tracker.mark_photos_as_deleted(deleted_photos)
        else:
            self.logger.debug("✅ No locally deleted photos detected")

        # Get previously tracked deleted photos
        deleted_photo_ids = self.deletion_tracker.get_deleted_photos()

        # Check if any deleted photos now exist locally (were restored)
        restored_count = 0
        for photo_id in deleted_photo_ids:
            # Check if this photo is back in local files
            downloaded_photos = self.deletion_tracker.get_downloaded_photos()
            if photo_id in downloaded_photos:
                metadata = downloaded_photos[photo_id]
                local_path = self.config.sync_directory / metadata['local_path']
                if local_path.exists():
                    # Photo was restored, remove from deletion tracker
                    self.deletion_tracker.remove_deleted_photo(photo_id)
                    self.logger.info(f"🔄 Restored deleted photo: {metadata['local_path']}")
                    restored_count += 1

        if restored_count > 0:
            self.logger.info(f"🔄 Found {restored_count} restored photos")

        # Get deletion tracker stats
        stats = self.deletion_tracker.get_stats()
        if stats['total_deleted'] > 0:
            self.logger.info(f"📝 Deletion tracker has {stats['total_deleted']} deleted photos")

    def _sync_photos(self, local_files: set[str]) -> None:
        """Sync photos from iCloud with album support.

        Args:
            local_files: Set of existing local file paths relative to sync directory
        """
        download_count = 0

        # Get photos based on selected source (main library and/or albums)
        photo_iterator = self._get_photo_iterator()

        for photo_info in photo_iterator:
            try:
                self.stats['total_photos'] += 1
                filename = photo_info['filename']
                photo_id = photo_info['id']
                album_name = photo_info.get('album_name')

                # Check if we've reached download limit
                if (self.config.max_downloads > 0 and
                        download_count >= self.config.max_downloads):
                    self.logger.info(f"📊 Reached download limit ({self.config.max_downloads})")
                    break

                # Check if photo was deleted locally (album-aware)
                if self.deletion_tracker.is_photo_deleted(filename, album_name):
                    self.logger.debug(f"⏭️ Skipping deleted photo: {filename} from {album_name}")
                    self.stats['deleted_skipped'] += 1
                    continue

                # Check if photo was already downloaded from this album (album-aware)
                if self.deletion_tracker.is_photo_downloaded(filename, album_name):
                    self.logger.debug(
                        f"⏭️ Photo already downloaded from album: {filename} from {album_name}"
                    )
                    self.stats['already_exists'] += 1
                    continue

                # Create album subfolder path (use root if no album)
                if album_name:
                    album_folder = self._sanitize_album_name(album_name)
                    relative_path = f"{album_folder}/{filename}"
                else:
                    # For backward compatibility - photos without album go to root
                    album_folder = ""
                    relative_path = filename

                # Check if file already exists locally (fallback safety check)
                if relative_path in local_files:
                    self.logger.debug(f"⏭️ Photo file already exists locally: {relative_path}")
                    # Record this as downloaded if not already tracked
                    if not self.deletion_tracker.is_photo_downloaded(filename, album_name):
                        self.deletion_tracker.add_downloaded_photo(
                            photo_id=photo_id,
                            filename=filename,
                            local_path=relative_path,
                            album_name=album_name
                        )
                    self.stats['already_exists'] += 1
                    continue

                # Create full local path
                local_path = self.config.sync_directory / relative_path

                # Create subdirectories if needed
                local_path.parent.mkdir(parents=True, exist_ok=True)

                if self.config.dry_run:
                    # In dry run mode, just log what would be downloaded
                    self.logger.info(f"[DRY RUN] Would download: {relative_path}")
                    download_count += 1
                    self.stats['new_downloads'] += 1
                    # Use the photo size from metadata if available
                    if 'size' in photo_info:
                        self.stats['bytes_downloaded'] += photo_info['size']

                    # In dry run, we don't actually record downloads to avoid
                    # polluting the tracking database with hypothetical data
                else:
                    # Actually download the photo
                    if self.icloud_client.download_photo(photo_info, str(local_path)):
                        download_count += 1
                        self.stats['new_downloads'] += 1

                        # Update file size stats
                        file_size = None
                        if local_path.exists():
                            file_size = local_path.stat().st_size
                            self.stats['bytes_downloaded'] += file_size

                        # Record the successful download in the tracker
                        self.deletion_tracker.add_downloaded_photo(
                            photo_id=photo_id,
                            filename=filename,
                            local_path=relative_path,
                            file_size=file_size,
                            album_name=album_name
                        )

                        self.logger.info(f"✅ Downloaded: {relative_path}")
                    else:
                        self.stats['errors'] += 1
                        self.logger.warning(f"⚠️ Failed to download: {relative_path}")

                # Log progress every 50 photos
                if self.stats['total_photos'] % 50 == 0:
                    self._log_progress()

            except Exception as e:
                self.stats['errors'] += 1
                self.logger.error(
                    f"❌ Error processing photo {photo_info.get('filename', 'unknown')}: {e}")
                continue

    def _get_photo_iterator(self) -> t.Iterator[dict[str, t.Any]]:
        """Get iterator for photos based on configuration.

        Returns:
            Iterator yielding photo information dictionaries
        """
        # Use album filtering based on configuration
        return self.icloud_client.list_photos_from_filtered_albums(
            self.config,
        )

    def _sanitize_album_name(self, album_name: str) -> str:
        """Sanitize album name for use as folder name.

        Args:
            album_name: Original album name

        Returns:
            Sanitized folder name
        """
        # Remove or replace invalid characters for folder names
        import re

        # Replace invalid characters with underscores
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', album_name)

        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(' .')

        # Ensure we have a valid name
        if not sanitized:
            sanitized = 'Unknown_Album'

        return sanitized

    def _log_progress(self) -> None:
        """Log current sync progress."""
        self.logger.info(
            f"📊 Progress: {self.stats['total_photos']} processed, "
            f"{self.stats['new_downloads']} downloaded, "
            f"{self.stats['already_exists']} existed, "
            f"{self.stats['deleted_skipped']} deleted, "
            f"{self.stats['errors']} errors"
        )

    def _print_summary(self) -> None:
        """Print sync summary."""
        self.logger.info("=" * 50)
        self.logger.info("📊 SYNC SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"Total photos processed: {self.stats['total_photos']}")
        self.logger.info(f"New downloads: {self.stats['new_downloads']}")
        self.logger.info(f"Already existed: {self.stats['already_exists']}")
        self.logger.info(f"Deleted (skipped): {self.stats['deleted_skipped']}")
        self.logger.info(f"Errors: {self.stats['errors']}")

        if self.stats['bytes_downloaded'] > 0:
            mb_downloaded = self.stats['bytes_downloaded'] / (1024 * 1024)
            self.logger.info(f"Data downloaded: {mb_downloaded:.1f} MB")

        if self.config.dry_run:
            self.logger.info("🔍 DRY RUN MODE - No files were actually downloaded")

        self.logger.info("=" * 50)

    def get_stats(self) -> dict[str, t.Any]:
        """Get sync statistics.

        Returns:
            Dictionary with sync statistics including computed fields
        """
        stats: dict[str, t.Any] = {}

        # Copy base stats
        for key, value in self.stats.items():
            stats[key] = value

        # Add computed fields
        stats['mb_downloaded'] = round(stats['bytes_downloaded'] / (1024 * 1024), 2)
        stats['success_rate'] = (
            round((stats['new_downloads'] / max(stats['total_photos'], 1)) * 100, 2)
            if stats['total_photos'] > 0 else 0.0
        )

        return stats

    def cleanup(self) -> None:
        """Clean up resources and close database connections.

        This method should be called when the syncer is no longer needed,
        especially important on Windows to prevent file handle leaks.
        """
        try:
            if hasattr(self, 'deletion_tracker') and self.deletion_tracker:
                self.deletion_tracker.close()
                self.logger.debug("✅ Deletion tracker database connections closed")
        except Exception as e:
            # Log but don't raise - cleanup should be best effort
            self.logger.warning(f"⚠️ Error during cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup happens even if not called explicitly."""
        self.cleanup()
