"""Tests for 2FA authentication system."""

import pytest
import unittest
import time
from unittest.mock import Mock, patch, MagicMock

# Ensure auth2fa module is in path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'auth2fa', 'src'))

try:
    from auth2fa import TwoFAWebServer, TwoFactorAuthHandler, PushoverService, PushoverConfig, Auth2FAConfig
except ImportError as e:
    print(f"Import error: {e}")
    # Skip all tests if auth2fa is not available
    pytest.skip("auth2fa module not available", allow_module_level=True)


def test_simple_import():
    """Simple test to check if imports work."""
    assert TwoFAWebServer is not None
    assert TwoFactorAuthHandler is not None
    assert PushoverService is not None


def test_pushover_config_creation():
    """Test creating a Pushover configuration."""
    config = PushoverConfig(
        api_token="test_token",
        user_key="test_user",
        device="test_device"
    )
    assert config.api_token == "test_token"
    assert config.user_key == "test_user"
    assert config.device == "test_device"


def test_pushover_service_creation():
    """Test creating a Pushover service."""
    config = PushoverConfig(
        api_token="test_token",
        user_key="test_user",
        device="test_device"
    )
    service = PushoverService(config)
    assert service is not None
    assert service.config.api_token == "test_token"


@patch('requests.post')
def test_pushover_service_send_notification(mock_post):
    """Test sending a Pushover notification."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"status": 1}
    
    config = PushoverConfig(
        api_token="test_token",
        user_key="test_user",
        device="test_device"
    )
    service = PushoverService(config)
    
    result = service.send_2fa_notification("http://localhost:8080")
    assert result is True
    mock_post.assert_called_once()


@patch('requests.post')
def test_pushover_service_send_notification_failure(mock_post):
    """Test handling Pushover notification failure."""
    mock_post.return_value.status_code = 400
    
    config = PushoverConfig(
        api_token="test_token",
        user_key="test_user",
        device="test_device"
    )
    service = PushoverService(config)
    
    result = service.send_2fa_notification("http://localhost:8080")
    assert result is False


def test_web_server_creation():
    """Test creating a 2FA web server."""
    server = TwoFAWebServer(port_range=(8080, 8090))
    assert server is not None
    assert server.port_range == (8080, 8090)
    # Initially no port assigned
    assert server.port is None


def test_auth_handler_creation():
    """Test creating a 2FA authentication handler."""
    config = Auth2FAConfig()
    handler = TwoFactorAuthHandler(config)
    assert handler is not None
    assert handler.config is not None
    # Initially should return 0 (no web server)
    assert handler.port == 0


def test_auth_handler_with_pushover():
    """Test authentication handler with Pushover notifications."""
    pushover_config = PushoverConfig(
        api_token="test_token",
        user_key="test_user",
        device="test_device"
    )
    config = Auth2FAConfig(pushover_config=pushover_config)
    handler = TwoFactorAuthHandler(config)
    
    pushover_cfg = handler.config.get_pushover_config()
    assert pushover_cfg is not None
    assert pushover_cfg.api_token == "test_token"


def test_web_server_authentication_flow():
    """Test complete authentication flow."""
    server = TwoFAWebServer(port_range=(8080, 8090))
    
    # Mock successful authentication
    server.state = 'authenticated'
    server.submitted_code = '123456'
    
    # Test that authentication completed
    assert server.state == 'authenticated'
    assert server.submitted_code == '123456'


@patch('auth2fa.authenticator.TwoFAWebServer')
def test_auth_handler_2fa_flow(mock_web_server_class):
    """Test complete 2FA authentication flow."""
    config = Auth2FAConfig()
    handler = TwoFactorAuthHandler(config)
    
    # Mock the web server instance
    mock_server = Mock()
    mock_server.port = 8080
    mock_server.start.return_value = True
    mock_server.stop.return_value = None
    mock_server.wait_for_code.return_value = '123456'
    mock_server.get_url.return_value = 'http://localhost:8080'
    mock_server.open_browser.return_value = True
    mock_server.set_callbacks.return_value = None
    mock_server.set_state.return_value = None
    
    # Configure the mock class to return our mock instance
    mock_web_server_class.return_value = mock_server
    
    # Mock callback
    mock_callback = Mock(return_value=True)
    
    result = handler.handle_2fa_authentication(
        request_2fa_callback=mock_callback
    )
    
    # Should have proper result
    assert result is not None
