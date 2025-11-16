"""MCP tools for session lifecycle management."""

import os
from datetime import datetime
from typing import Optional

from fastmcp.exceptions import ToolError

from shellsidekick.core.monitor import SessionMonitor
from shellsidekick.mcp.server import mcp
from shellsidekick.mcp.session_state import active_sessions
from shellsidekick.models.session import Session, SessionState, SessionType
from shellsidekick.utils.logging import get_logger

logger = get_logger(__name__)


@mcp.tool()
def start_session_monitor(
    session_id: str, session_type: str, log_file: str, metadata: Optional[dict[str, str]] = None
) -> dict:
    """Start monitoring a terminal session.

    Args:
        session_id: Unique identifier for the session (UUID4 recommended)
        session_type: Type of session (ssh, script, file)
        log_file: Absolute path to the session output log file
        metadata: Optional session metadata (e.g., SSH host, user)

    Returns:
        Session status with session_id, status, file_position, start_time, log_file

    Raises:
        ToolError: If session already exists, file not found, or file not readable
    """
    # Check for duplicate session
    if session_id in active_sessions:
        raise ToolError(f"Session {session_id} already exists", code="SESSION_ALREADY_EXISTS")

    # Validate file exists
    if not os.path.exists(log_file):
        raise ToolError(f"Log file not found: {log_file}", code="FILE_NOT_FOUND")

    # Validate file is readable
    if not os.access(log_file, os.R_OK):
        raise ToolError(f"Cannot read log file: {log_file}", code="FILE_NOT_READABLE")

    # Create session
    session = Session(
        session_id=session_id,
        session_type=SessionType(session_type),
        log_file=log_file,
        file_position=0,
        start_time=datetime.now(),
        state=SessionState.ACTIVE,
        metadata=metadata,
    )

    # Create monitor
    monitor = SessionMonitor(session)
    active_sessions[session_id] = monitor

    logger.info(f"Started monitoring session {session_id} ({session_type}): {log_file}")

    return session.to_dict()


@mcp.tool()
def get_session_updates(session_id: str) -> dict:
    """Retrieve new content from monitored session since last check.

    Args:
        session_id: Session ID to get updates from

    Returns:
        Dictionary with session_id, new_content, file_position, has_more

    Raises:
        ToolError: If session not found or file read error
    """
    if session_id not in active_sessions:
        raise ToolError(f"Session {session_id} not found", code="SESSION_NOT_FOUND")

    monitor = active_sessions[session_id]

    try:
        new_content, has_more = monitor.get_updates()

        return {
            "session_id": session_id,
            "new_content": new_content,
            "file_position": monitor.session.file_position,
            "has_more": has_more,
        }

    except (FileNotFoundError, PermissionError) as e:
        raise ToolError(f"Failed to read log file: {str(e)}", code="FILE_READ_ERROR")


@mcp.tool()
def stop_session_monitor(session_id: str, save_log: bool = False) -> dict:
    """Stop monitoring a session and cleanup resources.

    Args:
        session_id: Session ID to stop
        save_log: Whether to preserve log file (default: False)

    Returns:
        Dictionary with session_id, status, total_bytes_processed, session_duration_seconds

    Raises:
        ToolError: If session not found
    """
    if session_id not in active_sessions:
        raise ToolError(f"Session {session_id} not found", code="SESSION_NOT_FOUND")

    monitor = active_sessions[session_id]
    stats = monitor.stop(save_log=save_log)

    # Remove from active sessions
    del active_sessions[session_id]

    logger.info(f"Stopped session {session_id}, processed {stats['total_bytes_processed']} bytes")

    return stats
