"""Unit tests for iCloud client module."""

from unittest.mock import Mock, MagicMock, patch, mock_open
import pytest

from icloud_photo_sync.icloud_client import iCloudClient
from icloud_photo_sync.config import get_config
from icloud_photo_sync.logger import setup_logging


class TestiCloudClient:
    """Test the iCloudClient class."""

    @pytest.fixture(autouse=True)
    def setup_logger(self):
        """Setup logging for tests."""
        config = get_config()
        setup_logging(config.get_log_level())

    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        config = Mock()
        config.icloud_username = "test@example.com"
        config.icloud_password = "testpass123"
        config.max_file_size_mb = 0  # No limit
        config.dry_run = False
        config.session_directory = "C:\\Users\\uekoe\\icloud_photo_sync\\sessions"
        return config

    @pytest.fixture
    def mock_pyicloud_api(self):
        """Create a mock pyicloud API."""
        mock_service = Mock()
        mock_photos = Mock()
        mock_service.photos = mock_photos
        mock_service.requires_2fa = False
        mock_photos.all = []
        return mock_service

    def test_init(self, mock_config):
        """Test client initialization."""
        client = iCloudClient(mock_config)

        assert client.config == mock_config
        assert client._api is None

    def test_authenticate_success(self, mock_config, mock_pyicloud_api):
        """Test successful authentication."""
        with patch('icloud_photo_sync.icloud_client.PyiCloudService') as mock_api_class:
            mock_api_class.return_value = mock_pyicloud_api

            client = iCloudClient(mock_config)
            result = client.authenticate()

            assert result is True
            assert client._api == mock_pyicloud_api
            mock_api_class.assert_called_once_with(
                "test@example.com", "testpass123", cookie_directory=mock_config.session_directory
            )

    def test_authenticate_no_credentials(self, mock_config):
        """Test authentication without credentials."""
        mock_config.icloud_username = None
        mock_config.icloud_password = None

        client = iCloudClient(mock_config)
        result = client.authenticate()

        assert result is False

    def test_authenticate_no_photos_service(self, mock_config, mock_pyicloud_api):
        """Test authentication when photos service is unavailable."""
        mock_pyicloud_api.photos = None

        with patch('icloud_photo_sync.icloud_client.PyiCloudService') as mock_api_class:
            mock_api_class.return_value = mock_pyicloud_api

            client = iCloudClient(mock_config)
            result = client.authenticate()

            assert result is False

    def test_authenticate_exception(self, mock_config):
        """Test authentication with exception."""
        with patch('icloud_photo_sync.icloud_client.PyiCloudService') as mock_api_class:
            mock_api_class.side_effect = Exception("Auth failed")

            client = iCloudClient(mock_config)
            result = client.authenticate()

            assert result is False
            assert client._api is None

    def test_requires_2fa_no_api(self, mock_config):
        """Test requires_2fa without API connection."""
        client = iCloudClient(mock_config)

        assert client.requires_2fa() is False

    def test_requires_2fa_with_api(self, mock_config, mock_pyicloud_api):
        """Test requires_2fa with API connection."""
        mock_pyicloud_api.requires_2fa = True

        client = iCloudClient(mock_config)
        client._api = mock_pyicloud_api

        assert client.requires_2fa() is True

    def test_handle_2fa_success(self, mock_config, mock_pyicloud_api):
        """Test successful 2FA handling."""
        mock_pyicloud_api.validate_2fa_code.return_value = True

        client = iCloudClient(mock_config)
        client._api = mock_pyicloud_api

        result = client.handle_2fa_validation("123456")

        assert result is True
        mock_pyicloud_api.validate_2fa_code.assert_called_once_with("123456")

    def test_handle_2fa_failure(self, mock_config, mock_pyicloud_api):
        """Test failed 2FA handling."""
        mock_pyicloud_api.validate_2fa_code.return_value = False

        client = iCloudClient(mock_config)
        client._api = mock_pyicloud_api

        result = client.handle_2fa_validation("123456")

        assert result is False

    def test_handle_2fa_exception(self, mock_config, mock_pyicloud_api):
        """Test 2FA handling with exception."""
        mock_pyicloud_api.validate_2fa_code.side_effect = Exception("2FA failed")

        client = iCloudClient(mock_config)
        client._api = mock_pyicloud_api

        result = client.handle_2fa_validation("123456")

        assert result is False

    def test_handle_2fa_no_api(self, mock_config):
        """Test 2FA handling without API connection."""
        client = iCloudClient(mock_config)

        result = client.handle_2fa_validation("123456")

        assert result is False

    def test_list_photos_success(self, mock_config, mock_pyicloud_api):
        """Test successful photo listing."""
        # Mock photo objects
        mock_photo1 = Mock()
        mock_photo1.id = "id1"
        mock_photo1.filename = "photo1.jpg"
        mock_photo1.size = 1024
        mock_photo1.created = None
        mock_photo1.modified = None

        mock_photo2 = Mock()
        mock_photo2.id = "id2"
        mock_photo2.filename = "photo2.jpg"
        mock_photo2.size = 2048
        mock_photo2.created = None
        mock_photo2.modified = None

        mock_pyicloud_api.photos.all = [mock_photo1, mock_photo2]

        client = iCloudClient(mock_config)
        client._api = mock_pyicloud_api

        photos = list(client.list_photos())

        assert len(photos) == 2
        assert photos[0]['id'] == "id1"
        assert photos[0]['filename'] == "photo1.jpg"
        assert photos[0]['size'] == 1024
        assert photos[0]['photo_obj'] == mock_photo1

        assert photos[1]['id'] == "id2"
        assert photos[1]['filename'] == "photo2.jpg"
        assert photos[1]['size'] == 2048
        assert photos[1]['photo_obj'] == mock_photo2

    def test_list_photos_no_api(self, mock_config):
        """Test photo listing without API connection."""
        client = iCloudClient(mock_config)

        photos = list(client.list_photos())

        assert photos == []

    def test_list_photos_no_photos_service(self, mock_config, mock_pyicloud_api):
        """Test photo listing without photos service."""
        mock_pyicloud_api.photos = None

        client = iCloudClient(mock_config)
        client._api = mock_pyicloud_api

        photos = list(client.list_photos())

        assert photos == []

    def test_list_photos_exception(self, mock_config, mock_pyicloud_api):
        """Test photo listing with exception."""
        # Create a mock that raises exception when len() is called
        mock_photos_all = Mock()
        mock_photos_all.__len__ = Mock(side_effect=Exception("Photo fetch failed"))
        mock_pyicloud_api.photos.all = mock_photos_all

        client = iCloudClient(mock_config)
        client._api = mock_pyicloud_api

        photos = list(client.list_photos())

        assert photos == []

    def test_list_photos_with_progress_logging(self, mock_config, mock_pyicloud_api):
        """Test photo listing with progress logging."""
        # Create 200 photos to test progress logging
        mock_photos = []
        for i in range(200):
            mock_photo = Mock()
            mock_photo.id = f"id{i}"
            mock_photo.filename = f"photo{i}.jpg"
            mock_photo.size = 1024
            mock_photo.created = None
            mock_photo.modified = None
            mock_photos.append(mock_photo)

        mock_pyicloud_api.photos.all = mock_photos

        client = iCloudClient(mock_config)
        client._api = mock_pyicloud_api

        photos = list(client.list_photos())

        # Should return all photos
        assert len(photos) == 200
        assert photos[0]['id'] == "id0"
        assert photos[0]['filename'] == "photo0.jpg"

    def test_download_photo_success(self, mock_config):
        """Test successful photo download."""
        mock_photo = Mock()
        mock_download = Mock()
        mock_download.raw.read.return_value = b"fake image data"
        mock_photo.download.return_value = mock_download

        photo_info = {
            'id': 'test_id',
            'filename': 'test.jpg',
            'size': 1024,
            'photo_obj': mock_photo
        }

        client = iCloudClient(mock_config)

        with patch('builtins.open', mock_open()) as mock_file:
            result = client.download_photo(photo_info, "/tmp/test.jpg")

            assert result is True
            mock_photo.download.assert_called_once()
            mock_file.assert_called_once_with("/tmp/test.jpg", 'wb')
            mock_file().write.assert_called_once_with(b"fake image data")

    def test_download_photo_size_limit(self, mock_config):
        """Test photo download with size limit."""
        mock_config.max_file_size_mb = 1  # 1MB limit

        photo_info = {
            'id': 'test_id',
            'filename': 'large.jpg',
            'size': 2 * 1024 * 1024,  # 2MB photo
            'photo_obj': Mock()
        }

        client = iCloudClient(mock_config)

        result = client.download_photo(photo_info, "/tmp/large.jpg")

        assert result is False

    def test_download_photo_dry_run(self, mock_config):
        """Test photo download in dry run mode."""
        mock_config.dry_run = True

        photo_info = {
            'id': 'test_id',
            'filename': 'test.jpg',
            'size': 1024,
            'photo_obj': Mock()
        }

        client = iCloudClient(mock_config)

        result = client.download_photo(photo_info, "/tmp/test.jpg")

        assert result is True
        photo_info['photo_obj'].download.assert_not_called()

    def test_download_photo_exception(self, mock_config):
        """Test photo download with exception."""
        mock_photo = Mock()
        mock_photo.download.side_effect = Exception("Download failed")

        photo_info = {
            'id': 'test_id',
            'filename': 'test.jpg',
            'size': 1024,
            'photo_obj': mock_photo
        }

        client = iCloudClient(mock_config)

        result = client.download_photo(photo_info, "/tmp/test.jpg")

        assert result is False

    def test_download_photo_write_error(self, mock_config):
        """Test photo download with file write error."""
        mock_photo = Mock()
        mock_download = Mock()
        mock_download.raw.read.return_value = b"fake image data"
        mock_photo.download.return_value = mock_download

        photo_info = {
            'id': 'test_id',
            'filename': 'test.jpg',
            'size': 1024,
            'photo_obj': mock_photo
        }

        client = iCloudClient(mock_config)

        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = IOError("Write failed")

            result = client.download_photo(photo_info, "/tmp/test.jpg")

            assert result is False

    def test_is_authenticated_true(self, mock_config, mock_pyicloud_api):
        """Test is_authenticated when authenticated."""
        client = iCloudClient(mock_config)
        client._api = mock_pyicloud_api

        assert client.is_authenticated is True

    def test_is_authenticated_false_no_api(self, mock_config):
        """Test is_authenticated when not authenticated."""
        client = iCloudClient(mock_config)

        assert client.is_authenticated is False

    def test_is_authenticated_false_no_photos(self, mock_config, mock_pyicloud_api):
        """Test is_authenticated when API exists but no photos service."""
        mock_pyicloud_api.photos = None

        client = iCloudClient(mock_config)
        client._api = mock_pyicloud_api

        assert client.is_authenticated is False

    def test_cleanup_expired_sessions(self, mock_config, tmp_path):
        """Test cleanup of expired session files."""
        import time

        # Create a temporary session directory
        session_dir = tmp_path / "sessions"
        session_dir.mkdir()

        # Create some test session files with different ages
        current_time = time.time()

        # Old file (40 days old)
        old_file = session_dir / "old_session.txt"
        old_file.write_text("old session data")
        old_time = current_time - (40 * 24 * 60 * 60)  # 40 days ago
        import os
        os.utime(old_file, (old_time, old_time))

        # Recent file (10 days old)
        recent_file = session_dir / "recent_session.txt"
        recent_file.write_text("recent session data")
        recent_time = current_time - (10 * 24 * 60 * 60)  # 10 days ago
        os.utime(recent_file, (recent_time, recent_time))

        # Very recent file (1 day old)
        very_recent_file = session_dir / "very_recent_session.txt"
        very_recent_file.write_text("very recent session data")

        client = iCloudClient(mock_config)
        client.session_dir = session_dir

        # Clean up files older than 30 days
        client.cleanup_expired_sessions(max_age_days=30)

        # Check that only the old file was removed
        assert not old_file.exists()
        assert recent_file.exists()
        assert very_recent_file.exists()

    def test_cleanup_expired_sessions_no_session_dir(self, mock_config, tmp_path):
        """Test cleanup when session directory doesn't exist."""
        client = iCloudClient(mock_config)
        client.session_dir = tmp_path / "nonexistent"

        # Should not raise an exception
        client.cleanup_expired_sessions()

    def test_cleanup_sessions_standalone(self, tmp_path):
        """Test standalone cleanup_sessions function."""
        from icloud_photo_sync.icloud_client import cleanup_sessions
        import time

        # Create test files
        session_dir = tmp_path / "sessions"
        session_dir.mkdir()

        old_file = session_dir / "old.txt"
        old_file.write_text("old data")
        # Manually set old timestamp
        old_time = time.time() - (40 * 24 * 60 * 60)
        import os
        os.utime(old_file, (old_time, old_time))

        recent_file = session_dir / "recent.txt"
        recent_file.write_text("recent data")

        cleanup_sessions(max_age_days=30, session_dir=session_dir)

        assert not old_file.exists()
        assert recent_file.exists()

    def test_list_albums_success(self, mock_config):
        """Test listing albums successfully."""
        client = iCloudClient(mock_config)

        # Mock API structure
        mock_album1 = MagicMock()
        mock_album1.name = "Family Trip"
        mock_album1.id = "album1"
        mock_album1.photos = []
        mock_album1.isShared = False
        mock_album1.__len__ = Mock(return_value=5)

        mock_album2 = MagicMock()
        mock_album2.name = "Shared Album"
        mock_album2.id = "album2"
        mock_album2.photos = []
        mock_album2.isShared = True
        mock_album2.__len__ = Mock(return_value=3)
        mock_album2.list_type = "sharedstream"

        # Mock the shared streams  
        mock_shared_dict = {
            'album2': mock_album2
        }
        
        # Create mock albums dictionary
        mock_library = Mock()
        mock_library.name = "Library"  # Give it a name so it gets filtered out
        mock_library.service.shared_streams = mock_shared_dict
        
        # Use a mock dict that properly excludes Library from values()
        mock_albums_dict = Mock()
        mock_albums_dict.__getitem__ = lambda self, key: mock_library if key == 'Library' else mock_album1
        mock_albums_dict.values = Mock(return_value=[mock_album1])  # Only return non-Library albums

        mock_photos_service = MagicMock()
        mock_photos_service.albums = mock_albums_dict

        client._api = MagicMock()
        client._api.photos = mock_photos_service

        albums = list(client.list_albums())

        assert len(albums) == 2
        assert albums[0]['name'] == "Family Trip"
        assert albums[1]['name'] == "Shared Album"

    def test_list_albums_no_api(self, mock_config):
        """Test listing albums when not authenticated."""
        client = iCloudClient(mock_config)

        albums = list(client.list_albums())

        assert albums == []

    def test_list_photos_from_album_success(self, mock_config):
        """Test listing photos from a specific album."""
        client = iCloudClient(mock_config)

        # Mock photo in album
        mock_photo = MagicMock()
        mock_photo.id = "photo1"
        mock_photo.filename = "test.jpg"
        mock_photo.size = 1024

        # Mock album
        mock_album = MagicMock()
        mock_album.name = "Test Album"
        mock_album.__iter__ = MagicMock(return_value=iter([mock_photo]))
        mock_album.__len__ = MagicMock(return_value=1)

        # Mock the API to return our album
        client._api = MagicMock()
        client._api.photos.albums = {"Test Album": mock_album}

        photos = list(client.list_photos_from_album("Test Album", is_shared=False))

        assert len(photos) == 1
        assert photos[0]['id'] == "photo1"
        assert photos[0]['filename'] == "test.jpg"
        assert photos[0]['album_name'] == "Test Album"

    def test_list_photos_from_albums_success(self, mock_config):
        """Test listing photos from multiple albums."""
        client = iCloudClient(mock_config)

        # Mock albums
        album_names = ["Album1", "Album2"]

        # Mock API structure
        mock_album1 = MagicMock()
        mock_album1.name = "Album1"
        mock_photo1 = MagicMock()
        mock_photo1.id = "photo1"
        mock_photo1.filename = "test1.jpg"
        mock_photo1.size = 1024
        mock_album1.__iter__ = MagicMock(return_value=iter([mock_photo1]))
        mock_album1.__len__ = MagicMock(return_value=1)

        mock_album2 = MagicMock()
        mock_album2.name = "Album2"
        mock_photo2 = MagicMock()
        mock_photo2.id = "photo2"
        mock_photo2.filename = "test2.jpg"
        mock_photo2.size = 2048
        mock_album2.__iter__ = MagicMock(return_value=iter([mock_photo2]))
        mock_album2.__len__ = MagicMock(return_value=1)

        mock_photos_service = MagicMock()
        mock_photos_service.albums = {
            "Album1": mock_album1, 
            "Album2": mock_album2,
            "Library": Mock(service=Mock(shared_streams={}))
        }

        client._api = MagicMock()
        client._api.photos = mock_photos_service

        photos = list(client.list_photos_from_albums(album_names))

        assert len(photos) == 2
        assert photos[0]['album_name'] == "Album1"
        assert photos[1]['album_name'] == "Album2"

    def test_verify_albums_exist_success(self, mock_config):
        """Test verifying albums exist."""
        client = iCloudClient(mock_config)

        # Mock albums
        mock_album1 = MagicMock()
        mock_album1.name = "Existing Album"

        mock_photos_service = MagicMock()
        mock_photos_service.albums = {
            "Existing Album": mock_album1,
            "Library": Mock(service=Mock(shared_streams={}))
        }

        client._api = MagicMock()
        client._api.photos = mock_photos_service

        all_albums, existing, missing = client.verify_albums_exist(["Existing Album", "Missing Album"])

        assert missing == ["Missing Album"]
        assert existing == ["Existing Album"]

    def test_get_filtered_albums_personal_only(self, mock_config):
        """Test filtering to personal albums only."""
        from unittest.mock import MagicMock

        client = iCloudClient(mock_config)

        # Mock config
        mock_filter_config = MagicMock()
        mock_filter_config.include_personal_albums = True
        mock_filter_config.include_shared_albums = False
        mock_filter_config.personal_album_names_to_include = []
        mock_filter_config.shared_album_names_to_include = []

        # Mock albums - mix of personal and shared
        mock_personal = MagicMock()
        mock_personal.name = "Personal Album"
        mock_personal.id = "personal1"
        mock_personal.photos = []
        mock_personal.isShared = False
        mock_personal.__len__ = Mock(return_value=5)

        mock_shared = MagicMock()
        mock_shared.name = "Shared Album"
        mock_shared.id = "shared1"
        mock_shared.photos = []
        mock_shared.isShared = True
        mock_shared.list_type = "sharedstream"
        mock_shared.__len__ = Mock(return_value=3)

        # Create proper album dictionary structure
        mock_library = Mock()
        mock_library.name = 'Library'
        mock_albums_dict = {
            'personal1': mock_personal,
            'Library': mock_library
        }
        
        mock_shared_dict = {
            'shared1': mock_shared
        }
        
        mock_library.service.shared_streams = mock_shared_dict

        mock_photos_service = MagicMock()
        mock_photos_service.albums = mock_albums_dict

        client._api = MagicMock()
        client._api.photos = mock_photos_service

        filtered_albums = list(client.get_filtered_albums(mock_filter_config))

        assert len(filtered_albums) == 1
        assert filtered_albums[0]['name'] == "Personal Album"
        assert filtered_albums[0]['is_shared'] is False

    def test_get_filtered_albums_with_allowlist(self, mock_config):
        """Test filtering albums with allow-list."""
        from unittest.mock import MagicMock

        client = iCloudClient(mock_config)

        # Mock config with allow-list
        mock_filter_config = MagicMock()
        mock_filter_config.include_personal_albums = True
        mock_filter_config.include_shared_albums = True
        mock_filter_config.personal_album_names_to_include = ["Allowed Personal"]
        mock_filter_config.shared_album_names_to_include = ["Allowed Shared"]

        # Mock albums
        mock_allowed_personal = MagicMock()
        mock_allowed_personal.name = "Allowed Personal"
        mock_allowed_personal.id = "personal1"
        mock_allowed_personal.photos = []
        mock_allowed_personal.isShared = False
        mock_allowed_personal.__len__ = Mock(return_value=5)

        mock_denied_personal = MagicMock()
        mock_denied_personal.name = "Denied Personal"
        mock_denied_personal.id = "personal2"
        mock_denied_personal.photos = []
        mock_denied_personal.isShared = False
        mock_denied_personal.__len__ = Mock(return_value=3)

        mock_allowed_shared = MagicMock()
        mock_allowed_shared.name = "Allowed Shared"
        mock_allowed_shared.id = "shared1"
        mock_allowed_shared.photos = []
        mock_allowed_shared.isShared = True
        mock_allowed_shared.list_type = "sharedstream"
        mock_allowed_shared.__len__ = Mock(return_value=7)

        # Create proper album dictionary structure
        mock_albums_dict = {
            'personal1': mock_allowed_personal,
            'personal2': mock_denied_personal,
            'Library': Mock()
        }
        
        mock_shared_dict = {
            'shared1': mock_allowed_shared
        }
        
        mock_albums_dict['Library'].service.shared_streams = mock_shared_dict

        mock_photos_service = MagicMock()
        mock_photos_service.albums = mock_albums_dict

        client._api = MagicMock()
        client._api.photos = mock_photos_service

        filtered_albums = list(client.get_filtered_albums(mock_filter_config))

        assert len(filtered_albums) == 2
        album_names = [album['name'] for album in filtered_albums]
        assert "Allowed Personal" in album_names
        assert "Allowed Shared" in album_names
        assert "Denied Personal" not in album_names

    def test_list_photos_from_filtered_albums(self, mock_config):
        """Test listing photos from filtered albums."""
        from unittest.mock import MagicMock

        client = iCloudClient(mock_config)

        # Mock config
        mock_filter_config = MagicMock()
        mock_filter_config.include_personal_albums = True
        mock_filter_config.include_shared_albums = False
        mock_filter_config.personal_album_names_to_include = []
        mock_filter_config.shared_album_names_to_include = []

        # Mock main library photos
        mock_main_photo = MagicMock()
        mock_main_photo.id = "main1"
        mock_main_photo.filename = "main_photo.jpg"
        mock_main_photo.size = 1024

        # Mock album photos
        mock_album_photo = MagicMock()
        mock_album_photo.id = "album1"
        mock_album_photo.filename = "album_photo.jpg"
        mock_album_photo.size = 2048

        # Mock album
        mock_album = MagicMock()
        mock_album.name = "Test Album"  # Use 'name' not 'title'
        mock_album.id = "album_id"
        mock_album.photos = []
        mock_album.isShared = False
        mock_album.__iter__ = MagicMock(return_value=iter([mock_album_photo]))
        mock_album.__len__ = MagicMock(return_value=1)

        # Create proper album dictionary structure like other tests
        mock_library = MagicMock()
        mock_library.name = 'Library'
        mock_shared_dict = {}
        mock_library.service.shared_streams = mock_shared_dict
        
        mock_albums_dict = {
            'album_id': mock_album,
            'Library': mock_library
        }

        mock_photos_service = MagicMock()
        mock_photos_service.albums = mock_albums_dict
        mock_photos_service.all.__iter__ = MagicMock(return_value=iter([mock_main_photo]))
        mock_photos_service.all.__len__ = MagicMock(return_value=1)

        client._api = MagicMock()
        client._api.photos = mock_photos_service

        photos = list(client.list_photos_from_filtered_albums(
            mock_filter_config
        ))

        # Should get photos from filtered albums only
        assert len(photos) >= 1  # At least one album photo

        # Check that photos have album_name set (since they come from albums)
        album_photos = [p for p in photos if p.get('album_name') is not None]
        assert len(album_photos) >= 1
