"""Version management utilities for iPhoto Downloader."""

import sys
from pathlib import Path
from typing import Tuple


def get_version() -> str:
    """
    Get the current version of the application.
    
    Returns:
        str: Version string (e.g., "1.2.3") or "dev" if VERSION file not found
    """
    try:
        # Try to read from VERSION file in various locations
        version_paths = [
            # Development mode - from project root
            Path(__file__).parent.parent.parent.parent.parent / "VERSION",
            # PyInstaller bundle - VERSION file included as data
            Path(getattr(sys, '_MEIPASS', '.')) / "VERSION",
            # Alternative PyInstaller location
            Path(sys.executable).parent / "VERSION",
            # Current directory fallback
            Path("VERSION"),
        ]
        
        for version_path in version_paths:
            if version_path.exists() and version_path.is_file():
                with open(version_path, 'r', encoding='utf-8') as f:
                    version = f.read().strip()
                    if version:
                        return version
        
        # No VERSION file found, return development version
        return "dev"
        
    except Exception:
        # Any error reading version, fallback to dev
        return "dev"


def parse_version(version: str) -> Tuple[int, int, int]:
    """
    Parse a semantic version string into components.
    
    Args:
        version: Version string like "1.2.3"
        
    Returns:
        Tuple of (major, minor, patch) integers
        
    Raises:
        ValueError: If version string is not valid semver format
    """
    if version == "dev":
        return (0, 0, 0)
    
    try:
        parts = version.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version}")
        
        major, minor, patch = map(int, parts)
        return (major, minor, patch)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid version format: {version}") from e


def format_version(major: int, minor: int, patch: int) -> str:
    """
    Format version components into a version string.
    
    Args:
        major: Major version number
        minor: Minor version number  
        patch: Patch version number
        
    Returns:
        Version string like "1.2.3"
    """
    return f"{major}.{minor}.{patch}"


def increment_version(version: str, level: str) -> str:
    """
    Increment a version string according to semantic versioning rules.
    
    Args:
        version: Current version string
        level: Increment level ("major", "minor", or "patch")
        
    Returns:
        New version string
        
    Raises:
        ValueError: If version or level is invalid
    """
    if level not in ("major", "minor", "patch"):
        raise ValueError(f"Invalid increment level: {level}")
    
    major, minor, patch = parse_version(version)
    
    if level == "major":
        major += 1
        minor = 0
        patch = 0
    elif level == "minor":
        minor += 1
        patch = 0
    elif level == "patch":
        patch += 1
    
    return format_version(major, minor, patch)


def get_version_info() -> dict:
    """
    Get comprehensive version information.
    
    Returns:
        Dictionary with version details
    """
    version = get_version()
    
    # Check if it's a development version
    is_dev = version == "dev"
    
    if is_dev:
        major, minor, patch = 0, 0, 0
    else:
        try:
            major, minor, patch = parse_version(version)
        except ValueError:
            # Invalid version format, treat as development
            major, minor, patch = 0, 0, 0
            is_dev = True
    
    return {
        "version": version,
        "major": major,
        "minor": minor,
        "patch": patch,
        "is_development": is_dev,
        "is_release": not is_dev,
    }
