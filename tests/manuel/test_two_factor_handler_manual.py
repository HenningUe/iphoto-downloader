"""Manual testing for the TwoFactorAuthHandler.

This module provides interactive tests for manually validating the complete 2FA
authentication flow including web server integration, Pushover notifications,
and callback handling.

Run this file directly to start interactive testing:
    python tests/manuel/test_two_factor_handler_manual.py
"""

import logging
import time
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from icloud_photo_sync.config import KeyringConfig
from icloud_photo_sync.logger import setup_logging
from auth2fa import TwoFactorAuthHandler, handle_2fa_authentication


def test_complete_2fa_flow():
    """Test the complete 2FA authentication flow with all components."""
    print("\n🧪 Starting Complete 2FA Flow Test...")
    print("This test will simulate the full 2FA authentication process.")
    
    # Test data
    test_username = "test.user@icloud.com"
    test_codes = ["123456", "654321", "111111"]
    request_count = 0
    validation_attempts = []
    
    def mock_request_2fa():
        """Mock callback for requesting new 2FA code."""
        nonlocal request_count
        request_count += 1
        print(f"📱 Mock: New 2FA code requested (attempt #{request_count})")
        return True
    
    def mock_validate_2fa(code: str) -> bool:
        """Mock callback for validating 2FA code."""
        validation_attempts.append(code)
        print(f"🔍 Mock: Validating 2FA code '{code}'")
        
        # Simulate validation logic
        if code in test_codes:
            print(f"✅ Mock: Code '{code}' is valid")
            return True
        else:
            print(f"❌ Mock: Code '{code}' is invalid")
            return False
    
    try:
        # Load configuration
        config = KeyringConfig()
        
        # Create handler
        handler = TwoFactorAuthHandler(config)
        
        print(f"🎯 Testing with username: {test_username}")
        print(f"📝 Valid test codes: {test_codes}")
        print("\n📋 Instructions:")
        print("1. A web browser will open with the 2FA interface")
        print("2. If Pushover is configured, you should receive a notification")
        print("3. Try entering valid codes:", ', '.join(test_codes))
        print("4. Try entering invalid codes to test validation")
        print("5. Test the 'Request New 2FA' button")
        print("\n⏰ Test will timeout after 5 minutes")
        
        input("\nPress Enter to start the test...")
        
        # Start the authentication flow
        start_time = time.time()
        result_code = handler.handle_2fa_authentication(
            username=test_username,
            request_2fa_callback=mock_request_2fa,
            validate_2fa_callback=mock_validate_2fa
        )
        end_time = time.time()
        
        # Display results
        print(f"\n📊 Test Results:")
        print(f"   - Duration: {end_time - start_time:.1f} seconds")
        print(f"   - Result code: {result_code}")
        print(f"   - 2FA requests made: {request_count}")
        print(f"   - Validation attempts: {len(validation_attempts)}")
        if validation_attempts:
            print(f"   - Attempted codes: {validation_attempts}")
        
        if result_code:
            print("✅ Test completed successfully!")
            return True
        else:
            print("❌ Test failed or timed out")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False


def test_pushover_integration():
    """Test Pushover notification integration."""
    print("\n🧪 Testing Pushover Integration...")
    
    try:
        config = KeyringConfig()
        
        # Check if Pushover is configured
        pushover_config = config.get_pushover_config()
        if not pushover_config:
            print("⚠️ Pushover not configured - skipping notification test")
            print("To test notifications, configure Pushover in your .env file:")
            print("  ENABLE_PUSHOVER=true")
            print("  PUSHOVER_API_TOKEN=your-token")
            print("  PUSHOVER_USER_KEY=your-user-key")
            return True
        
        print(f"📱 Pushover configured:")
        print(f"   - API Token: {'*' * len(pushover_config.api_token)}")
        print(f"   - User Key: {'*' * len(pushover_config.user_key)}")
        print(f"   - Device: {pushover_config.device or 'All devices'}")
        
        # Test notification sending
        test_username = "test.user@icloud.com"
        test_url = "http://localhost:8080/test"
        
        print(f"\n📤 Sending test notification...")
        print(f"   - Username: {test_username}")
        print(f"   - URL: {test_url}")
        
        handler = TwoFactorAuthHandler(config)
        handler._send_pushover_notification(test_username, test_url)
        
        print("📱 Check your Pushover app for the test notification")
        feedback = input("Did you receive the notification? (y/n): ").lower().strip()
        
        if feedback == 'y':
            print("✅ Pushover integration test passed!")
            return True
        else:
            print("❌ Pushover integration test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during Pushover test: {e}")
        return False


def test_web_server_integration():
    """Test web server integration without full flow."""
    print("\n🧪 Testing Web Server Integration...")
    
    received_codes = []
    request_count = 0
    
    def on_code_received(code: str) -> bool:
        received_codes.append(code)
        print(f"✅ Handler received code: {code}")
        return True
    
    def on_request_2fa() -> bool:
        nonlocal request_count
        request_count += 1
        print(f"🔄 Handler received 2FA request #{request_count}")
        return True
    
    config = KeyringConfig()
    handler = TwoFactorAuthHandler(config)
    test_server = None
    
    try:
        # Test web server startup
        print("🌐 Testing web server startup...")
        
        # Create a web server directly for testing
        from icloud_photo_sync.auth2fa.web_server import TwoFAWebServer
        test_server = TwoFAWebServer()
        test_server.set_callbacks(
            request_2fa_callback=on_request_2fa,
            submit_code_callback=on_code_received
        )
        
        if test_server.start():
            url = test_server.get_url()
            print(f"✅ Web server started at: {url}")
            
            # Open browser
            if test_server.open_browser():
                print("🌐 Browser opened successfully")
            else:
                print("⚠️ Could not open browser")
                print(f"Please manually open: {url}")
            
            print("\n📋 Manual Test Instructions:")
            print("1. Test the web interface in your browser")
            print("2. Try submitting different 2FA codes")
            print("3. Test the 'Request New 2FA' button")
            print("4. Verify the interface is responsive")
            
            # Wait for user interaction
            print("\n⏰ Test will run for 60 seconds...")
            start_time = time.time()
            while time.time() - start_time < 60:
                time.sleep(1)
                if received_codes or request_count > 0:
                    remaining = 60 - int(time.time() - start_time)
                    print(f"\r⏱️ Time: {remaining}s | Codes: {len(received_codes)} | Requests: {request_count}", end="", flush=True)
            
            print(f"\n\n📊 Web Server Test Results:")
            print(f"   - Codes received: {len(received_codes)}")
            print(f"   - 2FA requests: {request_count}")
            if received_codes:
                print(f"   - Received codes: {received_codes}")
            
            test_server.stop()
            print("✅ Web server stopped")
            
            return len(received_codes) > 0 or request_count > 0
            
        else:
            print("❌ Failed to start web server")
            return False
            
    except Exception as e:
        print(f"❌ Error during web server test: {e}")
        return False
    finally:
        # Clean up test server
        if test_server is not None:
            try:
                test_server.stop()
            except:
                pass


def test_timeout_behavior():
    """Test timeout behavior of the 2FA handler."""
    print("\n🧪 Testing Timeout Behavior...")
    
    try:
        config = KeyringConfig()
        handler = TwoFactorAuthHandler(config)
        
        print("⏰ Testing 10-second timeout (do not enter any code)...")
        
        start_time = time.time()
        result = handler.handle_2fa_authentication(
            username="timeout.test@icloud.com",
            request_2fa_callback=lambda: True,
            validate_2fa_callback=lambda code: True
        )
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"📊 Timeout test results:")
        print(f"   - Duration: {duration:.1f} seconds")
        print(f"   - Result: {result}")
        
        # Should timeout and return None
        if result is None and duration >= 10:
            print("✅ Timeout behavior works correctly")
            return True
        else:
            print("❌ Timeout behavior failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during timeout test: {e}")
        return False


def test_convenience_function():
    """Test the convenience function for external use."""
    print("\n🧪 Testing Convenience Function...")
    
    validation_calls = []
    
    def test_validate(code: str) -> bool:
        validation_calls.append(code)
        print(f"🔍 Convenience function validation: {code}")
        return code == "999999"  # Only accept this specific code
    
    try:
        config = KeyringConfig()
        
        print("📋 Testing convenience function: handle_2fa_authentication()")
        print("   - Enter '999999' to pass validation")
        print("   - Try other codes to test validation failure")
        
        result = handle_2fa_authentication(
            config=config,
            username="convenience.test@icloud.com",
            request_2fa_callback=lambda: True,
            validate_2fa_callback=test_validate
        )
        
        print(f"\n📊 Convenience Function Results:")
        print(f"   - Result: {result}")
        print(f"   - Validation calls: {len(validation_calls)}")
        if validation_calls:
            print(f"   - Attempted codes: {validation_calls}")
        
        if result == "999999":
            print("✅ Convenience function test passed!")
            return True
        else:
            print("❌ Convenience function test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during convenience function test: {e}")
        return False


def test_error_handling():
    """Test error handling in various scenarios."""
    print("\n🧪 Testing Error Handling...")
    
    try:
        config = KeyringConfig()
        handler = TwoFactorAuthHandler(config)
        
        # Test with invalid callbacks
        def failing_callback():
            raise Exception("Test callback failure")
        
        def failing_validator(code: str):
            if code == "ERROR":
                raise Exception("Test validation failure")
            return True
        
        print("🔍 Testing error handling with failing callbacks...")
        
        # This should handle the exception gracefully
        result = handler.handle_2fa_authentication(
            username="error.test@icloud.com",
            request_2fa_callback=failing_callback,
            validate_2fa_callback=failing_validator
        )
        
        print(f"📊 Error handling results:")
        print(f"   - Result: {result}")
        print("   - Handler should have caught exceptions gracefully")
        
        # Test should not crash, regardless of result
        print("✅ Error handling test completed (no crash)")
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error during error handling test: {e}")
        return False


def run_all_manual_tests():
    """Run all manual tests for the TwoFactorAuthHandler."""
    print("🚀 Starting Manual TwoFactorAuthHandler Tests")
    print("=" * 60)
    
    # Setup logging
    try:
        config = KeyringConfig()
        setup_logging(config.get_log_level())
    except Exception:
        logging.basicConfig(level=logging.INFO)
    
    tests = [
        ("Complete 2FA Flow", test_complete_2fa_flow),
        ("Pushover Integration", test_pushover_integration),
        ("Web Server Integration", test_web_server_integration),
        ("Timeout Behavior", test_timeout_behavior),
        ("Convenience Function", test_convenience_function),
        ("Error Handling", test_error_handling),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            results[test_name] = False
        
        # Give user time to review results
        if test_name != list(results.keys())[-1]:  # Not the last test
            input("\nPress Enter to continue to next test...")
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 MANUAL TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All manual tests passed!")
        print("\n🚀 TwoFactorAuthHandler is ready for production use!")
    else:
        print("⚠️ Some tests failed - please review the results above")
    
    return passed == total


def interactive_mode():
    """Run tests in interactive mode with user choices."""
    print("🎮 Interactive Test Mode")
    print("=" * 40)
    
    available_tests = {
        "1": ("Complete 2FA Flow", test_complete_2fa_flow),
        "2": ("Pushover Integration", test_pushover_integration),
        "3": ("Web Server Integration", test_web_server_integration),
        "4": ("Timeout Behavior", test_timeout_behavior),
        "5": ("Convenience Function", test_convenience_function),
        "6": ("Error Handling", test_error_handling),
        "a": ("All Tests", run_all_manual_tests),
    }
    
    while True:
        print("\n📋 Available Tests:")
        for key, (name, _) in available_tests.items():
            print(f"  {key}. {name}")
        print("  q. Quit")
        
        choice = input("\nSelect test to run: ").lower().strip()
        
        if choice == 'q':
            print("👋 Goodbye!")
            break
        elif choice in available_tests:
            test_name, test_func = available_tests[choice]
            print(f"\n🚀 Running: {test_name}")
            print("=" * 40)
            
            try:
                result = test_func()
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"\n{status}: {test_name}")
            except Exception as e:
                print(f"\n❌ ERROR: {e}")
        else:
            print("❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    print("🧪 TwoFactorAuthHandler Manual Testing Tool")
    print("This tool provides interactive tests for the complete 2FA authentication flow")
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
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
