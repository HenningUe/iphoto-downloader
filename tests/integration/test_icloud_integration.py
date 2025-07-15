"""Integration tests for iCloud Photo Sync Tool with real iCloud authentication."""

import os
import pytest
import tempfile
from pathlib import Path

from icloud_photo_sync.config import get_config, KEYRING_AVAILABLE
from icloud_photo_sync.icloud_client import iCloudClient
from icloud_photo_sync.sync import PhotoSyncer
from icloud_photo_sync.logger import setup_logging


@pytest.mark.integration
class TestiCloudIntegration:
    """Integration tests that require real iCloud credentials and 2FA handling."""

    def setup_method(self):
        """Set up test environment."""
        # Create temporary directory for test downloads
        self.temp_dir = tempfile.mkdtemp()
        self.test_sync_dir = Path(self.temp_dir) / "test_photos"
        self.test_sync_dir.mkdir(exist_ok=True)

        # Override sync directory in environment
        os.environ['SYNC_DIRECTORY'] = str(self.test_sync_dir)
        os.environ['DRY_RUN'] = 'true'  # Start with dry run for safety
        os.environ['MAX_DOWNLOADS'] = '5'  # Limit downloads for testing

        # Set up logging for tests
        config = get_config()
        setup_logging(config.get_log_level())

    def teardown_method(self):
        """Clean up test environment."""
        # Clean up temporary directory
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

        # Clean up environment variables
        env_vars_to_clean = ['SYNC_DIRECTORY', 'DRY_RUN', 'MAX_DOWNLOADS']
        for var in env_vars_to_clean:
            os.environ.pop(var, None)

    def test_config_loads_with_keyring_credentials(self):
        """Test that configuration loads credentials from keyring."""
        if not KEYRING_AVAILABLE:
            pytest.skip("Keyring not available")

        config = get_config()

        # Should have credentials either from env or keyring
        assert config.icloud_username is not None, \
            "Username should be available from keyring or env"
        assert config.icloud_password is not None, \
            "Password should be available from keyring or env"
        assert config.sync_directory == self.test_sync_dir
        assert config.dry_run is True

    def test_icloud_authentication_without_2fa(self):
        """Test iCloud authentication when 2FA is not required."""
        if not KEYRING_AVAILABLE:
            pytest.skip("Keyring not available")

        config = get_config()
        client = iCloudClient(config)

        # Attempt authentication
        auth_result = client.authenticate()

        if not auth_result:
            pytest.skip(
                "Authentication failed - this may be due to 2FA requirement or invalid credentials")

        assert client.is_authenticated
        assert client._api is not None

    @pytest.mark.slow
    def test_icloud_authentication_with_2fa_simulation(self):
        """Test iCloud authentication workflow when 2FA is required."""
        if not KEYRING_AVAILABLE:
            pytest.skip("Keyring not available")

        config = get_config()
        client = iCloudClient(config)

        # First, try to authenticate
        auth_result = client.authenticate()

        if not auth_result:
            print("❌ Initial authentication failed")
            print("💡 This test requires valid iCloud credentials stored in keyring")
            print("💡 Run 'python manage_credentials.py' to store credentials first")
            pytest.skip("Authentication failed - check credentials")

        # Check if 2FA is required
        if client.requires_2fa():
            print("🔐 2FA is required for this account")
            print("💡 This test would need manual 2FA code input in a real scenario")
            print("💡 In automated testing, 2FA should be handled with trusted sessions")

            # For testing purposes, we'll just verify the 2FA detection works
            assert client.requires_2fa() is True

            # Note: In a real test environment, you would either:
            # 1. Use a test account with 2FA disabled
            # 2. Use trusted device sessions that don't require 2FA
            # 3. Mock the 2FA process for automated testing
            pytest.skip("2FA required - manual intervention needed")
        else:
            print("✅ 2FA not required - authentication successful")
            assert client.is_authenticated

    @pytest.mark.slow
    def test_photo_listing_integration(self):
        """Test fetching photo list from iCloud."""
        if not KEYRING_AVAILABLE:
            pytest.skip("Keyring not available")

        config = get_config()
        client = iCloudClient(config)

        # Authenticate first
        if not client.authenticate():
            pytest.skip("Authentication failed")

        if client.requires_2fa():
            pytest.skip("2FA required - manual intervention needed")

        # Test photo listing (limited to first few photos)
        photos = list(client.list_photos())

        # Should have some photos (or at least not error)
        assert isinstance(photos, list)
        print(f"📊 Found {len(photos)} photos in iCloud")

        if photos:
            # Verify photo structure
            first_photo = photos[0]
            required_keys = ['id', 'filename', 'size', 'created', 'photo_obj']
            for key in required_keys:
                assert key in first_photo, f"Photo should have {key} field"

            print(f"📸 First photo: {first_photo['filename']}")

    def test_full_sync_dry_run(self):
        """Test full sync operation in dry run mode."""
        if not KEYRING_AVAILABLE:
            pytest.skip("Keyring not available")

        config = get_config()
        sync = PhotoSyncer(config)

        try:
            # Run sync in dry run mode
            result = sync.sync()

            if not result:
                print("❌ Sync failed - likely due to authentication or 2FA")
                print("💡 Check that credentials are stored and 2FA is handled")
                pytest.skip("Sync failed - check authentication")

            print("✅ Dry run sync completed successfully")
            assert result is True

        except Exception as e:
            if "2fa" in str(e).lower() or "two-factor" in str(e).lower():
                pytest.skip(f"2FA required: {e}")
            else:
                raise


# @pytest.mark.integration
# @pytest.mark.slow
class TestiCloudInteractive:
    """Interactive integration tests that require manual intervention for 2FA."""

    def test_interactive_2fa_authentication(self):
        """Interactive test for 2FA authentication (requires manual input)."""
        if not KEYRING_AVAILABLE:
            pytest.skip("Keyring not available")

        # This test should only run when explicitly requested
        if not os.getenv('RUN_INTERACTIVE_TESTS'):
            pytest.skip("Interactive tests disabled - set RUN_INTERACTIVE_TESTS=1 to enable")

        config = get_config()
        setup_logging(config.get_log_level())  # Set up logging for interactive tests
        client = iCloudClient(config)

        print("\n🔐 Starting interactive 2FA test...")
        print("💡 This test requires manual 2FA code input")

        # Authenticate
        auth_result = client.authenticate()

        if not auth_result:
            pytest.fail("Initial authentication failed")

        if client.requires_2fa():
            print("\n📱 2FA code required!")
            print("💡 Check your Apple device for the 2FA code")

            # In a real interactive test, you might use input() here
            # For automated testing, this would need to be mocked
            code = input("Enter 2FA code: ")

            if code:
                result = client.handle_2fa(code)
                assert result, "2FA verification should succeed"
                print("✅ 2FA verification successful!")
            else:
                pytest.skip("No 2FA code provided")

        assert client.is_authenticated
        print("✅ Full authentication successful!")
