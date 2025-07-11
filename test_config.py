#!/usr/bin/env python3
"""Test script to verify the polymorphic config behavior."""

import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from icloud_photo_sync.config import get_config, KEYRING_AVAILABLE, KeyringConfig, EnvOnlyConfig


def test_config_factory():
    """Test that the Config factory returns the correct type."""
    print("🧪 Testing Config Factory")
    print("=" * 25)
    
    config = get_config()
    
    print(f"Keyring available: {KEYRING_AVAILABLE}")
    print(f"Config type: {type(config).__name__}")
    
    if KEYRING_AVAILABLE:
        assert isinstance(config, KeyringConfig), "Should return KeyringConfig when keyring is available"
        print("✅ KeyringConfig correctly instantiated")
    else:
        assert isinstance(config, EnvOnlyConfig), "Should return EnvOnlyConfig when keyring is not available"
        print("✅ EnvOnlyConfig correctly instantiated")
    
    print(f"Config details: {config}")
    
    # Test polymorphic behavior
    print("\n🔄 Testing Polymorphic Behavior")
    print("=" * 32)
    
    # All configs should have these methods
    methods_to_test = [
        'store_credentials',
        'delete_credentials', 
        'has_stored_credentials',
        'ensure_sync_directory',
        'get_log_level'
    ]
    
    for method_name in methods_to_test:
        assert hasattr(config, method_name), f"Config should have {method_name} method"
        print(f"✅ {method_name} method available")
    
    # Test that credential methods work (even if they return False for env-only)
    print(f"\nCredential storage support: {config.store_credentials('test', 'test')}")
    print(f"Has stored credentials: {config.has_stored_credentials()}")
    
    print("\n✅ All tests passed! Polymorphic config system working correctly.")


if __name__ == "__main__":
    try:
        test_config_factory()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
