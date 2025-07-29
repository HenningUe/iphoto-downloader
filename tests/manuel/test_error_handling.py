#!/usr/bin/env python3
import pytest
"""
Test script to verify the global exception handling implementation.
"""

from icloud_photo_sync.main import sanitize_error_message
import sys
sys.path.append('src/icloud_photo_sync/src')


@pytest.mark.manual
def test_error_sanitization():
    """Test that sensitive information is properly sanitized from error messages."""

    print("🧪 Testing Error Message Sanitization")
    print("=" * 50)

    # Test cases with sensitive information
    test_cases = [
        (ValueError("password=secret123 failed"), "password should be redacted"),
        (RuntimeError("token=abc123token in config"), "token should be redacted"),
        (Exception("user@example.com login failed"), "email should be redacted"),
        (OSError("C:\\Users\\testuser\\Documents\\file.txt not found"),
         "username path should be redacted"),
        (Exception("API key=xyz789 invalid"), "API key should be redacted"),
        (Exception("Very long error message " * 50), "long message should be truncated"),
    ]

    for i, (error, description) in enumerate(test_cases, 1):
        sanitized = sanitize_error_message(error)
        print(f"Test {i}: {description}")
        print(f"  Original: {str(error)}")
        print(f"  Sanitized: {sanitized}")
        passed_str = (
            '[REDACTED]' in sanitized
            or len(sanitized) < len(str(error)) or 'ValueError' in sanitized
        )
        print(
            f"  ✅ Passed: {passed_str}")
        print()

    print("✅ Error sanitization tests completed!")


if __name__ == "__main__":
    test_error_sanitization()
