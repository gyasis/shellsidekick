"""MCP tools for pattern learning and history management."""

from typing import Optional, Dict

from fastmcp.exceptions import ToolError

from shellsidekick.mcp.server import mcp
from shellsidekick.mcp.session_state import pattern_learner
from shellsidekick.models.input_event import InputSource
from shellsidekick.utils.logging import get_logger

logger = get_logger(__name__)


@mcp.tool()
def track_input_event(
    session_id: str,
    prompt_text: str,
    input_text: str,
    success: bool,
    input_source: str,
    response_time_ms: int
) -> dict:
    """Track a user input event for pattern learning.

    Records user input events to build patterns of common prompt-response pairs.
    Automatically redacts password inputs for security.

    Args:
        session_id: Session identifier
        prompt_text: The prompt that triggered the input
        input_text: The text user provided
        success: Whether the input was accepted (True) or rejected (False)
        input_source: How input was provided (user_typed, ai_suggested, auto_injected)
        response_time_ms: Time between prompt and input (milliseconds)

    Returns:
        Dictionary with:
        - event_id: Unique event identifier
        - recorded: Whether event was successfully recorded
        - pattern_updated: Whether patterns were updated from this event

    Raises:
        ToolError: If input_source is invalid
    """
    # Validate input_source
    try:
        source = InputSource(input_source)
    except ValueError:
        raise ToolError(
            f"Invalid input_source: {input_source}. Must be one of: "
            f"{', '.join([s.value for s in InputSource])}",
            code="INVALID_INPUT_SOURCE"
        )

    # Track the event
    result = pattern_learner.track_input_event(
        session_id=session_id,
        prompt_text=prompt_text,
        input_text=input_text,
        success=success,
        input_source=source,
        response_time_ms=response_time_ms
    )

    logger.info(
        f"Tracked input event for session {session_id}: "
        f"success={success}, pattern_updated={result['pattern_updated']}"
    )

    return result


@mcp.tool()
def get_learned_patterns(
    prompt_filter: Optional[str] = None,
    min_occurrences: int = 1,
    sort_by: str = "occurrences"
) -> dict:
    """Retrieve learned prompt-response patterns.

    Returns patterns learned from tracked input events, with optional filtering
    and sorting. Useful for understanding common user behaviors and improving
    AI suggestions.

    Args:
        prompt_filter: Optional substring filter for prompt text (case-insensitive)
        min_occurrences: Minimum number of occurrences to include (default: 1)
        sort_by: Sort field - "occurrences" (default), "last_seen", or "success_rate"

    Returns:
        Dictionary with:
        - patterns: Array of pattern objects, each containing:
            - prompt_text: The prompt text
            - total_occurrences: Total times this prompt appeared
            - most_common_response: Most frequently used response with stats
            - all_responses: All response variants with counts and success rates
            - last_seen: Last time this prompt was detected (ISO 8601)
        - total_patterns: Total number of patterns returned

    Raises:
        ToolError: If sort_by is invalid or min_occurrences is negative
    """
    # Validate sort_by
    valid_sort_fields = ["occurrences", "last_seen", "success_rate"]
    if sort_by not in valid_sort_fields:
        raise ToolError(
            f"Invalid sort_by: {sort_by}. Must be one of: {', '.join(valid_sort_fields)}",
            code="INVALID_SORT_FIELD"
        )

    # Validate min_occurrences
    if min_occurrences < 1:
        raise ToolError(
            "min_occurrences must be at least 1",
            code="INVALID_MIN_OCCURRENCES"
        )

    # Get formatted patterns
    result = pattern_learner.get_patterns_formatted(
        prompt_filter=prompt_filter,
        min_occurrences=min_occurrences,
        sort_by=sort_by
    )

    logger.info(
        f"Retrieved {result['total_patterns']} learned patterns "
        f"(filter='{prompt_filter}', min={min_occurrences}, sort={sort_by})"
    )

    return result
