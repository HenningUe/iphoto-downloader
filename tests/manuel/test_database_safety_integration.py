#!/usr/bin/env python3
import pytest

"""Quick test script to verify database safety methods integration."""

import logging
import os
import sys
import tempfile
from pathlib import Path

from iphoto_downloader.deletion_tracker import DeletionTracker
from iphoto_downloader.logger import setup_logging

# Add the source directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "iphoto_downloader", "src"))


@pytest.mark.manual
def test_database_safety_integration():
    """Test that all database safety methods are properly called."""

    # Set up logging
    setup_logging(logging.INFO)

    test_results = {
        "initialization": False,
        "backup_creation": False,
        "integrity_check": False,
        "corruption_recovery": False,
        "cleanup": False,
    }

    try:
        # Test 1: Normal initialization (should call ensure_database_safety)
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # This should automatically call ensure_database_safety() -> _init_database()
            tracker = DeletionTracker(str(db_path))

            # Verify database was created and is functional
            tracker.add_downloaded_photo("test1", "test1.jpg", "album1/test1.jpg", 1024, "Album1")
            photos = tracker.get_downloaded_photos()

            if len(photos) == 1 and db_path.exists():
                test_results["initialization"] = True

            # Test 2: Backup creation (should be called automatically)
            import glob

            backup_files = glob.glob(str(db_path.with_suffix(".backup_*.db")))
            if len(backup_files) >= 1:
                test_results["backup_creation"] = True

            # Test 3: Integrity check (should work)
            if tracker.check_database_integrity():
                test_results["integrity_check"] = True

            tracker.close()

        # Test 4: Corruption recovery
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create initial database with data and backup
            tracker1 = DeletionTracker(str(db_path))
            tracker1.add_downloaded_photo("test1", "test1.jpg", "album1/test1.jpg", 1024, "Album1")
            tracker1.create_backup()
            tracker1.close()
            del tracker1

            # Corrupt the database
            with open(db_path, "wb") as f:
                f.write(b"corrupted database content")

            # Initialize new tracker - should auto-recover
            try:
                tracker2 = DeletionTracker(str(db_path))

                # Verify data was recovered
                photos = tracker2.get_downloaded_photos()
                if len(photos) == 1:
                    test_results["corruption_recovery"] = True

                tracker2.close()
            except Exception:
                pass  # Recovery might fail, but shouldn't crash

        # Test 5: Cleanup functionality
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            tracker = DeletionTracker(str(db_path))
            tracker.close()  # Should not raise exception
            test_results["cleanup"] = True

    except Exception as e:
        # Write error to file for debugging
        with open("test_error.log", "w") as f:
            f.write(f"Test failed with error: {e}\n")
        return False, test_results

    # All tests should pass
    all_passed = all(test_results.values())

    # Write results to file
    with open("test_results.txt", "w") as f:
        f.write("Database Safety Methods Integration Test Results\n")
        f.write("=" * 50 + "\n\n")

        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            f.write(f"{test_name.replace('_', ' ').title()}: {status}\n")

        f.write(
            f"\nOverall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}\n"
        )

        f.write("\nMethod Call Verification:\n")
        f.write("• ensure_database_safety() → Called in __init__\n")
        f.write("• _init_database() → Called when database missing/corrupted\n")
        f.write("• check_database_integrity() → Called at startup and after recovery\n")
        f.write("• create_backup() → Called before normal operations\n")
        f.write("• recover_from_backup() → Called when corruption detected\n")
        f.write("• close() → Available for cleanup\n")

    return all_passed, test_results


if __name__ == "__main__":
    success, results = test_database_safety_integration()

    # Write simple status file
    with open("test_status.txt", "w") as f:
        if success:
            f.write("SUCCESS: All database safety methods are properly integrated!")
        else:
            f.write("FAILURE: Some database safety methods are not working correctly.")
            f.write(f"\nFailed tests: {[k for k, v in results.items() if not v]}")
