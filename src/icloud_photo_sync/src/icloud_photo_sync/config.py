"""Configuration management for iCloud Photo Sync Tool."""

import os
import logging
from pathlib import Path
from abc import ABC
from typing import TYPE_CHECKING
from dotenv import load_dotenv
import keyring

if TYPE_CHECKING:
    from auth2fa.pushover_service import PushoverConfig


class BaseConfig(ABC):
    """Base configuration class with common functionality."""

    # Keyring service name for storing credentials
    ICLOUD_KEYRING_SERVICE_NAME = "icloud-photo-sync"
    PUSHOVER_KEYRING_SERVICE_NAME = "pushover-photo-sync"

    def __init__(self, env_file: str | None = None) -> None:
        """Initialize configuration.

        Args:
            env_file: Path to .env file. If None, uses default .env
        """
        # Load environment variables from .env file
        env_path = env_file or '.env'
        if Path(env_path).exists():
            load_dotenv(env_path)

        # iCloud credentials - try multiple sources
        # Sync settings
        self.sync_directory = Path(os.getenv('SYNC_DIRECTORY', './photos'))
        self.dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

        # Download limits
        self.max_downloads = int(os.getenv('MAX_DOWNLOADS', '0'))
        self.max_file_size_mb = int(os.getenv('MAX_FILE_SIZE_MB', '0'))

        # Pushover notification settings
        self.pushover_device: str | None = os.getenv('PUSHOVER_DEVICE', '')
        self.enable_pushover: bool = os.getenv('ENABLE_PUSHOVER', 'true').lower() == 'true'

    @property
    def icloud_username(self) -> str:
        """Get iCloud username from environment variables or credential store."""
        v = self._icloud_get_username_from_store()
        if not v and self.enable_pushover:
            raise ValueError("icloud_username is required (store in keyring)")
        return v or ""

    @property
    def icloud_password(self) -> str:
        """Get iCloud password from environment variables or credential store."""
        v = self._icloud_get_password_from_store()
        if not v and self.enable_pushover:
            raise ValueError("icloud_password is required (store in keyring)")
        return v or ""

    @property
    def pushover_user_key(self) -> str:
        """Get Pushover user key from environment variables or credential store."""
        v = self._pushover_get_user_key_from_store()
        if not v:
            raise ValueError("pushover_user_key is required (store in keyring)")
        return v

    @property
    def pushover_api_token(self) -> str:
        """Get Pushover API token from environment variables or credential store."""
        v = self._pushover_get_api_token_from_store()
        if not v:
            raise ValueError("pushover_api_token is required (store in keyring)")
        return v

    def validate(self) -> None:
        """Validate configuration settings."""
        errors = []

        if not self.icloud_username:
            errors.append("icloud_username is required (store in keyring)")

        if not self.icloud_password:
            errors.append("icloud_password is required (store in keyring)")

        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
            errors.append(f"Invalid LOG_LEVEL: {self.log_level}")

        # Validate Pushover settings if enabled
        if self.enable_pushover:
            if not self.pushover_api_token:
                errors.append("PUSHOVER_API_TOKEN is required when ENABLE_PUSHOVER=true")
            if not self.pushover_user_key:
                errors.append("PUSHOVER_USER_KEY is required when ENABLE_PUSHOVER=true")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

    def ensure_sync_directory(self) -> None:
        """Create sync directory if it doesn't exist."""
        self.sync_directory.mkdir(parents=True, exist_ok=True)

    def get_log_level(self) -> int:
        """Get logging level as integer."""
        return getattr(logging, self.log_level, logging.INFO)

    def get_pushover_config(self) -> 'PushoverConfig | None':
        """Get Pushover configuration if enabled and properly configured."""
        if not self.enable_pushover:
            return None

        if not self.pushover_api_token or not self.pushover_user_key:
            return None

        from auth2fa.pushover_service import PushoverConfig
        return PushoverConfig(
            api_token=self.pushover_api_token,
            user_key=self.pushover_user_key,
            device=self.pushover_device
        )

    def _icloud_get_username_from_store(self) -> str | None:
        """Get username from keyring."""
        try:
            # Try to get username from keyring (stored as a separate entry)
            stored_username = keyring.get_password(self.ICLOUD_KEYRING_SERVICE_NAME, "username")
            return stored_username
        except Exception:
            # Keyring access failed
            return None

    def _icloud_get_password_from_store(self) -> str | None:
        """Get password from keyring."""
        try:
            stored_password = keyring.get_password(
                self.ICLOUD_KEYRING_SERVICE_NAME, self.icloud_username)
            return stored_password
        except Exception:
            # Keyring access failed
            return None

    def icloud_store_credentials(self, username: str, password: str) -> bool:
        """Store iCloud credentials in keyring."""
        try:
            # Store username as a separate entry
            keyring.set_password(self.ICLOUD_KEYRING_SERVICE_NAME, "username", username)
            # Store password with username as the key
            keyring.set_password(self.ICLOUD_KEYRING_SERVICE_NAME, username, password)
            return True
        except Exception:
            return False

    def icloud_delete_credentials(self) -> bool:
        """Delete stored credentials from keyring."""
        try:
            # Get stored username first
            stored_username = keyring.get_password(self.ICLOUD_KEYRING_SERVICE_NAME, "username")
            if stored_username:
                # Delete password entry
                keyring.delete_password(self.ICLOUD_KEYRING_SERVICE_NAME, stored_username)
                # Delete username entry
                keyring.delete_password(self.ICLOUD_KEYRING_SERVICE_NAME, "username")
            return True
        except Exception:
            return False

    def icloud_has_stored_credentials(self) -> bool:
        """Check if credentials are stored in keyring."""
        stored_username = keyring.get_password(self.ICLOUD_KEYRING_SERVICE_NAME, "username")
        if stored_username:
            stored_password = keyring.get_password(
                self.ICLOUD_KEYRING_SERVICE_NAME, stored_username)
            return stored_password is not None
        return False

    def _pushover_get_user_key_from_store(self) -> str | None:
        """Get pushover user key from keyring."""
        try:
            # Try to get user key from keyring (stored as a separate entry)
            stored_user_key = keyring.get_password(
                self.PUSHOVER_KEYRING_SERVICE_NAME, "user_key")
            return stored_user_key
        except Exception:
            # Keyring access failed
            return None

    def _pushover_get_api_token_from_store(self) -> str | None:
        """Get pushover API token from keyring."""
        try:
            stored_api_token = keyring.get_password(
                self.PUSHOVER_KEYRING_SERVICE_NAME, self.pushover_user_key)
            return stored_api_token
        except Exception:
            # Keyring access failed
            return None

    def pushover_store_credentials(self, user_key: str, api_token: str) -> bool:
        """Store pushover credentials in keyring."""
        try:
            # Store user key as a separate entry
            keyring.set_password(self.PUSHOVER_KEYRING_SERVICE_NAME, "user_key", user_key)
            # Store API token with user key as the key
            keyring.set_password(self.PUSHOVER_KEYRING_SERVICE_NAME, user_key, api_token)
            return True
        except Exception:
            return False

    def pushover_delete_credentials(self) -> bool:
        """Delete stored credentials from keyring."""
        try:
            # Get stored user key first
            stored_user_key = keyring.get_password(self.PUSHOVER_KEYRING_SERVICE_NAME, "user_key")
            if stored_user_key:
                # Delete API token entry
                keyring.delete_password(self.PUSHOVER_KEYRING_SERVICE_NAME, stored_user_key)
                # Delete user key entry
                keyring.delete_password(self.PUSHOVER_KEYRING_SERVICE_NAME, "user_key")
            return True
        except Exception:
            return False

    def pushover_has_stored_credentials(self) -> bool:
        """Check if credentials are stored in keyring."""
        stored_user_key = keyring.get_password(self.PUSHOVER_KEYRING_SERVICE_NAME, "user_key")
        if stored_user_key:
            stored_api_token = keyring.get_password(
                self.PUSHOVER_KEYRING_SERVICE_NAME, stored_user_key)
            return stored_api_token is not None
        return False

    def __str__(self) -> str:
        """String representation of config (without sensitive data)."""

        return (
            f"Config("
            f"icloud_username={'***' if self.icloud_username else None}, "
            f"icloud_password={'***' if self.icloud_password else None}, "
            f"pushover is {'enabled' if self.enable_pushover else 'disabled'}, "
            f"pushover_device={self.pushover_device}, "
            f"pushover_user_key={'***' if self.pushover_user_key else None}, "
            f"pushover_api_token={'***' if self.pushover_api_token else None}, "
            f"sync_dir={self.sync_directory}, "
            f"dry_run={self.dry_run}, "
            f"log_level={self.log_level}, "
            f"credential_store=keyring"
            f")"
        )


class KeyringConfig(BaseConfig):
    """Configuration class that uses keyring for storing sensitive data."""


def get_config() -> BaseConfig:
    """Factory function to create appropriate config instance.

    Returns:
        KeyringConfig if keyring is available, EnvOnlyConfig otherwise
    """
    return KeyringConfig()
