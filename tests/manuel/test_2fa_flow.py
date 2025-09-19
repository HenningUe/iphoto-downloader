#!/usr/bin/env python3
# Test the 2FA web server success page functionality - fully automated.

import os
import sys
import time
from pathlib import Path
from unittest.mock import patch
import pytest

# Add the shared package to path
sys.path.append(str(Path(__file__).parent.parent.parent / "shared" / "auth2fa" / "src"))

from auth2fa.web_server import TwoFAWebServer

@pytest.mark.manual
def test_2fa_flow():
    print(" Running fully automated 2FA flow test...")
    server = TwoFAWebServer(port_range=(8090, 8095))
    
    with patch('webbrowser.open') as mock_open:
        mock_open.return_value = True
        
        try:
            assert server.start(), "Server should start"
            print(f" Web server started at: {server.get_url()}")
            
            # Test browser opening (mocked)
            assert server.open_browser(), "Browser should open"
            assert mock_open.called, "webbrowser.open should be called"
            print(" Browser open call successful (mocked)")
            
            # Test state transitions
            server.set_state("waiting_for_code", "Test message")
            status = server.get_status()
            assert status['state'] == 'waiting_for_code'
            print(" State set correctly")
            
            # Test code submission
            result = server.submit_2fa_code("123456")
            assert result is True, "Code submission should succeed"
            
            status = server.get_status()
            assert status['state'] == 'authenticated'
            print(" Code submission successful")
            
            # Test invalid codes
            server.set_state("waiting_for_code", "Ready")
            result = server.submit_2fa_code("12345")  # Too short
            assert result is False, "Invalid code should be rejected"
            print(" Invalid codes rejected")
            
            print(" All automated tests passed!")
            
        finally:
            server.stop()
            print(" Web server stopped")

if __name__ == "__main__":
    test_2fa_flow()
