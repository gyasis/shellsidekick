"""Prompt detection with regex patterns."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from shellsidekick.models.prompt import PromptDetection, PromptType
from shellsidekick.utils.security import is_dangerous_operation, is_password_prompt


@dataclass
class PromptPattern:
    """A prompt detection pattern."""
    regex: re.Pattern
    prompt_type: PromptType
    confidence: float  # Base confidence (0.0-1.0)


# Prompt detection patterns (ordered by specificity)
PROMPT_PATTERNS = [
    # Password prompts (highest priority)
    PromptPattern(
        regex=re.compile(r"password\s*:", re.IGNORECASE),
        prompt_type=PromptType.PASSWORD,
        confidence=0.95
    ),
    PromptPattern(
        regex=re.compile(r"passphrase\s*:", re.IGNORECASE),
        prompt_type=PromptType.PASSWORD,
        confidence=0.95
    ),
    PromptPattern(
        regex=re.compile(r"enter\s+(?:your\s+)?password", re.IGNORECASE),
        prompt_type=PromptType.PASSWORD,
        confidence=0.92
    ),

    # Yes/No prompts
    PromptPattern(
        regex=re.compile(r"\(yes/no\)|\[y/n\]|\(y/n\)", re.IGNORECASE),
        prompt_type=PromptType.YES_NO,
        confidence=0.90
    ),
    PromptPattern(
        regex=re.compile(r"continue\?|proceed\?|confirm\?", re.IGNORECASE),
        prompt_type=PromptType.YES_NO,
        confidence=0.85
    ),

    # Path prompts
    PromptPattern(
        regex=re.compile(r"enter\s+(?:file\s+)?path\s*:|(?:file|directory)\s+path\s*:", re.IGNORECASE),
        prompt_type=PromptType.PATH,
        confidence=0.88
    ),
    PromptPattern(
        regex=re.compile(r"(?:file|directory)\s+name\s*:", re.IGNORECASE),
        prompt_type=PromptType.PATH,
        confidence=0.82
    ),

    # Choice prompts (numbered lists)
    PromptPattern(
        regex=re.compile(r"^\s*\[\d+\].*(?:\n\s*\[\d+\].*)+", re.MULTILINE),
        prompt_type=PromptType.CHOICE,
        confidence=0.82
    ),

    # Command prompts
    PromptPattern(
        regex=re.compile(r"enter\s+command\s*:|command\s*:", re.IGNORECASE),
        prompt_type=PromptType.COMMAND,
        confidence=0.85
    ),

    # Generic text input
    PromptPattern(
        regex=re.compile(r"enter\s+\w+\s*:|input\s*:", re.IGNORECASE),
        prompt_type=PromptType.TEXT,
        confidence=0.75
    ),
]


class PromptDetector:
    """Detects prompts waiting for user input in terminal output."""

    def __init__(self, min_confidence: float = 0.70):
        """Initialize prompt detector.

        Args:
            min_confidence: Minimum confidence threshold for detection
        """
        self.min_confidence = min_confidence

    def detect(self, content: str, file_position: int = 0) -> Optional[PromptDetection]:
        """Detect if content contains a prompt waiting for input.

        Args:
            content: Terminal output content to analyze
            file_position: Position in log file (for tracking)

        Returns:
            PromptDetection if a prompt is found, None otherwise
        """
        if not content:
            return None

        # Focus on last 50 lines (prompts typically appear at end)
        lines = content.split('\n')
        recent_lines = '\n'.join(lines[-50:])

        # Try each pattern in order
        for pattern in PROMPT_PATTERNS:
            match = pattern.regex.search(recent_lines)
            if match and pattern.confidence >= self.min_confidence:
                prompt_text = match.group(0).strip()

                # Check if this is a dangerous operation
                is_dangerous = is_dangerous_operation(prompt_text)

                return PromptDetection(
                    prompt_text=prompt_text,
                    confidence=pattern.confidence,
                    prompt_type=pattern.prompt_type,
                    matched_pattern=pattern.regex.pattern,
                    file_position=file_position,
                    timestamp=datetime.now(),
                    is_dangerous=is_dangerous
                )

        return None

    def detect_with_context(
        self,
        content: str,
        file_position: int = 0,
        context_lines: int = 3
    ) -> Optional[tuple[PromptDetection, list[str]]]:
        """Detect prompt with surrounding context lines.

        Args:
            content: Terminal output content
            file_position: Position in log file
            context_lines: Number of lines before/after prompt

        Returns:
            Tuple of (PromptDetection, context_lines) if found, None otherwise
        """
        detection = self.detect(content, file_position)
        if not detection:
            return None

        # Extract context
        lines = content.split('\n')
        # Find the line with the prompt
        prompt_line_idx = None
        for idx, line in enumerate(lines):
            if detection.prompt_text in line:
                prompt_line_idx = idx
                break

        if prompt_line_idx is not None:
            start_idx = max(0, prompt_line_idx - context_lines)
            end_idx = min(len(lines), prompt_line_idx + context_lines + 1)
            context = lines[start_idx:end_idx]
        else:
            context = lines[-context_lines-1:]

        return detection, context
