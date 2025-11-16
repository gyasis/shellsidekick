"""Contract tests for pattern persistence (T056)."""

import pytest
import uuid
from pathlib import Path


class TestPatternPersistence:
    """Contract tests for pattern loading/saving to JSON."""

    def test_save_and_load_patterns(self, tmp_path):
        """Test that patterns are saved and can be reloaded."""
        from shellsidekick.core.patterns import PatternLearner
        from shellsidekick.models.input_event import InputSource
        from shellsidekick.core import storage

        # Temporarily override storage location for test
        original_patterns_file = storage.PATTERNS_FILE
        test_patterns_file = tmp_path / "patterns.json"
        storage.PATTERNS_FILE = test_patterns_file

        try:
            # Create learner and track some events
            learner1 = PatternLearner(auto_load=False)
            session_id = str(uuid.uuid4())

            for _ in range(3):
                learner1.track_input_event(
                    session_id=session_id,
                    prompt_text="Continue? (yes/no)",
                    input_text="yes",
                    success=True,
                    input_source=InputSource.USER_TYPED,
                    response_time_ms=200
                )

            # Manually save patterns
            assert learner1.save_to_storage() is True
            assert test_patterns_file.exists()

            # Create new learner and load patterns
            learner2 = PatternLearner(auto_load=False)
            loaded_count = learner2.load_from_storage()

            assert loaded_count == 1
            patterns = learner2.get_patterns()
            assert len(patterns) == 1

            pattern = patterns[0]
            assert pattern.prompt_text == "Continue? (yes/no)"
            assert pattern.total_occurrences == 3
            assert "yes" in pattern.responses
            assert pattern.responses["yes"].count == 3

        finally:
            # Restore original storage location
            storage.PATTERNS_FILE = original_patterns_file

    def test_patterns_survive_restart(self, tmp_path):
        """Test that patterns persist across PatternLearner instances."""
        from shellsidekick.core.patterns import PatternLearner
        from shellsidekick.models.input_event import InputSource
        from shellsidekick.core import storage
        import uuid

        # Temporarily override storage location
        original_patterns_file = storage.PATTERNS_FILE
        test_patterns_file = tmp_path / "patterns.json"
        storage.PATTERNS_FILE = test_patterns_file

        try:
            session_id = str(uuid.uuid4())

            # First session: create and save patterns
            learner1 = PatternLearner(auto_load=False)
            learner1.track_input_event(
                session_id=session_id,
                prompt_text="Deploy? (yes/no)",
                input_text="no",
                success=True,
                input_source=InputSource.USER_TYPED,
                response_time_ms=150
            )

            # Simulate server restart - create new learner with auto_load
            learner2 = PatternLearner(auto_load=True)

            # Should have loaded the pattern
            patterns = learner2.get_patterns()
            assert len(patterns) == 1
            assert patterns[0].prompt_text == "Deploy? (yes/no)"
            assert patterns[0].responses["no"].count == 1

            # Add more data
            learner2.track_input_event(
                session_id=session_id,
                prompt_text="Deploy? (yes/no)",
                input_text="no",
                success=True,
                input_source=InputSource.USER_TYPED,
                response_time_ms=140
            )

            # Another restart
            learner3 = PatternLearner(auto_load=True)
            patterns = learner3.get_patterns()
            assert len(patterns) == 1
            assert patterns[0].responses["no"].count == 2

        finally:
            storage.PATTERNS_FILE = original_patterns_file

    def test_empty_storage_loads_gracefully(self, tmp_path):
        """Test that loading from empty storage doesn't crash."""
        from shellsidekick.core.patterns import PatternLearner
        from shellsidekick.core import storage

        # Point to non-existent file
        original_patterns_file = storage.PATTERNS_FILE
        test_patterns_file = tmp_path / "nonexistent.json"
        storage.PATTERNS_FILE = test_patterns_file

        try:
            # Should not crash, just load 0 patterns
            learner = PatternLearner(auto_load=True)
            patterns = learner.get_patterns()
            assert len(patterns) == 0

        finally:
            storage.PATTERNS_FILE = original_patterns_file

    def test_pattern_datetime_serialization(self, tmp_path):
        """Test that datetime fields serialize/deserialize correctly."""
        from shellsidekick.core.patterns import PatternLearner
        from shellsidekick.models.input_event import InputSource
        from shellsidekick.core import storage
        import uuid
        from datetime import datetime

        original_patterns_file = storage.PATTERNS_FILE
        test_patterns_file = tmp_path / "patterns.json"
        storage.PATTERNS_FILE = test_patterns_file

        try:
            session_id = str(uuid.uuid4())

            # Create pattern
            learner1 = PatternLearner(auto_load=False)
            before_time = datetime.now()

            learner1.track_input_event(
                session_id=session_id,
                prompt_text="Test prompt",
                input_text="test",
                success=True,
                input_source=InputSource.USER_TYPED,
                response_time_ms=100
            )

            after_time = datetime.now()

            # Load pattern
            learner2 = PatternLearner(auto_load=True)
            patterns = learner2.get_patterns()

            assert len(patterns) == 1
            pattern = patterns[0]

            # Check datetime fields are properly deserialized
            assert isinstance(pattern.created_at, datetime)
            assert isinstance(pattern.last_seen, datetime)
            assert before_time <= pattern.created_at <= after_time
            assert before_time <= pattern.last_seen <= after_time

        finally:
            storage.PATTERNS_FILE = original_patterns_file
