"""InputEvent entity and related enums."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class InputSource(str, Enum):
    """Source of the input."""
    USER_TYPED = "user_typed"
    AI_SUGGESTED = "ai_suggested"
    AUTO_INJECTED = "auto_injected"


@dataclass
class InputEvent:
    """Represents a user input event.

    Attributes:
        event_id: Unique event identifier (UUID4)
        session_id: Associated session ID
        timestamp: When input was provided (ISO 8601)
        prompt_text: The prompt that triggered input
        input_text: The text user provided (REDACTED for passwords)
        success: Whether input was accepted (True) or rejected (False)
        input_source: How input was provided
        response_time_ms: Time between prompt and input (milliseconds)
    """
    event_id: str
    session_id: str
    timestamp: datetime
    prompt_text: str
    input_text: str  # "[REDACTED]" for passwords
    success: bool
    input_source: InputSource
    response_time_ms: int

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict for storage."""
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "prompt_text": self.prompt_text,
            "input_text": self.input_text,
            "success": self.success,
            "input_source": self.input_source.value,
            "response_time_ms": self.response_time_ms
        }
