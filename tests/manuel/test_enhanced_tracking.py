#!/usr/bin/env python3
import pytest
"""Test script to verify enhanced photo tracking with album-aware schema."""

import sys
import sqlite3
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src" / "iphoto_downloader" / "src"))

try:
    from iphoto_downloader.deletion_tracker import DeletionTracker
    from iphoto_downloader.logger import setup_logging
    import logging
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Set up logging
setup_logging(logging.INFO)


@pytest.mark.manual
def test_album_aware_tracking():
    """Test the album-aware photo tracking functionality."""
    print("🧪 Testing Enhanced Photo Tracking (Album-Aware)...")

    # Create a test database
    test_db_path = "test_enhanced_tracking.db"
    if Path(test_db_path).exists():
        Path(test_db_path).unlink()

    try:
        # Initialize tracker - this should create the new album-aware schema
        tracker = DeletionTracker(test_db_path)

        print("✅ Database initialized with album-aware schema")

        # Test 1: Add photos from different albums
        print("\n📝 Test 1: Adding photos from different albums...")

        # Same photo name in different albums
        tracker.add_downloaded_photo(
            photo_id="photo1",
            filename="vacation.jpg",
            local_path="Album1/vacation.jpg",
            album_name="Album1"
        )

        tracker.add_downloaded_photo(
            photo_id="photo2",
            filename="vacation.jpg",
            local_path="Album2/vacation.jpg",
            album_name="Album2"
        )

        print("✅ Added same photo name to different albums")

        # Test 2: Check album-aware queries
        print("\n🔍 Test 2: Testing album-aware queries...")

        # Should find the photo in Album1
        exists_album1 = tracker.is_photo_downloaded("vacation.jpg", "Album1")
        exists_album2 = tracker.is_photo_downloaded("vacation.jpg", "Album2")
        exists_album3 = tracker.is_photo_downloaded("vacation.jpg", "Album3")

        print(f"Photo in Album1: {exists_album1}")
        print(f"Photo in Album2: {exists_album2}")
        print(f"Photo in Album3: {exists_album3}")

        if exists_album1 and exists_album2 and not exists_album3:
            print("✅ Album-aware photo tracking works correctly")
        else:
            print("❌ Album-aware photo tracking failed")
            return False

        # Test 3: Album-aware deletion tracking
        print("\n🗑️ Test 3: Testing album-aware deletion tracking...")

        # Mark photo as deleted from Album1 only
        tracker.add_deleted_photo(
            photo_id="photo1",
            filename="vacation.jpg",
            album_name="Album1"
        )

        deleted_album1 = tracker.is_photo_deleted("vacation.jpg", "Album1")
        deleted_album2 = tracker.is_photo_deleted("vacation.jpg", "Album2")

        print(f"Deleted from Album1: {deleted_album1}")
        print(f"Deleted from Album2: {deleted_album2}")

        if deleted_album1 and not deleted_album2:
            print("✅ Album-aware deletion tracking works correctly")
        else:
            print("❌ Album-aware deletion tracking failed")
            return False

        # Test 4: Check database schema
        print("\n📊 Test 4: Verifying database schema...")

        with sqlite3.connect(test_db_path) as conn:
            cursor = conn.cursor()

            # Check if new schema exists
            cursor.execute("PRAGMA table_info(downloaded_photos)")
            columns = {row[1] for row in cursor.fetchall()}

            expected_columns = {'photo_name', 'source_album_name',
                                'photo_id', 'local_path', 'downloaded_at', 'file_size'}

            if expected_columns.issubset(columns):
                print("✅ Database schema has correct album-aware columns")
            else:
                print(f"❌ Missing columns: {expected_columns - columns}")
                return False

        tracker.close()
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    finally:
        # Cleanup
        if Path(test_db_path).exists():
            Path(test_db_path).unlink()


@pytest.mark.manual
def test_legacy_migration():
    """Test migration from legacy schema to album-aware schema."""
    print("\n🔄 Testing Legacy Schema Migration...")

    # Create a test database with legacy schema
    test_db_path = "test_migration.db"
    if Path(test_db_path).exists():
        Path(test_db_path).unlink()

    try:
        # Create legacy schema manually
        with sqlite3.connect(test_db_path) as conn:
            # Old schema
            conn.execute("""
                CREATE TABLE downloaded_photos (
                    photo_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    local_path TEXT NOT NULL,
                    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_size INTEGER,
                    album_name TEXT
                )
            """)

            # Insert some legacy data
            conn.execute("""
                INSERT INTO downloaded_photos 
                (photo_id, filename, local_path, album_name)
                VALUES ('legacy1', 'old_photo.jpg', 'SomeAlbum/old_photo.jpg', 'SomeAlbum')
            """)
            conn.commit()

        print("✅ Created legacy database with test data")

        # Now initialize tracker - this should trigger migration
        tracker = DeletionTracker(test_db_path)

        # Check if migration worked
        photos = tracker.get_downloaded_photos()
        print(f"📊 Migrated photos: {len(photos)}")

        if len(photos) > 0:
            print("✅ Legacy data migration successful")
            # Check if we can find the migrated photo
            found = tracker.is_photo_downloaded("old_photo.jpg", "SomeAlbum")
            if found:
                print("✅ Migrated photo is findable with album-aware query")
            else:
                print("❌ Migrated photo not found with album-aware query")
                return False
        else:
            print("❌ No photos found after migration")
            return False

        tracker.close()
        return True

    except Exception as e:
        print(f"❌ Migration test failed: {e}")
        return False
    finally:
        # Cleanup
        if Path(test_db_path).exists():
            Path(test_db_path).unlink()


if __name__ == "__main__":
    print("🚀 Running Enhanced Photo Tracking Tests...\n")

    success1 = test_album_aware_tracking()
    success2 = test_legacy_migration()

    if success1 and success2:
        print("\n🎉 All enhanced photo tracking tests passed!")
        print("✅ Album-aware photo tracking is working correctly")
        print("✅ Database migration system is working correctly")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
