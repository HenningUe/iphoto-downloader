"""Complete 2FA authentication handler with web server and Pushover notifications."""

import time
import logging
from typing import Optional, Callable
from dataclasses import dataclass

from .web_server import TwoFAWebServer
from .pushover_service import PushoverService, PushoverConfig


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


@dataclass
class Auth2FAConfig:
    """Configuration for 2FA authentication."""
    pushover_config: Optional[PushoverConfig] = None

    def get_pushover_config(self) -> Optional[PushoverConfig]:
        """Get Pushover configuration if available."""
        return self.pushover_config


class TwoFactorAuthHandler:
    """Handles complete 2FA authentication flow including notifications and web interface."""

    def __init__(self, config: Auth2FAConfig):
        """Initialize the 2FA handler.

        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
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
            # Structured audit logging for 2FA session start
            self.logger.info("🔐 Starting 2FA authentication flow", extra={
                "event": "2fa_session_start",
                "session_id": id(self),
                "timestamp": time.time()
            })

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
                self.logger.info("🌐 Opened 2FA interface in browser", extra={
                    "event": "browser_opened",
                    "session_id": id(self),
                    "url": web_url
                })
            else:
                self.logger.warning("⚠️ Could not open browser automatically", extra={
                    "event": "browser_open_failed",
                    "session_id": id(self)
                })
                self.logger.info(f"Please open: {web_url}")

            # Wait for 2FA code through web interface
            self._web_server.set_state('waiting_for_code')
            self.logger.info("⏳ Waiting for 2FA code via web interface", extra={
                "event": "waiting_for_code",
                "session_id": id(self),
                "timeout_seconds": 300
            })
            code = self._web_server.wait_for_code(timeout=300)  # 5 minute timeout

            if code:
                self.logger.info("📱 2FA code received via web interface", extra={
                    "event": "2fa_code_received",
                    "session_id": id(self),
                    "code_length": len(code)
                })

                # If validation callback is provided, validate the code
                if validate_2fa_callback:
                    validation_result = validate_2fa_callback(code)
                    self.logger.info("🔍 2FA code validation attempt", extra={
                        "event": "2fa_code_validation",
                        "session_id": id(self),
                        "validation_result": validation_result
                    })
                    if validation_result:
                        self._web_server.set_state(
                            'authenticated',
                            'Authentication successful! You can close this window.'
                        )

                        # Send success notification
                        self._send_success_notification()
                        self.logger.info("✅ 2FA authentication successful", extra={
                            "event": "2fa_auth_success",
                            "session_id": id(self)
                        })
                        return code
                    else:
                        self._web_server.set_state(
                            'failed',
                            'Invalid 2FA code. Please try again.'
                        )
                        self.logger.warning("❌ 2FA authentication failed - invalid code", extra={
                            "event": "2fa_auth_failed",
                            "session_id": id(self),
                            "reason": "invalid_code"
                        })
                        return None
                else:
                    # No validation callback, just return the code
                    self._web_server.set_state(
                        'authenticated',
                        'Code received! You can close this window.'
                    )
                    self.logger.info("✅ 2FA code received (no validation)", extra={
                        "event": "2fa_code_received_no_validation",
                        "session_id": id(self)
                    })
                    return code
            else:
                self.logger.error("❌ Timeout waiting for 2FA code", extra={
                    "event": "2fa_timeout",
                    "session_id": id(self),
                    "timeout_seconds": 300
                })
                self._web_server.set_state('failed', 'Timeout waiting for 2FA code')
                return None

        except Exception as e:
            self.logger.error(f"❌ Error during 2FA authentication: {e}", extra={
                "event": "2fa_error",
                "session_id": id(self),
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
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
                self.logger.info("🔒 2FA session ended", extra={
                    "event": "2fa_session_end",
                    "session_id": id(self)
                })

    def _send_pushover_notification(self, web_url: str) -> None:
        """Send Pushover notification if configured.

        Args:
            web_url: Web server URL for the notification
        """
        if self.config is None:
            raise ValueError("Configuration is required to send notifications")
        try:
            pushover_config = self.config.get_pushover_config()
            if not pushover_config:
                self.logger.debug(
                    "Pushover notifications not configured, skipping notification",
                    extra={
                        "event": "pushover_notification_skipped",
                        "reason": "not_configured"
                    }
                )
                return

            notification_service = PushoverService(pushover_config)

            if notification_service.send_2fa_notification(web_url):
                self.logger.info("📱 2FA notification sent via Pushover", extra={
                    "event": "pushover_notification_sent",
                    "notification_type": "2fa_request"
                })
            else:
                self.logger.warning("⚠️ Failed to send 2FA notification via Pushover", extra={
                    "event": "pushover_notification_failed",
                    "notification_type": "2fa_request"
                })

        except Exception as e:
            self.logger.error(f"❌ Error sending Pushover notification: {e}", extra={
                "event": "pushover_notification_error",
                "notification_type": "2fa_request",
                "error_type": type(e).__name__,
                "error_message": str(e)
            })

    def _send_success_notification(self) -> None:
        """Send success notification via Pushover if configured.
        """
        if self.config is None:
            raise ValueError("Configuration is required to send notifications")
        try:
            pushover_config = self.config.get_pushover_config()
            if not pushover_config:
                return

            notification_service = PushoverService(pushover_config)

            if notification_service.send_auth_success_notification():
                self.logger.info("📱 2FA success notification sent via Pushover", extra={
                    "event": "pushover_notification_sent",
                    "notification_type": "2fa_success"
                })
            else:
                self.logger.warning(
                    "⚠️ Failed to send 2FA success notification via Pushover",
                    extra={
                        "event": "pushover_notification_failed",
                        "notification_type": "2fa_success"
                    }
                )

        except Exception as e:
            self.logger.error(f"❌ Error sending success notification: {e}", extra={
                "event": "pushover_notification_error",
                "notification_type": "2fa_success",
                "error_type": type(e).__name__,
                "error_message": str(e)
            })

    def cleanup(self) -> None:
        """Clean up resources."""
        if self._web_server:
            self._web_server.stop()
            self._web_server = None


# Convenience function for external use
def handle_2fa_authentication(
    config: Auth2FAConfig,
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
