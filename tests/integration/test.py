from icloud_photo_sync.config import get_config
from icloud_photo_sync.icloud_client import iCloudClient
from icloud_photo_sync.logger import setup_logging


def test_interactive_2fa_authentication():
    """Interactive test for 2FA authentication (requires manual input)."""

    config = get_config()
    setup_logging(config.get_log_level())  # Set up logging for interactive tests
    client = iCloudClient(config)

    print("\n🔐 Starting interactive 2FA test...")
    print("💡 This test requires manual 2FA code input")

    # Authenticate
    auth_result = client.authenticate()

    if client.requires_2fa():
        print("\n📱 2FA code required!")
        print("💡 Check your Apple device for the 2FA code")

        # In a real interactive test, you might use input() here
        # For automated testing, this would need to be mocked
        code = input("Enter 2FA code: ")

        result = client.handle_2fa_validation(code)
        assert result, "2FA verification should succeed"
        print("✅ 2FA verification successful!")

    assert client.is_authenticated
    print("✅ Full authentication successful!")


if __name__ == "__main__":
    # Run the interactive test
    test_interactive_2fa_authentication()
