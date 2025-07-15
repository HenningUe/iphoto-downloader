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
