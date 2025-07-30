"""
Integration tests for iPhoto Downloader Tool with mocked pyicloud.
These tests simulate various sync scenarios without requiring real iCloud credentials.
"""
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from iphoto_downloader.sync import PhotoSyncer
from iphoto_downloader.logger import setup_logging


@pytest.mark.integration
class TestSyncIntegration:
    """Integration tests for complete sync workflows."""

    @pytest.fixture(autouse=True)
    def setup_logging(self):
        """Setup logging for all tests."""
        from iphoto_downloader.config import BaseConfig

        # Create a minimal config for logging setup
        mock_log_config = Mock(spec=BaseConfig)
        mock_log_config.get_log_level.return_value = 20  # INFO level

        setup_logging(mock_log_config)

    @pytest.fixture
    def mock_config(self, tmp_path):  # noqa
        """Create a mock configuration for integration testing."""
        config = Mock()
        config.icloud_username = "test@example.com"
        config.icloud_password = "test-password"
        config.sync_directory = tmp_path / "photos"
        config.dry_run = False
        config.log_level = "INFO"
        config.max_downloads = 0
        config.max_file_size_mb = 0
        config.ensure_sync_directory.return_value = None
        config.get_log_level.return_value = 20  # INFO level

        # Ensure the sync directory exists
        config.sync_directory.mkdir(parents=True, exist_ok=True)

        return config

    @pytest.fixture
    def mock_photos(self):
        """Create mock photo data for testing."""
        return [
            {
                'id': 'photo1',
                'filename': 'vacation_01.jpg',
                'size': 1024 * 1024,  # 1MB
                'created': '2023-07-01T12:00:00Z'
            },
            {
                'id': 'photo2',
                'filename': 'vacation_02.jpg',
                'size': 2 * 1024 * 1024,  # 2MB
                'created': '2023-07-01T13:00:00Z'
            },
            {
                'id': 'photo3',
                'filename': 'family_portrait.png',
                'size': 3 * 1024 * 1024,  # 3MB
                'created': '2023-07-02T10:00:00Z'
            }
        ]

    @patch('iphoto_downloader.sync.iCloudClient')
    def test_integration_sync_new_photos(self, mock_icloud_client_class, mock_config, mock_photos):
        """Integration test: Sync new photos from empty local directory."""
        # Setup mock iCloud client
        mock_client = Mock()
        mock_icloud_client_class.return_value = mock_client
        mock_client.authenticate.return_value = True
        mock_client.requires_2fa.return_value = False
        mock_client.list_photos.return_value = mock_photos

        # Mock successful downloads with file creation
        def mock_download_photo(photo_info, local_path):
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            Path(local_path).write_bytes(b'x' * photo_info['size'])
            return True
        mock_client.download_photo.side_effect = mock_download_photo

        # Run sync
        syncer = PhotoSyncer(mock_config)
        try:
            result = syncer.sync()

            # Verify results
            assert result is True
            stats = syncer.get_stats()
            assert stats['total_photos'] == 3
            assert stats['new_downloads'] == 3
            assert stats['already_exists'] == 0
            assert stats['deleted_skipped'] == 0
            assert stats['errors'] == 0
            assert stats['bytes_downloaded'] == 6 * 1024 * 1024  # 6MB total

            # Verify files were created
            photos_dir = mock_config.sync_directory
            assert (photos_dir / 'vacation_01.jpg').exists()
            assert (photos_dir / 'vacation_02.jpg').exists()
            assert (photos_dir / 'family_portrait.png').exists()
        finally:
            # Cleanup
            if hasattr(syncer, 'deletion_tracker'):
                syncer.deletion_tracker.close()

    @patch('iphoto_downloader.sync.iCloudClient')
    def test_integration_sync_with_existing_photos(
            self, mock_icloud_client_class, mock_config, mock_photos):
        """Integration test: Sync when some photos already exist locally."""
        # Pre-create some local photos
        photos_dir = mock_config.sync_directory
        photos_dir.mkdir(parents=True, exist_ok=True)
        (photos_dir / 'vacation_01.jpg').write_bytes(b'existing photo')

        # Setup mock iCloud client
        mock_client = Mock()
        mock_icloud_client_class.return_value = mock_client
        mock_client.authenticate.return_value = True
        mock_client.requires_2fa.return_value = False
        mock_client.list_photos.return_value = mock_photos

        # Mock successful downloads for new photos only
        def mock_download_photo(photo_info, local_path):
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            Path(local_path).write_bytes(b'x' * photo_info['size'])
            return True
        mock_client.download_photo.side_effect = mock_download_photo

        # Run sync
        syncer = PhotoSyncer(mock_config)
        try:
            result = syncer.sync()

            # Verify results
            assert result is True
            stats = syncer.get_stats()
            assert stats['total_photos'] == 3
            assert stats['new_downloads'] == 2  # Only 2 new photos downloaded
            assert stats['already_exists'] == 1  # vacation_01.jpg already existed
            assert stats['deleted_skipped'] == 0
            assert stats['errors'] == 0
        finally:
            # Cleanup
            if hasattr(syncer, 'deletion_tracker'):
                syncer.deletion_tracker.close()

    @patch('iphoto_downloader.sync.iCloudClient')
    def test_integration_sync_dry_run_mode(
            self, mock_icloud_client_class, mock_config, mock_photos):
        """Integration test: Sync in dry-run mode should not download files."""
        # Enable dry-run mode
        mock_config.dry_run = True

        # Setup mock iCloud client
        mock_client = Mock()
        mock_icloud_client_class.return_value = mock_client
        mock_client.authenticate.return_value = True
        mock_client.requires_2fa.return_value = False
        mock_client.list_photos.return_value = mock_photos

        # Download should not be called in dry-run mode
        mock_client.download_photo = Mock()

        # Run sync
        syncer = PhotoSyncer(mock_config)
        try:
            result = syncer.sync()

            # Verify results
            assert result is True
            stats = syncer.get_stats()
            assert stats['total_photos'] == 3
            assert stats['new_downloads'] == 3  # Stats show downloads but no actual files
            assert stats['already_exists'] == 0
            assert stats['deleted_skipped'] == 0
            assert stats['errors'] == 0
            assert stats['bytes_downloaded'] == 6 * 1024 * 1024  # Uses metadata sizes

            # Verify no files were actually created
            photos_dir = mock_config.sync_directory
            if photos_dir.exists():
                downloaded_files = list(photos_dir.glob('*'))
                # Only the database file should exist
                non_db_files = [f for f in downloaded_files if f.name != 'deletion_tracker.db']
                assert len(non_db_files) == 0, "No image files should be downloaded in dry-run mode"

            # Verify download_photo was not called
            mock_client.download_photo.assert_not_called()
        finally:
            # Cleanup
            if hasattr(syncer, 'deletion_tracker'):
                syncer.deletion_tracker.close()

    @patch('iphoto_downloader.sync.iCloudClient')
    def test_integration_sync_authentication_failure(self, mock_icloud_client_class, mock_config):
        """Integration test: Handle authentication failure gracefully."""
        # Setup mock iCloud client with auth failure
        mock_client = Mock()
        mock_icloud_client_class.return_value = mock_client
        mock_client.authenticate.return_value = False

        # Run sync
        syncer = PhotoSyncer(mock_config)
        try:
            result = syncer.sync()

            # Verify failure
            assert result is False
            stats = syncer.get_stats()
            # Authentication failure is not counted as an error in stats,
            # it's a precondition failure that prevents the sync from starting
            assert stats['errors'] == 0  # No processing errors occurred
            assert stats['total_photos'] == 0  # No photos were processed
        finally:
            # Cleanup
            if hasattr(syncer, 'deletion_tracker'):
                syncer.deletion_tracker.close()
