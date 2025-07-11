"""Configuration management for iCloud Photo Sync Tool."""

import os
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from dotenv import load_dotenv

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    keyring = None
    KEYRING_AVAILABLE = False


class BaseConfig(ABC):
    """Base configuration class with common functionality."""
    
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
        self.icloud_username = self._get_username()
        self.icloud_password = self._get_password()
        
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
            errors.append(self._get_username_error_message())
        
        if not self.icloud_password:
            errors.append(self._get_password_error_message())
        
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
    
    def _get_username(self) -> str | None:
        """Get iCloud username from environment variables first, then from credential store."""
        # First try environment variable
        username = os.getenv('ICLOUD_USERNAME')
        if username:
            return username
        
        # Then try credential store
        return self._get_username_from_store()
    
    def _get_password(self) -> str | None:
        """Get iCloud password from environment variables first, then from credential store."""
        # First try environment variable
        password = os.getenv('ICLOUD_PASSWORD')
        if password:
            return password
        
        # Then try credential store
        return self._get_password_from_store()
    
    def __str__(self) -> str:
        """String representation of config (without sensitive data)."""
        # Determine credential source
        username_source = "env" if os.getenv('ICLOUD_USERNAME') else self._get_credential_source_name()
        password_source = "env" if os.getenv('ICLOUD_PASSWORD') else self._get_credential_source_name()
        
        return (
            f"Config("
            f"username={'***' if self.icloud_username else None} ({username_source}), "
            f"password={'***' if self.icloud_password else None} ({password_source}), "
            f"sync_dir={self.sync_directory}, "
            f"dry_run={self.dry_run}, "
            f"log_level={self.log_level}, "
            f"credential_store={self._get_credential_source_name()}"
            f")"
        )
    
    # Abstract methods to be implemented by subclasses
    @abstractmethod
    def _get_username_from_store(self) -> str | None:
        """Get username from credential store."""
        pass
    
    @abstractmethod
    def _get_password_from_store(self) -> str | None:
        """Get password from credential store."""
        pass
    
    @abstractmethod
    def store_credentials(self, username: str, password: str) -> bool:
        """Store credentials in credential store."""
        pass
    
    @abstractmethod
    def delete_credentials(self) -> bool:
        """Delete credentials from credential store."""
        pass
    
    @abstractmethod
    def has_stored_credentials(self) -> bool:
        """Check if credentials are stored in credential store."""
        pass
    
    @abstractmethod
    def _get_username_error_message(self) -> str:
        """Get error message for missing username."""
        pass
    
    @abstractmethod
    def _get_password_error_message(self) -> str:
        """Get error message for missing password."""
        pass
    
    @abstractmethod
    def _get_credential_source_name(self) -> str:
        """Get the name of the credential source."""
        pass


class KeyringConfig(BaseConfig):
    """Configuration class that uses keyring for credential storage."""
    
    # Keyring service name for storing credentials
    KEYRING_SERVICE_NAME = "icloud-photo-sync"
    
    def _get_username_from_store(self) -> str | None:
        """Get username from keyring."""
        if not KEYRING_AVAILABLE or keyring is None:
            return None
        
        try:
            # Try to get username from keyring (stored as a separate entry)
            stored_username = keyring.get_password(self.KEYRING_SERVICE_NAME, "username")
            return stored_username
        except Exception:
            # Keyring access failed
            return None

    def _get_password_from_store(self) -> str | None:
        """Get password from keyring."""
        if not KEYRING_AVAILABLE or keyring is None or not self.icloud_username:
            return None
        
        try:
            stored_password = keyring.get_password(self.KEYRING_SERVICE_NAME, self.icloud_username)
            return stored_password
        except Exception:
            # Keyring access failed
            return None
    
    def store_credentials(self, username: str, password: str) -> bool:
        """Store iCloud credentials in keyring."""
        if not KEYRING_AVAILABLE or keyring is None:
            return False
        
        try:
            # Store username as a separate entry
            keyring.set_password(self.KEYRING_SERVICE_NAME, "username", username)
            # Store password with username as the key
            keyring.set_password(self.KEYRING_SERVICE_NAME, username, password)
            return True
        except Exception:
            return False
    
    def delete_credentials(self) -> bool:
        """Delete stored credentials from keyring."""
        if not KEYRING_AVAILABLE or keyring is None:
            return False
        
        try:
            # Get stored username first
            stored_username = keyring.get_password(self.KEYRING_SERVICE_NAME, "username")
            if stored_username:
                # Delete password entry
                keyring.delete_password(self.KEYRING_SERVICE_NAME, stored_username)
                # Delete username entry
                keyring.delete_password(self.KEYRING_SERVICE_NAME, "username")
            return True
        except Exception:
            return False
    
    def has_stored_credentials(self) -> bool:
        """Check if credentials are stored in keyring."""
        if not KEYRING_AVAILABLE or keyring is None:
            return False
        
        try:
            stored_username = keyring.get_password(self.KEYRING_SERVICE_NAME, "username")
            if stored_username:
                stored_password = keyring.get_password(self.KEYRING_SERVICE_NAME, stored_username)
                return stored_password is not None
        except Exception:
            pass
        
        return False
    
    def _get_username_error_message(self) -> str:
        """Get error message for missing username."""
        return "ICLOUD_USERNAME is required (set in environment variable or store in keyring)"
    
    def _get_password_error_message(self) -> str:
        """Get error message for missing password."""
        return "ICLOUD_PASSWORD is required (set in environment variable or store in keyring)"
    
    def _get_credential_source_name(self) -> str:
        """Get the name of the credential source."""
        return "keyring"


class EnvOnlyConfig(BaseConfig):
    """Configuration class that only uses environment variables for credentials."""

    def _get_username_from_store(self) -> str | None:
        """Environment-only config doesn't use credential store."""
        return None

    def _get_password_from_store(self) -> str | None:
        """Environment-only config doesn't use credential store."""
        return None
    
    def store_credentials(self, username: str, password: str) -> bool:
        """Environment-only config doesn't support credential storage."""
        return False
    
    def delete_credentials(self) -> bool:
        """Environment-only config doesn't support credential deletion."""
        return False
    
    def has_stored_credentials(self) -> bool:
        """Environment-only config doesn't have stored credentials."""
        return False
    
    def _get_username_error_message(self) -> str:
        """Get error message for missing username."""
        return "ICLOUD_USERNAME is required (set in environment variable)"
    
    def _get_password_error_message(self) -> str:
        """Get error message for missing password."""
        return "ICLOUD_PASSWORD is required (set in environment variable)"
    
    def _get_credential_source_name(self) -> str:
        """Get the name of the credential source."""
        return "env-only"


def get_config(env_file: str | None = None) -> BaseConfig:
    """Factory function to create appropriate config instance.
    
    Args:
        env_file: Path to .env file. If None, uses default .env
        
    Returns:
        KeyringConfig if keyring is available, EnvOnlyConfig otherwise
    """
    if KEYRING_AVAILABLE:
        return KeyringConfig(env_file)
    else:
        return EnvOnlyConfig(env_file)
