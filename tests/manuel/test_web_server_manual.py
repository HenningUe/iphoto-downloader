"""Manual testing for the 2FA web server.

This module provides interactive tests for manually validating the web server
functionality including the web interface, 2FA workflow, and server management.

Run this file directly to start interactive testing:
    python tests/manuel/test_web_server_manual.py
"""

import time
import webbrowser
from pathlib import Path
import sys

from icloud_photo_sync.config import get_config
from icloud_photo_sync.logger import setup_logging
from icloud_photo_sync.web_server import TwoFAWebServer

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


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

    server = TwoFAWebServer()
    server.set_callbacks(
        request_2fa_callback=on_new_2fa_requested,
        submit_code_callback=on_code_received
    )

    try:
        success = server.start()
        if not success:
            print("❌ Failed to start server")
            return False

        url = f"http://localhost:{server.port}"
        print(f"🌐 Server started on {url}")

        # Open browser automatically
        try:
            webbrowser.open(url)
            print("🌐 Browser opened automatically")
        except Exception as e:
            print(f"⚠️ Could not open browser automatically: {e}")
            print(f"Please manually open: {url}")

        print("\n📋 Manual Testing Instructions:")
        print("1. The web interface should now be open in your browser")
        print("2. Test the 'Request New 2FA Code' button")
        print("3. Try entering different 2FA codes (use 6-digit numbers)")
        print("4. Test invalid codes (wrong length, non-numeric)")
        print("5. Observe the status updates and animations")
        print("6. Check that the interface is responsive and user-friendly")

        print("\n⏰ Server will run for 60 seconds for manual testing...")
        print("Press Ctrl+C to stop early if needed")

        # Keep server running for manual testing
        start_time = time.time()
        test_duration = 60  # 60 seconds

        try:
            while time.time() - start_time < test_duration:
                time.sleep(1)
                if received_codes or new_2fa_requests > 0:
                    # Show status update
                    elapsed = int(time.time() - start_time)
                    remaining = test_duration - elapsed
                    status = (f"\r⏱️ Time: {remaining}s | "
                              f"Codes: {len(received_codes)} | "
                              f"Requests: {new_2fa_requests}")
                    print(status, end="", flush=True)
        except KeyboardInterrupt:
            print("\n⚠️ Manual test interrupted by user")

        print("\n\n📊 Manual Test Results:")
        print(f"   - Codes received: {len(received_codes)}")
        print(f"   - New 2FA requests: {new_2fa_requests}")
        if received_codes:
            print(f"   - Received codes: {received_codes}")

        server.stop()
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
        if server:
            server.stop()
        return False


def test_port_conflict_handling():
    """Test port conflict handling by starting multiple servers."""
    print("\n🧪 Testing port conflict handling...")

    servers = []

    try:
        # Start multiple servers to test port conflict resolution
        for i in range(3):
            def make_callback(server_id):
                def callback(code):
                    print(f"Server {server_id} received code: {code}")
                    return True
                return callback

            server = TwoFAWebServer()
            server.set_callbacks(
                submit_code_callback=make_callback(i+1),
                request_2fa_callback=lambda: True
            )

            success = server.start()
            if success:
                print(f"✅ Server {i+1} started on port {server.port}")
                servers.append(server)
            else:
                print(f"❌ Server {i+1} failed to start")
                break

        if len(servers) >= 2:
            print("✅ Port conflict handling works - multiple servers on different ports")
        else:
            print("⚠️ Could only start one server - may need to test port conflicts manually")

        # Clean up
        for server in servers:
            try:
                server.stop()
            except Exception:
                pass

        print("✅ All servers stopped")
        return True

    except Exception as e:
        print(f"❌ Error during port conflict test: {e}")
        for server in servers:
            try:
                server.stop()
            except Exception:
                pass
        return False


def test_server_state_management():
    """Test server state management and transitions."""
    print("\n🧪 Testing server state management...")

    state_changes = []

    def on_code_received(code):
        state_changes.append(f"code_received:{code}")
        print(f"📝 State: Code received - {code}")
        return True

    def on_new_2fa_requested():
        state_changes.append("new_2fa_requested")
        print("📝 State: New 2FA requested")
        return True

    server = TwoFAWebServer()
    server.set_callbacks(
        request_2fa_callback=on_new_2fa_requested,
        submit_code_callback=on_code_received
    )

    try:
        # Test initial state
        print(f"📊 Initial state: {server.state}")

        # Start server
        success = server.start()
        if not success:
            print("❌ Failed to start server")
            return False

        print(f"📊 After start: {server.state}")

        # Simulate state changes
        print("🔄 Simulating 2FA code submission...")
        server.submit_2fa_code("123456")

        print("🔄 Simulating new 2FA request...")
        server.request_new_2fa()

        # Check final state
        print(f"📊 Final state: {server.state}")
        print(f"📊 State changes recorded: {state_changes}")

        server.stop()
        print("✅ State management test completed")

        return len(state_changes) > 0

    except Exception as e:
        print(f"❌ Error during state management test: {e}")
        if server:
            server.stop()
        return False


def test_browser_integration():
    """Test automatic browser opening functionality."""
    print("\n🧪 Testing browser integration...")

    def on_code_received(code):
        return True

    def on_new_2fa_requested():
        return True

    server = TwoFAWebServer()
    server.set_callbacks(
        request_2fa_callback=on_new_2fa_requested,
        submit_code_callback=on_code_received
    )

    try:
        success = server.start()
        if not success:
            print("❌ Failed to start server")
            return False

        url = f"http://localhost:{server.port}"
        print(f"🌐 Server running on {url}")

        # Test browser opening
        try:
            success = server.open_browser()
            if success:
                print("✅ Browser opened successfully")
                print("🤔 Please check if the browser opened the correct URL")

                # Give user time to verify
                feedback = input("Did the browser open correctly? (y/n): ").lower().strip()
                result = feedback == 'y'
            else:
                print("❌ Failed to open browser")
                result = False
        except Exception as e:
            print(f"❌ Error opening browser: {e}")
            result = False

        server.stop()
        return result

    except Exception as e:
        print(f"❌ Error during browser integration test: {e}")
        if server:
            server.stop()
        return False


def run_all_manual_tests():
    """Run all manual tests for the web server."""
    print("🚀 Starting Manual Web Server Tests")
    print("=" * 50)

    # Setup logging
    try:
        config = get_config()
        setup_logging(config.get_log_level())
    except Exception:
        # Basic logging setup if config fails
        logging.basicConfig(level=logging.INFO)

    tests = [
        ("Web Interface Manual Test", test_web_interface_manual),
        # ("Port Conflict Handling", test_port_conflict_handling),
        # ("Server State Management", test_server_state_management),
        # ("Browser Integration", test_browser_integration),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print(f"{'='*50}")

        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            results[test_name] = False

    # Print summary
    print(f"\n{'='*50}")
    print("📊 MANUAL TEST SUMMARY")
    print(f"{'='*50}")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    print(f"\n📈 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All manual tests passed!")
    else:
        print("⚠️ Some tests failed - please review the results above")

    return passed == total


if __name__ == "__main__":
    print("🧪 2FA Web Server Manual Testing Tool")
    print("This tool provides interactive tests for the web server functionality")
    print()

    try:
        success = run_all_manual_tests()
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
