"""Tests for the two-factor authentication handler."""

from unittest.mock import Mock, patch

from auth2fa.authenticator import (
    TwoFactorAuthHandler, handle_2fa_authentication
)


class TestTwoFactorAuthHandler:
    """Test the TwoFactorAuthHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        pass

        # Create a mock config
        self.config = Mock(spec=BaseConfig)
        self.config.enable_pushover = False
        self.config.pushover_api_token = None
        self.config.pushover_user_key = None
        self.handler = TwoFactorAuthHandler(self.config)

    def test_init(self):
        """Test handler initialization."""
        assert self.handler.config == self.config
        assert self.handler.logger is not None
        assert self.handler._web_server is None

    @patch('src.icloud_photo_sync.auth.two_factor_handler.TwoFAWebServer')
    def test_handle_2fa_authentication_success(self, mock_web_server_class):
        """Test successful 2FA authentication."""
        # Mock web server
        mock_web_server = Mock()
        mock_web_server.start.return_value = True
        mock_web_server.get_url.return_value = "http://localhost:8080"
        mock_web_server.open_browser.return_value = True
        mock_web_server.wait_for_code.return_value = "123456"
        mock_web_server_class.return_value = mock_web_server

        # Mock callbacks
        request_callback = Mock(return_value=True)
        validate_callback = Mock(return_value=True)

        # Test
        result = self.handler.handle_2fa_authentication(
            request_2fa_callback=request_callback,
            validate_2fa_callback=validate_callback
        )

        # Verify
        assert result == "123456"
        mock_web_server.start.assert_called_once()
        mock_web_server.set_state.assert_called()
        mock_web_server.wait_for_code.assert_called_once_with(timeout=300)
        mock_web_server.stop.assert_called_once()

    @patch('src.icloud_photo_sync.auth.two_factor_handler.TwoFAWebServer')
    def test_handle_2fa_authentication_server_start_failure(self, mock_web_server_class):
        """Test 2FA authentication when web server fails to start."""
        # Mock web server
        mock_web_server = Mock()
        mock_web_server.start.return_value = False
        mock_web_server_class.return_value = mock_web_server

        # Test
        result = self.handler.handle_2fa_authentication(
        )

        # Verify
        assert result is None
        mock_web_server.start.assert_called_once()
        # Stop is called in finally block even if start fails
        mock_web_server.stop.assert_called_once()

    @patch('src.icloud_photo_sync.auth.two_factor_handler.TwoFAWebServer')
    def test_handle_2fa_authentication_timeout(self, mock_web_server_class):
        """Test 2FA authentication timeout."""
        # Mock web server
        mock_web_server = Mock()
        mock_web_server.start.return_value = True
        mock_web_server.get_url.return_value = "http://localhost:8080"
        mock_web_server.open_browser.return_value = True
        mock_web_server.wait_for_code.return_value = None  # Timeout
        mock_web_server_class.return_value = mock_web_server

        # Test
        result = self.handler.handle_2fa_authentication(
        )

        # Verify
        assert result is None
        mock_web_server.start.assert_called_once()
        mock_web_server.set_state.assert_called()
        mock_web_server.stop.assert_called_once()

    @patch('src.icloud_photo_sync.auth.two_factor_handler.TwoFAWebServer')
    def test_handle_2fa_authentication_validation_failure(self, mock_web_server_class):
        """Test 2FA authentication with validation failure."""
        # Mock web server
        mock_web_server = Mock()
        mock_web_server.start.return_value = True
        mock_web_server.get_url.return_value = "http://localhost:8080"
        mock_web_server.open_browser.return_value = True
        mock_web_server.wait_for_code.return_value = "123456"
        mock_web_server_class.return_value = mock_web_server

        # Mock callbacks
        validate_callback = Mock(return_value=False)  # Validation fails

        # Test
        result = self.handler.handle_2fa_authentication(
            validate_2fa_callback=validate_callback
        )

        # Verify
        assert result is None
        validate_callback.assert_called_once_with("123456")
        mock_web_server.stop.assert_called_once()

    @patch('src.icloud_photo_sync.auth.two_factor_handler.PushoverService')
    def test_send_pushover_notification(self, mock_pushover_service_class):
        """Test sending Pushover notification."""
        # Enable Pushover in config
        self.config.enable_pushover = True
        self.config.pushover_api_token = "test_token"
        self.config.pushover_user_key = "test_user"

        # Mock Pushover service
        mock_service = Mock()
        mock_service.send_2fa_notification.return_value = True
        mock_pushover_service_class.return_value = mock_service

        # Test
        self.handler._send_pushover_notification("http://localhost:8080")

        # Verify
        mock_service.send_2fa_notification.assert_called_once_with(
            "http://localhost:8080",
            "test@example.com"
        )

    @patch('src.icloud_photo_sync.auth.two_factor_handler.PushoverService')
    def test_send_success_notification(self, mock_pushover_service_class):
        """Test sending success notification."""
        # Enable Pushover in config
        self.config.enable_pushover = True
        self.config.pushover_api_token = "test_token"
        self.config.pushover_user_key = "test_user"

        # Mock Pushover service
        mock_service = Mock()
        mock_service.send_auth_success_notification.return_value = True
        mock_pushover_service_class.return_value = mock_service

        # Test
        self.handler._send_success_notification()

        # Verify
        mock_service.send_auth_success_notification.assert_called_once_with("test@example.com")

    def test_cleanup(self):
        """Test cleanup method."""
        # Mock web server
        mock_web_server = Mock()
        self.handler._web_server = mock_web_server

        # Test
        self.handler.cleanup()

        # Verify
        mock_web_server.stop.assert_called_once()
        assert self.handler._web_server is None


class TestHandleTwoFactorAuthenticationFunction:
    """Test the handle_2fa_authentication convenience function."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock config
        self.config = Mock(spec=BaseConfig)
        self.config.enable_pushover = False

    @patch('src.icloud_photo_sync.auth.two_factor_handler.TwoFactorAuthHandler')
    def test_handle_2fa_authentication_function(self, mock_handler_class):
        """Test the convenience function."""
        # Mock handler
        mock_handler = Mock()
        mock_handler.handle_2fa_authentication.return_value = "123456"
        mock_handler_class.return_value = mock_handler

        # Test
        result = handle_2fa_authentication(
            config=self.config,
        )

        # Verify
        assert result == "123456"
        mock_handler_class.assert_called_once_with(self.config)
        mock_handler.handle_2fa_authentication.assert_called_once_with(
            request_2fa_callback=None,
            validate_2fa_callback=None
        )
        mock_handler.cleanup.assert_called_once()
