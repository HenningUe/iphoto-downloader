#!/usr/bin/env python3
"""Utility script to manage iCloud credentials in keyring."""

import sys
import getpass
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from icloud_photo_sync.config import get_config, KEYRING_AVAILABLE, KeyringConfig


def main():
    """Main function for credential management."""
    if not KEYRING_AVAILABLE:
        print("❌ Keyring is not available. Please install it with: pip install keyring")
        sys.exit(1)
    
    print("🔑 iCloud Photo Sync - Credential Manager")
    print("=" * 45)
    
    # Use KeyringConfig directly for credential management
    config = KeyringConfig()
    
    while True:
        print("\nOptions:")
        print("1. Store credentials in keyring")
        print("2. Check stored credentials")
        print("3. Delete stored credentials")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            store_credentials(config)
        elif choice == "2":
            check_credentials()
        elif choice == "3":
            delete_credentials(config)
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")


def store_credentials(config: KeyringConfig):
    """Store credentials in keyring."""
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
    
    if config.store_credentials(username, password):
        print("✅ Credentials stored successfully in keyring!")
        print("💡 You can now remove ICLOUD_USERNAME and ICLOUD_PASSWORD from your .env file")
    else:
        print("❌ Failed to store credentials in keyring.")


def check_credentials():
    """Check stored credentials."""
    print("\n🔍 Check Stored Credentials")
    print("-" * 30)
    
    # Create a new config instance to test credential retrieval
    try:
        config = get_config()
        
        if isinstance(config, KeyringConfig) and config.has_stored_credentials():
            print("✅ Credentials are stored in keyring")
            if config.icloud_username and config.icloud_password:
                print(f"📧 Username: {config.icloud_username}")
                print("🔑 Password: *** (hidden)")
            else:
                print("⚠️ Credentials found in keyring but couldn't retrieve them")
        else:
            print("❌ No credentials found in keyring")
            
            # Check if credentials are in environment variables
            if config.icloud_username and config.icloud_password:
                print("💡 Credentials are available via environment variables")
            else:
                print("💡 No credentials found in environment variables either")
                
    except Exception as e:
        print(f"❌ Error checking credentials: {e}")


def delete_credentials(config: KeyringConfig):
    """Delete stored credentials."""
    print("\n🗑️ Delete Stored Credentials")
    print("-" * 30)
    
    if not config.has_stored_credentials():
        print("❌ No credentials found in keyring to delete.")
        return
    
    confirm = input("Are you sure you want to delete stored credentials? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Operation cancelled.")
        return
    
    if config.delete_credentials():
        print("✅ Credentials deleted successfully from keyring!")
    else:
        print("❌ Failed to delete credentials from keyring.")


if __name__ == "__main__":
    main()
