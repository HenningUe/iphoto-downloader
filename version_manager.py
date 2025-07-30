#!/usr/bin/env python3
"""Version management script for iPhoto Downloader project."""

import argparse
import sys
from pathlib import Path

# Add the src directory to the path to import version module
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src" / "iphoto_downloader" / "src"))

from iphoto_downloader.version import get_version, increment_version, parse_version


def write_version(version: str, version_file: Path) -> None:
    """Write version to VERSION file."""
    try:
        # Validate version format
        parse_version(version)

        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(version + '\n')

        print(f"✅ Version updated to {version}")

    except Exception as e:
        print(f"❌ Error writing version: {e}")
        sys.exit(1)


def main():
    """Main version management function."""
    parser = argparse.ArgumentParser(
        description="Manage version for iPhoto Downloader project",
        epilog="""
Examples:
  python version_manager.py show                 # Show current version
  python version_manager.py set 1.2.3           # Set specific version  
  python version_manager.py bump patch          # Increment patch version
  python version_manager.py bump minor          # Increment minor version
  python version_manager.py bump major          # Increment major version
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Show current version
    show_parser = subparsers.add_parser('show', help='Show current version')

    # Set specific version
    set_parser = subparsers.add_parser('set', help='Set specific version')
    set_parser.add_argument('version', help='Version to set (e.g., 1.2.3)')

    # Bump version
    bump_parser = subparsers.add_parser('bump', help='Increment version')
    bump_parser.add_argument('level', choices=['major', 'minor', 'patch'],
                           help='Version level to increment')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Determine VERSION file location
    version_file = project_root / "VERSION"

    if args.command == 'show':
        current = get_version()
        print(f"Current version: {current}")

        if version_file.exists():
            print(f"VERSION file: {version_file}")
        else:
            print("VERSION file: Not found (using development version)")

    elif args.command == 'set':
        write_version(args.version, version_file)

    elif args.command == 'bump':
        current = get_version()

        if current == "dev":
            print("❌ Cannot bump development version. Set a specific version first.")
            print("Example: python version_manager.py set 0.1.0")
            sys.exit(1)

        new_version = increment_version(current, args.level)
        print(f"Bumping {args.level} version: {current} → {new_version}")
        write_version(new_version, version_file)


if __name__ == "__main__":
    main()
