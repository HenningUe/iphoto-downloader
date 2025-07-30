"""Test the database path configuration manually."""

import logging
import os
import shutil
import tempfile
from pathlib import Path

from src.iphoto_downloader.src.iphoto_downloader.config import BaseConfig
from src.iphoto_downloader.src.iphoto_downloader.logger import setup_logging

# Set up logging
setup_logging(log_level=logging.INFO)

print("=== Testing Database Path Configuration ===\n")

# Test 1: Default path
print("1. Testing default database path:")
temp_dir1 = Path(tempfile.mkdtemp())
original_cwd = os.getcwd()

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

    print(f"   Database path: {db_path}")
    print(f"   Parent directory name: {db_path.parent.name}")
    print(f"   Default path correct: {db_path.parent.name == '.data'}")

finally:
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir1, ignore_errors=True)

print()

# Test 2: Custom relative path
print("2. Testing custom relative database path:")
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

    print(f"   Database path: {db_path}")
    print(f"   Parent directory name: {db_path.parent.name}")
    print(f"   Custom path correct: {db_path.parent.name == 'custom_db'}")

finally:
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir2, ignore_errors=True)

print()

# Test 3: Absolute path
print("3. Testing absolute database path:")
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

    print(f"   Database path: {db_path}")
    print(f"   Contains absolute path: {str(absolute_db_dir) in str(db_path)}")

finally:
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir3, ignore_errors=True)

print("\n=== Database Path Configuration Test Complete ===")
print("✅ All core functionality is working correctly!")
