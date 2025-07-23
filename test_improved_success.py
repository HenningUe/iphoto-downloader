#!/usr/bin/env python3
"""Test the improved 2FA success page with better closing functionality."""

from auth2fa.web_server import TwoFAWebServer
import sys
import time
from pathlib import Path

# Add the shared package to path
sys.path.append(str(Path(__file__).parent / "shared" / "auth2fa" / "src"))


def test_improved_success_page():
    """Test the improved success page with better window closing."""

    print("🔧 Testing improved 2FA success page...")
    server = TwoFAWebServer(port_range=(8090, 8095))

    if not server.start():
        print("❌ Failed to start web server")
        return False

    url = server.get_url()
    print(f"✅ Web server started at: {url}")
    print(f"🌐 Direct success page: {url}/success")

    # Set authenticated state and open browser to main page
    server.set_state('waiting_for_code', 'Ready for testing - enter any 6-digit code')

    if server.open_browser():
        print("✅ Browser opened to main page")
    else:
        print(f"⚠️ Please open: {url}")

    print("\n📋 Test Instructions:")
    print("1. Enter any 6-digit code (e.g., 123456) on the 2FA page")
    print("2. You should be redirected to the success page")
    print("3. The success page now has improved closing behavior:")
    print("   - Countdown from 10 seconds")
    print("   - If auto-close fails, shows user-friendly message")
    print("   - Close button provides better feedback")
    print("   - Page title changes to indicate completion")
    print("   - Instructions on how to close manually if needed")

    print("\n⏳ Test server running for 45 seconds...")
    print("   Press Ctrl+C to stop early")

    try:
        time.sleep(45)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted")

    server.stop()
    print("🛑 Web server stopped")

    print("\n✅ Success page improvements:")
    print("• Better error handling when window.close() fails")
    print("• User-friendly messages and instructions")
    print("• Visual feedback with title flashing")
    print("• Fallback methods for closing/navigation")
    print("• Clear instructions for manual window closing")

    return True


if __name__ == "__main__":
    test_improved_success_page()
