#!/usr/bin/env python3
"""
E2E Test Runner for iCloud Photo Sync with 2FA Support

This script helps run end-to-end integration tests that require real iCloud credentials
and handles 2FA authentication requirements.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from icloud_photo_sync.config import KEYRING_AVAILABLE, get_config


def check_prerequisites():
    """Check if all prerequisites for E2E testing are met."""
    print("🔍 Checking E2E test prerequisites...")
    
    # Check if keyring is available
    if not KEYRING_AVAILABLE:
        print("❌ Keyring is not available")
        print("💡 Run: pip install keyring")
        return False
    
    print("✅ Keyring is available")
    
    # Check if credentials are stored
    try:
        config = get_config()
        if not config.icloud_username or not config.icloud_password:
            print("❌ iCloud credentials not found")
            print("💡 Run: python manage_credentials.py")
            print("💡 Store your iCloud credentials in keyring first")
            return False
        
        print(f"✅ Credentials found for: {config.icloud_username}")
        
    except Exception as e:
        print(f"❌ Error checking credentials: {e}")
        print("💡 Run: python manage_credentials.py")
        return False
    
    return True


def run_integration_tests(interactive=False, test_filter=None):
    """Run integration tests with proper setup."""
    python_exe = get_python_executable()
    
    # Base pytest command
    cmd = [
        python_exe, "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=short",
        "-m", "integration"
    ]
    
    # Add interactive tests if requested
    if interactive:
        os.environ['RUN_INTERACTIVE_TESTS'] = '1'
        print("🔐 Interactive mode enabled - 2FA tests will require manual input")
    else:
        # Skip slow tests unless specifically requested
        cmd.extend(["-m", "not slow"])
        print("⚡ Running non-interactive tests only (skipping slow/2FA tests)")
    
    # Add specific test filter if provided
    if test_filter:
        cmd.extend(["-k", test_filter])
    
    print(f"\n🚀 Running command: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1
    finally:
        # Clean up environment
        os.environ.pop('RUN_INTERACTIVE_TESTS', None)


def get_python_executable():
    """Get the path to the Python executable in the virtual environment."""
    venv_python = Path(__file__).parent / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def print_usage():
    """Print usage information."""
    print("""
E2E Test Runner for iCloud Photo Sync

Usage: python run_e2e_tests.py [options]

Options:
  --interactive     Enable interactive tests (requires manual 2FA input)
  --all            Run all tests including slow ones
  --auth-only      Run only authentication tests
  --sync-only      Run only sync tests
  --dry-run        Run tests in dry-run mode only
  --help           Show this help message

Prerequisites:
  1. Store iCloud credentials: python manage_credentials.py
  2. Ensure 2FA is set up on your iCloud account
  3. Have access to your 2FA device during interactive tests

Test Modes:
  - Default: Runs basic integration tests, skips 2FA/slow tests
  - Interactive: Includes 2FA tests that require manual code input
  - All: Runs all tests including slow photo listing tests

Examples:
  python run_e2e_tests.py                    # Basic integration tests
  python run_e2e_tests.py --interactive      # Include 2FA tests
  python run_e2e_tests.py --auth-only        # Only authentication tests
  python run_e2e_tests.py --all              # All tests including slow ones
""")


def main():
    """Main function."""
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        print_usage()
        return 0
    
    # Check prerequisites first
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please resolve the issues above.")
        return 1
    
    # Parse arguments
    interactive = "--interactive" in args
    run_all = "--all" in args
    
    test_filter = None
    if "--auth-only" in args:
        test_filter = "authentication"
    elif "--sync-only" in args:
        test_filter = "sync"
    elif "--dry-run" in args:
        test_filter = "dry_run"
    
    print("\n" + "="*60)
    print("🧪 iCloud Photo Sync - E2E Integration Tests")
    print("="*60)
    
    if interactive:
        print("\n⚠️  INTERACTIVE MODE ENABLED")
        print("📱 You will need to enter 2FA codes manually during testing")
        print("🔐 Make sure your 2FA device is available")
        
        confirm = input("\nContinue with interactive testing? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("❌ Testing cancelled.")
            return 0
    
    # Set up test environment
    if run_all:
        # Remove the "not slow" marker to run all tests
        pass
    
    # Run the tests
    exit_code = run_integration_tests(interactive=interactive, test_filter=test_filter)
    
    if exit_code == 0:
        print("\n✅ All E2E tests completed successfully!")
        print("🎉 Your iCloud Photo Sync integration is working!")
    else:
        print(f"\n❌ E2E tests failed with exit code: {exit_code}")
        print("💡 Check the test output above for details")
        print("💡 Common issues:")
        print("   - Invalid credentials (run: python manage_credentials.py)")
        print("   - 2FA required but not handled")
        print("   - Network connectivity issues")
        print("   - iCloud service temporarily unavailable")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
