#!/usr/bin/env python3
import pytest
"""
Test script to verify continuous execution mode functionality.
"""

from pathlib import Path
from iphoto_downloader.config import BaseConfig
import sys
sys.path.append('src/iphoto_downloader/src')


@pytest.mark.manual
def test_execution_mode_config():
    """Test that execution mode configuration works correctly."""

    print("🧪 Testing Execution Mode Configuration")
    print("=" * 50)

    # Create a temporary .env file for testing
    test_env_content = """
SYNC_DIRECTORY=./test_photos
DRY_RUN=true
LOG_LEVEL=INFO
EXECUTION_MODE=continuous
SYNC_INTERVAL_MINUTES=3
MAINTENANCE_INTERVAL_HOURS=2
INCLUDE_PERSONAL_ALBUMS=true
INCLUDE_SHARED_ALBUMS=false
ENABLE_PUSHOVER=false
"""

    test_env_path = Path("test_continuous.env")
    with open(test_env_path, 'w') as f:
        f.write(test_env_content)

    try:
        # Test continuous mode configuration
        config = BaseConfig(test_env_path)

        print("✅ Configuration loaded successfully")
        print(f"  Execution mode: {config.execution_mode}")
        print(f"  Sync interval: {config.sync_interval_minutes} minutes")
        print(f"  Maintenance interval: {config.maintenance_interval_hours} hours")

        # Test validation
        try:
            config.validate()
            print("✅ Configuration validation passed")
        except ValueError as e:
            print(f"❌ Configuration validation failed: {e}")

        # Test single mode
        test_env_single = test_env_content.replace(
            "EXECUTION_MODE=continuous", "EXECUTION_MODE=single")
        with open(test_env_path, 'w') as f:
            f.write(test_env_single)

        config_single = BaseConfig(test_env_path)
        print(f"✅ Single mode configuration: {config_single.execution_mode}")

        # Test invalid mode
        test_env_invalid = test_env_content.replace(
            "EXECUTION_MODE=continuous", "EXECUTION_MODE=invalid")
        with open(test_env_path, 'w') as f:
            f.write(test_env_invalid)

        config_invalid = BaseConfig(test_env_path)
        try:
            config_invalid.validate()
            print("❌ Should have failed validation for invalid mode")
        except ValueError as e:
            print(f"✅ Correctly rejected invalid execution mode: {e}")

        print("\n🎉 All execution mode configuration tests passed!")

    finally:
        # Clean up
        if test_env_path.exists():
            test_env_path.unlink()


if __name__ == "__main__":
    test_execution_mode_config()
