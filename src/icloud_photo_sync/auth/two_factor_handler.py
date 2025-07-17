"""Complete 2FA authentication handler with web server and Pushover notifications."""

import time
from typing import Optional, Callable

from ..config import BaseConfig
from ..logger import get_logger
from .web_server import TwoFAWebServer
from .pushover_service import PushoverService


class TwoFactorAuthHandler:
    """Handles complete 2FA authentication flow including notifications and web interface."""

    def __init__(self, config: BaseConfig):
        """Initialize the 2FA handler.

        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = get_logger()
        self._web_server: Optional[TwoFAWebServer] = None

    @property
    def port(self) -> int:
        """Get the port of the web server."""
        port = self._web_server.port if self._web_server else 0
        if not port:
            port = 0
        return port

    def handle_2fa_authentication(
        self,
        request_2fa_callback: Optional[Callable[[], bool]] = None,
        validate_2fa_callback: Optional[Callable[[str], bool]] = None
    ) -> Optional[str]:
        """Handle complete 2FA authentication flow.

        This is the main entry point for 2FA authentication. It:
        1. Sends a Pushover notification (if configured)
        2. Starts the web server
        3. Opens the browser
        4. Waits for user input
        5. Returns the 2FA code

        Args:
            request_2fa_callback: Optional callback to request new 2FA code from Apple
            validate_2fa_callback: Optional callback to validate 2FA code

        Returns:
            2FA code if successful, None if failed or timeout
        """
        try:
            self.logger.info("🔐 Starting 2FA authentication flow")

            # Initialize web server for 2FA
            self._web_server = TwoFAWebServer()

            # Set up callbacks
            self._web_server.set_callbacks(
                request_2fa_callback=request_2fa_callback,
                submit_code_callback=validate_2fa_callback
            )

            # Start web server
            if not self._web_server.start():
                self.logger.error("❌ Failed to start 2FA web server")
                return None

            web_url = self._web_server.get_url()
            if not web_url:
                self.logger.error("❌ Failed to get web server URL")
                return None

            self.logger.info(f"🌐 2FA web interface available at: {web_url}")

            # Send Pushover notification if configured
            self._send_pushover_notification(web_url)

            # Open browser automatically
            if self._web_server.open_browser():
                self.logger.info("🌐 Opened 2FA interface in browser")
            else:
                self.logger.warning("⚠️ Could not open browser automatically")
                self.logger.info(f"Please open: {web_url}")

            # Wait for 2FA code through web interface
            self._web_server.set_state('waiting_for_code')
            code = self._web_server.wait_for_code(timeout=300)  # 5 minute timeout

            if code:
                self.logger.info("📱 2FA code received via web interface")

                # If validation callback is provided, validate the code
                if validate_2fa_callback:
                    if validate_2fa_callback(code):
                        self._web_server.set_state(
                            'authenticated',
                            'Authentication successful! You can close this window.'
                        )

                        # Send success notification
                        self._send_success_notification()
                        return code
                    else:
                        self._web_server.set_state(
                            'failed',
                            'Invalid 2FA code. Please try again.'
                        )
                        return None
                else:
                    # No validation callback, just return the code
                    self._web_server.set_state(
                        'authenticated',
                        'Code received! You can close this window.'
                    )
                    return code
            else:
                self.logger.error("❌ Timeout waiting for 2FA code")
                self._web_server.set_state('failed', 'Timeout waiting for 2FA code')
                return None

        except Exception as e:
            self.logger.error(f"❌ Error during 2FA authentication: {e}")
            if self._web_server:
                self._web_server.set_state('failed', f'Error: {str(e)}')
            return None
        finally:
            # Clean up web server
            if self._web_server:
                # Give user a moment to see the final status
                time.sleep(2)
                self._web_server.stop()
                self._web_server = None

    def _send_pushover_notification(self, web_url: str) -> None:
        """Send Pushover notification if configured.

        Args:
            web_url: Web server URL for the notification
        """
        try:
            pushover_config = self.config.get_pushover_config()
            if not pushover_config:
                self.logger.debug("Pushover notifications not configured, skipping notification")
                return

            notification_service = PushoverService(pushover_config)

            if notification_service.send_2fa_notification(web_url):
                self.logger.info("📱 2FA notification sent via Pushover")
            else:
                self.logger.warning("⚠️ Failed to send 2FA notification via Pushover")

        except Exception as e:
            self.logger.error(f"❌ Error sending Pushover notification: {e}")

    def _send_success_notification(self) -> None:
        """Send success notification via Pushover if configured.
        """
        try:
            pushover_config = self.config.get_pushover_config()
            if not pushover_config:
                return

            notification_service = PushoverService(pushover_config)

            if notification_service.send_auth_success_notification():
                self.logger.info("📱 2FA success notification sent via Pushover")
            else:
                self.logger.warning("⚠️ Failed to send 2FA success notification via Pushover")

        except Exception as e:
            self.logger.error(f"❌ Error sending success notification: {e}")

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._web_server:
            self._web_server.stop()
            self._web_server = None


# Convenience function for external use
def handle_2fa_authentication(
    config: BaseConfig,
    request_2fa_callback: Optional[Callable[[], bool]] = None,
    validate_2fa_callback: Optional[Callable[[str], bool]] = None
) -> Optional[str]:
    """Handle complete 2FA authentication flow.

    This is the main entry point for 2FA authentication from outside the auth package.

    Args:
        config: Application configuration
        request_2fa_callback: Optional callback to request new 2FA code from Apple
        validate_2fa_callback: Optional callback to validate 2FA code

    Returns:
        2FA code if successful, None if failed or timeout
    """
    handler = TwoFactorAuthHandler(config)
    try:
        return handler.handle_2fa_authentication(
            request_2fa_callback=request_2fa_callback,
            validate_2fa_callback=validate_2fa_callback
        )
    finally:
        handler.cleanup()
