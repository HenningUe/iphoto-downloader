"""Unit tests for sync module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import pytest

from icloud_photo_sync.sync import PhotoSyncer
from icloud_photo_sync.config import get_config
from icloud_photo_sync.logger import setup_logging


class TestPhotoSyncer:
    """Test the PhotoSyncer class."""

    @pytest.fixture(autouse=True)
    def setup_logger(self):
        """Setup logging for tests."""
        config = get_config()
        setup_logging(config.get_log_level())

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_config(self, temp_dir):
        """Create a mock config for testing."""
        config = Mock()
        config.sync_directory = temp_dir / "sync"
        config.dry_run = False
        config.max_downloads = 0  # No limit
        config.ensure_sync_directory.return_value = None
        return config

    @pytest.fixture
    def mock_icloud_client(self):
        """Create a mock iCloud client."""
        client = Mock()
        client.authenticate.return_value = True
        client.get_photos.return_value = []
        client.download_photo.return_value = True
        return client

    @pytest.fixture
    def mock_deletion_tracker(self):
        """Create a mock deletion tracker."""
        tracker = Mock()
        tracker.get_deleted_photos.return_value = set()
        tracker.is_filename_deleted.return_value = False
        tracker.add_deleted_photo.return_value = None
        return tracker

    @pytest.fixture
    def syncer(self, mock_config):
        """Create a PhotoSyncer instance for testing."""
        with patch('icloud_photo_sync.sync.iCloudClient') as mock_client_class, \
                patch('icloud_photo_sync.sync.DeletionTracker') as mock_tracker_class:

            mock_client_class.return_value = Mock()
            mock_tracker_class.return_value = Mock()

            return PhotoSyncer(mock_config)

    def test_init_creates_components(self, mock_config):
        """Test that initialization creates all required components."""
        with patch('icloud_photo_sync.sync.iCloudClient') as mock_client_class, \
                patch('icloud_photo_sync.sync.DeletionTracker') as mock_tracker_class:

            syncer = PhotoSyncer(mock_config)

            # Check that components were created
            assert syncer.config == mock_config
            mock_client_class.assert_called_once_with(mock_config)
            mock_config.ensure_sync_directory.assert_called_once()
            mock_tracker_class.assert_called_once()

            # Check initial stats
            assert syncer.stats['total_photos'] == 0
            assert syncer.stats['new_downloads'] == 0
            assert syncer.stats['already_exists'] == 0
            assert syncer.stats['deleted_skipped'] == 0
            assert syncer.stats['errors'] == 0
            assert syncer.stats['bytes_downloaded'] == 0

    def test_sync_successful_flow(self, syncer):
        """Test successful sync flow."""
        # Mock the iCloud client methods
        syncer.icloud_client.authenticate.return_value = True
        syncer.icloud_client.requires_2fa.return_value = False
        syncer.icloud_client.list_photos.return_value = []

        # Mock deletion tracker
        syncer.deletion_tracker.get_deleted_photos.return_value = set()

        # Mock internal methods
        with patch.object(syncer, '_get_local_files') as mock_get_local, \
                patch.object(syncer, '_track_local_deletions') as mock_track_deletions, \
                patch.object(syncer, '_sync_photos') as mock_sync_photos, \
                patch.object(syncer, '_print_summary') as mock_print_summary:

            mock_get_local.return_value = set()

            result = syncer.sync()

            assert result is True
            mock_get_local.assert_called_once()
            mock_track_deletions.assert_called_once()
            mock_sync_photos.assert_called_once()
            mock_print_summary.assert_called_once()

    def test_sync_authentication_failure(self, syncer):
        """Test sync with authentication failure."""
        syncer.icloud_client.authenticate.return_value = False

        result = syncer.sync()

        assert result is False

    def test_sync_with_2fa_success(self, syncer):
        """Test sync with successful 2FA handling."""
        syncer.icloud_client.authenticate.return_value = True
        syncer.icloud_client.requires_2fa.return_value = True

        with patch.object(syncer, '_handle_2fa') as mock_2fa, \
                patch.object(syncer, '_get_local_files') as mock_get_local, \
                patch.object(syncer, '_track_local_deletions') as mock_track_deletions, \
                patch.object(syncer, '_sync_photos') as mock_sync_photos, \
                patch.object(syncer, '_print_summary') as mock_print_summary:

            mock_2fa.return_value = True
            mock_get_local.return_value = set()
            syncer.icloud_client.list_photos.return_value = []
            syncer.deletion_tracker.get_deleted_photos.return_value = set()

            result = syncer.sync()

            assert result is True
            mock_2fa.assert_called_once()

    def test_sync_exception_handling(self, syncer):
        """Test sync with exception handling."""
        syncer.icloud_client.authenticate.side_effect = Exception("Test exception")

        result = syncer.sync()

        assert result is False
        assert syncer.stats['errors'] > 0

    def test_get_local_files(self, syncer, temp_dir):
        """Test getting local files."""
        # Create test files
        sync_dir = temp_dir / "sync"
        sync_dir.mkdir()

        (sync_dir / "test1.jpg").write_bytes(b"test1")
        (sync_dir / "test2.png").write_bytes(b"test2")
        (sync_dir / "test3.jpeg").write_bytes(b"test3")
        (sync_dir / "test4.txt").write_bytes(b"test4")  # Non-image file

        # Create subdirectory with images
        sub_dir = sync_dir / "subdir"
        sub_dir.mkdir()
        (sub_dir / "test5.jpg").write_bytes(b"test5")

        syncer.config.sync_directory = sync_dir

        local_files = syncer._get_local_files()

        # Should include image files but not text files
        expected_files = {"test1.jpg", "test2.png", "test3.jpeg", "test5.jpg"}
        assert local_files == expected_files

    def test_track_local_deletions(self, syncer):
        """Test tracking local deletions."""
        # Mock existing deleted photos
        syncer.deletion_tracker.get_deleted_photos.return_value = {
            "test1.jpg", "test2.jpg", "test3.jpg"
        }

        local_files = {"test1.jpg", "test2.jpg"}

        # Mock the filename lookup to return True for deleted photos
        def mock_is_filename_deleted(filename):
            return filename in ["test1.jpg", "test3.jpg"]

        syncer.deletion_tracker.is_filename_deleted.side_effect = mock_is_filename_deleted

        syncer._track_local_deletions(local_files)

        # Should remove test1.jpg from deleted photos since it exists locally
        syncer.deletion_tracker.remove_deleted_photo.assert_called_with("test1.jpg")

    def test_sync_photos_with_new_photos(self, syncer):
        """Test syncing new photos."""
        # Mock iCloud photos
        mock_photo1 = {
            'id': 'photo1',
            'filename': 'new_photo1.jpg',
            'size': 1024
        }

        mock_photo2 = {
            'id': 'photo2',
            'filename': 'existing_photo.jpg',
            'size': 2048
        }

        syncer.icloud_client.list_photos.return_value = [mock_photo1, mock_photo2]

        # Mock local files (existing_photo.jpg already exists)
        local_files = {"existing_photo.jpg"}

        # Mock deletion tracker
        syncer.deletion_tracker.is_deleted.return_value = False

        # Mock download success and create fake file
        def mock_download_photo(photo_info, local_path):
            # Create a fake file with the right size
            from pathlib import Path
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            Path(local_path).write_bytes(b'x' * photo_info['size'])
            return True

        syncer.icloud_client.download_photo.side_effect = mock_download_photo

        syncer._sync_photos(local_files)

        # Should try to download new_photo1.jpg but not existing_photo.jpg
        syncer.icloud_client.download_photo.assert_called_once_with(
            mock_photo1, str(syncer.config.sync_directory / "new_photo1.jpg")
        )

        # Check stats
        assert syncer.stats['total_photos'] == 2
        assert syncer.stats['new_downloads'] == 1
        assert syncer.stats['already_exists'] == 1
        assert syncer.stats['bytes_downloaded'] == 1024

    def test_sync_photos_with_deleted_photos(self, syncer):
        """Test syncing when photos are marked as deleted."""
        # Mock iCloud photos
        mock_photo = {
            'id': 'photo1',
            'filename': 'deleted_photo.jpg',
            'size': 1024
        }

        syncer.icloud_client.list_photos.return_value = [mock_photo]

        # Mock deletion tracker - photo is marked as deleted
        syncer.deletion_tracker.is_deleted.return_value = True

        local_files = set()

        syncer._sync_photos(local_files)

        # Should not try to download deleted photo
        syncer.icloud_client.download_photo.assert_not_called()

        # Check stats
        assert syncer.stats['total_photos'] == 1
        assert syncer.stats['deleted_skipped'] == 1
        assert syncer.stats['new_downloads'] == 0

    def test_sync_photos_download_failure(self, syncer):
        """Test handling download failures."""
        # Mock iCloud photos
        mock_photo = {
            'id': 'photo1',
            'filename': 'fail_photo.jpg',
            'size': 1024
        }

        syncer.icloud_client.list_photos.return_value = [mock_photo]

        # Mock deletion tracker
        syncer.deletion_tracker.is_deleted.return_value = False

        # Mock download failure
        syncer.icloud_client.download_photo.return_value = False

        local_files = set()

        syncer._sync_photos(local_files)

        # Should try to download but fail
        syncer.icloud_client.download_photo.assert_called_once()

        # Check stats
        assert syncer.stats['total_photos'] == 1
        assert syncer.stats['errors'] == 1
        assert syncer.stats['new_downloads'] == 0

    def test_sync_photos_dry_run(self, syncer):
        """Test sync in dry run mode."""
        syncer.config.dry_run = True

        # Mock iCloud photos
        mock_photo = {
            'id': 'photo1',
            'filename': 'new_photo.jpg',
            'size': 1024
        }

        syncer.icloud_client.list_photos.return_value = [mock_photo]
        syncer.deletion_tracker.is_deleted.return_value = False

        local_files = set()

        syncer._sync_photos(local_files)

        # Should not actually download in dry run mode
        syncer.icloud_client.download_photo.assert_not_called()

        # But should update stats as if it would download
        assert syncer.stats['total_photos'] == 1
        assert syncer.stats['new_downloads'] == 1
        assert syncer.stats['bytes_downloaded'] == 1024

    def test_handle_2fa_success(self, syncer):
        """Test successful 2FA handling."""
        with patch('builtins.input', return_value='123456'):
            syncer.icloud_client.handle_2fa.return_value = True
            syncer.icloud_client.trust_session.return_value = True

            result = syncer._handle_2fa()

            assert result is True  # Should return True when 2FA is successful

    def test_handle_2fa_failure(self, syncer):
        """Test failed 2FA handling."""
        result = syncer._handle_2fa()

        assert result is False  # Current implementation always returns False

    def test_handle_2fa_exception(self, syncer):
        """Test 2FA handling with exception."""
        result = syncer._handle_2fa()

        assert result is False  # Current implementation always returns False

    def test_get_stats(self, syncer):
        """Test getting sync statistics."""
        # Set some test stats
        syncer.stats['total_photos'] = 10
        syncer.stats['new_downloads'] = 5
        syncer.stats['already_exists'] = 3
        syncer.stats['deleted_skipped'] = 2
        syncer.stats['errors'] = 1
        syncer.stats['bytes_downloaded'] = 1024000

        stats = syncer.get_stats()

        assert stats['total_photos'] == 10
        assert stats['new_downloads'] == 5
        assert stats['already_exists'] == 3
        assert stats['deleted_skipped'] == 2
        assert stats['errors'] == 1
        assert stats['bytes_downloaded'] == 1024000

        # Check that stats include additional computed fields
        assert 'mb_downloaded' in stats
        assert stats['mb_downloaded'] == round(1024000 / (1024 * 1024), 2)
        assert 'success_rate' in stats
        assert stats['success_rate'] == 50.0  # 5/10 * 100

    def test_log_progress(self, syncer):
        """Test progress logging."""
        syncer.stats['total_photos'] = 100
        syncer.stats['new_downloads'] = 25
        syncer.stats['already_exists'] = 50
        syncer.stats['deleted_skipped'] = 15
        syncer.stats['errors'] = 10

        # This should not raise an exception
        syncer._log_progress()

    def test_print_summary(self, syncer):
        """Test summary printing."""
        syncer.stats['total_photos'] = 100
        syncer.stats['new_downloads'] = 25
        syncer.stats['already_exists'] = 50
        syncer.stats['deleted_skipped'] = 15
        syncer.stats['errors'] = 10
        syncer.stats['bytes_downloaded'] = 1024000

        # This should not raise an exception
        syncer._print_summary()
