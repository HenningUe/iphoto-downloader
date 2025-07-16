"""Unit tests for Pushover notification service."""

import pytest
import json
from unittest.mock import Mock, patch
from requests.exceptions import RequestException, Timeout

from src.icloud_photo_sync.auth.pushover_service import (
    PushoverConfig,
    PushoverService as PushoverNotificationService
)


class TestPushoverConfig:
    """Test PushoverConfig class."""

    def test_valid_config(self):
        """Test creating a valid Pushover configuration."""
        config = PushoverConfig(
            api_token="test_token",
            user_key="test_user"
        )
        assert config.api_token == "test_token"
        assert config.user_key == "test_user"
        assert config.device is None

    def test_config_with_device(self):
        """Test creating a Pushover configuration with device."""
        config = PushoverConfig(
            api_token="test_token",
            user_key="test_user",
            device="test_device"
        )
        assert config.device == "test_device"

    def test_empty_api_token(self):
        """Test that empty API token raises ValueError."""
        with pytest.raises(ValueError, match="Pushover API token is required"):
            PushoverConfig(api_token="", user_key="test_user")

    def test_empty_user_key(self):
        """Test that empty user key raises ValueError."""
        with pytest.raises(ValueError, match="Pushover user key is required"):
            PushoverConfig(api_token="test_token", user_key="")


class TestPushoverNotificationService:
    """Test PushoverNotificationService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = PushoverConfig(
            api_token="test_token",
            user_key="test_user",
            device="test_device"
        )
        self.service = PushoverNotificationService(self.config)

    @patch('src.icloud_photo_sync.auth.pushover_service.requests.post')
    def test_send_2fa_notification_success(self, mock_post):
        """Test successful 2FA notification."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 1}
        mock_post.return_value = mock_response

        result = self.service.send_2fa_notification(
            web_server_url="http://localhost:8080",
            username="test@example.com"
        )

        assert result is True
        mock_post.assert_called_once()

        # Check the payload
        call_args = mock_post.call_args
        payload = call_args[1]['data']
        assert payload['token'] == "test_token"
        assert payload['user'] == "test_user"
        assert payload['device'] == "test_device"
        assert payload['priority'] == 1
        assert "test@example.com" in payload['message']
        assert "http://localhost:8080" in payload['message']
        assert payload['url'] == "http://localhost:8080"

    @patch('src.icloud_photo_sync.auth.pushover_service.requests.post')
    def test_send_2fa_notification_api_error(self, mock_post):
        """Test 2FA notification with API error."""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": 0,
            "errors": ["invalid token"]
        }
        mock_post.return_value = mock_response

        result = self.service.send_2fa_notification(
            web_server_url="http://localhost:8080",
            username="test@example.com"
        )

        assert result is False

    @patch('src.icloud_photo_sync.auth.pushover_service.requests.post')
    def test_send_2fa_notification_http_error(self, mock_post):
        """Test 2FA notification with HTTP error."""
        # Mock HTTP error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        result = self.service.send_2fa_notification(
            web_server_url="http://localhost:8080",
            username="test@example.com"
        )

        assert result is False

    @patch('src.icloud_photo_sync.auth.pushover_service.requests.post')
    def test_send_2fa_notification_network_error(self, mock_post):
        """Test 2FA notification with network error."""
        # Mock network error
        mock_post.side_effect = RequestException("Network error")

        result = self.service.send_2fa_notification(
            web_server_url="http://localhost:8080",
            username="test@example.com"
        )

        assert result is False

    @patch('src.icloud_photo_sync.auth.pushover_service.requests.post')
    def test_send_auth_success_notification(self, mock_post):
        """Test successful authentication notification."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 1}
        mock_post.return_value = mock_response

        result = self.service.send_auth_success_notification("test@example.com")

        assert result is True
        mock_post.assert_called_once()

        # Check the payload
        call_args = mock_post.call_args
        payload = call_args[1]['data']
        assert payload['priority'] == 0  # Normal priority for success
        assert "successful" in payload['message'].lower()

    @patch('src.icloud_photo_sync.auth.pushover_service.requests.post')
    def test_test_connection_success(self, mock_post):
        """Test connection test success."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 1}
        mock_post.return_value = mock_response

        result = self.service.test_connection()

        assert result is True
        mock_post.assert_called_once()

        # Check the payload
        call_args = mock_post.call_args
        payload = call_args[1]['data']
        assert "test" in payload['title'].lower()
        assert "test" in payload['message'].lower()

    def test_service_without_device(self):
        """Test service without device specified."""
        config_no_device = PushoverConfig(
            api_token="test_token",
            user_key="test_user"
        )
        service = PushoverNotificationService(config_no_device)

        with patch('src.icloud_photo_sync.auth.pushover_service.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": 1}
            mock_post.return_value = mock_response

            service.send_2fa_notification("http://localhost:8080", "test@example.com")

            # Check that device is not in payload
            call_args = mock_post.call_args
            payload = call_args[1]['data']
            assert 'device' not in payload

    @patch('src.icloud_photo_sync.auth.pushover_service.requests.post')
    def test_timeout_handling(self, mock_post):
        """Test timeout handling."""
        mock_post.side_effect = Timeout("Request timeout")

        result = self.service.send_2fa_notification(
            web_server_url="http://localhost:8080",
            username="test@example.com"
        )

        assert result is False

    @patch('src.icloud_photo_sync.auth.pushover_service.requests.post')
    def test_unexpected_error_handling(self, mock_post):
        """Test unexpected error handling."""
        mock_post.side_effect = Exception("Unexpected error")

        result = self.service.send_2fa_notification(
            web_server_url="http://localhost:8080",
            username="test@example.com"
        )

        assert result is False
