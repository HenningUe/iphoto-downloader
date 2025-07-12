"""iCloud authentication and API interaction."""

import typing as t
from pathlib import Path
from pyicloud import PyiCloudService
from pyicloud.exceptions import PyiCloudFailedLoginException, PyiCloudAPIResponseException

from .config import BaseConfig
from .logger import get_logger


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
        self.session_dir = Path.home() / "icloud_photo_sync" / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)

    @property
    def logger(self):
        """Get the global logger instance."""
        return get_logger()
    
    def authenticate(self) -> bool:
        """Authenticate with iCloud with session persistence.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
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
            
            # Test the connection by accessing photos
            if self._api.photos:
                self.logger.info("✅ Successfully authenticated with iCloud")
                return True
            else:
                self.logger.error("❌ Failed to access iCloud Photos")
                return False
                
        except PyiCloudFailedLoginException as e:
            self.logger.error(f"❌ iCloud login failed: {e}")
            return False
        except PyiCloudAPIResponseException as e:
            self.logger.error(f"❌ iCloud API error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Unexpected error during authentication: {e}")
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
    
    def handle_2fa(self, code: str) -> bool:
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
            self.logger.error(f"❌ Error during 2FA verification: {e}")
            return False
    
    def trust_session(self) -> bool:
        """Request to trust the current session to avoid future 2FA.
        
        Returns:
            True if session was successfully trusted, False otherwise
        """
        if not self._api:
            return False
        
        try:
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
        except Exception as e:
            self.logger.error(f"❌ Error trusting session: {e}")
            return False
    
    def list_photos(self) -> t.Iterator[dict[str, t.Any]]:
        """List all photos from iCloud.
        
        Yields:
            Photo metadata dictionaries
        """
        if not self._api or not self._api.photos:
            self.logger.error("❌ Not authenticated or photos service unavailable")
            return
        
        try:
            self.logger.info("📥 Fetching photo list from iCloud...")
            
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
                        'photo_obj': photo  # Keep reference for downloading
                    }
                    
                    yield photo_info
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error processing photo {i}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"❌ Error fetching photos from iCloud: {e}")
    
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
                    self.logger.info(f"⏭️ Skipping {filename} (size: {size_mb:.1f}MB > limit: {self.config.max_file_size_mb}MB)")
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
            self.logger.error(f"❌ Error downloading photo {photo_info.get('filename', 'unknown')}: {e}")
            return False
    
    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return self._api is not None and self._api.photos is not None
