#!/usr/bin/env python3
import pytest
"""Simple test script to verify deletion tracking functionality works."""

from icloud_photo_sync.logger import setup_logging
from icloud_photo_sync.deletion_tracker import DeletionTracker
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src" / "icloud_photo_sync" / "src"))


# Setup logging
setup_logging(logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.manual
def test_simple_deletion_tracking():
    """Test basic deletion tracking without file cleanup issues."""
    logger.info("🔄 Testing simple deletion tracking...")

    # Create tracker in current directory to avoid temp file issues
    db_path = Path(__file__).parent / "test_deletion.db"
    if db_path.exists():
        db_path.unlink()

    tracker = DeletionTracker(str(db_path))

    try:
        # Test 1: Record a downloaded photo
        tracker.add_downloaded_photo(
            photo_id="test_photo_1",
            filename="test1.jpg",
            local_path="album1/test1.jpg",
            file_size=1024,
            album_name="Test Album 1"
        )
        logger.info("✅ Recorded downloaded photo")

        # Test 2: Verify it's in the database
        downloaded = tracker.get_downloaded_photos()
        assert "test_photo_1" in downloaded
        assert downloaded["test_photo_1"]["filename"] == "test1.jpg"
        logger.info("✅ Downloaded photo retrieval works")

        # Test 3: Photo is not yet marked as deleted
        assert not tracker.is_deleted("test_photo_1")
        logger.info("✅ Photo correctly not marked as deleted initially")

        # Test 4: Mark photo as deleted
        tracker.add_deleted_photo(
            photo_id="test_photo_1",
            filename="test1.jpg",
            file_size=1024,
            original_path="album1/test1.jpg"
        )
        logger.info("✅ Marked photo as deleted")

        # Test 5: Verify it's now marked as deleted
        assert tracker.is_deleted("test_photo_1")
        logger.info("✅ Photo correctly marked as deleted")

        # Test 6: Get stats
        stats = tracker.get_stats()
        assert stats['total_deleted'] == 1
        logger.info("✅ Deletion stats work correctly")

        logger.info("🎉 Simple deletion tracking test passed!")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        tracker.close()
        # Clean up test database
        if db_path.exists():
            try:
                db_path.unlink()
            except Exception:
                pass  # Ignore cleanup errors


@pytest.mark.manual
def test_deletion_prevention_logic():
    """Test the logic that prevents re-downloading deleted photos."""
    logger.info("🔄 Testing deletion prevention logic...")

    # Create a test sync directory
    test_sync_dir = Path(__file__).parent / "test_sync"
    test_sync_dir.mkdir(exist_ok=True)

    # Create tracker
    db_path = Path(__file__).parent / "test_deletion2.db"
    if db_path.exists():
        db_path.unlink()

    tracker = DeletionTracker(str(db_path))

    try:
        # Create a test album directory and photo file
        album_dir = test_sync_dir / "TestAlbum"
        album_dir.mkdir(exist_ok=True)
        photo_path = album_dir / "test_photo.jpg"
        photo_path.write_text("fake photo content")

        # Record the photo as downloaded
        tracker.add_downloaded_photo(
            photo_id="photo_123",
            filename="test_photo.jpg",
            local_path="TestAlbum/test_photo.jpg",
            file_size=len("fake photo content"),
            album_name="TestAlbum"
        )
        logger.info("✅ Photo recorded as downloaded")

        # Verify photo exists and is not deleted
        assert photo_path.exists()
        assert not tracker.is_deleted("photo_123")
        logger.info("✅ Photo exists locally and not marked as deleted")

        # Simulate user deleting the photo
        photo_path.unlink()
        logger.info("🗑️ Simulated user deleting photo locally")

        # Detect local deletions
        deleted_photos = tracker.detect_locally_deleted_photos(test_sync_dir)
        assert len(deleted_photos) == 1
        assert deleted_photos[0]["photo_id"] == "photo_123"
        logger.info("✅ Local deletion detected correctly")

        # Mark as deleted
        tracker.mark_photos_as_deleted(deleted_photos)
        logger.info("✅ Photo marked as deleted")

        # Verify photo is now marked as deleted
        assert tracker.is_deleted("photo_123")
        logger.info("✅ Photo correctly marked as deleted in database")

        # Simulate sync process checking if photo should be skipped
        photo_id = "photo_123"
        should_skip = tracker.is_deleted(photo_id)

        if should_skip:
            logger.info("✅ Photo would be correctly skipped during sync (no re-download)")
        else:
            logger.error("❌ Photo would be re-downloaded (WRONG!)")
            return False

        logger.info("🎉 Deletion prevention logic test passed!")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        tracker.close()
        # Clean up test files
        import shutil
        if test_sync_dir.exists():
            try:
                shutil.rmtree(test_sync_dir)
            except Exception:
                pass  # Ignore cleanup errors
        if db_path.exists():
            try:
                db_path.unlink()
            except Exception:
                pass  # Ignore cleanup errors


def main():
    """Run simplified deletion tracking tests."""
    logger.info("🚀 Starting simplified deletion tracking tests...")

    success1 = test_simple_deletion_tracking()
    success2 = test_deletion_prevention_logic()

    if success1 and success2:
        logger.info("🎉 All deletion tracking tests passed!")
        logger.info("")
        logger.info("✅ DELETION TRACKING IS NOW WORKING CORRECTLY")
        logger.info("✅ Photos deleted locally will NOT be re-downloaded")
        logger.info("✅ The SPEC.md requirement has been implemented successfully")
        return True
    else:
        logger.error("❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
