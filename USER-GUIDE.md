# 📖 iPhoto Downloader Tool - User Guide

Complete guide for installing, configuring, and using the iPhoto Downloader Tool.

## 📋 Table of Contents

1. [Installation](#-installation)
2. [Initial Setup & Configuration](#️-initial-setup--configuration)
3. [Credential Management](#-credential-management)
4. [Album Filtering Configuration](#-album-filtering-configuration)
5. [Database Configuration](#️-database-configuration)
6. [2FA Authentication Setup](#-2fa-authentication-setup)
7. [Running the Application](#-running-the-application)
8. [Advanced Configuration](#️-advanced-configuration)
9. [Troubleshooting](#-troubleshooting)
10. [FAQ](#-faq)

---

## 🚀 Installation

### Windows Installation

#### Option 1: Download Executable (Recommended)
1. Go to the [Releases page](https://github.com/HenningUe/iphoto-downloader/releases)
2. Download the latest `iphoto_downloader.zip` and extract it
3. Place both files in a dedicated folder (e.g., `C:\iPhotoDownloader\`)
4. Run `iphoto_downloader.exe` for the first time to set up configuration files
5. Run `iphoto_downloader_credentials.exe` to set your credentials

**⚠️ Windows Defender Warning**
If Windows Defender shows a security warning:
- Click "More info" → "Run anyway" (the files are safe)
- To permanently allow: Add the executable folder to Windows Defender exclusions
- See [Windows Defender Guide](docs/WINDOWS_DEFENDER_GUIDE.md) for detailed instructions

#### Option 2: Install via WinGet
NOT YET WORKING :-(
```powershell
winget install HenningUe.iPhotoDownloader
```

#### Option 3: From Source
```powershell
# Clone the repository
git clone https://github.com/HenningUe/iphoto-downloader.git
cd iphoto-downloader

# Build the executable
.\build_windows.ps1
```

### Linux Installation

#### Option 1: Download Executable (Recommended)
1. Go to the [Releases page](https://github.com/HenningUe/iphoto-downloader/releases)
2. Download the latest `iphoto_downloader.tar.gz` and extract it
3. Make them executable:
   ```bash
   chmod +x iphoto_downloader iphoto_downloader_credentials
   ```
4. Run `./iphoto_downloader` for the first time to set up configuration files
5. Run `./iphoto_downloader_credentials` to set your credentials

#### Option 2: Install via APT (Ubuntu/Debian)
```bash
# Add the repository
sudo add-apt-repository ppa:henningue/iphoto-downloader
sudo apt update

# Install the package
sudo apt install iphoto-downloader
```

#### Option 3: From Source
```bash
# Clone the repository
git clone https://github.com/HenningUe/iphoto-downloader.git
cd iphoto-downloader

# Build the executable
./build_linux.sh
```

---

## ⚙️ Initial Setup & Configuration

### First Run Setup

When you run the application for the first time, it will create a settings folder and copy configuration files:

**Windows**: `%USERPROFILE%\AppData\Local\iPhotoDownloader\`
**Linux**: `~/.local/share/iphoto-downloader/`

The following files will be created:
- `settings.ini` - Your configuration file (edit this)
- `settings.ini.template` - Template file (don't edit)
- `README.md` - Documentation

### Basic Configuration

1. Navigate to your settings folder
2. Open `settings.ini` in a text editor
3. Configure the essential settings:

```ini
# Essential Settings
SYNC_DIRECTORY=/path/to/your/photos
DRY_RUN=true
LOG_LEVEL=INFO

```

### Sync Directory Setup

Choose where your photos will be stored:

**Windows Examples:**
```ini
SYNC_DIRECTORY=C:\Users\YourName\Pictures\iCloudSync
# or
SYNC_DIRECTORY=D:\Photos\iCloud
```

**Linux Examples:**
```ini
SYNC_DIRECTORY=/home/username/Pictures/iCloudSync
# or
SYNC_DIRECTORY=/media/external/Photos/iCloud
```

**Important**: Use forward slashes (/) even on Windows for cross-platform compatibility.

---

## 🔑 Credential Management

The application supports two methods for storing credentials:

### Method 1: Secure Keyring Storage (Recommended)

Use the credential manager to store credentials securely in your system's credential store:

```bash
# Windows
iphoto_downloader_credentials.exe

# Linux
./iphoto_downloader_credentials
```

The credential manager will guide you through:
1. **iCloud Credentials**: Store your iCloud username and app-specific password
2. **Pushover Credentials**: Store Pushover API tokens for notifications
3. **Credential Verification**: Test stored credentials
4. **Credential Management**: View, update, or delete stored credentials

#### Creating iCloud App-Specific Password

1. Go to [Apple ID account page](https://appleid.apple.com/)
2. Sign in with your iCloud credentials
3. Navigate to "Security" → "App-Specific Passwords"
4. Generate a new password with label "iPhoto Downloader"
5. Use this password (not your regular iCloud password)

### Method 2: Environment Variables

Add credentials directly to your `settings.ini`:

```ini
# iCloud Credentials
ICLOUD_USERNAME=your.email@icloud.com
ICLOUD_PASSWORD=your-app-specific-password

# Pushover Notifications (Optional)
PUSHOVER_USER_KEY=your-pushover-user-key
PUSHOVER_API_TOKEN=your-pushover-api-token
```

**Security Note**: Keyring storage is more secure as credentials are encrypted by your operating system.

---

## 📁 Album Filtering Configuration

Control which albums are synced from your iCloud account:

### Basic Album Configuration

```ini
# Include personal albums (created by you)
INCLUDE_PERSONAL_ALBUMS=true

# Include shared albums (shared with you by others)
INCLUDE_SHARED_ALBUMS=true
```

### Album Allow-Lists

Specify exactly which albums to sync:

```ini
# Only sync specific personal albums
PERSONAL_ALBUM_NAMES_TO_INCLUDE=Family Photos,Vacation 2024,Work Events

# Only sync specific shared albums  
SHARED_ALBUM_NAMES_TO_INCLUDE=Shared Family,Trip Photos,Wedding Album
```

**Notes**:
- Leave allow-lists empty to include all albums of that type
- Album names are case-sensitive
- Use comma separation for multiple albums
- Photos from each album are stored in separate subfolders

### Album Folder Structure

Photos are organized by album:
```
📁 SYNC_DIRECTORY/
├── 📁 Family Photos/
│   ├── IMG_001.jpg
│   └── IMG_002.jpg
├── 📁 Vacation 2024/
│   ├── IMG_003.jpg
│   └── IMG_004.jpg
└── 📁 Shared Family/
    ├── IMG_005.jpg
    └── IMG_006.jpg
```

### Album Configuration Examples

**Sync everything:**
```ini
INCLUDE_PERSONAL_ALBUMS=true
INCLUDE_SHARED_ALBUMS=true
PERSONAL_ALBUM_NAMES_TO_INCLUDE=
SHARED_ALBUM_NAMES_TO_INCLUDE=
```

**Personal albums only:**
```ini
INCLUDE_PERSONAL_ALBUMS=true
INCLUDE_SHARED_ALBUMS=false
```

**Specific albums only:**
```ini
INCLUDE_PERSONAL_ALBUMS=true
INCLUDE_SHARED_ALBUMS=true
PERSONAL_ALBUM_NAMES_TO_INCLUDE=Family,Vacation
SHARED_ALBUM_NAMES_TO_INCLUDE=Wedding Photos
```

---

## 🗄️ Database Configuration

The application uses SQLite to track downloaded photos and prevent duplicates.

### Database Location Options

#### Option 1: Default Location (Recommended)
```ini
DATABASE_PARENT_DIRECTORY=.data
```
Creates: `SYNC_DIRECTORY/.data/deletion_tracker.db`

#### Option 2: Absolute Path
**Windows:**
```ini
DATABASE_PARENT_DIRECTORY=C:\Users\YourName\AppData\Local\iPhotoDownloader\Database
```

**Linux:**
```ini
DATABASE_PARENT_DIRECTORY=/home/username/.local/share/iphoto-downloader/database
```

#### Option 3: Environment Variables

**Windows:**
```ini
DATABASE_PARENT_DIRECTORY=%LOCALAPPDATA%\iPhotoDownloader\Database
```

**Linux:**
```ini
DATABASE_PARENT_DIRECTORY=$HOME/.local/share/iphoto-downloader/database
```

### Cross-Platform Environment Variables

The application automatically handles environment variable differences:

| Variable | Windows | Linux/macOS |
|----------|---------|-------------|
| `%LOCALAPPDATA%` | `C:\Users\User\AppData\Local` | `~/.local/share` |
| `%USERPROFILE%` | `C:\Users\User` | `~` |
| `%APPDATA%` | `C:\Users\User\AppData\Roaming` | `~/.config` |

### Database Safety Features

- **Automatic Backups**: Created before each sync
- **Corruption Recovery**: Automatic restore from backup if database is corrupted
- **Integrity Checks**: Regular database health checks in continuous mode

---

## 🔐 2FA Authentication Setup

The application provides a web-based interface for Two-Factor Authentication.

### Pushover Notifications Setup

For convenient 2FA notifications, set up Pushover:

1. **Create Pushover Account**: Go to [pushover.net](https://pushover.net)
2. **Get User Key**: Found on your dashboard
3. **Create Application**: Create a new application for "iPhoto Downloader"
4. **Get API Token**: Copy the API token for your application

**Configuration:**
```ini
PUSHOVER_USER_KEY=your-user-key-here
PUSHOVER_API_TOKEN=your-api-token-here
PUSHOVER_DEVICE=your-device-name  # Optional: specific device
```

### 2FA Web Interface

When 2FA is required:

1. **Notification**: You'll receive a Pushover notification (if configured)
2. **Web Interface**: A local web server starts at `http://localhost:5000`
3. **Authentication**: Enter your 2FA code in the web interface
4. **Session Storage**: Sessions are stored securely in your user directory

### 2FA Troubleshooting

**Port Conflicts**: The application automatically tries different ports if 5000 is occupied.

**Browser Issues**: The web interface is designed for modern browsers. If you experience issues:
- Try refreshing the page
- Check browser console for errors
- Ensure JavaScript is enabled

**Session Problems**: Clear old sessions using the credential manager:
```bash
iphoto_downloader_credentials
# Choose option 4: "iCloud - Delete 2FA sessions"
```

---

## 🏃 Running the Application

### Execution Modes

#### Single Execution Mode (Default)
Runs once and exits:
```ini
EXECUTION_MODE=single
```

```bash
# Windows
iphoto_downloader.exe

# Linux
./iphoto_downloader
```

#### Continuous Mode
Runs continuously with automatic intervals:
```ini
EXECUTION_MODE=continuous
SYNC_INTERVAL_MINUTES=30        # Wait 30 minutes between syncs
MAINTENANCE_INTERVAL_HOURS=1    # Database maintenance every hour
```

### Dry Run Mode

Test your configuration without downloading files:
```ini
DRY_RUN=true
```

This will show you what would be downloaded without actually downloading anything.

### Multi-Instance Control

Control whether multiple instances can run simultaneously:

```ini
# Default: Only one instance allowed
ALLOW_MULTI_INSTANCE=false

# Allow multiple instances (not recommended for shared databases)
ALLOW_MULTI_INSTANCE=true
```

### Command Line Usage

**Basic Sync:**
```bash
# Windows
iphoto_downloader.exe

# Linux  
./iphoto_downloader
```

**With Custom Config Location:**
```bash
# Place settings.ini in current directory
./iphoto_downloader
```

**Monitor Logs:**
Logs are written to:
- **Windows**: `%USERPROFILE%\AppData\Local\iPhotoDownloader\logs\`
- **Linux**: `~/.local/share/iphoto-downloader/logs/`

---

## ⚡ Advanced Configuration

### Performance Tuning

```ini
# Limit number of downloads per run
MAX_DOWNLOADS=100

# Skip large files (in MB, 0 = no limit)
MAX_FILE_SIZE_MB=50

# Logging verbosity
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR
```

### Network Configuration

```ini
# Timeout settings (if experiencing network issues)
REQUEST_TIMEOUT=30
MAX_RETRIES=3
```

### Operating Mode Configuration

```ini
# Development vs Production mode
# (automatically set to "Delivered" for executables)
OPERATING_MODE=InDevelopment
```

---

## 🔧 Troubleshooting

### Common Issues

#### Authentication Problems

**Symptom**: "Invalid credentials" error
**Solutions**:
1. Verify you're using an app-specific password, not your regular iCloud password
2. Check that 2FA is enabled on your iCloud account
3. Use the credential manager to verify stored credentials
4. Clear 2FA sessions and try again

#### Download Issues

**Symptom**: Photos not downloading
**Solutions**:
1. Check `DRY_RUN=false` in your configuration
2. Verify sync directory permissions
3. Check available disk space
4. Review logs for specific error messages

#### Database Issues

**Symptom**: "Database corrupted" or "Cannot open database"
**Solutions**:
1. The application will automatically restore from backup
2. If issues persist, delete the database to start fresh
3. Check database directory permissions

#### 2FA Web Interface Issues

**Symptom**: Cannot access web interface
**Solutions**:
1. Check if port 5000 is available
2. Try accessing `http://127.0.0.1:5000` instead
3. Check firewall settings
4. Review logs for port binding errors

### Log Analysis

**Log Locations**:
- **Windows**: `%USERPROFILE%\AppData\Local\iPhotoDownloader\logs\`
- **Linux**: `~/.local/share/iphoto-downloader/logs/`

**Important Log Files**:
- `iphoto_downloader.log` - Main application log
- `2fa_session.log` - 2FA authentication events
- `database.log` - Database operations and recovery

**Log Level Configuration**:
```ini
# More verbose logging for troubleshooting
LOG_LEVEL=DEBUG
```

### Performance Issues

**Symptom**: Slow sync or high memory usage
**Solutions**:
1. Reduce `MAX_DOWNLOADS` for smaller batches
2. Set `MAX_FILE_SIZE_MB` to skip very large files
3. Use continuous mode with longer intervals
4. Check available system resources

### Network Issues

**Symptom**: Connection timeouts or API errors
**Solutions**:
1. Check internet connection stability
2. Verify iCloud service status
3. Use continuous mode to retry automatically
4. Check if VPN affects iCloud connectivity

---

## ❓ FAQ

### General Questions

**Q: Is this application safe to use?**
A: Yes. The application only downloads photos and never deletes anything from your iCloud account. All operations are read-only on the iCloud side.

**Q: Will this duplicate photos I already have?**
A: No. The application tracks downloaded photos and skips files that already exist locally.

**Q: What happens if I delete a photo locally?**
A: The application remembers deleted photos and won't re-download them, respecting your local deletion decisions.

**Q: Can I sync multiple iCloud accounts?**
A: Yes, by using separate sync directories and configuration files, or by allowing multiple instances.

### Technical Questions

**Q: Where are my credentials stored?**
A: When using keyring storage, credentials are encrypted by your operating system's credential manager (Windows Credential Manager, macOS Keychain, or Linux Secret Service).

**Q: Can I run this on a server?**
A: Yes, but you'll need to handle 2FA authentication. Consider using continuous mode for automated syncing.

**Q: How much disk space do I need?**
A: This depends on your iCloud library size. The application shows download progress and you can set size limits.

**Q: Can I sync only new photos?**
A: Yes, the application only downloads photos that don't exist locally and haven't been previously deleted.

### Configuration Questions

**Q: How do I sync only specific albums?**
A: Use the album filtering configuration to specify exactly which personal and shared albums to include.

**Q: Can I change the sync directory after initial setup?**
A: Yes, but you'll need to either move existing photos or start fresh with a new database.

**Q: How do I backup my settings?**
A: Copy your `settings.ini` file and optionally the database file for a complete backup.

### Troubleshooting Questions

**Q: The 2FA web page won't open**
A: Check if another application is using port 5000, or access the interface directly at `http://localhost:5000`.

**Q: I'm getting "Another instance is running" error**
A: Set `ALLOW_MULTI_INSTANCE=true` in your configuration, or make sure no other instance is actually running.

**Q: Photos are downloading but to the wrong location**
A: Check your `SYNC_DIRECTORY` setting and ensure the path exists and is writable.

---

## 📞 Support

If you encounter issues not covered in this guide:

1. **Check the logs** in your application's log directory
2. **Search existing issues** on the [GitHub Issues page](https://github.com/HenningUe/iphoto-downloader/issues)
3. **Create a new issue** with:
   - Your operating system
   - Application version
   - Relevant log excerpts
   - Steps to reproduce the problem

---

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

*Last updated: July 29, 2025*
