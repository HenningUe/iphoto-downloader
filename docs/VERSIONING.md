# Versioning Guide

This document explains the versioning system for the iPhoto Downloader project.

## Overview

The project uses [Semantic Versioning (SemVer)](https://semver.org/) with the format `MAJOR.MINOR.PATCH`:

- **MAJOR**: Incompatible API changes or major feature overhauls
- **MINOR**: New functionality added in a backward-compatible manner  
- **PATCH**: Backward-compatible bug fixes

## Version Management

### Current Version

To check the current version:

```bash
python version_manager.py show
```

### Setting a Version

To set a specific version:

```bash
python version_manager.py set 1.2.3
```

### Incrementing Versions

To bump the version:

```bash
# Increment patch version (1.2.3 → 1.2.4)
python version_manager.py bump patch

# Increment minor version (1.2.3 → 1.3.0)  
python version_manager.py bump minor

# Increment major version (1.2.3 → 2.0.0)
python version_manager.py bump major
```

## Version Display

Both applications display their version on startup:

- **Main Application**: `🌟 iPhoto Downloader Tool vX.Y.Z`
- **Credentials Manager**: `🔑 iPhoto Downloader - Credential Manager vX.Y.Z`

## Release Process

### Automated Releases

1. **Tag-triggered Release**: Push a git tag starting with `v` (e.g., `v1.2.3`)
   ```bash
   git tag v1.2.3
   git push origin v1.2.3
   ```

2. **Manual Release**: Use GitHub Actions workflow dispatch
   - Go to Actions → Release
   - Choose "Run workflow"
   - Enter version (e.g., `1.2.3`)
   - Choose whether to create a git tag

### Version Validation

The CI/CD pipeline automatically:
- Validates version format (must be valid SemVer)
- Updates the `VERSION` file
- Builds executables with correct version
- Creates GitHub releases with version info

## Development vs. Release Versions

- **Development**: When no `VERSION` file exists, applications show `vdev`
- **Release**: Applications read version from `VERSION` file or embedded resources

## Version Increment Guidelines

### MAJOR Version (X.0.0)

Increment when making incompatible changes:
- Removing or changing existing configuration options
- Changing database schema without migration
- Removing command-line arguments
- Major architectural changes

### MINOR Version (X.Y.0)

Increment when adding backward-compatible functionality:
- New configuration options (with defaults)
- New command-line arguments
- New features
- Performance improvements

### PATCH Version (X.Y.Z)

Increment for backward-compatible bug fixes:
- Bug fixes
- Security patches
- Documentation updates
- Internal refactoring without behavior changes

## File Locations

- **VERSION file**: `VERSION` (project root)
- **Version module**: `src/iphoto_downloader/src/iphoto_downloader/version.py`
- **Version manager**: `version_manager.py`

## CI/CD Integration

The release workflow:
1. Validates version format
2. Updates `VERSION` file
3. Builds executables for Windows and Linux
4. Tests built executables
5. Creates GitHub release with assets
6. Includes version in release artifacts

## Examples

### Setting Initial Version
```bash
python version_manager.py set 0.1.0
```

### Release Workflow
```bash
# Development cycle
python version_manager.py bump patch  # 0.1.0 → 0.1.1
git add VERSION
git commit -m "Bump version to 0.1.1"
git push

# Create release
git tag v0.1.1
git push origin v0.1.1
```

### Pre-release Versions
For pre-releases, append identifiers:
```bash
python version_manager.py set 1.0.0-alpha.1
python version_manager.py set 1.0.0-beta.2
python version_manager.py set 1.0.0-rc.1
```

## Troubleshooting

### Invalid Version Format
```
❌ Invalid version format: 1.2
```
Ensure version follows SemVer format: `MAJOR.MINOR.PATCH`

### Cannot Bump Development Version
```
❌ Cannot bump development version. Set a specific version first.
```
Set an initial version before bumping:
```bash
python version_manager.py set 0.1.0
```

### VERSION File Not Found
Applications fall back to `dev` version when `VERSION` file is missing.
