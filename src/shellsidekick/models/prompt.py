"""PromptDetection entity and related enums."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class PromptType(str, Enum):
    """Type of detected prompt."""
    PASSWORD = "password"
    YES_NO = "yes_no"
    CHOICE = "choice"
    PATH = "path"
    TEXT = "text"
    COMMAND = "command"
    UNKNOWN = "unknown"


@dataclass
class PromptDetection:
    """Represents a detected terminal prompt.

    Attributes:
        prompt_text: The text of the detected prompt
        confidence: Detection confidence score (0.0-1.0)
        prompt_type: Type of prompt detected
        matched_pattern: Regex pattern that matched (for debugging)
        file_position: Position in log file where detected (bytes)
        timestamp: When prompt was detected (ISO 8601)
        is_dangerous: Whether prompt involves dangerous operations
    """
    prompt_text: str
    confidence: float
    prompt_type: PromptType
    matched_pattern: str
    file_position: int
    timestamp: datetime
    is_dangerous: bool = False

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict for MCP responses."""
        return {
            "prompt_text": self.prompt_text,
            "confidence": self.confidence,
            "prompt_type": self.prompt_type.value,
            "matched_pattern": self.matched_pattern,
            "file_position": self.file_position,
            "timestamp": self.timestamp.isoformat(),
            "is_dangerous": self.is_dangerous
        }
