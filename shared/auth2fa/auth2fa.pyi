"""
Type stubs for the auth2fa package.
"""

from collections.abc import Callable
from dataclasses import dataclass

@dataclass
class PushoverConfig:
    """Configuration for Pushover notifications."""
    api_token: str
    user_key: str
    device: str | None = None


@dataclass
class Auth2FAConfig:
    """Configuration for 2FA authentication."""
    pushover_config: PushoverConfig | None = None

    def get_pushover_config(self) -> PushoverConfig | None: ...


class TwoFactorAuthHandler:
    """Handles complete 2FA authentication flow including notifications and web interface."""

    def __init__(self, config: Auth2FAConfig | None = None) -> None: ...

    def handle_2fa_authentication(
        self,
        request_2fa_callback: Callable[[], bool] | None = None,
        validate_2fa_callback: Callable[[str], bool] | None = None
    ) -> str | None: ...

    def cleanup(self) -> None: ...

    @property
    def config(self) -> Auth2FAConfig | None: ...

    @property
    def port(self) -> int: ...


class TwoFAWebServer:
    """Web server for 2FA authentication interface."""

    def __init__(self, port_range: tuple[int, int] = (8080, 8090)) -> None: ...
    def start(self) -> bool: ...
    def stop(self) -> None: ...
    def get_url(self) -> str | None: ...
    def open_browser(self) -> bool: ...
    def wait_for_code(self, timeout: int = 300) -> str | None: ...
    def set_state(self, state: str, message: str = "") -> None: ...

    def set_callbacks(
        self,
        request_2fa_callback: Callable[[], bool] | None = None,
        submit_code_callback: Callable[[str], bool] | None = None
    ) -> None: ...

    @property
    def port(self) -> int: ...


class TwoFAHandler:
    """HTTP request handler for 2FA web interface."""
    ...


class PushoverService:
    """Service for sending Pushover notifications during 2FA authentication."""

    def __init__(self, config: PushoverConfig) -> None: ...
    def send_2fa_notification(self, web_url: str) -> bool: ...
    def send_auth_success_notification(self) -> bool: ...


def handle_2fa_authentication(
    config: Auth2FAConfig | None = None,
    request_2fa_callback: Callable[[], bool] | None = None,
    validate_2fa_callback: Callable[[str], bool] | None = None
) -> str | None: ...
