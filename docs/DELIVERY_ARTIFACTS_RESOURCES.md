# Delivery Artifacts Resource Management

## Overview

The iPhoto Downloader Tool uses a delivery artifacts management system that includes actual repository files (USER-GUIDE.md and .env.example) as resources in the PyInstaller executable, avoiding code duplication.

## Resource Files

The following files are included as resources in the executable:

- **USER-GUIDE.md** - Copied from repository root
- **settings.ini.template** - Copied from .env.example in repository root

## Resource Directory Structure

```
src/iphoto_downloader/src/iphoto_downloader/resources/
├── __init__.py
├── USER-GUIDE.md (copy of repository USER-GUIDE.md)
└── settings.ini.template (copy of repository .env.example)
```

## How It Works

### Development Mode
When running from source code (`OPERATING_MODE=InDevelopment`):
- Resource files are read from `src/iphoto_downloader/src/iphoto_downloader/resources/`
- If resource files are missing, fallback content is generated programmatically

### Delivered Mode
When running from PyInstaller executable (`OPERATING_MODE=Delivered`):
- Resource files are extracted from the embedded PyInstaller bundle
- Files are accessed via `sys._MEIPASS` location
- If extraction fails, fallback content is generated programmatically

## Updating Resource Files

### Manual Update
Run the update script to sync resource files with repository sources:
```bash
python update_resources.py
```

### Automatic Update (Recommended)
Add the following to your build process before running PyInstaller:

```bash
# Update resources before building
python update_resources.py

# Build executable
pyinstaller iphoto_downloader.spec
```

## PyInstaller Configuration

The `iphoto_downloader.spec` file includes the resource files in the `datas` section:

```python
datas = [
    ('src/iphoto_downloader/src/iphoto_downloader/resources/USER-GUIDE.md', 'iphoto_downloader/resources'),
    ('src/iphoto_downloader/src/iphoto_downloader/resources/settings.ini.template', 'iphoto_downloader/resources')
]
```

## Fallback Content

If resource files cannot be accessed (corrupted, missing, etc.), the system automatically generates fallback content to ensure the application continues to function.

## Benefits

1. **No Code Duplication**: Content is maintained in repository files, not duplicated in Python code
2. **Always Up-to-Date**: Resource files reflect the current repository state
3. **Robust**: Fallback content ensures the application works even if resources are missing
4. **PyInstaller Compatible**: Resources are properly embedded in the executable

## Compliance

This implementation fulfills the SPEC.md requirement:
> "READMD.md and .env.example (as source for settings.ini.template) from the repository are to be used. I.e. when the executable is created these files must be included in the executable as additional resources. The content of the created READM.md and shall **not** be included in a python file as strings to avoid duplicated sources."
