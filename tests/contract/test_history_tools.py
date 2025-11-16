"""Contract tests for history and pattern retrieval MCP tools."""

import os
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


class TestSearchSessionHistory:
    """Contract tests for search_session_history MCP tool (User Story 4, T065-T068)."""

    def test_search_single_session(self, tmp_path):
        """T065: Test searching a single session for patterns."""
        from shellsidekick.core.storage import search_log_file

        # Create test log file
        log_file = tmp_path / "test-session.log"
        log_file.write_text(
            "Starting application\n"
            "ERROR: Connection refused\n"
            "Retrying connection...\n"
            "ERROR: Timeout after 30s\n"
            "Application terminated\n"
        )

        # Search for ERROR pattern
        results = search_log_file(
            log_file=str(log_file),
            query="ERROR",
            context_lines=0,
            max_results=10
        )

        assert len(results) == 2
        assert results[0]["matched_text"] == "ERROR: Connection refused"
        assert results[1]["matched_text"] == "ERROR: Timeout after 30s"
        assert results[0]["line_number"] == 2
        assert results[1]["line_number"] == 4

    def test_search_with_context_lines(self, tmp_path):
        """T067: Test context lines before and after matches."""
        from shellsidekick.core.storage import search_log_file

        # Create test log file
        log_file = tmp_path / "test-session.log"
        log_file.write_text(
            "Line 1\n"
            "Line 2\n"
            "ERROR: Something went wrong\n"
            "Line 4\n"
            "Line 5\n"
        )

        # Search with 2 lines of context
        results = search_log_file(
            log_file=str(log_file),
            query="ERROR",
            context_lines=2,
            max_results=10
        )

        assert len(results) == 1
        match = results[0]

        # Verify context before
        assert len(match["context_before"]) == 2
        assert match["context_before"] == ["Line 1", "Line 2"]

        # Verify context after
        assert len(match["context_after"]) == 2
        assert match["context_after"] == ["Line 4", "Line 5"]

        # Verify matched line
        assert match["matched_text"] == "ERROR: Something went wrong"
        assert match["line_number"] == 3

    def test_search_with_regex_pattern(self, tmp_path):
        """T066: Test regex search functionality."""
        from shellsidekick.core.storage import search_log_file

        # Create test log file
        log_file = tmp_path / "test-session.log"
        log_file.write_text(
            "ERROR: 404 Not Found\n"
            "ERROR: 500 Internal Server Error\n"
            "INFO: 200 OK\n"
            "ERROR: 502 Bad Gateway\n"
        )

        # Search for 4xx and 5xx errors using regex
        results = search_log_file(
            log_file=str(log_file),
            query=r"ERROR: [45]\d{2}",
            context_lines=0,
            max_results=10
        )

        assert len(results) == 3
        assert "404" in results[0]["matched_text"]
        assert "500" in results[1]["matched_text"]
        assert "502" in results[2]["matched_text"]

    def test_search_max_results_limiting(self, tmp_path):
        """T068: Test max results parameter."""
        from shellsidekick.core.storage import search_log_file

        # Create log file with many matches
        log_file = tmp_path / "test-session.log"
        lines = [f"ERROR {i}\n" for i in range(50)]
        log_file.write_text("".join(lines))

        # Search with max_results limit
        results = search_log_file(
            log_file=str(log_file),
            query="ERROR",
            context_lines=0,
            max_results=10
        )

        # Should return only 10 results
        assert len(results) == 10

        # But we should know total matches (this would be in metadata)
        # For now just verify we got exactly max_results
        assert results[0]["matched_text"] == "ERROR 0"
        assert results[9]["matched_text"] == "ERROR 9"

    def test_search_no_matches(self, tmp_path):
        """Test search with no matching results."""
        from shellsidekick.core.storage import search_log_file

        # Create test log file
        log_file = tmp_path / "test-session.log"
        log_file.write_text(
            "Normal log entry\n"
            "Another normal entry\n"
        )

        # Search for pattern that doesn't exist
        results = search_log_file(
            log_file=str(log_file),
            query="NONEXISTENT_PATTERN",
            context_lines=0,
            max_results=10
        )

        assert len(results) == 0

    def test_search_invalid_regex_raises_error(self, tmp_path):
        """Test that invalid regex patterns raise appropriate error."""
        from shellsidekick.core.storage import search_log_file
        import re

        log_file = tmp_path / "test-session.log"
        log_file.write_text("Some content\n")

        # Invalid regex pattern (unclosed bracket)
        with pytest.raises(re.error):
            search_log_file(
                log_file=str(log_file),
                query="[unclosed",
                context_lines=0,
                max_results=10
            )


class TestCleanupOldSessions:
    """Contract tests for cleanup_old_sessions MCP tool (User Story 4, T069-T070)."""

    def test_cleanup_dry_run_mode(self, tmp_path):
        """T070: Test cleanup dry run mode."""
        from shellsidekick.core.storage import cleanup_old_sessions
        import time

        # Create old session file (8 days ago)
        old_session = tmp_path / "old-session.log"
        old_session.write_text("Old session content")

        # Set file mtime to 8 days ago
        eight_days_ago = time.time() - (8 * 24 * 60 * 60)
        os.utime(old_session, (eight_days_ago, eight_days_ago))

        # Run cleanup in dry run mode
        result = cleanup_old_sessions(
            sessions_dir=str(tmp_path),
            retention_days=7,
            dry_run=True
        )

        # File should still exist (dry run)
        assert old_session.exists()

        # But should be listed in deleted_sessions
        assert len(result["deleted_sessions"]) >= 1
        assert result["dry_run"] is True
        assert result["bytes_freed"] > 0

    def test_cleanup_actual_deletion(self, tmp_path):
        """T069: Test actual session cleanup."""
        from shellsidekick.core.storage import cleanup_old_sessions
        import time

        # Create old session file (8 days ago)
        old_session = tmp_path / "old-session.log"
        old_session.write_text("Old session content that will be deleted")

        # Create recent session file (2 days ago)
        recent_session = tmp_path / "recent-session.log"
        recent_session.write_text("Recent session content")

        # Set file mtimes
        eight_days_ago = time.time() - (8 * 24 * 60 * 60)
        two_days_ago = time.time() - (2 * 24 * 60 * 60)
        os.utime(old_session, (eight_days_ago, eight_days_ago))
        os.utime(recent_session, (two_days_ago, two_days_ago))

        # Run actual cleanup
        result = cleanup_old_sessions(
            sessions_dir=str(tmp_path),
            retention_days=7,
            dry_run=False
        )

        # Old file should be deleted
        assert not old_session.exists()

        # Recent file should still exist
        assert recent_session.exists()

        # Verify result
        assert result["total_deleted"] >= 1
        assert result["dry_run"] is False
        assert result["bytes_freed"] > 0
        assert "old-session.log" in result["deleted_sessions"]

    def test_cleanup_retention_boundary(self, tmp_path):
        """Test that files exactly at retention days are NOT deleted."""
        from shellsidekick.core.storage import cleanup_old_sessions
        import time

        # Create session file 7 days minus 10 seconds old
        # (slightly newer than the boundary to avoid timing edge cases)
        seven_day_session = tmp_path / "seven-day-session.log"
        seven_day_session.write_text("Content")

        # Set to 7 days minus 10 seconds ago (just inside retention window)
        seven_days_minus = time.time() - (7 * 24 * 60 * 60) + 10
        os.utime(seven_day_session, (seven_days_minus, seven_days_minus))

        # Run cleanup with 7-day retention
        result = cleanup_old_sessions(
            sessions_dir=str(tmp_path),
            retention_days=7,
            dry_run=False
        )

        # File should NOT be deleted (it's within the 7-day retention window)
        assert seven_day_session.exists()
        assert "seven-day-session.log" not in result["deleted_sessions"]
