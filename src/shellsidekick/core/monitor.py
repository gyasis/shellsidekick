"""Session monitoring with file position tracking."""

from datetime import datetime
from typing import Optional

from shellsidekick.models.session import Session, SessionState, SessionType
from shellsidekick.utils.file_utils import read_from_position, get_file_size


class SessionMonitor:
    """Monitors a terminal session log file with incremental reading."""

    def __init__(self, session: Session):
        """Initialize session monitor.

        Args:
            session: Session entity to monitor
        """
        self.session = session

    def get_updates(self) -> tuple[str, bool]:
        """Read new content since last check.

        Returns:
            Tuple of (new_content, has_more)
            - new_content: Text added since last read
            - has_more: Whether more content is immediately available

        Raises:
            FileNotFoundError: If log file doesn't exist
            PermissionError: If log file is not readable
        """
        try:
            new_content, new_position = read_from_position(
                self.session.log_file,
                self.session.file_position
            )

            # Update session file position
            old_position = self.session.file_position
            self.session.file_position = new_position

            # Check if there's more content (file grew during read)
            current_size = get_file_size(self.session.log_file)
            has_more = new_position < current_size

            return new_content, has_more

        except FileNotFoundError:
            # Log file disappeared during monitoring
            self.session.state = SessionState.STOPPED
            raise
        except PermissionError:
            # Lost read permissions
            self.session.state = SessionState.STOPPED
            raise

    def get_session_duration(self) -> float:
        """Get session duration in seconds.

        Returns:
            Duration since start_time in seconds
        """
        return (datetime.now() - self.session.start_time).total_seconds()

    def stop(self, save_log: bool = False) -> dict:
        """Stop monitoring and return statistics.

        Args:
            save_log: Whether to preserve the log file

        Returns:
            Dictionary with session statistics
        """
        import os

        self.session.state = SessionState.STOPPED
        duration = self.get_session_duration()

        stats = {
            "session_id": self.session.session_id,
            "status": self.session.state.value,
            "total_bytes_processed": self.session.file_position,
            "session_duration_seconds": duration
        }

        # Clean up log file if requested
        if not save_log and os.path.exists(self.session.log_file):
            try:
                os.remove(self.session.log_file)
            except OSError:
                # File might be in use, skip cleanup
                pass

        return stats

    @property
    def is_active(self) -> bool:
        """Check if session is still active.

        Returns:
            True if session state is ACTIVE
        """
        return self.session.state == SessionState.ACTIVE
