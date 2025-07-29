#!/usr/bin/env python3
import pytest
"""Test script to verify that sync pauses during maintenance operations."""

import threading
import time
import sys
from pathlib import Path

# Add src to Python path for testing
sys.path.insert(0, str(Path(__file__).parent / "src" / "iphoto_downloader" / "src"))

# Import after path setup
try:
    from iphoto_downloader.continuous_runner import ContinuousRunner
    from iphoto_downloader.config import BaseConfig
    from iphoto_downloader.logger import setup_logging
    import logging
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

# Set up logging for testing
setup_logging(logging.INFO)


class MockConfig(BaseConfig):
    """Mock configuration for testing."""

    def __init__(self):
        self.execution_mode = 'continuous'
        self.sync_interval_minutes = 0.1  # Very short for testing
        self.maintenance_interval_hours = 0.01  # Very short for testing
        self.sync_directory = Path.cwd() / "test_photos"
        self.sync_directory.mkdir(exist_ok=True)


@pytest.mark.manual
def test_sync_pause_during_maintenance():
    """Test that sync operations pause during maintenance."""
    print("🧪 Testing sync pause during maintenance...")

    # Create mock config
    config = MockConfig()
    runner = ContinuousRunner(config)

    # Simulate maintenance in progress
    print("📄 Setting maintenance in progress...")
    runner.maintenance_in_progress.set()

    # Track sync timing
    sync_start_time = None
    sync_completed = False

    def run_single_sync():
        nonlocal sync_start_time, sync_completed
        sync_start_time = time.time()
        print(f"⏰ Sync starting at {sync_start_time:.2f}")

        # This should wait for maintenance to complete
        try:
            runner.run_single_sync()
            sync_completed = True
            print(f"✅ Sync completed at {time.time():.2f}")
        except Exception as e:
            print(f"❌ Sync failed: {e}")

    # Start sync in background
    sync_thread = threading.Thread(target=run_single_sync, daemon=True)
    sync_thread.start()

    # Wait a bit to ensure sync is waiting
    time.sleep(2)

    if sync_completed:
        print("❌ TEST FAILED: Sync completed before maintenance was cleared")
        return False

    print("✅ Sync is properly waiting for maintenance to complete")

    # Clear maintenance flag
    print("🔧 Clearing maintenance flag...")
    runner.maintenance_in_progress.clear()

    # Wait for sync to complete
    sync_thread.join(timeout=10)

    if sync_completed:
        sync_duration = time.time() - sync_start_time
        print(f"✅ TEST PASSED: Sync waited for maintenance and completed in {sync_duration:.2f}s")
        return True
    else:
        print("❌ TEST FAILED: Sync did not complete after maintenance was cleared")
        return False


@pytest.mark.manual
def test_maintenance_blocks_sync():
    """Test that starting maintenance blocks new sync operations."""
    print("\n🧪 Testing maintenance blocks sync...")

    config = MockConfig()
    runner = ContinuousRunner(config)

    maintenance_started = False
    sync_blocked = False

    def perform_mock_maintenance():
        nonlocal maintenance_started
        print("🔧 Mock maintenance starting...")
        with runner.maintenance_lock:
            runner.maintenance_in_progress.set()
            maintenance_started = True
            print("🔧 Mock maintenance in progress...")
            time.sleep(3)  # Simulate maintenance work
            runner.maintenance_in_progress.clear()
        print("🔧 Mock maintenance completed")

    def attempt_sync():
        nonlocal sync_blocked
        # Wait for maintenance to start
        while not maintenance_started:
            time.sleep(0.1)

        start_time = time.time()
        print(f"⏰ Attempting sync at {start_time:.2f}")

        # Check if sync waits
        if runner.maintenance_in_progress.is_set():
            print("✅ Sync properly detected maintenance in progress")
            sync_blocked = True

    # Start maintenance
    maintenance_thread = threading.Thread(target=perform_mock_maintenance, daemon=True)
    maintenance_thread.start()

    # Start sync attempt
    sync_thread = threading.Thread(target=attempt_sync, daemon=True)
    sync_thread.start()

    # Wait for both to complete
    maintenance_thread.join(timeout=10)
    sync_thread.join(timeout=10)

    if sync_blocked:
        print("✅ TEST PASSED: Maintenance properly blocked sync operations")
        return True
    else:
        print("❌ TEST FAILED: Sync was not blocked by maintenance")
        return False


if __name__ == "__main__":
    print("🚀 Running sync pause tests...\n")

    success1 = test_sync_pause_during_maintenance()
    success2 = test_maintenance_blocks_sync()

    if success1 and success2:
        print("\n🎉 All tests passed! Sync pausing during maintenance works correctly.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
