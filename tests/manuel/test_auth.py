#!/usr/bin/env python3
import pytest
"""Simple authentication test to check if 2FA is required."""

from iphoto_downloader.logger import setup_logging
from iphoto_downloader.icloud_client import iCloudClient
from iphoto_downloader.config import get_config, KEYRING_AVAILABLE
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))


@pytest.mark.manual
def test_authentication():
    """Test iCloud authentication and check 2FA status."""
    print("🔐 Testing iCloud Authentication")
    print("=" * 40)

    if not KEYRING_AVAILABLE:
        print("❌ Keyring not available")
        return False

    try:
        # Get config and set up logging
        config = get_config()
        setup_logging(config.get_log_level())

        print(f"📧 Using credentials for: {config.icloud_username}")

        # Create client and authenticate
        client = iCloudClient(config)
        print("🔄 Attempting authentication...")

        auth_result = client.authenticate()

        if auth_result:
            print("✅ Initial authentication successful!")

            # Check if 2FA is required
            if client.requires_2fa():
                print("🔐 2FA is required for this account")
                print("📱 You would need to enter a 2FA code to proceed")

                # For demonstration, let's see if we can get a 2FA prompt
                print("\n💡 To complete authentication, you would need to:")
                print("   1. Check your Apple device for a 2FA code")
                print("   2. Enter the code using client.handle_2fa(code)")

                return "2fa_required"
            else:
                print("✅ No 2FA required - full authentication successful!")
                print("📊 Can now access iCloud Photos API")
                return True
        else:
            print("❌ Authentication failed")
            print("💡 This could be due to:")
            print("   - Invalid credentials")
            print("   - Network issues")
            print("   - iCloud service issues")
            return False

    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        return False


if __name__ == "__main__":
    result = test_authentication()

    if result is True:
        print("\n🎉 Authentication fully successful - E2E tests can run!")
    elif result == "2fa_required":
        print("\n⚠️  2FA required - E2E tests need interactive mode")
        print("💡 Run: python run_e2e_tests.py --interactive")
    else:
        print("\n❌ Authentication failed - check credentials")
        print("💡 Run: python manage_credentials.py")
