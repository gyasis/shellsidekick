"""Contract tests for history and pattern retrieval MCP tools."""

import pytest


class TestGetLearnedPatterns:
    """Contract tests for get_learned_patterns tool (User Story 3)."""

    def test_get_all_patterns_empty(self):
        """Test getting patterns when none exist."""
        from shellsidekick.core.patterns import PatternLearner

        learner = PatternLearner(auto_load=False)

        # Get patterns (should return empty structure)
        result = learner.get_patterns_formatted()

        assert "patterns" in result
        assert "total_patterns" in result
        assert result["total_patterns"] == 0
        assert len(result["patterns"]) == 0

    def test_get_all_patterns_with_data(self):
        """Test getting all patterns after tracking events."""
        from shellsidekick.core.patterns import PatternLearner
        from shellsidekick.models.input_event import InputSource
        import uuid

        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        # Track multiple events
        learner.track_input_event(
            session_id=session_id,
            prompt_text="Continue? (yes/no)",
            input_text="yes",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=200
        )

        learner.track_input_event(
            session_id=session_id,
            prompt_text="Restart service? (yes/no)",
            input_text="no",
            success=True,
            input_source=InputSource.AI_SUGGESTED,
            response_time_ms=150
        )

        # Get all patterns
        result = learner.get_patterns_formatted()

        assert result["total_patterns"] == 2
        assert len(result["patterns"]) == 2

        # Each pattern should have required fields
        for pattern in result["patterns"]:
            assert "prompt_text" in pattern
            assert "total_occurrences" in pattern
            assert "most_common_response" in pattern
            assert "all_responses" in pattern
            assert "last_seen" in pattern

            # Most common response should have required fields
            mcr = pattern["most_common_response"]
            assert "input_text" in mcr
            assert "count" in mcr
            assert "success_rate" in mcr

    def test_filter_patterns_by_prompt_text(self):
        """Test filtering patterns by prompt text substring."""
        from shellsidekick.core.patterns import PatternLearner
        from shellsidekick.models.input_event import InputSource
        import uuid

        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        # Track events with different prompts
        learner.track_input_event(
            session_id=session_id,
            prompt_text="Restart service? (yes/no)",
            input_text="yes",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=200
        )

        learner.track_input_event(
            session_id=session_id,
            prompt_text="Continue? (yes/no)",
            input_text="yes",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=150
        )

        # Filter for "Restart"
        result = learner.get_patterns_formatted(prompt_filter="Restart")

        assert result["total_patterns"] == 1
        assert len(result["patterns"]) == 1
        assert "Restart" in result["patterns"][0]["prompt_text"]

    def test_filter_by_min_occurrences(self):
        """Test filtering patterns by minimum occurrences."""
        from shellsidekick.core.patterns import PatternLearner
        from shellsidekick.models.input_event import InputSource
        import uuid

        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        # Track one prompt 3 times
        for _ in range(3):
            learner.track_input_event(
                session_id=session_id,
                prompt_text="Continue? (yes/no)",
                input_text="yes",
                success=True,
                input_source=InputSource.USER_TYPED,
                response_time_ms=200
            )

        # Track another prompt once
        learner.track_input_event(
            session_id=session_id,
            prompt_text="Restart? (yes/no)",
            input_text="no",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=150
        )

        # Filter for min_occurrences=3
        result = learner.get_patterns_formatted(min_occurrences=3)

        assert result["total_patterns"] == 1
        assert result["patterns"][0]["total_occurrences"] >= 3

    def test_sort_patterns_by_occurrences(self):
        """Test sorting patterns by occurrence count."""
        from shellsidekick.core.patterns import PatternLearner
        from shellsidekick.models.input_event import InputSource
        import uuid

        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        # Track prompt A 5 times
        for _ in range(5):
            learner.track_input_event(
                session_id=session_id,
                prompt_text="Prompt A",
                input_text="yes",
                success=True,
                input_source=InputSource.USER_TYPED,
                response_time_ms=200
            )

        # Track prompt B 2 times
        for _ in range(2):
            learner.track_input_event(
                session_id=session_id,
                prompt_text="Prompt B",
                input_text="no",
                success=True,
                input_source=InputSource.USER_TYPED,
                response_time_ms=150
            )

        # Sort by occurrences (descending)
        result = learner.get_patterns_formatted(sort_by="occurrences")

        patterns = result["patterns"]
        assert len(patterns) == 2

        # Should be sorted: 5 occurrences first, then 2
        assert patterns[0]["total_occurrences"] == 5
        assert patterns[1]["total_occurrences"] == 2

    def test_pattern_success_rate_calculation(self):
        """Test that success rate is calculated correctly."""
        from shellsidekick.core.patterns import PatternLearner
        from shellsidekick.models.input_event import InputSource
        import uuid

        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        # Track 3 successful and 1 failed
        for _ in range(3):
            learner.track_input_event(
                session_id=session_id,
                prompt_text="Enter number:",
                input_text="5",
                success=True,
                input_source=InputSource.USER_TYPED,
                response_time_ms=200
            )

        learner.track_input_event(
            session_id=session_id,
            prompt_text="Enter number:",
            input_text="5",
            success=False,
            input_source=InputSource.USER_TYPED,
            response_time_ms=180
        )

        # Get patterns
        result = learner.get_patterns_formatted()

        pattern = result["patterns"][0]
        mcr = pattern["most_common_response"]

        # Success rate should be 3/4 = 0.75
        assert mcr["count"] == 4
        assert mcr["success_rate"] == 0.75

    def test_all_responses_field(self):
        """Test that all_responses includes all response variants."""
        from shellsidekick.core.patterns import PatternLearner
        from shellsidekick.models.input_event import InputSource
        import uuid

        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        # Track multiple different responses to same prompt
        learner.track_input_event(
            session_id=session_id,
            prompt_text="Select option:",
            input_text="1",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=200
        )

        learner.track_input_event(
            session_id=session_id,
            prompt_text="Select option:",
            input_text="2",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=150
        )

        learner.track_input_event(
            session_id=session_id,
            prompt_text="Select option:",
            input_text="1",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=180
        )

        # Get patterns
        result = learner.get_patterns_formatted()

        pattern = result["patterns"][0]
        all_responses = pattern["all_responses"]

        # Should have 2 response variants
        assert len(all_responses) == 2

        # Find the responses
        resp_1 = next((r for r in all_responses if r["input_text"] == "1"), None)
        resp_2 = next((r for r in all_responses if r["input_text"] == "2"), None)

        assert resp_1 is not None
        assert resp_2 is not None
        assert resp_1["count"] == 2
        assert resp_2["count"] == 1
