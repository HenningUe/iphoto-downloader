#!/usr/bin/env python3
"""
Simple import test to verify the auth2fa cloud test can be imported.
"""
import sys
import os

# Add auth2fa to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

try:
    print("Testing import...")
    from test_auth2fa_cloud import test_auth2fa_cloud_integration
    print("✅ Import successful!")
    print("✅ The import issue has been fixed!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
except Exception as e:
    print(f"⚠️  Other error: {e}")