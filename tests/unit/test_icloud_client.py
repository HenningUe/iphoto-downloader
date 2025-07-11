"""Unit tests for iCloud client module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
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
        setup_logging(config)
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock config for testing."""
        config = Mock()
        config.icloud_username = "test@example.com"
        config.icloud_password = "testpass123"
        config.max_file_size_mb = 0  # No limit
        config.dry_run = False
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
                "test@example.com", "testpass123"
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
        
        result = client.handle_2fa("123456")
        
        assert result is True
        mock_pyicloud_api.validate_2fa_code.assert_called_once_with("123456")
    
    def test_handle_2fa_failure(self, mock_config, mock_pyicloud_api):
        """Test failed 2FA handling."""
        mock_pyicloud_api.validate_2fa_code.return_value = False
        
        client = iCloudClient(mock_config)
        client._api = mock_pyicloud_api
        
        result = client.handle_2fa("123456")
        
        assert result is False
    
    def test_handle_2fa_exception(self, mock_config, mock_pyicloud_api):
        """Test 2FA handling with exception."""
        mock_pyicloud_api.validate_2fa_code.side_effect = Exception("2FA failed")
        
        client = iCloudClient(mock_config)
        client._api = mock_pyicloud_api
        
        result = client.handle_2fa("123456")
        
        assert result is False
    
    def test_handle_2fa_no_api(self, mock_config):
        """Test 2FA handling without API connection."""
        client = iCloudClient(mock_config)
        
        result = client.handle_2fa("123456")
        
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
        mock_pyicloud_api.photos.all = Mock(side_effect=Exception("Photo fetch failed"))
        
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
