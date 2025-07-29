# Pushover Notification Setup

This guide shows how to configure Pushover notifications for 2FA authentication
alerts.

## Prerequisites

1. **Pushover Account**: Sign up at [pushover.net](https://pushover.net)
2. **Pushover App**: Install the Pushover app on your mobile device

## Configuration Steps

### 1. Get Your Pushover Credentials

1. **User Key**:
   - Go to [pushover.net](https://pushover.net)
   - Your user key is displayed on the main page after logging in

2. **API Token**:
   - Go to [pushover.net/apps/build](https://pushover.net/apps/build)
   - Create a new application (e.g., "iPhoto Downloader")
   - Copy the API Token/Key

### 2. Configure Environment Variables

Add the following to your `.env` file:

```bash
# Enable Pushover notifications
ENABLE_PUSHOVER=true

# Pushover API token from your app
PUSHOVER_API_TOKEN=your-api-token-here

# Your Pushover user key
PUSHOVER_USER_KEY=your-user-key-here

# Optional: Specific device name (leave empty for all devices)
PUSHOVER_DEVICE=
```

### 3. Test Your Configuration

Run the test script to verify your setup:

```bash
python test_pushover.py
```

This will send a test notification to verify your configuration is working.

## How It Works

When 2FA authentication is required:

1. **Notification Sent**: A Pushover notification is sent to your device
2. **Manual Entry**: You still need to manually enter the 2FA code in the
   terminal
3. **Success Notification**: A confirmation notification is sent when
   authentication succeeds

## Notification Content

### 2FA Required Notification

- **Title**: "iPhoto Downloader - 2FA Required"
- **Message**: Contains your iCloud username and instructions
- **Priority**: High (ensures immediate delivery)
- **URL**: Link to future web interface (placeholder for now)

### Success Notification

- **Title**: "iPhoto Downloader - Authentication Successful"
- **Message**: Confirms successful authentication
- **Priority**: Normal

## Troubleshooting

### Common Issues

1. **"Invalid token" error**:
   - Verify your `PUSHOVER_API_TOKEN` is correct
   - Ensure the token is from an active application

2. **"Invalid user" error**:
   - Verify your `PUSHOVER_USER_KEY` is correct
   - Check that your Pushover account is active

3. **Network timeout**:
   - Check your internet connection
   - Verify firewall settings allow HTTPS requests

### Testing

Use the test script to diagnose issues:

```bash
python test_pushover.py
```

The script will:

- ✅ Validate your configuration
- ✅ Test API connectivity
- ✅ Send a test notification
- ❌ Report specific errors if found

## Optional Configuration

### Device-Specific Notifications

To send notifications only to a specific device:

1. Find your device names in the Pushover app settings
2. Set the device name in your `.env` file:

```bash
PUSHOVER_DEVICE=iPhone
```

### Disable Notifications

To disable Pushover notifications:

```bash
ENABLE_PUSHOVER=false
```

## Future Enhancements

The current implementation sends notifications but still requires manual 2FA
code entry. Future versions will include:

- 🌐 **Local Web Server**: Browser-based 2FA code entry
- 📱 **Direct Links**: Click notification to open web interface
- ⚙️ **Advanced Settings**: Customizable notification priority and retry logic
