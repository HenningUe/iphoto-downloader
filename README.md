# 📸 iPhoto Downloader Workspace

A uv monorepo workspace for iCloud photo download tools and utilities.

## ✨ Features

- **🔄 Smart Sync**: Only downloads new photos that don't exist locally
- **🛡️ Deletion Protection**: Tracks locally deleted photos to prevent
  re-downloading
- **☁️ iCloud Safe**: Never deletes photos from your iCloud account
- **🎯 Idempotent**: Safe to run multiple times without duplicates
- **🖥️ Cross-Platform**: Works on Windows and Linux
- **📊 Logging**: Detailed console and file logging
- **🔧 Configurable**: Customizable sync directory and settings. Allow- and blocklists for albums.
- **🏗️ Shared Albums**: Support of shared and personal albums.
- **🔐 2FA Support**: Integrated two-factor authentication for iCloud. Comfortable Web-UI to enter 2FA code (for server operation)

## 🏗️ Why another tool?
- Apple's notorious icloud windows app downloads fotos only with weird names
- pycloud downloader  s missing some features that I miss.
   - missing possibility to easily download shared albums
   - missing notification via pushover for new 2FA requests
   - missing configuration via setting-file
   - missing continuous execution mode

## **How to use?**
**see [User Guide](./USER-GUIDE.md)**

## **Releases**
**see [Releases](https://github.com/HenningUe/iphoto-downloader/releases/)**

## ✨ On my personal behalf
I honor democracy, which
- Is being ruled by a head of state who has been in power for a maximum of 20 years
- Whose elected heads of state receive a maximum of 50% of the votes in elections, in individual cases up to 60%
- In which opposition members do not have to flee, sit in prisons or die unexpectedly
- In which there is a real choice between more than 3 different parties with different views
- In which the gap between the poorest and the richest in society decreases over time, or at least does not increase

## 🏗️ Workspace Structure

This workspace contains the following packages:

### `src/iphoto_downloader/`

The main application package for syncing photos from iCloud to local storage
with deletion tracking.

### `shared/auth2fa/`

A shared authentication package providing 2FA functionality for iCloud
authentication.

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- iCloud account with Two-Factor Authentication enabled
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/iphoto-downloader.git
   cd iphoto-downloader
   ```

2. **Install all workspace dependencies:**
   ```bash
   uv sync
   ```

3. **Configure your settings:**
   ```bash
   cp .env.example .env
   # Edit .env with your iCloud credentials and sync directory
   ```

4. **Run the sync:**
   ```bash
   uv run iphoto-downloader
   ```

## 🔧 Development

This workspace uses [uv](https://docs.astral.sh/uv/) for dependency management
and workspace orchestration.

### Installing Development Dependencies

```bash
uv sync --dev
```

### Running Tests

Run tests across all packages:

```bash
uv run pytest
```

Run tests for a specific package:

```bash
uv run pytest src/iphoto_downloader/tests/
uv run pytest shared/auth2fa/tests/
```

### Package Dependencies

The workspace is configured so that packages can depend on each other:

- `iphoto_downloader` depends on `auth2fa` for authentication functionality
- Both packages can be developed and tested together

## ⚙️ Configuration

### Option 1: Environment Variables (Traditional)

Create a `.env` file in the project root:

```env
# iCloud Credentials
ICLOUD_USERNAME=your.email@icloud.com
ICLOUD_PASSWORD=your-app-specific-password

# Sync Settings
SYNC_DIRECTORY=/path/to/your/photos
DRY_RUN=false
LOG_LEVEL=INFO
```

### Option 2: Keyring (Secure Storage)

For enhanced security, you can store your credentials in your system's
credential store (Windows Credential Manager, macOS Keychain, Linux Secret
Service). The application automatically detects keyring availability and uses
the appropriate configuration class:

- **KeyringConfig**: Used when keyring is available - supports both environment
  variables and secure credential storage
- **EnvOnlyConfig**: Used when keyring is not available - only supports
  environment variables

1. **Store credentials securely:**
   ```bash
   uv run python iphoto_downloader_credentials.py
   ```

2. **Update your .env file to only include sync settings:**
   ```env
   # Sync Settings (credentials will be retrieved from keyring)
   SYNC_DIRECTORY=/path/to/your/photos
   DRY_RUN=false
   LOG_LEVEL=INFO
   ```

## 🧪 Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/iphoto_downloader

# Run linting
uv run ruff check .
uv run mypy src/
```

### Building Executables

```bash
# Install PyInstaller
uv add --dev pyinstaller

# Build for current platform
uv run pyinstaller iphoto-downloader.spec
```

## 🛠️ How It Works

1. **Authentication**: Securely connects to iCloud using your credentials
2. **Photo Discovery**: Scans your iCloud photo library for all photos
3. **Local Check**: Compares with existing local files and deletion database
4. **Smart Download**: Downloads only new photos that haven't been deleted
   locally
5. **Tracking**: Updates deletion database for any locally missing photos

## 🔒 Security & Privacy

- **No Cloud Storage**: Your credentials and photos stay on your devices
- **App-Specific Passwords**: Uses iCloud app-specific passwords (recommended)
- **Local Database**: Deletion tracking stored locally in SQLite
- **No Data Sharing**: No data is sent to external services

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file
for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Requirements

- Python 3.9+
- iCloud account with Two-Factor Authentication
- Sufficient local storage for your photo library

## 🆘 Support

If you encounter issues:

1. Check the [Issues](https://github.com/your-username/iphoto-downloader/issues)
   page
2. Review the logs in the `logs/` directory
3. Ensure your iCloud credentials are correct
4. Verify Two-Factor Authentication is enabled

## 🙏 Acknowledgments

- Built with [pyicloud](https://pypi.org/project/pyicloud/) for iCloud API
  access
- Dependency management by [uv](https://docs.astral.sh/uv/)
- Inspired by the need for safe, local photo backups
