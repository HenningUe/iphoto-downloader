"""Test automation utilities to eliminate manual interactions during automated test runs."""

import os
import typing as t
from unittest.mock import Mock


def is_automated_test_environment() -> bool:
    """Check if we're running in an automated test environment.

    Returns:
        True if running in pytest or CI environment, False otherwise
    """
    # Check for pytest environment variables
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return True
    if os.environ.get("_PYTEST_RAISE"):
        return True

    # Check for CI environment variables
    ci_indicators = [
        "CI",
        "CONTINUOUS_INTEGRATION",
        "GITHUB_ACTIONS",
        "JENKINS_URL",
        "TRAVIS",
        "CIRCLECI",
        "GITLAB_CI",
        "APPVEYOR",
        "TF_BUILD",  # Azure DevOps
    ]

    for indicator in ci_indicators:
        if os.environ.get(indicator):
            return True

    return False


def automated_input(prompt: str, default_response: str = "y") -> str:
    """Replacement for input() that returns automated responses in test environments.

    Args:
        prompt: The prompt that would be shown to user
        default_response: Default response to return in automated mode

    Returns:
        User input in manual mode, default_response in automated mode
    """
    if is_automated_test_environment():
        print(f"{prompt}{default_response} (automated)")
        return default_response
    else:
        return input(prompt)


def automated_input_with_mapping(prompt: str, response_mapping: dict[str, str]) -> str:
    """Input replacement with specific responses based on prompt content.

    Args:
        prompt: The prompt shown to user
        response_mapping: Dict mapping prompt keywords to responses

    Returns:
        Mapped response in automated mode, user input in manual mode
    """
    if is_automated_test_environment():
        prompt_lower = prompt.lower()

        # Find matching response based on prompt content
        for keyword, response in response_mapping.items():
            if keyword.lower() in prompt_lower:
                print(f"{prompt}{response} (automated)")
                return response

        # Default to "y" if no specific mapping found
        print(f"{prompt}y (automated - default)")
        return "y"
    else:
        return input(prompt)


def mock_browser_open() -> Mock:
    """Create a mock for browser opening operations.

    Returns:
        Mock object that simulates successful browser opening
    """
    mock_open = Mock(return_value=True)
    mock_open.__name__ = "mock_browser_open"
    return mock_open


def should_skip_browser_operations() -> bool:
    """Check if browser operations should be skipped.

    Returns:
        True if browser operations should be skipped (automated environment)
    """
    return is_automated_test_environment()


class AutomatedTestContext:
    """Context manager for automated test operations."""

    def __init__(self, mock_browser: bool = True, mock_input: bool = True):
        self.mock_browser = mock_browser
        self.mock_input = mock_input
        self.original_functions: dict[str, t.Any] = {}

    def __enter__(self):
        """Enter automated test context."""
        if is_automated_test_environment():
            # Store original functions if needed for restoration
            if self.mock_browser:
                try:
                    import webbrowser

                    self.original_functions["webbrowser_open"] = webbrowser.open
                    webbrowser.open = mock_browser_open()
                except ImportError:
                    pass

            if self.mock_input:
                import builtins

                self.original_functions["builtin_input"] = builtins.input
                builtins.input = lambda prompt: automated_input(str(prompt), "y")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit automated test context and restore functions."""
        # Restore original functions
        for name, func in self.original_functions.items():
            if name == "webbrowser_open":
                import webbrowser

                webbrowser.open = func
            elif name == "builtin_input":
                import builtins

                builtins.input = func

        self.original_functions.clear()
