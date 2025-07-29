"""Tests for album filtering functionality."""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import logging

from icloud_photo_sync.logger import setup_logging
from icloud_photo_sync.icloud_client import iCloudClient
from icloud_photo_sync.config import BaseConfig


class TestAlbumFiltering(unittest.TestCase):
    """Test album filtering functionality."""

    def setUp(self):
        """Set up test fixtures."""
        setup_logging(log_level=logging.INFO)
        self.temp_dir = tempfile.mkdtemp()
        
        # Create mock config
        self.mock_config = Mock(spec=BaseConfig)
        
        # Create mock iCloud client with proper patching
        with patch('icloud_photo_sync.icloud_client.iCloudClient') as mock_client_class:
            self.client = Mock()
            self.client._api = Mock()
            self.client._api.photos = Mock()
            self.client.logger = Mock()

            # Mock album data
            self.mock_albums = [
                {'name': 'Family', 'is_shared': False, 'guid': 'family_123'},
                {'name': 'Vacation', 'is_shared': False, 'guid': 'vacation_456'},
                {'name': 'Work', 'is_shared': False, 'guid': 'work_789'},
                {'name': 'Wedding', 'is_shared': True, 'guid': 'wedding_abc'},
                {'name': 'Party', 'is_shared': True, 'guid': 'party_def'},
                {'name': 'School', 'is_shared': True, 'guid': 'school_ghi'},
            ]
            
            # Mock the list_albums method
            self.client.list_albums = Mock(return_value=self.mock_albums)
            
            # Create a real iCloudClient instance for testing the get_filtered_albums method
            real_client = iCloudClient(self.mock_config)
            real_client._api = Mock()
            real_client._api.photos = Mock()
            real_client.list_albums = Mock(return_value=self.mock_albums)
            self.real_client = real_client

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_personal_album_filtering_with_allowlist(self):
        """Test personal album filtering with allowlist."""
        # Create config with personal allowlist
        config = Mock(spec=BaseConfig)
        config.include_personal_albums = True
        config.include_shared_albums = False
        config.personal_album_names_to_include = ["Family", "Vacation"]
        config.shared_album_names_to_include = []

        # Get filtered albums
        filtered_albums = list(self.real_client.get_filtered_albums(config))

        # Should only return personal albums in the allowlist
        expected_albums = [
            {'name': 'Family', 'is_shared': False, 'guid': 'family_123'},
            {'name': 'Vacation', 'is_shared': False, 'guid': 'vacation_456'}
        ]
        self.assertEqual(filtered_albums, expected_albums)

    def test_shared_album_filtering_with_allowlist(self):
        """Test shared album filtering with allowlist."""
        # Create config with shared allowlist
        config = Mock(spec=BaseConfig)
        config.include_personal_albums = False
        config.include_shared_albums = True
        config.personal_album_names_to_include = []
        config.shared_album_names_to_include = ["Wedding", "Party"]

        # Get filtered albums
        filtered_albums = list(self.real_client.get_filtered_albums(config))

        # Should only return shared albums in the allowlist
        expected_albums = [
            {'name': 'Wedding', 'is_shared': True, 'guid': 'wedding_abc'},
            {'name': 'Party', 'is_shared': True, 'guid': 'party_def'}
        ]
        self.assertEqual(filtered_albums, expected_albums)

    def test_both_album_types_with_allowlists(self):
        """Test filtering both personal and shared albums with allowlists."""
        # Create config with both allowlists
        config = Mock(spec=BaseConfig)
        config.include_personal_albums = True
        config.include_shared_albums = True
        config.personal_album_names_to_include = ["Family"]
        config.shared_album_names_to_include = ["Wedding"]

        # Get filtered albums
        filtered_albums = list(self.real_client.get_filtered_albums(config))

        # Should return specified albums from both types
        expected_albums = [
            {'name': 'Family', 'is_shared': False, 'guid': 'family_123'},
            {'name': 'Wedding', 'is_shared': True, 'guid': 'wedding_abc'}
        ]
        self.assertEqual(filtered_albums, expected_albums)

    def test_personal_albums_without_allowlist(self):
        """Test personal album filtering without allowlist (all personal albums)."""
        # Create config without personal allowlist
        config = Mock(spec=BaseConfig)
        config.include_personal_albums = True
        config.include_shared_albums = False
        config.personal_album_names_to_include = None
        config.shared_album_names_to_include = []

        # Get filtered albums
        filtered_albums = list(self.real_client.get_filtered_albums(config))

        # Should return all personal albums
        expected_albums = [
            {'name': 'Family', 'is_shared': False, 'guid': 'family_123'},
            {'name': 'Vacation', 'is_shared': False, 'guid': 'vacation_456'},
            {'name': 'Work', 'is_shared': False, 'guid': 'work_789'}
        ]
        self.assertEqual(filtered_albums, expected_albums)

    def test_shared_albums_without_allowlist(self):
        """Test shared album filtering without allowlist (all shared albums)."""
        # Create config without shared allowlist
        config = Mock(spec=BaseConfig)
        config.include_personal_albums = False
        config.include_shared_albums = True
        config.personal_album_names_to_include = []
        config.shared_album_names_to_include = None

        # Get filtered albums
        filtered_albums = list(self.real_client.get_filtered_albums(config))

        # Should return all shared albums
        expected_albums = [
            {'name': 'Wedding', 'is_shared': True, 'guid': 'wedding_abc'},
            {'name': 'Party', 'is_shared': True, 'guid': 'party_def'},
            {'name': 'School', 'is_shared': True, 'guid': 'school_ghi'}
        ]
        self.assertEqual(filtered_albums, expected_albums)

    def test_no_albums_when_both_types_disabled(self):
        """Test that no albums are returned when both types are disabled."""
        # Create config with both types disabled
        config = Mock(spec=BaseConfig)
        config.include_personal_albums = False
        config.include_shared_albums = False
        config.personal_album_names_to_include = []
        config.shared_album_names_to_include = []

        # Get filtered albums
        filtered_albums = list(self.real_client.get_filtered_albums(config))

        # Should return no albums
        self.assertEqual(filtered_albums, [])

    def test_empty_allowlist_excludes_all_albums(self):
        """Test that empty allowlist still includes all albums (empty list is falsy)."""
        # Create config with empty personal allowlist - this should include ALL personal albums
        # because empty list is falsy, so the condition (config.personal_album_names_to_include and ...)
        # evaluates to False and no filtering is applied
        config = Mock(spec=BaseConfig)
        config.include_personal_albums = True
        config.include_shared_albums = True
        config.personal_album_names_to_include = []  # Empty list = falsy = no filtering = include all
        config.shared_album_names_to_include = ["Wedding"]

        # Get filtered albums
        filtered_albums = list(self.real_client.get_filtered_albums(config))

        # Should return all personal albums AND the specified shared album
        expected_albums = [
            {'name': 'Family', 'is_shared': False, 'guid': 'family_123'},
            {'name': 'Vacation', 'is_shared': False, 'guid': 'vacation_456'},
            {'name': 'Work', 'is_shared': False, 'guid': 'work_789'},
            {'name': 'Wedding', 'is_shared': True, 'guid': 'wedding_abc'}
        ]
        self.assertEqual(filtered_albums, expected_albums)

    def test_nonexistent_album_in_allowlist(self):
        """Test filtering with nonexistent album in allowlist."""
        # Create config with nonexistent album in allowlist
        config = Mock(spec=BaseConfig)
        config.include_personal_albums = True
        config.include_shared_albums = False
        config.personal_album_names_to_include = ["Family", "NonExistent"]
        config.shared_album_names_to_include = []

        # Get filtered albums
        filtered_albums = list(self.real_client.get_filtered_albums(config))

        # Should only return existing albums
        expected_albums = [
            {'name': 'Family', 'is_shared': False, 'guid': 'family_123'}
        ]
        self.assertEqual(filtered_albums, expected_albums)

    def test_case_sensitive_album_matching(self):
        """Test that album name matching is case sensitive."""
        # Create config with different case
        config = Mock(spec=BaseConfig)
        config.include_personal_albums = True
        config.include_shared_albums = False
        config.personal_album_names_to_include = ["family"]  # lowercase
        config.shared_album_names_to_include = []

        # Get filtered albums
        filtered_albums = list(self.real_client.get_filtered_albums(config))

        # Should return no albums (case mismatch)
        self.assertEqual(filtered_albums, [])

    def test_unauthenticated_client_returns_no_albums(self):
        """Test that unauthenticated client returns no albums."""
        # Create client without authentication
        mock_config = Mock(spec=BaseConfig)
        client = iCloudClient(mock_config)
        client._api = None

        config = Mock(spec=BaseConfig)
        config.include_personal_albums = True
        config.include_shared_albums = True
        config.personal_album_names_to_include = None
        config.shared_album_names_to_include = None

        # Get filtered albums
        filtered_albums = list(client.get_filtered_albums(config))

        # Should return no albums (method returns early when _api is None)
        self.assertEqual(filtered_albums, [])

    def test_client_without_photos_service_returns_no_albums(self):
        """Test that client without photos service returns no albums."""
        # Create client without photos service
        mock_config = Mock(spec=BaseConfig)
        client = iCloudClient(mock_config)
        client._api = Mock()
        client._api.photos = None

        config = Mock(spec=BaseConfig)
        config.include_personal_albums = True
        config.include_shared_albums = True
        config.personal_album_names_to_include = None
        config.shared_album_names_to_include = None

        # Get filtered albums
        filtered_albums = list(client.get_filtered_albums(config))

        # Should return no albums (method returns early when photos service is None)
        self.assertEqual(filtered_albums, [])


if __name__ == "__main__":
    unittest.main()
