#!/usr/bin/env python3
"""Test script to verify IPv4 detection."""

import socket


def get_local_ipv4():
    """Get the local IPv4 address of the current machine."""
    try:
        # Create a socket and connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Connect to Google's DNS server (doesn't actually send data)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            return local_ip
    except Exception as e:
        print(f"Could not determine local IP address: {e}")
        # Fallback to localhost
        return "127.0.0.1"


if __name__ == "__main__":
    ip = get_local_ipv4()
    print(f"Detected local IPv4 address: {ip}")

    # Test if we can bind to this IP
    test_port = 9999
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((ip, test_port))
            print(f"Successfully bound to {ip}:{test_port}")
    except Exception as e:
        print(f"Failed to bind to {ip}:{test_port}: {e}")
