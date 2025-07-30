# 🔨 Build System Documentation

This document describes how to build the iPhoto Downloader Tool for different platforms.

## 📋 Prerequisites

### All Platforms
- [uv](https://docs.astral.sh/uv/) package manager installed
- Python 3.12+ 
- Git (for cloning the repository)

### Windows Specific
- PowerShell 5.1 or later
- Windows 10/11

### Linux Specific
- Bash shell
- Development packages: `python3-dev` (Ubuntu/Debian) or `python3-devel` (CentOS/RHEL)

## 🚀 Quick Start

### Windows Build

```powershell
# Simple build
.\build_windows.ps1

# Clean build with testing
.\build_windows.ps1 -Clean -Test

# Custom output directory
.\build_windows.ps1 -OutputDir "releases"
```

### Linux Build

```bash
# Simple build
./build_linux.sh

# Clean build with testing
./build_linux.sh --clean --test

# Custom output directory
./build_linux.sh --output-dir releases
```

## 🧪 Testing Built Executables

Use the cross-platform test script to verify your builds:

```bash
# Full test suite
python test_build.py dist/iphoto_downloader.exe     # Windows
python test_build.py dist/iphoto_downloader         # Linux

# Quick smoke test
python test_build.py --summary-only dist/iphoto_downloader.exe
```

## 📁 Build Outputs

### Directory Structure
```
dist/
├── iphoto_downloader.exe      # Windows executable
├── iphoto_downloader          # Linux executable
└── _internal/                 # PyInstaller runtime files (if using --onedir)

build/                         # Temporary build files (can be deleted)
```

### Embedded Resources

Both executables include the following embedded resources for delivery artifacts:
- `USER-GUIDE.md` - Repository documentation
- `.env.example` - Configuration template (becomes `settings.ini.template`)

These resources are automatically copied to the user's settings folder in "Delivered" mode.

## ⚙️ Build Configuration

### PyInstaller Spec File

The build process uses `iphoto_downloader.spec` which includes:

```python
# Data files included in executable
datas = [
    ('USER-GUIDE.md', '.'),           # Repository README
    ('.env.example', '.'),        # Configuration template
]

# Hidden imports for keyring backends
hiddenimports = [
    'keyring.backends.Windows',
    'keyring.backends.macOS', 
    'keyring.backends.SecretService',
    'keyring.backends.kwallet',
    # ... other imports
]
```

### Operating Mode Detection

Built executables automatically:
1. Detect they're running in PyInstaller "frozen" mode
2. Default to "Delivered" operating mode
3. Access embedded resources via `sys._MEIPASS`
4. Create user settings folders as needed

## 🛠️ Customizing Builds

### Build Script Options

#### Windows (`build_windows.ps1`)
- `-Clean`: Remove previous build artifacts
- `-Test`: Run basic executable tests after build
- `-OutputDir <path>`: Specify output directory

#### Linux (`build_linux.sh`)
- `--clean`: Remove previous build artifacts
- `--test`: Run basic executable tests after build
- `--output-dir <path>`: Specify output directory

### Advanced PyInstaller Options

You can modify `iphoto_downloader.spec` to customize:

```python
# Single file vs directory bundle
exe = EXE(
    # ...
    console=False,    # Hide console window (Windows)
    onefile=True,     # Single file executable
    # ...
)

# Additional data files
datas = [
    ('additional_file.txt', '.'),
    ('config/', 'config/'),
]

# Exclude unnecessary modules
excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
]
```

## 🧪 Test Scenarios

### Automated Tests

The `test_build.py` script performs:

1. **Executable Exists**: Verifies file presence and permissions
2. **Basic Startup**: Tests `--help` command functionality
3. **Version Info**: Tests version command handling
4. **Delivered Mode**: Verifies default mode behavior
5. **Dependencies**: Checks shared library dependencies (Linux)
6. **Embedded Resources**: Validates reasonable executable size

### Manual Testing Checklist

After building, manually verify:

- [ ] Executable starts without errors
- [ ] Delivery artifacts are created in "Delivered" mode
- [ ] Settings folder is created in correct location
- [ ] USER-GUIDE.md and settings.ini.template are copied correctly
- [ ] 2FA web server starts successfully
- [ ] Pushover notifications work
- [ ] Keyring integration functions properly

## 🐛 Troubleshooting

### Common Issues

#### Windows
- **"Execution Policy" Error**: Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- **Missing Dependencies**: Ensure `uv` is in PATH
- **Large Executable Size**: Normal for Python applications (20-100MB)

#### Linux
- **Permission Denied**: Run `chmod +x build_linux.sh`
- **Missing python3-dev**: Install with `sudo apt install python3-dev`
- **Shared Library Errors**: Install missing system packages

#### Both Platforms
- **Build Failures**: Check `uv sync --dev` runs successfully
- **Missing Resources**: Verify `USER-GUIDE.md` and `.env.example` exist in repository root
- **Import Errors**: Add missing modules to `hiddenimports` in spec file

### Debug Mode

For detailed build information:

```bash
# Verbose PyInstaller output
uv run pyinstaller --log-level DEBUG iphoto_downloader.spec

# Check imported modules
uv run pyi-makespec --onefile src/iphoto_downloader/src/iphoto_downloader/main.py
```

## 📦 Distribution

### Windows
- Distribute the `.exe` file directly
- Consider creating an installer with [Inno Setup](https://jrsoftware.org/isinfo.php)
- Package for [WinGet](https://docs.microsoft.com/en-us/windows/package-manager/)

### Linux
- Distribute the executable directly
- Create AppImage with [linuxdeploy](https://github.com/linuxdeploy/linuxdeploy)
- Package as `.deb` or `.rpm` with [fpm](https://github.com/jordansissel/fpm)

### Example packaging commands:

```bash
# Create AppImage (requires linuxdeploy)
linuxdeploy --appdir AppDir --executable dist/iphoto_downloader --create-desktop-file --output appimage

# Create deb package (requires fpm)
fpm -s dir -t deb -n iphoto-downloader -v 1.0.0 \
    --description "iPhoto Downloader Tool" \
    --url "https://github.com/your-org/iphoto-downloader" \
    --maintainer "Your Name <your.email@example.com>" \
    dist/iphoto_downloader=/usr/local/bin/

# Create rpm package (requires fpm)
fpm -s dir -t rpm -n iphoto-downloader -v 1.0.0 \
    --description "iPhoto Downloader Tool" \
    --url "https://github.com/your-org/iphoto-downloader" \
    --maintainer "Your Name <your.email@example.com>" \
    dist/iphoto_downloader=/usr/local/bin/
```

## 📚 References

- [PyInstaller Documentation](https://pyinstaller.readthedocs.io/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Delivery Artifacts Design](docs/DELIVERY_ARTIFACTS_DESIGN.md)
- [Cross-Platform Build Testing](test_build.py)
