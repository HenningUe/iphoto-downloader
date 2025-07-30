"""Unit tests for configuration module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from iphoto_downloader.config import (
    BaseConfig,
    KeyringConfig,
    get_config,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def clean_env(monkeypatch):
    """Clean environment variables for testing."""
    # Remove any existing iCloud related environment variables
    env_vars_to_clean = [
        "ICLOUD_USERNAME",
        "ICLOUD_PASSWORD",
        "SYNC_DIRECTORY",
        "DRY_RUN",
        "LOG_LEVEL",
        "MAX_DOWNLOADS",
        "MAX_FILE_SIZE_MB",
        "INCLUDE_PERSONAL_ALBUMS",
        "INCLUDE_SHARED_ALBUMS",
        "PERSONAL_ALBUM_NAMES_TO_INCLUDE",
        "SHARED_ALBUM_NAMES_TO_INCLUDE",
    ]

    for var in env_vars_to_clean:
        monkeypatch.delenv(var, raising=False)


class TestBaseConfig:
    """Test the BaseConfig class."""

    def test_can_instantiate_base_config(self, temp_dir):
        """Test that BaseConfig can be instantiated directly."""
        # BaseConfig requires env_file_path parameter
        env_file = temp_dir / ".env"
        env_file.write_text("LOG_LEVEL=INFO\n")
        config = BaseConfig(env_file)
        assert config is not None


class TestConfigFactory:
    """Test the get_config factory function."""

    def test_returns_keyring_config_when_available(self, clean_env, monkeypatch):
        """Test that get_config returns KeyringConfig when keyring is available."""
        # Set up environment with valid credentials to pass validation
        monkeypatch.setenv("ICLOUD_USERNAME", "test@example.com")
        monkeypatch.setenv("ICLOUD_PASSWORD", "test-password")
        monkeypatch.setenv("ENABLE_PUSHOVER", "false")
        config = get_config()
        assert isinstance(config, KeyringConfig)


@pytest.fixture
def mock_keyring():
    """Mock keyring module."""
    with patch("iphoto_downloader.config.keyring") as mock_keyring:
        yield mock_keyring


class TestKeyringConfig:
    """Test KeyringConfig class."""

    def test_init_with_env_variables(self, temp_dir, clean_env, mock_keyring):
        """Test initialization with environment variables."""
        # Mock keyring to return no credentials to ensure env vars are used
        mock_keyring.get_password.return_value = None

        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=test@example.com\n"
            "ICLOUD_PASSWORD=test-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
            "DRY_RUN=true\n"
            "LOG_LEVEL=DEBUG\n"
            "MAX_DOWNLOADS=100\n"
            "MAX_FILE_SIZE_MB=50\n"
        )

        config = KeyringConfig(env_file)

        assert config.icloud_username == "test@example.com"
        assert config.icloud_password == "test-password"
        assert config.sync_directory.name == "test_photos"
        assert config.dry_run is True
        assert config.log_level == "DEBUG"
        assert config.max_downloads == 100
        assert config.max_file_size_mb == 50

    def test_init_with_keyring_credentials(self, temp_dir, clean_env, mock_keyring):
        """Test initialization with keyring credentials."""
        # Mock keyring to return stored credentials
        mock_keyring.get_password.side_effect = lambda service, key: {
            ("iphoto-downloader", "username"): "keyring@example.com",
            ("iphoto-downloader", "keyring@example.com"): "keyring-password",
        }.get((service, key))

        env_file = temp_dir / ".env"
        env_file.write_text("SYNC_DIRECTORY=./test_photos\n")

        config = KeyringConfig(env_file)

        assert config.icloud_username == "keyring@example.com"
        assert config.icloud_password == "keyring-password"

    def test_env_variables_take_precedence(self, temp_dir, clean_env, mock_keyring):
        """Test that environment variables take precedence over keyring."""
        # Mock keyring to return stored credentials
        mock_keyring.get_password.side_effect = lambda service, key: {
            ("iphoto-downloader", "username"): "keyring@example.com",
            ("iphoto-downloader", "keyring@example.com"): "keyring-password",
        }.get((service, key))

        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=env@example.com\n"
            "ICLOUD_PASSWORD=env-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
        )

        config = KeyringConfig(env_file)

        assert config.icloud_username == "env@example.com"
        assert config.icloud_password == "env-password"

    def test_validation_fails_without_credentials(self, temp_dir, clean_env, mock_keyring):
        """Test that validation fails when no credentials are provided."""
        # Mock keyring to return no credentials
        mock_keyring.get_password.return_value = None

        env_file = temp_dir / ".env"
        env_file.write_text("SYNC_DIRECTORY=./test_photos\n")

        config = KeyringConfig(env_file)
        with pytest.raises(ValueError, match="Configuration errors"):
            config.validate()

    def test_store_credentials_success(self, temp_dir, clean_env, mock_keyring):
        """Test successful credential storage."""
        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=test@example.com\n"
            "ICLOUD_PASSWORD=test-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
        )

        config = KeyringConfig(env_file)

        result = config.icloud_store_credentials("new@example.com", "new-password")

        assert result is True
        mock_keyring.set_password.assert_any_call(
            "iphoto-downloader", "username", "new@example.com"
        )
        mock_keyring.set_password.assert_any_call(
            "iphoto-downloader", "new@example.com", "new-password"
        )

    def test_store_credentials_failure(self, temp_dir, clean_env, mock_keyring):
        """Test credential storage failure."""
        mock_keyring.set_password.side_effect = Exception("Keyring error")

        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=test@example.com\n"
            "ICLOUD_PASSWORD=test-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
        )

        config = KeyringConfig(env_file)

        result = config.icloud_store_credentials("new@example.com", "new-password")

        assert result is False

    def test_has_stored_credentials(self, temp_dir, clean_env, mock_keyring):
        """Test checking for stored credentials."""
        mock_keyring.get_password.side_effect = lambda service, key: {
            ("iphoto-downloader", "username"): "stored@example.com",
            ("iphoto-downloader", "stored@example.com"): "stored-password",
        }.get((service, key))

        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=test@example.com\n"
            "ICLOUD_PASSWORD=test-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
        )

        config = KeyringConfig(env_file)

        assert config.icloud_has_stored_credentials() is True

    def test_delete_credentials_success(self, temp_dir, clean_env, mock_keyring):
        """Test successful credential deletion."""
        mock_keyring.get_password.return_value = "stored@example.com"

        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=test@example.com\n"
            "ICLOUD_PASSWORD=test-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
        )

        config = KeyringConfig(env_file)

        result = config.icloud_delete_credentials()

        assert result is True
        mock_keyring.delete_password.assert_any_call("iphoto-downloader", "stored@example.com")
        mock_keyring.delete_password.assert_any_call("iphoto-downloader", "username")

    def test_ensure_sync_directory_creates_directory(self, temp_dir, clean_env):
        """Test that ensure_sync_directory creates the sync directory."""
        env_file = temp_dir / ".env"
        sync_dir = temp_dir / "new_photos"
        env_file.write_text(
            f"ICLOUD_USERNAME=test@example.com\n"
            f"ICLOUD_PASSWORD=test-password\n"
            f"SYNC_DIRECTORY={sync_dir}\n"
        )

        config = KeyringConfig(env_file)

        assert not sync_dir.exists()
        config.ensure_sync_directory()
        assert sync_dir.exists()

    def test_get_log_level_returns_integer(self, temp_dir, clean_env):
        """Test that get_log_level returns proper integer values."""
        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=test@example.com\n"
            "ICLOUD_PASSWORD=test-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
            "LOG_LEVEL=DEBUG\n"
        )

        config = KeyringConfig(env_file)

        assert config.get_log_level() == 10  # DEBUG level

    def test_string_representation_hides_sensitive_data(self, temp_dir, clean_env, mock_keyring):
        """Test that string representation hides sensitive data."""
        # Mock keyring to return no credentials to ensure env vars are used
        mock_keyring.get_password.return_value = None

        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=test@example.com\n"
            "ICLOUD_PASSWORD=test-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
        )

        config = KeyringConfig(env_file)
        config_str = str(config)

        assert "test@example.com" not in config_str
        assert "test-password" not in config_str
        assert "***" in config_str
        assert "env-only" in config_str


class TestConfigsWithEnvVars:
    """Test EnvOnlyConfig class."""

    def test_init_with_env_variables(self, temp_dir, clean_env):
        """Test initialization with environment variables."""
        env_file = temp_dir / ".env"
        env_file.write_text("SYNC_DIRECTORY=./test_photos\n")

        config = KeyringConfig(env_file)

        assert config.sync_directory == Path("./test_photos")

    def test_string_representation_shows_env_only(self, temp_dir, clean_env, mock_keyring):
        """Test that string representation shows env-only source."""
        # Mock keyring to return no credentials to ensure env vars are used
        mock_keyring.get_password.return_value = None

        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=test@example.com\n"
            "ICLOUD_PASSWORD=test-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
        )

        config = KeyringConfig(env_file)
        config_str = str(config)

        assert "env-only" in config_str


class TestAlbumFilteringConfig:
    """Test album filtering configuration functionality."""

    def test_default_album_settings(self, temp_dir, clean_env):
        """Test default album filtering settings."""
        env_file = temp_dir / ".env"
        env_file.write_text("")

        config = KeyringConfig(env_file)

        assert config.include_personal_albums is True
        assert config.include_shared_albums is True
        assert config.personal_album_names_to_include == []
        assert config.shared_album_names_to_include == []

    def test_album_filtering_boolean_settings(self, temp_dir, clean_env):
        """Test album filtering boolean configuration."""
        env_file = temp_dir / ".env"
        env_file.write_text("INCLUDE_PERSONAL_ALBUMS=false\nINCLUDE_SHARED_ALBUMS=true\n")

        config = KeyringConfig(env_file)

        assert config.include_personal_albums is False
        assert config.include_shared_albums is True

    def test_album_names_parsing(self, temp_dir, clean_env):
        """Test parsing of album name lists."""
        env_file = temp_dir / ".env"
        env_file.write_text(
            "PERSONAL_ALBUM_NAMES_TO_INCLUDE=Album1,Album2,Album3\n"
            "SHARED_ALBUM_NAMES_TO_INCLUDE=Shared1, Shared2 , Shared3\n"
        )

        config = KeyringConfig(env_file)

        assert config.personal_album_names_to_include == ["Album1", "Album2", "Album3"]
        assert config.shared_album_names_to_include == ["Shared1", "Shared2", "Shared3"]

    def test_empty_album_names(self, temp_dir, clean_env):
        """Test handling of empty album name lists."""
        env_file = temp_dir / ".env"
        env_file.write_text("PERSONAL_ALBUM_NAMES_TO_INCLUDE=\nSHARED_ALBUM_NAMES_TO_INCLUDE=,,,\n")

        config = KeyringConfig(env_file)

        assert config.personal_album_names_to_include == []
        assert config.shared_album_names_to_include == []

    def test_album_validation_error_both_disabled(self, temp_dir, clean_env):
        """Test validation error when both album types are disabled."""
        env_file = temp_dir / ".env"
        env_file.write_text("INCLUDE_PERSONAL_ALBUMS=false\nINCLUDE_SHARED_ALBUMS=false\n")

        config = KeyringConfig(env_file)

        with pytest.raises(
            ValueError,
            match="At least one of INCLUDE_PERSONAL_ALBUMS or INCLUDE_SHARED_ALBUMS must be true",
        ):
            config.validate()

    def test_validate_albums_exist_with_missing_albums(self, temp_dir, clean_env):
        """Test album existence validation with missing albums."""
        from unittest.mock import MagicMock

        env_file = temp_dir / ".env"
        env_file.write_text(
            "PERSONAL_ALBUM_NAMES_TO_INCLUDE=Existing,Missing\n"
            "SHARED_ALBUM_NAMES_TO_INCLUDE=SharedExisting,SharedMissing\n"
        )

        config = KeyringConfig(env_file)

        # Mock icloud_client
        mock_client = MagicMock()
        mock_client.verify_albums_exist.side_effect = [
            (
                ["all_albums"],
                ["Existing"],
                ["Missing"],
            ),  # Personal albums - (all, existing, missing)
            (
                ["all_albums"],
                ["SharedExisting"],
                ["SharedMissing"],
            ),  # Shared albums - (all, existing, missing)
        ]

        with pytest.raises(ValueError, match="The following specified albums do not exist"):
            config.validate_albums_exist(mock_client)

    def test_validate_albums_exist_all_found(self, temp_dir, clean_env):
        """Test album existence validation when all albums are found."""
        from unittest.mock import MagicMock

        env_file = temp_dir / ".env"
        env_file.write_text(
            "PERSONAL_ALBUM_NAMES_TO_INCLUDE=Album1,Album2\n"
            "SHARED_ALBUM_NAMES_TO_INCLUDE=Shared1,Shared2\n"
        )

        config = KeyringConfig(env_file)

        # Mock icloud_client
        mock_client = MagicMock()
        mock_client.verify_albums_exist.side_effect = [
            (["all_albums"], ["Album1", "Album2"], []),  # Personal albums - all found
            (["all_albums"], ["Shared1", "Shared2"], []),  # Shared albums - all found
        ]

        # Should not raise an exception
        config.validate_albums_exist(mock_client)
