"""Authentication package for iCloud Photo Sync.

This package contains all authentication-related components including:
- 2FA web server interface
- Pushover notification service
- Session management
- Authentication handlers
"""

from .web_server import TwoFAWebServer, TwoFAHandler
from .pushover_service import PushoverService, PushoverConfig
from .two_factor_handler import TwoFactorAuthHandler, handle_2fa_authentication

__all__ = [
    'TwoFAWebServer',
    'TwoFAHandler',
    'PushoverService',
    'PushoverConfig',
    'TwoFactorAuthHandler',
    'handle_2fa_authentication'
]
