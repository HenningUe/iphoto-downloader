"""Manual testing for the 2FA web server.

This module provides interactive tests for manually validating the web server
functionality including the web interface, 2FA workflow, and server management.

Run this file directly to start interactive testing:
    python tests/manuel/test_web_server_manual.py
"""
import pytest
from pathlib import Path
import sys

from icloud_photo_sync.config import get_config
from icloud_photo_sync.logger import setup_logging
from auth2fa import TwoFactorAuthHandler
from auth2fa.authenticator import Auth2FAConfig

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.mark.manual
def test_web_interface_manual():
    """Manual test of the web interface - opens browser for user interaction."""
    print("\n🧪 Starting manual web interface test...")
    print("This will open a browser window for you to test the interface manually.")

    # Track received codes and requests
    received_codes = []
    new_2fa_requests = 0

    def on_code_received(code):
        received_codes.append(code)
        print(f"✅ Code received via web interface: {code}")
        return True

    def on_new_2fa_requested():
        nonlocal new_2fa_requests
        new_2fa_requests += 1
        print(f"🔄 New 2FA request #{new_2fa_requests} received via web interface")
        return True

    config = get_config()
    setup_logging(config.get_log_level())
    cfg_2fa = Auth2FAConfig(pushover_config=config.get_pushover_config())
    two_factor_hdl = TwoFactorAuthHandler(cfg_2fa)
    try:
        two_factor_hdl.handle_2fa_authentication(
            request_2fa_callback=on_new_2fa_requested,
            validate_2fa_callback=on_code_received
        )

        print("\n📋 Manual Testing Instructions:")
        print("1. The web interface should now be open in your browser")
        print("2. Test the 'Request New 2FA Code' button")
        print("3. Try entering different 2FA codes (use 6-digit numbers)")
        print("4. Test invalid codes (wrong length, non-numeric)")
        print("5. Observe the status updates and animations")
        print("6. Check that the interface is responsive and user-friendly")

        print("\n⏰ Server will run for 60 seconds for manual testing...")
        print("Press Ctrl+C to stop early if needed")

        print("\n\n📊 Manual Test Results:")
        print(f"   - Codes received: {len(received_codes)}")
        print(f"   - New 2FA requests: {new_2fa_requests}")
        if received_codes:
            print(f"   - Received codes: {received_codes}")

        print("✅ Server stopped successfully")

        # Ask user for feedback
        print("\n🤔 Manual Test Feedback:")
        feedback = input("Did the web interface work correctly? (y/n): ").lower().strip()
        if feedback == 'y':
            print("✅ Manual test passed!")
            return True
        else:
            print("❌ Manual test failed - please check the issues")
            return False

    except Exception as e:
        print(f"❌ Error during manual test: {e}")
        return False
    finally:
        if two_factor_hdl:
            two_factor_hdl.cleanup()


if __name__ == "__main__":
    print("🧪 2FA Web Server Manual Testing Tool")
    print("This tool provides interactive tests for the web server functionality")
    print()

    try:
        success = test_web_interface_manual()
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
