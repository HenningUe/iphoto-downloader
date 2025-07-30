import pytest

"""Manual test script for multi-instance control functionality."""

import os
import sys
import tempfile
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src" / "iphoto_downloader" / "src"))

from iphoto_downloader.config import BaseConfig
from iphoto_downloader.instance_manager import (
    InstanceManager,
    validate_multi_instance_config,
)


@pytest.mark.manual
def test_validate_multi_instance_config():
    """Test the validation function."""
    print("Testing validate_multi_instance_config...")

    # Test valid values
    assert validate_multi_instance_config(True) == True
    assert validate_multi_instance_config(False) == True
    print("✅ Valid boolean values work correctly")

    # Test invalid values
    try:
        validate_multi_instance_config("true")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "allow_multi_instance must be a boolean" in str(e)
        print("✅ Invalid string value properly rejected")

    try:
        validate_multi_instance_config(1)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "allow_multi_instance must be a boolean" in str(e)
        print("✅ Invalid number value properly rejected")


@pytest.mark.manual
def test_config_integration():
    """Test integration with config system."""
    print("\nTesting config integration...")

    # Create temporary env file
    temp_dir = tempfile.mkdtemp()
    temp_env_file = Path(temp_dir) / ".env"

    try:
        # Test default value (false)
        temp_env_file.write_text("""
SYNC_DIRECTORY=./photos
DRY_RUN=false
ENABLE_PUSHOVER=false
""")

        config = BaseConfig(temp_env_file)
        assert config.allow_multi_instance == False
        print("✅ Default multi-instance setting is False")

        # Test explicit true
        temp_env_file.write_text("""
SYNC_DIRECTORY=./photos
DRY_RUN=false
ENABLE_PUSHOVER=false
ALLOW_MULTI_INSTANCE=true
""")

        config = BaseConfig(temp_env_file)
        assert config.allow_multi_instance == True
        print("✅ Explicit true setting works")

        # Test explicit false
        temp_env_file.write_text("""
SYNC_DIRECTORY=./photos
DRY_RUN=false
ENABLE_PUSHOVER=false
ALLOW_MULTI_INSTANCE=false
""")

        config = BaseConfig(temp_env_file)
        assert config.allow_multi_instance == False
        print("✅ Explicit false setting works")

    finally:
        # Cleanup
        if temp_env_file.exists():
            temp_env_file.unlink()
        os.rmdir(temp_dir)


@pytest.mark.manual
def test_instance_manager_basic():
    """Test basic InstanceManager functionality."""
    print("\nTesting InstanceManager basic functionality...")

    # Test multi-instance allowed
    manager = InstanceManager(allow_multi_instance=True)
    result = manager.check_and_acquire_lock()
    assert result == True
    print("✅ Multi-instance mode allows execution")

    # Test lock file path generation
    manager = InstanceManager(allow_multi_instance=False)
    assert "iphoto_downloader.lock" in str(manager.lock_file_path)
    print("✅ Lock file path is generated correctly")


def main():
    """Run all tests."""
    print("🧪 Running Multi-Instance Control Manual Tests")
    print("=" * 50)

    try:
        test_validate_multi_instance_config()
        test_config_integration()
        test_instance_manager_basic()

        print("\n🎉 All tests passed!")
        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
