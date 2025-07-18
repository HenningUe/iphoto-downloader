#!/usr/bin/env python3
"""
Example usage of the auth2fa package with proper typing.
"""

from auth2fa import Auth2FAConfig, PushoverConfig, TwoFactorAuthHandler, handle_2fa_authentication


def main():
    """Demonstrate usage of Auth2FAConfig with proper typing."""

    # Create a Pushover configuration
    pushover_config = PushoverConfig(
        api_token="your_pushover_app_token",
        user_key="your_pushover_user_key",
        device="your_device_name"  # optional
    )

    # Create the auth2fa configuration
    auth_config = Auth2FAConfig(
        pushover_config=pushover_config
    )

    # Method 1: Use the handler directly
    print("=== Method 1: Direct handler usage ===")
    handler = TwoFactorAuthHandler(auth_config)
    print(f"Handler config type: {type(handler.config)}")
    print(f"Pushover config: {handler.config.get_pushover_config()}")

    # Method 2: Use the convenience function
    print("\n=== Method 2: Convenience function ===")

    def request_2fa_callback() -> bool:
        """Callback to request new 2FA code from Apple."""
        print("Requesting new 2FA code from Apple...")
        return True

    def validate_2fa_callback(code: str) -> bool:
        """Callback to validate 2FA code."""
        print(f"Validating 2FA code: {code}")
        # In real usage, this would validate with iCloud
        return len(code) == 6 and code.isdigit()

    # This would typically be called when 2FA is needed
    # code = handle_2fa_authentication(
    #     config=auth_config,
    #     request_2fa_callback=request_2fa_callback,
    #     validate_2fa_callback=validate_2fa_callback
    # )

    print("Auth2FA configuration is properly typed!")
    print(f"Config type: {type(auth_config)}")
    print(
        f"Available methods: {[method for method in dir(auth_config) if not method.startswith('_')]}")


if __name__ == "__main__":
    main()
