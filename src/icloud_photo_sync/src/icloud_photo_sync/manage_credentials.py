#!/usr/bin/env python3
"""Utility script to manage iCloud credentials in keyring."""

import getpass

from icloud_photo_sync.config import get_config, KeyringConfig


def main():
    """Main function for credential management."""

    print("🔑 iCloud Photo Sync - Credential Manager")
    print("=" * 45)

    while True:
        print("\nOptions:")
        print("1. iCloud - Store credentials in keyring")
        print("2. iCloud - Check stored credentials")
        print("3. iCloud - Delete stored credentials")
        print("4. Pushover - Store credentials in keyring")
        print("5. Pushover - Check stored credentials")
        print("6. Pushover - Delete stored credentials")
        print("7. Exit")

        choice = input("\nEnter your choice (1-7): ").strip()

        if choice == "1":
            icloud_store_credentials()
        elif choice == "2":
            icloud_check_credentials()
        elif choice == "3":
            icloud_delete_credentials()
        elif choice == "4":
            pushover_store_credentials()
        elif choice == "5":
            pushover_check_credentials()
        elif choice == "6":
            pushover_delete_credentials()
        elif choice == "7":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")


def icloud_store_credentials():
    """Store iCloud credentials in keyring."""
    print("\n🔐 Store iCloud Credentials")
    print("-" * 30)

    username = input("Enter your iCloud username (email): ").strip()
    if not username:
        print("❌ Username cannot be empty.")
        return

    password = getpass.getpass("Enter your iCloud app-specific password: ").strip()
    if not password:
        print("❌ Password cannot be empty.")
        return

    print("\n⏳ Storing credentials in keyring...")

    config = _create_temp_config()
    if config.icloud_store_credentials(username, password):
        print("✅ iCloud Credentials stored successfully in keyring!")
    else:
        print("❌ Failed to store iCloud credentials in keyring.")


def icloud_check_credentials():
    """Check iCloud stored credentials."""
    print("\n🔍 Check Stored iCloud Credentials")
    print("-" * 30)

    # Create a new config instance to test credential retrieval
    try:
        config = get_config()

        if isinstance(config, KeyringConfig) and config.icloud_has_stored_credentials():
            print("✅ iCloud Credentials are stored in keyring")
            if config.icloud_username and config.icloud_password:
                print(f"📧 Username: {config.icloud_username}")
                print("🔑 Password: *** (hidden)")
            else:
                print("⚠️ Credentials found in keyring but couldn't retrieve them")
        else:
            print("❌ No credentials found in keyring")

    except Exception as e:
        print(f"❌ Error checking credentials: {e}")


def icloud_delete_credentials():
    """Delete iCloud stored credentials."""
    print("\n🗑️ Delete iCloud Stored Credentials")
    print("-" * 30)

    config = _create_temp_config()
    if not config.icloud_has_stored_credentials():
        print("❌ No credentials found in keyring to delete.")
        return

    confirm = input("Are you sure you want to delete stored credentials? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Operation cancelled.")
        return

    if config.icloud_delete_credentials():
        print("✅ Credentials deleted successfully from keyring!")
    else:
        print("❌ Failed to delete credentials from keyring.")


def pushover_store_credentials():
    """Store pushover credentials in keyring."""
    print("\n🔐 Store Pushover Credentials")
    print("-" * 30)

    user_key = input("Enter your pushover user-key: ").strip()
    if not user_key:
        print("❌ User-key cannot be empty.")
        return

    api_token = getpass.getpass("Enter your pushover API token: ").strip()
    if not api_token:
        print("❌ API token cannot be empty.")
        return

    print("\n⏳ Storing credentials in keyring...")

    config = _create_temp_config()
    if config.pushover_store_credentials(user_key, api_token):
        print("✅ Pushover Credentials stored successfully in keyring!")
    else:
        print("❌ Failed to store Pushover credentials in keyring.")


def pushover_check_credentials():
    """Check Pushover stored credentials."""
    print("\n🔍 Check Stored Pushover Credentials")
    print("-" * 30)

    # Create a new config instance to test credential retrieval
    try:
        config = get_config()

        if isinstance(config, KeyringConfig) and config.pushover_has_stored_credentials():
            print("✅ Pushover Credentials are stored in keyring")
            if config.pushover_user_key and config.pushover_api_token:
                print(f"📧 User Key: {config.pushover_user_key}")
                print(f"🔑 API Token: {config.pushover_api_token}")
            else:
                print("⚠️ Credentials found in keyring but couldn't retrieve them")
        else:
            print("❌ No credentials found in keyring")

    except Exception as e:
        print(f"❌ Error checking credentials: {e}")


def pushover_delete_credentials():
    """Delete Pushover stored credentials."""
    print("\n🗑️ Delete Pushover Stored Credentials")
    print("-" * 30)

    config = _create_temp_config()
    if not config.pushover_has_stored_credentials():
        print("❌ No credentials found in keyring to delete.")
        return

    confirm = input("Are you sure you want to delete stored credentials? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Operation cancelled.")
        return

    if config.pushover_delete_credentials():
        print("✅ Pushover Credentials deleted successfully from keyring!")
    else:
        print("❌ Failed to delete Pushover credentials from keyring.")


def _create_temp_config():
    """Create a KeyringConfig instance that can be used for credential management."""
    # Create a temporary KeyringConfig without validation by temporarily setting env vars
    import os
    temp_username = os.environ.get('PUSHOVER_DEVICE')
    temp_password = os.environ.get('ENABLE_PUSHOVER')

    os.environ['PUSHOVER_DEVICE'] = 'temp'
    os.environ['ENABLE_PUSHOVER'] = 'true'

    try:
        config = KeyringConfig()
        return config
    finally:
        # Restore original environment
        if temp_username is None:
            os.environ.pop('PUSHOVER_DEVICE', None)
        else:
            os.environ['PUSHOVER_DEVICE'] = temp_username

        if temp_password is None:
            os.environ.pop('ENABLE_PUSHOVER', None)
        else:
            os.environ['ENABLE_PUSHOVER'] = temp_password


if __name__ == "__main__":
    main()
