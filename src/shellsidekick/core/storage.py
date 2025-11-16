"""JSON storage utilities for session history and patterns."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


# Base storage directory
STORAGE_DIR = Path("/tmp/ssk-sessions")
HISTORY_DIR = STORAGE_DIR / "history"
PATTERNS_FILE = STORAGE_DIR / "patterns.json"


def init_storage() -> None:
    """Initialize storage directories with secure permissions."""
    STORAGE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)


def save_json(file_path: Path, data: Dict[str, Any]) -> None:
    """Save data to JSON file with secure permissions.

    Args:
        file_path: Path to JSON file
        data: Data to save
    """
    file_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

    # Set secure permissions (user-only read/write)
    os.chmod(file_path, 0o600)


def load_json(file_path: Path) -> Dict[str, Any]:
    """Load data from JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Loaded data, or empty dict if file doesn't exist
    """
    if not file_path.exists():
        return {}

    with open(file_path, 'r') as f:
        return json.load(f)


def get_session_history_path(session_id: str) -> Path:
    """Get path to session history file.

    Args:
        session_id: Session identifier

    Returns:
        Path to history JSON file
    """
    return HISTORY_DIR / f"{session_id}.json"


def save_session_history(session_id: str, events: List[Dict[str, Any]]) -> None:
    """Save session input history.

    Args:
        session_id: Session identifier
        events: List of input events
    """
    history_path = get_session_history_path(session_id)
    data = {
        "session_id": session_id,
        "events": events
    }
    save_json(history_path, data)


def load_session_history(session_id: str) -> List[Dict[str, Any]]:
    """Load session input history.

    Args:
        session_id: Session identifier

    Returns:
        List of input events, empty if no history exists
    """
    history_path = get_session_history_path(session_id)
    data = load_json(history_path)
    return data.get("events", [])


def save_patterns(patterns: List[Dict[str, Any]]) -> None:
    """Save learned patterns to global patterns file.

    Args:
        patterns: List of pattern dicts
    """
    data = {"patterns": patterns}
    save_json(PATTERNS_FILE, data)


def load_patterns() -> List[Dict[str, Any]]:
    """Load learned patterns from global patterns file.

    Returns:
        List of pattern dicts, empty if no patterns exist
    """
    data = load_json(PATTERNS_FILE)
    return data.get("patterns", [])


def cleanup_old_files(retention_days: int = 7, dry_run: bool = False) -> tuple[List[str], int]:
    """Clean up files older than retention period.

    Args:
        retention_days: Files older than this are deleted
        dry_run: If True, don't actually delete files

    Returns:
        Tuple of (deleted_files, bytes_freed)
    """
    import time

    cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
    deleted_files = []
    bytes_freed = 0

    # Scan all files in storage directory
    for root, dirs, files in os.walk(STORAGE_DIR):
        for filename in files:
            file_path = Path(root) / filename

            # Skip patterns file (global, not session-specific)
            if file_path == PATTERNS_FILE:
                continue

            # Check file age
            if os.path.getmtime(file_path) < cutoff_time:
                file_size = os.path.getsize(file_path)
                deleted_files.append(str(file_path))
                bytes_freed += file_size

                if not dry_run:
                    os.remove(file_path)

    return deleted_files, bytes_freed
