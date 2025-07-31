"""
End-to-end tests for iPhoto Downloader Tool.
These tests require a dummy or sandbox iCloud account and will perform real
sync operations in a temp directory.
"""

import getpass
import os
import subprocess
import sys
from pathlib import Path

import pytest

# These tests are marked as 'e2e' and 'slow' and are skipped by default unless --run-e2e is passed
pytestmark = pytest.mark.slow


def get_icloud_credentials():
    """Get iCloud credentials from environment variables or user input."""
    username = os.getenv("E2E_ICLOUD_USERNAME")
    password = os.getenv("E2E_ICLOUD_PASSWORD")

    if not username or not password:
        print("\n" + "=" * 60)
        print("E2E Test Setup: iCloud Credentials Required")
        print("=" * 60)
        print("These end-to-end tests require iCloud credentials.")
        print("You can set them as environment variables:")
        print("  E2E_ICLOUD_USERNAME=your_test_username")
        print("  E2E_ICLOUD_PASSWORD=your_test_password")
        print("\nOr enter them interactively below:")
        print("(Use a dummy/test iCloud account, not your primary account!)")
        print("-" * 60)

        if not username:
            username = input("iCloud Username/Email: ").strip()
            if not username:
                pytest.skip("No iCloud username provided.")

        if not password:
            password = getpass.getpass("iCloud Password: ").strip()
            if not password:
                pytest.skip("No iCloud password provided.")

        print("Credentials received. Running E2E tests...")
        print("=" * 60)

    return username, password


@pytest.mark.e2e
@pytest.mark.skipif(
    bool(os.environ.get("CI")) or bool(os.environ.get("GITHUB_ACTIONS")),
    reason="E2E tests disabled in CI environment",
)
@pytest.mark.skipif(
    not os.getenv("E2E_ICLOUD_USERNAME") and not os.getenv("E2E_ICLOUD_PASSWORD"),
    reason=(
        "E2E tests require iCloud credentials. Set E2E_ICLOUD_USERNAME and "
        "E2E_ICLOUD_PASSWORD env vars or run with -s to enter interactively."
    ),
)
def test_e2e_sync_real_icloud(tmp_path):
    """
    End-to-end: Run the sync tool against a real (dummy/sandbox) iCloud account.
    Requires E2E_ICLOUD_USERNAME and E2E_ICLOUD_PASSWORD env vars or interactive input.
    """
    # Get credentials dynamically during test execution
    ICLOUD_USERNAME, ICLOUD_PASSWORD = get_icloud_credentials()

    # Prepare .env file in temp dir
    env_file = tmp_path / ".env"
    env_file.write_text(f"""
ICLOUD_USERNAME={ICLOUD_USERNAME}
ICLOUD_PASSWORD={ICLOUD_PASSWORD}
SYNC_DIRECTORY={tmp_path / "photos"}
DRY_RUN=false
LOG_LEVEL=DEBUG
MAX_DOWNLOADS=5
""")

    # Run the sync tool as a subprocess
    import sys

    python_executable = sys.executable

    result = subprocess.run(
        [python_executable, "-m", "iphoto_downloader.main", "--config", str(env_file)],
        check=False,
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
        timeout=120,
    )

    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    assert result.returncode == 0, f"Sync failed: {result.stderr}"
    photos_dir = tmp_path / "photos"
    assert photos_dir.exists(), "Photos directory was not created."
    downloaded = (
        list(photos_dir.glob("*.jpg"))
        + list(photos_dir.glob("*.jpeg"))
        + list(photos_dir.glob("*.png"))
    )
    assert len(downloaded) > 0, "No photos were downloaded."


@pytest.mark.e2e
@pytest.mark.skipif(
    bool(os.environ.get("CI")) or bool(os.environ.get("GITHUB_ACTIONS")),
    reason="E2E tests disabled in CI environment",
)
@pytest.mark.skipif(
    not os.getenv("E2E_ICLOUD_USERNAME") and not os.getenv("E2E_ICLOUD_PASSWORD"),
    reason=(
        "E2E tests require iCloud credentials. Set E2E_ICLOUD_USERNAME and "
        "E2E_ICLOUD_PASSWORD env vars or run with -s to enter interactively."
    ),
)
def test_e2e_sync_dry_run(tmp_path):
    """
    End-to-end: Run the sync tool in dry-run mode and ensure no files are downloaded.
    """
    # Get credentials dynamically during test execution
    ICLOUD_USERNAME, ICLOUD_PASSWORD = get_icloud_credentials()

    env_file = tmp_path / ".env"
    env_file.write_text(f"""
ICLOUD_USERNAME={ICLOUD_USERNAME}
ICLOUD_PASSWORD={ICLOUD_PASSWORD}
SYNC_DIRECTORY={tmp_path / "photos"}
DRY_RUN=true
LOG_LEVEL=DEBUG
MAX_DOWNLOADS=2
""")

    python_executable = sys.executable

    result = subprocess.run(
        [python_executable, "-m", "iphoto_downloader.main", "--config", str(env_file)],
        check=False,
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
        timeout=120,
    )

    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    assert result.returncode == 0, f"Sync failed: {result.stderr}"
    photos_dir = tmp_path / "photos"
    assert photos_dir.exists(), "Photos directory was not created."
    downloaded = (
        list(photos_dir.glob("*.jpg"))
        + list(photos_dir.glob("*.jpeg"))
        + list(photos_dir.glob("*.png"))
    )
    assert len(downloaded) == 0, "Photos were downloaded in dry-run mode."


@pytest.mark.e2e
@pytest.mark.skipif(
    bool(os.environ.get("CI")) or bool(os.environ.get("GITHUB_ACTIONS")),
    reason="E2E tests disabled in CI environment",
)
def test_e2e_sync_handles_invalid_credentials(tmp_path):
    """
    End-to-end: Run the sync tool with invalid credentials and expect failure.
    """
    env_file = tmp_path / ".env"
    env_file.write_text(f"""
ICLOUD_USERNAME=invalid_user@example.com
ICLOUD_PASSWORD=wrongpassword
SYNC_DIRECTORY={tmp_path / "photos"}
DRY_RUN=false
LOG_LEVEL=DEBUG
MAX_DOWNLOADS=1
""")

    import sys

    python_executable = sys.executable

    result = subprocess.run(
        [python_executable, "-m", "iphoto_downloader.main", "--config", str(env_file)],
        check=False,
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
        timeout=60,
    )

    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)

    assert result.returncode != 0, "Sync should fail with invalid credentials."
    assert (
        "authentication" in result.stderr.lower()
        or "failed" in result.stderr.lower()
        or result.returncode != 0
    )
