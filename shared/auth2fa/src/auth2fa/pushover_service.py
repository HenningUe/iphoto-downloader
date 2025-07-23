"""
Pushover notification service for 2FA authentication notifications.
"""

import requests
import logging
from typing import Optional
from dataclasses import dataclass


logger = logging.getLogger(__name__)


PUSOVER_PRIORITY = {
    "low": -1,
    "normal": 0,
    "high": 1,
    "emergency": 2
}


@dataclass
class PushoverConfig:
    """Configuration for Pushover notifications."""
    api_token: str
    user_key: str
    device: Optional[str] = None

    def __post_init__(self):
        if not self.api_token:
            raise ValueError("Pushover API token is required")
        if not self.user_key:
            raise ValueError("Pushover user key is required")


class PushoverService:
    """Service for sending Pushover notifications during 2FA authentication."""

    PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"

    def __init__(self, config: PushoverConfig):
        """
        Initialize the Pushover notification service.

        Args:
            config: Pushover configuration with API token and user key
        """
        self.config = config

    def send_2fa_notification(self, web_server_url: str) -> bool:
        """
        Send a 2FA notification to the user with a link to the web interface.

        Args:
            web_server_url: URL of the local web server for 2FA code entry

        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            title = "iCloud Photo Sync - 2FA Required"
            message = (
                f"2FA authentication required.\n\n"
                f"Click the link below to enter your 2FA code:\n"
                f"{web_server_url}"
            )

            payload = {
                "token": self.config.api_token,
                "user": self.config.user_key,
                "title": title,
                "message": message,
                "priority": PUSOVER_PRIORITY["high"],
                "url": web_server_url,
                "url_title": "Enter 2FA Code"
            }

            # Add device if specified
            if self.config.device:
                payload["device"] = self.config.device

            logger.info("Sending 2FA notification via Pushover")

            response = requests.post(
                self.PUSHOVER_API_URL,
                data=payload,
                timeout=10
            )

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("status") == 1:
                    logger.info("2FA notification sent successfully via Pushover")
                    return True
                else:
                    logger.error(
                        f"Pushover API error: {response_data.get('errors', 'Unknown error')}")
                    return False
            else:
                logger.error(
                    f"Pushover API request failed with status {response.status_code}: "
                    f"{response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending Pushover notification: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Pushover notification: {e}")
            return False

    def send_auth_success_notification(self) -> bool:
        """
        Send a notification when 2FA authentication is successful.

        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            title = "iCloud Photo Sync - Authentication Successful"
            message = ("2FA authentication completed successfully. "
                       "Photo sync will continue.")

            payload = {
                "token": self.config.api_token,
                "user": self.config.user_key,
                "title": title,
                "message": message,
                "priority": PUSOVER_PRIORITY["low"],
            }

            if self.config.device:
                payload["device"] = self.config.device

            logger.info("Sending authentication success notification.")

            response = requests.post(
                self.PUSHOVER_API_URL,
                data=payload,
                timeout=10
            )

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("status") == 1:
                    logger.info("Authentication success notification sent via Pushover")
                    return True
                else:
                    logger.error(
                        f"Pushover API error: {response_data.get('errors', 'Unknown error')}")
                    return False
            else:
                logger.error(
                    f"Pushover API request failed with status {response.status_code}: "
                    f"{response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending Pushover notification: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Pushover notification: {e}")
            return False

    def test_connection(self) -> bool:
        """
        Test the Pushover configuration by sending a test notification.

        Returns:
            True if test notification was sent successfully, False otherwise
        """
        try:
            title = "iCloud Photo Sync - Test Notification"
            message = "This is a test notification to verify your Pushover configuration."

            payload = {
                "token": self.config.api_token,
                "user": self.config.user_key,
                "title": title,
                "message": message,
                "priority": 0
            }

            if self.config.device:
                payload["device"] = self.config.device

            logger.info("Sending test notification via Pushover")

            response = requests.post(
                self.PUSHOVER_API_URL,
                data=payload,
                timeout=10
            )

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("status") == 1:
                    logger.info("Test notification sent successfully via Pushover")
                    return True
                else:
                    logger.error(
                        f"Pushover API error: {response_data.get('errors', 'Unknown error')}")
                    return False
            else:
                logger.error(
                    f"Pushover API request failed with status {response.status_code}: "
                    f"{response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending test notification: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending test notification: {e}")
            return False


# Legacy alias for backward compatibility
PushoverNotificationService = PushoverService
