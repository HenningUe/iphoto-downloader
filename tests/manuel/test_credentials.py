#!/usr/bin/env python3
"""Test script for credential manager functionality."""

from icloud_photo_sync.config import KEYRING_AVAILABLE, KeyringConfig
import sys
import os
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_keyring_helper():
    """Test the keyring helper function."""
    print("Testing keyring helper...")

    # Save original environment
    temp_username = os.environ.get('ICLOUD_USERNAME')
    temp_password = os.environ.get('ICLOUD_PASSWORD')

    # Set temporary values to avoid validation errors
    os.environ['ICLOUD_USERNAME'] = 'temp'
    os.environ['ICLOUD_PASSWORD'] = 'temp'

    try:
        config = KeyringConfig()
        print("✅ KeyringConfig created successfully!")

        # Test if methods exist
        has_creds = config.icloud_has_stored_credentials()
        print(f"✅ has_stored_credentials() method works: {has_creds}")

        return config
    except Exception as e:
        print(f"❌ Error creating KeyringConfig: {e}")
        return None
    finally:
        # Restore original environment
        if temp_username is None:
            os.environ.pop('ICLOUD_USERNAME', None)
        else:
            os.environ['ICLOUD_USERNAME'] = temp_username

        if temp_password is None:
            os.environ.pop('ICLOUD_PASSWORD', None)
        else:
            os.environ['ICLOUD_PASSWORD'] = temp_password


if __name__ == "__main__":
    print(f"KEYRING_AVAILABLE: {KEYRING_AVAILABLE}")

    if KEYRING_AVAILABLE:
        config = test_keyring_helper()
        if config:
            print("✅ Credential manager helper approach works!")
        else:
            print("❌ Credential manager helper approach failed!")
    else:
        print("❌ Keyring not available!")
