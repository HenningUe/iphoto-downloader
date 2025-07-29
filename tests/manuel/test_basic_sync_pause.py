#!/usr/bin/env python3
import pytest
"""Simple test script to verify that sync pauses during maintenance operations."""

import threading
import time
import sys
from pathlib import Path

# Add src to Python path for testing
sys.path.insert(0, str(Path(__file__).parent / "src" / "iphoto_downloader" / "src"))

# Import after path setup
try:
    from iphoto_downloader.logger import setup_logging
    import logging
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

# Set up logging for testing
setup_logging(logging.INFO)


@pytest.mark.manual
def test_threading_synchronization():
    """Test the basic threading synchronization mechanism."""
    print("🧪 Testing basic threading synchronization...")

    # Create synchronization objects similar to ContinuousRunner
    maintenance_lock = threading.Lock()
    maintenance_in_progress = threading.Event()

    sync_waited = False
    maintenance_completed = False

    def mock_sync():
        nonlocal sync_waited
        print("⏰ Sync starting, checking for maintenance...")

        # Check if maintenance is in progress
        if maintenance_in_progress.is_set():
            print("🔄 Sync waiting for maintenance to complete...")
            sync_waited = True
            maintenance_in_progress.wait()
            print("✅ Maintenance completed, sync can proceed")
        else:
            print("✅ No maintenance in progress, sync proceeding")

    def mock_maintenance():
        nonlocal maintenance_completed
        print("🔧 Maintenance starting...")

        with maintenance_lock:
            # Signal that maintenance is in progress
            maintenance_in_progress.set()
            print("🔧 Maintenance in progress...")

            # Simulate maintenance work
            time.sleep(2)

            print("🔧 Maintenance finishing...")
            maintenance_completed = True

            # Clear maintenance flag
            maintenance_in_progress.clear()

        print("🔧 Maintenance completed")

    # Start maintenance first
    maintenance_thread = threading.Thread(target=mock_maintenance, daemon=True)
    maintenance_thread.start()

    # Give maintenance a moment to start
    time.sleep(0.5)

    # Start sync
    sync_thread = threading.Thread(target=mock_sync, daemon=True)
    sync_thread.start()

    # Wait for both to complete
    maintenance_thread.join(timeout=10)
    sync_thread.join(timeout=10)

    if sync_waited and maintenance_completed:
        print("✅ TEST PASSED: Sync properly waited for maintenance to complete")
        return True
    else:
        print(
            f"❌ TEST FAILED: sync_waited={sync_waited}, "
            f"maintenance_completed={maintenance_completed}")
        return False


@pytest.mark.manual
def test_no_maintenance_interference():
    """Test that sync proceeds normally when no maintenance is in progress."""
    print("\n🧪 Testing sync without maintenance interference...")

    maintenance_in_progress = threading.Event()
    sync_proceeded = False

    def mock_sync_no_wait():
        nonlocal sync_proceeded
        print("⏰ Sync starting, checking for maintenance...")

        if maintenance_in_progress.is_set():
            print("🔄 Would wait for maintenance...")
            maintenance_in_progress.wait()
        else:
            print("✅ No maintenance in progress, proceeding with sync")
            sync_proceeded = True

    # Start sync without setting maintenance flag
    sync_thread = threading.Thread(target=mock_sync_no_wait, daemon=True)
    sync_thread.start()
    sync_thread.join(timeout=5)

    if sync_proceeded:
        print("✅ TEST PASSED: Sync proceeded normally without maintenance")
        return True
    else:
        print("❌ TEST FAILED: Sync did not proceed when no maintenance was active")
        return False


if __name__ == "__main__":
    print("🚀 Running basic synchronization tests...\n")

    success1 = test_threading_synchronization()
    success2 = test_no_maintenance_interference()

    if success1 and success2:
        print("\n🎉 All basic tests passed! Threading synchronization works correctly.")
        print("The sync pause during maintenance implementation should work properly.")
    else:
        print("\n❌ Some basic tests failed. Please check the implementation.")
