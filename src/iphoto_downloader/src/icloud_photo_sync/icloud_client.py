"""iCloud authentication and API interaction."""

import time
import typing as t
from pathlib import Path
from pyicloud.services.photos import AlbumContainer, BasePhotoAlbum
from pyicloud import PyiCloudService
from pyicloud.exceptions import PyiCloudFailedLoginException, PyiCloudAPIResponseException

from .config import BaseConfig
from .logger import get_logger
from auth2fa import handle_2fa_authentication, Auth2FAConfig, PushoverConfig


class iCloudClient:
    """Handles iCloud authentication and photo operations."""

    def __init__(self, config: BaseConfig) -> None:
        """Initialize iCloud client.

        Args:
            config: Application configuration
        """
        self.config = config
        self._api: PyiCloudService | None = None

        # Set up session storage directory
        self.session_dir = Path.home() / "iphoto_downloader" / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)

    @property
    def logger(self):
        """Get the global logger instance."""
        return get_logger()

    def authenticate(self) -> bool:
        """Authenticate with iCloud with session persistence and web-based 2FA.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Clean up expired session files before authentication
            self.cleanup_expired_sessions()

            if not self.config.icloud_username or not self.config.icloud_password:
                self.logger.error("❌ iCloud username or password not configured")
                return False

            self.logger.info(f"Authenticating with iCloud as {self.config.icloud_username}")

            # Create PyiCloudService with session storage
            self._api = PyiCloudService(
                self.config.icloud_username,
                self.config.icloud_password,
                cookie_directory=str(self.session_dir)
            )

            # Check if we have a trusted session
            if hasattr(self._api, 'is_trusted_session') and self._api.is_trusted_session:
                self.logger.info("✅ Using existing trusted session - no 2FA required")
                return self._verify_access()

            # Check if 2FA is required
            if self.requires_2fa():
                self.logger.info("🔐 2FA authentication required")
                code = self._handle_2fa_with_web_server()
                if code:
                    self.trust_session()
                else:
                    return False

            # Verify access after authentication
            return self._verify_access()

        except PyiCloudFailedLoginException as e:
            self.logger.error(f"❌ iCloud login failed: {e}")
            return False
        except PyiCloudAPIResponseException as e:
            self.logger.error(f"❌ iCloud API error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Unexpected error during authentication: {e}")
            return False

    def _verify_access(self) -> bool:
        """Verify that we can access iCloud Photos.

        Returns:
            True if access is successful, False otherwise
        """
        try:
            if self._api and self._api.photos:
                self.logger.info("✅ Successfully authenticated with iCloud")
                return True
            else:
                self.logger.error("❌ Failed to access iCloud Photos")
                return False
        except Exception as e:
            self.logger.error(f"❌ Error verifying iCloud access: {e}")
            return False

    def _handle_2fa_with_web_server(self) -> str | None:
        """Handle 2FA authentication using the web server interface.

        Returns:
            2FA code if successful, None if failed or timeout
        """
        cfg_2fa = Auth2FAConfig(
            pushover_config=PushoverConfig(
                api_token=self.config.pushover_api_token,
                user_key=self.config.pushover_user_key
            ),
        )
        return handle_2fa_authentication(
            config=cfg_2fa,
            request_2fa_callback=self._request_new_2fa,
            validate_2fa_callback=self.handle_2fa_validation
        )

    def _request_new_2fa(self) -> bool:
        """Request a new 2FA code from Apple.

        Returns:
            True if request was successful, False otherwise
        """
        if self._api and hasattr(self._api, 'send_verification_code'):
            # Try to get trusted devices and send to first one
            if hasattr(self._api, 'trusted_devices') and self._api.trusted_devices:
                device = self._api.trusted_devices[0]
                self._api.send_verification_code(device)
                self.logger.info("📱 New 2FA code requested from Apple")
                return True
            else:
                self.logger.warning("⚠️ No trusted devices found for 2FA")
                return False
        else:
            self.logger.warning("⚠️ Cannot request new 2FA code - not supported")
            return False

    def requires_2fa(self) -> bool:
        """Check if 2FA is required.

        Returns:
            True if 2FA is required, False otherwise
        """
        if not self._api:
            return False
        return self._api.requires_2fa

    def is_trusted_session(self) -> bool:
        """Check if the current session is trusted.

        Returns:
            True if session is trusted, False otherwise
        """
        if not self._api:
            return False
        return hasattr(self._api, 'is_trusted_session') and self._api.is_trusted_session

    def handle_2fa_validation(self, code: str) -> bool:
        """Handle 2FA verification.

        Args:
            code: 2FA verification code

        Returns:
            True if 2FA verification successful, False otherwise
        """
        if not self._api:
            return False

        try:
            result = self._api.validate_2fa_code(code)
            if result:
                self.logger.info("✅ 2FA verification successful")
            else:
                self.logger.error("❌ 2FA verification failed")
            return result
        except Exception as e:
            self.logger.error(f"❌ 2FA verification error: {e}")
            return False

    def trust_session(self) -> bool:
        """Request to trust the current session to avoid future 2FA.

        Returns:
            True if session was successfully trusted, False otherwise
        """
        if not self._api:
            return False

        if hasattr(self._api, 'trust_session'):
            result = self._api.trust_session()
            if result:
                self.logger.info("✅ Session trusted successfully")
            else:
                self.logger.warning("⚠️ Failed to trust session")
            return result
        else:
            self.logger.warning("⚠️ Session trusting not supported by this version of pyicloud")
            return False

    def cleanup_expired_sessions(self, max_age_days: int = 30) -> None:
        """Clean up expired session files older than specified days.

        Args:
            max_age_days: Maximum age in days for session files (default: 30)
        """
        if not self.session_dir.exists():
            return

        current_time = time.time()
        cutoff_time = current_time - (max_age_days * 24 * 60 * 60)  # Convert days to seconds

        cleaned_count = 0
        total_size = 0

        # Clean up session files (cookies, cache, etc.)
        for session_file in self.session_dir.iterdir():
            if session_file.is_file():
                try:
                    file_mtime = session_file.stat().st_mtime
                    if file_mtime < cutoff_time:
                        file_size = session_file.stat().st_size
                        session_file.unlink()
                        cleaned_count += 1
                        total_size += file_size
                        self.logger.debug(f"Removed expired session file: {session_file.name}")
                except (OSError, FileNotFoundError) as e:
                    self.logger.warning(
                        f"Failed to remove session file {session_file.name}: {e}"
                    )

        if cleaned_count > 0:
            self.logger.info(
                f"🧹 Cleaned up {cleaned_count} expired session files "
                f"({total_size / 1024:.1f} KB freed)"
            )
        else:
            self.logger.debug("No expired session files found to clean up")

    def list_photos(self) -> t.Iterator[dict[str, t.Any]]:
        """List all photos from iCloud.

        Yields:
            Photo metadata dictionaries
        """
        if not self._api or not self._api.photos:
            self.logger.error("❌ Not authenticated or photos service unavailable")
            return

        self.logger.info("📥 Fetching photo list from iCloud...")

        try:
            # Get all photos from iCloud
            photos = self._api.photos.all
            total_count = len(photos)

            self.logger.info(f"📊 Found {total_count} photos in iCloud")

            for i, photo in enumerate(photos, 1):
                if i % 100 == 0:  # Log progress every 100 photos
                    self.logger.info(f"📥 Processing photo {i}/{total_count}")

                try:
                    # Extract photo metadata
                    photo_info = {
                        'id': photo.id,
                        'filename': photo.filename,
                        'size': getattr(photo, 'size', 0),
                        'created': getattr(photo, 'created', None),
                        'modified': getattr(photo, 'modified', None),
                        'album_name': 'All Photos',  # Default album for main library
                        'photo_obj': photo  # Keep reference for downloading
                    }

                    yield photo_info

                except Exception as e:
                    self.logger.warning(f"⚠️ Error processing photo {i}: {e}")
                    continue
        except Exception as e:
            self.logger.error(f"❌ Error fetching photos from iCloud: {e}")
            return

    def list_albums(self) -> t.Iterator[dict[str, t.Any]]:
        """List all albums from iCloud Photos.

        Yields:
            Album metadata dictionaries
        """
        if not self._api or not self._api.photos:
            self.logger.error("❌ Not authenticated or photos service unavailable")
            return

        self.logger.info("📥 Fetching album list from iCloud...")

        # Get all albums from iCloud
        albums = self._api.photos.albums
        
        # Get personal albums (excluding the Library album which contains shared streams)  
        all_albums = list(albums.values()) if hasattr(albums, 'values') else []
        albums_list = [album for album in all_albums if getattr(album, 'name', '') != 'Library']
        
        self.logger.info(f"📊 Found {len(albums_list)} personal albums in iCloud")

        # shared albums
        album_library = self._api.photos.albums['Library']
        albums_shared: AlbumContainer = album_library.service.shared_streams
        albums_shared_list = list(albums_shared.values())
        self.logger.info(f"📊 Found {len(albums_shared_list)} shared albums in iCloud")

        for album in albums_list + albums_shared_list:
            is_shared = getattr(album, 'list_type', '') == "sharedstream"
            # Extract album metadata
            try:
                photo_count = len(album)
            except (TypeError, AttributeError):
                photo_count = 0
                
            album_info = {
                'id': getattr(album, 'id', None),
                'name': album.name,
                'photo_count': photo_count,
                'is_shared': is_shared,
                'album_obj': album  # Keep reference for accessing photos
            }

            yield album_info

    def list_photos_from_album(
        self,
        album_name: str,
        is_shared: bool | None = None,
    ) -> t.Iterator[dict[str, t.Any]]:
        """List photos from a specific album.

        Args:
            album_name: Name of the album to list photos from

        Yields:
            Photo metadata dictionaries
        """
        if not self._api or not self._api.photos:
            self.logger.error("❌ Not authenticated or photos service unavailable")
            return

        all_albums = []

        if is_shared is None or is_shared is False:
            # Get all albums from iCloud
            albums = self._api.photos.albums
            albums_list = list(albums.values())
            all_albums.extend(albums_list)

        if is_shared is None or is_shared is True:
            # Get all shared albums from iCloud
            album_library = self._api.photos.albums['Library']
            albums_shared: AlbumContainer = album_library.service.shared_streams
            albums_shared_list = list(albums_shared.values())
            all_albums.extend(albums_shared_list)

        # Find the album by name
        target_album: BasePhotoAlbum | None = None
        for album in all_albums:
            if album.name == album_name:
                target_album = album
                break

        if not target_album:
            self.logger.error(f"❌ Album '{album_name}' not found")
            return

        self.logger.info(f"📥 Fetching photos from album '{album_name}'...")

        photos = target_album  # type: ignore
        total_count = len(target_album)

        self.logger.info(f"📊 Found {total_count} photos in album '{album_name}'")

        for i, photo in enumerate(photos, 1):
            if i % 50 == 0:  # Log progress every 50 photos for albums
                self.logger.info(f"📥 Processing photo {i}/{total_count} "
                                 f"from album '{album_name}'")

            try:
                # Extract photo metadata
                photo_info = {
                    'id': photo.id,
                    'filename': photo.filename,
                    'size': getattr(photo, 'size', 0),
                    'created': getattr(photo, 'created', None),
                    'modified': getattr(photo, 'modified', None),
                    'album_name': album_name,
                    'photo_obj': photo  # Keep reference for downloading
                }

                yield photo_info

            except Exception as e:
                self.logger.warning(f"⚠️ Error processing photo {i} "
                                    f"from album '{album_name}': {e}")
                continue

    def list_photos_from_albums(self, album_names: list[str],
                                include_main_library: bool = True) -> t.Iterator[dict[str, t.Any]]:
        """List photos from multiple specified albums.

        Args:
            album_names: List of album names to include
            include_main_library: Whether to include photos from main library

        Yields:
            Photo metadata dictionaries
        """
        if not self._api or not self._api.photos:
            self.logger.error("❌ Not authenticated or photos service unavailable")
            return

        processed_photo_ids = set()  # Track to avoid duplicates

        # Include main library photos if requested
        if include_main_library:
            self.logger.info("📥 Including photos from main library")
            for photo_info in self.list_photos():
                if photo_info['id'] not in processed_photo_ids:
                    processed_photo_ids.add(photo_info['id'])
                    yield photo_info

        # Include photos from specified albums
        if album_names:
            for album_name in album_names:
                self.logger.info(f"📥 Including photos from album '{album_name}'")
                for photo_info in self.list_photos_from_album(album_name):
                    if photo_info['id'] not in processed_photo_ids:
                        processed_photo_ids.add(photo_info['id'])
                        yield photo_info
                    else:
                        self.logger.debug(f"⏭️ Skipping duplicate photo: {photo_info['filename']} "
                                          f"(already processed from another album)")

    def verify_albums_exist(self, album_names: list[str]) -> tuple[list[str], list[str], list[str]]:
        """Verify that specified albums exist in iCloud.

        Args:
            album_names: List of album names to verify

        Returns:
            Tuple of (existing_albums, missing_albums)
        """
        if not self._api or not self._api.photos:
            self.logger.error("❌ Not authenticated or photos service unavailable")
            return [], [], album_names

        # Get all albums from iCloud
        albums = self._api.photos.albums
        albums_list = list(albums.values())

        # shared albums
        album_library = self._api.photos.albums['Library']
        albums_shared: AlbumContainer = album_library.service.shared_streams
        albums_shared_list = list(albums_shared.values())

        # Get all available album names
        available_albums = {album.name for album in albums_list + albums_shared_list}

        existing_albums = []
        missing_albums = []

        for album_name in album_names:
            if album_name in available_albums:
                existing_albums.append(album_name)
            else:
                missing_albums.append(album_name)

        if missing_albums:
            self.logger.warning(f"⚠️ Missing albums: {', '.join(missing_albums)}")

        return list(available_albums), existing_albums, missing_albums

    def get_filtered_albums(self, config: BaseConfig) -> t.Iterator[dict[str, t.Any]]:
        """Get albums filtered by configuration settings.

        Args:
            config: Configuration object with album filtering settings

        Yields:
            Album metadata dictionaries matching filter criteria
        """
        if not self._api or not self._api.photos:
            self.logger.error("❌ Not authenticated or photos service unavailable")
            return

        for album_info in self.list_albums():
            is_shared = album_info.get('is_shared', False)
            album_name = album_info['name']

            # Filter by album type (personal vs shared)
            if is_shared:
                if not config.include_shared_albums:
                    continue
                # Check shared album allow-list
                if (config.shared_album_names_to_include and
                        album_name not in config.shared_album_names_to_include):
                    continue
            else:
                if not config.include_personal_albums:
                    continue
                # Check personal album allow-list
                if (config.personal_album_names_to_include and
                        album_name not in config.personal_album_names_to_include):
                    continue

            yield album_info

    def list_photos_from_filtered_albums(
            self,
            config: BaseConfig
    ) -> t.Iterator[dict[str, t.Any]]:
        """List photos from albums based on configuration filtering.

        Args:
            config: Configuration object with album filtering settings
            include_main_library: Whether to include photos from main library

        Yields:
            Photo metadata dictionaries from filtered albums
        """
        processed_photo_ids = set()  # Track to avoid duplicates

        # Include photos from filtered albums
        for album_info in self.get_filtered_albums(config):
            album_name = album_info['name']
            is_shared = album_info.get('is_shared', False)
            album_type = "shared" if is_shared else "personal"

            self.logger.info(f"📥 Including photos from {album_type} album '{album_name}'")

            for photo_info in self.list_photos_from_album(album_name, is_shared=is_shared):
                if photo_info['id'] not in processed_photo_ids:
                    processed_photo_ids.add(photo_info['id'])
                    yield photo_info
                else:
                    self.logger.debug(f"⏭️ Skipping duplicate photo: {photo_info['filename']} "
                                      f"(already processed from another source)")

    def download_photo(self, photo_info: dict[str, t.Any], local_path: str) -> bool:
        """Download a photo to local storage.

        Args:
            photo_info: Photo metadata from list_photos()
            local_path: Local file path to save the photo

        Returns:
            True if download successful, False otherwise
        """
        try:
            photo = photo_info['photo_obj']
            filename = photo_info['filename']

            self.logger.debug(f"📥 Downloading {filename} to {local_path}")

            # Check file size limit if configured
            if self.config.max_file_size_mb > 0:
                size_mb = photo_info.get('size', 0) / (1024 * 1024)
                if size_mb > self.config.max_file_size_mb:
                    self.logger.info(
                        f"⏭️ Skipping {filename} (size: {size_mb:.1f}MB > limit: "
                        f"{self.config.max_file_size_mb}MB)")
                    return False

            if self.config.dry_run:
                self.logger.info(f"🔍 DRY RUN: Would download {filename} to {local_path}")
                return True

            # Download the photo
            download = photo.download()

            # Write to file
            with open(local_path, 'wb') as f:
                f.write(download.raw.read())

            self.logger.debug(f"✅ Downloaded {filename}")
            return True

        except Exception as e:
            self.logger.error(
                f"❌ Error downloading photo {photo_info.get('filename', 'unknown')}: {e}")
            return False

    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self._api is not None and self._api.photos is not None


def cleanup_sessions(max_age_days: int = 30, session_dir: t.Optional[Path] = None) -> None:
    """Standalone utility to clean up expired session files.

    This can be used independently of the iCloudClient class.

    Args:
        max_age_days: Maximum age in days for session files (default: 30)
        session_dir: Optional custom session directory path
    """
    import time
    from .logger import get_logger

    logger = get_logger()

    if session_dir is None:
        session_dir = Path.home() / "iphoto_downloader" / "sessions"

    if not session_dir.exists():
        logger.debug("Session directory does not exist, nothing to clean")
        return

    current_time = time.time()
    cutoff_time = current_time - (max_age_days * 24 * 60 * 60)

    cleaned_count = 0
    total_size = 0

    for session_file in session_dir.iterdir():
        if session_file.is_file():
            try:
                file_mtime = session_file.stat().st_mtime
                if file_mtime < cutoff_time:
                    file_size = session_file.stat().st_size
                    session_file.unlink()
                    cleaned_count += 1
                    total_size += file_size
                    logger.debug(f"Removed expired session file: {session_file.name}")
            except (OSError, FileNotFoundError) as e:
                logger.warning(f"Failed to remove session file {session_file.name}: {e}")

    if cleaned_count > 0:
        logger.info(
            f"🧹 Cleaned up {cleaned_count} expired session files "
            f"({total_size / 1024:.1f} KB freed)"
        )
    else:
        logger.debug("No expired session files found to clean up")
