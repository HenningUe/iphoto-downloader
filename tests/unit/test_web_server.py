"""Unit tests for the 2FA web server."""

import threading
import time
import requests
from unittest.mock import Mock, patch
import pytest

from icloud_photo_sync.auth.web_server import TwoFAWebServer, TwoFAHandler
from icloud_photo_sync.logger import setup_logging


class TestTwoFAWebServer:
    """Test cases for the 2FA web server."""

    @pytest.fixture(autouse=True)
    def setup_logging(self):
        """Setup logging for tests."""
        from icloud_photo_sync.config import BaseConfig
        mock_config = Mock(spec=BaseConfig)
        mock_config.get_log_level.return_value = 20
        setup_logging(mock_config)

    @pytest.fixture
    def web_server(self):
        """Create a web server instance for testing."""
        server = TwoFAWebServer(port_range=(8900, 8910))
        yield server
        # Cleanup
        if server.server:
            server.stop()

    def test_find_available_port(self, web_server):
        """Test finding an available port."""
        port = web_server.find_available_port()
        assert port is not None
        assert 8900 <= port <= 8910

    def test_start_stop_server(self, web_server):
        """Test starting and stopping the web server."""
        # Test start
        assert web_server.start() is True
        assert web_server.server is not None
        assert web_server.port is not None
        assert web_server.server_thread is not None

        # Test URL generation
        url = web_server.get_url()
        assert url == f"http://{web_server.host}:{web_server.port}"
        # Verify that we have a valid IP address (either localhost fallback or real IP)
        import re
        ip_pattern = (r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
                      r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
        assert re.match(ip_pattern, web_server.host), f"Invalid IP address: {web_server.host}"

        # Test stop
        web_server.stop()
        assert web_server.server is None
        assert web_server.server_thread is None

    def test_server_responses(self, web_server):
        """Test HTTP responses from the server."""
        assert web_server.start() is True
        base_url = web_server.get_url()

        # Test main page
        response = requests.get(f"{base_url}/", timeout=5)
        assert response.status_code == 200
        assert "iCloud Photo Sync" in response.text
        assert "Two-Factor Authentication" in response.text

        # Test CSS
        response = requests.get(f"{base_url}/styles.css", timeout=5)
        assert response.status_code == 200
        assert "body" in response.text

        # Test 404
        response = requests.get(f"{base_url}/nonexistent", timeout=5)
        assert response.status_code == 404

        web_server.stop()

    def test_status_endpoint(self, web_server):
        """Test the status endpoint."""
        assert web_server.start() is True
        base_url = web_server.get_url()

        # Test initial status
        response = requests.get(f"{base_url}/status", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert 'state' in data
        assert 'status' in data
        assert data['state'] == 'pending'

        # Change state and test again
        web_server.set_state('waiting_for_code', 'Test message')
        response = requests.get(f"{base_url}/status", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data['state'] == 'waiting_for_code'
        assert data['message'] == 'Test message'

        web_server.stop()

    def test_2fa_code_submission(self, web_server):
        """Test 2FA code submission."""
        assert web_server.start() is True
        base_url = web_server.get_url()

        # Submit a code
        response = requests.post(
            f"{base_url}/submit_2fa",
            data={'code': '123456'},
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

        # Test empty code
        response = requests.post(
            f"{base_url}/submit_2fa",
            data={'code': ''},
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is False
        assert 'No code provided' in data['message']

        web_server.stop()

    def test_new_2fa_request(self, web_server):
        """Test requesting new 2FA code."""
        assert web_server.start() is True
        base_url = web_server.get_url()

        # Mock callback
        callback_called = []

        def mock_callback():
            callback_called.append(True)
            return True

        web_server.set_callbacks(request_2fa_callback=mock_callback)

        # Request new 2FA
        response = requests.post(f"{base_url}/request_new_2fa", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(callback_called) == 1

        web_server.stop()

    def test_wait_for_code(self, web_server):
        """Test waiting for 2FA code submission."""
        assert web_server.start() is True

        # Submit code from another thread
        def submit_code():
            time.sleep(0.5)  # Wait a bit before submitting
            web_server.submit_2fa_code('654321')

        submit_thread = threading.Thread(target=submit_code)
        submit_thread.start()

        # Wait for code
        code = web_server.wait_for_code(timeout=2)
        assert code == '654321'

        submit_thread.join()
        web_server.stop()

    def test_wait_for_code_timeout(self, web_server):
        """Test timeout when waiting for 2FA code."""
        assert web_server.start() is True

        # Wait for code with short timeout
        code = web_server.wait_for_code(timeout=0.5)
        assert code is None
        assert web_server.state == 'failed'

        web_server.stop()

    def test_state_management(self, web_server):
        """Test state management."""
        # Test initial state
        assert web_server.state == 'pending'

        # Test state changes
        web_server.set_state('waiting_for_code', 'Waiting...')
        assert web_server.state == 'waiting_for_code'
        assert web_server.status_message == 'Waiting...'

        # Test status dictionary
        status = web_server.get_status()
        assert status['state'] == 'waiting_for_code'
        assert status['message'] == 'Waiting...'
        assert 'Waiting for 2FA code' in status['status']

    def test_callbacks(self, web_server):
        """Test callback functionality."""
        request_called = []
        submit_called = []

        def request_callback():
            request_called.append(True)
            return True

        def submit_callback():
            submit_called.append(True)
            return True

        web_server.set_callbacks(
            request_2fa_callback=request_callback,
            submit_code_callback=submit_callback
        )

        # Test request callback
        assert web_server.request_new_2fa() is True
        assert len(request_called) == 1

        # Submit callback is not used in current implementation
        assert len(submit_called) == 0

    @patch('webbrowser.open')
    def test_open_browser(self, mock_open, web_server):
        """Test opening browser."""
        assert web_server.start() is True

        # Test successful browser opening
        mock_open.return_value = True
        assert web_server.open_browser() is True
        mock_open.assert_called_once_with(web_server.get_url())

        # Test browser opening failure
        mock_open.side_effect = Exception("Browser failed")
        assert web_server.open_browser() is False

        web_server.stop()

    def test_port_conflict_handling(self):
        """Test handling of port conflicts."""
        # Start first server
        server1 = TwoFAWebServer(port_range=(8950, 8952))
        assert server1.start() is True
        port1 = server1.port

        # Start second server (should get different port)
        server2 = TwoFAWebServer(port_range=(8950, 8952))
        assert server2.start() is True
        port2 = server2.port

        # Ports should be different
        assert port1 != port2

        # Cleanup
        server1.stop()
        server2.stop()

    def test_no_available_ports(self):
        """Test behavior when no ports are available."""
        # Try to start server with invalid port range
        server = TwoFAWebServer(port_range=(99999, 99999))  # Invalid port
        assert server.start() is False
        assert server.port is None


class TestTwoFAHandler:
    """Test cases for the HTTP request handler."""

    def test_handler_initialization(self):
        """Test handler can be initialized."""
        # This is mainly for coverage - the handler is tested
        # indirectly through the server tests above
        handler = TwoFAHandler
        assert handler is not None

        # Test that the handler has the required methods
        assert hasattr(handler, 'do_GET')
        assert hasattr(handler, 'do_POST')
        assert hasattr(handler, '_serve_main_page')
        assert hasattr(handler, '_serve_status')
        assert hasattr(handler, '_handle_2fa_submission')
        assert hasattr(handler, '_handle_new_2fa_request')
