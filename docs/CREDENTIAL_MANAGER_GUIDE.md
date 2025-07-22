# Credential Manager Usage Guide

The `manage_credentials.py` script has been fixed to properly handle the KeyringConfig initialization issue.

## Problem Fixed

**Before:** The script was calling `config = KeyringConfig()` directly, which triggered validation that required credentials to already exist.

**After:** The script now uses a `create_keyring_helper()` function that temporarily sets environment variables to bypass validation, allowing the KeyringConfig to be created for credential management operations.

## How to Use

Run the credential manager:
```powershell
python manage_credentials.py
```

This will show you a menu with options:
1. Store credentials in keyring
2. Check stored credentials  
3. Delete stored credentials
4. Exit

## How the Fix Works

The `create_keyring_helper()` function:
1. Saves any existing `ICLOUD_USERNAME` and `ICLOUD_PASSWORD` environment variables
2. Sets temporary values (`'temp'`) to satisfy the KeyringConfig validation
3. Creates the KeyringConfig instance successfully
4. Restores the original environment variables
5. Returns the working KeyringConfig instance for credential operations

This allows you to use the credential manager even when no credentials exist yet, which was the original problem.

## Security Notes

- Credentials are stored securely in your system's keyring (Windows Credential Manager, macOS Keychain, etc.)
- The temporary environment variables are immediately restored
- No actual credentials are exposed during the helper creation process

## Example Usage

1. **Store credentials**: Enter your iCloud email and app-specific password
2. **Check credentials**: Verify if credentials are stored and accessible
3. **Delete credentials**: Remove stored credentials from keyring

After storing credentials in keyring, you can remove `ICLOUD_USERNAME` and `ICLOUD_PASSWORD` from your `.env` file for better security.
