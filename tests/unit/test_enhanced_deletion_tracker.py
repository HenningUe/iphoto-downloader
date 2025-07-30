"""Unit tests for enhanced deletion tracking functionality."""

import logging
import os
import sys
import tempfile
import unittest
from pathlib import Path

from iphoto_downloader.deletion_tracker import DeletionTracker
from iphoto_downloader.logger import setup_logging

# Add the source path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src/iphoto_downloader/src"))


# Setup logging for tests
setup_logging(logging.WARNING)  # Reduce noise during tests


class TestEnhancedDeletionTracker(unittest.TestCase):
    """Test enhanced deletion tracking features."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_tracker.db")
        self.tracker = DeletionTracker(self.db_path)

    def tearDown(self):
        """Clean up test fixtures."""
        self.tracker.close()
        # Clean up temp directory
        import shutil

        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass  # Ignore cleanup errors on Windows

    def test_add_downloaded_photo(self):
        """Test adding downloaded photo record."""
        self.tracker.add_downloaded_photo(
            photo_id="test_photo_1",
            filename="test.jpg",
            local_path="album/test.jpg",
            file_size=1024,
            album_name="Test Album",
        )

        downloaded = self.tracker.get_downloaded_photos()
        self.assertIn("test_photo_1", downloaded)
        self.assertEqual(downloaded["test_photo_1"]["filename"], "test.jpg")
        self.assertEqual(downloaded["test_photo_1"]["local_path"], "album/test.jpg")
        self.assertEqual(downloaded["test_photo_1"]["file_size"], 1024)
        self.assertEqual(downloaded["test_photo_1"]["album_name"], "Test Album")

    def test_get_downloaded_photos_empty(self):
        """Test getting downloaded photos when none exist."""
        downloaded = self.tracker.get_downloaded_photos()
        self.assertEqual(downloaded, {})

    def test_detect_locally_deleted_photos_no_deletions(self):
        """Test detection when no photos are deleted."""
        sync_dir = Path(self.temp_dir) / "sync"
        sync_dir.mkdir()

        # Create a photo file
        album_dir = sync_dir / "TestAlbum"
        album_dir.mkdir()
        photo_path = album_dir / "test.jpg"
        photo_path.write_text("test content")

        # Record it as downloaded
        self.tracker.add_downloaded_photo(
            photo_id="photo1",
            filename="test.jpg",
            local_path="TestAlbum/test.jpg",
            file_size=12,
            album_name="TestAlbum",
        )

        # Detect deletions - should be empty since file exists
        deleted = self.tracker.detect_locally_deleted_photos(sync_dir)
        self.assertEqual(len(deleted), 0)

    def test_detect_locally_deleted_photos_with_deletions(self):
        """Test detection when photos are deleted."""
        sync_dir = Path(self.temp_dir) / "sync"
        sync_dir.mkdir()

        # Record a photo as downloaded but don't create the file
        self.tracker.add_downloaded_photo(
            photo_id="photo1",
            filename="deleted.jpg",
            local_path="TestAlbum/deleted.jpg",
            file_size=1024,
            album_name="TestAlbum",
        )

        # Detect deletions - should find the missing file
        deleted = self.tracker.detect_locally_deleted_photos(sync_dir)
        self.assertEqual(len(deleted), 1)
        self.assertEqual(deleted[0]["photo_id"], "photo1")
        self.assertEqual(deleted[0]["filename"], "deleted.jpg")
        self.assertEqual(deleted[0]["local_path"], "TestAlbum/deleted.jpg")

    def test_detect_locally_deleted_photos_skips_already_marked(self):
        """Test that already marked deleted photos are skipped."""
        sync_dir = Path(self.temp_dir) / "sync"
        sync_dir.mkdir()

        # Record a photo as downloaded
        self.tracker.add_downloaded_photo(
            photo_id="photo1",
            filename="deleted.jpg",
            local_path="TestAlbum/deleted.jpg",
            file_size=1024,
            album_name="TestAlbum",
        )

        # Mark it as deleted
        self.tracker.add_deleted_photo(
            photo_id="photo1",
            filename="deleted.jpg",
            file_size=1024,
            original_path="TestAlbum/deleted.jpg",
        )

        # Detect deletions - should skip since already marked
        deleted = self.tracker.detect_locally_deleted_photos(sync_dir)
        self.assertEqual(len(deleted), 0)

    def test_mark_photos_as_deleted(self):
        """Test marking multiple photos as deleted."""
        deleted_photos = [
            {
                "photo_id": "photo1",
                "filename": "test1.jpg",
                "local_path": "album/test1.jpg",
                "file_size": 1024,
                "album_name": "Album1",
            },
            {
                "photo_id": "photo2",
                "filename": "test2.jpg",
                "local_path": "album/test2.jpg",
                "file_size": 2048,
                "album_name": "Album1",
            },
        ]

        self.tracker.mark_photos_as_deleted(deleted_photos)

        # Verify both are marked as deleted
        self.assertTrue(self.tracker.is_deleted("photo1"))
        self.assertTrue(self.tracker.is_deleted("photo2"))

    def test_remove_downloaded_photo(self):
        """Test removing downloaded photo record."""
        # Add a downloaded photo
        self.tracker.add_downloaded_photo(
            photo_id="photo1",
            filename="test.jpg",
            local_path="album/test.jpg",
            file_size=1024,
            album_name="TestAlbum",
        )

        # Verify it exists
        downloaded = self.tracker.get_downloaded_photos()
        self.assertIn("photo1", downloaded)

        # Remove it
        self.tracker.remove_downloaded_photo("photo1")

        # Verify it's gone
        downloaded = self.tracker.get_downloaded_photos()
        self.assertNotIn("photo1", downloaded)

    def test_database_integration(self):
        """Test that downloaded and deleted photos work together."""
        # Add a downloaded photo
        self.tracker.add_downloaded_photo(
            photo_id="photo1",
            filename="test.jpg",
            local_path="album/test.jpg",
            file_size=1024,
            album_name="TestAlbum",
        )

        # Initially not deleted
        self.assertFalse(self.tracker.is_deleted("photo1"))

        # Mark as deleted
        self.tracker.add_deleted_photo(
            photo_id="photo1", filename="test.jpg", file_size=1024, original_path="album/test.jpg"
        )

        # Now should be marked as deleted
        self.assertTrue(self.tracker.is_deleted("photo1"))

        # Downloaded record should still exist
        downloaded = self.tracker.get_downloaded_photos()
        self.assertIn("photo1", downloaded)


if __name__ == "__main__":
    unittest.main()
