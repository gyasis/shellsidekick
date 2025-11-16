"""Session entity and related enums."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SessionType(str, Enum):
    """Type of session being monitored."""
    SSH = "ssh"
    SCRIPT = "script"
    FILE = "file"


class SessionState(str, Enum):
    """Current state of the session."""
    ACTIVE = "active"
    STOPPED = "stopped"


@dataclass
class Session:
    """Represents a monitored terminal session.

    Attributes:
        session_id: Unique identifier (UUID4 recommended)
        session_type: Type of session (SSH, script, file)
        log_file: Absolute path to session output log
        file_position: Current read position in log file (bytes)
        start_time: When monitoring started (ISO 8601)
        state: Current session state (active, stopped)
        metadata: Optional session metadata (e.g., SSH host, user)
    """
    session_id: str
    session_type: SessionType
    log_file: str
    file_position: int
    start_time: datetime
    state: SessionState
    metadata: dict[str, str] | None = None

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict for MCP responses."""
        return {
            "session_id": self.session_id,
            "session_type": self.session_type.value,
            "log_file": self.log_file,
            "file_position": self.file_position,
            "start_time": self.start_time.isoformat(),
            "state": self.state.value,
            "metadata": self.metadata or {}
        }
