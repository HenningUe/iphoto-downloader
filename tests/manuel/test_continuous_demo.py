#!/usr/bin/env python3
import pytest

"""
Integration test to demonstrate continuous execution mode functionality.
"""

import sys
import tempfile
import threading
import time
from pathlib import Path

from iphoto_downloader.config import BaseConfig
from iphoto_downloader.continuous_runner import ContinuousRunner
from iphoto_downloader.logger import setup_logging

sys.path.append("src/iphoto_downloader/src")


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
        with open(env_file, "w") as f:
            f.write(test_env_content)

        # Create config first
        config = BaseConfig(env_file)

        # Setup logging
        setup_logging(config)

        # Ensure photos directory exists
        photos_dir = temp_path / "photos"
        photos_dir.mkdir(parents=True, exist_ok=True)

        print(f"📁 Using temporary directory: {temp_path}")
        print(f"📸 Photos will be saved to: {photos_dir}")
        print("🔄 This is a DRY RUN - no actual downloads will occur")
        print()

        # Test configuration
        print("⚙️ Configuration:")
        print(f"  - Sync Directory: {config.sync_directory}")
        print(f"  - Dry Run: {config.dry_run}")
        print(f"  - Log Level: {config.log_level}")
        print(f"  - Execution Mode: {config.execution_mode}")
        print(f"  - Sync Interval: {config.sync_interval_minutes} minutes")
        print()

        # Create a mock database directory and cleanup any existing files
        db_dir = temp_path / "data"
        if db_dir.exists():
            for db_file in db_dir.glob("*.db"):
                try:
                    db_file.unlink()
                except Exception as e:
                    print(f"Warning: Could not delete {db_file}: {e}")

        # Test single mode
        print("\n📍 Testing single execution mode...")
        config.execution_mode = "single"
        runner = ContinuousRunner(config)

        success = runner.run_single_sync()
        print(f"✅ Single sync result: {'Success' if success else 'Failed'}")

        # Test that continuous mode can be started (but stop it quickly)
        print("\n🔄 Testing continuous execution mode (5 second demo)...")
        config.execution_mode = "continuous"
        runner = ContinuousRunner(config)

        # Start continuous mode in a thread
        def run_continuous():
            runner.run_continuous_sync()

        continuous_thread = threading.Thread(target=run_continuous, daemon=True)
        continuous_thread.start()

        # Let it run for a few seconds
        time.sleep(5)

        # Stop it gracefully
        if hasattr(runner, '_stop_event'):
            runner._stop_event.set()
        elif hasattr(runner, 'stop'):
            runner.stop()

        print("🛑 Stopping continuous mode...")
        
        # Wait a bit for cleanup
        time.sleep(1)

        # Explicitly clean up any database files that might be locked
        db_dir = temp_path / "data"
        photos_db_dir = temp_path / "photos" / ".data"
        
        for db_path in [db_dir, photos_db_dir]:
            if db_path.exists():
                for db_file in db_path.glob("*.db"):
                    try:
                        # Force close any database connections
                        import gc
                        gc.collect()
                        time.sleep(0.1)  # Brief wait for cleanup
                        db_file.unlink()
                        print(f"✅ Cleaned up {db_file}")
                    except Exception as e:
                        print(f"⚠️ Warning: Could not delete {db_file}: {e}")
                        # Try to at least make it writable
                        try:
                            import stat
                            db_file.chmod(stat.S_IWRITE)
                            db_file.unlink()
                            print(f"✅ Forced cleanup of {db_file}")
                        except Exception as e2:
                            print(f"❌ Failed forced cleanup: {e2}")

        print("\n✅ Continuous mode demo completed!")
        print("💡 Note: This was a dry run with mock data")
        print("   In real usage, provide actual iCloud credentials")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])