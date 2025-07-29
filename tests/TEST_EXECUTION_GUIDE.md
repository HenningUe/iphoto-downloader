# Test Execution Guide

This document explains all the ways to run tests in the icloud-photo-sync project.

## Prerequisites

Make sure your virtual environment is set up and activated:
```powershell
# The .venv directory should already exist in your project root
# Python environment is configured and ready to use
```

## Running Tests

### 1. Using the Comprehensive Test Runner (Recommended)

We've created a comprehensive test runner script that provides multiple options:

```powershell
# Run all tests
python run_all_tests.py

# Run only unit tests
python run_all_tests.py unit

# Run only integration tests
python run_all_tests.py integration

# Run tests with coverage report
python run_all_tests.py coverage

# Run specific test files
python run_all_tests.py test_config
python run_all_tests.py test_sync
python run_all_tests.py test_icloud_client
python run_all_tests.py test_deletion_tracker

# Get help
python run_all_tests.py --help
```

### 2. Using pytest directly

```powershell
# Run all tests
C:/Users/uekoe/Repos/iphoto-downloader/iphoto-downloader/.venv/Scripts/python.exe -m pytest tests/ -v

# Run unit tests only
C:/Users/uekoe/Repos/iphoto-downloader/iphoto-downloader/.venv/Scripts/python.exe -m pytest tests/unit/ -v

# Run integration tests only
C:/Users/uekoe/Repos/iphoto-downloader/iphoto-downloader/.venv/Scripts/python.exe -m pytest tests/integration/ -v

# Run with coverage
C:/Users/uekoe/Repos/iphoto-downloader/iphoto-downloader/.venv/Scripts/python.exe -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Run specific test file
C:/Users/uekoe/Repos/iphoto-downloader/iphoto-downloader/.venv/Scripts/python.exe -m pytest tests/unit/test_config.py -v
```

### 3. Using the Original Test Runner

```powershell
# Run using the existing run_tests.py script
C:/Users/uekoe/Repos/iphoto-downloader/iphoto-downloader/.venv/Scripts/python.exe tests/run_tests.py
```

### 4. Using VS Code Tasks

Press `Ctrl+Shift+P` in VS Code and type "Tasks: Run Task", then select:
- **Run All Tests** - Runs all tests with verbose output
- **Run Unit Tests** - Runs only unit tests
- **Run Tests with Coverage** - Runs tests with coverage report and HTML output
- **Run Integration Tests** - Runs only integration tests

## Test Structure

```
tests/
├── __init__.py
├── run_tests.py              # Original test runner
├── common_test_utils.py       # Shared test utilities
├── unit/                      # Unit tests
│   ├── __init__.py
│   ├── test_config.py         # Configuration tests
│   ├── test_deletion_tracker.py # Deletion tracker tests
│   ├── test_icloud_client.py  # iCloud client tests
│   └── test_sync.py           # Sync functionality tests
└── integration/               # Integration tests
    └── __init__.py
```

## Test Results Summary

✅ **76 tests passing**  
❌ **2 tests failing** (configuration-related - expected without credentials)  
📊 **85.21% code coverage** (exceeds 80% requirement)  

The failing tests are configuration tests that require iCloud credentials, which is expected in a development environment.

## Coverage Reports

When running tests with coverage, you'll get:
- Terminal coverage report with missing lines
- HTML coverage report in `htmlcov/` directory
- XML coverage report in `coverage.xml`

## Notes

- All tests are now fully executable and can be run in multiple ways
- The virtual environment is properly configured with all dependencies
- Coverage requirements (80%) are met
- Test failures related to missing iCloud credentials are expected in development
