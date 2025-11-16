"""Unit tests for security utilities."""

import pytest

from shellsidekick.utils.security import (
    get_dangerous_keywords,
    is_dangerous_operation,
    is_password_prompt,
    redact_password,
)


class TestPasswordPromptDetection:
    """Test password prompt detection."""

    def test_detect_password_colon(self):
        """Test detection of 'password:' pattern."""
        assert is_password_prompt("Password:") is True
        assert is_password_prompt("Enter password:") is True

    def test_detect_passphrase_colon(self):
        """Test detection of 'passphrase:' pattern."""
        assert is_password_prompt("Passphrase:") is True
        assert is_password_prompt("Enter passphrase:") is True

    def test_detect_pass_colon(self):
        """Test detection of 'pass:' pattern."""
        assert is_password_prompt("Pass:") is True

    def test_detect_enter_password(self):
        """Test detection of 'enter password' pattern."""
        assert is_password_prompt("Enter password") is True
        assert is_password_prompt("Please enter password") is True

    def test_detect_authentication_required(self):
        """Test detection of 'authentication required' pattern."""
        assert is_password_prompt("Authentication required") is True

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        assert is_password_prompt("PASSWORD:") is True
        assert is_password_prompt("PassPhrase:") is True
        assert is_password_prompt("AUTHENTICATION REQUIRED") is True

    def test_non_password_prompts(self):
        """Test that non-password prompts are not detected."""
        assert is_password_prompt("Enter name:") is False
        assert is_password_prompt("Continue? (yes/no)") is False
        assert is_password_prompt("Select option:") is False

    def test_empty_string(self):
        """Test with empty string."""
        assert is_password_prompt("") is False

    def test_password_in_middle_of_text(self):
        """Test detection when pattern is in middle of text."""
        text = "Please provide credentials\nPassword:"
        assert is_password_prompt(text) is True


class TestDangerousOperationDetection:
    """Test dangerous operation detection."""

    def test_detect_rm_rf_root(self):
        """Test detection of 'rm -rf /' command."""
        assert is_dangerous_operation("rm -rf /") is True
        assert is_dangerous_operation("sudo rm -rf /var") is True

    def test_detect_mkfs(self):
        """Test detection of mkfs command."""
        assert is_dangerous_operation("mkfs /dev/sda1") is True
        assert is_dangerous_operation("mkfs.ext4") is True

    def test_detect_dd_command(self):
        """Test detection of dd command."""
        assert is_dangerous_operation("dd if=/dev/zero") is True
        assert is_dangerous_operation("sudo dd if=/dev/sda") is True

    def test_detect_fork_bomb(self):
        """Test detection of fork bomb."""
        assert is_dangerous_operation(":(){ :|:& };:") is True

    def test_detect_windows_format(self):
        """Test detection of Windows format command."""
        assert is_dangerous_operation("format C:") is True
        assert is_dangerous_operation("format D: /q") is True

    def test_detect_windows_del(self):
        """Test detection of Windows del command."""
        assert is_dangerous_operation("del /f /q") is True
        assert is_dangerous_operation("del /s *.*") is True

    def test_detect_database_delete(self):
        """Test detection of database delete operations."""
        assert is_dangerous_operation("DELETE FROM table") is True
        assert is_dangerous_operation("delete all files") is True
        assert is_dangerous_operation("delete all data") is True

    def test_detect_drop_table(self):
        """Test detection of DROP TABLE."""
        assert is_dangerous_operation("DROP TABLE users") is True
        assert is_dangerous_operation("drop table if exists") is True

    def test_detect_truncate_table(self):
        """Test detection of TRUNCATE TABLE."""
        assert is_dangerous_operation("TRUNCATE TABLE logs") is True

    def test_detect_remove_all(self):
        """Test detection of 'remove all' operations."""
        assert is_dangerous_operation("remove all files") is True
        assert is_dangerous_operation("remove all data") is True

    def test_detect_destroy(self):
        """Test detection of 'destroy' keyword."""
        assert is_dangerous_operation("destroy database") is True
        assert is_dangerous_operation("This will destroy everything") is True

    def test_detect_wipe(self):
        """Test detection of 'wipe' keyword."""
        assert is_dangerous_operation("wipe disk") is True
        assert is_dangerous_operation("This will wipe all data") is True

    def test_detect_erase(self):
        """Test detection of 'erase all' operations."""
        assert is_dangerous_operation("erase all files") is True
        assert is_dangerous_operation("erase all data") is True

    def test_case_insensitive_dangerous(self):
        """Test case-insensitive detection."""
        assert is_dangerous_operation("RM -RF /") is True
        assert is_dangerous_operation("DELETE FROM TABLE") is True
        assert is_dangerous_operation("DROP TABLE") is True

    def test_safe_operations_not_flagged(self):
        """Test that safe operations are not flagged."""
        assert is_dangerous_operation("ls -la") is False
        assert is_dangerous_operation("echo hello") is False
        assert is_dangerous_operation("cat file.txt") is False
        assert is_dangerous_operation("SELECT * FROM users") is False

    def test_empty_text(self):
        """Test with empty text."""
        assert is_dangerous_operation("") is False

    def test_dangerous_in_prompt(self):
        """Test detection in interactive prompts."""
        prompt = "This will delete all files. Continue? (yes/no)"
        assert is_dangerous_operation(prompt) is True


class TestPasswordRedaction:
    """Test password redaction."""

    def test_redact_password_colon(self):
        """Test redacting password after 'password:' prompt."""
        text = "Password: mysecret123"
        result = redact_password(text)
        assert "[REDACTED]" in result
        assert "mysecret123" not in result

    def test_redact_passphrase_colon(self):
        """Test redacting passphrase."""
        text = "Passphrase: secret_passphrase"
        result = redact_password(text)
        assert "[REDACTED]" in result
        assert "secret_passphrase" not in result

    def test_redact_pass_colon(self):
        """Test redacting 'pass:' pattern."""
        text = "Pass: mypass"
        result = redact_password(text)
        assert "[REDACTED]" in result
        assert "mypass" not in result

    def test_preserve_prompt_text(self):
        """Test that prompt text is preserved."""
        text = "Password: secret"
        result = redact_password(text)
        assert "Password:" in result or "password:" in result

    def test_multiple_passwords(self):
        """Test redacting multiple passwords in text."""
        text = "Password: first\nPassphrase: second"
        result = redact_password(text)
        assert "first" not in result
        assert "second" not in result
        assert result.count("[REDACTED]") == 2

    def test_case_insensitive_redaction(self):
        """Test case-insensitive redaction."""
        text = "PASSWORD: secret"
        result = redact_password(text)
        assert "[REDACTED]" in result
        assert "secret" not in result

    def test_no_password_in_text(self):
        """Test text without passwords remains unchanged."""
        text = "Enter name: john"
        result = redact_password(text)
        assert result == text

    def test_empty_text_redaction(self):
        """Test redacting empty text."""
        result = redact_password("")
        assert result == ""


class TestGetDangerousKeywords:
    """Test dangerous keyword extraction."""

    def test_extract_single_keyword(self):
        """Test extracting single dangerous keyword."""
        text = "rm -rf /var"
        keywords = get_dangerous_keywords(text)
        assert len(keywords) >= 1
        assert any("rm -rf /" in kw.lower() for kw in keywords)

    def test_extract_multiple_keywords(self):
        """Test extracting multiple keywords from text."""
        text = "This will delete all files and drop table users"
        keywords = get_dangerous_keywords(text)
        assert len(keywords) >= 2

    def test_extract_database_keywords(self):
        """Test extracting database-related keywords."""
        text = "DROP TABLE users; TRUNCATE TABLE logs;"
        keywords = get_dangerous_keywords(text)
        assert len(keywords) >= 2
        assert any("drop" in kw.lower() for kw in keywords)
        assert any("truncate" in kw.lower() for kw in keywords)

    def test_no_keywords_in_safe_text(self):
        """Test that safe text returns empty list."""
        text = "List all files in directory"
        keywords = get_dangerous_keywords(text)
        assert keywords == []

    def test_empty_text_keywords(self):
        """Test with empty text."""
        keywords = get_dangerous_keywords("")
        assert keywords == []

    def test_keyword_case_insensitive(self):
        """Test case-insensitive keyword extraction."""
        text = "DELETE ALL DATA"
        keywords = get_dangerous_keywords(text)
        assert len(keywords) >= 1

    def test_exact_match_returned(self):
        """Test that exact matched text is returned."""
        text = "wipe disk"
        keywords = get_dangerous_keywords(text)
        assert len(keywords) == 1
        assert "wipe" in keywords[0].lower()


class TestSecurityEdgeCases:
    """Test edge cases and combinations."""

    def test_password_and_dangerous_combined(self):
        """Test text with both password and dangerous patterns."""
        text = "Password: secret\nThis will delete all files"
        assert is_password_prompt(text) is True
        assert is_dangerous_operation(text) is True

    def test_unicode_text(self):
        """Test with unicode characters."""
        text = "Password: \u0073\u0065\u0063\u0072\u0065\u0074"  # "secret" in unicode
        assert is_password_prompt(text) is True

    def test_multiline_text(self):
        """Test with multiline text."""
        text = """
        Starting migration...
        This will delete all records
        Continue? (yes/no):
        """
        assert is_dangerous_operation(text) is True

    def test_whitespace_variations(self):
        """Test patterns with various whitespace."""
        assert is_password_prompt("Password   :") is True
        assert is_dangerous_operation("rm   -rf   /") is True

    def test_very_long_text(self):
        """Test with very long text."""
        # Build realistic long text with proper word boundaries
        text = ("Normal log output. " * 500) + "This will delete all files. " + ("More log output. " * 500)
        assert is_dangerous_operation(text) is True

    def test_special_characters(self):
        """Test text with special characters."""
        text = "password: p@ssw0rd!#$%"
        result = redact_password(text)
        assert "p@ssw0rd!#$%" not in result
