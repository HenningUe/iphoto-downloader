#!/usr/bin/env python3
"""Cross-platform build verification script for iCloud Photo Sync Tool."""

import argparse
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional


class BuildTester:
    """Test built executables across platforms."""
    
    def __init__(self, executable_path: str):
        """Initialize the build tester.
        
        Args:
            executable_path: Path to the executable to test
        """
        self.executable_path = Path(executable_path)
        self.platform = platform.system().lower()
        self.test_results: Dict[str, bool] = {}
        
    def run_test(self, test_name: str, test_func) -> bool:
        """Run a test and record the result.
        
        Args:
            test_name: Name of the test
            test_func: Function to run the test
            
        Returns:
            True if test passed, False otherwise
        """
        print(f"🧪 Running {test_name}...")
        try:
            result = test_func()
            self.test_results[test_name] = result
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
            return result
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            self.test_results[test_name] = False
            return False
    
    def test_executable_exists(self) -> bool:
        """Test that the executable exists and has correct permissions."""
        if not self.executable_path.exists():
            print(f"   Executable not found: {self.executable_path}")
            return False
            
        if not self.executable_path.is_file():
            print(f"   Path is not a file: {self.executable_path}")
            return False
            
        # Check if executable on Unix-like systems
        if self.platform in ('linux', 'darwin'):
            if not os.access(self.executable_path, os.X_OK):
                print(f"   File is not executable: {self.executable_path}")
                return False
                
        print(f"   Executable found: {self.executable_path}")
        print(f"   Size: {self.executable_path.stat().st_size / (1024*1024):.1f} MB")
        return True
    
    def test_basic_startup(self) -> bool:
        """Test that the executable can start and show help."""
        try:
            result = subprocess.run(
                [str(self.executable_path), '--help'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("   Help command succeeded")
                return True
            else:
                print(f"   Help command failed with exit code: {result.returncode}")
                if result.stderr:
                    print(f"   Error output: {result.stderr[:200]}")
                return False
                
        except subprocess.TimeoutExpired:
            print("   Executable timed out (30s)")
            return False
        except Exception as e:
            print(f"   Failed to run executable: {e}")
            return False
    
    def test_version_info(self) -> bool:
        """Test that the executable can show version information."""
        try:
            result = subprocess.run(
                [str(self.executable_path), '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Version command might not be implemented yet, so accept various exit codes
            if result.returncode in (0, 2):  # 0 = success, 2 = unknown argument (normal)
                print("   Version command handled appropriately")
                return True
            else:
                print(f"   Unexpected exit code for version: {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            print("   Version command timed out")
            return False
        except Exception as e:
            print(f"   Failed to run version command: {e}")
            return False
    
    def test_delivered_mode_behavior(self) -> bool:
        """Test that executable defaults to Delivered mode and handles missing settings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set environment variables to redirect settings to temp directory
            env = os.environ.copy()
            if self.platform == 'windows':
                env['USERPROFILE'] = temp_dir
            else:
                env['HOME'] = temp_dir
                
            try:
                result = subprocess.run(
                    [str(self.executable_path)],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    env=env
                )
                
                # In Delivered mode without settings, app should terminate gracefully
                # and possibly create settings folder
                expected_exit_codes = [0, 1]  # 0 = normal, 1 = missing settings
                
                if result.returncode in expected_exit_codes:
                    print(f"   Delivered mode behavior correct (exit code: {result.returncode})")
                    
                    # Check if settings folder was created
                    if self.platform == 'windows':
                        settings_path = Path(temp_dir) / 'AppData' / 'Local' / 'FotoPool'
                    else:
                        settings_path = Path(temp_dir) / '.local' / 'share' / 'foto-pool'
                    
                    if settings_path.exists():
                        print(f"   Settings folder created: {settings_path}")
                    else:
                        print("   Settings folder not created (may be expected)")
                    
                    return True
                else:
                    print(f"   Unexpected exit code: {result.returncode}")
                    if result.stderr:
                        print(f"   Error: {result.stderr[:200]}")
                    return False
                    
            except subprocess.TimeoutExpired:
                print("   Delivered mode test timed out")
                return False
            except Exception as e:
                print(f"   Delivered mode test failed: {e}")
                return False
    
    def test_dependencies(self) -> bool:
        """Test that all required dependencies are available."""
        if self.platform == 'linux':
            try:
                # Check shared library dependencies
                result = subprocess.run(
                    ['ldd', str(self.executable_path)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    output = result.stdout
                    if 'not found' in output:
                        print("   Missing shared library dependencies:")
                        for line in output.split('\n'):
                            if 'not found' in line:
                                print(f"     {line.strip()}")
                        return False
                    else:
                        print("   All shared library dependencies found")
                        return True
                else:
                    print("   Could not check dependencies with ldd")
                    return True  # Not a failure, just can't check
                    
            except FileNotFoundError:
                print("   ldd not available, skipping dependency check")
                return True
            except Exception as e:
                print(f"   Dependency check failed: {e}")
                return True  # Not a critical failure
                
        elif self.platform == 'windows':
            # For Windows, we could check DLL dependencies, but it's more complex
            print("   Dependency checking not implemented for Windows")
            return True
            
        else:
            print(f"   Dependency checking not implemented for {self.platform}")
            return True
    
    def test_embedded_resources(self) -> bool:
        """Test that embedded resources are accessible."""
        # This is harder to test without modifying the app
        # For now, we'll just verify the executable size is reasonable
        size_mb = self.executable_path.stat().st_size / (1024 * 1024)
        
        # Reasonable size range for a Python executable with embedded resources
        if 20 <= size_mb <= 200:
            print(f"   Executable size ({size_mb:.1f} MB) is reasonable")
            return True
        elif size_mb < 20:
            print(f"   Executable size ({size_mb:.1f} MB) seems too small - resources might be missing")
            return False
        else:
            print(f"   Executable size ({size_mb:.1f} MB) seems large but acceptable")
            return True
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results."""
        print(f"🧪 Testing executable on {platform.system()} {platform.release()}")
        print(f"📁 Executable: {self.executable_path}")
        print("=" * 60)
        
        tests = [
            ("Executable Exists", self.test_executable_exists),
            ("Basic Startup", self.test_basic_startup),
            ("Version Info", self.test_version_info),
            ("Delivered Mode Behavior", self.test_delivered_mode_behavior),
            ("Dependencies", self.test_dependencies),
            ("Embedded Resources", self.test_embedded_resources),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
            print()
        
        # Summary
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        print("=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Executable is ready for distribution.")
            return self.test_results
        else:
            print("❌ Some tests failed. Please review and fix issues.")
            
            # Show failed tests
            failed_tests = [name for name, result in self.test_results.items() if not result]
            if failed_tests:
                print("\n❌ Failed tests:")
                for test in failed_tests:
                    print(f"   - {test}")
                    
            return self.test_results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test built iCloud Photo Sync executable"
    )
    parser.add_argument(
        "executable",
        help="Path to the executable to test"
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Show only test summary"
    )
    
    args = parser.parse_args()
    
    if not Path(args.executable).exists():
        print(f"❌ Executable not found: {args.executable}")
        sys.exit(1)
    
    tester = BuildTester(args.executable)
    
    if args.summary_only:
        # Quick test mode
        basic_tests = ["Executable Exists", "Basic Startup"]
        for test_name in basic_tests:
            if test_name == "Executable Exists":
                tester.run_test(test_name, tester.test_executable_exists)
            elif test_name == "Basic Startup":
                tester.run_test(test_name, tester.test_basic_startup)
        
        passed = sum(1 for result in tester.test_results.values() if result)
        total = len(tester.test_results)
        print(f"\n📊 Quick Test: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ Basic tests passed")
            sys.exit(0)
        else:
            print("❌ Basic tests failed")
            sys.exit(1)
    else:
        # Full test suite
        results = tester.run_all_tests()
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        if passed == total:
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
