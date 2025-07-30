#!/usr/bin/env python3
"""
Test runner script for iphoto-downloader project.
Provides easy ways to run all tests, specific test files, or test categories.
"""

import subprocess
import sys
from pathlib import Path


def get_python_executable() -> str:
    """Get the path to the Python executable in the virtual environment."""
    venv_python = Path(__file__).parent / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def run_command(cmd: list[str], description: str) -> int:
    """Run a command and return the exit code."""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(cmd)}")
    print("-" * 50)

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return 1


def main():
    """Main test runner function."""
    python_exe = get_python_executable()

    if len(sys.argv) > 1:
        test_target = sys.argv[1]

        if test_target == "unit":
            # Run only unit tests
            cmd = [python_exe, "-m", "pytest", "tests/unit/", "-v", "--tb=short"]
            return run_command(cmd, "Running Unit Tests")

        elif test_target == "integration":
            # Run only integration tests
            cmd = [python_exe, "-m", "pytest", "tests/integration/", "-v", "--tb=short"]
            return run_command(cmd, "Running Integration Tests")

        elif test_target == "coverage":
            # Run tests with coverage
            cmd = [
                python_exe,
                "-m",
                "pytest",
                "tests/",
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-report=html",
                "--cov-fail-under=80",
            ]
            return run_command(cmd, "Running Tests with Coverage")

        elif test_target.startswith("test_"):
            # Run specific test file
            test_file = f"tests/unit/{test_target}.py"
            if not Path(test_file).exists():
                print(f"❌ Test file not found: {test_file}")
                return 1
            cmd = [python_exe, "-m", "pytest", test_file, "-v", "--tb=short"]
            return run_command(cmd, f"Running {test_file}")

        else:
            print(f"❌ Unknown test target: {test_target}")
            print_usage()
            return 1
    else:
        # Run all tests by default
        cmd = [python_exe, "-m", "pytest", "tests/", "-v", "--tb=short"]
        return run_command(cmd, "Running All Tests")


def print_usage():
    """Print usage information."""
    print("""
Usage: python run_all_tests.py [target]

Targets:
  (no target)     - Run all tests
  unit           - Run only unit tests
  integration    - Run only integration tests  
  coverage       - Run tests with coverage report
  test_config    - Run specific test file (e.g., test_config.py)
  test_sync      - Run specific test file (e.g., test_sync.py)
  test_icloud_client - Run specific test file
  test_deletion_tracker - Run specific test file

Examples:
  python run_all_tests.py
  python run_all_tests.py unit
  python run_all_tests.py coverage
  python run_all_tests.py test_config
""")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        print_usage()
        sys.exit(0)

    exit_code = main()

    if exit_code == 0:
        print("\n✅ All tests completed successfully!")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")

    sys.exit(exit_code)
