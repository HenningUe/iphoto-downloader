"""Tests for database path configuration functionality."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.iphoto_downloader.src.iphoto_downloader.config import BaseConfig
from src.iphoto_downloader.src.iphoto_downloader.deletion_tracker import DeletionTracker
from src.iphoto_downloader.src.iphoto_downloader.logger import setup_logging


class TestDatabasePathConfiguration(unittest.TestCase):
    """Test database path configuration functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Set up logging for tests
        import logging
        setup_logging(log_level=logging.INFO)

        self.temp_dir = Path(tempfile.mkdtemp())
        self.env_file = self.temp_dir / ".env"

        # Store original working directory
        self.original_cwd = os.getcwd()
        # Change to temp directory for relative path testing
        os.chdir(self.temp_dir)

        # Create minimal .env file for testing
        self.env_file.write_text("""
SYNC_DIRECTORY=./test_photos
DRY_RUN=true
LOG_LEVEL=INFO
ENABLE_PUSHOVER=false
""")

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original working directory
        os.chdir(self.original_cwd)

        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_default_database_path(self):
        """Test default database path configuration."""
        # Create a fresh env file for this test in a subdirectory
        test_dir = self.temp_dir / "test_default"
        test_dir.mkdir()
        test_env_file = test_dir / ".env"
        test_env_file.write_text("""
SYNC_DIRECTORY=./test_photos
DRY_RUN=true
LOG_LEVEL=INFO
ENABLE_PUSHOVER=false
""")

        # Change to the test subdirectory
        original_cwd = os.getcwd()
        os.chdir(test_dir)

        # Ensure DATABASE_PARENT_DIRECTORY is not set in environment for this test
        with patch.dict(os.environ, {}, clear=False):
            # Remove DATABASE_PARENT_DIRECTORY if it exists
            if 'DATABASE_PARENT_DIRECTORY' in os.environ:
                del os.environ['DATABASE_PARENT_DIRECTORY']
            
            try:
                config = BaseConfig(test_env_file)
                database_path = config.database_path

                # Should default to .data subdirectory - check by looking at parent directory name
                # The parent directory should be named .data
                self.assertEqual(database_path.parent.name, ".data")
                self.assertTrue(str(database_path).endswith("deletion_tracker.db"))

                # Database directory should be created
                self.assertTrue(database_path.parent.exists())
            finally:
                os.chdir(original_cwd)

    def test_relative_database_path(self):
        """Test relative database path configuration."""
        # Create a fresh env file for this test
        test_env_file = self.temp_dir / "test_relative.env"
        test_env_file.write_text("""
SYNC_DIRECTORY=./test_photos
DATABASE_PARENT_DIRECTORY=custom_db
DRY_RUN=true
LOG_LEVEL=INFO
ENABLE_PUSHOVER=false
""")

        config = BaseConfig(test_env_file)
        database_path = config.database_path

        # Should be relative to sync directory - check parent directory name
        self.assertEqual(database_path.parent.name, "custom_db")
        self.assertTrue(str(database_path).endswith("deletion_tracker.db"))

    def test_absolute_database_path(self):
        """Test absolute database path configuration."""
        absolute_db_dir = self.temp_dir / "absolute_db"

        # Create a fresh env file for this test
        test_env_file = self.temp_dir / "test_absolute.env"
        test_env_file.write_text(f"""
SYNC_DIRECTORY=./test_photos
DATABASE_PARENT_DIRECTORY={absolute_db_dir}
DRY_RUN=true
LOG_LEVEL=INFO
ENABLE_PUSHOVER=false
""")

        config = BaseConfig(test_env_file)
        database_path = config.database_path

        # Should use absolute path
        self.assertTrue(str(database_path).startswith(str(absolute_db_dir)))
        self.assertTrue(str(database_path).endswith("deletion_tracker.db"))

    def test_environment_variable_expansion(self):
        """Test environment variable expansion."""
        # Create a test environment variable
        test_env_path = str(self.temp_dir / "env_test")

        with patch.dict(os.environ, {'TEST_DB_PATH': test_env_path}):
            # Update env file with environment variable
            env_file_abs = self.temp_dir / ".env"
            env_file_abs.write_text("""
SYNC_DIRECTORY=./test_photos
DATABASE_PARENT_DIRECTORY=$TEST_DB_PATH/iphoto_downloader
DRY_RUN=true
LOG_LEVEL=INFO
ENABLE_PUSHOVER=false
""")

            config = BaseConfig(env_file_abs)
            database_path = config.database_path

            # Should expand environment variable
            self.assertTrue(str(database_path).startswith(test_env_path))
            self.assertTrue(str(database_path).endswith("deletion_tracker.db"))
            self.assertTrue("iphoto_downloader" in str(database_path))

    def test_database_path_with_deletion_tracker(self):
        """Test that DeletionTracker can use configured database path."""
        # Update env file with custom path
        custom_db_dir = self.temp_dir / "custom_tracker_db"
        env_file_abs = self.temp_dir / ".env"
        env_file_abs.write_text(f"""
SYNC_DIRECTORY=./test_photos
DATABASE_PARENT_DIRECTORY={custom_db_dir}
DRY_RUN=true
LOG_LEVEL=INFO
ENABLE_PUSHOVER=false
""")

        config = BaseConfig(env_file_abs)
        database_path = config.database_path

        # Create DeletionTracker with configured path
        tracker = DeletionTracker(str(database_path))

        # Verify database was created in the configured location
        self.assertTrue(database_path.exists())
        self.assertEqual(tracker.db_path, database_path)

    def test_database_directory_creation(self):
        """Test that database directories are created automatically."""
        nested_db_dir = self.temp_dir / "level1" / "level2" / "level3"

        # Update env file with nested path
        env_file_abs = self.temp_dir / ".env"
        env_file_abs.write_text(f"""
SYNC_DIRECTORY=./test_photos
DATABASE_PARENT_DIRECTORY={nested_db_dir}
DRY_RUN=true
LOG_LEVEL=INFO
ENABLE_PUSHOVER=false
""")

        config = BaseConfig(env_file_abs)
        database_path = config.database_path

        # Accessing database_path should create the directory structure
        self.assertTrue(database_path.parent.exists())
        self.assertTrue(database_path.parent.is_dir())

    def test_validation_with_valid_path(self):
        """Test that validation passes with valid database path."""
        # Use temp directory which should be writable
        env_file_abs = self.temp_dir / ".env"
        env_file_abs.write_text(f"""
SYNC_DIRECTORY=./test_photos
DATABASE_PARENT_DIRECTORY={self.temp_dir}/valid_db
DRY_RUN=true
LOG_LEVEL=INFO
ENABLE_PUSHOVER=false
EXECUTION_MODE=single
ICLOUD_USERNAME=test@example.com
ICLOUD_PASSWORD=testpassword
""")

        config = BaseConfig(env_file_abs)

        # Should not raise any exceptions
        try:
            config.validate()
        except ValueError:
            self.fail("validate() raised ValueError unexpectedly with valid database path")


if __name__ == '__main__':
    unittest.main()
