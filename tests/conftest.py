"""Pytest configuration and fixtures."""

import os
import tempfile

import pytest


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
        f.write("Initial log content\n")
        log_path = f.name

    yield log_path

    # Cleanup
    if os.path.exists(log_path):
        os.remove(log_path)


@pytest.fixture
def temp_session_dir(tmp_path):
    """Create a temporary session directory."""
    session_dir = tmp_path / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


@pytest.fixture(autouse=True)
def cleanup_active_sessions():
    """Clean up active sessions after each test."""
    yield
    # Import here to avoid circular dependencies
    from shellsidekick.mcp.session_state import active_sessions

    active_sessions.clear()
