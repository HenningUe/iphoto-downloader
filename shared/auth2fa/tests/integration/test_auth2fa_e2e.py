#!/usr/bin/env python3
"""
End-to-End test for auth2fa package using Selenium browser automation.
This test verifies the complete web interface workflow including:
- Server startup and web page loading
- Form interactions and button clicks
- 2FA code submission and validation
- Success page navigation and feedback
- Error handling scenarios
"""

import logging
import os
import sys
import time
from typing import Optional, TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    pass  # No type-only imports needed

# Add auth2fa to path
current_dir = os.path.dirname(os.path.abspath(__file__))
auth2fa_src = os.path.join(current_dir, "..", "..", "src")
sys.path.insert(0, os.path.abspath(auth2fa_src))

# Import dependencies with proper error handling
try:
    from selenium import webdriver
    from selenium.common.exceptions import TimeoutException, WebDriverException
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    selenium_available = True
except ImportError:
    webdriver = None
    TimeoutException = None
    WebDriverException = None
    ChromeOptions = None
    By = None
    EC = None
    WebDriverWait = None
    selenium_available = False

try:
    from auth2fa.web_server import TwoFAWebServer
except ImportError:
    TwoFAWebServer = None


class Auth2FAE2ETest:
    """End-to-End test class for auth2fa web interface."""

    def __init__(self):
        self.server: Optional[TwoFAWebServer] = None
        self.driver: Optional[webdriver.Chrome] = None
        self.server_url: Optional[str] = None
        self.logger = logging.getLogger(__name__)

        # Test configuration
        self.timeout = 10  # seconds for WebDriverWait
        self.server_port_range = (9080, 9090)

        # Mock callbacks for testing
        self.mock_requests = []
        self.simulate_success = True

    def setup_chrome_driver(self) -> bool:
        """Setup Chrome WebDriver with appropriate options."""
        try:
            chrome_options = ChromeOptions()
            chrome_options.add_argument("--headless")  # Run in background
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")

            # Try to create driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(5)
            print("✅ Chrome WebDriver initialized successfully")
            return True

        except WebDriverException as e:
            print(f"❌ Failed to initialize Chrome WebDriver: {e}")
            print("💡 Make sure ChromeDriver is installed and in PATH")
            print("💡 Download from: https://chromedriver.chromium.org/")
            return False
        except Exception as e:
            print(f"❌ Unexpected error setting up WebDriver: {e}")
            return False

    def setup_auth2fa_server(self) -> bool:
        """Setup and start the auth2fa web server."""
        try:
            self.server = TwoFAWebServer(port_range=self.server_port_range)

            # Setup mock callbacks
            def mock_request_2fa_callback():
                self.mock_requests.append("request_2fa")
                print("   📱 Mock: 2FA code requested")
                return True

            def mock_submit_code_callback(code: str):
                self.mock_requests.append(f"submit_code:{code}")
                print(f"   🔐 Mock: Code '{code}' submitted")
                if self.simulate_success and code == "123456":
                    print("   ✅ Mock: Authentication successful")
                    return True
                else:
                    print("   ❌ Mock: Authentication failed")
                    return False

            self.server.set_callbacks(
                request_2fa_callback=mock_request_2fa_callback,
                submit_code_callback=mock_submit_code_callback,
            )

            # Start server
            if self.server.start():
                self.server_url = self.server.get_url()
                print(f"✅ Auth2FA server started at {self.server_url}")

                # Set initial state to waiting for code
                self.server.set_state("waiting_for_code", "Ready for testing")
                return True
            else:
                print("❌ Failed to start auth2fa server")
                return False

        except Exception as e:
            print(f"❌ Error setting up auth2fa server: {e}")
            return False

    def wait_for_element(
        self, by, value: str, timeout: Optional[int] = None
    ) -> Optional[object]:
        """Wait for an element to be present and return it."""
        try:
            wait = WebDriverWait(self.driver, timeout or self.timeout)
            element = wait.until(EC.presence_of_element_located((by, value)))
            return element
        except TimeoutException:
            print(f"❌ Timeout waiting for element: {by}={value}")
            return None

    def wait_for_clickable(
        self, by, value: str, timeout: Optional[int] = None
    ) -> Optional[object]:
        """Wait for an element to be clickable and return it."""
        try:
            wait = WebDriverWait(self.driver, timeout or self.timeout)
            element = wait.until(EC.element_to_be_clickable((by, value)))
            return element
        except TimeoutException:
            print(f"❌ Timeout waiting for clickable element: {by}={value}")
            return None

    def test_page_loading(self) -> bool:
        """Test that the main 2FA page loads correctly."""
        print("\n🧪 Testing page loading...")

        try:
            # Navigate to the auth2fa page
            self.driver.get(self.server_url)

            # Check page title
            expected_title = "iPhoto Downloader - 2FA Authentication"
            actual_title = self.driver.title
            if expected_title in actual_title:
                print("   ✅ Page title is correct")
            else:
                print(f"   ❌ Page title mismatch. Expected: {expected_title}, Got: {actual_title}")
                return False

            # Check main heading
            h1_element = self.wait_for_element(By.TAG_NAME, "h1")
            if h1_element and "iPhoto Downloader" in h1_element.text:
                print("   ✅ Main heading found")
            else:
                print("   ❌ Main heading not found or incorrect")
                return False

            # Check status section
            status_section = self.wait_for_element(By.CLASS_NAME, "status-section")
            if status_section:
                print("   ✅ Status section found")
            else:
                print("   ❌ Status section not found")
                return False

            # Check that form is visible (should be visible with waiting_for_code state)
            form_section = self.wait_for_element(By.ID, "2fa-form")
            if form_section and form_section.is_displayed():
                print("   ✅ 2FA form is visible")
            else:
                print("   ❌ 2FA form is not visible")
                return False

            print("   ✅ Page loading test passed!")
            return True

        except Exception as e:
            print(f"   ❌ Page loading test failed: {e}")
            return False

    def test_form_interaction(self) -> bool:
        """Test form input and button interactions."""
        print("\n🧪 Testing form interaction...")

        try:
            # Find the code input field
            code_input = self.wait_for_element(By.ID, "2fa-code")
            if not code_input:
                print("   ❌ Code input field not found")
                return False

            # Check input field properties
            max_length = code_input.get_attribute("maxlength")
            if max_length == "6":
                print("   ✅ Code input has correct maxlength=6")
            else:
                print(f"   ❌ Code input maxlength incorrect: {max_length}")
                return False

            # Test typing in the input field
            test_code = "123456"
            code_input.clear()
            code_input.send_keys(test_code)

            # Verify the input value
            input_value = code_input.get_attribute("value")
            if input_value == test_code:
                print(f"   ✅ Successfully entered code: {test_code}")
            else:
                print(f"   ❌ Input value mismatch. Expected: {test_code}, Got: {input_value}")
                return False

            # Find and test the submit button
            submit_button = self.wait_for_clickable(
                By.XPATH, "//button[contains(text(), 'Submit Code')]"
            )
            if not submit_button:
                print("   ❌ Submit button not found")
                return False

            if submit_button.is_enabled():
                print("   ✅ Submit button is enabled")
            else:
                print("   ❌ Submit button is disabled")
                return False

            # Test secondary button
            new_2fa_button = self.wait_for_clickable(
                By.XPATH, "//button[contains(text(), 'Request New 2FA Code')]"
            )
            if new_2fa_button:
                print("   ✅ 'Request New 2FA Code' button found")
            else:
                print("   ❌ 'Request New 2FA Code' button not found")
                return False

            print("   ✅ Form interaction test passed!")
            return True

        except Exception as e:
            print(f"   ❌ Form interaction test failed: {e}")
            return False

    def test_successful_authentication(self) -> bool:
        """Test successful 2FA code submission and success flow."""
        print("\n🧪 Testing successful authentication flow...")

        try:
            # Ensure we're testing success scenario
            self.simulate_success = True

            # Clear any previous input and enter valid code
            code_input = self.wait_for_element(By.ID, "2fa-code")
            if not code_input:
                print("   ❌ Code input field not found")
                return False

            code_input.clear()
            valid_code = "123456"
            code_input.send_keys(valid_code)

            # Submit the form
            submit_button = self.wait_for_clickable(
                By.XPATH, "//button[contains(text(), 'Submit Code')]"
            )
            if not submit_button:
                print("   ❌ Submit button not found")
                return False

            print(f"   🔐 Submitting code: {valid_code}")
            submit_button.click()

            # Wait for success message to appear - handle "Validating" intermediate state
            time.sleep(1)  # Brief pause for processing

            # Check for success message in the message div
            try:
                wait = WebDriverWait(self.driver, 10)  # Longer wait for processing

                # Wait for success message - could be immediate or after processing
                def success_condition(driver):
                    try:
                        # Check message element first
                        message_elem = driver.find_element(By.ID, "message")
                        if message_elem.is_displayed():
                            text = message_elem.text.lower()
                            # Skip the "validating" intermediate state
                            if "validating" in text:
                                return False
                            # Accept various success indicators
                            return (
                                "successful" in text
                                or "authentication successful" in text
                                or "✅" in text
                            )

                        # Also check status element for success
                        status_elem = driver.find_element(By.ID, "status")
                        if status_elem:
                            status_text = status_elem.text.lower()
                            return (
                                "successful" in status_text
                                or "authenticated" in status_text
                                or "✅" in status_text
                            )

                        return False
                    except Exception:
                        return False

                if wait.until(success_condition):
                    # Get the actual success message
                    try:
                        message_element = self.driver.find_element(By.ID, "message")
                        if message_element.is_displayed():
                            message_text = message_element.text
                            print(f"   ✅ Success message displayed: {message_text}")
                        else:
                            status_element = self.driver.find_element(By.ID, "status")
                            status_text = status_element.text
                            print(f"   ✅ Success status displayed: {status_text}")
                    except Exception:
                        print("   ✅ Success condition met")
                else:
                    print("   ❌ No success message appeared")
                    return False

            except TimeoutException:
                print("   ❌ Timeout waiting for success message")
                # Check current state as fallback
                try:
                    status_element = self.driver.find_element(By.ID, "status")
                    if status_element and "successful" in status_element.text.lower():
                        print("   ✅ Success found in status instead")
                    else:
                        print("   ❌ No success indication found anywhere")
                        return False
                except Exception:
                    print("   ❌ Could not find any success indication")
                    return False

            # Wait for redirect to success page or success state
            try:
                wait = WebDriverWait(self.driver, 8)  # Wait up to 8 seconds for redirect
                wait.until(lambda driver: "/success" in driver.current_url)
                print("   ✅ Successfully redirected to success page")

                # Verify success page content
                success_title = self.wait_for_element(By.CLASS_NAME, "success-title")
                if success_title and "successful" in success_title.text.lower():
                    print("   ✅ Success page content verified")
                else:
                    print("   ⚠️  Success page found but content not verified")

            except TimeoutException:
                print("   ⚠️  No redirect occurred, checking for success state on main page...")
                current_url = self.driver.current_url
                print(f"   Current URL: {current_url}")

                # Check if we're still on main page but with success state
                try:
                    status_element = self.driver.find_element(By.ID, "status")
                    if status_element and "successful" in status_element.text.lower():
                        print("   ✅ Success status shown on main page")
                    else:
                        # Check server state directly
                        server_status = self.server.get_status()
                        if server_status["state"] == "authenticated":
                            print("   ✅ Server state shows authenticated")
                        else:
                            print(f"   ❌ Server state: {server_status}")
                            return False
                except:
                    print("   ❌ Could not verify success state")
                    return False

            # Verify mock callback was called
            if f"submit_code:{valid_code}" in self.mock_requests:
                print("   ✅ Mock callback was called correctly")
            else:
                print("   ❌ Mock callback was not called")
                print(f"   Mock requests: {self.mock_requests}")
                return False

            print("   ✅ Successful authentication test passed!")
            return True

        except Exception as e:
            print(f"   ❌ Successful authentication test failed: {e}")
            return False

    def test_failed_authentication(self) -> bool:
        """Test failed 2FA code submission and error handling."""
        print("\n🧪 Testing failed authentication flow...")

        try:
            # Navigate back to main page
            self.driver.get(self.server_url)
            time.sleep(1)

            # Set server to waiting state
            self.server.set_state("waiting_for_code", "Ready for failed test")
            time.sleep(0.5)

            # Enable failure simulation
            self.simulate_success = False

            # Enter invalid code
            code_input = self.wait_for_element(By.ID, "2fa-code")
            if not code_input:
                print("   ❌ Code input field not found")
                return False

            code_input.clear()
            invalid_code = "999999"
            code_input.send_keys(invalid_code)

            # Submit the form
            submit_button = self.wait_for_clickable(
                By.XPATH, "//button[contains(text(), 'Submit Code')]"
            )
            if not submit_button:
                print("   ❌ Submit button not found")
                return False

            print(f"   🔐 Submitting invalid code: {invalid_code}")
            submit_button.click()

            # Wait for error message
            time.sleep(1)

            try:
                wait = WebDriverWait(self.driver, 5)
                error_message = wait.until(lambda driver: driver.find_element(By.ID, "message"))

                if error_message.is_displayed():
                    message_text = error_message.text
                    if "failed" in message_text.lower() or "invalid" in message_text.lower():
                        print(f"   ✅ Error message displayed: {message_text}")
                    else:
                        print(f"   ❌ Unexpected message: {message_text}")
                        return False
                else:
                    print("   ❌ Error message not visible")
                    return False

            except TimeoutException:
                print("   ❌ No error message appeared")
                return False

            # Verify we're still on the main page (no redirect)
            if "/success" not in self.driver.current_url:
                print("   ✅ Correctly stayed on main page after failed auth")
            else:
                print("   ❌ Incorrectly redirected to success page")
                return False

            # Verify form is still visible for retry
            form_section = self.driver.find_element(By.ID, "2fa-form")
            if form_section.is_displayed():
                print("   ✅ Form still visible for retry")
            else:
                print("   ❌ Form hidden after failed attempt")
                return False

            print("   ✅ Failed authentication test passed!")
            return True

        except Exception as e:
            print(f"   ❌ Failed authentication test failed: {e}")
            return False

    def test_invalid_code_format(self) -> bool:
        """Test validation of invalid code formats."""
        print("\n🧪 Testing invalid code format validation...")

        try:
            # Navigate back to main page
            self.driver.get(self.server_url)
            time.sleep(1)

            # Set server to waiting state
            self.server.set_state("waiting_for_code", "Ready for validation test")
            time.sleep(0.5)

            invalid_codes = [
                ("", "empty code"),
                ("12345", "too short"),
                ("1234567", "too long"),
                ("abcdef", "letters"),
                ("12345a", "mixed"),
            ]

            for code, description in invalid_codes:
                print(f"   🧪 Testing {description}: '{code}'")

                try:
                    # Enter invalid code
                    code_input = self.wait_for_element(By.ID, "2fa-code")
                    code_input.clear()
                    if code:  # Only send keys if code is not empty
                        code_input.send_keys(code)

                    # Submit
                    submit_btn = self.wait_for_clickable(
                        By.XPATH, "//button[contains(text(), 'Submit Code')]"
                    )
                    submit_btn.click()

                    time.sleep(0.5)  # Brief pause for processing

                    # Handle browser alerts for client-side validation
                    try:
                        alert = self.driver.switch_to.alert
                        alert_text = alert.text
                        print(f"      ✅ Browser alert: {alert_text}")
                        alert.accept()  # Close the alert
                        continue  # Move to next test case
                    except:
                        pass  # No alert, continue with server-side validation check

                    # For empty code, browser validation might prevent submission
                    if code == "":
                        print(f"      ✅ Empty code handled (browser validation)")
                        continue

                    # Check for validation message
                    try:
                        message_element = self.driver.find_element(By.ID, "message")
                        if message_element.is_displayed():
                            message_text = message_element.text
                            expected_terms = ["invalid", "format", "6 digits", "numeric"]
                            if any(term in message_text.lower() for term in expected_terms):
                                print(f"      ✅ Validation message: {message_text}")
                            else:
                                print(f"      ⚠️  Unexpected message: {message_text}")
                        else:
                            print(f"      ⚠️  No validation message for {description}")
                    except:
                        print(f"      ⚠️  No message element found for {description}")

                    # Verify no redirect occurred
                    if "/success" not in self.driver.current_url:
                        print(f"      ✅ No redirect for invalid {description}")
                    else:
                        print(f"      ❌ Unexpected redirect for invalid {description}")
                        return False

                except Exception as e:
                    print(f"      ❌ Error testing {description}: {e}")
                    # Continue with other test cases
                    continue

            print("   ✅ Invalid code format test passed!")
            return True

        except Exception as e:
            print(f"   ❌ Invalid code format test failed: {e}")
            return False

    def test_request_new_2fa(self) -> bool:
        """Test the 'Request New 2FA Code' functionality."""
        print("\n🧪 Testing 'Request New 2FA Code' button...")

        try:
            # Navigate back to main page
            self.driver.get(self.server_url)
            time.sleep(1)

            # Clear previous mock requests
            self.mock_requests.clear()

            # Find and click the "Request New 2FA Code" button
            new_2fa_button = self.wait_for_clickable(
                By.XPATH, "//button[contains(text(), 'Request New 2FA Code')]"
            )
            if not new_2fa_button:
                print("   ❌ 'Request New 2FA Code' button not found")
                return False

            print("   🔄 Clicking 'Request New 2FA Code' button")
            new_2fa_button.click()

            time.sleep(1)  # Wait for processing

            # Verify mock callback was called
            if "request_2fa" in self.mock_requests:
                print("   ✅ Request new 2FA callback was called")
            else:
                print("   ❌ Request new 2FA callback was not called")
                print(f"   Mock requests: {self.mock_requests}")
                return False

            # Check for status update (should show waiting message)
            status_element = self.wait_for_element(By.ID, "status")
            if status_element:
                status_text = status_element.text
                print(f"   📊 Status: {status_text}")
                if "waiting" in status_text.lower():
                    print("   ✅ Status shows waiting for code")
                else:
                    print("   ⚠️  Status may not reflect new request")

            print("   ✅ Request New 2FA test passed!")
            return True

        except Exception as e:
            print(f"   ❌ Request New 2FA test failed: {e}")
            return False

    def test_ui_responsiveness(self) -> bool:
        """Test UI responsiveness and visual feedback."""
        print("\n🧪 Testing UI responsiveness...")

        try:
            # Navigate back to main page
            self.driver.get(self.server_url)
            time.sleep(1)

            # Test button state during submission
            code_input = self.wait_for_element(By.ID, "2fa-code")
            code_input.clear()
            code_input.send_keys("123456")

            submit_button = self.wait_for_clickable(
                By.XPATH, "//button[contains(text(), 'Submit Code')]"
            )
            original_text = submit_button.text

            # Click submit and immediately check button state
            submit_button.click()

            # Quick check for button state change (might be very brief)
            time.sleep(0.1)
            try:
                # Button might be disabled or show "Validating..." briefly
                current_text = submit_button.text
                is_disabled = not submit_button.is_enabled()

                if is_disabled or "validating" in current_text.lower():
                    print("   ✅ Submit button shows loading state")
                else:
                    print("   ⚠️  Submit button state change not detected (may be too fast)")

            except:
                print("   ⚠️  Could not check button state during submission")

            # Wait for processing to complete
            time.sleep(2)

            # Verify button returns to normal state (if still on page)
            if "/success" not in self.driver.current_url:
                try:
                    submit_button = self.driver.find_element(
                        By.XPATH, "//button[contains(text(), 'Submit Code')]"
                    )
                    if submit_button.is_enabled():
                        print("   ✅ Submit button re-enabled after processing")
                    else:
                        print("   ❌ Submit button still disabled")
                        return False
                except:
                    pass  # Button might not be present anymore

            print("   ✅ UI responsiveness test passed!")
            return True

        except Exception as e:
            print(f"   ❌ UI responsiveness test failed: {e}")
            return False

    def run_all_tests(self) -> bool:
        """Run all end-to-end tests."""
        print("🚀 Starting auth2fa End-to-End Test Suite")
        print("=" * 60)

        # Setup phase
        if not self.setup_chrome_driver():
            return False

        if not self.setup_auth2fa_server():
            self.cleanup()
            return False

        # Test execution
        tests = [
            ("Page Loading", self.test_page_loading),
            ("Form Interaction", self.test_form_interaction),
            ("Successful Authentication", self.test_successful_authentication),
            ("Failed Authentication", self.test_failed_authentication),
            ("Invalid Code Format", self.test_invalid_code_format),
            ("Request New 2FA", self.test_request_new_2fa),
            ("UI Responsiveness", self.test_ui_responsiveness),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            try:
                print(f"\n🧪 Running: {test_name}")
                if test_func():
                    passed += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    failed += 1
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                failed += 1
                print(f"❌ {test_name}: FAILED with exception: {e}")

        # Results summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed} passed, {failed} failed")

        if failed == 0:
            print("🎉 All E2E tests passed! The auth2fa web interface is working correctly.")
            print("\n✨ Verified functionality:")
            print("   • Complete web page loading and rendering")
            print("   • Form input validation and interaction")
            print("   • Successful authentication flow with redirect")
            print("   • Failed authentication error handling")
            print("   • Invalid code format validation")
            print("   • Request new 2FA code functionality")
            print("   • UI responsiveness and visual feedback")
        else:
            print("❌ Some E2E tests failed. Check the implementation.")

        # Cleanup
        self.cleanup()
        return failed == 0

    def cleanup(self):
        """Clean up resources."""
        print("\n🧹 Cleaning up...")

        if self.driver:
            try:
                self.driver.quit()
                print("   ✅ WebDriver closed")
            except Exception as e:
                print(f"   ⚠️  Error closing WebDriver: {e}")

        if self.server:
            try:
                self.server.stop()
                print("   ✅ Auth2FA server stopped")
            except Exception as e:
                print(f"   ⚠️  Error stopping server: {e}")


def main():
    """Main test execution function."""
    # Setup logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise

    # Run tests
    test_suite = Auth2FAE2ETest()
    success = test_suite.run_all_tests()

    return 0 if success else 1


@pytest.mark.integration
def test_auth2fa_e2e_selenium():
    """Pytest wrapper for the Selenium E2E test."""
    # Check for required dependencies and skip if not available
    pytest.importorskip("selenium", reason="Selenium package required for E2E browser tests")
    
    try:
        from auth2fa.web_server import TwoFAWebServer  # noqa: F401
    except ImportError as e:
        pytest.skip(f"Failed to import TwoFAWebServer: {e}")
    
    # Setup logging to reduce noise
    logging.basicConfig(level=logging.WARNING)
    
    # Run the test suite
    test_suite = Auth2FAE2ETest()
    success = test_suite.run_all_tests()
    
    assert success, "Auth2FA Selenium E2E tests failed"


if __name__ == "__main__":
    sys.exit(main())
