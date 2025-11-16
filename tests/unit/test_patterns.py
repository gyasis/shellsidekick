"""Unit tests for PatternLearner."""

import uuid
from datetime import datetime

import pytest

from shellsidekick.core.patterns import PatternLearner
from shellsidekick.models.input_event import InputSource


class TestPatternLearnerInit:
    """Test PatternLearner initialization."""

    def test_init_without_auto_load(self):
        """Test initialization without auto-loading patterns."""
        learner = PatternLearner(auto_load=False)

        assert learner._events == {}
        assert learner._patterns == {}

    def test_init_with_auto_load_empty_storage(self, tmp_path, monkeypatch):
        """Test auto-load with empty storage doesn't crash."""
        # Mock storage location to empty dir
        from shellsidekick.core import storage

        test_file = tmp_path / "patterns.json"
        monkeypatch.setattr(storage, "PATTERNS_FILE", test_file)

        learner = PatternLearner(auto_load=True)

        # Should initialize with no patterns
        assert len(learner.get_patterns()) == 0


class TestTrackInputEvent:
    """Test event tracking."""

    def test_track_successful_input(self):
        """Test tracking a successful input event."""
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        result = learner.track_input_event(
            session_id=session_id,
            prompt_text="Continue? (yes/no)",
            input_text="yes",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=200,
        )

        assert result["recorded"] is True
        assert result["pattern_updated"] is True
        assert "event_id" in result

    def test_track_failed_input(self):
        """Test tracking a failed input event."""
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        result = learner.track_input_event(
            session_id=session_id,
            prompt_text="Enter number:",
            input_text="invalid",
            success=False,
            input_source=InputSource.USER_TYPED,
            response_time_ms=150,
        )

        assert result["recorded"] is True
        assert result["pattern_updated"] is True

    def test_track_password_redaction(self):
        """Test that password inputs are redacted."""
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        result = learner.track_input_event(
            session_id=session_id,
            prompt_text="Password:",
            input_text="mysecretpassword",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        # Event recorded but pattern not updated for passwords
        assert result["recorded"] is True
        assert result["pattern_updated"] is False

        # Check the stored event has redacted input
        events = learner.get_session_events(session_id)
        assert len(events) == 1
        assert events[0].input_text == "[REDACTED]"

    def test_event_id_is_unique(self):
        """Test that each event gets a unique ID."""
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        result1 = learner.track_input_event(
            session_id=session_id,
            prompt_text="Test:",
            input_text="a",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        result2 = learner.track_input_event(
            session_id=session_id,
            prompt_text="Test:",
            input_text="b",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        assert result1["event_id"] != result2["event_id"]


class TestSessionEvents:
    """Test session event retrieval."""

    def test_get_session_events(self):
        """Test retrieving events for a specific session."""
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        # Track multiple events
        learner.track_input_event(
            session_id=session_id,
            prompt_text="Test 1:",
            input_text="a",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        learner.track_input_event(
            session_id=session_id,
            prompt_text="Test 2:",
            input_text="b",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=150,
        )

        events = learner.get_session_events(session_id)

        assert len(events) == 2
        assert events[0].input_text == "a"
        assert events[1].input_text == "b"

    def test_get_session_events_empty(self):
        """Test retrieving events for nonexistent session."""
        learner = PatternLearner(auto_load=False)

        events = learner.get_session_events("nonexistent-session")

        assert events == []

    def test_events_isolated_by_session(self):
        """Test that events are isolated per session."""
        learner = PatternLearner(auto_load=False)
        session1 = str(uuid.uuid4())
        session2 = str(uuid.uuid4())

        learner.track_input_event(
            session_id=session1,
            prompt_text="Test:",
            input_text="session1",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        learner.track_input_event(
            session_id=session2,
            prompt_text="Test:",
            input_text="session2",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        events1 = learner.get_session_events(session1)
        events2 = learner.get_session_events(session2)

        assert len(events1) == 1
        assert len(events2) == 1
        assert events1[0].input_text == "session1"
        assert events2[0].input_text == "session2"


class TestPatternCreation:
    """Test pattern creation and updates."""

    def test_pattern_created_on_first_event(self):
        """Test that a pattern is created for a new prompt."""
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        learner.track_input_event(
            session_id=session_id,
            prompt_text="Continue? (yes/no)",
            input_text="yes",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        patterns = learner.get_patterns()

        assert len(patterns) == 1
        assert patterns[0].prompt_text == "Continue? (yes/no)"
        assert patterns[0].total_occurrences == 1

    def test_pattern_updated_on_repeated_prompt(self):
        """Test that pattern is updated for repeated prompts."""
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        # Track same prompt 3 times
        for _ in range(3):
            learner.track_input_event(
                session_id=session_id,
                prompt_text="Continue? (yes/no)",
                input_text="yes",
                success=True,
                input_source=InputSource.USER_TYPED,
                response_time_ms=100,
            )

        patterns = learner.get_patterns()

        assert len(patterns) == 1
        assert patterns[0].total_occurrences == 3

    def test_multiple_responses_tracked(self):
        """Test tracking different responses to same prompt."""
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        # Track "yes" twice
        for _ in range(2):
            learner.track_input_event(
                session_id=session_id,
                prompt_text="Continue? (yes/no)",
                input_text="yes",
                success=True,
                input_source=InputSource.USER_TYPED,
                response_time_ms=100,
            )

        # Track "no" once
        learner.track_input_event(
            session_id=session_id,
            prompt_text="Continue? (yes/no)",
            input_text="no",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        patterns = learner.get_patterns()
        pattern = patterns[0]

        assert len(pattern.responses) == 2
        assert pattern.responses["yes"].count == 2
        assert pattern.responses["no"].count == 1

    def test_success_rate_calculation(self):
        """Test success rate is calculated correctly."""
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        # 3 successful
        for _ in range(3):
            learner.track_input_event(
                session_id=session_id,
                prompt_text="Enter number:",
                input_text="5",
                success=True,
                input_source=InputSource.USER_TYPED,
                response_time_ms=100,
            )

        # 1 failed
        learner.track_input_event(
            session_id=session_id,
            prompt_text="Enter number:",
            input_text="5",
            success=False,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        pattern = learner.get_patterns()[0]
        stats = pattern.responses["5"]

        assert stats.count == 4
        assert stats.success_count == 3
        assert stats.success_rate == 0.75


class TestPatternIdGeneration:
    """Test pattern ID generation."""

    def test_same_prompt_same_id(self):
        """Test that identical prompts get the same pattern ID."""
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        # Track same prompt twice
        learner.track_input_event(
            session_id=session_id,
            prompt_text="Test prompt",
            input_text="a",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        learner.track_input_event(
            session_id=session_id,
            prompt_text="Test prompt",
            input_text="b",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        # Should create only one pattern
        patterns = learner.get_patterns()
        assert len(patterns) == 1

    def test_case_insensitive_matching(self):
        """Test that prompt text is normalized (case-insensitive)."""
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        learner.track_input_event(
            session_id=session_id,
            prompt_text="TEST PROMPT",
            input_text="a",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        learner.track_input_event(
            session_id=session_id,
            prompt_text="test prompt",
            input_text="b",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        # Should match same pattern (case-insensitive)
        patterns = learner.get_patterns()
        assert len(patterns) == 1

    def test_whitespace_normalization(self):
        """Test that whitespace is normalized."""
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        learner.track_input_event(
            session_id=session_id,
            prompt_text="  Test prompt  ",
            input_text="a",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        learner.track_input_event(
            session_id=session_id,
            prompt_text="Test prompt",
            input_text="b",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        # Should match same pattern (whitespace-normalized)
        patterns = learner.get_patterns()
        assert len(patterns) == 1


class TestPatternRetrieval:
    """Test pattern retrieval methods."""

    def test_get_all_patterns(self):
        """Test retrieving all patterns."""
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        # Create 3 patterns
        for i in range(3):
            learner.track_input_event(
                session_id=session_id,
                prompt_text=f"Prompt {i}",
                input_text="test",
                success=True,
                input_source=InputSource.USER_TYPED,
                response_time_ms=100,
            )

        patterns = learner.get_patterns()

        assert len(patterns) == 3

    def test_get_pattern_by_prompt(self):
        """Test retrieving a specific pattern by prompt text."""
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        learner.track_input_event(
            session_id=session_id,
            prompt_text="Specific prompt",
            input_text="test",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        pattern = learner.get_pattern_by_prompt("Specific prompt")

        assert pattern is not None
        assert pattern.prompt_text == "Specific prompt"

    def test_get_pattern_by_prompt_not_found(self):
        """Test retrieving nonexistent pattern."""
        learner = PatternLearner(auto_load=False)

        pattern = learner.get_pattern_by_prompt("Nonexistent")

        assert pattern is None


class TestFormattedPatterns:
    """Test formatted pattern output."""

    def test_get_patterns_formatted_basic(self):
        """Test basic formatted pattern retrieval."""
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        learner.track_input_event(
            session_id=session_id,
            prompt_text="Test:",
            input_text="response",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        result = learner.get_patterns_formatted()

        assert "patterns" in result
        assert "total_patterns" in result
        assert result["total_patterns"] == 1

        pattern = result["patterns"][0]
        assert "prompt_text" in pattern
        assert "total_occurrences" in pattern
        assert "most_common_response" in pattern
        assert "all_responses" in pattern

    def test_filter_by_prompt_text(self):
        """Test filtering patterns by prompt text substring."""
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        learner.track_input_event(
            session_id=session_id,
            prompt_text="Delete file?",
            input_text="yes",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        learner.track_input_event(
            session_id=session_id,
            prompt_text="Continue?",
            input_text="yes",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        result = learner.get_patterns_formatted(prompt_filter="Delete")

        assert result["total_patterns"] == 1
        assert "Delete" in result["patterns"][0]["prompt_text"]

    def test_filter_by_min_occurrences(self):
        """Test filtering by minimum occurrences."""
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        # Pattern with 5 occurrences
        for _ in range(5):
            learner.track_input_event(
                session_id=session_id,
                prompt_text="Prompt A",
                input_text="yes",
                success=True,
                input_source=InputSource.USER_TYPED,
                response_time_ms=100,
            )

        # Pattern with 1 occurrence
        learner.track_input_event(
            session_id=session_id,
            prompt_text="Prompt B",
            input_text="no",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        result = learner.get_patterns_formatted(min_occurrences=3)

        assert result["total_patterns"] == 1
        assert result["patterns"][0]["total_occurrences"] >= 3

    def test_sort_by_occurrences(self):
        """Test sorting by occurrence count."""
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        # Create patterns with different occurrence counts
        for i in range(3):
            for _ in range(i + 1):  # 1, 2, 3 occurrences
                learner.track_input_event(
                    session_id=session_id,
                    prompt_text=f"Prompt {i}",
                    input_text="test",
                    success=True,
                    input_source=InputSource.USER_TYPED,
                    response_time_ms=100,
                )

        result = learner.get_patterns_formatted(sort_by="occurrences")

        # Should be sorted descending
        assert result["patterns"][0]["total_occurrences"] == 3
        assert result["patterns"][1]["total_occurrences"] == 2
        assert result["patterns"][2]["total_occurrences"] == 1


class TestPatternPersistence:
    """Test save/load functionality."""

    def test_save_to_storage(self, tmp_path, monkeypatch):
        """Test saving patterns to storage."""
        from shellsidekick.core import storage

        test_file = tmp_path / "patterns.json"
        monkeypatch.setattr(storage, "PATTERNS_FILE", test_file)

        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        learner.track_input_event(
            session_id=session_id,
            prompt_text="Test:",
            input_text="response",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        result = learner.save_to_storage()

        assert result is True
        assert test_file.exists()

    def test_load_from_storage(self, tmp_path, monkeypatch):
        """Test loading patterns from storage."""
        from shellsidekick.core import storage

        test_file = tmp_path / "patterns.json"
        monkeypatch.setattr(storage, "PATTERNS_FILE", test_file)

        # Create and save patterns
        learner1 = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        learner1.track_input_event(
            session_id=session_id,
            prompt_text="Test prompt",
            input_text="test",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        learner1.save_to_storage()

        # Load in new learner
        learner2 = PatternLearner(auto_load=True)

        patterns = learner2.get_patterns()
        assert len(patterns) == 1
        assert patterns[0].prompt_text == "Test prompt"

    def test_persistence_across_restarts(self, tmp_path, monkeypatch):
        """Test patterns survive multiple save/load cycles."""
        from shellsidekick.core import storage

        test_file = tmp_path / "patterns.json"
        monkeypatch.setattr(storage, "PATTERNS_FILE", test_file)

        session_id = str(uuid.uuid4())

        # First instance
        learner1 = PatternLearner(auto_load=False)
        learner1.track_input_event(
            session_id=session_id,
            prompt_text="Prompt 1",
            input_text="a",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        # Second instance (auto-loads)
        learner2 = PatternLearner(auto_load=True)
        learner2.track_input_event(
            session_id=session_id,
            prompt_text="Prompt 2",
            input_text="b",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        # Third instance (should have both patterns)
        learner3 = PatternLearner(auto_load=True)
        patterns = learner3.get_patterns()

        assert len(patterns) == 2
