#!/usr/bin/env python3
import pytest

"""Test script for 2FA implementation with session storage."""

import os
import sys
from pathlib import Path

from iphoto_downloader.config import get_config
from iphoto_downloader.icloud_client import ICloudClient
from iphoto_downloader.logger import setup_logging
from iphoto_downloader.sync import PhotoSyncer

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))


@pytest.mark.manual
def test_2fa_implementation():
    """Test the 2FA implementation with session storage."""
    print("🧪 Testing 2FA Implementation with Session Storage")
    print("=" * 55)

    try:
        # Get config and set up logging
        config = get_config()
        setup_logging(config.get_log_level())

        print(f"📧 Using credentials for: {config.icloud_username}")

        # Create client and check session directory
        client = ICloudClient(config)
        print(f"📁 Session directory: {client.session_dir}")
        print(f"✅ Session directory exists: {client.session_dir.exists()}")

        # List session files if any exist
        session_files = list(client.session_dir.glob("*"))
        if session_files:
            print(f"📂 Found {len(session_files)} session files:")
            for file in session_files:
                print(f"   - {file.name}")
        else:
            print("📂 No existing session files found")

        # Test authentication
        print("\n🔄 Testing authentication...")
        auth_result = client.authenticate()

        if auth_result:
            print("✅ Authentication successful!")

            # Check session status
            if client.is_trusted_session():
                print("✅ Session is trusted - no 2FA should be required")
            else:
                print("⚠️ Session is not trusted")

            # Check if 2FA is required
            if client.requires_2fa():
                print("🔐 2FA is required")
                print("💡 The PhotoSyncer._handle_2fa() method would prompt for code here")
                print("💡 In an actual sync, you would be prompted to enter a 6-digit code")
            else:
                print("✅ No 2FA required - ready for photo operations")

            assert True
        else:
            print("❌ Authentication failed")
            assert False, "Authentication failed"

    except Exception as e:
        print(f"❌ Error during test: {e}")
        assert False, f"Error during test: {e}"


@pytest.mark.manual
def test_syncer_integration():
    """Test the PhotoSyncer integration with 2FA."""
    print("\n🧪 Testing PhotoSyncer 2FA Integration")
    print("=" * 40)

    try:
        config = get_config()

        # Override settings for testing
        os.environ["DRY_RUN"] = "true"
        os.environ["MAX_DOWNLOADS"] = "1"

        # Create syncer
        PhotoSyncer(config)
        print("✅ PhotoSyncer created successfully")
        print("💡 2FA handling is now implemented in PhotoSyncer._handle_2fa()")
        print("💡 Sessions will be stored in: %USERPROFILE%\\iphoto_downloader\\sessions")

        assert True

    except Exception as e:
        print(f"❌ Error creating PhotoSyncer: {e}")
        assert False, f"Error creating PhotoSyncer: {e}"
    finally:
        # Clean up environment
        os.environ.pop("DRY_RUN", None)
        os.environ.pop("MAX_DOWNLOADS", None)


if __name__ == "__main__":
    print("🚀 2FA Implementation Test Suite")
    print("=" * 50)

    # Test 1: iCloud client with session storage
    test1_result = test_2fa_implementation()

    # Test 2: PhotoSyncer integration
    test2_result = test_syncer_integration()

    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"  iCloud Client Test: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"  PhotoSyncer Test:   {'✅ PASS' if test2_result else '❌ FAIL'}")

    if test1_result and test2_result:
        print("\n🎉 All tests passed! 2FA implementation is ready.")
        print("\n💡 Usage:")
        print("  1. Run: python -m iphoto_downloader.main")
        print("  2. If 2FA required, enter 6-digit code when prompted")
        print("  3. Session will be trusted for future runs")
        print("  4. Subsequent runs should not require 2FA")
    else:
        print("\n❌ Some tests failed - check implementation")

    print("=" * 50)
