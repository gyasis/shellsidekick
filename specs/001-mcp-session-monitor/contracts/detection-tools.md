# MCP Tool Contract: Prompt Detection

**Category**: Prompt Detection & Analysis
**Generated**: 2025-11-14
**Status**: Design Complete

## Tool: detect_input_prompt

**Purpose**: Analyze session output to detect if terminal is waiting for input.

**MCP Tool Name**: `detect_input_prompt`

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "session_id": {
      "type": "string",
      "description": "Session ID to analyze"
    },
    "min_confidence": {
      "type": "number",
      "description": "Minimum confidence threshold (0.0-1.0)",
      "minimum": 0.0,
      "maximum": 1.0,
      "default": 0.70
    }
  },
  "required": ["session_id"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "detected": {
      "type": "boolean",
      "description": "Whether a prompt was detected"
    },
    "prompt": {
      "type": "object",
      "nullable": true,
      "properties": {
        "prompt_text": {"type": "string"},
        "confidence": {"type": "number"},
        "prompt_type": {
          "type": "string",
          "enum": ["password", "yes_no", "choice", "path", "text", "command", "unknown"]
        },
        "matched_pattern": {"type": "string"},
        "file_position": {"type": "integer"},
        "timestamp": {"type": "string", "format": "date-time"},
        "is_dangerous": {"type": "boolean"}
      }
    }
  },
  "required": ["detected"]
}
```

### Error Cases

| Error Code | Condition | HTTP Status | Response |
|------------|-----------|-------------|----------|
| `SESSION_NOT_FOUND` | Session ID not active | 404 | `{"error": "Session {id} not found", "code": "SESSION_NOT_FOUND"}` |
| `INVALID_CONFIDENCE` | Confidence not in [0.0, 1.0] | 400 | `{"error": "Confidence must be 0.0-1.0", "code": "INVALID_CONFIDENCE"}` |

### Performance Requirements

- Detection latency: <500ms (FR-004)
- Can process 10,000 lines/sec (Technical Context)

### Test Cases

```python
# Test 1: Detect password prompt
async def test_detect_password_prompt():
    # Setup session with password prompt content
    await append_to_log("Password: ")

    result = await client.call_tool("detect_input_prompt", {
        "session_id": "abc123-def456-..."
    })

    assert result.data["detected"] == True
    assert result.data["prompt"]["prompt_type"] == "password"
    assert result.data["prompt"]["confidence"] >= 0.70
    assert result.data["prompt"]["is_dangerous"] == False

# Test 2: Detect yes/no prompt
async def test_detect_yes_no_prompt():
    await append_to_log("Continue? (yes/no): ")

    result = await client.call_tool("detect_input_prompt", {
        "session_id": "abc123-def456-..."
    })

    assert result.data["detected"] == True
    assert result.data["prompt"]["prompt_type"] == "yes_no"
    assert "yes/no" in result.data["prompt"]["prompt_text"]

# Test 3: Detect dangerous operation
async def test_detect_dangerous_prompt():
    await append_to_log("Delete 3 tables? (yes/no): ")

    result = await client.call_tool("detect_input_prompt", {
        "session_id": "abc123-def456-..."
    })

    assert result.data["detected"] == True
    assert result.data["prompt"]["is_dangerous"] == True

# Test 4: No prompt detected
async def test_no_prompt_detected():
    await append_to_log("Normal log output without prompt")

    result = await client.call_tool("detect_input_prompt", {
        "session_id": "abc123-def456-..."
    })

    assert result.data["detected"] == False
    assert result.data["prompt"] is None

# Test 5: Confidence threshold filtering
async def test_confidence_threshold():
    await append_to_log("Maybe a prompt?")  # Low confidence match

    result = await client.call_tool("detect_input_prompt", {
        "session_id": "abc123-def456-...",
        "min_confidence": 0.85  # High threshold
    })

    assert result.data["detected"] == False

# Test 6: Performance test (10k lines)
async def test_detection_performance():
    # Generate 10k lines of log output
    large_content = "\n".join([f"Log line {i}" for i in range(10000)])
    large_content += "\nPassword: "

    await append_to_log(large_content)

    start = time.perf_counter()
    result = await client.call_tool("detect_input_prompt", {
        "session_id": "abc123-def456-..."
    })
    elapsed = time.perf_counter() - start

    assert result.data["detected"] == True
    assert elapsed < 0.5  # Must complete in <500ms
```

---

## Tool: infer_expected_input

**Purpose**: Suggest appropriate inputs based on prompt context and learned patterns.

**MCP Tool Name**: `infer_expected_input`

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "prompt_text": {
      "type": "string",
      "description": "The detected prompt text"
    },
    "prompt_type": {
      "type": "string",
      "enum": ["password", "yes_no", "choice", "path", "text", "command", "unknown"],
      "description": "Type of prompt detected"
    },
    "session_context": {
      "type": "object",
      "description": "Optional session context (metadata, history)",
      "additionalProperties": true
    }
  },
  "required": ["prompt_text", "prompt_type"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "suggestions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "input_text": {"type": "string"},
          "confidence": {"type": "number"},
          "source": {
            "type": "string",
            "enum": ["pattern_learning", "context_inference", "default"]
          },
          "reasoning": {"type": "string"}
        }
      }
    },
    "warnings": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Warnings about dangerous operations"
    }
  },
  "required": ["suggestions", "warnings"]
}
```

### Test Cases

```python
# Test 1: Suggest yes/no for confirmation
async def test_infer_yes_no_input():
    result = await client.call_tool("infer_expected_input", {
        "prompt_text": "Continue? (yes/no)",
        "prompt_type": "yes_no"
    })

    suggestions = result.data["suggestions"]
    assert len(suggestions) == 2
    assert any(s["input_text"] == "yes" for s in suggestions)
    assert any(s["input_text"] == "no" for s in suggestions)

# Test 2: Suggest path patterns
async def test_infer_path_input():
    result = await client.call_tool("infer_expected_input", {
        "prompt_text": "Enter file path:",
        "prompt_type": "path"
    })

    suggestions = result.data["suggestions"]
    assert len(suggestions) > 0
    assert any("./" in s["input_text"] for s in suggestions)
    assert any("/tmp/" in s["input_text"] for s in suggestions)

# Test 3: Warn about dangerous operations
async def test_infer_dangerous_warning():
    result = await client.call_tool("infer_expected_input", {
        "prompt_text": "Delete all files? (yes/no)",
        "prompt_type": "yes_no"
    })

    assert len(result.data["warnings"]) > 0
    assert any("dangerous" in w.lower() for w in result.data["warnings"])

# Test 4: Use learned patterns
async def test_infer_from_learned_pattern():
    # Simulate pattern where user always says "no" to restart
    # (Pattern would be pre-loaded in storage)

    result = await client.call_tool("infer_expected_input", {
        "prompt_text": "Restart services immediately?",
        "prompt_type": "yes_no"
    })

    # Should prioritize "no" based on pattern
    suggestions = result.data["suggestions"]
    assert suggestions[0]["input_text"] == "no"
    assert suggestions[0]["source"] == "pattern_learning"
    assert "10/10 times" in suggestions[0]["reasoning"]
```

---

## Tool: track_input_event

**Purpose**: Record user input event for pattern learning and history.

**MCP Tool Name**: `track_input_event`

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "session_id": {"type": "string"},
    "prompt_text": {"type": "string"},
    "input_text": {"type": "string"},
    "success": {"type": "boolean"},
    "input_source": {
      "type": "string",
      "enum": ["user_typed", "ai_suggested", "auto_injected"]
    },
    "response_time_ms": {"type": "integer"}
  },
  "required": ["session_id", "prompt_text", "input_text", "success", "input_source", "response_time_ms"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "event_id": {"type": "string"},
    "recorded": {"type": "boolean"},
    "pattern_updated": {"type": "boolean"}
  },
  "required": ["event_id", "recorded", "pattern_updated"]
}
```

### Security Requirements

- Password prompts: `input_text` MUST be redacted as `"[REDACTED]"`
- Never log plaintext passwords

### Test Cases

```python
# Test 1: Track successful input
async def test_track_input_success():
    result = await client.call_tool("track_input_event", {
        "session_id": "abc123-def456-...",
        "prompt_text": "Continue? (yes/no)",
        "input_text": "yes",
        "success": True,
        "input_source": "user_typed",
        "response_time_ms": 250
    })

    assert result.data["recorded"] == True
    assert result.data["pattern_updated"] == True

# Test 2: Password redaction
async def test_track_password_redaction():
    result = await client.call_tool("track_input_event", {
        "session_id": "abc123-def456-...",
        "prompt_text": "Password:",
        "input_text": "secret123",
        "success": True,
        "input_source": "user_typed",
        "response_time_ms": 150
    })

    # Verify stored event has redacted password
    history = load_session_history("abc123-def456-...")
    assert history["events"][-1]["input_text"] == "[REDACTED]"

# Test 3: Failed input tracking
async def test_track_failed_input():
    result = await client.call_tool("track_input_event", {
        "session_id": "abc123-def456-...",
        "prompt_text": "Enter number (1-10):",
        "input_text": "99",
        "success": False,
        "input_source": "user_typed",
        "response_time_ms": 100
    })

    assert result.data["recorded"] == True
    # Failed inputs should not update patterns (or decrement confidence)
```

---

**Contract Status**: ✅ Complete - Ready for test-first implementation
