"""Unit tests for adaptive sync delay and persistence in PhotoSyncer."""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from iphoto_downloader.config import BaseConfig
from iphoto_downloader.sync import PhotoSyncer


class DummyConfig(BaseConfig):
    def __init__(self, tmp_path):
        env_file_path = tmp_path / ".env"
        env_file_path.write_text("")
        super().__init__(env_file_path=env_file_path)
        self.sync_directory = tmp_path / "photos"
        self.sync_directory.mkdir(parents=True, exist_ok=True)
        self._test_database_path = tmp_path / "db.sqlite"
        self.dry_run = True
        self.max_downloads = 0
        self.ensure_sync_directory = lambda: None
        self.validate_albums_exist = lambda icloud_client: None

    @property
    def database_path(self):
        return self._test_database_path

    def get_log_level(self, fallback_lvl=30):
        return 30  # WARNING


@pytest.fixture
def syncer(tmp_path):
    config = DummyConfig(tmp_path)
    # Create syncer instance
    s = PhotoSyncer(config)
    # Set delay file to a temp location after instance creation
    s._sync_delay_file = Path(tempfile.gettempdir()) / f"test_sync_delay_{os.getpid()}.json"
    # Reset to initial state for consistent testing
    s._sync_delay_seconds = s._SYNC_DELAY_INITIAL
    # Clean up any existing delay file
    if s._sync_delay_file.exists():
        s._sync_delay_file.unlink()
    yield s
    # Cleanup
    if s._sync_delay_file.exists():
        s._sync_delay_file.unlink()


def test_initial_delay(syncer):
    """Test initial delay and file absence."""
    assert syncer._sync_delay_seconds == syncer._SYNC_DELAY_INITIAL
    assert not syncer._sync_delay_file.exists()


def test_increase_and_persist_delay(syncer):
    """Test delay doubling and persistence across restarts."""
    syncer._increase_sync_delay()
    assert syncer._sync_delay_seconds == syncer._SYNC_DELAY_INITIAL * 2
    # Simulate process restart
    s2 = PhotoSyncer(syncer.config)
    assert s2._sync_delay_seconds == syncer._SYNC_DELAY_INITIAL * 2


def test_delay_capped(syncer):
    syncer._sync_delay_seconds = syncer._SYNC_DELAY_MAX // 2
    """Test handling of corrupt delay file."""
    syncer._increase_sync_delay()
    assert syncer._sync_delay_seconds == syncer._SYNC_DELAY_MAX
    syncer._increase_sync_delay()
    assert syncer._sync_delay_seconds == syncer._SYNC_DELAY_MAX


def test_reset_delay(syncer):
    syncer._increase_sync_delay()
    syncer._reset_sync_delay()
    assert syncer._sync_delay_seconds == syncer._SYNC_DELAY_INITIAL
    assert not syncer._sync_delay_file.exists()


def test_load_corrupt_file(syncer):
    # Write invalid JSON
    syncer._sync_delay_file.write_text("not a json")
    # Should fallback to initial
    s2 = PhotoSyncer(syncer.config)
    # Set the same delay file path for consistent testing
    s2._sync_delay_file = syncer._sync_delay_file
    # Reload from the corrupted file
    s2._sync_delay_seconds = s2._load_sync_delay()
    assert s2._sync_delay_seconds == syncer._SYNC_DELAY_INITIAL
    s2._reset_sync_delay()
