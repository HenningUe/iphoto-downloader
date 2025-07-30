"""Authentication package for iPhoto Downloader.

This package contains all authentication-related components including:
- 2FA web server interface
- Pushover notification service
- Session management
- Authentication handlers
"""

from .authenticator import Auth2FAConfig, TwoFactorAuthHandler, handle_2fa_authentication
from .pushover_service import PushoverConfig, PushoverService
from .web_server import TwoFAHandler, TwoFAWebServer

__all__ = [
    "Auth2FAConfig",
    "PushoverConfig",
    "PushoverService",
    "TwoFAHandler",
    "TwoFAWebServer",
    "TwoFactorAuthHandler",
    "handle_2fa_authentication",
]
