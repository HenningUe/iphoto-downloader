#!/usr/bin/env python3
"""
Simple workflow validation script to check basic structure.
"""

import sys
from pathlib import Path

def validate_workflow():
    """Validate the GitHub Actions workflow file."""
    workflow_path = Path('.github/workflows/release.yml')
    
    if not workflow_path.exists():
        print(f"❌ Workflow file not found: {workflow_path}")
        return False
    
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("✅ Workflow file is readable")
        
        # Check if we have the required jobs
        required_items = [
            'package-snap:',
            'publish-to-snap:',
            'snapcraft',
            'snapcraft.yaml'
        ]
        
        for item in required_items:
            if item in content:
                print(f"✅ Found: {item}")
            else:
                print(f"❌ Missing: {item}")
                return False
        
        # Check if we don't have old APT jobs
        old_items = ['package-apt:', 'publish-to-apt:', 'dpkg-deb']
        for item in old_items:
            if item in content:
                print(f"❌ Found old item that should be removed: {item}")
                return False
            else:
                print(f"✅ Old item properly removed: {item}")
        
        print("✅ All validations passed!")
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = validate_workflow()
    sys.exit(0 if success else 1)
