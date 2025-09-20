"""Unit tests for adaptive sync delay and persistence in PhotoSyncer."""

import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from iphoto_downloader.config import BaseConfig
from iphoto_downloader.sync import PhotoSyncer


class DummyConfig(BaseConfig):
    def __init__(self, tmp_path):
        super().__init__()
        self.sync_directory = tmp_path / "photos"
        self.sync_directory.mkdir(parents=True, exist_ok=True)
        self.database_path = tmp_path / "db.sqlite"
        self.dry_run = True
        self.max_downloads = 0
        self.get_log_level = lambda: "WARNING"
        self.ensure_sync_directory = lambda: None
        self.validate_albums_exist = lambda icloud_client: None


@pytest.fixture
def syncer(tmp_path):
    config = DummyConfig(tmp_path)
    # Patch the delay file to a temp location
    with mock.patch.object(
        PhotoSyncer,
        "_sync_delay_file",
        Path(tempfile.gettempdir()) / f"test_sync_delay_{os.getpid()}.json",
    ):
        s = PhotoSyncer(config)
        yield s
        # Cleanup
        if s._sync_delay_file.exists():
            s._sync_delay_file.unlink()


def test_initial_delay(syncer):
    assert syncer._sync_delay_seconds == syncer._SYNC_DELAY_INITIAL
    assert not syncer._sync_delay_file.exists()


def test_increase_and_persist_delay(syncer):
    syncer._increase_sync_delay()
    assert syncer._sync_delay_seconds == syncer._SYNC_DELAY_INITIAL * 2
    # Simulate process restart
    s2 = PhotoSyncer(syncer.config)
    assert s2._sync_delay_seconds == syncer._SYNC_DELAY_INITIAL * 2


def test_delay_capped(syncer):
    syncer._sync_delay_seconds = syncer._SYNC_DELAY_MAX // 2
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
    assert s2._sync_delay_seconds == syncer._SYNC_DELAY_INITIAL
    s2._reset_sync_delay()
