"""Context inference logic for suggesting inputs based on prompts."""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from shellsidekick.models.prompt import PromptType
from shellsidekick.utils.security import is_dangerous_operation


@dataclass
class InputSuggestion:
    """A suggested input with confidence and reasoning."""

    input_text: str
    confidence: float  # 0.0-1.0
    source: str  # "pattern_learning", "context_inference", "default"
    reasoning: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "input_text": self.input_text,
            "confidence": self.confidence,
            "source": self.source,
            "reasoning": self.reasoning,
        }


class InputInferenceEngine:
    """Infers expected inputs based on prompt context."""

    def __init__(self, pattern_learner=None):
        """Initialize inference engine.

        Args:
            pattern_learner: Optional PatternLearner instance for pattern-based suggestions
        """
        self.pattern_learner = pattern_learner

    def infer_inputs(
        self, prompt_text: str, prompt_type: PromptType, session_context: Optional[Dict] = None
    ) -> tuple[List[InputSuggestion], List[str]]:
        """Infer expected inputs based on prompt and context.

        Suggestions are prioritized in this order:
        1. Pattern learning (if available) - highest confidence
        2. Context inference (session metadata)
        3. Default suggestions (fallback)

        Args:
            prompt_text: The detected prompt text
            prompt_type: Type of prompt detected
            session_context: Optional session context (metadata, history)

        Returns:
            Tuple of (suggestions, warnings)
        """
        suggestions = []
        warnings = []

        # Check for dangerous operations
        if is_dangerous_operation(prompt_text):
            warnings.append(
                "⚠️  Dangerous operation detected: This prompt involves potentially "
                "destructive actions. Review carefully before proceeding."
            )

        # Try to get pattern-based suggestions first
        pattern_suggestions = self._get_pattern_suggestions(prompt_text)

        # Generate default suggestions based on prompt type
        if prompt_type == PromptType.PASSWORD:
            suggestions = self._suggest_password_inputs()
            warnings.append(
                "Security: Manual password entry required. Never auto-suggest passwords."
            )

        elif prompt_type == PromptType.YES_NO:
            suggestions = self._suggest_yes_no_inputs(prompt_text, session_context)

        elif prompt_type == PromptType.CHOICE:
            suggestions = self._suggest_choice_inputs(prompt_text)

        elif prompt_type == PromptType.PATH:
            suggestions = self._suggest_path_inputs(prompt_text, session_context)

        elif prompt_type == PromptType.COMMAND:
            suggestions = self._suggest_command_inputs(prompt_text)

        elif prompt_type == PromptType.TEXT:
            suggestions = self._suggest_text_inputs(prompt_text, session_context)

        else:  # UNKNOWN
            suggestions = []
            warnings.append("Unknown prompt type - manual input required")

        # Merge pattern suggestions with defaults
        # Pattern suggestions get priority (higher confidence)
        if pattern_suggestions:
            # Create a map of default suggestions by input_text for easy lookup
            default_map = {s.input_text: s for s in suggestions}

            # Add pattern suggestions (they override defaults with higher confidence)
            merged = []
            for pattern_sugg in pattern_suggestions:
                merged.append(pattern_sugg)
                # Remove from defaults if it exists (pattern takes priority)
                default_map.pop(pattern_sugg.input_text, None)

            # Add remaining defaults that weren't covered by patterns
            merged.extend(default_map.values())

            suggestions = merged

        return suggestions, warnings

    def _suggest_password_inputs(self) -> List[InputSuggestion]:
        """Suggest inputs for password prompts (none - security)."""
        return []

    def _suggest_yes_no_inputs(
        self, prompt_text: str, session_context: Optional[Dict] = None
    ) -> List[InputSuggestion]:
        """Suggest yes/no inputs."""
        suggestions = []

        # Check if this is a dangerous operation
        is_dangerous = is_dangerous_operation(prompt_text)

        if is_dangerous:
            # Suggest "no" with higher confidence for dangerous operations
            suggestions.append(
                InputSuggestion(
                    input_text="no",
                    confidence=0.85,
                    source="default",
                    reasoning=(
                        "Recommended: Dangerous operation detected. "
                        "Saying 'no' is the safer choice."
                    ),
                )
            )
            suggestions.append(
                InputSuggestion(
                    input_text="yes",
                    confidence=0.60,
                    source="default",
                    reasoning=(
                        "⚠️  Proceed with caution: This will execute a "
                        "potentially dangerous operation."
                    ),
                )
            )
        else:
            # Normal yes/no suggestions
            context_info = ""
            if session_context and "working_directory" in session_context:
                context_info = f" (working directory: {session_context['working_directory']})"

            suggestions.append(
                InputSuggestion(
                    input_text="yes",
                    confidence=0.75,
                    source="default",
                    reasoning=f"Confirm the operation{context_info}",
                )
            )
            suggestions.append(
                InputSuggestion(
                    input_text="no",
                    confidence=0.75,
                    source="default",
                    reasoning=f"Cancel the operation{context_info}",
                )
            )

        return suggestions

    def _suggest_choice_inputs(self, prompt_text: str) -> List[InputSuggestion]:
        """Suggest inputs for numbered choice prompts."""
        suggestions = []

        # Extract choice numbers from prompt (e.g., [1], [2], [3])
        pattern = r"\[(\d+)\]"
        matches = re.findall(pattern, prompt_text)

        for num in matches:
            suggestions.append(
                InputSuggestion(
                    input_text=num,
                    confidence=0.80,
                    source="default",
                    reasoning=f"Select option {num}",
                )
            )

        return suggestions

    def _suggest_path_inputs(
        self, prompt_text: str, session_context: Optional[Dict] = None
    ) -> List[InputSuggestion]:
        """Suggest path inputs."""
        suggestions = []

        # Suggest current directory
        suggestions.append(
            InputSuggestion(
                input_text="./",
                confidence=0.70,
                source="default",
                reasoning="Current directory (relative path)",
            )
        )

        # Suggest common directories
        suggestions.append(
            InputSuggestion(
                input_text="/tmp/",
                confidence=0.65,
                source="default",
                reasoning="Temporary directory",
            )
        )

        suggestions.append(
            InputSuggestion(
                input_text="/home/", confidence=0.65, source="default", reasoning="Home directory"
            )
        )

        # Context-aware suggestion
        if session_context and "working_directory" in session_context:
            wd = session_context["working_directory"]
            suggestions.insert(
                0,
                InputSuggestion(
                    input_text=wd,
                    confidence=0.80,
                    source="context_inference",
                    reasoning="Current working directory from session context",
                ),
            )

        return suggestions

    def _suggest_command_inputs(self, prompt_text: str) -> List[InputSuggestion]:
        """Suggest safe command inputs."""
        common_commands = [
            ("help", "Display help information"),
            ("exit", "Exit the current session"),
            ("status", "Check status"),
            ("ls", "List directory contents"),
        ]

        suggestions = []
        for cmd, description in common_commands:
            suggestions.append(
                InputSuggestion(
                    input_text=cmd, confidence=0.60, source="default", reasoning=description
                )
            )

        return suggestions

    def _suggest_text_inputs(
        self, prompt_text: str, session_context: Optional[Dict] = None
    ) -> List[InputSuggestion]:
        """Suggest generic text inputs."""
        # For generic text prompts, we can't make good suggestions
        # Return empty list - user must provide input
        return []

    def _get_pattern_suggestions(self, prompt_text: str) -> List[InputSuggestion]:
        """Get suggestions based on learned patterns.

        Args:
            prompt_text: The prompt text to match against patterns

        Returns:
            List of pattern-based suggestions (empty if no patterns found)
        """
        if not self.pattern_learner:
            return []

        # Try to find a matching pattern
        pattern = self.pattern_learner.get_pattern_by_prompt(prompt_text)
        if not pattern:
            return []

        suggestions = []

        # Generate suggestions from pattern responses
        # Sort responses by count (most common first)
        sorted_responses = sorted(pattern.responses.items(), key=lambda x: x[1].count, reverse=True)

        for input_text, stats in sorted_responses:
            # Calculate confidence based on:
            # - Frequency (how many times this response was used)
            # - Success rate (how often it worked)
            # - Total occurrences (more data = higher confidence)

            # Frequency score: normalize by total occurrences
            frequency_score = stats.count / pattern.total_occurrences

            # Success rate score
            success_score = stats.success_rate

            # Combine scores with weights (70% frequency, 30% success)
            confidence = (frequency_score * 0.70) + (success_score * 0.30)

            # Boost confidence for patterns with more data
            if pattern.total_occurrences >= 10:
                confidence = min(0.95, confidence + 0.05)

            reasoning = (
                f"Learned from pattern: used {stats.count}/{pattern.total_occurrences} times "
                f"({stats.count/pattern.total_occurrences*100:.0f}%), "
                f"{stats.success_rate*100:.0f}% success rate"
            )

            suggestions.append(
                InputSuggestion(
                    input_text=input_text,
                    confidence=confidence,
                    source="pattern_learning",
                    reasoning=reasoning,
                )
            )

        return suggestions
