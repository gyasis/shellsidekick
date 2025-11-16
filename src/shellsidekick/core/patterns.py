"""Pattern learning logic for prompt-response tracking."""

import hashlib
import uuid
from datetime import datetime
from typing import List, Dict

from shellsidekick.models.input_event import InputEvent, InputSource
from shellsidekick.models.pattern import Pattern, ResponseStats
from shellsidekick.utils.security import is_password_prompt
from shellsidekick.utils.logging import get_logger
from shellsidekick.core.storage import save_patterns, load_patterns

logger = get_logger(__name__)


class PatternLearner:
    """Learns and manages prompt-response patterns from user interactions."""

    def __init__(self, auto_load: bool = True):
        """Initialize pattern learner with optional auto-load.

        Args:
            auto_load: If True, load patterns from storage on init (default: True)
        """
        self._events: Dict[str, List[InputEvent]] = {}  # session_id → events
        self._patterns: Dict[str, Pattern] = {}  # pattern_id → pattern

        # Load existing patterns from storage
        if auto_load:
            self.load_from_storage()

    def track_input_event(
        self,
        session_id: str,
        prompt_text: str,
        input_text: str,
        success: bool,
        input_source: InputSource,
        response_time_ms: int
    ) -> dict:
        """Track a user input event and update learned patterns.

        Args:
            session_id: Session identifier
            prompt_text: The prompt that triggered input
            input_text: The text user provided
            success: Whether input was accepted
            input_source: How input was provided
            response_time_ms: Response time in milliseconds

        Returns:
            Dictionary with event_id, recorded, and pattern_updated status
        """
        # Generate event ID
        event_id = str(uuid.uuid4())

        # Check if password and redact if needed
        is_password = is_password_prompt(prompt_text)
        if is_password:
            input_text = "[REDACTED]"
            logger.info(f"Password prompt detected in session {session_id}, input redacted")

        # Create event
        event = InputEvent(
            event_id=event_id,
            session_id=session_id,
            timestamp=datetime.now(),
            prompt_text=prompt_text,
            input_text=input_text,
            success=success,
            input_source=input_source,
            response_time_ms=response_time_ms
        )

        # Store event
        if session_id not in self._events:
            self._events[session_id] = []
        self._events[session_id].append(event)

        # Update patterns (not for passwords - always track success/failure for patterns)
        pattern_updated = False
        if not is_password:
            pattern_updated = self._update_pattern(prompt_text, input_text, success)

        logger.info(
            f"Tracked input event {event_id} for session {session_id}: "
            f"prompt='{prompt_text[:50]}...', success={success}, "
            f"pattern_updated={pattern_updated}"
        )

        return {
            "event_id": event_id,
            "recorded": True,
            "pattern_updated": pattern_updated
        }

    def _update_pattern(self, prompt_text: str, input_text: str, success: bool) -> bool:
        """Update learned pattern with new prompt-response pair.

        Args:
            prompt_text: The prompt text
            input_text: The response text
            success: Whether response was successful

        Returns:
            True if pattern was updated
        """
        # Generate pattern ID from prompt text
        pattern_id = self._generate_pattern_id(prompt_text)

        # Get or create pattern
        if pattern_id not in self._patterns:
            self._patterns[pattern_id] = Pattern(
                pattern_id=pattern_id,
                prompt_text=prompt_text,
                responses={},
                total_occurrences=0,
                last_seen=datetime.now(),
                created_at=datetime.now()
            )
            logger.debug(f"Created new pattern {pattern_id} for prompt: '{prompt_text[:50]}...'")

        pattern = self._patterns[pattern_id]

        # Update response statistics
        if input_text not in pattern.responses:
            pattern.responses[input_text] = ResponseStats(count=0, success_count=0)

        pattern.responses[input_text].count += 1
        if success:
            pattern.responses[input_text].success_count += 1

        # Update pattern metadata
        pattern.total_occurrences += 1
        pattern.last_seen = datetime.now()

        logger.debug(
            f"Updated pattern {pattern_id}: response '{input_text}' now has "
            f"{pattern.responses[input_text].count} occurrences, "
            f"{pattern.responses[input_text].success_count} successful"
        )

        # Persist patterns to storage
        self.save_to_storage()

        return True

    def _generate_pattern_id(self, prompt_text: str) -> str:
        """Generate a consistent pattern ID from prompt text.

        Args:
            prompt_text: The prompt text to hash

        Returns:
            SHA256 hash of the prompt text (first 16 chars)
        """
        # Normalize prompt text (lowercase, strip whitespace)
        normalized = prompt_text.lower().strip()

        # Generate hash
        hash_obj = hashlib.sha256(normalized.encode('utf-8'))
        return hash_obj.hexdigest()[:16]

    def get_session_events(self, session_id: str) -> List[InputEvent]:
        """Get all tracked events for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of InputEvent objects (may be empty)
        """
        return self._events.get(session_id, [])

    def get_patterns(self) -> List[Pattern]:
        """Get all learned patterns.

        Returns:
            List of Pattern objects
        """
        return list(self._patterns.values())

    def get_pattern_by_prompt(self, prompt_text: str) -> Pattern | None:
        """Get pattern for a specific prompt text.

        Args:
            prompt_text: The prompt text to look up

        Returns:
            Pattern object if found, None otherwise
        """
        pattern_id = self._generate_pattern_id(prompt_text)
        return self._patterns.get(pattern_id)

    def get_patterns_formatted(
        self,
        prompt_filter: str | None = None,
        min_occurrences: int = 1,
        sort_by: str = "occurrences"
    ) -> dict:
        """Get learned patterns with filtering and sorting.

        Args:
            prompt_filter: Optional substring filter for prompt text
            min_occurrences: Minimum number of occurrences (default: 1)
            sort_by: Sort field - "occurrences", "last_seen", or "success_rate"

        Returns:
            Dictionary with patterns array and total_patterns count
        """
        # Start with all patterns
        patterns = list(self._patterns.values())

        # Apply prompt filter
        if prompt_filter:
            patterns = [
                p for p in patterns
                if prompt_filter.lower() in p.prompt_text.lower()
            ]

        # Apply min_occurrences filter
        patterns = [p for p in patterns if p.total_occurrences >= min_occurrences]

        # Sort patterns
        if sort_by == "occurrences":
            patterns.sort(key=lambda p: p.total_occurrences, reverse=True)
        elif sort_by == "last_seen":
            patterns.sort(key=lambda p: p.last_seen, reverse=True)
        elif sort_by == "success_rate":
            # Sort by success rate of most common response
            def get_success_rate(pattern: Pattern) -> float:
                mcr = pattern.get_most_common_response()
                return mcr[1].success_rate if mcr else 0.0

            patterns.sort(key=get_success_rate, reverse=True)

        # Format patterns for output
        formatted_patterns = []
        for pattern in patterns:
            # Get most common response
            mcr_tuple = pattern.get_most_common_response()
            if mcr_tuple:
                mcr_text, mcr_stats = mcr_tuple
                most_common_response = {
                    "input_text": mcr_text,
                    "count": mcr_stats.count,
                    "success_rate": mcr_stats.success_rate
                }
            else:
                most_common_response = None

            # Get all responses
            all_responses = [
                {
                    "input_text": text,
                    "count": stats.count,
                    "success_count": stats.success_count,
                    "success_rate": stats.success_rate
                }
                for text, stats in pattern.responses.items()
            ]

            formatted_patterns.append({
                "prompt_text": pattern.prompt_text,
                "total_occurrences": pattern.total_occurrences,
                "most_common_response": most_common_response,
                "all_responses": all_responses,
                "last_seen": pattern.last_seen.isoformat()
            })

        return {
            "patterns": formatted_patterns,
            "total_patterns": len(formatted_patterns)
        }

    def load_from_storage(self) -> int:
        """Load patterns from JSON storage.

        Returns:
            Number of patterns loaded
        """
        try:
            pattern_dicts = load_patterns()
            loaded_count = 0

            for pattern_dict in pattern_dicts:
                pattern = Pattern.from_dict(pattern_dict)
                self._patterns[pattern.pattern_id] = pattern
                loaded_count += 1

            if loaded_count > 0:
                logger.info(f"Loaded {loaded_count} patterns from storage")
            else:
                logger.debug("No patterns found in storage")

            return loaded_count

        except Exception as e:
            logger.error(f"Failed to load patterns from storage: {e}")
            return 0

    def save_to_storage(self) -> bool:
        """Save patterns to JSON storage.

        Returns:
            True if save succeeded, False otherwise
        """
        try:
            pattern_dicts = [p.to_dict() for p in self._patterns.values()]
            save_patterns(pattern_dicts)
            logger.debug(f"Saved {len(pattern_dicts)} patterns to storage")
            return True

        except Exception as e:
            logger.error(f"Failed to save patterns to storage: {e}")
            return False
