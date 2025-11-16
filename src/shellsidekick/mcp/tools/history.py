"""MCP tools for pattern learning and history management."""

from typing import Optional

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
    response_time_ms: int,
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
            code="INVALID_INPUT_SOURCE",
        )

    # Track the event
    result = pattern_learner.track_input_event(
        session_id=session_id,
        prompt_text=prompt_text,
        input_text=input_text,
        success=success,
        input_source=source,
        response_time_ms=response_time_ms,
    )

    logger.info(
        f"Tracked input event for session {session_id}: "
        f"success={success}, pattern_updated={result['pattern_updated']}"
    )

    return result


@mcp.tool()
def get_learned_patterns(
    prompt_filter: Optional[str] = None, min_occurrences: int = 1, sort_by: str = "occurrences"
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
            code="INVALID_SORT_FIELD",
        )

    # Validate min_occurrences
    if min_occurrences < 1:
        raise ToolError("min_occurrences must be at least 1", code="INVALID_MIN_OCCURRENCES")

    # Get formatted patterns
    result = pattern_learner.get_patterns_formatted(
        prompt_filter=prompt_filter, min_occurrences=min_occurrences, sort_by=sort_by
    )

    logger.info(
        f"Retrieved {result['total_patterns']} learned patterns "
        f"(filter='{prompt_filter}', min={min_occurrences}, sort={sort_by})"
    )

    return result


@mcp.tool()
def search_session_history(
    query: str, session_id: Optional[str] = None, context_lines: int = 3, max_results: int = 10
) -> dict:
    """Search session history for specific patterns or keywords.

    Searches through session log files for matching patterns using regex support.
    Useful for debugging issues, finding error messages, or analyzing session behavior.

    Args:
        query: Search query (supports regex patterns)
        session_id: Session ID to search (None for all sessions)
        context_lines: Lines of context before/after match (0-10, default: 3)
        max_results: Maximum number of results to return (1-100, default: 10)

    Returns:
        Dictionary with:
        - matches: Array of match objects with matched_text, line_number, context
        - total_matches: Total number of matches found
        - searched_sessions: List of session IDs that were searched

    Raises:
        ToolError: If session not found, invalid regex, or invalid parameters
    """
    import re

    from shellsidekick.core.storage import search_log_file
    from shellsidekick.mcp.session_state import active_sessions

    # Validate parameters
    if context_lines < 0 or context_lines > 10:
        raise ToolError("context_lines must be between 0 and 10", code="INVALID_CONTEXT_LINES")

    if max_results < 1 or max_results > 100:
        raise ToolError("max_results must be between 1 and 100", code="INVALID_MAX_RESULTS")

    # Validate regex pattern
    try:
        re.compile(query)
    except re.error as e:
        raise ToolError(f"Invalid regex pattern: {str(e)}", code="INVALID_REGEX")

    # Determine which sessions to search
    if session_id:
        # Search specific session
        if session_id not in active_sessions:
            raise ToolError(f"Session {session_id} not found", code="SESSION_NOT_FOUND")

        sessions_to_search = {session_id: active_sessions[session_id]}
    else:
        # Search all active sessions
        sessions_to_search = active_sessions

    # Search each session
    all_matches = []
    searched_sessions = []

    for sid, monitor in sessions_to_search.items():
        try:
            matches = search_log_file(
                log_file=monitor.session.log_file,
                query=query,
                context_lines=context_lines,
                max_results=max_results,
            )

            # Add session_id to each match
            for match in matches:
                match["session_id"] = sid

            all_matches.extend(matches)
            searched_sessions.append(sid)

            # Check if we've hit max_results
            if len(all_matches) >= max_results:
                all_matches = all_matches[:max_results]
                break

        except Exception as e:
            logger.warning(f"Failed to search session {sid}: {str(e)}")
            continue

    logger.info(
        f"Searched {len(searched_sessions)} sessions for '{query}', "
        f"found {len(all_matches)} matches"
    )

    return {
        "matches": all_matches,
        "total_matches": len(all_matches),
        "searched_sessions": searched_sessions,
    }


@mcp.tool()
def cleanup_old_sessions(retention_days: int = 7, dry_run: bool = False) -> dict:
    """Clean up expired session data based on retention policy.

    Removes session log files older than the retention period to free disk space
    and maintain privacy. Useful for regular maintenance and compliance with
    data retention policies.

    Args:
        retention_days: Delete sessions older than N days (1-365, default: 7)
        dry_run: Show what would be deleted without actually deleting (default: False)

    Returns:
        Dictionary with:
        - deleted_sessions: List of deleted session file names
        - total_deleted: Total number of sessions deleted
        - bytes_freed: Total disk space freed in bytes
        - dry_run: Whether this was a dry run

    Raises:
        ToolError: If retention_days is out of range
    """
    from shellsidekick.core.storage import STORAGE_DIR
    from shellsidekick.core.storage import cleanup_old_sessions as cleanup_func

    # Validate retention_days
    if retention_days < 1 or retention_days > 365:
        raise ToolError("retention_days must be between 1 and 365", code="INVALID_RETENTION_DAYS")

    # Run cleanup
    result = cleanup_func(
        sessions_dir=str(STORAGE_DIR), retention_days=retention_days, dry_run=dry_run
    )

    action = "Would delete" if dry_run else "Deleted"
    logger.info(
        f"{action} {result['total_deleted']} sessions "
        f"({result['bytes_freed']} bytes freed, retention={retention_days} days)"
    )

    return result
