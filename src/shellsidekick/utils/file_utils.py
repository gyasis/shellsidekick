"""File position tracking and incremental file reading utilities."""

import os
from typing import Tuple


def read_from_position(file_path: str, position: int) -> Tuple[str, int]:
    """Read file content from a specific position.

    Args:
        file_path: Absolute path to file
        position: Byte position to start reading from

    Returns:
        Tuple of (new_content, new_position)

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file is not readable
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"Cannot read file: {file_path}")

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        f.seek(position)
        new_content = f.read()
        new_position = f.tell()

    return new_content, new_position


def get_file_size(file_path: str) -> int:
    """Get the size of a file in bytes.

    Args:
        file_path: Absolute path to file

    Returns:
        File size in bytes
    """
    return os.path.getsize(file_path)


def ensure_file_exists(file_path: str) -> None:
    """Ensure a file exists, create if it doesn't.

    Args:
        file_path: Absolute path to file
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, "w") as _:
            pass
