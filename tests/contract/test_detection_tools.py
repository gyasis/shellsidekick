"""Contract tests for prompt detection MCP tools."""


import pytest


class TestDetectInputPrompt:
    """Test detect_input_prompt MCP tool."""

    @pytest.mark.asyncio
    async def test_detect_password_prompt(self):
        """Test detecting password prompts."""
        # This test will be implemented once MCP tools are available
        # Expected behavior:
        # - Detects password prompt with high confidence (>0.85)
        # - prompt_type is "password"
        # - is_dangerous is False for simple password prompts
        pytest.skip("Waiting for MCP tool implementation")

    @pytest.mark.asyncio
    async def test_detect_yes_no_prompt(self):
        """Test detecting yes/no confirmation prompts."""
        # This test will be implemented once MCP tools are available
        # Expected behavior:
        # - Detects yes/no prompt
        # - prompt_type is "yes_no"
        # - Returns matched pattern for debugging
        pytest.skip("Waiting for MCP tool implementation")

    @pytest.mark.asyncio
    async def test_detect_dangerous_prompt(self):
        """Test detecting dangerous operation prompts."""
        # This test will be implemented once MCP tools are available
        # Expected behavior:
        # - Detects prompt with dangerous keywords
        # - is_dangerous is True
        # - Flags delete/remove/destroy operations
        pytest.skip("Waiting for MCP tool implementation")

    @pytest.mark.asyncio
    async def test_no_prompt_detected(self):
        """Test when no prompt is detected."""
        # This test will be implemented once MCP tools are available
        # Expected behavior:
        # - detected is False
        # - prompt is None
        pytest.skip("Waiting for MCP tool implementation")

    @pytest.mark.asyncio
    async def test_confidence_threshold(self):
        """Test confidence threshold filtering."""
        # This test will be implemented once MCP tools are available
        # Expected behavior:
        # - Low confidence matches are filtered out
        # - min_confidence parameter works correctly
        pytest.skip("Waiting for MCP tool implementation")


class TestDetectionPerformance:
    """Performance tests for prompt detection."""

    def test_detection_latency_500ms(self, tmp_path):
        """Test that detection completes within 500ms (FR-004)."""
        import time

        from shellsidekick.core.detector import PromptDetector

        detector = PromptDetector()

        # Create test content with prompt at the end
        test_content = "Starting process...\n" * 100
        test_content += "Password: "

        # Measure detection time
        start_time = time.perf_counter()
        result = detector.detect(test_content)
        end_time = time.perf_counter()

        elapsed_ms = (end_time - start_time) * 1000

        # CRITICAL: Detection must complete in <500ms (FR-004)
        assert elapsed_ms < 500, f"Detection took {elapsed_ms:.2f}ms, exceeds 500ms limit"
        assert result is not None
        assert result.prompt_type.value == "password"

    def test_throughput_10k_lines_per_second(self, tmp_path):
        """Test processing 10,000 lines per second."""
        import time
        import uuid
        from datetime import datetime

        from shellsidekick.core.monitor import SessionMonitor
        from shellsidekick.models.session import Session, SessionState, SessionType

        # Create log file with 10,000 lines
        log_file = tmp_path / "large.log"
        num_lines = 10000
        with open(log_file, "w") as f:
            for i in range(num_lines):
                f.write(f"Log line {i}: Processing request...\n")

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)

        # Measure processing time
        start_time = time.perf_counter()
        content, _ = monitor.get_updates()
        end_time = time.perf_counter()

        elapsed_seconds = end_time - start_time
        lines_per_second = num_lines / elapsed_seconds

        # Should process >10,000 lines per second
        assert lines_per_second >= 10000, (
            f"Throughput {lines_per_second:.0f} lines/sec, " f"expected >=10,000 lines/sec"
        )
        assert len(content) > 0

    def test_large_file_performance(self, tmp_path):
        """Test detection performance with large log files."""
        import time
        import uuid
        from datetime import datetime

        from shellsidekick.core.detector import PromptDetector
        from shellsidekick.core.monitor import SessionMonitor
        from shellsidekick.models.session import Session, SessionState, SessionType

        # Create large log file with 10,000 lines + password prompt
        log_file = tmp_path / "large.log"
        with open(log_file, "w") as f:
            for i in range(10000):
                f.write(f"[{i}] Processing task...\n")
            f.write("Password: ")

        session = Session(
            session_id=str(uuid.uuid4()),
            session_type=SessionType.FILE,
            log_file=str(log_file),
            file_position=0,
            start_time=datetime.now(),
            state=SessionState.ACTIVE,
            metadata={},
        )

        monitor = SessionMonitor(session)
        detector = PromptDetector()

        # Read file content
        start_read = time.perf_counter()
        content, _ = monitor.get_updates()
        end_read = time.perf_counter()

        # Detect prompt (testing last few lines for efficiency)
        last_lines = "\n".join(content.split("\n")[-20:])
        start_detect = time.perf_counter()
        result = detector.detect(last_lines)
        end_detect = time.perf_counter()

        total_time_ms = (end_detect - start_read) * 1000
        detect_time_ms = (end_detect - start_detect) * 1000

        # Detection should complete in <500ms
        assert detect_time_ms < 500, (
            f"Detection took {detect_time_ms:.2f}ms, " f"exceeds 500ms limit"
        )

        # Total processing should be reasonable
        assert total_time_ms < 2000, (
            f"Total processing {total_time_ms:.2f}ms, " f"should be <2000ms"
        )

        # Verify detection worked
        assert result is not None
        assert result.prompt_type.value == "password"


class TestPromptTypeDetection:
    """Test detection of different prompt types."""

    @pytest.mark.asyncio
    async def test_detect_path_prompt(self):
        """Test detecting file path prompts."""
        pytest.skip("Waiting for MCP tool implementation")

    @pytest.mark.asyncio
    async def test_detect_choice_prompt(self):
        """Test detecting multiple choice prompts."""
        pytest.skip("Waiting for MCP tool implementation")

    @pytest.mark.asyncio
    async def test_detect_command_prompt(self):
        """Test detecting command input prompts."""
        pytest.skip("Waiting for MCP tool implementation")

    @pytest.mark.asyncio
    async def test_detect_text_prompt(self):
        """Test detecting generic text input prompts."""
        pytest.skip("Waiting for MCP tool implementation")


class TestInferExpectedInput:
    """Contract tests for infer_expected_input tool (User Story 2)."""

    def test_infer_yes_no_input(self):
        """Test suggesting yes/no inputs for confirmation prompt."""
        from shellsidekick.core.inference import InputInferenceEngine
        from shellsidekick.models.prompt import PromptType

        engine = InputInferenceEngine()
        suggestions, warnings = engine.infer_inputs(
            prompt_text="Continue? (yes/no)", prompt_type=PromptType.YES_NO
        )

        result = {"suggestions": [s.to_dict() for s in suggestions], "warnings": warnings}

        # Should suggest both yes and no
        suggestions = result["suggestions"]
        assert len(suggestions) == 2
        assert any(s["input_text"] == "yes" for s in suggestions)
        assert any(s["input_text"] == "no" for s in suggestions)

        # Each suggestion should have required fields
        for suggestion in suggestions:
            assert "input_text" in suggestion
            assert "confidence" in suggestion
            assert "source" in suggestion
            assert "reasoning" in suggestion
            assert suggestion["source"] in ["pattern_learning", "context_inference", "default"]

        # Should have no warnings for normal yes/no
        assert result["warnings"] == []

    def test_infer_path_input(self):
        """Test suggesting path inputs."""
        from shellsidekick.core.inference import InputInferenceEngine
        from shellsidekick.models.prompt import PromptType

        engine = InputInferenceEngine()
        suggestions, warnings = engine.infer_inputs(
            prompt_text="Enter file path:", prompt_type=PromptType.PATH
        )

        result = {"suggestions": [s.to_dict() for s in suggestions], "warnings": warnings}

        # Should suggest common path patterns
        suggestions = result["suggestions"]
        assert len(suggestions) > 0

        # Should include relative and absolute paths
        input_texts = [s["input_text"] for s in suggestions]
        assert any("./" in text for text in input_texts)
        assert any("/tmp/" in text or "/home/" in text for text in input_texts)

        # Each suggestion should have reasoning
        for suggestion in suggestions:
            assert len(suggestion["reasoning"]) > 0

    def test_infer_dangerous_warning(self):
        """Test warning generation for dangerous operations."""
        from shellsidekick.core.inference import InputInferenceEngine
        from shellsidekick.models.prompt import PromptType

        engine = InputInferenceEngine()
        suggestions, warnings = engine.infer_inputs(
            prompt_text="Delete all files? (yes/no)", prompt_type=PromptType.YES_NO
        )

        result = {"suggestions": [s.to_dict() for s in suggestions], "warnings": warnings}

        # Should detect dangerous keywords
        assert len(result["warnings"]) > 0
        assert any("dangerous" in w.lower() or "delete" in w.lower() for w in result["warnings"])

        # Should still provide suggestions
        suggestions = result["suggestions"]
        assert len(suggestions) == 2

        # "no" should be suggested with higher confidence or better reasoning
        no_suggestion = next((s for s in suggestions if s["input_text"] == "no"), None)
        assert no_suggestion is not None
        assert (
            "dangerous" in no_suggestion["reasoning"].lower()
            or "safe" in no_suggestion["reasoning"].lower()
        )

    def test_infer_password_prompt(self):
        """Test that password prompts don't suggest actual passwords."""
        from shellsidekick.core.inference import InputInferenceEngine
        from shellsidekick.models.prompt import PromptType

        engine = InputInferenceEngine()
        suggestions, warnings = engine.infer_inputs(
            prompt_text="Password:", prompt_type=PromptType.PASSWORD
        )

        result = {"suggestions": [s.to_dict() for s in suggestions], "warnings": warnings}

        # Should not suggest passwords
        suggestions = result["suggestions"]
        assert len(suggestions) == 0 or all(
            s["input_text"] in ["[manual entry required]", "[user input required]"]
            for s in suggestions
        )

        # Should have security warning
        assert len(result["warnings"]) > 0
        assert any("manual" in w.lower() or "security" in w.lower() for w in result["warnings"])

    def test_infer_with_context(self):
        """Test context-aware suggestions."""
        from shellsidekick.core.inference import InputInferenceEngine
        from shellsidekick.models.prompt import PromptType

        # Context indicating we're in a deployment scenario
        session_context = {
            "working_directory": "/var/www/app",
            "recent_commands": ["git pull", "npm install"],
        }

        engine = InputInferenceEngine()
        suggestions, warnings = engine.infer_inputs(
            prompt_text="Restart service? (yes/no)",
            prompt_type=PromptType.YES_NO,
            session_context=session_context,
        )

        result = {"suggestions": [s.to_dict() for s in suggestions], "warnings": warnings}

        suggestions = result["suggestions"]
        assert len(suggestions) == 2

        # Context might influence reasoning
        yes_suggestion = next((s for s in suggestions if s["input_text"] == "yes"), None)
        assert yes_suggestion is not None
        # Reasoning should be contextual
        assert len(yes_suggestion["reasoning"]) > 10

    def test_infer_command_prompt(self):
        """Test suggestions for command input prompts."""
        from shellsidekick.core.inference import InputInferenceEngine
        from shellsidekick.models.prompt import PromptType

        engine = InputInferenceEngine()
        suggestions, warnings = engine.infer_inputs(
            prompt_text="Enter command:", prompt_type=PromptType.COMMAND
        )

        result = {"suggestions": [s.to_dict() for s in suggestions], "warnings": warnings}

        suggestions = result["suggestions"]
        assert len(suggestions) > 0

        # Should suggest common safe commands
        input_texts = [s["input_text"] for s in suggestions]
        common_commands = ["help", "exit", "status", "ls"]
        assert any(cmd in text for text in input_texts for cmd in common_commands)

    def test_infer_choice_prompt(self):
        """Test suggestions for numbered choice prompts."""
        from shellsidekick.core.inference import InputInferenceEngine
        from shellsidekick.models.prompt import PromptType

        engine = InputInferenceEngine()
        suggestions, warnings = engine.infer_inputs(
            prompt_text="[1] Option A\n[2] Option B\n[3] Exit", prompt_type=PromptType.CHOICE
        )

        result = {"suggestions": [s.to_dict() for s in suggestions], "warnings": warnings}

        suggestions = result["suggestions"]
        assert len(suggestions) >= 3

        # Should suggest the choice numbers
        input_texts = [s["input_text"] for s in suggestions]
        assert "1" in input_texts
        assert "2" in input_texts
        assert "3" in input_texts


class TestPatternBasedSuggestions:
    """Contract tests for pattern learning integration (T053)."""

    def test_pattern_suggestions_prioritized(self):
        """Test that learned patterns are prioritized over defaults."""
        import uuid

        from shellsidekick.core.inference import InputInferenceEngine
        from shellsidekick.core.patterns import PatternLearner
        from shellsidekick.models.input_event import InputSource
        from shellsidekick.models.prompt import PromptType

        # Build pattern history: user always says "no" to restart prompts
        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        for _ in range(5):
            learner.track_input_event(
                session_id=session_id,
                prompt_text="Restart service? (yes/no)",
                input_text="no",
                success=True,
                input_source=InputSource.USER_TYPED,
                response_time_ms=200,
            )

        # Track one "yes" for comparison
        learner.track_input_event(
            session_id=session_id,
            prompt_text="Restart service? (yes/no)",
            input_text="yes",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=150,
        )

        # Get suggestions with pattern learning
        engine = InputInferenceEngine(pattern_learner=learner)
        suggestions, warnings = engine.infer_inputs(
            prompt_text="Restart service? (yes/no)", prompt_type=PromptType.YES_NO
        )

        # Should still suggest both yes and no
        input_texts = [s.input_text for s in suggestions]
        assert "yes" in input_texts
        assert "no" in input_texts

        # "no" should have higher confidence (learned from patterns)
        no_suggestion = next(s for s in suggestions if s.input_text == "no")
        yes_suggestion = next(s for s in suggestions if s.input_text == "yes")

        assert no_suggestion.confidence > yes_suggestion.confidence
        assert no_suggestion.source == "pattern_learning"

    def test_pattern_with_high_success_rate(self):
        """Test that high success rate patterns get higher confidence."""
        import uuid

        from shellsidekick.core.inference import InputInferenceEngine
        from shellsidekick.core.patterns import PatternLearner
        from shellsidekick.models.input_event import InputSource
        from shellsidekick.models.prompt import PromptType

        learner = PatternLearner(auto_load=False)
        session_id = str(uuid.uuid4())

        # Track "yes" with 100% success rate
        for _ in range(10):
            learner.track_input_event(
                session_id=session_id,
                prompt_text="Deploy to production? (yes/no)",
                input_text="yes",
                success=True,
                input_source=InputSource.USER_TYPED,
                response_time_ms=200,
            )

        # Get suggestions
        engine = InputInferenceEngine(pattern_learner=learner)
        suggestions, warnings = engine.infer_inputs(
            prompt_text="Deploy to production? (yes/no)", prompt_type=PromptType.YES_NO
        )

        # "yes" should have very high confidence
        yes_suggestion = next(s for s in suggestions if s.input_text == "yes")
        assert yes_suggestion.confidence >= 0.90
        assert yes_suggestion.source == "pattern_learning"
        assert "learned" in yes_suggestion.reasoning.lower()

    def test_no_pattern_falls_back_to_defaults(self):
        """Test that suggestions work even without learned patterns."""
        from shellsidekick.core.inference import InputInferenceEngine
        from shellsidekick.core.patterns import PatternLearner
        from shellsidekick.models.prompt import PromptType

        # Empty pattern learner
        learner = PatternLearner(auto_load=False)

        engine = InputInferenceEngine(pattern_learner=learner)
        suggestions, warnings = engine.infer_inputs(
            prompt_text="Continue? (yes/no)", prompt_type=PromptType.YES_NO
        )

        # Should fall back to default suggestions
        assert len(suggestions) == 2
        for suggestion in suggestions:
            assert suggestion.source == "default"


class TestTrackInputEvent:
    """Contract tests for track_input_event tool (User Story 3)."""

    def test_track_successful_input(self, tmp_path):
        """Test recording successful user input event."""
        import uuid

        from shellsidekick.core.patterns import PatternLearner
        from shellsidekick.models.input_event import InputSource

        # Create a temporary session ID
        session_id = str(uuid.uuid4())

        # Track input event
        learner = PatternLearner(auto_load=False)
        event = learner.track_input_event(
            session_id=session_id,
            prompt_text="Continue? (yes/no)",
            input_text="yes",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=250,
        )

        # Verify event recorded
        assert event["event_id"] is not None
        assert event["recorded"] is True
        assert event["pattern_updated"] is True

    def test_track_password_redaction(self, tmp_path):
        """Test that password inputs are redacted (FR-006)."""
        import uuid

        from shellsidekick.core.patterns import PatternLearner
        from shellsidekick.models.input_event import InputSource

        session_id = str(uuid.uuid4())
        learner = PatternLearner(auto_load=False)

        # Track password input
        event = learner.track_input_event(
            session_id=session_id,
            prompt_text="Password:",
            input_text="secret123",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=150,
        )

        # Event should be recorded
        assert event["recorded"] is True

        # Verify stored event has redacted password
        events = learner.get_session_events(session_id)
        assert len(events) == 1
        assert events[0].input_text == "[REDACTED]"
        assert events[0].prompt_text == "Password:"

    def test_track_failed_input(self, tmp_path):
        """Test tracking failed input attempts."""
        import uuid

        from shellsidekick.core.patterns import PatternLearner
        from shellsidekick.models.input_event import InputSource

        session_id = str(uuid.uuid4())
        learner = PatternLearner(auto_load=False)

        # Track failed input
        event = learner.track_input_event(
            session_id=session_id,
            prompt_text="Enter number (1-10):",
            input_text="99",
            success=False,
            input_source=InputSource.USER_TYPED,
            response_time_ms=100,
        )

        # Event should be recorded
        assert event["recorded"] is True

        # Failed inputs should update patterns (for success rate calculation)
        # Pattern learning tracks both successful and failed attempts
        assert event["pattern_updated"] is True

    def test_track_multiple_inputs_same_prompt(self, tmp_path):
        """Test pattern building from multiple inputs to same prompt."""
        import uuid

        from shellsidekick.core.patterns import PatternLearner
        from shellsidekick.models.input_event import InputSource

        session_id = str(uuid.uuid4())
        learner = PatternLearner(auto_load=False)

        # Track multiple "yes" responses
        for i in range(3):
            learner.track_input_event(
                session_id=session_id,
                prompt_text="Continue? (yes/no)",
                input_text="yes",
                success=True,
                input_source=InputSource.USER_TYPED,
                response_time_ms=200,
            )

        # Track one "no" response
        learner.track_input_event(
            session_id=session_id,
            prompt_text="Continue? (yes/no)",
            input_text="no",
            success=True,
            input_source=InputSource.USER_TYPED,
            response_time_ms=150,
        )

        # Get learned patterns
        patterns = learner.get_patterns()

        # Should have learned "yes" is more common (3/4 = 75%)
        prompt_pattern = next((p for p in patterns if "Continue?" in p.prompt_text), None)
        assert prompt_pattern is not None
        assert "yes" in prompt_pattern.responses
        assert "no" in prompt_pattern.responses
        assert prompt_pattern.responses["yes"].count == 3
        assert prompt_pattern.responses["no"].count == 1
