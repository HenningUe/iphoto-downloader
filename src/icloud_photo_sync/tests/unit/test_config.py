"""Unit tests for configuration module."""

import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

from icloud_photo_sync.config import (
    get_config, BaseConfig, KeyringConfig, EnvOnlyConfig, KEYRING_AVAILABLE)


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
        'ICLOUD_USERNAME', 'ICLOUD_PASSWORD', 'SYNC_DIRECTORY',
        'DRY_RUN', 'LOG_LEVEL', 'MAX_DOWNLOADS', 'MAX_FILE_SIZE_MB'
    ]

    for var in env_vars_to_clean:
        monkeypatch.delenv(var, raising=False)


class TestBaseConfig:
    """Test the BaseConfig abstract class."""

    def test_cannot_instantiate_base_config(self):
        """Test that BaseConfig cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseConfig()  # type: ignore


class TestConfigFactory:
    """Test the get_config factory function."""

    def test_returns_keyring_config_when_available(self):
        """Test that get_config returns KeyringConfig when keyring is available."""
        if KEYRING_AVAILABLE:
            config = get_config()
            assert isinstance(config, KeyringConfig)
        else:
            pytest.skip("Keyring not available")

    def test_returns_env_only_config_when_keyring_unavailable(self):
        """Test that get_config returns EnvOnlyConfig when keyring is not available."""
        with patch('icloud_photo_sync.config.KEYRING_AVAILABLE', False):
            config = get_config()
            assert isinstance(config, EnvOnlyConfig)


class TestKeyringConfig:
    """Test KeyringConfig class."""

    @pytest.fixture
    def mock_keyring(self):
        """Mock keyring module."""
        with patch('icloud_photo_sync.config.keyring') as mock_keyring:
            yield mock_keyring

    def test_init_with_env_variables(self, temp_dir, clean_env):
        """Test initialization with environment variables."""
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

        config = KeyringConfig(str(env_file))

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
            ("icloud-photo-sync", "username"): "keyring@example.com",
            ("icloud-photo-sync", "keyring@example.com"): "keyring-password"
        }.get((service, key))

        env_file = temp_dir / ".env"
        env_file.write_text("SYNC_DIRECTORY=./test_photos\n")

        config = KeyringConfig(str(env_file))

        assert config.icloud_username == "keyring@example.com"
        assert config.icloud_password == "keyring-password"

    def test_env_variables_take_precedence(self, temp_dir, clean_env, mock_keyring):
        """Test that environment variables take precedence over keyring."""
        # Mock keyring to return stored credentials
        mock_keyring.get_password.side_effect = lambda service, key: {
            ("icloud-photo-sync", "username"): "keyring@example.com",
            ("icloud-photo-sync", "keyring@example.com"): "keyring-password"
        }.get((service, key))

        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=env@example.com\n"
            "ICLOUD_PASSWORD=env-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
        )

        config = KeyringConfig(str(env_file))

        assert config.icloud_username == "env@example.com"
        assert config.icloud_password == "env-password"

    def test_validation_fails_without_credentials(self, temp_dir, clean_env, mock_keyring):
        """Test that validation fails when no credentials are provided."""
        # Mock keyring to return no credentials
        mock_keyring.get_password.return_value = None

        env_file = temp_dir / ".env"
        env_file.write_text("SYNC_DIRECTORY=./test_photos\n")

        with pytest.raises(ValueError, match="Configuration errors"):
            KeyringConfig(str(env_file))

    def test_store_credentials_success(self, temp_dir, clean_env, mock_keyring):
        """Test successful credential storage."""
        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=test@example.com\n"
            "ICLOUD_PASSWORD=test-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
        )

        config = KeyringConfig(str(env_file))

        result = config.icloud_store_credentials("new@example.com", "new-password")

        assert result is True
        mock_keyring.set_password.assert_any_call(
            "icloud-photo-sync", "username", "new@example.com")
        mock_keyring.set_password.assert_any_call(
            "icloud-photo-sync", "new@example.com", "new-password")

    def test_store_credentials_failure(self, temp_dir, clean_env, mock_keyring):
        """Test credential storage failure."""
        mock_keyring.set_password.side_effect = Exception("Keyring error")

        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=test@example.com\n"
            "ICLOUD_PASSWORD=test-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
        )

        config = KeyringConfig(str(env_file))

        result = config.icloud_store_credentials("new@example.com", "new-password")

        assert result is False

    def test_has_stored_credentials(self, temp_dir, clean_env, mock_keyring):
        """Test checking for stored credentials."""
        mock_keyring.get_password.side_effect = lambda service, key: {
            ("icloud-photo-sync", "username"): "stored@example.com",
            ("icloud-photo-sync", "stored@example.com"): "stored-password"
        }.get((service, key))

        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=test@example.com\n"
            "ICLOUD_PASSWORD=test-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
        )

        config = KeyringConfig(str(env_file))

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

        config = KeyringConfig(str(env_file))

        result = config.icloud_delete_credentials()

        assert result is True
        mock_keyring.delete_password.assert_any_call("icloud-photo-sync", "stored@example.com")
        mock_keyring.delete_password.assert_any_call("icloud-photo-sync", "username")

    def test_ensure_sync_directory_creates_directory(self, temp_dir, clean_env):
        """Test that ensure_sync_directory creates the sync directory."""
        env_file = temp_dir / ".env"
        sync_dir = temp_dir / "new_photos"
        env_file.write_text(
            f"ICLOUD_USERNAME=test@example.com\n"
            f"ICLOUD_PASSWORD=test-password\n"
            f"SYNC_DIRECTORY={sync_dir}\n"
        )

        config = KeyringConfig(str(env_file))

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

        config = KeyringConfig(str(env_file))

        assert config.get_log_level() == 10  # DEBUG level

    def test_string_representation_hides_sensitive_data(self, temp_dir, clean_env):
        """Test that string representation hides sensitive data."""
        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=test@example.com\n"
            "ICLOUD_PASSWORD=test-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
        )

        config = KeyringConfig(str(env_file))
        config_str = str(config)

        assert "test@example.com" not in config_str
        assert "test-password" not in config_str
        assert "***" in config_str
        assert "keyring" in config_str


class TestEnvOnlyConfig:
    """Test EnvOnlyConfig class."""

    def test_init_with_env_variables(self, temp_dir, clean_env):
        """Test initialization with environment variables."""
        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=test@example.com\n"
            "ICLOUD_PASSWORD=test-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
        )

        config = EnvOnlyConfig(str(env_file))

        assert config.icloud_username == "test@example.com"
        assert config.icloud_password == "test-password"

    def test_store_credentials_always_fails(self, temp_dir, clean_env):
        """Test that store_credentials always returns False for env-only config."""
        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=test@example.com\n"
            "ICLOUD_PASSWORD=test-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
        )

        config = EnvOnlyConfig(str(env_file))

        result = config.store_credentials("new@example.com", "new-password")

        assert result is False

    def test_has_stored_credentials_always_false(self, temp_dir, clean_env):
        """Test that has_stored_credentials always returns False for env-only config."""
        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=test@example.com\n"
            "ICLOUD_PASSWORD=test-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
        )

        config = EnvOnlyConfig(str(env_file))

        assert config.has_stored_credentials() is False

    def test_delete_credentials_always_fails(self, temp_dir, clean_env):
        """Test that delete_credentials always returns False for env-only config."""
        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=test@example.com\n"
            "ICLOUD_PASSWORD=test-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
        )

        config = EnvOnlyConfig(str(env_file))

        result = config.delete_credentials()

        assert result is False

    def test_error_messages_mention_env_only(self, temp_dir, clean_env):
        """Test that error messages mention environment variables only."""
        env_file = temp_dir / ".env"
        env_file.write_text("SYNC_DIRECTORY=./test_photos\n")

        with pytest.raises(ValueError, match="set in environment variable"):
            EnvOnlyConfig(str(env_file))

    def test_string_representation_shows_env_only(self, temp_dir, clean_env):
        """Test that string representation shows env-only source."""
        env_file = temp_dir / ".env"
        env_file.write_text(
            "ICLOUD_USERNAME=test@example.com\n"
            "ICLOUD_PASSWORD=test-password\n"
            "SYNC_DIRECTORY=./test_photos\n"
        )

        config = EnvOnlyConfig(str(env_file))
        config_str = str(config)

        assert "env-only" in config_str
