"""Integration tests for context-aware input suggestions (User Story 2)."""



def test_dangerous_operation_warning_integration():
    """Test dangerous operation detection in real scenario."""
    from shellsidekick.core.inference import InputInferenceEngine
    from shellsidekick.models.prompt import PromptType

    # Simulate a database migration script with dangerous operation
    prompt_text = """
    WARNING: This migration will:
    - Delete 3 tables
    - Remove all data from users table
    - Drop indexes

    Continue with migration? (yes/no):
    """

    engine = InputInferenceEngine()
    suggestions, warnings = engine.infer_inputs(
        prompt_text=prompt_text, prompt_type=PromptType.YES_NO
    )

    # Should detect multiple dangerous keywords
    assert len(warnings) > 0
    warning_text = " ".join(warnings).lower()
    assert "dangerous" in warning_text

    # Should suggest both yes and no
    assert len(suggestions) == 2

    # "no" should be recommended
    no_suggestion = next((s for s in suggestions if s.input_text == "no"), None)
    assert no_suggestion is not None
    assert no_suggestion.confidence > 0.80
    assert (
        "dangerous" in no_suggestion.reasoning.lower() or "safe" in no_suggestion.reasoning.lower()
    )


def test_context_aware_path_suggestion():
    """Test path suggestions using session context."""
    from shellsidekick.core.inference import InputInferenceEngine
    from shellsidekick.models.prompt import PromptType

    # Session context from a web app deployment
    session_context = {
        "working_directory": "/var/www/myapp",
        "recent_commands": ["git pull", "npm install", "npm run build"],
    }

    engine = InputInferenceEngine()
    suggestions, warnings = engine.infer_inputs(
        prompt_text="Enter log file path:",
        prompt_type=PromptType.PATH,
        session_context=session_context,
    )

    # Should prioritize working directory
    assert len(suggestions) > 0
    first_suggestion = suggestions[0]
    assert first_suggestion.input_text == "/var/www/myapp"
    assert first_suggestion.source == "context_inference"


def test_password_security_warnings():
    """Test that password prompts trigger security warnings."""
    from shellsidekick.core.inference import InputInferenceEngine
    from shellsidekick.models.prompt import PromptType

    engine = InputInferenceEngine()
    suggestions, warnings = engine.infer_inputs(
        prompt_text="Enter database password:", prompt_type=PromptType.PASSWORD
    )

    # Should NOT suggest passwords
    assert len(suggestions) == 0

    # Should have security warning
    assert len(warnings) > 0
    warning_text = " ".join(warnings).lower()
    assert "security" in warning_text or "manual" in warning_text


def test_choice_extraction_from_menu():
    """Test extracting choices from numbered menu."""
    from shellsidekick.core.inference import InputInferenceEngine
    from shellsidekick.models.prompt import PromptType

    menu_prompt = """
    Select deployment environment:
    [1] Development
    [2] Staging
    [3] Production
    [4] Cancel

    Enter choice:
    """

    engine = InputInferenceEngine()
    suggestions, warnings = engine.infer_inputs(
        prompt_text=menu_prompt, prompt_type=PromptType.CHOICE
    )

    # Should extract all 4 choices
    assert len(suggestions) >= 4

    input_texts = [s.input_text for s in suggestions]
    assert "1" in input_texts
    assert "2" in input_texts
    assert "3" in input_texts
    assert "4" in input_texts


def test_command_suggestions_safety():
    """Test that command suggestions are safe."""
    from shellsidekick.core.inference import InputInferenceEngine
    from shellsidekick.models.prompt import PromptType

    engine = InputInferenceEngine()
    suggestions, warnings = engine.infer_inputs(
        prompt_text="admin> Enter command:", prompt_type=PromptType.COMMAND
    )

    # Should only suggest safe commands
    assert len(suggestions) > 0

    for suggestion in suggestions:
        cmd = suggestion.input_text.lower()
        # Should NOT suggest dangerous commands
        assert "rm" not in cmd
        assert "delete" not in cmd
        assert "format" not in cmd

        # Should suggest helpful commands
        safe_commands = ["help", "exit", "status", "ls"]
        assert any(safe in cmd for safe in safe_commands)


def test_integration_end_to_end_suggestions():
    """End-to-end test: detect prompt and infer inputs."""
    from shellsidekick.core.detector import PromptDetector
    from shellsidekick.core.inference import InputInferenceEngine
    from shellsidekick.models.prompt import PromptType

    # Simulate terminal output
    terminal_output = """
    Deploying application to production...
    Configuration validated.
    Database connection: OK

    WARNING: This will overwrite the current production deployment!
    Proceed? (yes/no):
    """

    # Step 1: Detect the prompt
    detector = PromptDetector(min_confidence=0.70)
    detection = detector.detect(terminal_output)

    assert detection is not None
    assert detection.prompt_type == PromptType.YES_NO

    # Step 2: Infer appropriate inputs - use full context for danger detection
    engine = InputInferenceEngine()
    suggestions, warnings = engine.infer_inputs(
        prompt_text=terminal_output,  # Use full output for context
        prompt_type=detection.prompt_type,
    )

    # Should suggest both options
    assert len(suggestions) == 2

    # Should have yes and no suggestions
    input_texts = [s.input_text for s in suggestions]
    assert "yes" in input_texts
    assert "no" in input_texts

    # Each should have reasoning
    for suggestion in suggestions:
        assert len(suggestion.reasoning) > 0
        assert suggestion.confidence > 0.0
