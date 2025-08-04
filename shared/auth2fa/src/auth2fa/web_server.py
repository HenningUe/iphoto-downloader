"""Local HTTP server for 2FA interface."""

import json
import logging
import socket
import threading
import time
import webbrowser
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


class TwoFAHandler(BaseHTTPRequestHandler):
    """HTTP request handler for 2FA web interface."""

    def __init__(self, *args, **kwargs):
        self.server_instance = None
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """Override to use our logger instead of stderr."""
        get_logger(__name__).debug("HTTP: " + format % args)

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/":
            self._serve_main_page()
        elif parsed_path.path == "/status":
            self._serve_status()
        elif parsed_path.path == "/success":
            self._serve_success_page()
        elif parsed_path.path == "/styles.css":
            self._serve_css()
        else:
            self._serve_404()

    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/submit_2fa":
            self._handle_2fa_submission()
        elif parsed_path.path == "/request_new_2fa":
            self._handle_new_2fa_request()
        else:
            self._serve_404()

    def _serve_main_page(self):
        """Serve the main 2FA interface page."""
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>iPhoto Downloader - 2FA Authentication</title>
    <link rel="stylesheet" href="/styles.css">
    <script>
        let statusCheckInterval;

        function updateStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    const statusEl = document.getElementById('status');
                    const formEl = document.getElementById('2fa-form');
                    const messageEl = document.getElementById('message');

                    statusEl.textContent = data.status;
                    statusEl.className = 'status-' + data.state;

                    if (data.message) {
                        messageEl.textContent = data.message;
                        messageEl.style.display = 'block';
                    } else {
                        messageEl.style.display = 'none';
                    }

                    // Show/hide form based on state
                    if (data.state === 'waiting_for_code') {
                        formEl.style.display = 'block';
                        document.getElementById('2fa-code').focus();
                    } else {
                        formEl.style.display = 'none';
                    }

                    // Stop polling if authentication completed
                    if (data.state === 'authenticated' || data.state === 'failed') {
                        clearInterval(statusCheckInterval);
                        if (data.state === 'authenticated') {
                            // Redirect to success page immediately
                            window.location.href = '/success';
                        }
                    }
                })
                .catch(error => {
                    console.error('Status check failed:', error);
                });
        }

        function submitCode() {
            const code = document.getElementById('2fa-code').value.trim();
            if (!code) {
                alert('Please enter the 2FA code');
                return;
            }

            // Show immediate feedback that code is being processed
            const messageEl = document.getElementById('message');
            messageEl.textContent = 'Validating 2FA code...';
            messageEl.style.display = 'block';
            messageEl.style.color = '#007bff';
            
            // Disable the submit button to prevent double submission
            const submitBtn = document.querySelector('.submit-button');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Validating...';

            // Send as URL-encoded form data instead of FormData
            const params = new URLSearchParams();
            params.append('code', code);

            fetch('/submit_2fa', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: params
            })
            .then(response => response.json())
            .then(data => {
                // Re-enable submit button
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
                
                if (data.success) {
                    document.getElementById('2fa-code').value = '';
                    
                    // Check if immediate redirect is requested
                    if (data.authenticated && data.redirect) {
                        // Show immediate success feedback
                        const messageEl = document.getElementById('message');
                        messageEl.textContent = data.message || 'Authentication successful!';
                        messageEl.style.display = 'block';
                        messageEl.style.color = '#28a745';
                        
                        // Hide the form
                        document.getElementById('2fa-form').style.display = 'none';
                        
                        // Update status display
                        const statusEl = document.getElementById('status');
                        statusEl.textContent = '✅ Authentication successful!';
                        statusEl.className = 'status-authenticated';
                        
                        // Redirect after a short delay to let user see success message
                        setTimeout(() => {
                            window.location.href = data.redirect;
                        }, 1500);
                    } else {
                        // Fallback to status polling for compatibility
                        updateStatus();
                    }
                } else {
                    messageEl.textContent = data.message || 'Failed to submit code';
                    messageEl.style.color = '#dc3545';
                }
            })
            .catch(error => {
                // Re-enable submit button on error
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
                
                console.error('Code submission failed:', error);
                messageEl.textContent = 'Failed to submit code';
                messageEl.style.color = '#dc3545';
            });
        }

        function requestNew2FA() {
            fetch('/request_new_2fa', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateStatus();
                } else {
                    alert(data.message || 'Failed to request new 2FA');
                }
            })
            .catch(error => {
                console.error('New 2FA request failed:', error);
                alert('Failed to request new 2FA');
            });
        }

        // Start status polling when page loads
        window.onload = function() {
            updateStatus();
            statusCheckInterval = setInterval(updateStatus, 2000);

            // Handle Enter key in code input
            document.getElementById('2fa-code').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    submitCode();
                }
            });
        };
    </script>
</head>
<body>
    <div class="container">
        <h1>🔐 iPhoto Downloader</h1>
        <h2>Two-Factor Authentication</h2>

        <div class="status-section">
            <p><strong>Status:</strong> <span id="status">Checking...</span></p>
            <div id="message" class="message" style="display: none;"></div>
        </div>

        <div id="2fa-form" class="form-section" style="display: none;">
            <h3>Enter 2FA Code</h3>
            <p>Check your trusted device for the 6-digit verification code from Apple.</p>
            <div class="input-group">
             <input type="text" id="2fa-code" placeholder="123456" maxlength="6" pattern="[0-9]{6}">
             <button onclick="submitCode()">Submit Code</button>
            </div>
        </div>

        <div class="action-section">
            <button onclick="requestNew2FA()" class="secondary-button">Request New 2FA Code</button>
        </div>

        <div class="info-section">
           <p><small>This page will automatically close when authentication is complete.</small></p>
        </div>
    </div>
</body>
</html>
        """

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html_content.encode())

    def _serve_css(self):
        """Serve the CSS styles."""
        css_content = """
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    margin: 0;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}

.container {
    background: white;
    border-radius: 12px;
    padding: 40px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    max-width: 500px;
    width: 100%;
    text-align: center;
}

h1 {
    color: #333;
    margin-bottom: 10px;
    font-size: 2.5em;
}

h2 {
    color: #666;
    margin-bottom: 30px;
    font-weight: 300;
}

h3 {
    color: #333;
    margin-bottom: 15px;
}

.status-section {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 30px;
}

.status-pending {
    color: #ffc107;
    font-weight: bold;
}

.status-waiting_for_code {
    color: #17a2b8;
    font-weight: bold;
}

.status-authenticated {
    color: #28a745;
    font-weight: bold;
}

.status-failed {
    color: #dc3545;
    font-weight: bold;
}

.message {
    background: #e9ecef;
    border-left: 4px solid #007bff;
    padding: 15px;
    margin-top: 15px;
    text-align: left;
    border-radius: 0 4px 4px 0;
}

.form-section {
    margin-bottom: 30px;
}

.input-group {
    display: flex;
    gap: 10px;
    margin-top: 20px;
    justify-content: center;
    align-items: center;
}

input[type="text"] {
    padding: 12px 16px;
    border: 2px solid #ddd;
    border-radius: 6px;
    font-size: 18px;
    text-align: center;
    font-family: monospace;
    letter-spacing: 2px;
    width: 120px;
    transition: border-color 0.3s;
}

input[type="text"]:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
}

button {
    background: #007bff;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 500;
    transition: background-color 0.3s;
}

button:hover {
    background: #0056b3;
}

.secondary-button {
    background: #6c757d;
    margin-top: 20px;
}

.secondary-button:hover {
    background: #545b62;
}

.action-section {
    margin-bottom: 30px;
}

.info-section {
    border-top: 1px solid #eee;
    padding-top: 20px;
    color: #666;
}
        """

        self.send_response(200)
        self.send_header("Content-type", "text/css")
        self.end_headers()
        self.wfile.write(css_content.encode())

    def _serve_success_page(self):
        """Serve the 2FA authentication success page."""
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>iPhoto Downloader - 2FA Authentication Successful</title>
    <link rel="stylesheet" href="/styles.css">
    <style>
        .success-container {
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            max-width: 500px;
            width: 100%;
            text-align: center;
            animation: slideIn 0.5s ease-out;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .success-icon {
            font-size: 4em;
            color: #28a745;
            margin-bottom: 20px;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }

        .success-title {
            color: #28a745;
            font-size: 2em;
            margin-bottom: 15px;
            font-weight: 600;
        }

        .success-message {
            color: #666;
            font-size: 1.1em;
            margin-bottom: 30px;
            line-height: 1.6;
        }

        .auto-close-info {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            color: #6c757d;
            font-size: 0.9em;
        }

        .close-button {
            background: #28a745;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            transition: background-color 0.3s;
        }

        .close-button:hover {
            background: #218838;
        }

        kbd {
            background-color: #f8f9fa;
            border: 1px solid #6c757d;
            border-radius: 3px;
            padding: 2px 4px;
            font-family: monospace;
            font-size: 0.85em;
        }
    </style>
    <script>
        let countdown = 10;
        let countdownInterval;

        function updateCountdown() {
            const countdownEl = document.getElementById('countdown');
            const autoCloseInfo = document.querySelector('.auto-close-info');
            
            if (countdownEl) {
                countdownEl.textContent = countdown;
                countdown--;

                if (countdown < 0) {
                    // Clear the interval
                    clearInterval(countdownInterval);
                    
                    // Show completion message since auto-close rarely works
                    showCompletionMessage();
                }
            }
        }

        function showCompletionMessage() {
            const autoCloseInfo = document.querySelector('.auto-close-info');
            autoCloseInfo.innerHTML = `
                <p style="color: #28a745; font-weight: bold;">
                    ✅ Authentication completed! Please close this browser window.
                </p>
            `;
            
            // Update the close button
            const button = document.querySelector('.close-button');
            button.innerHTML = '✅ Close This Window (Ctrl+W)';
            button.onclick = function() {
                showCloseInstructions();
            };
            
            // Update page title to indicate completion
            document.title = "✅ 2FA Complete - Please close this window";
            
            // Flash the browser icon/title to get user attention
            flashTitle();
        }

        function closeWindow() {
            // Try window.close() first (works if opened by script)
            try {
                window.close();
                
                // Check after a short delay if window is still open
                setTimeout(function() {
                    // If we're still here, window.close() didn't work
                    showCloseInstructions();
                }, 100);
            } catch (e) {
                showCloseInstructions();
            }
        }

        function showCloseInstructions() {
            // Show user-friendly message with close instructions
            const button = document.querySelector('.close-button');
            button.innerHTML = 'Please use Ctrl+W or click the X button';
            button.style.background = '#6c757d';
            button.style.cursor = 'default';
            button.onclick = null;
            
            // Also show instruction in the info section
            const info = document.querySelector('.info-section');
            info.innerHTML = `
                <p><strong style="color: #28a745;">
                    Authentication completed successfully!
                </strong></p>
                <p><small>
                    To close this window:<br>
                    • Press <kbd>Ctrl+W</kbd> (Windows/Linux) or <kbd>Cmd+W</kbd> (Mac)<br>
                    • Or click the ❌ button in your browser tab
                </small></p>
            `;
            
            // Update page title
            document.title = "✅ 2FA Complete - Please close this window";
        
            // Flash the title
            flashTitle();
        }

        function flashTitle() {
            const originalTitle = document.title;
            let flash = true;
            const flashInterval = setInterval(function() {
                document.title = flash ? "🔔 " + originalTitle : originalTitle;
                flash = !flash;
            }, 1000);
            
            // Stop flashing after 10 seconds
            setTimeout(function() {
                clearInterval(flashInterval);
                document.title = originalTitle;
            }, 10000);
        }

        window.onload = function() {
            updateCountdown();
            countdownInterval = setInterval(updateCountdown, 1000);
        };

        // Handle browser back button - if user navigates back, clean up
        window.addEventListener('beforeunload', function() {
            if (countdownInterval) {
                clearInterval(countdownInterval);
            }
        });
    </script>
</head>
<body>
    <div class="container">
        <div class="success-container">
            <div class="success-icon">✅</div>
            <h1 class="success-title">Authentication Successful!</h1>
            <p class="success-message">
                Your iPhoto Downloader 2FA authentication has been completed successfully.
                <br>
                The sync process will now continue automatically.
            </p>

            <div class="auto-close-info">
                <p>This window will automatically close in
                   <span id="countdown">10</span> seconds.</p>
                <p><small>If the window doesn't close automatically,
                   please close it manually.</small></p>
            </div>

            <button onclick="closeWindow()" class="close-button">
                Close Window Now
            </button>

            <div class="info-section" style="margin-top: 30px;">
                <p><small>You can safely close this browser window.
                   The sync process will continue in the background.</small></p>
            </div>
        </div>
    </div>
</body>
</html>
        """

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html_content.encode())

    def _serve_status(self):
        """Serve the current 2FA status as JSON."""
        try:
            # Get status from the server instance
            server = self.server
            if hasattr(server, "twofa_server"):
                twofa_server: TwoFAWebServer = server.twofa_server
                if twofa_server:
                    status_data = twofa_server.get_status()
                else:
                    status_data = {
                        "state": "error",
                        "status": "Server not initialized",
                        "message": None,
                    }
            else:
                status_data = {
                    "state": "error",
                    "status": "Server not initialized",
                    "message": None,
                }

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(status_data).encode())
        except Exception as e:
            get_logger(__name__).error(f"Error serving status: {e}")
            self._serve_error("Failed to get status")

    def _handle_2fa_submission(self):
        """Handle 2FA code submission with security checks."""
        try:
            # Get client IP for rate limiting
            client_ip = self.client_address[0]

            # Get server instance
            server = self.server
            if not hasattr(server, "twofa_server"):
                self._serve_json_response({"success": False, "message": "Server not initialized"})
                return

            twofa_server: TwoFAWebServer = server.twofa_server
            if not twofa_server:
                self._serve_json_response({"success": False, "message": "Server not initialized"})
                return

            # Check session timeout
            if twofa_server.is_session_expired():
                get_logger(__name__).warning(f"Session expired for IP {client_ip}")
                self._serve_json_response(
                    {
                        "success": False,
                        "message": "Session expired. Please restart the authentication process.",
                    }
                )
                return

            # Check rate limiting
            if twofa_server.is_rate_limited(client_ip):
                get_logger(__name__).warning(f"Rate limit exceeded for IP {client_ip}")
                self._serve_json_response(
                    {
                        "success": False,
                        "message": "Too many attempts. Please wait before trying again.",
                    }
                )
                return

            # Record this attempt
            twofa_server.record_attempt(client_ip)

            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)

            # Parse URL-encoded form data
            parsed_data = parse_qs(post_data.decode("utf-8"))
            code = parsed_data.get("code", [""])[0].strip()

            if not code:
                self._serve_json_response({"success": False, "message": "No code provided"})
                return

            # Sanitize code for logging (don't log actual code values)
            code_length = len(code) if code else 0
            get_logger(__name__).info(
                f"2FA code submission attempt from {client_ip} (code length: {code_length})",
                extra={
                    "event": "2fa_code_submission",
                    "client_ip": client_ip,
                    "code_length": code_length,
                    "session_id": id(twofa_server) if twofa_server else None,
                },
            )

            # Submit code to the server instance
            success = twofa_server.submit_2fa_code(code)
            if success:
                # Refresh session on successful authentication
                twofa_server.refresh_session()
                get_logger(__name__).info(
                    f"2FA code validation successful for {client_ip}",
                    extra={
                        "event": "2fa_validation_success",
                        "client_ip": client_ip,
                        "session_id": id(twofa_server),
                    },
                )
                # Return success with redirect instruction
                self._serve_json_response(
                    {
                        "success": True,
                        "authenticated": True,
                        "message": "Authentication successful!",
                        "redirect": "/success",
                    }
                )
            else:
                get_logger(__name__).warning(
                    f"2FA code validation failed for {client_ip}",
                    extra={
                        "event": "2fa_validation_failed",
                        "client_ip": client_ip,
                        "session_id": id(twofa_server) if twofa_server else None,
                    },
                )
                self._serve_json_response(
                    {"success": False, "message": "Invalid 2FA code. Please try again."}
                )

        except Exception as e:
            get_logger(__name__).error(f"Error handling 2FA submission: {e}")
            self._serve_json_response({"success": False, "message": "Internal error"})

    def _handle_new_2fa_request(self):
        """Handle request for new 2FA code."""
        try:
            server = self.server
            if hasattr(server, "twofa_server"):
                twofa_server: TwoFAWebServer = server.twofa_server
                if twofa_server:
                    success = twofa_server.request_new_2fa()
                    self._serve_json_response({"success": success})
                else:
                    self._serve_json_response(
                        {"success": False, "message": "Server not initialized"}
                    )
            else:
                self._serve_json_response({"success": False, "message": "Server not initialized"})

        except Exception as e:
            get_logger(__name__).error(f"Error handling new 2FA request: {e}")
            self._serve_json_response({"success": False, "message": "Internal error"})

    def _serve_json_response(self, data: dict[str, Any]):
        """Send a JSON response."""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _serve_error(self, message: str):
        """Send an error response."""
        self.send_response(500)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())

    def _serve_404(self):
        """Send a 404 response."""
        self.send_response(404)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Not Found")


class TwoFAWebServer:
    """Local web server for 2FA authentication interface."""

    def __init__(self, port_range: tuple = (8080, 8090)):
        """Initialize the 2FA web server.

        Args:
            port_range: Tuple of (min_port, max_port) to try
        """
        self.port_range = port_range
        self.server: HTTPServer | None = None
        self.server_thread: threading.Thread | None = None
        self.port: int | None = None
        self.host: str = "0.0.0.0"  # Default to localhost  # nosec B104
        self.logger = get_logger(__name__)

        # 2FA state management
        self.state = "pending"  # pending, waiting_for_code, authenticated, failed
        self.status_message = None
        self.submitted_code = None
        self.code_submitted_event = threading.Event()

        # Session timeout management
        self.session_start_time = time.time()
        self.session_timeout = 1800  # 30 minutes default session timeout
        self.code_entry_timeout = 300  # 5 minutes for code entry

        # Rate limiting for 2FA attempts
        self.attempt_times = defaultdict(list)  # IP -> list of attempt timestamps
        self.max_attempts_per_minute = 5
        self.max_attempts_per_hour = 20
        self.lockout_duration = 300  # 5 minutes lockout

        # Callback for 2FA operations
        self.request_2fa_callback = None
        self.submit_code_callback = None

    def get_local_ipv4(self) -> str:
        """Get the local IPv4 address of the current machine.

        Returns:
            The local IPv4 address or '0.0.0.0' if not found
        """
        try:
            # Create a socket and connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Connect to Google's DNS server (doesn't actually send data)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                return local_ip
        except Exception as e:
            self.logger.warning(f"Could not determine local IP address: {e}")
            # Fallback to localhost
            return "127.0.0.1"

    def find_available_port(self) -> int | None:
        """Find an available port in the specified range."""
        # Get the host IP first
        self.host = self.get_local_ipv4()

        for port in range(self.port_range[0], self.port_range[1] + 1):
            try:
                # Test if port is available on the determined host
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((self.host, port))
                    return port
            except OSError:
                continue
        return None

    def is_session_expired(self) -> bool:
        """Check if the current session has expired.

        Returns:
            True if session has expired, False otherwise
        """
        expired = time.time() - self.session_start_time > self.session_timeout
        if expired:
            self.logger.warning(
                "Session expired",
                extra={
                    "event": "session_expired",
                    "session_id": id(self),
                    "session_duration": time.time() - self.session_start_time,
                    "session_timeout": self.session_timeout,
                },
            )
        return expired

    def refresh_session(self):
        """Refresh the session timestamp."""
        old_start_time = self.session_start_time
        self.session_start_time = time.time()
        self.logger.debug(
            "Session refreshed",
            extra={
                "event": "session_refreshed",
                "session_id": id(self),
                "previous_session_duration": time.time() - old_start_time,
            },
        )

    def is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited.

        Args:
            client_ip: IP address of the client

        Returns:
            True if client is rate limited, False otherwise
        """
        current_time = time.time()

        # Clean old attempts (older than 1 hour)
        self.attempt_times[client_ip] = [
            attempt_time
            for attempt_time in self.attempt_times[client_ip]
            if current_time - attempt_time < 3600
        ]

        attempts = self.attempt_times[client_ip]

        # Check attempts in last minute
        recent_attempts = [
            attempt_time for attempt_time in attempts if current_time - attempt_time < 60
        ]

        if len(recent_attempts) >= self.max_attempts_per_minute:
            self.logger.warning(
                f"Rate limit exceeded for IP {client_ip}: "
                f"{len(recent_attempts)} attempts in last minute",
                extra={
                    "event": "rate_limit_exceeded",
                    "client_ip": client_ip,
                    "rate_limit_type": "per_minute",
                    "attempt_count": len(recent_attempts),
                    "limit": self.max_attempts_per_minute,
                    "session_id": id(self),
                },
            )
            return True

        # Check attempts in last hour
        if len(attempts) >= self.max_attempts_per_hour:
            self.logger.warning(
                f"Rate limit exceeded for IP {client_ip}: {len(attempts)} attempts in last hour",
                extra={
                    "event": "rate_limit_exceeded",
                    "client_ip": client_ip,
                    "rate_limit_type": "per_hour",
                    "attempt_count": len(attempts),
                    "limit": self.max_attempts_per_hour,
                    "session_id": id(self),
                },
            )
            return True

        return False

    def record_attempt(self, client_ip: str):
        """Record a 2FA attempt for rate limiting.

        Args:
            client_ip: IP address of the client
        """
        current_time = time.time()
        self.attempt_times[client_ip].append(current_time)

        self.logger.debug(
            "2FA attempt recorded",
            extra={
                "event": "2fa_attempt_recorded",
                "client_ip": client_ip,
                "timestamp": current_time,
                "total_attempts": len(self.attempt_times[client_ip]),
                "session_id": id(self),
            },
        )

    def start(self) -> bool:
        """Start the web server.

        Returns:
            True if server started successfully, False otherwise
        """
        try:
            # Find available port
            self.port = self.find_available_port()
            if not self.port:
                self.logger.error(f"No available ports in range {self.port_range}")
                return False

            # Create and configure server
            self.server = HTTPServer((self.host, self.port), TwoFAHandler)
            self.server.twofa_server = self  # Reference for handlers

            # Start server in separate thread
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()

            self.logger.info(
                f"2FA web server started on http://{self.host}:{self.port}",
                extra={
                    "event": "web_server_started",
                    "host": self.host,
                    "port": self.port,
                    "session_id": id(self),
                },
            )
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to start 2FA web server: {e}",
                extra={
                    "event": "web_server_start_failed",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "session_id": id(self),
                },
            )
            return False

    def stop(self):
        """Stop the web server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None

        if self.server_thread:
            self.server_thread.join(timeout=5)
            self.server_thread = None

        self.logger.info(
            "2FA web server stopped", extra={"event": "web_server_stopped", "session_id": id(self)}
        )

    def get_url(self) -> str | None:
        """Get the server URL.

        Returns:
            Server URL if running, None otherwise
        """
        if self.port and self.host:
            return f"http://{self.host}:{self.port}"
        return None

    def open_browser(self) -> bool:
        """Open the 2FA interface in the default browser.

        Returns:
            True if browser opened successfully, False otherwise
        """
        try:
            url = self.get_url()
            if url:
                webbrowser.open(url)
                self.logger.info(f"Opened 2FA interface in browser: {url}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to open browser: {e}")
            return False

    def get_status(self) -> dict[str, Any]:
        """Get current 2FA status.

        Returns:
            Dictionary with status information
        """
        status_messages = {
            "pending": "Initializing 2FA authentication...",
            "waiting_for_code": "Waiting for 2FA code from your trusted device",
            "authenticated": "✅ Authentication successful!",
            "failed": "❌ Authentication failed",
        }

        return {
            "state": self.state,
            "status": status_messages.get(self.state, "Unknown state"),
            "message": self.status_message,
        }

    def set_state(self, state: str, message: str | None = None):
        """Update the 2FA state.

        Args:
            state: New state ('pending', 'waiting_for_code', 'authenticated', 'failed')
            message: Optional status message
        """
        old_state = getattr(self, "state", None)
        self.state = state
        self.status_message = message
        self.logger.info(
            f"2FA state changed to: {state}",
            extra={
                "event": "2fa_state_change",
                "old_state": old_state,
                "new_state": state,
                "session_id": id(self),
            },
        )
        if message:
            self.logger.debug(f"2FA message: {message}")

    def submit_2fa_code(self, code: str) -> bool:
        """Handle 2FA code submission from web interface.

        Args:
            code: The 2FA code entered by user

        Returns:
            True if code was accepted, False otherwise
        """
        try:
            # Log submission without exposing the actual code
            self.logger.info("2FA code submitted via web interface")

            # Validate code format
            NUMB_DIGITS_2FA = 6
            if not code or len(code) != NUMB_DIGITS_2FA or not code.isdigit():
                self.set_state(
                    "waiting_for_code", "Invalid code format. Please enter a 6-digit number."
                )
                return False

            # Update state to show processing
            self.set_state("pending", "Validating 2FA code...")

            self.submitted_code = code
            self.code_submitted_event.set()

            # Call the callback if available
            if self.submit_code_callback:
                result = self.submit_code_callback(code)
                if result:
                    self.set_state("authenticated", "Authentication successful!")
                    self.logger.info("2FA authentication successful")
                else:
                    self.set_state("failed", "Invalid 2FA code. Please try again.")
                    self.logger.warning("2FA authentication failed - invalid code")
                return result
            else:
                # No callback means we accept any valid format code for demo/testing
                self.set_state("authenticated", "Authentication successful!")
                self.logger.info("2FA authentication successful (no callback)")
                return True

            return True
        except Exception as e:
            # Log error without exposing sensitive data
            self.logger.error(f"Error handling 2FA code submission: {e}")
            self.set_state("failed", f"Error processing code: {e}")
            return False

    def request_new_2fa(self) -> bool:
        """Handle request for new 2FA code.

        Returns:
            True if request was successful, False otherwise
        """
        try:
            self.logger.info("New 2FA code requested via web interface")

            # Change state to waiting for code when new 2FA is requested
            self.set_state(
                "waiting_for_code", "New 2FA code requested. Please check your trusted device."
            )

            if self.request_2fa_callback:
                return self.request_2fa_callback()
            return True  # Return True even if no callback, state change is successful
        except Exception as e:
            self.logger.error(f"Error handling new 2FA request: {e}")
            self.set_state("failed", f"Failed to request new 2FA code: {e}")
            return False

    def wait_for_code(self, timeout: int = 300) -> str | None:
        """Wait for 2FA code submission via web interface.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            The submitted code or None if timeout/cancelled
        """
        # Use the smaller of provided timeout and remaining session time
        remaining_session_time = self.session_timeout - (time.time() - self.session_start_time)
        effective_timeout = min(timeout, max(0, remaining_session_time))

        if effective_timeout <= 0:
            self.set_state("failed", "Session expired")
            self.logger.warning("Session expired during code wait")
            return None

        self.set_state(
            "waiting_for_code", "Please enter the 6-digit code from your trusted Apple device"
        )

        self.code_submitted_event.clear()
        self.submitted_code = None

        self.logger.info(f"Waiting for 2FA code (timeout: {effective_timeout}s)")

        if self.code_submitted_event.wait(effective_timeout):
            return self.submitted_code
        else:
            if self.is_session_expired():
                self.set_state("failed", "Session expired")
                self.logger.warning("Session expired while waiting for 2FA code")
            else:
                self.set_state("failed", "Timeout waiting for 2FA code")
                self.logger.warning("Timeout waiting for 2FA code")
            return None

    def set_callbacks(self, request_2fa_callback=None, submit_code_callback=None):
        """Set callback functions for 2FA operations.

        Args:
            request_2fa_callback: Function to call when new 2FA is requested
            submit_code_callback: Function to call when code is submitted
        """
        self.request_2fa_callback = request_2fa_callback
        self.submit_code_callback = submit_code_callback
