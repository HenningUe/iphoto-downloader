# Manual Web Server Testing

This directory contains manual testing tools for the 2FA web server implementation.

## Files

- **`test_web_server_manual.py`** - Comprehensive manual testing functions
- **`run_web_server_tests.py`** - Interactive menu to run individual tests
- **`README.md`** - This documentation

## Quick Start

### Run All Tests
```bash
cd "c:\Users\henningue\Documents\Privat\vscode\foto-pool\foto-pool"
uv run python tests/manuel/test_web_server_manual.py
```

### Interactive Testing Menu
```bash
cd "c:\Users\henningue\Documents\Privat\vscode\foto-pool\foto-pool"
uv run python tests/manuel/run_web_server_tests.py
```

### Run Individual Test
```bash
cd "c:\Users\henningue\Documents\Privat\vscode\foto-pool\foto-pool"
uv run python -c "from tests.manuel.test_web_server_manual import test_basic_server_startup; print(test_basic_server_startup())"
```

## Available Tests

### 1. Basic Server Startup
- Tests server initialization and shutdown
- Verifies port binding and cleanup
- **Expected Result**: Server starts and stops cleanly

### 2. Port Conflict Handling
- Tests multiple servers to verify port conflict resolution
- Ensures servers bind to different ports when conflicts occur
- **Expected Result**: Multiple servers start on different ports

### 3. Server State Management
- Tests 2FA state transitions and callbacks
- Simulates code submission and new 2FA requests
- **Expected Result**: State changes are tracked correctly

### 4. Browser Integration
- Tests automatic browser opening functionality
- **Expected Result**: Browser opens to the correct URL
- **User Action**: Verify browser opens correctly

### 5. Web Interface Manual Test (Interactive)
- **🌐 INTERACTIVE TEST** - Opens browser for manual testing
- Tests the complete web interface functionality
- **Duration**: 60 seconds of interactive testing
- **User Actions Required**:
  1. Click "Request New 2FA Code" button
  2. Enter various 2FA codes (try 6-digit numbers)
  3. Test invalid codes (wrong length, non-numeric)
  4. Observe status updates and animations
  5. Verify interface responsiveness

## Test Features

Each test includes:
- ✅ **Automatic Setup**: Proper logging and server initialization
- 🔧 **Error Handling**: Graceful cleanup on failures
- 📊 **Progress Reporting**: Real-time status updates
- 🤔 **User Feedback**: Interactive verification where needed

## Manual Web Interface Testing Guide

When running the interactive web interface test:

### What to Test:
1. **Visual Appearance**
   - Modern, clean interface
   - Responsive design
   - Proper styling and animations

2. **Functionality**
   - "Request New 2FA Code" button works
   - 2FA code input field accepts input
   - Form validation (6-digit numbers only)
   - Status updates in real-time

3. **Error Handling**
   - Invalid code formats are rejected
   - Clear error messages displayed
   - Graceful handling of network issues

4. **User Experience**
   - Auto-refresh functionality works
   - Progress indicators are visible
   - Interface is intuitive and user-friendly

### Expected Behavior:
- Server starts on `http://localhost:8080` (or next available port)
- Browser opens automatically to the web interface
- Status updates appear in real-time
- Code submissions trigger callbacks
- Interface provides immediate feedback

## Troubleshooting

### Common Issues:

1. **"Logging has not been set up" Error**
   - Each test now includes proper logging setup
   - Should be automatically resolved

2. **Port Already in Use**
   - Tests automatically find available ports
   - Multiple servers will use different ports

3. **Browser Doesn't Open**
   - Manually navigate to the displayed URL
   - Usually `http://localhost:8080`

4. **Network Permission Issues**
   - Ensure Windows Firewall allows local connections
   - Server only binds to localhost for security

### Getting Help:
If tests fail or behave unexpectedly:
1. Check the console output for error messages
2. Verify no other services are using ports 8080-8090
3. Ensure you have proper permissions to bind to network ports
4. Try running tests individually to isolate issues

## Integration with Main Project

These manual tests complement the automated unit tests in:
- `tests/unit/test_web_server.py` - Automated unit tests
- `tests/integration/` - Integration tests

The manual tests focus on:
- User interface validation
- Browser integration
- Real-world user experience
- Visual and interactive elements not covered by unit tests

# Manual Testing for TwoFactorAuthHandler

This directory contains comprehensive manual tests for the `TwoFactorAuthHandler` class.

## Test Files

### `test_two_factor_handler_manual.py`
Complete manual test suite for the TwoFactorAuthHandler including:

- **Complete 2FA Flow**: Full authentication flow with web server and notifications
- **Pushover Integration**: Test notification sending and configuration
- **Web Server Integration**: Test web interface without full flow
- **Timeout Behavior**: Test timeout handling (10-second test)
- **Convenience Function**: Test the external convenience function
- **Error Handling**: Test error scenarios and exception handling

### `run_two_factor_handler_tests.py`
Quick setup verification script to check if all dependencies are available.

## Usage

### Run All Tests
```bash
python tests/manuel/test_two_factor_handler_manual.py
```

### Interactive Mode
```bash
python tests/manuel/test_two_factor_handler_manual.py --interactive
```

### Check Setup
```bash
python tests/manuel/run_two_factor_handler_tests.py
```

## Test Requirements

### Configuration
- Valid `.env` file with iCloud credentials
- Optional: Pushover configuration for notification tests

### Dependencies
- Web server components (`TwoFAWebServer`)
- Pushover service (`PushoverService`)
- Configuration system (`KeyringConfig`)

### Browser
- Tests will automatically open your default browser
- Requires manual interaction for testing web interface

## Test Coverage

### ✅ What's Tested
- Complete 2FA authentication flow
- Web server startup and browser integration
- Pushover notification sending
- Timeout behavior and error handling
- Callback system functionality
- State management and cleanup

### 🔄 Manual Verification Required
- Web interface usability and responsiveness
- Notification reception on mobile devices
- Browser compatibility
- User experience flow

## Expected Behavior

### Successful Test Run
- Web server starts on available port
- Browser opens automatically to 2FA interface
- Pushover notifications sent (if configured)
- Proper cleanup after timeout or completion
- All callbacks executed correctly

### Common Issues
- **Port conflicts**: Tests handle automatic port selection
- **Browser not opening**: Manual URL provided as fallback
- **Pushover not configured**: Tests skip notification gracefully
- **Timeout**: 5-minute timeout for full flow, shorter for specific tests

## Interactive Testing

The interactive mode allows you to:
1. Run individual test components
2. Repeat tests multiple times
3. Focus on specific functionality
4. Debug issues in isolation

Select from:
- `1` - Complete 2FA Flow
- `2` - Pushover Integration
- `3` - Web Server Integration
- `4` - Timeout Behavior
- `5` - Convenience Function
- `6` - Error Handling
- `a` - All Tests
- `q` - Quit

## Integration with Main Application

These tests verify the components that will be used in the main iCloud Photo Sync application:

```python
from icloud_photo_sync.auth.two_factor_handler import handle_2fa_authentication

# In your iCloud client code
def authenticate_with_2fa(username):
    return handle_2fa_authentication(
        config=config,
        username=username,
        request_2fa_callback=lambda: request_new_2fa_from_apple(),
        validate_2fa_callback=lambda code: validate_code_with_apple(code)
    )
```

## Troubleshooting

### Test Failures
1. Check import paths and dependencies
2. Verify configuration files exist
3. Ensure no other processes are using test ports
4. Check browser permissions and default browser settings

### Notification Issues
1. Verify Pushover credentials in `.env`
2. Test with `python test_pushover.py` first
3. Check device connectivity and app installation
4. Verify API token permissions

### Web Server Issues
1. Check firewall settings
2. Verify port availability (8080-8090 range)
3. Test browser compatibility
4. Check for JavaScript errors in browser console

---

*These manual tests are designed to verify the complete 2FA authentication system works correctly in real-world conditions with actual user interaction.*
