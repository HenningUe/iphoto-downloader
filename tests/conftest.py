"""Global test configuration and fixtures."""

import contextlib
import logging
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add the source directories to Python path
project_root = Path(__file__).parent.parent  # Go up to project root
sys.path.insert(0, str(project_root / "src" / "iphoto_downloader" / "src"))
sys.path.insert(0, str(project_root / "shared" / "auth2fa" / "src"))

# Import must be after path setup
from iphoto_downloader.logger import setup_logging  # noqa: E402


@pytest.fixture(autouse=True, scope="session")
def setup_test_logging():
    """Set up logging for all tests automatically at session level."""
    # Set up logging with INFO level for tests
    setup_logging(logging.INFO)
    yield
    # Cleanup: Reset logging configuration after session
    logging.getLogger().handlers.clear()


@pytest.fixture(autouse=True, scope="function")
def ensure_logging_per_test():
    """Ensure logging is available for each test function."""
    # Check if logging is set up, if not, set it up
    logger = logging.getLogger()
    if not logger.handlers:
        setup_logging(logging.INFO)
    yield


@pytest.fixture(autouse=True)
def clean_test_environment(monkeypatch):
    """Clean up environment variables that might interfere with tests."""
    # Preserve current working directory
    original_cwd = os.getcwd()

    # List of environment variables to preserve/clean
    env_vars_to_clean = [
        "ICLOUD_USERNAME",
        "ICLOUD_PASSWORD",
        "SYNC_DIRECTORY",
        "DRY_RUN",
        "LOG_LEVEL",
        "MAX_DOWNLOADS",
        "MAX_FILE_SIZE_MB",
        "INCLUDE_PERSONAL_ALBUMS",
        "INCLUDE_SHARED_ALBUMS",
        "PERSONAL_ALBUM_NAMES_TO_INCLUDE",
        "SHARED_ALBUM_NAMES_TO_INCLUDE",
        "DATABASE_PARENT_DIRECTORY",
        "EXECUTION_MODE",
        "SYNC_INTERVAL_MINUTES",
        "MAINTENANCE_INTERVAL_HOURS",
        "ALLOW_MULTI_INSTANCE",
        "PUSHOVER_DEVICE",
    ]

    # Clean environment variables
    for var in env_vars_to_clean:
        monkeypatch.delenv(var, raising=False)

    yield

    # Restore working directory
    os.chdir(original_cwd)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db():
    """Create a temporary database file for tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    with contextlib.suppress(PermissionError):
        Path(db_path).unlink(missing_ok=True)
