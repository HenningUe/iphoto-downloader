#!/usr/bin/env python3
"""Quick test runner for the TwoFactorAuthHandler manual tests."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def check_imports():
    """Check if all required modules can be imported."""
    try:
        from iphoto_downloader.config import KeyringConfig  # noqa
        from auth2fa.authenticator import TwoFactorAuthHandler  # noqa

        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def run_basic_test():
    """Run a basic test to verify the handler can be created."""
    try:
        from auth2fa.authenticator import Auth2FAConfig, TwoFactorAuthHandler

        config = Auth2FAConfig()
        TwoFactorAuthHandler(config)
        print("✅ TwoFactorAuthHandler created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating handler: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Testing TwoFactorAuthHandler setup...")

    if check_imports() and run_basic_test():
        print("\n✅ Ready to run manual tests!")
        print("Run: python tests/manuel/test_two_factor_handler_manual.py")
    else:
        print("\n❌ Setup issues detected")
        sys.exit(1)
