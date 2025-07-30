# CI Environment Setup

## Overview

The GitHub Actions workflows automatically create a `.env` file from `.env.example` before running tests. This ensures that all tests have access to the required configuration settings.

## Why This Is Needed

Several components of the iPhoto Downloader rely on configuration from environment variables or a `.env` file:

1. **Configuration Loading**: The `get_config()` function first looks for `.env` in the current directory
2. **Test Dependencies**: Many tests use `get_config()` to initialize components
3. **Build Process**: Some build scripts may require configuration values

## Implementation

### In CI Workflows

All GitHub Actions workflows now include this step before running tests:

**Linux/macOS:**
```yaml
- name: Create .env file for testing
  run: |
    cp .env.example .env
    echo "✓ Created .env file from .env.example for testing"
```

**Windows:**
```yaml
- name: Create .env file for testing
  run: |
    copy .env.example .env
    echo "✓ Created .env file from .env.example for testing"
```

### Modified Workflows

The following workflows have been updated:

- `ci.yml` - Main CI pipeline
- `quality.yml` - Code quality checks  
- `nightly.yml` - Extended testing (3 jobs)
- `release.yml` - Release builds (Windows & Linux)
- `dependencies.yml` - Dependency updates

## Test-Friendly Defaults

The `.env.example` file is configured with test-friendly defaults:

- `DRY_RUN=true` - Prevents actual iCloud operations
- `SYNC_DIRECTORY=./photos` - Safe local directory
- `LOG_LEVEL=INFO` - Reasonable verbosity
- `MAX_DOWNLOADS=0` - No limits for testing
- `EXECUTION_MODE=single` - Run once and exit

## Local Development

For local development, developers should still copy `.env.example` to `.env` and customize it:

```bash
cp .env.example .env
# Edit .env with your settings
```

## Benefits

1. **Consistent Testing**: All CI environments have the same configuration
2. **No Missing Config**: Tests won't fail due to missing environment setup
3. **Safe Defaults**: Test-friendly settings prevent accidental operations
4. **Cross-Platform**: Works correctly on Linux, macOS, and Windows runners
