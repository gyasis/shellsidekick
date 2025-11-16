"""Unit tests for SessionMonitor."""

import os
import time
import uuid
from datetime import datetime
from pathlib import Path

import pytest

from shellsidekick.core.monitor import SessionMonitor
from shellsidekick.models.session import Session, SessionState, SessionType


class TestSessionMonitorInit:
    """Test SessionMonitor initialization."""

    def test_init_with_session(self, tmp_path):
        """Test initialization with a valid session."""
        log_file = tmp_path / "test.log"
        log_file.write_text("Initial content")

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)

        assert monitor.session == session
        assert monitor.is_active is True


class TestGetUpdates:
    """Test incremental content reading."""

    def test_get_updates_with_new_content(self, tmp_path):
        """Test reading new content from file."""
        log_file = tmp_path / "test.log"
        log_file.write_text("Initial content\n")

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)

        # Read initial content
        content, has_more = monitor.get_updates()

        assert content == "Initial content\n"
        assert session.file_position > 0
        assert has_more is False

    def test_get_updates_incremental(self, tmp_path):
        """Test incremental reading with file position tracking."""
        log_file = tmp_path / "test.log"
        log_file.write_text("Line 1\n")

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)

        # First read
        content1, _ = monitor.get_updates()
        assert content1 == "Line 1\n"
        position_after_first = session.file_position

        # Append more content
        with open(log_file, "a") as f:
            f.write("Line 2\n")

        # Second read (should only get new content)
        content2, _ = monitor.get_updates()
        assert content2 == "Line 2\n"
        assert session.file_position > position_after_first

    def test_get_updates_empty_file(self, tmp_path):
        """Test reading from empty file."""
        log_file = tmp_path / "empty.log"
        log_file.write_text("")

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)
        content, has_more = monitor.get_updates()

        assert content == ""
        assert has_more is False

    def test_get_updates_no_new_content(self, tmp_path):
        """Test reading when file hasn't changed."""
        log_file = tmp_path / "test.log"
        log_file.write_text("Content\n")

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)

        # First read
        content1, _ = monitor.get_updates()
        assert content1 == "Content\n"

        # Second read without appending (should be empty)
        content2, _ = monitor.get_updates()
        assert content2 == ""

    def test_get_updates_has_more_flag(self, tmp_path):
        """Test has_more flag when file grows during read."""
        log_file = tmp_path / "test.log"
        log_file.write_text("Initial\n")

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)

        # Read initial content
        _, has_more = monitor.get_updates()
        assert has_more is False

        # Append more content
        with open(log_file, "a") as f:
            f.write("New content\n")

        # Check that has_more would be True if file size > position
        current_size = os.path.getsize(log_file)
        assert session.file_position < current_size


class TestErrorHandling:
    """Test error handling in SessionMonitor."""

    def test_file_not_found_error(self, tmp_path):
        """Test handling of missing log file."""
        log_file = tmp_path / "nonexistent.log"

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)

        # Should raise FileNotFoundError and set state to STOPPED
        with pytest.raises(FileNotFoundError):
            monitor.get_updates()

        # Session state should be STOPPED
        assert session.state == SessionState.STOPPED

    def test_permission_error(self, tmp_path):
        """Test handling of permission errors."""
        log_file = tmp_path / "restricted.log"
        log_file.write_text("Content")

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)

        # Make file unreadable (Unix only)
        if os.name != "nt":  # Skip on Windows
            os.chmod(log_file, 0o000)

            try:
                with pytest.raises(PermissionError):
                    monitor.get_updates()

                # Session state should be STOPPED
                assert session.state == SessionState.STOPPED
            finally:
                # Restore permissions for cleanup
                os.chmod(log_file, 0o644)

    def test_deleted_file_during_monitoring(self, tmp_path):
        """Test handling file deletion during active monitoring."""
        log_file = tmp_path / "test.log"
        log_file.write_text("Content\n")

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)

        # First read succeeds
        content, _ = monitor.get_updates()
        assert content == "Content\n"

        # Delete file
        os.remove(log_file)

        # Next read should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            monitor.get_updates()

        assert session.state == SessionState.STOPPED


class TestSessionDuration:
    """Test session duration calculation."""

    def test_get_session_duration(self, tmp_path):
        """Test duration calculation."""
        log_file = tmp_path / "test.log"
        log_file.write_text("")

        start_time = datetime.now()
        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=start_time,
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)

        # Wait a small amount
        time.sleep(0.1)

        duration = monitor.get_session_duration()

        # Should be approximately 0.1 seconds (with some tolerance)
        assert 0.09 <= duration <= 0.5  # Generous range for test reliability

    def test_duration_increases_over_time(self, tmp_path):
        """Test that duration increases over time."""
        log_file = tmp_path / "test.log"
        log_file.write_text("")

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)

        duration1 = monitor.get_session_duration()
        time.sleep(0.05)
        duration2 = monitor.get_session_duration()

        assert duration2 > duration1


class TestStopMonitoring:
    """Test stopping session monitoring."""

    def test_stop_basic(self, tmp_path):
        """Test basic stop functionality."""
        log_file = tmp_path / "test.log"
        log_file.write_text("Test content")

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)

        # Read some content first
        monitor.get_updates()

        # Stop monitoring
        stats = monitor.stop()

        assert session.state == SessionState.STOPPED
        assert stats["session_id"] == session.session_id
        assert stats["status"] == "stopped"
        assert stats["total_bytes_processed"] > 0
        assert stats["session_duration_seconds"] >= 0

    def test_stop_with_save_log(self, tmp_path):
        """Test stop with save_log=True preserves file."""
        log_file = tmp_path / "test.log"
        log_file.write_text("Important content")

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)
        monitor.stop(save_log=True)

        # File should still exist
        assert log_file.exists()

    def test_stop_without_save_log(self, tmp_path):
        """Test stop with save_log=False deletes file."""
        log_file = tmp_path / "test.log"
        log_file.write_text("Temporary content")

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)
        monitor.stop(save_log=False)

        # File should be deleted
        assert not log_file.exists()

    def test_stop_statistics(self, tmp_path):
        """Test stop returns correct statistics."""
        log_file = tmp_path / "test.log"
        log_file.write_text("A" * 100)  # 100 bytes

        session_id = str(uuid.uuid4())
        session = Session(
            session_id=session_id,
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)

        # Read all content
        monitor.get_updates()

        # Small delay for duration
        time.sleep(0.05)

        stats = monitor.stop()

        assert stats["session_id"] == session_id
        assert stats["status"] == "stopped"
        assert stats["total_bytes_processed"] == 100
        assert stats["session_duration_seconds"] > 0


class TestIsActiveProperty:
    """Test is_active property."""

    def test_is_active_when_active(self, tmp_path):
        """Test is_active returns True for active session."""
        log_file = tmp_path / "test.log"
        log_file.write_text("")

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)

        assert monitor.is_active is True

    def test_is_active_when_stopped(self, tmp_path):
        """Test is_active returns False for stopped session."""
        log_file = tmp_path / "test.log"
        log_file.write_text("")

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.STOPPED,
            metadata={},
        )

        monitor = SessionMonitor(session)

        assert monitor.is_active is False

    def test_is_active_after_stop(self, tmp_path):
        """Test is_active becomes False after stopping."""
        log_file = tmp_path / "test.log"
        log_file.write_text("")

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)

        assert monitor.is_active is True

        monitor.stop()

        assert monitor.is_active is False


class TestFilePositionTracking:
    """Test file position tracking across reads."""

    def test_position_advances_on_read(self, tmp_path):
        """Test that file position advances correctly."""
        log_file = tmp_path / "test.log"
        log_file.write_text("0123456789")  # 10 bytes

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)

        # Initial position
        assert session.file_position == 0

        # Read content
        content, _ = monitor.get_updates()

        # Position should have advanced
        assert session.file_position == 10
        assert content == "0123456789"

    def test_position_persistence_across_reads(self, tmp_path):
        """Test that position persists correctly across multiple reads."""
        log_file = tmp_path / "test.log"
        log_file.write_text("Part1\n")

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)

        # First read
        content1, _ = monitor.get_updates()
        assert content1 == "Part1\n"
        position1 = session.file_position

        # Append more
        with open(log_file, "a") as f:
            f.write("Part2\n")

        # Second read (should only get Part2)
        content2, _ = monitor.get_updates()
        assert content2 == "Part2\n"
        position2 = session.file_position

        # Position should have increased
        assert position2 > position1

    def test_starting_from_middle_of_file(self, tmp_path):
        """Test starting monitoring from a specific file position."""
        log_file = tmp_path / "test.log"
        log_file.write_text("Old content\nNew content\n")

        # Start from position 12 (after "Old content\n")
        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=12,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)

        # Should only read from position 12 onwards
        content, _ = monitor.get_updates()
        assert content == "New content\n"
        assert "Old content" not in content
