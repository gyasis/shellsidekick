"""Security utilities for password detection and dangerous command detection."""

import re
from typing import List

# Password detection patterns
PASSWORD_PATTERNS = [
    re.compile(r"password\s*:", re.IGNORECASE),
    re.compile(r"passphrase\s*:", re.IGNORECASE),
    re.compile(r"pass\s*:", re.IGNORECASE),
    re.compile(r"enter\s+password", re.IGNORECASE),
    re.compile(r"authentication\s+required", re.IGNORECASE),
]


# Dangerous command patterns
DANGEROUS_PATTERNS = [
    re.compile(r"\brm\s+-rf\s+/", re.IGNORECASE),
    re.compile(r"\bmkfs\b", re.IGNORECASE),
    re.compile(r"\bdd\s+if=", re.IGNORECASE),
    re.compile(r":[(][)]\{.*?[:][|&].*?\};:", re.IGNORECASE),  # Fork bomb
    re.compile(r"\bformat\s+[A-Z]:", re.IGNORECASE),
    re.compile(r"\bdel\s+/[fqs]", re.IGNORECASE),
    re.compile(r"\bdelete\b.*?\btable", re.IGNORECASE),
    re.compile(r"\bdelete\b.*?\b(all|files|data|everything)", re.IGNORECASE),
    re.compile(r"\bdrop\s+table", re.IGNORECASE),
    re.compile(r"\btruncate\b.*?\btable", re.IGNORECASE),
    re.compile(r"\bremove\b.*?\b(all|files|data)", re.IGNORECASE),
    re.compile(r"\bdestroy\b", re.IGNORECASE),
    re.compile(r"\bwipe\b", re.IGNORECASE),
    re.compile(r"\berase\b.*?\b(all|files|data)", re.IGNORECASE),
]


def is_password_prompt(text: str) -> bool:
    """Check if text appears to be a password prompt.

    Args:
        text: Text to check

    Returns:
        True if text matches password patterns
    """
    for pattern in PASSWORD_PATTERNS:
        if pattern.search(text):
            return True
    return False


def is_dangerous_operation(text: str) -> bool:
    """Check if text involves dangerous operations.

    Args:
        text: Text to check (prompt or command)

    Returns:
        True if text contains dangerous keywords
    """
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(text):
            return True
    return False


def redact_password(text: str) -> str:
    """Redact passwords from text.

    Args:
        text: Text that may contain passwords

    Returns:
        Text with passwords replaced by [REDACTED]
    """
    # Replace password input text (anything after password: prompt)
    return re.sub(
        r"(password|passphrase|pass)\s*:\s*\S+", r"\1: [REDACTED]", text, flags=re.IGNORECASE
    )


def get_dangerous_keywords(text: str) -> List[str]:
    """Extract dangerous keywords from text.

    Args:
        text: Text to analyze

    Returns:
        List of matched dangerous keywords
    """
    keywords = []
    for pattern in DANGEROUS_PATTERNS:
        match = pattern.search(text)
        if match:
            keywords.append(match.group(0))
    return keywords
