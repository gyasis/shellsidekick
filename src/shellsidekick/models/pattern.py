"""Pattern entity for learned prompt-response patterns."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ResponseStats:
    """Statistics for a specific response to a prompt."""
    count: int
    success_count: int

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0-1.0)."""
        return self.success_count / self.count if self.count > 0 else 0.0


@dataclass
class Pattern:
    """Represents a learned prompt-response pattern.

    Attributes:
        pattern_id: Unique pattern identifier (hash of prompt_text)
        prompt_text: The prompt text (normalized)
        responses: Map of response text → statistics
        total_occurrences: Total times this prompt appeared
        last_seen: Last time this prompt was detected (ISO 8601)
        created_at: When pattern was first learned (ISO 8601)
    """
    pattern_id: str
    prompt_text: str
    responses: dict[str, ResponseStats]
    total_occurrences: int
    last_seen: datetime
    created_at: datetime

    def get_most_common_response(self) -> tuple[str, ResponseStats] | None:
        """Get the most frequently used response."""
        if not self.responses:
            return None
        return max(self.responses.items(), key=lambda x: x[1].count)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict for storage."""
        return {
            "pattern_id": self.pattern_id,
            "prompt_text": self.prompt_text,
            "responses": {
                text: {"count": stats.count, "success_count": stats.success_count}
                for text, stats in self.responses.items()
            },
            "total_occurrences": self.total_occurrences,
            "last_seen": self.last_seen.isoformat(),
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pattern":
        """Reconstruct Pattern from JSON dict.

        Args:
            data: Dictionary from to_dict()

        Returns:
            Pattern instance
        """
        # Reconstruct ResponseStats objects
        responses = {
            text: ResponseStats(
                count=stats_dict["count"],
                success_count=stats_dict["success_count"]
            )
            for text, stats_dict in data["responses"].items()
        }

        return cls(
            pattern_id=data["pattern_id"],
            prompt_text=data["prompt_text"],
            responses=responses,
            total_occurrences=data["total_occurrences"],
            last_seen=datetime.fromisoformat(data["last_seen"]),
            created_at=datetime.fromisoformat(data["created_at"])
        )
