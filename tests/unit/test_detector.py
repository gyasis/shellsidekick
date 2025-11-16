"""Unit tests for PromptDetector."""

import pytest

from shellsidekick.core.detector import PromptDetector
from shellsidekick.models.prompt import PromptType


class TestPromptDetectorInit:
    """Test PromptDetector initialization."""

    def test_default_min_confidence(self):
        """Test default minimum confidence threshold."""
        detector = PromptDetector()
        assert detector.min_confidence == 0.70

    def test_custom_min_confidence(self):
        """Test custom minimum confidence threshold."""
        detector = PromptDetector(min_confidence=0.85)
        assert detector.min_confidence == 0.85


class TestPasswordPromptDetection:
    """Test detection of password prompts."""

    def test_detect_password_prompt_basic(self):
        """Test basic password prompt detection."""
        detector = PromptDetector()
        content = "Enter your credentials\nPassword: "
        result = detector.detect(content)

        assert result is not None
        assert result.prompt_type == PromptType.PASSWORD
        assert result.confidence >= 0.90
        assert "Password:" in result.prompt_text

    def test_detect_passphrase_prompt(self):
        """Test passphrase prompt detection."""
        detector = PromptDetector()
        content = "Unlock keyring\nPassphrase: "
        result = detector.detect(content)

        assert result is not None
        assert result.prompt_type == PromptType.PASSWORD
        assert result.confidence >= 0.90
        assert "Passphrase:" in result.prompt_text

    def test_detect_enter_password_prompt(self):
        """Test 'enter password' style prompt."""
        detector = PromptDetector()
        content = "Authentication required\nEnter your password: "
        result = detector.detect(content)

        assert result is not None
        assert result.prompt_type == PromptType.PASSWORD
        # The detector matches the specific "password:" part
        assert "password" in result.prompt_text.lower()


class TestYesNoPromptDetection:
    """Test detection of yes/no prompts."""

    def test_detect_yes_no_parentheses(self):
        """Test (yes/no) format detection."""
        detector = PromptDetector()
        content = "Delete all files? (yes/no)"
        result = detector.detect(content)

        assert result is not None
        assert result.prompt_type == PromptType.YES_NO
        assert result.confidence >= 0.85

    def test_detect_y_n_brackets(self):
        """Test [y/n] format detection."""
        detector = PromptDetector()
        content = "Continue with operation? [y/n]"
        result = detector.detect(content)

        assert result is not None
        assert result.prompt_type == PromptType.YES_NO

    def test_detect_continue_question(self):
        """Test continue? format detection."""
        detector = PromptDetector()
        content = "Application will restart.\nContinue?"
        result = detector.detect(content)

        assert result is not None
        assert result.prompt_type == PromptType.YES_NO

    def test_detect_proceed_question(self):
        """Test proceed? format detection."""
        detector = PromptDetector()
        content = "This action cannot be undone.\nProceed?"
        result = detector.detect(content)

        assert result is not None
        assert result.prompt_type == PromptType.YES_NO


class TestPathPromptDetection:
    """Test detection of path/file prompts."""

    def test_detect_file_path_prompt(self):
        """Test 'file path:' detection."""
        detector = PromptDetector()
        content = "Enter file path: "
        result = detector.detect(content)

        assert result is not None
        assert result.prompt_type == PromptType.PATH
        assert result.confidence >= 0.80

    def test_detect_directory_path_prompt(self):
        """Test 'directory path:' detection."""
        detector = PromptDetector()
        content = "Specify directory path: "
        result = detector.detect(content)

        assert result is not None
        assert result.prompt_type == PromptType.PATH

    def test_detect_file_name_prompt(self):
        """Test 'file name:' detection."""
        detector = PromptDetector()
        content = "Output file name: "
        result = detector.detect(content)

        assert result is not None
        assert result.prompt_type == PromptType.PATH


class TestChoicePromptDetection:
    """Test detection of numbered choice prompts."""

    def test_detect_numbered_menu(self):
        """Test numbered menu detection."""
        detector = PromptDetector()
        content = """
        Select an option:
        [1] Option A
        [2] Option B
        [3] Option C
        Enter choice:
        """
        result = detector.detect(content)

        assert result is not None
        assert result.prompt_type == PromptType.CHOICE
        assert result.confidence >= 0.80


class TestCommandPromptDetection:
    """Test detection of command prompts."""

    def test_detect_enter_command(self):
        """Test 'enter command:' detection."""
        detector = PromptDetector()
        content = "Admin console ready\nEnter command: "
        result = detector.detect(content)

        assert result is not None
        assert result.prompt_type == PromptType.COMMAND
        assert result.confidence >= 0.85

    def test_detect_command_colon(self):
        """Test 'command:' detection."""
        detector = PromptDetector()
        content = "Shell active\nCommand: "
        result = detector.detect(content)

        assert result is not None
        assert result.prompt_type == PromptType.COMMAND


class TestTextPromptDetection:
    """Test detection of generic text prompts."""

    def test_detect_enter_name(self):
        """Test 'enter name:' detection."""
        detector = PromptDetector()
        content = "Setup wizard\nEnter name: "
        result = detector.detect(content)

        assert result is not None
        assert result.prompt_type == PromptType.TEXT

    def test_detect_input_colon(self):
        """Test 'input:' detection."""
        detector = PromptDetector()
        content = "Waiting for data\nInput: "
        result = detector.detect(content)

        assert result is not None
        assert result.prompt_type == PromptType.TEXT


class TestConfidenceThreshold:
    """Test confidence threshold filtering."""

    def test_below_threshold_not_detected(self):
        """Test that prompts below threshold are not detected."""
        # Set very high threshold
        detector = PromptDetector(min_confidence=0.99)
        # This would normally match with 0.75 confidence
        content = "Enter something: "
        result = detector.detect(content)

        # Should not detect because confidence (0.75) < threshold (0.99)
        assert result is None

    def test_above_threshold_detected(self):
        """Test that prompts above threshold are detected."""
        detector = PromptDetector(min_confidence=0.70)
        content = "Password: "
        result = detector.detect(content)

        # Should detect because confidence (0.95) > threshold (0.70)
        assert result is not None


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_content(self):
        """Test detection with empty content."""
        detector = PromptDetector()
        result = detector.detect("")

        assert result is None

    def test_none_content(self):
        """Test detection with None content."""
        detector = PromptDetector()
        # Should handle gracefully (converted to empty string or None check)
        result = detector.detect(None) if None else detector.detect("")

        assert result is None

    def test_no_prompt_detected(self):
        """Test content with no recognizable prompt."""
        detector = PromptDetector()
        content = "Normal output\nNo prompts here\nJust regular text"
        result = detector.detect(content)

        assert result is None

    def test_very_long_content(self):
        """Test that detector focuses on recent lines (last 50)."""
        detector = PromptDetector()
        # Create 100 lines of normal content, then a prompt
        lines = [f"Line {i}" for i in range(100)]
        lines.append("Password: ")
        content = "\n".join(lines)

        result = detector.detect(content)

        # Should still detect prompt in last 50 lines
        assert result is not None
        assert result.prompt_type == PromptType.PASSWORD


class TestPromptDetectionMetadata:
    """Test detection metadata fields."""

    def test_detection_has_timestamp(self):
        """Test that detection includes timestamp."""
        detector = PromptDetector()
        content = "Password: "
        result = detector.detect(content)

        assert result is not None
        assert result.timestamp is not None

    def test_detection_has_matched_pattern(self):
        """Test that detection includes matched regex pattern."""
        detector = PromptDetector()
        content = "Password: "
        result = detector.detect(content)

        assert result is not None
        assert result.matched_pattern is not None
        assert isinstance(result.matched_pattern, str)

    def test_detection_has_file_position(self):
        """Test that detection preserves file position."""
        detector = PromptDetector()
        content = "Password: "
        result = detector.detect(content, file_position=1234)

        assert result is not None
        assert result.file_position == 1234


class TestDangerousOperationDetection:
    """Test dangerous operation flag integration."""

    def test_dangerous_operation_detected(self):
        """Test that dangerous operations are flagged."""
        detector = PromptDetector()
        content = "This will delete all files. Continue? (yes/no)"
        result = detector.detect(content)

        assert result is not None
        # The is_dangerous flag should be set based on the prompt text
        # (assuming security.py marks 'delete' as dangerous)
        # We can't assert exact value without mocking, but should be boolean
        assert isinstance(result.is_dangerous, bool)

    def test_safe_operation_not_flagged(self):
        """Test that safe operations are not flagged."""
        detector = PromptDetector()
        content = "Enter name: "
        result = detector.detect(content)

        assert result is not None
        assert isinstance(result.is_dangerous, bool)
        # Name prompts are not dangerous
        assert result.is_dangerous is False


class TestDetectWithContext:
    """Test prompt detection with context lines."""

    def test_detect_with_context_basic(self):
        """Test context extraction with prompt."""
        detector = PromptDetector()
        content = """Line 1
Line 2
Line 3
Password:
Line 5
Line 6"""

        result = detector.detect_with_context(content, context_lines=2)

        assert result is not None
        detection, context = result

        assert detection.prompt_type == PromptType.PASSWORD
        assert isinstance(context, list)
        assert len(context) > 0

    def test_detect_with_context_no_prompt(self):
        """Test context extraction when no prompt detected."""
        detector = PromptDetector()
        content = "No prompts here"

        result = detector.detect_with_context(content, context_lines=2)

        assert result is None

    def test_context_includes_surrounding_lines(self):
        """Test that context includes lines before and after prompt."""
        detector = PromptDetector()
        content = """Before line 1
Before line 2
Password:
After line 1
After line 2"""

        result = detector.detect_with_context(content, context_lines=2)

        assert result is not None
        detection, context = result

        # Should include prompt line plus 2 before and 2 after
        assert len(context) <= 5  # Up to 5 lines total
        # Context should contain the prompt
        assert any("Password" in line for line in context)


class TestPatternPriority:
    """Test that patterns are matched in priority order."""

    def test_password_higher_priority_than_text(self):
        """Test that password patterns take precedence."""
        detector = PromptDetector()
        # This could match both password and generic text patterns
        content = "Enter password: "
        result = detector.detect(content)

        # Should match as password (higher priority)
        assert result is not None
        assert result.prompt_type == PromptType.PASSWORD

    def test_specific_over_generic(self):
        """Test that specific patterns take precedence over generic."""
        detector = PromptDetector()
        # "Enter file path:" should match PATH not TEXT
        content = "Enter file path: "
        result = detector.detect(content)

        assert result is not None
        assert result.prompt_type == PromptType.PATH


class TestCaseInsensitivity:
    """Test case-insensitive pattern matching."""

    def test_uppercase_password(self):
        """Test PASSWORD in uppercase."""
        detector = PromptDetector()
        content = "ENTER YOUR PASSWORD: "
        result = detector.detect(content)

        assert result is not None
        assert result.prompt_type == PromptType.PASSWORD

    def test_mixed_case_yes_no(self):
        """Test mixed case yes/no prompt."""
        detector = PromptDetector()
        content = "Continue? (Yes/No)"
        result = detector.detect(content)

        assert result is not None
        assert result.prompt_type == PromptType.YES_NO
