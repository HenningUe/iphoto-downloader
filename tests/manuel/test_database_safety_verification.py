#!/usr/bin/env python3
import pytest
"""Quick verification test for database safety methods integration."""

from icloud_photo_sync.deletion_tracker import DeletionTracker
from icloud_photo_sync.logger import setup_logging
import logging
import tempfile
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'icloud_photo_sync', 'src'))


@pytest.mark.manual
def test_database_safety_integration():
    """Test that all database safety methods are properly integrated."""

    # Set up logging
    setup_logging(logging.INFO)

    results = []

    # Test 1: Normal initialization flow
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'test.db'

            # This should trigger: ensure_database_safety() -> _init_database() -> create_backup()
            tracker = DeletionTracker(str(db_path))

            # Verify database was created
            if db_path.exists():
                results.append("✅ Database initialization: PASS")
            else:
                results.append("❌ Database initialization: FAIL")

            # Verify backup was created
            backup_files = list(Path(tmpdir).glob("test.backup_*.db"))
            if backup_files:
                results.append("✅ Backup creation during init: PASS")
            else:
                results.append("❌ Backup creation during init: FAIL")

            # Test normal operations
            tracker.add_downloaded_photo('test1', 'test1.jpg', 'album1/test1.jpg', 1024, 'Album1')
            photos = tracker.get_downloaded_photos()
            if len(photos) == 1:
                results.append("✅ Normal database operations: PASS")
            else:
                results.append("❌ Normal database operations: FAIL")

            # Clean up properly
            tracker.close()

    except Exception as e:
        results.append(f"❌ Normal initialization test: FAIL - {e}")

    # Test 2: Database corruption recovery
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'test.db'

            # Create initial database with data and backup
            tracker1 = DeletionTracker(str(db_path))
            tracker1.add_downloaded_photo('test1', 'test1.jpg', 'album1/test1.jpg', 1024, 'Album1')
            tracker1.create_backup()
            tracker1.close()
            del tracker1

            # Corrupt the database
            with open(db_path, 'wb') as f:
                f.write(b'corrupted database content')

            # This should trigger: ensure_database_safety()
            # -> check_database_integrity() -> recover_from_backup()
            tracker2 = DeletionTracker(str(db_path))

            # Verify data was recovered
            photos = tracker2.get_downloaded_photos()
            if len(photos) == 1 and 'test1' in photos:
                results.append("✅ Database corruption recovery: PASS")
            else:
                results.append("❌ Database corruption recovery: FAIL")

            tracker2.close()

    except Exception as e:
        results.append(f"❌ Corruption recovery test: FAIL - {e}")

    # Test 3: Backup cleanup functionality
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'test.db'
            tracker = DeletionTracker(str(db_path))

            # Create multiple backups (should keep only max_backups)
            for i in range(7):
                tracker.add_downloaded_photo(
                    f'test{i}', f'test{i}.jpg', f'album1/test{i}.jpg', 1024, 'Album1')
                tracker.create_backup(max_backups=3)

            # Count backup files
            backup_files = list(Path(tmpdir).glob("test.backup_*.db"))
            if len(backup_files) <= 3:
                results.append("✅ Backup cleanup (max_backups): PASS")
            else:
                results.append(
                    f"❌ Backup cleanup: FAIL - Found {len(backup_files)} backups, expected ≤3")

            tracker.close()

    except Exception as e:
        results.append(f"❌ Backup cleanup test: FAIL - {e}")

    # Test 4: Integration with PhotoSyncer cleanup
    try:
        # Test that cleanup method exists and works
        from icloud_photo_sync.sync import PhotoSyncer

        # Check if cleanup method exists
        if hasattr(PhotoSyncer, 'cleanup'):
            results.append("✅ PhotoSyncer.cleanup() method exists: PASS")
        else:
            results.append("❌ PhotoSyncer.cleanup() method missing: FAIL")

        # Check if __del__ method exists
        if hasattr(PhotoSyncer, '__del__'):
            results.append("✅ PhotoSyncer.__del__() method exists: PASS")
        else:
            results.append("❌ PhotoSyncer.__del__() method missing: FAIL")

    except Exception as e:
        results.append(f"❌ PhotoSyncer integration test: FAIL - {e}")

    return results


def main():
    """Run all tests and report results."""
    print("🧪 Database Safety Methods Integration Verification")
    print("=" * 60)

    results = test_database_safety_integration()

    print("\n📊 Test Results:")
    print("-" * 40)

    passed = 0
    failed = 0

    for result in results:
        print(result)
        if "✅" in result:
            passed += 1
        else:
            failed += 1

    print("-" * 40)
    print(f"Total: {passed + failed} tests | Passed: {passed} | Failed: {failed}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Database safety integration is working correctly.")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
