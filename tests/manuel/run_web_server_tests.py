"""Interactive runner for manual web server tests.

This script allows you to run individual manual tests for the 2FA web server
or run all tests together.

Usage:
    python tests/manuel/run_web_server_tests.py
"""

import sys
from pathlib import Path

import test_web_server_manual

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import the manual test functions directly
sys.path.insert(0, str(Path(__file__).parent))

# Get the test functions
test_port_conflict_handling = test_web_server_manual.test_port_conflict_handling
test_server_state_management = test_web_server_manual.test_server_state_management
test_browser_integration = test_web_server_manual.test_browser_integration
test_web_interface_manual = test_web_server_manual.test_web_interface_manual


def main():
    """Main interactive menu for manual testing."""
    print("🧪 2FA Web Server Manual Testing")
    print("=" * 40)
    print()
    print("Available tests:")
    print("1. Port Conflict Handling")
    print("2. Server State Management")
    print("3. Browser Integration")
    print("4. Web Interface Manual Test (Interactive)")
    print("0. Exit")
    print("0. Exit")
    print()

    while True:
        try:
            choice = input("Select a test (0-4): ").strip()

            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "1":
                print("\n" + "=" * 50)
                result = test_port_conflict_handling()
                print(f"Result: {'✅ PASSED' if result else '❌ FAILED'}")
            elif choice == "2":
                print("\n" + "=" * 50)
                result = test_server_state_management()
                print(f"Result: {'✅ PASSED' if result else '❌ FAILED'}")
            elif choice == "3":
                print("\n" + "=" * 50)
                result = test_browser_integration()
                print(f"Result: {'✅ PASSED' if result else '❌ FAILED'}")
            elif choice == "4":
                print("\n" + "=" * 50)
                print("⚠️ This test will open a browser window for manual interaction")
                confirm = input("Continue? (y/n): ").lower().strip()
                if confirm == "y":
                    result = test_web_interface_manual()
                    print(f"Result: {'✅ PASSED' if result else '❌ FAILED'}")
                else:
                    print("Test skipped.")
            else:
                print("❌ Invalid choice. Please select 0-4.")
                continue

            print("\n" + "=" * 50)
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
