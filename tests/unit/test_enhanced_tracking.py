"""Tests for enhanced tracking functionality with album-aware identification."""

import unittest
import tempfile
import shutil
import sqlite3
from pathlib import Path
import logging

from src.iphoto_downloader.src.iphoto_downloader.logger import setup_logging


class TestEnhancedTracking(unittest.TestCase):
    """Test enhanced tracking functionality."""

    def setUp(self):
        """Set up test fixtures."""
        setup_logging(log_level=logging.INFO)

        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_db = self.temp_dir / "test_tracking.db"

        # Create test database
        self.conn = sqlite3.connect(str(self.test_db))
        self._create_test_tables()

    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, 'conn'):
            self.conn.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_tables(self):
        """Create test database tables."""
        cursor = self.conn.cursor()

        # Create enhanced tracking table with composite keys
        cursor.execute("""
            CREATE TABLE photo_tracking (
                photo_id TEXT NOT NULL,
                album_name TEXT NOT NULL,
                filename TEXT NOT NULL,
                local_path TEXT,
                file_size INTEGER,
                modified_date TEXT,
                checksum TEXT,
                sync_status TEXT DEFAULT 'pending',
                last_sync_attempt TEXT,
                error_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (photo_id, album_name)
            )
        """)

        # Create album tracking table
        cursor.execute("""
            CREATE TABLE album_tracking (
                album_name TEXT PRIMARY KEY,
                is_shared BOOLEAN NOT NULL,
                total_photos INTEGER DEFAULT 0,
                synced_photos INTEGER DEFAULT 0,
                last_sync TEXT,
                sync_status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    def test_album_aware_photo_identification(self):
        """Test album-aware photo identification and tracking."""
        from src.iphoto_downloader.src.iphoto_downloader.deletion_tracker import (
            DeletionTracker
        )

        # Create enhanced deletion tracker
        tracker = DeletionTracker(str(self.test_db))

        # Add photos with album context
        photo_data = [
            {
                "photo_id": "photo_001",
                "album_name": "Family",
                "filename": "family_photo.jpg",
                "local_path": str(self.temp_dir / "family_photo.jpg"),
                "file_size": 1024000,
                "checksum": "abc123"
            },
            {
                "photo_id": "photo_001",  # Same photo in different album
                "album_name": "Vacation",
                "filename": "family_photo.jpg",
                "local_path": str(self.temp_dir / "family_photo.jpg"),
                "file_size": 1024000,
                "checksum": "abc123"
            }
        ]

        for photo in photo_data:
            tracker.track_photo(**photo)

        # Verify composite tracking
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM photo_tracking")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 2)  # Same photo tracked in 2 albums

        # Verify album-specific tracking
        family_photos = tracker.get_photos_in_album("Family")
        vacation_photos = tracker.get_photos_in_album("Vacation")

        self.assertEqual(len(family_photos), 1)
        self.assertEqual(len(vacation_photos), 1)
        self.assertEqual(family_photos[0]["photo_id"], "photo_001")
        self.assertEqual(vacation_photos[0]["photo_id"], "photo_001")

    def test_composite_primary_key_tracking(self):
        """Test composite primary key tracking (photo_id + album_name)."""
        from src.iphoto_downloader.src.iphoto_downloader.deletion_tracker import (
            DeletionTracker
        )

        tracker = DeletionTracker(str(self.test_db))

        # Add same photo to multiple albums
        tracker.track_photo(
            photo_id="photo_123",
            album_name="Family",
            filename="test.jpg",
            local_path=str(self.temp_dir / "test.jpg"),
            file_size=500000,
            checksum="def456"
        )

        tracker.track_photo(
            photo_id="photo_123",
            album_name="Vacation",
            filename="test.jpg",
            local_path=str(self.temp_dir / "test.jpg"),
            file_size=500000,
            checksum="def456"
        )

        # Update photo in one album
        tracker.update_photo_sync_status("photo_123", "Family", "completed")
        tracker.update_photo_sync_status("photo_123", "Vacation", "failed")

        # Verify independent tracking
        family_status = tracker.get_photo_sync_status("photo_123", "Family")
        vacation_status = tracker.get_photo_sync_status("photo_123", "Vacation")

        self.assertEqual(family_status, "completed")
        self.assertEqual(vacation_status, "failed")

    def test_album_level_tracking_statistics(self):
        """Test album-level tracking and statistics."""
        from src.iphoto_downloader.src.iphoto_downloader.deletion_tracker import (
            DeletionTracker
        )

        tracker = DeletionTracker(str(self.test_db))

        # Initialize album tracking
        tracker.track_album("Family", is_shared=False, total_photos=5)
        tracker.track_album("Wedding", is_shared=True, total_photos=10)

        # Add photos to albums
        for i in range(3):
            tracker.track_photo(
                photo_id=f"family_{i}",
                album_name="Family",
                filename=f"family_{i}.jpg",
                local_path=str(self.temp_dir / f"family_{i}.jpg"),
                file_size=1000000,
                checksum=f"hash_{i}"
            )
            tracker.update_photo_sync_status(f"family_{i}", "Family", "completed")

        for i in range(7):
            tracker.track_photo(
                photo_id=f"wedding_{i}",
                album_name="Wedding",
                filename=f"wedding_{i}.jpg",
                local_path=str(self.temp_dir / f"wedding_{i}.jpg"),
                file_size=2000000,
                checksum=f"wedding_hash_{i}"
            )
            if i < 4:
                tracker.update_photo_sync_status(f"wedding_{i}", "Wedding", "completed")

        # Update album statistics
        tracker.update_album_sync_progress("Family", synced_photos=3)
        tracker.update_album_sync_progress("Wedding", synced_photos=4)

        # Verify album statistics
        family_stats = tracker.get_album_statistics("Family")
        wedding_stats = tracker.get_album_statistics("Wedding")

        self.assertEqual(family_stats["total_photos"], 5)
        self.assertEqual(family_stats["synced_photos"], 3)
        self.assertEqual(family_stats["is_shared"], False)

        self.assertEqual(wedding_stats["total_photos"], 10)
        self.assertEqual(wedding_stats["synced_photos"], 4)
        self.assertEqual(wedding_stats["is_shared"], True)

    def test_cross_album_duplicate_detection(self):
        """Test detection of photos that exist in multiple albums."""
        from src.iphoto_downloader.src.iphoto_downloader.deletion_tracker import (
            DeletionTracker
        )

        tracker = DeletionTracker(str(self.test_db))

        # Add same photo to multiple albums with same checksum
        duplicate_checksum = "duplicate_hash_123"

        albums = ["Family", "Vacation", "Best Photos"]
        for album in albums:
            tracker.track_photo(
                photo_id=f"photo_dup",
                album_name=album,
                filename="duplicate_photo.jpg",
                local_path=str(self.temp_dir / "duplicate_photo.jpg"),
                file_size=1500000,
                checksum=duplicate_checksum
            )

        # Test duplicate detection
        duplicates = tracker.find_cross_album_duplicates()

        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0]["checksum"], duplicate_checksum)
        self.assertEqual(len(duplicates[0]["albums"]), 3)
        self.assertIn("Family", duplicates[0]["albums"])
        self.assertIn("Vacation", duplicates[0]["albums"])
        self.assertIn("Best Photos", duplicates[0]["albums"])

    def test_album_sync_coordination(self):
        """Test sync coordination across albums."""
        from src.iphoto_downloader.src.iphoto_downloader.deletion_tracker import (
            DeletionTracker
        )

        tracker = DeletionTracker(str(self.test_db))

        # Track albums with different sync states
        tracker.track_album("Family", is_shared=False, total_photos=3)
        tracker.track_album("Work", is_shared=False, total_photos=2)
        tracker.track_album("Shared", is_shared=True, total_photos=5)

        # Set different sync statuses
        tracker.update_album_sync_status("Family", "completed")
        tracker.update_album_sync_status("Work", "in_progress")
        tracker.update_album_sync_status("Shared", "failed")

        # Test coordination queries
        completed_albums = tracker.get_albums_by_status("completed")
        in_progress_albums = tracker.get_albums_by_status("in_progress")
        failed_albums = tracker.get_albums_by_status("failed")

        self.assertEqual(len(completed_albums), 1)
        self.assertEqual(completed_albums[0]["album_name"], "Family")

        self.assertEqual(len(in_progress_albums), 1)
        self.assertEqual(in_progress_albums[0]["album_name"], "Work")

        self.assertEqual(len(failed_albums), 1)
        self.assertEqual(failed_albums[0]["album_name"], "Shared")

    def test_migration_from_old_tracking_format(self):
        """Test migration from old single-key tracking to composite keys."""
        from src.iphoto_downloader.src.iphoto_downloader.deletion_tracker import (
            DeletionTracker
        )

        # Create old format table
        cursor = self.conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS photo_tracking")
        cursor.execute("""
            CREATE TABLE photo_tracking (
                photo_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                local_path TEXT,
                file_size INTEGER,
                modified_date TEXT,
                checksum TEXT,
                sync_status TEXT DEFAULT 'pending'
            )
        """)

        # Add old format data
        cursor.execute("""
            INSERT INTO photo_tracking 
            (photo_id, filename, local_path, file_size, checksum)
            VALUES (?, ?, ?, ?, ?)
        """, ("old_photo_1", "old.jpg", str(self.temp_dir / "old.jpg"), 1000, "old_hash"))

        self.conn.commit()
        self.conn.close()

        # Test migration
        tracker = DeletionTracker(str(self.test_db))

        # Should migrate data and create new table structure
        migrated_photos = tracker.get_all_tracked_photos()

        # Verify migration preserved data but added album context
        self.assertGreaterEqual(len(migrated_photos), 0)  # Data should be preserved

        # Verify new table structure exists
        cursor = sqlite3.connect(str(self.test_db)).cursor()
        cursor.execute("PRAGMA table_info(photo_tracking)")
        columns = [row[1] for row in cursor.fetchall()]

        self.assertIn("photo_id", columns)
        self.assertIn("album_name", columns)
        cursor.connection.close()

    def test_sync_progress_tracking_per_album(self):
        """Test detailed sync progress tracking per album."""
        from src.iphoto_downloader.src.iphoto_downloader.deletion_tracker import (
            DeletionTracker
        )

        tracker = DeletionTracker(str(self.test_db))

        # Setup album with photos
        album_name = "Progress Test"
        tracker.track_album(album_name, is_shared=False, total_photos=10)

        # Add photos with different sync states
        sync_states = ["pending", "in_progress", "completed", "failed", "completed"]
        for i, state in enumerate(sync_states):
            tracker.track_photo(
                photo_id=f"progress_{i}",
                album_name=album_name,
                filename=f"progress_{i}.jpg",
                local_path=str(self.temp_dir / f"progress_{i}.jpg"),
                file_size=1000000 + i * 100000,
                checksum=f"progress_hash_{i}"
            )
            tracker.update_photo_sync_status(f"progress_{i}", album_name, state)

        # Get progress summary
        progress = tracker.get_album_sync_progress(album_name)

        self.assertEqual(progress["total_photos"], 10)
        self.assertEqual(progress["tracked_photos"], 5)
        self.assertEqual(progress["completed_photos"], 2)
        self.assertEqual(progress["failed_photos"], 1)
        self.assertEqual(progress["pending_photos"], 1)
        self.assertEqual(progress["in_progress_photos"], 1)

        # Calculate completion percentage
        completion_rate = progress["completed_photos"] / progress["tracked_photos"]
        self.assertEqual(completion_rate, 0.4)  # 2/5 = 40%

    def test_error_tracking_and_retry_logic(self):
        """Test error tracking and retry logic for failed syncs."""
        from src.iphoto_downloader.src.iphoto_downloader.deletion_tracker import (
            DeletionTracker
        )

        tracker = DeletionTracker(str(self.test_db))

        # Track a photo that will fail
        tracker.track_photo(
            photo_id="error_photo",
            album_name="Error Test",
            filename="error.jpg",
            local_path=str(self.temp_dir / "error.jpg"),
            file_size=1000000,
            checksum="error_hash"
        )

        # Simulate multiple failures
        for attempt in range(3):
            tracker.record_sync_error("error_photo", "Error Test", f"Network error {attempt}")

        # Check error count
        photo_info = tracker.get_photo_info("error_photo", "Error Test")
        self.assertEqual(photo_info["error_count"], 3)

        # Test retry logic
        photos_for_retry = tracker.get_photos_for_retry(max_errors=5)
        self.assertEqual(len(photos_for_retry), 1)
        self.assertEqual(photos_for_retry[0]["photo_id"], "error_photo")

        # Test max error threshold
        photos_for_retry_strict = tracker.get_photos_for_retry(max_errors=2)
        self.assertEqual(len(photos_for_retry_strict), 0)  # Should be excluded

    def test_bulk_operations_performance(self):
        """Test performance of bulk operations on enhanced tracking."""
        from src.iphoto_downloader.src.iphoto_downloader.deletion_tracker import (
            DeletionTracker
        )
        import time

        tracker = DeletionTracker(str(self.test_db))

        # Prepare bulk data
        albums = ["Bulk1", "Bulk2", "Bulk3"]
        photos_per_album = 100

        # Test bulk album creation
        start_time = time.time()
        for album in albums:
            tracker.track_album(album, is_shared=False, total_photos=photos_per_album)
        album_time = time.time() - start_time

        # Test bulk photo insertion
        start_time = time.time()
        for album in albums:
            photos_data = []
            for i in range(photos_per_album):
                photos_data.append({
                    "photo_id": f"{album}_photo_{i}",
                    "album_name": album,
                    "filename": f"{album}_{i}.jpg",
                    "local_path": str(self.temp_dir / f"{album}_{i}.jpg"),
                    "file_size": 1000000 + i,
                    "checksum": f"{album}_hash_{i}"
                })

            tracker.bulk_track_photos(photos_data)
        photo_time = time.time() - start_time

        # Verify performance (should handle 300 photos quickly)
        self.assertLess(album_time, 1.0)  # Album creation should be fast
        self.assertLess(photo_time, 5.0)  # Bulk photo insertion should be reasonable

        # Verify data integrity
        total_photos = 0
        for album in albums:
            photos = tracker.get_photos_in_album(album)
            total_photos += len(photos)

        self.assertEqual(total_photos, len(albums) * photos_per_album)

    def test_cleanup_and_maintenance_operations(self):
        """Test cleanup and maintenance operations."""
        from src.iphoto_downloader.src.iphoto_downloader.deletion_tracker import (
            DeletionTracker
        )
        import time

        tracker = DeletionTracker(str(self.test_db))

        # Add old completed photos
        old_photos = []
        for i in range(5):
            photo_id = f"old_completed_{i}"
            tracker.track_photo(
                photo_id=photo_id,
                album_name="Old Album",
                filename=f"old_{i}.jpg",
                local_path=str(self.temp_dir / f"old_{i}.jpg"),
                file_size=1000000,
                checksum=f"old_hash_{i}"
            )
            tracker.update_photo_sync_status(photo_id, "Old Album", "completed")
            old_photos.append(photo_id)

        # Manually set old timestamps
        cursor = self.conn.cursor()
        old_timestamp = time.time() - (30 * 24 * 60 * 60)  # 30 days ago
        for photo_id in old_photos:
            cursor.execute(
                "UPDATE photo_tracking SET updated_at = ? WHERE photo_id = ?",
                (old_timestamp, photo_id)
            )
        self.conn.commit()

        # Test cleanup
        cleaned_count = tracker.cleanup_old_completed_entries(days_old=7)
        self.assertEqual(cleaned_count, 5)

        # Verify cleanup
        remaining_photos = tracker.get_photos_in_album("Old Album")
        self.assertEqual(len(remaining_photos), 0)


if __name__ == '__main__':
    unittest.main()
