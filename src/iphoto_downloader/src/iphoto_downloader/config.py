"""Configuration management for iPhoto Downloader Tool."""

import logging
import os
import sys
from abc import ABC
from pathlib import Path

import keyring
from dotenv import load_dotenv

from auth2fa.pushover_service import PushoverConfig

# Check if keyring is available and functional
try:
    keyring.get_password("test", "test")
    KEYRING_AVAILABLE = True
except Exception:
    KEYRING_AVAILABLE = False


class BaseConfig(ABC):  # noqa
    """Base configuration class with common functionality."""

    # Keyring service name for storing credentials
    ICLOUD_KEYRING_SERVICE_NAME = "iphoto-downloader"
    PUSHOVER_KEYRING_SERVICE_NAME = "pushover-photo-sync"

    def __init__(self, env_file_path: Path) -> None:
        """Initialize configuration.

        Args:
            env_file: Path to .env file. If None, uses default .env
        """
        # Load environment variables from .env file
        load_dotenv(str(env_file_path), override=True)

        # iCloud credentials - try multiple sources
        # Sync settings
        self.sync_directory = Path(os.getenv("SYNC_DIRECTORY", "./photos"))
        self.dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        # Download limits
        self.max_downloads = int(os.getenv("MAX_DOWNLOADS", "0"))
        self.max_file_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", "0"))

        # Pushover notification settings
        self.pushover_device: str | None = os.getenv("PUSHOVER_DEVICE", "")
        self.enable_pushover: bool = os.getenv("ENABLE_PUSHOVER", "true").lower() == "true"

        # Album filtering settings
        self.include_personal_albums: bool = (
            os.getenv("INCLUDE_PERSONAL_ALBUMS", "true").lower() == "true"
        )
        self.include_shared_albums: bool = (
            os.getenv("INCLUDE_SHARED_ALBUMS", "true").lower() == "true"
        )

        # Parse album name lists from comma-separated strings
        personal_albums_str = os.getenv("PERSONAL_ALBUM_NAMES_TO_INCLUDE", "")
        self.personal_album_names_to_include: list[str] = (
            [name.strip() for name in personal_albums_str.split(",") if name.strip()]
            if personal_albums_str
            else []
        )

        personal_albums_str = os.getenv("PERSONAL_ALBUM_NAMES_TO_EXCLUDE", "")
        self.personal_album_names_to_exclude: list[str] = (
            [name.strip() for name in personal_albums_str.split(",") if name.strip()]
            if personal_albums_str
            else []
        )

        shared_albums_str = os.getenv("SHARED_ALBUM_NAMES_TO_INCLUDE", "")
        self.shared_album_names_to_include: list[str] = (
            [name.strip() for name in shared_albums_str.split(",") if name.strip()]
            if shared_albums_str
            else []
        )

        shared_albums_str = os.getenv("SHARED_ALBUM_NAMES_TO_EXCLUDE", "")
        self.shared_album_names_to_exclude: list[str] = (
            [name.strip() for name in shared_albums_str.split(",") if name.strip()]
            if shared_albums_str
            else []
        )

        # Execution mode settings
        self.execution_mode = os.getenv("EXECUTION_MODE", "single").lower()
        self.sync_interval_minutes = float(os.getenv("SYNC_INTERVAL_MINUTES", "2"))
        self.maintenance_interval_hours = float(os.getenv("MAINTENANCE_INTERVAL_HOURS", "1"))

        # Multi-instance control settings
        self.allow_multi_instance: bool = (
            os.getenv("ALLOW_MULTI_INSTANCE", "false").lower() == "true"
        )

        # Database path configuration
        self.database_parent_directory = os.getenv("DATABASE_PARENT_DIRECTORY", ".data")

        # Operating mode configuration for delivery artifacts management
        self.operating_mode = get_operating_mode()

    @property
    def icloud_username(self) -> str:
        """Get iCloud username from credential store."""
        # First check environment variables
        env_username = os.getenv("ICLOUD_USERNAME")
        if env_username:
            return env_username

        # Fall back to keyring
        v = self._icloud_get_username_from_store()
        if not v and self.enable_pushover:
            raise ValueError("icloud_username is required (store in keyring)")
        return v or ""

    @property
    def icloud_password(self) -> str:
        """Get iCloud password from credential store."""
        # First check environment variables
        env_password = os.getenv("ICLOUD_PASSWORD")
        if env_password:
            return env_password

        # Fall back to keyring
        v = self._icloud_get_password_from_store()
        if not v and self.enable_pushover:
            raise ValueError("icloud_password is required (store in keyring)")
        return v or ""

    @property
    def pushover_user_key(self) -> str:
        """Get Pushover user key from environment variables or credential store."""
        # Fall back to keyring
        v = self._pushover_get_user_key_from_store()
        if not v and self.enable_pushover:
            raise ValueError("pushover_user_key is required (store in keyring)")
        return v or ""

    @property
    def pushover_api_token(self) -> str:
        """Get Pushover API token from environment variables or credential store."""
        # Fall back to keyring
        v = self._pushover_get_api_token_from_store()
        if not v and self.enable_pushover:
            raise ValueError("pushover_api_token is required (store in keyring)")
        return v or ""

    @property
    def database_path(self) -> Path:
        """Get the full database path with environment variable expansion."""
        # Expand environment variables in the database parent directory
        expanded_path = os.path.expandvars(self.database_parent_directory)

        # Cross-platform environment variable mapping
        if "%LOCALAPPDATA%" in expanded_path and os.name != "nt":
            # Map Windows %LOCALAPPDATA% to Linux equivalent
            home = os.path.expanduser("~")
            expanded_path = expanded_path.replace("%LOCALAPPDATA%", f"{home}/.local/share")

        database_dir = Path(expanded_path)

        # Handle relative vs absolute paths
        if not database_dir.is_absolute():
            # Relative paths are relative to the sync directory
            database_dir = self.sync_directory / database_dir

        # Ensure database directory exists
        database_dir.mkdir(parents=True, exist_ok=True)

        # Return full path to the database file
        return database_dir / "deletion_tracker.db"

    def validate(self) -> None:
        """Validate configuration settings."""
        errors = []

        # Check iCloud credentials without triggering exceptions
        try:
            username = self.icloud_username
            if not username:
                errors.append("icloud_username is required (store in keyring)")
        except ValueError:
            errors.append("icloud_username is required (store in keyring)")

        try:
            password = self.icloud_password
            if not password:
                errors.append("icloud_password is required (store in keyring)")
        except ValueError:
            errors.append("icloud_password is required (store in keyring)")

        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            errors.append(f"Invalid LOG_LEVEL: {self.log_level}")

        # Validate Pushover settings if enabled
        if self.enable_pushover:
            try:
                api_token = self.pushover_api_token
                if not api_token:
                    errors.append("PUSHOVER_API_TOKEN is required when ENABLE_PUSHOVER=true")
            except ValueError:
                errors.append("PUSHOVER_API_TOKEN is required when ENABLE_PUSHOVER=true")

            try:
                user_key = self.pushover_user_key
                if not user_key:
                    errors.append("PUSHOVER_USER_KEY is required when ENABLE_PUSHOVER=true")
            except ValueError:
                errors.append("PUSHOVER_USER_KEY is required when ENABLE_PUSHOVER=true")

        # Validate album filtering settings
        if not self.include_personal_albums and not self.include_shared_albums:
            errors.append(
                "At least one of INCLUDE_PERSONAL_ALBUMS or INCLUDE_SHARED_ALBUMS must be true"
            )

        # Validate execution mode settings
        if self.execution_mode not in ["single", "continuous"]:
            errors.append(
                f"Invalid EXECUTION_MODE: {self.execution_mode}. Must be 'single' or 'continuous'"
            )

        if self.sync_interval_minutes <= 0:
            errors.append("SYNC_INTERVAL_MINUTES must be bigger than 0 minutes")

        if self.maintenance_interval_hours <= 0:
            errors.append("MAINTENANCE_INTERVAL_HOURS must be bigger than 0 hours")

        if self.maintenance_interval_hours * 60 <= self.sync_interval_minutes:
            errors.append(
                "MAINTENANCE_INTERVAL_HOURS * 60 must be bigger than SYNC_INTERVAL_MINUTES"
            )

        # Validate multi-instance control settings
        if not isinstance(self.allow_multi_instance, bool):
            errors.append(
                f"ALLOW_MULTI_INSTANCE must be a boolean (true/false), got: "
                f"{self.allow_multi_instance}"
            )

        # Validate database path configuration
        try:
            database_path = self.database_path
            # Test if the directory is accessible and writable
            database_path.parent.mkdir(parents=True, exist_ok=True)
            if not os.access(database_path.parent, os.W_OK):
                errors.append(f"Database directory is not writable: {database_path.parent}")
        except (OSError, PermissionError, ValueError) as e:
            errors.append(f"Invalid database path configuration: {e}")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

    def ensure_sync_directory(self) -> None:
        """Create sync directory if it doesn't exist."""
        self.sync_directory.mkdir(parents=True, exist_ok=True)

    def get_log_level(self, fallback_lvl: int = logging.INFO) -> int:
        """Get logging level as integer."""
        return getattr(logging, self.log_level, fallback_lvl)

    def get_pushover_config(self) -> "PushoverConfig | None":
        """Get Pushover configuration if enabled and properly configured."""
        if not self.enable_pushover:
            return None

        if not self.pushover_api_token or not self.pushover_user_key:
            return None

        return PushoverConfig(
            api_token=self.pushover_api_token,
            user_key=self.pushover_user_key,
            device=self.pushover_device,
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
                self.ICLOUD_KEYRING_SERVICE_NAME, self.icloud_username
            )
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
                self.ICLOUD_KEYRING_SERVICE_NAME, stored_username
            )
            return stored_password is not None
        return False

    def _pushover_get_user_key_from_store(self) -> str | None:
        """Get pushover user key from keyring."""
        try:
            # Try to get user key from keyring (stored as a separate entry)
            stored_user_key = keyring.get_password(self.PUSHOVER_KEYRING_SERVICE_NAME, "user_key")
            return stored_user_key
        except Exception:
            # Keyring access failed
            return None

    def _pushover_get_api_token_from_store(self) -> str | None:
        """Get pushover API token from keyring."""
        try:
            stored_api_token = keyring.get_password(
                self.PUSHOVER_KEYRING_SERVICE_NAME, self.pushover_user_key
            )
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
                self.PUSHOVER_KEYRING_SERVICE_NAME, stored_user_key
            )
            return stored_api_token is not None
        return False

    def __str__(self) -> str:
        """String representation of config (without sensitive data)."""
        # Safely get pushover properties
        try:
            pushover_user_key = self.pushover_user_key
            pushover_user_key_display = "***" if pushover_user_key else None
        except ValueError:
            pushover_user_key_display = None

        try:
            pushover_api_token = self.pushover_api_token
            pushover_api_token_display = "***" if pushover_api_token else None
        except ValueError:
            pushover_api_token_display = None

        credential_store = "keyring"

        # Check if credentials come from environment variables
        if os.getenv("ICLOUD_USERNAME") and not self._icloud_get_username_from_store():
            credential_store = "env-only"

        return (
            f"Config("
            f"icloud_username={'***' if self.icloud_username else None}, "
            f"icloud_password={'***' if self.icloud_password else None}, "
            f"pushover is {'enabled' if self.enable_pushover else 'disabled'}, "
            f"pushover_device={self.pushover_device}, "
            f"pushover_user_key={pushover_user_key_display}, "
            f"pushover_api_token={pushover_api_token_display}, "
            f"sync_dir={self.sync_directory}, "
            f"dry_run={self.dry_run}, "
            f"log_level={self.log_level}, "
            f"credential_store={credential_store}"
            f")"
        )

    def validate_albums_exist(self, icloud_client) -> None:
        """Validate that specified album names actually exist in iCloud.

        Args:
            icloud_client: Authenticated ICloudClient instance

        Raises:
            ValueError: If any specified albums don't exist
        """
        from iphoto_downloader.sync import ICloudClient  # noqa

        missing_albums = []
        icloud_client_typed: ICloudClient = icloud_client
        cst_props_to_check = []

        if self.include_personal_albums:
            cst_props_to_check.extend(
                [
                    dict(name="personal_album_names_to_include", album_type="personal"),
                    dict(name="personal_album_names_to_exclude", album_type="personal"),
                ]
            )
        if self.include_shared_albums:
            cst_props_to_check.extend(
                [
                    dict(name="shared_album_names_to_include", album_type="shared"),
                    dict(name="shared_album_names_to_exclude", album_type="shared"),
                ]
            )

        for prop in cst_props_to_check:
            album_names = getattr(self, prop["name"])
            if not album_names:
                continue
            album_type: str = prop["album_type"]
            available_albums, _, current_missing = icloud_client_typed.verify_albums_exist(
                album_names
            )
            if current_missing:
                missing_albums.extend(
                    [f"{album_type.capitalize()}: {name}" for name in current_missing]
                )
                missing_albums.append(
                    f"(Note: existing {album_type} albums: {', '.join(available_albums)})"
                )

        if missing_albums:
            raise ValueError(
                f"The following specified albums do not exist: {', '.join(missing_albums)}"
            )


class KeyringConfig(BaseConfig):
    """Configuration class that uses keyring for storing sensitive data."""


def get_operating_mode() -> str:
    """Get and validate operating mode configuration.

    Returns:
        Operating mode: "InDevelopment" or "Delivered"
    """
    # Check if running from PyInstaller executable
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running from PyInstaller executable - default to 'Delivered'
        default_mode = "Delivered"
    else:
        # Running from source - default to 'InDevelopment'
        default_mode = "InDevelopment"

    mode = os.getenv("OPERATING_MODE", default_mode)

    # Validate operating mode
    valid_modes = ["InDevelopment", "Delivered"]
    valid_modes = [m.lower() for m in valid_modes]
    mode = mode.strip().lower()
    if mode not in valid_modes:
        mode = default_mode  # Use appropriate default

    return mode.lower()


def get_app_data_folder_path() -> Path:
    """Get the App's data folder path for 'Delivered' mode.

    Returns:
        Path to the App's data folder based on the operating system
    """
    if get_operating_mode() == "delivered":
        if os.name == "nt":  # Windows
            # Use %USERPROFILE%/iphoto_downloader_settings
            base_path = Path(os.getenv("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")))
        elif os.name == "posix":
            # Linux/Unix
            # Use ~/.config/iphoto_downloader
            base_path = Path(os.path.expanduser("~/.config"))
        else:
            raise OSError(f"Unsupported OS: {os.name}")
        base_path /= "iphoto_downloader"
    else:
        # In development mode, use current working directory
        base_path = Path.cwd()

    return base_path


def get_settings_folder_path() -> Path:
    """Get the settings folder path for 'Delivered' mode.

    Returns:
        Path to the settings folder based on the operating system
    """
    if get_operating_mode() == "delivered":
        base_path = get_app_data_folder_path()
        base_path /= "settings"
    else:
        # In development mode, use current working directory
        base_path = Path.cwd()
    return base_path


def get_settings_env_file_path() -> Path:
    """Get the path to the settings .env file.

    First searches for .env in current directory, then falls back to
    settings.ini in system user settings directory.

    Returns:
        Path to the configuration file (.env or settings.ini)
    """
    settings_ini_file_p_options: list[Path] = []

    # First try current directory's .env file
    settings_ini_file_p = Path(".env")
    settings_ini_file_p_options.append(settings_ini_file_p)

    # Create the iphoto_downloader subdirectory path
    iphoto_downloader_settings_dir = get_settings_folder_path()
    settings_ini_file_p = iphoto_downloader_settings_dir / "settings.ini"
    settings_ini_file_p_options.append(settings_ini_file_p)

    settings_ini_file_p = None
    for loop_file_p in settings_ini_file_p_options:
        if loop_file_p.is_dir():
            raise OSError(f"Expected file but found directory: {loop_file_p}")
        if loop_file_p.exists():
            settings_ini_file_p = loop_file_p
            break
    if not settings_ini_file_p:
        msg = (
            "Warning: No configuration file found. Options are: "
            f"{', '.join(map(str, settings_ini_file_p_options))}"
        )
        raise OSError(msg)
    return settings_ini_file_p


def get_config() -> BaseConfig:
    """Factory function to create appropriate config instance.

    Args:
        env_file_path: Optional path to .env file. If None, uses default discovery

    Returns:
        KeyringConfig instance
    """
    env_file_path = get_settings_env_file_path()
    return KeyringConfig(env_file_path)
