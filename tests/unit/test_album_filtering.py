"""Tests for album filtering functionality."""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock
import logging

from src.icloud_photo_sync.src.icloud_photo_sync.logger import setup_logging
from src.icloud_photo_sync.src.icloud_photo_sync.icloud_client import iCloudClient
from src.icloud_photo_sync.src.icloud_photo_sync.config import BaseConfig


class TestAlbumFiltering(unittest.TestCase):
    """Test album filtering functionality."""

    def setUp(self):
        """Set up test fixtures."""
        setup_logging(log_level=logging.INFO)

        self.temp_dir = Path(tempfile.mkdtemp())
        self.env_file = self.temp_dir / ".env"

        # Create test .env file
        self.env_file.write_text("""
SYNC_DIRECTORY=./test_photos
DRY_RUN=true
LOG_LEVEL=INFO
PERSONAL_ALBUMS_ALLOWLIST=Family,Vacation
SHARED_ALBUMS_ALLOWLIST=Wedding,Party
""")

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_personal_album_filtering_with_allowlist(self):
        """Test personal album filtering with allowlist."""
        from src.icloud_photo_sync.src.icloud_photo_sync.album_filter import (
            AlbumFilter
        )

        # Create album filter with personal allowlist
        config = Mock()
        config.personal_albums_allowlist = ["Family", "Vacation", "Pets"]
        config.shared_albums_allowlist = []
        config.enable_shared_albums = False

        album_filter = AlbumFilter(config)

        # Test personal albums that should be included
        self.assertTrue(album_filter.should_include_album("Family", is_shared=False))
        self.assertTrue(album_filter.should_include_album("Vacation", is_shared=False))
        self.assertTrue(album_filter.should_include_album("Pets", is_shared=False))

        # Test personal albums that should be excluded
        self.assertFalse(album_filter.should_include_album("Work", is_shared=False))
        self.assertFalse(album_filter.should_include_album("Random", is_shared=False))

    def test_shared_album_filtering_with_allowlist(self):
        """Test shared album filtering with allowlist."""
        from src.icloud_photo_sync.src.icloud_photo_sync.album_filter import (
            AlbumFilter
        )

        # Create album filter with shared allowlist
        config = Mock()
        config.personal_albums_allowlist = []
        config.shared_albums_allowlist = ["Wedding", "Party", "Group Trip"]
        config.enable_shared_albums = True

        album_filter = AlbumFilter(config)

        # Test shared albums that should be included
        self.assertTrue(album_filter.should_include_album("Wedding", is_shared=True))
        self.assertTrue(album_filter.should_include_album("Party", is_shared=True))
        self.assertTrue(album_filter.should_include_album("Group Trip", is_shared=True))

        # Test shared albums that should be excluded
        self.assertFalse(album_filter.should_include_album("Other Event", is_shared=True))
        self.assertFalse(album_filter.should_include_album("Private", is_shared=True))

    def test_mixed_album_filtering(self):
        """Test mixed personal and shared album filtering."""
        from src.icloud_photo_sync.src.icloud_photo_sync.album_filter import (
            AlbumFilter
        )

        config = Mock()
        config.personal_albums_allowlist = ["Family", "Vacation"]
        config.shared_albums_allowlist = ["Wedding", "Party"]
        config.enable_shared_albums = True

        album_filter = AlbumFilter(config)

        # Test personal albums
        self.assertTrue(album_filter.should_include_album("Family", is_shared=False))
        self.assertFalse(album_filter.should_include_album("Work", is_shared=False))

        # Test shared albums
        self.assertTrue(album_filter.should_include_album("Wedding", is_shared=True))
        self.assertFalse(album_filter.should_include_album("Other", is_shared=True))

    def test_album_filtering_disabled_shared_albums(self):
        """Test album filtering when shared albums are disabled."""
        from src.icloud_photo_sync.src.icloud_photo_sync.album_filter import (
            AlbumFilter
        )

        config = Mock()
        config.personal_albums_allowlist = ["Family"]
        config.shared_albums_allowlist = ["Wedding"]
        config.enable_shared_albums = False

        album_filter = AlbumFilter(config)

        # Personal albums should work as expected
        self.assertTrue(album_filter.should_include_album("Family", is_shared=False))

        # Shared albums should always be excluded when disabled
        self.assertFalse(album_filter.should_include_album("Wedding", is_shared=True))
        self.assertFalse(album_filter.should_include_album("Any Shared", is_shared=True))

    def test_empty_allowlists_behavior(self):
        """Test behavior with empty allowlists."""
        from src.icloud_photo_sync.src.icloud_photo_sync.album_filter import (
            AlbumFilter
        )

        config = Mock()
        config.personal_albums_allowlist = []
        config.shared_albums_allowlist = []
        config.enable_shared_albums = True

        album_filter = AlbumFilter(config)

        # Empty allowlists should include all albums
        self.assertTrue(album_filter.should_include_album("Any Personal", is_shared=False))
        self.assertTrue(album_filter.should_include_album("Any Shared", is_shared=True))

    def test_case_insensitive_album_matching(self):
        """Test case-insensitive album name matching."""
        from src.icloud_photo_sync.src.icloud_photo_sync.album_filter import (
            AlbumFilter
        )

        config = Mock()
        config.personal_albums_allowlist = ["Family", "VACATION"]
        config.shared_albums_allowlist = ["wedding"]
        config.enable_shared_albums = True

        album_filter = AlbumFilter(config)

        # Test case variations
        self.assertTrue(album_filter.should_include_album("family", is_shared=False))
        self.assertTrue(album_filter.should_include_album("FAMILY", is_shared=False))
        self.assertTrue(album_filter.should_include_album("vacation", is_shared=False))
        self.assertTrue(album_filter.should_include_album("Vacation", is_shared=False))
        self.assertTrue(album_filter.should_include_album("Wedding", is_shared=True))
        self.assertTrue(album_filter.should_include_album("WEDDING", is_shared=True))

    def test_special_album_handling(self):
        """Test handling of special album types."""
        from src.icloud_photo_sync.src.icloud_photo_sync.album_filter import (
            AlbumFilter
        )

        config = Mock()
        config.personal_albums_allowlist = ["Family"]
        config.shared_albums_allowlist = []
        config.enable_shared_albums = False
        config.include_all_photos = True
        config.include_recently_deleted = False

        album_filter = AlbumFilter(config)

        # Test special albums
        self.assertTrue(album_filter.should_include_album("All Photos", is_shared=False))
        self.assertFalse(album_filter.should_include_album("Recently Deleted", is_shared=False))

        # Test with recently deleted enabled
        config.include_recently_deleted = True
        album_filter = AlbumFilter(config)
        self.assertTrue(album_filter.should_include_album("Recently Deleted", is_shared=False))

    def test_album_pattern_matching(self):
        """Test pattern-based album matching."""
        from src.icloud_photo_sync.src.icloud_photo_sync.album_filter import (
            AlbumFilter
        )

        config = Mock()
        config.personal_albums_allowlist = ["Family*", "*Vacation*", "*Trip"]
        config.shared_albums_allowlist = []
        config.enable_shared_albums = False

        album_filter = AlbumFilter(config)

        # Test pattern matching
        self.assertTrue(album_filter.should_include_album("Family Photos", is_shared=False))
        self.assertTrue(album_filter.should_include_album("Family 2023", is_shared=False))
        self.assertTrue(album_filter.should_include_album(
            "Summer Vacation Photos", is_shared=False))
        self.assertTrue(album_filter.should_include_album("Europe Trip", is_shared=False))
        self.assertTrue(album_filter.should_include_album("Road Trip", is_shared=False))

        # Test non-matching patterns
        self.assertFalse(album_filter.should_include_album("Work Photos", is_shared=False))
        self.assertFalse(album_filter.should_include_album("Random", is_shared=False))

    def test_album_priority_logic(self):
        """Test album priority logic for overlapping names."""
        from src.icloud_photo_sync.src.icloud_photo_sync.album_filter import (
            AlbumFilter
        )

        config = Mock()
        config.personal_albums_allowlist = ["Family"]
        config.shared_albums_allowlist = ["Family"]  # Same name in both lists
        config.enable_shared_albums = True

        album_filter = AlbumFilter(config)

        # Both personal and shared "Family" albums should be included
        self.assertTrue(album_filter.should_include_album("Family", is_shared=False))
        self.assertTrue(album_filter.should_include_album("Family", is_shared=True))

    def test_album_metadata_filtering(self):
        """Test filtering based on album metadata."""
        from src.icloud_photo_sync.src.icloud_photo_sync.album_filter import (
            AlbumFilter
        )

        config = Mock()
        config.personal_albums_allowlist = []
        config.shared_albums_allowlist = []
        config.enable_shared_albums = True
        config.filter_by_date_range = True
        config.start_date = "2023-01-01"
        config.end_date = "2023-12-31"

        album_filter = AlbumFilter(config)

        # Mock album metadata
        album_metadata = {
            "name": "Family Photos",
            "is_shared": False,
            "created_date": "2023-06-15",
            "photo_count": 50
        }

        # Test metadata-based filtering
        result = album_filter.should_include_album_with_metadata(album_metadata)
        self.assertTrue(result)

        # Test album outside date range
        album_metadata["created_date"] = "2022-06-15"
        result = album_filter.should_include_album_with_metadata(album_metadata)
        self.assertFalse(result)

    def test_dynamic_album_discovery(self):
        """Test dynamic album discovery and filtering."""
        from src.icloud_photo_sync.src.icloud_photo_sync.album_filter import (
            AlbumFilter
        )
        from src.icloud_photo_sync.src.icloud_photo_sync.icloud_client import (
            iCloudClient
        )

        # Mock iCloud client
        mock_client = Mock(spec=iCloudClient)
        mock_albums = [
            {"name": "Family", "is_shared": False, "photo_count": 10},
            {"name": "Work", "is_shared": False, "photo_count": 5},
            {"name": "Wedding", "is_shared": True, "photo_count": 20},
            {"name": "Private", "is_shared": True, "photo_count": 3}
        ]
        mock_client.get_albums.return_value = mock_albums

        config = Mock()
        config.personal_albums_allowlist = ["Family"]
        config.shared_albums_allowlist = ["Wedding"]
        config.enable_shared_albums = True

        album_filter = AlbumFilter(config)

        # Test filtering discovered albums
        filtered_albums = album_filter.filter_albums(mock_albums)

        self.assertEqual(len(filtered_albums), 2)
        album_names = [album["name"] for album in filtered_albums]
        self.assertIn("Family", album_names)
        self.assertIn("Wedding", album_names)
        self.assertNotIn("Work", album_names)
        self.assertNotIn("Private", album_names)

    def test_album_sync_coordination(self):
        """Test album filtering coordination with sync process."""
        from src.icloud_photo_sync.src.icloud_photo_sync.album_filter import (
            AlbumFilter
        )
        from src.icloud_photo_sync.src.icloud_photo_sync.sync import PhotoSync

        # Mock PhotoSync
        mock_sync = Mock(spec=PhotoSync)

        config = Mock()
        config.personal_albums_allowlist = ["Family", "Vacation"]
        config.shared_albums_allowlist = ["Wedding"]
        config.enable_shared_albums = True

        album_filter = AlbumFilter(config)

        # Mock albums from sync process
        sync_albums = [
            {"name": "Family", "is_shared": False},
            {"name": "Work", "is_shared": False},
            {"name": "Wedding", "is_shared": True},
            {"name": "Other", "is_shared": True}
        ]

        # Test integration with sync process
        filtered_albums = []
        for album in sync_albums:
            if album_filter.should_include_album(album["name"], album["is_shared"]):
                filtered_albums.append(album)

        self.assertEqual(len(filtered_albums), 2)
        self.assertEqual(filtered_albums[0]["name"], "Family")
        self.assertEqual(filtered_albums[1]["name"], "Wedding")

    def test_album_filtering_performance(self):
        """Test album filtering performance with large album lists."""
        from src.icloud_photo_sync.src.icloud_photo_sync.album_filter import (
            AlbumFilter
        )
        import time

        config = Mock()
        config.personal_albums_allowlist = ["Family", "Vacation", "Work"]
        config.shared_albums_allowlist = ["Wedding", "Party"]
        config.enable_shared_albums = True

        album_filter = AlbumFilter(config)

        # Create large list of albums to test performance
        large_album_list = []
        for i in range(1000):
            large_album_list.append({
                "name": f"Album_{i}",
                "is_shared": i % 2 == 0
            })

        # Add some albums that should match
        large_album_list.extend([
            {"name": "Family", "is_shared": False},
            {"name": "Wedding", "is_shared": True}
        ])

        # Test filtering performance
        start_time = time.time()
        filtered_albums = album_filter.filter_albums(large_album_list)
        end_time = time.time()

        # Should complete quickly (under 1 second for 1000+ albums)
        self.assertLess(end_time - start_time, 1.0)

        # Should find the matching albums
        self.assertEqual(len(filtered_albums), 2)
        album_names = [album["name"] for album in filtered_albums]
        self.assertIn("Family", album_names)
        self.assertIn("Wedding", album_names)


if __name__ == '__main__':
    unittest.main()
