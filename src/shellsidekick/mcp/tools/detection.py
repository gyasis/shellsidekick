"""MCP tools for prompt detection and analysis."""

from typing import Optional, Dict

from fastmcp.exceptions import ToolError

from shellsidekick.mcp.server import mcp
from shellsidekick.mcp.session_state import active_sessions, pattern_learner
from shellsidekick.core.detector import PromptDetector
from shellsidekick.core.inference import InputInferenceEngine
from shellsidekick.models.prompt import PromptType
from shellsidekick.utils.logging import get_logger

logger = get_logger(__name__)


@mcp.tool()
def detect_input_prompt(
    session_id: str,
    min_confidence: float = 0.70
) -> dict:
    """Analyze session output to detect if terminal is waiting for input.

    Args:
        session_id: Session ID to analyze
        min_confidence: Minimum confidence threshold (0.0-1.0), default 0.70

    Returns:
        Dictionary with:
        - detected: Boolean indicating if prompt was detected
        - prompt: PromptDetection dict if detected, None otherwise

    Raises:
        ToolError: If session not found or invalid confidence value
    """
    # Validate session exists
    if session_id not in active_sessions:
        raise ToolError(
            f"Session {session_id} not found",
            code="SESSION_NOT_FOUND"
        )

    # Validate confidence range
    if not 0.0 <= min_confidence <= 1.0:
        raise ToolError(
            "Confidence must be between 0.0 and 1.0",
            code="INVALID_CONFIDENCE"
        )

    monitor = active_sessions[session_id]

    # Get recent content from session
    try:
        content, _ = monitor.get_updates()
    except Exception as e:
        raise ToolError(
            f"Failed to read session content: {str(e)}",
            code="FILE_READ_ERROR"
        )

    # Initialize detector
    detector = PromptDetector(min_confidence=min_confidence)

    # Detect prompt
    detection = detector.detect(
        content,
        file_position=monitor.session.file_position
    )

    if detection:
        logger.info(
            f"Detected {detection.prompt_type.value} prompt in session {session_id} "
            f"(confidence: {detection.confidence:.2f})"
        )

        return {
            "detected": True,
            "prompt": detection.to_dict()
        }
    else:
        return {
            "detected": False,
            "prompt": None
        }


@mcp.tool()
def infer_expected_input(
    prompt_text: str,
    prompt_type: str,
    session_context: Optional[Dict] = None
) -> dict:
    """Suggest appropriate inputs based on prompt context.

    Args:
        prompt_text: The detected prompt text
        prompt_type: Type of prompt (password, yes_no, choice, path, text, command, unknown)
        session_context: Optional session context (metadata, history)

    Returns:
        Dictionary with:
        - suggestions: List of input suggestions with confidence, source, and reasoning
        - warnings: List of warnings about dangerous operations

    Raises:
        ToolError: If prompt_type is invalid
    """
    # Validate prompt_type
    try:
        pt = PromptType(prompt_type)
    except ValueError:
        raise ToolError(
            f"Invalid prompt_type: {prompt_type}. Must be one of: "
            f"{', '.join([t.value for t in PromptType])}",
            code="INVALID_PROMPT_TYPE"
        )

    # Initialize inference engine with pattern learning
    engine = InputInferenceEngine(pattern_learner=pattern_learner)

    # Get suggestions and warnings
    suggestions, warnings = engine.infer_inputs(
        prompt_text=prompt_text,
        prompt_type=pt,
        session_context=session_context
    )

    logger.info(
        f"Inferred {len(suggestions)} suggestions for {prompt_type} prompt: '{prompt_text}'"
    )

    if warnings:
        logger.warning(
            f"Generated {len(warnings)} warnings for prompt: '{prompt_text}'"
        )

    return {
        "suggestions": [s.to_dict() for s in suggestions],
        "warnings": warnings
    }
