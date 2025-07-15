"""Shared test utilities and fixtures."""

import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
import pytest
from unittest.mock import Mock


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path

    # Windows-specific cleanup with retry
    def cleanup_dir(path, retries=3):
        import time
        import os
        for attempt in range(retries):
            try:
                # Force close any open file handles
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            os.chmod(file_path, 0o777)
                        except Exception:
                            pass

                shutil.rmtree(path)
                break
            except PermissionError:
                if attempt < retries - 1:
                    time.sleep(0.1 * (attempt + 1))  # Progressive delay
                    continue
                else:
                    # If all attempts fail, try to clean up what we can
                    print(f"Warning: Could not completely clean up {path}")

    cleanup_dir(temp_path)


@pytest.fixture
def mock_config(temp_dir):
    """Create a mock configuration for testing."""
    from icloud_photo_sync.config import BaseConfig

    config = Mock(spec=BaseConfig)
    config.icloud_username = "test@example.com"
    config.icloud_password = "test-password"
    config.sync_directory = temp_dir / "photos"
    config.dry_run = False
    config.log_level = "INFO"
    config.max_downloads = 0
    config.max_file_size_mb = 0
    config.ensure_sync_directory.return_value = None
    config.get_log_level.return_value = 20  # INFO level

    return config


@pytest.fixture
def mock_icloud_photo():
    """Create a mock iCloud photo object."""
    photo = Mock()
    photo.filename = "test_photo.jpg"
    photo.size = 1024 * 1024  # 1MB
    photo.created = "2023-01-01T12:00:00Z"
    photo.download.return_value = b"fake_image_data"
    return photo


@pytest.fixture
def mock_icloud_service():
    """Create a mock iCloud service."""
    service = Mock()
    service.photos = Mock()
    service.photos.all = Mock(return_value=[])
    service.requires_2sa = False
    service.requires_2fa = False
    return service


class MockPhotoInfo:
    """Mock photo info for testing."""

    def __init__(self, filename: str, size: int = 1024, created: str = "2023-01-01T12:00:00Z"):
        self.filename = filename
        self.size = size
        self.created = created
        self.download_url = f"https://example.com/{filename}"

    def download(self) -> bytes:
        """Mock download method."""
        return b"fake_image_data"


def create_test_photo_info(filename: str, **kwargs) -> Dict[str, Any]:
    """Create test photo info dictionary."""
    return {
        'filename': filename,
        'size': kwargs.get('size', 1024 * 1024),
        'created': kwargs.get('created', '2023-01-01T12:00:00Z'),
        'download_url': kwargs.get('download_url', f'https://example.com/{filename}'),
        'id': kwargs.get('id', f'photo_{filename}'),
        'type': kwargs.get('type', 'image/jpeg'),
    }


def create_test_files(directory: Path, filenames: list[str]) -> None:
    """Create test files in the given directory."""
    directory.mkdir(parents=True, exist_ok=True)
    for filename in filenames:
        (directory / filename).write_bytes(b"test file content")


def assert_file_exists(file_path: Path, should_exist: bool = True) -> None:
    """Assert that a file exists or doesn't exist."""
    if should_exist:
        assert file_path.exists(), f"File {file_path} should exist"
    else:
        assert not file_path.exists(), f"File {file_path} should not exist"


def assert_file_content(file_path: Path, expected_content: bytes) -> None:
    """Assert that a file contains expected content."""
    assert file_path.read_bytes() == expected_content
