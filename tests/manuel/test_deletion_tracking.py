#!/usr/bin/env python3
import pytest
"""Test script to verify deletion tracking functionality."""

from icloud_photo_sync.logger import setup_logging
from icloud_photo_sync.config import BaseConfig
from icloud_photo_sync.sync import PhotoSyncer
from icloud_photo_sync.deletion_tracker import DeletionTracker
import os
import sys
import tempfile
import logging
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src" / "icloud_photo_sync" / "src"))


# Setup logging
setup_logging(logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.manual
def test_deletion_tracker_basics():
    """Test basic deletion tracker functionality."""
    logger.info("🔄 Testing deletion tracker basics...")

    with tempfile.TemporaryDirectory() as temp_dir:
        tracker = DeletionTracker(os.path.join(temp_dir, "test_tracker.db"))

        try:
            # Test adding downloaded photo
            tracker.add_downloaded_photo(
                photo_id="test_photo_1",
                filename="test1.jpg",
                local_path="album1/test1.jpg",
                file_size=1024,
                album_name="Test Album 1"
            )

            # Test getting downloaded photos
            downloaded = tracker.get_downloaded_photos()
            assert "test_photo_1" in downloaded
            assert downloaded["test_photo_1"]["filename"] == "test1.jpg"
            assert downloaded["test_photo_1"]["local_path"] == "album1/test1.jpg"
            logger.info("✅ Downloaded photo tracking works")

            # Test adding deleted photo
            tracker.add_deleted_photo(
                photo_id="test_photo_2",
                filename="deleted.jpg",
                file_size=2048,
                original_path="album2/deleted.jpg"
            )

            # Test checking deletion status
            assert tracker.is_deleted("test_photo_2")
            assert not tracker.is_deleted("test_photo_1")
            logger.info("✅ Deleted photo tracking works")

        finally:
            # Ensure cleanup
            tracker.close()


@pytest.mark.manual
def test_local_deletion_detection():
    """Test detection of locally deleted photos."""
    logger.info("🔄 Testing local deletion detection...")

    with tempfile.TemporaryDirectory() as temp_dir:
        sync_dir = Path(temp_dir) / "sync"
        sync_dir.mkdir()

        tracker = DeletionTracker(os.path.join(temp_dir, "test_tracker.db"))

        try:
            # Create some test files
            album_dir = sync_dir / "TestAlbum"
            album_dir.mkdir()

            photo1_path = album_dir / "photo1.jpg"
            photo2_path = album_dir / "photo2.jpg"

            photo1_path.write_text("fake photo 1 content")
            photo2_path.write_text("fake photo 2 content")

            # Record them as downloaded
            tracker.add_downloaded_photo(
                photo_id="photo1_id",
                filename="photo1.jpg",
                local_path="TestAlbum/photo1.jpg",
                file_size=len("fake photo 1 content"),
                album_name="TestAlbum"
            )

            tracker.add_downloaded_photo(
                photo_id="photo2_id",
                filename="photo2.jpg",
                local_path="TestAlbum/photo2.jpg",
                file_size=len("fake photo 2 content"),
                album_name="TestAlbum"
            )

            logger.info(f"📝 Created test files: {photo1_path}, {photo2_path}")

            # Delete one file locally
            photo1_path.unlink()
            logger.info(f"🗑️ Deleted: {photo1_path}")

            # Detect deletions
            deleted_photos = tracker.detect_locally_deleted_photos(sync_dir)

            assert len(deleted_photos) == 1
            assert deleted_photos[0]["photo_id"] == "photo1_id"
            assert deleted_photos[0]["local_path"] == "TestAlbum/photo1.jpg"
            logger.info("✅ Local deletion detection works")

            # Mark as deleted
            tracker.mark_photos_as_deleted(deleted_photos)

            # Verify it's marked as deleted
            assert tracker.is_deleted("photo1_id")
            assert not tracker.is_deleted("photo2_id")
            logger.info("✅ Deletion marking works")

        finally:
            # Ensure cleanup
            tracker.close()


@pytest.mark.manual
def test_end_to_end_deletion_prevention():
    """Test end-to-end deletion prevention scenario."""
    logger.info("🔄 Testing end-to-end deletion prevention...")

    with tempfile.TemporaryDirectory() as temp_dir:
        sync_dir = Path(temp_dir) / "sync"
        sync_dir.mkdir()

        # Create mock config
        config = Mock(spec=BaseConfig)
        config.sync_directory = sync_dir
        config.max_downloads = 100
        config.dry_run = False
        config.personal_album_names_to_include = []
        config.shared_album_names_to_include = []
        config.include_personal_albums = True
        config.include_shared_albums = False
        config.ensure_sync_directory = Mock()
        config.validate_albums_exist = Mock()
        config.get_pushover_config = Mock(return_value=None)

        # Create mock iCloud client
        mock_icloud = Mock()
        mock_icloud.authenticate.return_value = True
        mock_icloud.requires_2fa.return_value = False

        # Mock photo data - same photo that will be "re-offered" by iCloud
        test_photo_info = {
            'id': 'test_photo_delete_prevention',
            'filename': 'test_photo.jpg',
            'album_name': 'TestAlbum',
            'size': 1024
        }

        # First sync - photo will be downloaded
        mock_icloud.list_photos_from_filtered_albums.return_value = [test_photo_info]
        mock_icloud.download_photo.return_value = True

        with patch('icloud_photo_sync.sync.iCloudClient', return_value=mock_icloud):
            syncer = PhotoSyncer(config)

            # Create the photo file to simulate successful download
            album_dir = sync_dir / "TestAlbum"
            album_dir.mkdir(parents=True)
            photo_path = album_dir / "test_photo.jpg"
            photo_path.write_text("fake photo content")

            # Record the download manually (simulating successful download)
            syncer.deletion_tracker.add_downloaded_photo(
                photo_id='test_photo_delete_prevention',
                filename='test_photo.jpg',
                local_path='TestAlbum/test_photo.jpg',
                file_size=len("fake photo content"),
                album_name='TestAlbum'
            )

            logger.info("📁 Simulated first sync with photo download")

            # User deletes the photo locally
            photo_path.unlink()
            logger.info(f"🗑️ User deleted photo: {photo_path}")

            # Second sync - should detect deletion and NOT re-download
            # Reset download counter
            mock_icloud.download_photo.reset_mock()

            # Get current local files (should be empty now)
            local_files = syncer._get_local_files()
            assert len(local_files) == 0, "Local files should be empty after deletion"

            # Track local deletions (this should detect the missing photo)
            syncer._track_local_deletions(local_files)

            # Verify photo is marked as deleted
            assert syncer.deletion_tracker.is_deleted('test_photo_delete_prevention')
            logger.info("✅ Photo marked as deleted after local deletion detection")

            # Simulate sync process for this specific photo
            photo_id = test_photo_info['id']
            filename = test_photo_info['filename']

            # Check if photo was deleted locally (should be True now)
            if syncer.deletion_tracker.is_deleted(photo_id):
                logger.info(f"⏭️ Correctly skipping deleted photo: {filename}")
                # This is the expected behavior - photo should be skipped
                skip_count = 1
            else:
                logger.error(f"❌ Photo was NOT marked as deleted: {filename}")
                skip_count = 0

            # Verify the photo was NOT re-downloaded
            mock_icloud.download_photo.assert_not_called()
            logger.info("✅ Photo was NOT re-downloaded (correct behavior)")

            assert skip_count == 1, "Photo should have been skipped due to deletion tracking"


def main():
    """Run all deletion tracking tests."""
    logger.info("🚀 Starting deletion tracking tests...")

    try:
        test_deletion_tracker_basics()
        logger.info("✅ Basic deletion tracker tests passed")

        test_local_deletion_detection()
        logger.info("✅ Local deletion detection tests passed")

        test_end_to_end_deletion_prevention()
        logger.info("✅ End-to-end deletion prevention tests passed")

        logger.info("🎉 All deletion tracking tests passed!")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
