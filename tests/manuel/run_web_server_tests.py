"""Interactive runner for manual web server tests.

This script allows you to run individual manual tests for the 2FA web server
or run all tests together.

Usage:
    python tests/manuel/run_web_server_tests.py
"""

import test_web_server_manual
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import the manual test functions directly
sys.path.insert(0, str(Path(__file__).parent))

# Get the test functions
test_basic_server_startup = test_web_server_manual.test_basic_server_startup
test_port_conflict_handling = test_web_server_manual.test_port_conflict_handling
test_server_state_management = test_web_server_manual.test_server_state_management
test_browser_integration = test_web_server_manual.test_browser_integration
test_web_interface_manual = test_web_server_manual.test_web_interface_manual
run_all_manual_tests = test_web_server_manual.run_all_manual_tests


def main():
    """Main interactive menu for manual testing."""
    print("🧪 2FA Web Server Manual Testing")
    print("=" * 40)
    print()
    print("Available tests:")
    print("1. Basic Server Startup & Shutdown")
    print("2. Port Conflict Handling")
    print("3. Server State Management")
    print("4. Browser Integration")
    print("5. Web Interface Manual Test (Interactive)")
    print("6. Run All Tests")
    print("0. Exit")
    print()

    while True:
        try:
            choice = input("Select a test (0-6): ").strip()

            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "1":
                print("\n" + "="*50)
                result = test_basic_server_startup()
                print(f"Result: {'✅ PASSED' if result else '❌ FAILED'}")
            elif choice == "2":
                print("\n" + "="*50)
                result = test_port_conflict_handling()
                print(f"Result: {'✅ PASSED' if result else '❌ FAILED'}")
            elif choice == "3":
                print("\n" + "="*50)
                result = test_server_state_management()
                print(f"Result: {'✅ PASSED' if result else '❌ FAILED'}")
            elif choice == "4":
                print("\n" + "="*50)
                result = test_browser_integration()
                print(f"Result: {'✅ PASSED' if result else '❌ FAILED'}")
            elif choice == "5":
                print("\n" + "="*50)
                print("⚠️ This test will open a browser window for manual interaction")
                confirm = input("Continue? (y/n): ").lower().strip()
                if confirm == 'y':
                    result = test_web_interface_manual()
                    print(f"Result: {'✅ PASSED' if result else '❌ FAILED'}")
                else:
                    print("Test skipped.")
            elif choice == "6":
                print("\n" + "="*50)
                print("🚀 Running all manual tests...")
                print("⚠️ This will open browser windows for manual interaction")
                confirm = input("Continue? (y/n): ").lower().strip()
                if confirm == 'y':
                    result = run_all_manual_tests()
                    print(f"Overall Result: {'✅ ALL PASSED' if result else '❌ SOME FAILED'}")
                else:
                    print("Test skipped.")
            else:
                print("❌ Invalid choice. Please select 0-6.")
                continue

            print("\n" + "="*50)
            print("Press Enter to continue...")
            input()

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Press Enter to continue...")
            input()


if __name__ == "__main__":
    main()
