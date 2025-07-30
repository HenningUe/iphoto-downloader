"""Integration tests for multi-instance control with configuration system."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from iphoto_downloader.config import BaseConfig
from iphoto_downloader.instance_manager import InstanceManager


class TestMultiInstanceConfigIntegration(unittest.TestCase):
    """Integration tests for multi-instance control with configuration."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_env_file = Path(self.temp_dir) / ".env"

    def tearDown(self):
        """Clean up test environment."""
        # Clean up temp files
        if self.temp_env_file.exists():
            self.temp_env_file.unlink()
        try:
            os.rmdir(self.temp_dir)
        except OSError:
            pass

    def create_env_file(self, content: str):
        """Create a .env file with given content."""
        self.temp_env_file.write_text(content)

    @patch("iphoto_downloader.config.get_operating_mode")
    def test_config_default_multi_instance_false(self, mock_get_operating_mode):
        """Test that default multi-instance setting is False."""
        mock_get_operating_mode.return_value = "InDevelopment"

        self.create_env_file("""
SYNC_DIRECTORY=./photos
DRY_RUN=false
""")

        config = BaseConfig(self.temp_env_file)

        self.assertFalse(config.allow_multi_instance)

    @patch("iphoto_downloader.config.get_operating_mode")
    def test_config_multi_instance_true(self, mock_get_operating_mode):
        """Test multi-instance setting when explicitly set to true."""
        mock_get_operating_mode.return_value = "InDevelopment"

        self.create_env_file("""
SYNC_DIRECTORY=./photos
DRY_RUN=false
ALLOW_MULTI_INSTANCE=true
""")

        config = BaseConfig(self.temp_env_file)

        self.assertTrue(config.allow_multi_instance)

    @patch("iphoto_downloader.config.get_operating_mode")
    def test_config_multi_instance_false_explicit(self, mock_get_operating_mode):
        """Test multi-instance setting when explicitly set to false."""
        mock_get_operating_mode.return_value = "InDevelopment"

        self.create_env_file("""
SYNC_DIRECTORY=./photos
DRY_RUN=false
ALLOW_MULTI_INSTANCE=false
""")

        config = BaseConfig(self.temp_env_file)

        self.assertFalse(config.allow_multi_instance)

    @patch("iphoto_downloader.config.get_operating_mode")
    def test_config_multi_instance_case_insensitive(self, mock_get_operating_mode):
        """Test that multi-instance setting is case insensitive."""
        mock_get_operating_mode.return_value = "InDevelopment"

        test_cases = ["TRUE", "True", "tRuE", "FALSE", "False", "fAlSe"]
        expected_results = [True, True, True, False, False, False]

        for value, expected in zip(test_cases, expected_results, strict=False):
            with self.subTest(value=value):
                self.create_env_file(f"""
SYNC_DIRECTORY=./photos
DRY_RUN=false
ALLOW_MULTI_INSTANCE={value}
""")

                config = BaseConfig(self.temp_env_file)
                self.assertEqual(config.allow_multi_instance, expected)

    @patch("iphoto_downloader.config.get_operating_mode")
    @patch("keyring.get_password")
    def test_config_validation_includes_multi_instance(self, mock_keyring, mock_get_operating_mode):
        """Test that configuration validation includes multi-instance validation."""
        mock_get_operating_mode.return_value = "InDevelopment"
        mock_keyring.return_value = "test_value"

        # Test with valid boolean value (should not raise)
        self.create_env_file("""
SYNC_DIRECTORY=./photos
DRY_RUN=false
ALLOW_MULTI_INSTANCE=true
ENABLE_PUSHOVER=false
""")

        config = BaseConfig(self.temp_env_file)

        # Mock the credential methods to avoid validation errors
        with (
            patch.object(config, "icloud_has_stored_credentials", return_value=True),
            patch.object(config, "pushover_has_stored_credentials", return_value=True),
            patch.object(config, "_icloud_get_username_from_store", return_value="test"),
            patch.object(config, "_icloud_get_password_from_store", return_value="test"),
        ):
            try:
                config.validate()  # Should not raise an exception
            except ValueError as e:
                # If there's a validation error, it shouldn't be about multi-instance
                self.assertNotIn("ALLOW_MULTI_INSTANCE", str(e))

    @patch("iphoto_downloader.instance_manager.get_logger")
    @patch("iphoto_downloader.instance_manager.get_app_data_folder_path")
    @patch("iphoto_downloader.config.get_operating_mode")
    def test_instance_manager_integration_with_config(
        self, mock_get_operating_mode, mock_get_app_data, mock_get_logger
    ):
        """Test InstanceManager integration with configuration."""
        mock_get_operating_mode.return_value = "InDevelopment"
        mock_get_app_data.return_value = Path(self.temp_dir)
        mock_get_logger.return_value = Mock()

        # Test with multi-instance disabled
        self.create_env_file("""
SYNC_DIRECTORY=./photos
ALLOW_MULTI_INSTANCE=false
""")

        config = BaseConfig(self.temp_env_file)
        instance_manager = InstanceManager(config.allow_multi_instance)

        self.assertFalse(instance_manager.allow_multi_instance)

        # Test with multi-instance enabled
        self.create_env_file("""
SYNC_DIRECTORY=./photos
ALLOW_MULTI_INSTANCE=true
""")

        config = BaseConfig(self.temp_env_file)
        instance_manager = InstanceManager(config.allow_multi_instance)

        self.assertTrue(instance_manager.allow_multi_instance)

    @patch("iphoto_downloader.instance_manager.get_logger")
    @patch("iphoto_downloader.instance_manager.get_app_data_folder_path")
    @patch("iphoto_downloader.config.get_operating_mode")
    def test_multi_instance_logging_behavior(
        self, mock_get_operating_mode, mock_get_app_data, mock_get_logger
    ):
        """Test that multi-instance behavior is properly logged."""
        mock_get_operating_mode.return_value = "InDevelopment"
        mock_get_app_data.return_value = Path(self.temp_dir)
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Test multi-instance enabled logging
        self.create_env_file("""
SYNC_DIRECTORY=./photos
ALLOW_MULTI_INSTANCE=true
""")

        config = BaseConfig(self.temp_env_file)
        instance_manager = InstanceManager(config.allow_multi_instance)

        result = instance_manager.check_and_acquire_lock()

        self.assertTrue(result)
        mock_logger.info.assert_called_with(
            "Multi-instance mode enabled - not checking for existing instances"
        )

    @patch("iphoto_downloader.config.get_operating_mode")
    def test_invalid_multi_instance_values(self, mock_get_operating_mode):
        """Test that invalid multi-instance values default to False."""
        mock_get_operating_mode.return_value = "InDevelopment"

        invalid_values = ["yes", "no", "1", "0", "enabled", "disabled", ""]

        for invalid_value in invalid_values:
            with self.subTest(value=invalid_value):
                self.create_env_file(f"""
SYNC_DIRECTORY=./photos
ALLOW_MULTI_INSTANCE={invalid_value}
""")

                config = BaseConfig(self.temp_env_file)
                # Invalid values should default to False
                self.assertFalse(config.allow_multi_instance)


if __name__ == "__main__":
    unittest.main()
