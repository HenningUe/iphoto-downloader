#!/usr/bin/env python3
import pytest
"""
Integration test to demonstrate continuous execution mode functionality.
"""

from icloud_photo_sync.logger import setup_logging
from icloud_photo_sync.continuous_runner import ContinuousRunner
from icloud_photo_sync.config import BaseConfig
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.append('src/icloud_photo_sync/src')


@pytest.mark.manual
def test_continuous_mode_demo():
    """Demonstrate continuous execution mode with a short demo."""

    print("🚀 Continuous Execution Mode Demo")
    print("=" * 40)

    # Create temporary directory and config
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test .env
        test_env_content = f"""
SYNC_DIRECTORY={temp_path}/photos
DRY_RUN=true
LOG_LEVEL=INFO
EXECUTION_MODE=continuous
SYNC_INTERVAL_MINUTES=1
MAINTENANCE_INTERVAL_HOURS=1
INCLUDE_PERSONAL_ALBUMS=true
INCLUDE_SHARED_ALBUMS=false
ENABLE_PUSHOVER=false
"""

        env_file = temp_path / "test.env"
        with open(env_file, 'w') as f:
            f.write(test_env_content)

        # Create config first
        config = BaseConfig(env_file)

        # Setup logging
        setup_logging(config.get_log_level())

        print("✅ Configuration created:")
        print(f"  - Execution mode: {config.execution_mode}")
        print(f"  - Sync interval: {config.sync_interval_minutes} minutes")
        print(f"  - Maintenance interval: {config.maintenance_interval_hours} hours")
        print(f"  - Sync directory: {config.sync_directory}")
        print(f"  - Dry run: {config.dry_run}")

        # Test single mode
        print("\n📍 Testing single execution mode...")
        config.execution_mode = 'single'
        runner = ContinuousRunner(config)

        success = runner.run_single_sync()
        print(f"✅ Single sync result: {'Success' if success else 'Failed'}")

        # Test that continuous mode can be started (but stop it quickly)
        print("\n🔄 Testing continuous execution mode (5 second demo)...")
        config.execution_mode = 'continuous'
        runner = ContinuousRunner(config)

        # Start continuous mode in a thread
        def run_continuous():
            runner.run_continuous_sync()

        continuous_thread = threading.Thread(target=run_continuous, daemon=True)
        continuous_thread.start()

        # Let it run for a few seconds
        time.sleep(5)

        # Stop it gracefully
        runner.stop()

        print("✅ Continuous mode started and stopped successfully")

        print("\n🎉 Continuous execution mode demo completed!")
        print("💡 The application now supports both single and continuous execution modes!")


if __name__ == "__main__":
    test_continuous_mode_demo()
