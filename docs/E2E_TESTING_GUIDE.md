# E2E Testing Guide with 2FA Support

This guide explains how to run end-to-end (E2E) integration tests for the iPhoto Downloader tool, including handling 2FA authentication.

## Prerequisites ✅

Before running E2E tests, ensure you have:

1. **Keyring package installed** (already done ✅)
2. **iCloud credentials stored** in keyring
3. **2FA-enabled iCloud account** (recommended for security)
4. **Access to your 2FA device** during testing

## Setting Up Credentials

If you haven't stored your credentials yet:

```powershell
python manage_credentials.py
```

This will prompt you for:
- Your iCloud email address
- Your app-specific password (not your regular iCloud password)

## Running E2E Tests

### 1. Basic Integration Tests (No 2FA)

Run basic tests that skip 2FA requirements:

```powershell
python run_e2e_tests.py
```

This runs:
- ✅ Configuration validation
- ✅ Credential loading from keyring
- ✅ Basic authentication (if 2FA not required)
- ⏭️ Skips slow photo listing tests
- ⏭️ Skips 2FA authentication tests

### 2. Authentication-Only Tests

Test only the authentication components:

```powershell
python run_e2e_tests.py --auth-only
```

### 3. Interactive Tests with 2FA

For accounts that require 2FA (most modern iCloud accounts):

```powershell
python run_e2e_tests.py --interactive
```

This will:
- ✅ Run all basic tests
- 🔐 Prompt for 2FA codes when needed
- 📱 Require you to check your Apple device
- ⏱️ May take longer due to manual input

### 4. Comprehensive Tests

Run all tests including slow photo listing:

```powershell
python run_e2e_tests.py --all
```

### 5. Dry-Run Only Tests

Test sync operations without actual downloads:

```powershell
python run_e2e_tests.py --dry-run
```

## Understanding 2FA in Testing

### What Happens During 2FA

1. **Initial Authentication**: Script attempts to log in with stored credentials
2. **2FA Challenge**: iCloud sends a code to your trusted device
3. **Code Entry**: You enter the 6-digit code when prompted
4. **Session Establishment**: Creates a trusted session for further API calls

### 2FA Testing Scenarios

#### Scenario 1: 2FA Not Required
- Account has trusted device sessions
- Authentication completes automatically
- All tests run without manual intervention

#### Scenario 2: 2FA Required
- Fresh authentication needed
- Manual code entry required
- Interactive mode necessary

### Managing 2FA for Testing

#### Option 1: Trusted Device Sessions
- Use a device that's already trusted
- 2FA may not be required for subsequent logins
- Best for automated testing

#### Option 2: App-Specific Passwords
- Generate app-specific passwords in iCloud settings
- May reduce 2FA requirements
- Recommended approach

#### Option 3: Test Account
- Use a dedicated test iCloud account
- Configure minimal 2FA requirements
- Separate from personal data

## Test Results and Interpretation

### Successful Authentication
```
✅ Initial authentication successful!
✅ No 2FA required - full authentication successful!
📊 Can now access iCloud Photos API
```

### 2FA Required
```
✅ Initial authentication successful!
🔐 2FA is required for this account
📱 You would need to enter a 2FA code to proceed
```

### Authentication Failed
```
❌ Authentication failed
💡 This could be due to:
   - Invalid credentials
   - Network issues
   - iCloud service issues
```

## Troubleshooting

### Common Issues

1. **"Authentication failed"**
   - Check stored credentials: `python manage_credentials.py` → option 2
   - Verify app-specific password is correct
   - Check network connectivity

2. **"2FA required but tests skip"**
   - Use `--interactive` flag
   - Ensure your 2FA device is available
   - Consider using trusted device session

3. **"Keyring not available"**
   - Keyring package should be installed ✅
   - Check Windows Credential Manager access

4. **"Tests hang during authentication"**
   - iCloud service may be slow
   - Network connectivity issues
   - Try again after a few minutes

### Environment Variables for Testing

You can override test behavior with environment variables:

```powershell
# Enable interactive tests without flag
$env:RUN_INTERACTIVE_TESTS = "1"

# Custom test settings
$env:SYNC_DIRECTORY = "C:\\temp\\test_photos"
$env:DRY_RUN = "true"
$env:MAX_DOWNLOADS = "3"
```

## Security Considerations

- ✅ **Credentials stored securely** in Windows Credential Manager
- ✅ **App-specific passwords** recommended over main password
- ✅ **Dry-run mode** prevents accidental downloads during testing
- ✅ **Limited downloads** during tests to avoid quota issues
- ⚠️ **2FA codes** are single-use and time-sensitive

## Next Steps

1. **Start with basic tests**: `python run_e2e_tests.py`
2. **Check if 2FA is needed**: Look for 2FA prompts in output
3. **Run interactive tests** if 2FA required: `python run_e2e_tests.py --interactive`
4. **Validate full sync**: `python run_e2e_tests.py --all` (when ready)

The E2E testing framework is now ready to validate your iPhoto Downloader integration with proper 2FA handling! 🚀
