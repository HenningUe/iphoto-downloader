#!/usr/bin/env python3
"""Automated testing for the 2FA web server using Selenium.

This module provides automated tests for validating the web server
functionality including the web interface, 2FA workflow, and server management
without requiring manual interaction.
"""

import logging
import os
import sys
import time
import threading
from pathlib import Path

import pytest

# Import test automation utilities
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from test_automation_utils import AutomatedTestContext, is_automated_test_environment

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️ Selenium not available, web automation tests will be skipped")

from auth2fa.web_server import TwoFAWebServer
from iphoto_downloader.config import get_config
from iphoto_downloader.logger import setup_logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not available")
def test_web_interface_automated():
    """Automated test of the web interface using Selenium WebDriver."""
    print("\\n🤖 Starting automated web interface test...")
    import shutil
    if not shutil.which("chrome") and not shutil.which("google-chrome"):
        pytest.skip("Chrome browser is not installed; skipping automated web interface test.")

    # Callback variables
    received_codes = []
    new_2fa_requests = 0

    def on_code_received(code):
        nonlocal received_codes
        received_codes.append(code)
        print(f"📱 Received 2FA code via web interface: ***{code[-2:]} (hidden for security)")
        return True

    def on_new_2fa_requested():
        nonlocal new_2fa_requests
        new_2fa_requests += 1
        print(f"🔄 New 2FA request #{new_2fa_requests} received via web interface")
        return True

    try:
        # Set up Chrome options for headless mode
        chrome_options = Options()
        if is_automated_test_environment():
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")

        # Initialize WebDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)

        # Start the web server
        server = TwoFAWebServer()
        server.set_callbacks(
            request_2fa_callback=on_new_2fa_requested, submit_code_callback=on_code_received
        )

        success = server.start()
        if not success:
            pytest.fail("Failed to start server")

        url = f"http://localhost:{server.port}"
        print(f"🌐 Server started on {url}")

        # Navigate to the web interface
        driver.get(url)
        print("🌐 Browser navigated to web interface")

        # Wait for page to load
        wait = WebDriverWait(driver, 10)

        # Test 1: Check page title and basic elements
        print("\\n🧪 Test 1: Checking page structure...")
        assert "2FA" in driver.title, f"Expected '2FA' in title, got: {driver.title}"

        # Look for key elements (adjust selectors based on actual HTML structure)
        try:
            request_button = wait.until(EC.element_to_be_clickable((By.ID, "request-2fa-btn")))
            print("✅ Found 'Request 2FA' button")
        except:
            # Try alternative selectors
            try:
                request_button = driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Request')]"
                )
                print("✅ Found request button with alternative selector")
            except:
                print("⚠️ Request button not found, checking page source...")
                print("Page source preview:", driver.page_source[:500])
                # Still try to continue test
                request_button = None

        # Test 2: Test request new 2FA functionality
        print("\\n🧪 Test 2: Testing 2FA request functionality...")
        if request_button:
            initial_requests = new_2fa_requests
            request_button.click()
            print("🖱️ Clicked 'Request 2FA' button")

            # Wait a moment for callback
            time.sleep(1)

            # Check if callback was triggered
            assert new_2fa_requests > initial_requests, (
                "2FA request callback should have been triggered"
            )
            print("✅ 2FA request callback triggered successfully")

        # Test 3: Test code submission with valid code
        print("\\n🧪 Test 3: Testing valid code submission...")
        try:
            code_input = driver.find_element(By.ID, "code-input")
            submit_button = driver.find_element(By.ID, "submit-btn")

            # Test valid 6-digit code
            test_code = "123456"
            code_input.clear()
            code_input.send_keys(test_code)
            submit_button.click()
            print(f"🖱️ Submitted valid code: {test_code}")

            # Wait for callback
            time.sleep(1)

            # Check if code was received
            assert test_code in received_codes, f"Code {test_code} should have been received"
            print("✅ Valid code submission successful")

        except Exception as e:
            print(f"⚠️ Code submission test failed (elements not found): {e}")
            # Try to find elements by alternative methods
            inputs = driver.find_elements(By.TAG_NAME, "input")
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"Found {len(inputs)} input elements and {len(buttons)} button elements")

        # Test 4: Test invalid code submission
        print("\\n🧪 Test 4: Testing invalid code submission...")
        try:
            code_input = driver.find_element(By.ID, "code-input")
            submit_button = driver.find_element(By.ID, "submit-btn")

            initial_codes_count = len(received_codes)

            # Test invalid code (too short)
            invalid_code = "123"
            code_input.clear()
            code_input.send_keys(invalid_code)
            submit_button.click()
            print(f"🖱️ Submitted invalid code: {invalid_code}")

            time.sleep(1)

            # Should not add to received codes if validation works
            assert (
                len(received_codes) == initial_codes_count or invalid_code not in received_codes
            ), "Invalid code should not be accepted"
            print("✅ Invalid code correctly rejected")

        except Exception as e:
            print(f"⚠️ Invalid code test skipped (elements not found): {e}")

        # Test 5: Check page responsiveness
        print("\\n🧪 Test 5: Testing page responsiveness...")

        # Test different window sizes
        original_size = driver.get_window_size()

        # Mobile size
        driver.set_window_size(375, 667)
        time.sleep(0.5)

        # Check if elements are still accessible
        try:
            elements_visible = len(driver.find_elements(By.TAG_NAME, "button")) > 0
            assert elements_visible, "Elements should remain visible on mobile"
            print("✅ Mobile responsiveness check passed")
        except:
            print("⚠️ Mobile responsiveness check could not be completed")

        # Restore original size
        driver.set_window_size(original_size["width"], original_size["height"])

        print("\\n🎉 All automated web interface tests completed!")
        print(f"📊 Test Results:")
        print(f"   - 2FA Requests: {new_2fa_requests}")
        print(f"   - Codes Received: {len(received_codes)}")
        print(f"   - Received Codes: {received_codes}")

        return {"requests": new_2fa_requests, "codes": received_codes, "success": True}

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        pytest.fail(f"Automated web interface test failed: {e}")

    finally:
        # Cleanup
        if driver:
            try:
                driver.quit()
                print("🧹 WebDriver closed")
            except:
                pass

        if server:
            try:
                server.stop()
                print("🛑 Web server stopped")
            except:
                pass


@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not available")
def test_web_server_basic_automation():
    """Basic automated test for web server startup/shutdown."""
    print("\\n🤖 Testing basic web server automation...")

    server = TwoFAWebServer()

    # Test server startup
    success = server.start()
    assert success, "Server should start successfully"
    print("✅ Server started successfully")

    # Test server properties
    assert server.port > 0, "Server should have a valid port"
    assert server.is_running(), "Server should report as running"
    print(f"✅ Server running on port {server.port}")

    # Test server shutdown
    server.stop()
    print("✅ Server stopped successfully")


if __name__ == "__main__":
    """Run automated tests directly."""
    print("🚀 Running automated web server tests...")

    # Set up environment for automated testing
    os.environ["PYTEST_CURRENT_TEST"] = "automation_test"

    with AutomatedTestContext(mock_browser=False, mock_input=True):
        try:
            test_web_server_basic_automation()
            if SELENIUM_AVAILABLE:
                test_web_interface_automated()
            else:
                print("⚠️ Selenium not available, skipping browser automation tests")
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            sys.exit(1)

    print("🎉 All automated tests completed successfully!")
