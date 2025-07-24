"""Tests for 2FA authentication system."""

import unittest
import tempfile
import shutil
import time
import requests
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import logging

from src.icloud_photo_sync.src.icloud_photo_sync.logger import setup_logging


class Test2FASystem(unittest.TestCase):
    """Test 2FA authentication system functionality."""

    def setUp(self):
        """Set up test fixtures."""
        setup_logging(log_level=logging.INFO)

        self.temp_dir = Path(tempfile.mkdtemp())
        self.env_file = self.temp_dir / ".env"

        # Create test .env file
        self.env_file.write_text("""
SYNC_DIRECTORY=./test_photos
DRY_RUN=true
LOG_LEVEL=INFO
ENABLE_PUSHOVER=true
""")

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('requests.post')
    def test_pushover_notification_sending(self):
        """Test Pushover notification sending."""
        from src.icloud_photo_sync.src.icloud_photo_sync.auth2fa.pushover_service import (
            PushoverService
        )

        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 1}

        mock_post = requests.post
        mock_post.return_value = mock_response

        # Create PushoverService
        config = Mock()
        config.pushover_api_token = "test_token"
        config.pushover_user_key = "test_user"
        config.pushover_device = "test_device"

        service = PushoverService(config)

        # Test sending notification
        result = service.send_notification(
            title="Test Title",
            message="Test Message",
            url="http://localhost:8080"
        )

        self.assertTrue(result)
        mock_post.assert_called_once()

        # Verify request parameters
        call_args = mock_post.call_args
        self.assertIn("token", call_args[1]["data"])
        self.assertIn("user", call_args[1]["data"])
        self.assertEqual(call_args[1]["data"]["title"], "Test Title")
        self.assertEqual(call_args[1]["data"]["message"], "Test Message")

    @patch('requests.post')
    def test_pushover_notification_failure(self):
        """Test Pushover notification failure handling."""
        from src.icloud_photo_sync.src.icloud_photo_sync.auth2fa.pushover_service import (
            PushoverService
        )

        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"errors": ["Invalid token"]}

        mock_post = requests.post
        mock_post.return_value = mock_response

        config = Mock()
        config.pushover_api_token = "invalid_token"
        config.pushover_user_key = "test_user"
        config.pushover_device = ""

        service = PushoverService(config)

        result = service.send_notification(
            title="Test Title",
            message="Test Message"
        )

        self.assertFalse(result)

    def test_local_web_server_startup_shutdown(self):
        """Test local web server startup and shutdown."""
        from src.icloud_photo_sync.src.icloud_photo_sync.auth2fa.web_server import Auth2FAWebServer

        # Create web server
        server = Auth2FAWebServer()

        # Test startup
        port = server.start()
        self.assertIsNotNone(port)
        self.assertTrue(8080 <= port <= 8090)  # Should be in expected range

        # Test server is accessible
        time.sleep(0.5)  # Give server time to start
        response = requests.get(f"http://localhost:{port}", timeout=2)
        self.assertEqual(response.status_code, 200)
        self.assertIn("2FA Authentication", response.text)

        # Test shutdown
        server.stop()

        # Verify server is stopped
        time.sleep(0.5)
        with self.assertRaises(requests.exceptions.ConnectionError):
            requests.get(f"http://localhost:{port}", timeout=2)

    def test_web_server_port_conflict_handling(self):
        """Test web server port conflict handling."""
        from src.icloud_photo_sync.src.icloud_photo_sync.auth2fa.web_server import Auth2FAWebServer

        # Start first server
        server1 = Auth2FAWebServer()
        port1 = server1.start()
        self.assertIsNotNone(port1)

        try:
            # Start second server - should use different port
            server2 = Auth2FAWebServer()
            port2 = server2.start()
            self.assertIsNotNone(port2)
            self.assertNotEqual(port1, port2)

            server2.stop()
        finally:
            server1.stop()

    def test_2fa_code_validation_via_web_interface(self):
        """Test 2FA code validation through web interface."""
        from src.icloud_photo_sync.src.icloud_photo_sync.auth2fa.web_server import Auth2FAWebServer
        from src.icloud_photo_sync.src.icloud_photo_sync.auth2fa.session_manager import SessionManager

        # Create session manager and web server
        session_manager = SessionManager()
        server = Auth2FAWebServer(session_manager=session_manager)

        # Start server
        port = server.start()
        self.assertIsNotNone(port)

        try:
            time.sleep(0.5)  # Give server time to start

            # Create a 2FA session
            session_id = session_manager.create_session()

            # Test submitting 2FA code
            response = requests.post(
                f"http://localhost:{port}/submit_2fa",
                data={"code": "123456", "session_id": session_id},
                timeout=2
            )

            self.assertEqual(response.status_code, 200)

            # Verify session was updated
            session = session_manager.get_session(session_id)
            self.assertIsNotNone(session)
            self.assertEqual(session["code"], "123456")

        finally:
            server.stop()

    def test_session_storage_and_retrieval(self):
        """Test session storage and retrieval."""
        from src.icloud_photo_sync.src.icloud_photo_sync.auth2fa.session_manager import SessionManager

        # Create session manager with temp directory
        session_manager = SessionManager(session_dir=self.temp_dir / "sessions")

        # Create a session
        session_id = session_manager.create_session()
        self.assertIsNotNone(session_id)

        # Retrieve session
        session = session_manager.get_session(session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session["id"], session_id)
        self.assertEqual(session["status"], "pending")

        # Update session
        session_manager.update_session(session_id, code="123456", status="authenticated")

        # Verify update
        updated_session = session_manager.get_session(session_id)
        self.assertEqual(updated_session["code"], "123456")
        self.assertEqual(updated_session["status"], "authenticated")

        # Test session persistence (create new manager)
        new_session_manager = SessionManager(session_dir=self.temp_dir / "sessions")
        persisted_session = new_session_manager.get_session(session_id)
        self.assertEqual(persisted_session["code"], "123456")
        self.assertEqual(persisted_session["status"], "authenticated")

    def test_session_cleanup(self):
        """Test session cleanup for expired sessions."""
        from src.icloud_photo_sync.src.icloud_photo_sync.auth2fa.session_manager import SessionManager

        session_manager = SessionManager(session_dir=self.temp_dir / "sessions")

        # Create session
        session_id = session_manager.create_session()

        # Manually expire session by modifying creation time
        session = session_manager.get_session(session_id)
        session["created_at"] = time.time() - 3700  # 1+ hour ago
        session_manager._save_session(session)

        # Run cleanup
        session_manager.cleanup_expired_sessions()

        # Verify session was removed
        cleaned_session = session_manager.get_session(session_id)
        self.assertIsNone(cleaned_session)

    def test_2fa_error_handling_port_conflicts(self):
        """Test error handling for port conflicts."""
        from src.icloud_photo_sync.src.icloud_photo_sync.auth2fa.web_server import Auth2FAWebServer
        import socket

        # Occupy all ports in the range
        sockets = []
        try:
            for port in range(8080, 8091):  # Occupy all available ports
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('localhost', port))
                sock.listen(1)
                sockets.append(sock)

            # Try to start server - should fail gracefully
            server = Auth2FAWebServer()
            port = server.start()

            # Should return None when no ports available
            self.assertIsNone(port)

        finally:
            # Clean up sockets
            for sock in sockets:
                sock.close()

    @patch('src.icloud_photo_sync.src.icloud_photo_sync.auth2fa.pushover_service.requests.post')
    def test_2fa_api_failure_handling(self):
        """Test handling of API failures."""
        from src.icloud_photo_sync.src.icloud_photo_sync.auth2fa.pushover_service import PushoverService

        # Mock network error
        mock_post = MagicMock()
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        config = Mock()
        config.pushover_api_token = "test_token"
        config.pushover_user_key = "test_user"
        config.pushover_device = ""

        service = PushoverService(config)

        # Test that network errors are handled gracefully
        result = service.send_notification("Title", "Message")
        self.assertFalse(result)

    def test_session_timeout_mechanisms(self):
        """Test session timeout mechanisms."""
        from src.icloud_photo_sync.src.icloud_photo_sync.auth2fa.session_manager import SessionManager

        session_manager = SessionManager(session_dir=self.temp_dir / "sessions")

        # Create session
        session_id = session_manager.create_session()

        # Check if session is valid (should be)
        self.assertTrue(session_manager.is_session_valid(session_id))

        # Manually expire session
        session = session_manager.get_session(session_id)
        session["created_at"] = time.time() - 3700  # 1+ hour ago
        session_manager._save_session(session)

        # Check if session is still valid (should not be)
        self.assertFalse(session_manager.is_session_valid(session_id))

    def test_rate_limiting_for_2fa_attempts(self):
        """Test rate limiting for 2FA attempts."""
        from src.icloud_photo_sync.src.icloud_photo_sync.auth2fa.session_manager import SessionManager

        session_manager = SessionManager(session_dir=self.temp_dir / "sessions")

        # Create session
        session_id = session_manager.create_session()

        # Make multiple rapid attempts (should be rate limited)
        for i in range(10):
            session_manager.update_session(session_id, code=f"wrong{i}")

        # Check if rate limiting is enforced
        session = session_manager.get_session(session_id)
        self.assertIn("attempts", session)

        # Should prevent too many attempts
        is_blocked = session_manager.is_rate_limited(session_id)
        if session["attempts"] > 5:  # Assuming 5 is the limit
            self.assertTrue(is_blocked)


if __name__ == '__main__':
    unittest.main()
