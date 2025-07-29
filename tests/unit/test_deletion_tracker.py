"""Unit tests for deletion tracker module."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import pytest

from iphoto_downloader.deletion_tracker import DeletionTracker
from iphoto_downloader.logger import setup_logging


class TestDeletionTracker:
    """Test the DeletionTracker class."""

    @pytest.fixture(autouse=True)
    def setup_logger(self):
        """Setup logging for tests."""
        from iphoto_downloader.config import get_config
        config = get_config()
        setup_logging(config.get_log_level())

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        # Force close any open connections before cleanup
        try:
            # Give time for connections to close
            import time
            time.sleep(0.1)
            Path(db_path).unlink(missing_ok=True)
        except PermissionError:
            # On Windows, if file is still locked, try again after a moment
            import time
            time.sleep(0.5)
            try:
                Path(db_path).unlink(missing_ok=True)
            except PermissionError:
                pass  # If still locked, let it be cleaned up by the OS

    def test_init_creates_database(self, temp_db):
        """Test that initialization creates the database and table."""
        tracker = DeletionTracker(temp_db)

        # Check that database file exists
        assert Path(temp_db).exists()

        # Check that table exists
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='deleted_photos'"
            )
            assert cursor.fetchone() is not None

    def test_add_deleted_photo(self, temp_db):
        """Test adding a deleted photo."""
        tracker = DeletionTracker(temp_db)

        tracker.add_deleted_photo("photo123", "test.jpg", file_size=1024,
                                  original_path="/path/to/test.jpg")

        # Verify it was recorded
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT photo_id, photo_name, file_size, original_path "
                "FROM deleted_photos WHERE photo_id = ?",
                ("photo123",)
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "photo123"
            assert row[1] == "test.jpg"
            assert row[2] == 1024
            assert row[3] == "/path/to/test.jpg"

    def test_add_deleted_photo_duplicate(self, temp_db):
        """Test adding a duplicate deletion replaces the existing one."""
        tracker = DeletionTracker(temp_db)

        # Add same photo twice with different data
        tracker.add_deleted_photo("photo123", "test.jpg", file_size=1024)
        tracker.add_deleted_photo("photo123", "test.jpg", file_size=2048)

        # Verify only one record exists with updated data
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*), file_size FROM deleted_photos WHERE photo_id = ?",
                ("photo123",)
            )
            row = cursor.fetchone()
            assert row[0] == 1  # Only one record
            assert row[1] == 2048  # Updated file size

    def test_is_deleted_existing_photo(self, temp_db):
        """Test checking if a photo is marked as deleted."""
        tracker = DeletionTracker(temp_db)

        # Add a deletion
        tracker.add_deleted_photo("photo123", "test.jpg")

        # Check if it's marked as deleted
        assert tracker.is_deleted("photo123") is True
        assert tracker.is_deleted("nonexistent") is False

    def test_is_filename_deleted(self, temp_db):
        """Test checking if a photo is deleted by filename."""
        tracker = DeletionTracker(temp_db)

        # Add a deletion
        tracker.add_deleted_photo("photo123", "test.jpg")

        # Check by filename
        assert tracker.is_filename_deleted("test.jpg") is True
        assert tracker.is_filename_deleted("nonexistent.jpg") is False

    def test_get_deleted_photos(self, temp_db):
        """Test getting all deleted photos."""
        tracker = DeletionTracker(temp_db)

        # Add several deletions
        tracker.add_deleted_photo("photo1", "test1.jpg")
        tracker.add_deleted_photo("photo2", "test2.jpg")
        tracker.add_deleted_photo("photo3", "test3.jpg")

        deleted_photos = tracker.get_deleted_photos()

        assert len(deleted_photos) == 3
        assert deleted_photos == {"photo1", "photo2", "photo3"}

    def test_remove_deleted_photo(self, temp_db):
        """Test removing a photo from deleted list."""
        tracker = DeletionTracker(temp_db)

        # Add a deletion
        tracker.add_deleted_photo("photo123", "test.jpg")
        assert tracker.is_deleted("photo123") is True

        # Remove from deleted
        tracker.remove_deleted_photo("photo123")
        assert tracker.is_deleted("photo123") is False

    def test_get_stats(self, temp_db):
        """Test getting deletion statistics."""
        tracker = DeletionTracker(temp_db)

        # Add several deletions
        tracker.add_deleted_photo("photo1", "test1.jpg")
        tracker.add_deleted_photo("photo2", "test2.jpg")

        stats = tracker.get_stats()

        assert stats['total_deleted'] == 2
        assert 'first_deletion' in stats
        assert 'last_deletion' in stats
        assert stats['db_path'] == temp_db

    def test_get_stats_empty(self, temp_db):
        """Test getting statistics from empty database."""
        tracker = DeletionTracker(temp_db)

        stats = tracker.get_stats()

        assert stats['total_deleted'] == 0
        assert stats['first_deletion'] is None
        assert stats['last_deletion'] is None

    def test_database_error_handling(self, tmp_path):
        """Test handling of database errors."""
        # Create tracker with invalid database path
        invalid_path = tmp_path / "nonexistent" / "database.db"

        with pytest.raises(Exception):
            DeletionTracker(str(invalid_path))

    def test_corrupted_database_handling(self, temp_db):
        """Test handling of corrupted database."""
        # Create a corrupted database file
        with open(temp_db, 'w') as f:
            f.write("This is not a valid SQLite database")

        # Should handle corruption gracefully by recreating database
        tracker = DeletionTracker(temp_db)
        
        # Verify that database was recreated and is functional
        tracker.add_deleted_photo("test_photo", "test.jpg")
        assert tracker.is_photo_deleted("test.jpg") is True

    @patch('iphoto_downloader.deletion_tracker.get_logger')
    def test_logging_on_operations(self, mock_get_logger, temp_db):
        """Test that operations are logged."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        tracker = DeletionTracker(temp_db)

        # Test logging on add_deleted_photo
        tracker.add_deleted_photo("photo123", "test.jpg")
        mock_logger.debug.assert_called()

        # Test logging on remove_deleted_photo
        tracker.remove_deleted_photo("photo123")
        mock_logger.debug.assert_called()

    def test_multiple_trackers_same_db(self, temp_db):
        """Test that multiple tracker instances can use the same database."""
        tracker1 = DeletionTracker(temp_db)
        tracker2 = DeletionTracker(temp_db)

        # Add deletion with first tracker
        tracker1.add_deleted_photo("photo123", "test.jpg")

        # Check with second tracker
        assert tracker2.is_deleted("photo123") is True

    def test_filename_deletion_error_handling(self, temp_db):
        """Test error handling in is_filename_deleted."""
        tracker = DeletionTracker(temp_db)

        # Close the database to simulate error
        with sqlite3.connect(temp_db) as conn:
            conn.execute("DROP TABLE deleted_photos")

        # Should return False on error
        assert tracker.is_filename_deleted("test.jpg") is False

    def test_optional_parameters(self, temp_db):
        """Test that optional parameters work correctly."""
        tracker = DeletionTracker(temp_db)

        # Add deletion with minimal parameters
        tracker.add_deleted_photo("photo123", "test.jpg")

        # Verify it was recorded
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT photo_id, photo_name, file_size, original_path "
                "FROM deleted_photos WHERE photo_id = ?",
                ("photo123",)
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "photo123"
            assert row[1] == "test.jpg"
            assert row[2] is None  # file_size should be None
            assert row[3] is None  # original_path should be None
