#!/usr/bin/env python3
"""Test the 2FA web server success page functionality."""

import sys
import time
from pathlib import Path

import pytest

from auth2fa.web_server import TwoFAWebServer

# Add the shared package to path
sys.path.append(str(Path(__file__).parent / "shared" / "auth2fa" / "src"))


@pytest.mark.manual
def test_2fa_flow():
    """Test the complete 2FA flow including success page."""

    print("🔧 Starting 2FA web server...")
    server = TwoFAWebServer(port_range=(8090, 8095))

    if not server.start():
        print("❌ Failed to start web server")
        return False

    url = server.get_url()
    print(f"✅ Web server started at: {url}")
    print(f"🌐 Success page will be at: {url}/success")

    # Open browser to main page
    print("🌍 Opening browser...")
    if server.open_browser():
        print("✅ Browser opened successfully")
    else:
        print("⚠️ Could not open browser automatically")
        print(f"   Please open: {url}")

    print("\n📋 Test Instructions:")
    print("1. The 2FA page should load in your browser")
    print("2. Enter any 6-digit code (e.g., 123456) when the form appears")
    print("3. After submission, you should be redirected to the success page")
    print("4. The success page should show a green checkmark and countdown")
    print("5. The window should auto-close after 10 seconds")

    # Set the state to waiting for code to enable the form
    server.set_state("waiting_for_code", "Please enter any 6-digit code for testing")

    print("\n⏳ Server will run for 60 seconds for testing...")
    print("   Press Ctrl+C to stop early")

    try:
        time.sleep(60)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")

    server.stop()
    print("🛑 Web server stopped")
    return True


if __name__ == "__main__":
    test_2fa_flow()
