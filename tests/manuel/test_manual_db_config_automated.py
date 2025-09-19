#!/usr/bin/env python3
"""Automated test for database path configuration."""

import logging
import os
import shutil
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch

from src.iphoto_downloader.src.iphoto_downloader.config import BaseConfig
from src.iphoto_downloader.src.iphoto_downloader.logger import setup_logging


@pytest.mark.manual
def test_database_path_configuration():
    """Test database path configuration with various settings."""
    
    # Set up logging with mock to prevent output during test
    with patch('src.iphoto_downloader.src.iphoto_downloader.logger.setup_logging'):
        setup_logging(log_level=logging.INFO)

    original_cwd = os.getcwd()

    # Test 1: Default path
    temp_dir1 = Path(tempfile.mkdtemp())
    try:
        os.chdir(temp_dir1)
        env_file = temp_dir1 / ".env"
        env_file.write_text("""
SYNC_DIRECTORY=./test_photos
DRY_RUN=true
LOG_LEVEL=INFO
ENABLE_PUSHOVER=false
""")

        config = BaseConfig(env_file)
        db_path = config.database_path

        assert db_path.parent.name == '.data', f"Expected '.data', got '{db_path.parent.name}'"

    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir1, ignore_errors=True)

    # Test 2: Custom relative path
    temp_dir2 = Path(tempfile.mkdtemp())
    try:
        os.chdir(temp_dir2)
        env_file = temp_dir2 / ".env"
        env_file.write_text("""
SYNC_DIRECTORY=./test_photos
DATABASE_PARENT_DIRECTORY=custom_db
DRY_RUN=true
LOG_LEVEL=INFO
ENABLE_PUSHOVER=false
""")

        config = BaseConfig(env_file)
        db_path = config.database_path

        assert db_path.parent.name == 'custom_db', f"Expected 'custom_db', got '{db_path.parent.name}'"

    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir2, ignore_errors=True)

    # Test 3: Absolute path
    temp_dir3 = Path(tempfile.mkdtemp())
    absolute_db_dir = temp_dir3 / "absolute_db"
    try:
        os.chdir(temp_dir3)
        env_file = temp_dir3 / ".env"
        env_file.write_text(f"""
SYNC_DIRECTORY=./test_photos
DATABASE_PARENT_DIRECTORY={absolute_db_dir}
DRY_RUN=true
LOG_LEVEL=INFO
ENABLE_PUSHOVER=false
""")

        config = BaseConfig(env_file)
        db_path = config.database_path

        assert str(absolute_db_dir) in str(db_path), "Database path should contain absolute path"

    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir3, ignore_errors=True)


if __name__ == "__main__":
    test_database_path_configuration()
    print("✅ Database path configuration test passed!")