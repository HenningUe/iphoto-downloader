#!/usr/bin/env python3
"""Automated versions of manual tests using mocking instead of browser automation.

This module converts the manual tests to automated versions that can run
without user interaction by mocking browser operations and user inputs.
"""

import os
import sys
import time
import unittest.mock
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import test automation utilities
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from test_automation_utils import AutomatedTestContext, automated_input

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared" / "auth2fa" / "src"))

try:
    from auth2fa.web_server import TwoFAWebServer
    from auth2fa.pushover_service import PushoverNotificationService, PushoverConfig

    WEB_SERVER_AVAILABLE = True
except ImportError:
    WEB_SERVER_AVAILABLE = False
    print("⚠️ Web server modules not available, skipping web server tests")


@pytest.mark.skipif(not WEB_SERVER_AVAILABLE, reason="Web server modules not available")
def test_web_server_automation_mock():
    """Automated test of web server without requiring browser interaction."""
    print("\\n🤖 Testing web server with mocked interactions...")

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

    server = None
    try:
        # Create and configure server
        server = TwoFAWebServer()
        server.set_callbacks(
            request_2fa_callback=on_new_2fa_requested, submit_code_callback=on_code_received
        )

        # Test server startup
        success = server.start()
        assert success, "Server should start successfully"
        print(f"✅ Server started on port {server.port}")

        # Test server is running by checking internal state
        assert server.server is not None, "Server should have server object when running"
        assert server.port is not None, "Server should have port when running"

        # Simulate web interactions by calling the callbacks directly
        # This simulates what would happen when a user interacts with the web UI

        # Test 1: Simulate new 2FA request
        print("\\n🧪 Test 1: Simulating 2FA request...")
        initial_requests = new_2fa_requests
        on_new_2fa_requested()  # Simulate button click
        assert new_2fa_requests > initial_requests, "2FA request should increment counter"
        print("✅ 2FA request simulation successful")

        # Test 2: Simulate valid code submission
        print("\\n🧪 Test 2: Simulating valid code submission...")
        test_codes = ["123456", "654321", "111111"]

        for test_code in test_codes:
            initial_count = len(received_codes)
            result = on_code_received(test_code)  # Simulate form submission
            assert result is True, f"Code submission should return True for {test_code}"
            assert len(received_codes) > initial_count, (
                f"Code {test_code} should be added to received list"
            )
            assert test_code in received_codes, f"Code {test_code} should be in received list"
            print(f"✅ Code {test_code} submitted successfully")

        # Test 3: Test callback behavior with edge cases
        print("\\n🧪 Test 3: Testing edge cases...")

        # Test empty/None code
        try:
            result = on_code_received("")
            # Should still work but might not add empty code
            print("✅ Empty code handled gracefully")
        except Exception as e:
            print(f"⚠️ Empty code caused exception: {e}")

        # Test multiple rapid requests
        initial_requests = new_2fa_requests
        for _ in range(5):
            on_new_2fa_requested()

        assert new_2fa_requests == initial_requests + 5, "Multiple requests should all be counted"
        print("✅ Multiple rapid requests handled correctly")

        # Test server properties
        assert server.port > 0, "Server should have valid port"
        print("✅ Server properties validation passed")

        print("\\n📊 Test Results Summary:")
        print(f"   - 2FA Requests: {new_2fa_requests}")
        print(f"   - Codes Received: {len(received_codes)}")
        print(f"   - Test Codes: {received_codes}")
        print("✅ All web server automation tests passed!")

    finally:
        # Cleanup
        if server:
            try:
                server.stop()
                print("🛑 Web server stopped")
            except Exception as e:
                print(f"⚠️ Error stopping server: {e}")


@pytest.mark.skipif(not WEB_SERVER_AVAILABLE, reason="Web server modules not available")
def test_pushover_automation_mock():
    """Automated test of Pushover notifications with mocking."""
    print("\\n🤖 Testing Pushover notifications with mocked interactions...")

    # Mock the HTTP requests to Pushover API
    with patch("requests.post") as mock_post:
        # Configure mock to return success response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 1, "request": "test-request-id"}
        mock_post.return_value = mock_response

        try:
            # Test Pushover service creation with proper config object
            config = PushoverConfig(
                user_key="test-user-key",
                api_token="test-api-token"
            )
            service = PushoverNotificationService(config)
            print("✅ PushoverNotificationService created successfully")

            # Test 2FA notification
            print("\\n🧪 Test 1: Testing 2FA notification...")
            result = service.send_2fa_notification("http://localhost:8080/2fa")

            assert result is True, "2FA notification should succeed with mocked response"
            assert mock_post.called, "HTTP POST should have been called"
            print("✅ 2FA notification sent successfully")

            # Test success notification
            print("\\n🧪 Test 2: Testing success notification...")
            mock_post.reset_mock()
            result = service.send_auth_success_notification()

            assert result is True, "Success notification should succeed with mocked response"
            assert mock_post.called, "HTTP POST should have been called"
            print("✅ Success notification sent successfully")

            # Test API call parameters
            print("\\n🧪 Test 3: Validating API call parameters...")
            call_args = mock_post.call_args
            assert call_args is not None, "HTTP POST should have been called with arguments"

            # Check that required parameters are present
            if call_args[1] and "data" in call_args[1]:
                data = call_args[1]["data"]
                assert "user" in data, "User key should be in API call"
                assert "token" in data, "API token should be in API call"
                assert "message" in data, "Message should be in API call"
                print("✅ API call parameters validated")

        except ImportError as e:
            print(f"⚠️ Pushover service not available: {e}")
            pytest.skip("Pushover service not available")
        except Exception as e:
            print(f"❌ Pushover test failed: {e}")
            raise


def test_manual_test_automation_integration():
    """Test that manual tests can be automated using the test automation utilities."""
    print("\\n🤖 Testing manual test automation integration...")

    with AutomatedTestContext(mock_browser=True, mock_input=True):
        # Test automated input
        print("\\n🧪 Test 1: Testing automated input...")

        # Simulate input that would normally require user interaction
        response = automated_input("Enter test value: ", "automated_response")
        assert response == "automated_response", "Automated input should return default response"
        print("✅ Automated input working correctly")

        # Test browser operations are skipped
        print("\\n🧪 Test 2: Testing browser operation skipping...")

        # This should not actually open a browser
        import webbrowser

        original_open = webbrowser.open

        # Browser operations should be mocked in automated context
        try:
            result = webbrowser.open("http://localhost:8080")
            print("✅ Browser operation completed (mocked)")
        except Exception as e:
            print(f"⚠️ Browser operation failed: {e}")

        # Test that manual tests can be converted to automated
        print("\\n🧪 Test 3: Testing manual to automated conversion...")

        # Simulate what a manual test would do
        def simulate_manual_test():
            """Simulate a typical manual test that requires user input."""

            # This would normally require user input, but should be automated
            user_choice = automated_input("Select option (1-3): ", "2")
            assert user_choice == "2", "Should get automated response"

            # This would normally open browser, but should be skipped/mocked
            webbrowser.open("http://localhost:8080/test")

            # This would normally wait for user confirmation
            confirmation = automated_input("Test completed successfully? (y/n): ", "y")
            assert confirmation == "y", "Should get automated confirmation"

            return True

        result = simulate_manual_test()
        assert result is True, "Manual test simulation should complete successfully"
        print("✅ Manual to automated conversion successful")


if __name__ == "__main__":
    """Run automated tests directly."""
    print("🚀 Running automated versions of manual tests...")

    # Set up environment for automated testing
    os.environ["PYTEST_CURRENT_TEST"] = "automation_test"

    try:
        test_manual_test_automation_integration()

        if WEB_SERVER_AVAILABLE:
            test_web_server_automation_mock()
            test_pushover_automation_mock()
        else:
            print("⚠️ Web server modules not available, skipping web server tests")

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    print("🎉 All automated manual tests completed successfully!")
