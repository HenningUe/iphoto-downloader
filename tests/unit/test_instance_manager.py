"""Unit tests for multi-instance control functionality."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from iphoto_downloader.instance_manager import (
    InstanceManager,
    enforce_single_instance,
    validate_multi_instance_config,
)


class TestInstanceManager(unittest.TestCase):
    """Test cases for InstanceManager class."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for lock files
        self.temp_dir = tempfile.mkdtemp()
        self.test_lock_file = Path(self.temp_dir) / "test_lock.lock"

        # Mock logger to avoid issues during testing
        self.mock_logger = Mock()

    def tearDown(self):
        """Clean up test environment."""
        # Clean up any lock files
        if self.test_lock_file.exists():
            self.test_lock_file.unlink()

        # Clean up temp directory
        try:
            os.rmdir(self.temp_dir)
        except OSError:
            pass

    @patch("iphoto_downloader.instance_manager.get_logger")
    @patch("iphoto_downloader.instance_manager.get_app_data_folder_path")
    def test_init_with_app_data_folder(self, mock_get_app_data, mock_get_logger):
        """Test initialization with app data folder available."""
        mock_get_logger.return_value = self.mock_logger
        mock_get_app_data.return_value = Path(self.temp_dir)

        manager = InstanceManager(allow_multi_instance=False)

        self.assertFalse(manager.allow_multi_instance)
        expected_path = Path(self.temp_dir) / "locks" / "iphoto_downloader.lock"
        self.assertEqual(manager.lock_file_path, expected_path)
        self.assertIsNone(manager.lock_file_handle)

    @patch("iphoto_downloader.instance_manager.get_logger")
    @patch("iphoto_downloader.instance_manager.get_app_data_folder_path")
    def test_init_without_app_data_folder(self, mock_get_app_data, mock_get_logger):
        """Test initialization without app data folder."""
        mock_get_logger.return_value = self.mock_logger
        mock_get_app_data.return_value = None

        manager = InstanceManager(allow_multi_instance=True)

        self.assertTrue(manager.allow_multi_instance)
        expected_path = Path("iphoto_downloader.lock")
        self.assertEqual(manager.lock_file_path, expected_path)

    @patch("iphoto_downloader.instance_manager.get_logger")
    @patch("iphoto_downloader.instance_manager.get_app_data_folder_path")
    def test_multi_instance_allowed_skips_lock(self, mock_get_app_data, mock_get_logger):
        """Test that multi-instance mode skips lock acquisition."""
        mock_get_logger.return_value = self.mock_logger
        mock_get_app_data.return_value = Path(self.temp_dir)

        manager = InstanceManager(allow_multi_instance=True)

        result = manager.check_and_acquire_lock()

        self.assertTrue(result)
        self.mock_logger.info.assert_called_with(
            "Multi-instance mode enabled - not checking for existing instances"
        )

    @patch("iphoto_downloader.instance_manager.get_logger")
    @patch("iphoto_downloader.instance_manager.get_app_data_folder_path")
    @patch("platform.system")
    def test_acquire_lock_windows_success(self, mock_platform, mock_get_app_data, mock_get_logger):
        """Test successful lock acquisition on Windows."""
        mock_get_logger.return_value = self.mock_logger
        mock_get_app_data.return_value = Path(self.temp_dir)
        mock_platform.return_value = "Windows"

        manager = InstanceManager(allow_multi_instance=False)
        manager.lock_file_path = self.test_lock_file

        with (
            patch("os.open") as mock_open,
            patch("os.write") as mock_write,
            patch("os.fsync") as mock_fsync,
            patch("os.getpid", return_value=12345),
            patch("iphoto_downloader.instance_manager._msvcrt") as mock_msvcrt,
        ):
            mock_open.return_value = 123
            mock_msvcrt.locking = Mock()
            mock_msvcrt.LK_NBLCK = 1

            result = manager.check_and_acquire_lock()

            self.assertTrue(result)
            self.assertEqual(manager.lock_file_handle, 123)
            mock_open.assert_called_once()
            mock_msvcrt.locking.assert_called_once_with(123, 1, 1)
            mock_write.assert_called_once()
            mock_fsync.assert_called_once()

    @patch("iphoto_downloader.instance_manager.get_logger")
    @patch("iphoto_downloader.instance_manager.get_app_data_folder_path")
    @patch("platform.system")
    def test_acquire_lock_unix_success(self, mock_platform, mock_get_app_data, mock_get_logger):
        """Test successful lock acquisition on Unix-like systems."""
        mock_get_logger.return_value = self.mock_logger
        mock_get_app_data.return_value = Path(self.temp_dir)
        mock_platform.return_value = "Linux"

        manager = InstanceManager(allow_multi_instance=False)
        manager.lock_file_path = self.test_lock_file

        with (
            patch("os.open") as mock_open,
            patch("os.write") as mock_write,
            patch("os.fsync") as mock_fsync,
            patch("os.getpid", return_value=12345),
            patch("iphoto_downloader.instance_manager._fcntl") as mock_fcntl,
        ):
            mock_open.return_value = 123
            mock_fcntl.flock = Mock()
            mock_fcntl.LOCK_EX = 2
            mock_fcntl.LOCK_NB = 4

            result = manager.check_and_acquire_lock()

            self.assertTrue(result)
            self.assertEqual(manager.lock_file_handle, 123)
            mock_open.assert_called_once()
            mock_fcntl.flock.assert_called_once_with(123, 6)  # LOCK_EX | LOCK_NB
            mock_write.assert_called_once()
            mock_fsync.assert_called_once()

    @patch("iphoto_downloader.instance_manager.get_logger")
    @patch("iphoto_downloader.instance_manager.get_app_data_folder_path")
    @patch("platform.system")
    def test_acquire_lock_windows_failure(self, mock_platform, mock_get_app_data, mock_get_logger):
        """Test failed lock acquisition on Windows (another instance running)."""
        mock_get_logger.return_value = self.mock_logger
        mock_get_app_data.return_value = Path(self.temp_dir)
        mock_platform.return_value = "Windows"

        manager = InstanceManager(allow_multi_instance=False)
        manager.lock_file_path = self.test_lock_file

        with (
            patch("os.open") as mock_open,
            patch("os.close") as mock_close,
            patch("iphoto_downloader.instance_manager._msvcrt") as mock_msvcrt,
        ):
            mock_open.return_value = 123
            mock_msvcrt.locking = Mock(side_effect=OSError("Lock failed"))
            mock_msvcrt.LK_NBLCK = 1

            result = manager.check_and_acquire_lock()

            self.assertFalse(result)
            self.assertIsNone(manager.lock_file_handle)
            mock_close.assert_called_once_with(123)

    @patch("iphoto_downloader.instance_manager.get_logger")
    @patch("iphoto_downloader.instance_manager.get_app_data_folder_path")
    def test_get_running_instance_info_with_pid(self, mock_get_app_data, mock_get_logger):
        """Test getting running instance info when lock file contains PID."""
        mock_get_logger.return_value = self.mock_logger
        mock_get_app_data.return_value = Path(self.temp_dir)

        manager = InstanceManager(allow_multi_instance=False)
        manager.lock_file_path = self.test_lock_file

        # Create lock file with PID
        self.test_lock_file.write_text("12345")

        result = manager.get_running_instance_info()

        self.assertEqual(result, "Process ID: 12345")

    @patch("iphoto_downloader.instance_manager.get_logger")
    @patch("iphoto_downloader.instance_manager.get_app_data_folder_path")
    def test_get_running_instance_info_no_file(self, mock_get_app_data, mock_get_logger):
        """Test getting running instance info when no lock file exists."""
        mock_get_logger.return_value = self.mock_logger
        mock_get_app_data.return_value = Path(self.temp_dir)

        manager = InstanceManager(allow_multi_instance=False)
        manager.lock_file_path = self.test_lock_file

        result = manager.get_running_instance_info()

        self.assertIsNone(result)

    @patch("iphoto_downloader.instance_manager.get_logger")
    @patch("iphoto_downloader.instance_manager.get_app_data_folder_path")
    @patch("platform.system")
    def test_release_lock_windows(self, mock_platform, mock_get_app_data, mock_get_logger):
        """Test lock release on Windows."""
        mock_get_logger.return_value = self.mock_logger
        mock_get_app_data.return_value = Path(self.temp_dir)
        mock_platform.return_value = "Windows"

        manager = InstanceManager(allow_multi_instance=False)
        manager.lock_file_path = self.test_lock_file
        manager.lock_file_handle = 123

        # Create the lock file
        self.test_lock_file.touch()

        with (
            patch("os.close") as mock_close,
            patch("iphoto_downloader.instance_manager._msvcrt") as mock_msvcrt,
        ):
            mock_msvcrt.locking = Mock()
            mock_msvcrt.LK_UNLCK = 0

            manager.release_lock()

            mock_msvcrt.locking.assert_called_once_with(123, 0, 1)
            mock_close.assert_called_once_with(123)
            self.assertIsNone(manager.lock_file_handle)
            self.assertFalse(self.test_lock_file.exists())

    @patch("iphoto_downloader.instance_manager.get_logger")
    @patch("iphoto_downloader.instance_manager.get_app_data_folder_path")
    @patch("builtins.print")
    def test_instance_context_blocks_second_instance(
        self, mock_print, mock_get_app_data, mock_get_logger
    ):
        """Test that instance context blocks second instance when multi-instance is disabled."""
        mock_get_logger.return_value = self.mock_logger
        mock_get_app_data.return_value = Path(self.temp_dir)

        manager = InstanceManager(allow_multi_instance=False)

        with (
            patch.object(manager, "check_and_acquire_lock", return_value=False),
            patch.object(manager, "get_running_instance_info", return_value="Process ID: 12345"),
            self.assertRaises(SystemExit) as cm,
        ):
            with manager.instance_context():
                pass

        self.assertEqual(cm.exception.code, 1)
        mock_print.assert_any_call(
            "❌ Another instance of iPhoto Downloader Tool is already running."
        )

    @patch("iphoto_downloader.instance_manager.get_logger")
    @patch("iphoto_downloader.instance_manager.get_app_data_folder_path")
    def test_instance_context_allows_when_lock_acquired(self, mock_get_app_data, mock_get_logger):
        """Test that instance context allows execution when lock is acquired."""
        mock_get_logger.return_value = self.mock_logger
        mock_get_app_data.return_value = Path(self.temp_dir)

        manager = InstanceManager(allow_multi_instance=False)

        executed = False

        with (
            patch.object(manager, "check_and_acquire_lock", return_value=True),
            patch.object(manager, "release_lock") as mock_release,
        ):
            with manager.instance_context():
                executed = True

        self.assertTrue(executed)
        mock_release.assert_called_once()


class TestValidateMultiInstanceConfig(unittest.TestCase):
    """Test cases for validate_multi_instance_config function."""

    def test_validate_true(self):
        """Test validation with True value."""
        result = validate_multi_instance_config(True)
        self.assertTrue(result)

    def test_validate_false(self):
        """Test validation with False value."""
        result = validate_multi_instance_config(False)
        self.assertTrue(result)

    def test_validate_invalid_type(self):
        """Test validation with invalid type."""
        with self.assertRaises(ValueError) as cm:
            validate_multi_instance_config("true")

        self.assertIn("allow_multi_instance must be a boolean", str(cm.exception))

    def test_validate_invalid_number(self):
        """Test validation with number instead of boolean."""
        with self.assertRaises(ValueError) as cm:
            validate_multi_instance_config(1)

        self.assertIn("allow_multi_instance must be a boolean", str(cm.exception))


class TestEnforceSingleInstance(unittest.TestCase):
    """Test cases for enforce_single_instance function."""

    @patch("iphoto_downloader.instance_manager.InstanceManager")
    def test_enforce_single_instance_valid_config(self, mock_instance_manager_class):
        """Test enforce_single_instance with valid configuration."""
        mock_instance = Mock()
        mock_instance_manager_class.return_value = mock_instance
        mock_instance.instance_context.return_value.__enter__ = Mock()
        mock_instance.instance_context.return_value.__exit__ = Mock(return_value=False)

        result = enforce_single_instance(False)

        self.assertEqual(result, mock_instance)
        mock_instance_manager_class.assert_called_once_with(False)

    def test_enforce_single_instance_invalid_config(self):
        """Test enforce_single_instance with invalid configuration."""
        with self.assertRaises(ValueError):
            enforce_single_instance("false")


if __name__ == "__main__":
    unittest.main()
