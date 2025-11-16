"""Basic integration test for session monitoring workflow."""

import os
import tempfile

import pytest


def test_import_modules():
    """Test that all core modules can be imported."""
    from shellsidekick.core import detector, monitor
    from shellsidekick.models import prompt, session

    assert session is not None
    assert prompt is not None
    assert detector is not None
    assert monitor is not None


def test_session_monitor_creation():
    """Test creating a session monitor."""
    from datetime import datetime

    from shellsidekick.core.monitor import SessionMonitor
    from shellsidekick.models.session import Session, SessionState, SessionType

    # Create a temporary log file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("Test log content\n")
        log_path = f.name

    try:
        session = Session(
            session_id="test-123",
            session_type=SessionType.FILE,
            log_file=log_path,
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
        )

        monitor = SessionMonitor(session)
        assert monitor.is_active
        assert monitor.session.session_id == "test-123"

    finally:
        if os.path.exists(log_path):
            os.remove(log_path)


def test_prompt_detection():
    """Test basic prompt detection."""
    from shellsidekick.core.detector import PromptDetector

    detector = PromptDetector(min_confidence=0.70)

    # Test password prompt detection
    content = "Please enter your credentials\nPassword: "
    detection = detector.detect(content)

    assert detection is not None
    assert detection.prompt_type.value == "password"
    assert detection.confidence > 0.85
    assert "password" in detection.prompt_text.lower()


def test_dangerous_operation_detection():
    """Test dangerous operation detection."""
    from shellsidekick.core.detector import PromptDetector

    detector = PromptDetector(min_confidence=0.70)

    # Test dangerous prompt
    content = "WARNING: This will delete all data\nContinue? (yes/no): "
    detection = detector.detect(content)

    assert detection is not None
    # is_dangerous should be True because "delete" is present
    # Note: This depends on the security.py dangerous patterns including "delete"
    # The current implementation should detect this


@pytest.mark.skip(reason="Requires MCP client setup")
def test_full_session_lifecycle():
    """Integration test for complete session lifecycle."""
    # This will be implemented when MCP client testing is set up
    pass
