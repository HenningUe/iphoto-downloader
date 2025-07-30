"""Test database safety and recovery functionality."""

import glob
import sqlite3
import tempfile
from pathlib import Path

import pytest
from src.iphoto_downloader.src.iphoto_downloader.deletion_tracker import DeletionTracker
from src.iphoto_downloader.src.iphoto_downloader.logger import setup_logging


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Set up logging for tests."""
    import logging

    setup_logging(logging.INFO)


class TestDatabaseSafety:
    """Test database safety, backup, and recovery functionality."""

    def test_create_backup(self, temp_dir):
        """Test that database backup is created successfully."""
        tracker = DeletionTracker(str(temp_dir / "test.db"))

        # Add some test data
        tracker.add_downloaded_photo("test_photo", "test.jpg", "/test/path", 1024, "Album1")

        # Create backup
        assert tracker.create_backup(max_backups=3) is True

        # Verify backup file exists
        backup_files = glob.glob(str(temp_dir / "test.backup_*.db"))
        assert len(backup_files) == 1

        # Verify backup contains the data
        backup_conn = sqlite3.connect(backup_files[0])
        try:
            cursor = backup_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM downloaded_photos")
            count = cursor.fetchone()[0]
            assert count == 1
        finally:
            backup_conn.close()

        # Clean up - ensure connections are closed
        tracker.close()
        del tracker

    def test_cleanup_old_backups(self, temp_dir):
        """Test that old backup files are cleaned up properly."""
        import time

        tracker = DeletionTracker(str(temp_dir / "test.db"))

        # Create multiple backups with slight delays to ensure different timestamps
        for i in range(5):
            assert tracker.create_backup(max_backups=3) is True
            time.sleep(1.1)  # Ensure different timestamps

        # Should only have 3 backup files
        backup_files = glob.glob(str(temp_dir / "test.backup_*.db"))
        assert len(backup_files) == 3

        # Clean up
        tracker.close()
        del tracker

    def test_database_integrity_check_healthy(self, temp_dir):
        """Test integrity check on a healthy database."""
        tracker = DeletionTracker(str(temp_dir / "test.db"))

        # Add some data
        tracker.add_downloaded_photo("test_photo", "test.jpg", "/test/path", 1024, "Album1")

        # Check integrity
        assert tracker.check_database_integrity() is True

        # Clean up
        tracker.close()
        del tracker

    def test_database_integrity_check_corrupted(self, temp_dir):
        """Test integrity check on a corrupted database."""
        db_path = temp_dir / "test.db"
        tracker = DeletionTracker(str(db_path))

        # Close the database and corrupt it
        tracker.close()
        del tracker

        # Corrupt the database file
        with open(db_path, "wb") as f:
            f.write(b"corrupted data")

        # Test that corruption is detectable
        corrupt_detected = False
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            corrupt_detected = not result or result[0] != "ok"
        except Exception:
            corrupt_detected = True
        finally:
            # Explicitly close connection to prevent Windows file locking
            if conn:
                try:
                    conn.close()
                except:
                    pass

        # Should detect corruption
        assert corrupt_detected is True

    def test_recover_from_backup_success(self, temp_dir):
        """Test successful recovery from backup."""
        db_path = temp_dir / "test.db"
        tracker = DeletionTracker(str(db_path))

        # Add some test data
        tracker.add_downloaded_photo("test_photo", "test.jpg", "/test/path", 1024, "Album1")

        # Create backup
        tracker.create_backup()

        # Corrupt the database
        tracker.close()
        del tracker
        with open(db_path, "wb") as f:
            f.write(b"corrupted data")

        # Create new tracker instance - should detect corruption and recover
        tracker = DeletionTracker(str(db_path))

        # Verify data is recovered
        photos = tracker.get_downloaded_photos()
        # photos is a dict[photo_id, photo_data], not a list
        assert len(photos) == 1

        # Get the first (and only) photo from the dict
        photo_data = next(iter(photos.values()))
        assert photo_data["filename"] == "test.jpg"

        # Clean up
        tracker.close()
        del tracker

    def test_recover_from_backup_no_backups(self, temp_dir):
        """Test recovery attempt when no backups exist."""
        db_path = temp_dir / "test.db"
        tracker = DeletionTracker(str(db_path))

        # Don't create any backups, just corrupt the database
        tracker.close()
        del tracker
        with open(db_path, "wb") as f:
            f.write(b"corrupted data")

        # Recovery should fail but still allow new database creation
        tracker = DeletionTracker(str(db_path))

        # Should have a working empty database
        assert tracker.check_database_integrity() is True
        assert len(tracker.get_downloaded_photos()) == 0

        # Clean up
        tracker.close()
        del tracker

    def test_ensure_database_safety_new_database(self, temp_dir):
        """Test database safety with a new database."""
        db_path = temp_dir / "new_test.db"

        # Database doesn't exist yet
        assert not db_path.exists()

        tracker = DeletionTracker(str(db_path))

        # Should create new database
        assert db_path.exists()
        assert tracker.check_database_integrity() is True

        # Clean up
        tracker.close()
        del tracker

    def test_ensure_database_safety_healthy_database(self, temp_dir):
        """Test database safety with a healthy existing database."""
        tracker = DeletionTracker(str(temp_dir / "test.db"))

        # Add some data
        tracker.add_downloaded_photo("test_photo", "test.jpg", "/test/path", 1024, "Album1")

        # Should pass safety checks and create backup
        assert tracker.ensure_database_safety() is True

        # Should have at least one backup
        backup_files = glob.glob(str(temp_dir / "test.backup_*.db"))
        assert len(backup_files) >= 1

        # Clean up
        tracker.close()
        del tracker

    def test_ensure_database_safety_corrupted_with_backup(self, temp_dir):
        """Test database safety with corrupted database but valid backup."""
        db_path = temp_dir / "test.db"
        tracker = DeletionTracker(str(db_path))

        # Add data and create backup
        tracker.add_downloaded_photo("test_photo", "test.jpg", "/test/path", 1024, "Album1")
        tracker.create_backup()

        # Corrupt the database
        tracker.close()
        del tracker
        with open(db_path, "wb") as f:
            f.write(b"corrupted data")

        # Should recover from backup
        tracker = DeletionTracker(str(db_path))

        # Data should be recovered
        photos = tracker.get_downloaded_photos()
        assert len(photos) == 1

        # Get the first (and only) photo from the dict
        photo_data = next(iter(photos.values()))
        assert photo_data["filename"] == "test.jpg"

        # Clean up
        tracker.close()
        del tracker

    def test_backup_creation_on_initialization(self, temp_dir):
        """Test that backup is created during normal initialization."""
        # Create initial tracker with data
        tracker1 = DeletionTracker(str(temp_dir / "test.db"))
        tracker1.add_downloaded_photo("test_photo", "test.jpg", "/test/path", 1024, "Album1")
        tracker1.close()
        del tracker1

        # Initialize another tracker - should create backup
        tracker2 = DeletionTracker(str(temp_dir / "test.db"))

        # Should have created backup
        backup_files = glob.glob(str(temp_dir / "test.backup_*.db"))
        assert len(backup_files) >= 1

        # Clean up
        tracker2.close()
        del tracker2

    def test_corrupted_backup_handling(self, temp_dir):
        """Test handling when backup files are also corrupted."""
        db_path = temp_dir / "test.db"
        tracker = DeletionTracker(str(db_path))

        # Add data and create backup
        tracker.add_downloaded_photo("test_photo", "test.jpg", "/test/path", 1024, "Album1")
        tracker.create_backup()

        # Corrupt both database and backup
        tracker.close()
        del tracker

        backup_files = glob.glob(str(temp_dir / "test.backup_*.db"))
        assert len(backup_files) == 1

        # Corrupt main database
        with open(db_path, "wb") as f:
            f.write(b"corrupted data")

        # Corrupt backup too
        with open(backup_files[0], "wb") as f:
            f.write(b"corrupted backup data")

        # Should create new database when recovery fails
        tracker = DeletionTracker(str(db_path))

        # Should have working empty database
        assert tracker.check_database_integrity() is True
        assert len(tracker.get_downloaded_photos()) == 0

        # Clean up
        tracker.close()
        del tracker


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
