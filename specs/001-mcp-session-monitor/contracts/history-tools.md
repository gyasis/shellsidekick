# MCP Tool Contract: History & Search

**Category**: Session History & Pattern Analysis
**Generated**: 2025-11-14
**Status**: Design Complete

## Tool: search_session_history

**Purpose**: Search session history for specific patterns or keywords.

**MCP Tool Name**: `search_session_history`

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "session_id": {
      "type": "string",
      "description": "Session ID to search (or null for all sessions)",
      "nullable": true
    },
    "query": {
      "type": "string",
      "description": "Search query (supports regex)"
    },
    "context_lines": {
      "type": "integer",
      "description": "Lines of context before/after match",
      "default": 3,
      "minimum": 0,
      "maximum": 10
    },
    "max_results": {
      "type": "integer",
      "description": "Maximum number of results to return",
      "default": 10,
      "minimum": 1,
      "maximum": 100
    }
  },
  "required": ["query"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "matches": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "session_id": {"type": "string"},
          "line_number": {"type": "integer"},
          "matched_text": {"type": "string"},
          "context_before": {
            "type": "array",
            "items": {"type": "string"}
          },
          "context_after": {
            "type": "array",
            "items": {"type": "string"}
          },
          "timestamp": {"type": "string", "format": "date-time"}
        }
      }
    },
    "total_matches": {"type": "integer"},
    "searched_sessions": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["matches", "total_matches", "searched_sessions"]
}
```

### Error Cases

| Error Code | Condition | HTTP Status | Response |
|------------|-----------|-------------|----------|
| `SESSION_NOT_FOUND` | Session ID not found | 404 | `{"error": "Session {id} not found", "code": "SESSION_NOT_FOUND"}` |
| `INVALID_REGEX` | Query is invalid regex | 400 | `{"error": "Invalid regex pattern", "code": "INVALID_REGEX"}` |

### Performance Requirements

- Search 30 days of logs in <1 second (SC-006)

### Test Cases

```python
# Test 1: Search single session
async def test_search_session_history():
    # Setup session with known content
    await append_to_log("ERROR: Connection refused\n")
    await append_to_log("ERROR: Timeout\n")

    result = await client.call_tool("search_session_history", {
        "session_id": "abc123-def456-...",
        "query": "ERROR",
        "context_lines": 0
    })

    assert result.data["total_matches"] == 2
    assert len(result.data["matches"]) == 2

# Test 2: Search all sessions
async def test_search_all_sessions():
    result = await client.call_tool("search_session_history", {
        "session_id": None,  # Search all
        "query": "connection refused"
    })

    assert len(result.data["searched_sessions"]) > 0

# Test 3: Context lines
async def test_search_with_context():
    await append_to_log("Line 1\nLine 2\nERROR\nLine 4\nLine 5\n")

    result = await client.call_tool("search_session_history", {
        "session_id": "abc123-def456-...",
        "query": "ERROR",
        "context_lines": 2
    })

    match = result.data["matches"][0]
    assert len(match["context_before"]) == 2
    assert len(match["context_after"]) == 2
    assert "Line 2" in match["context_before"]
    assert "Line 4" in match["context_after"]

# Test 4: Regex search
async def test_search_regex_pattern():
    await append_to_log("ERROR: 404\nERROR: 500\nINFO: 200\n")

    result = await client.call_tool("search_session_history", {
        "session_id": "abc123-def456-...",
        "query": r"ERROR: [45]\d{2}"  # Match 4xx or 5xx errors
    })

    assert result.data["total_matches"] == 2

# Test 5: Max results limit
async def test_search_max_results():
    # Generate 50 matching lines
    for i in range(50):
        await append_to_log(f"ERROR {i}\n")

    result = await client.call_tool("search_session_history", {
        "session_id": "abc123-def456-...",
        "query": "ERROR",
        "max_results": 10
    })

    assert len(result.data["matches"]) == 10
    assert result.data["total_matches"] == 50  # But total is tracked

# Test 6: No matches
async def test_search_no_matches():
    result = await client.call_tool("search_session_history", {
        "session_id": "abc123-def456-...",
        "query": "NONEXISTENT_PATTERN"
    })

    assert result.data["total_matches"] == 0
    assert len(result.data["matches"]) == 0
```

---

## Tool: get_learned_patterns

**Purpose**: Retrieve learned prompt-response patterns.

**MCP Tool Name**: `get_learned_patterns`

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "prompt_filter": {
      "type": "string",
      "description": "Optional filter for prompt text (substring match)",
      "nullable": true
    },
    "min_occurrences": {
      "type": "integer",
      "description": "Minimum number of occurrences",
      "default": 1,
      "minimum": 1
    },
    "sort_by": {
      "type": "string",
      "enum": ["occurrences", "last_seen", "success_rate"],
      "default": "occurrences"
    }
  }
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "patterns": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "prompt_text": {"type": "string"},
          "total_occurrences": {"type": "integer"},
          "most_common_response": {
            "type": "object",
            "properties": {
              "input_text": {"type": "string"},
              "count": {"type": "integer"},
              "success_rate": {"type": "number"}
            }
          },
          "all_responses": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "input_text": {"type": "string"},
                "count": {"type": "integer"},
                "success_count": {"type": "integer"},
                "success_rate": {"type": "number"}
              }
            }
          },
          "last_seen": {"type": "string", "format": "date-time"}
        }
      }
    },
    "total_patterns": {"type": "integer"}
  },
  "required": ["patterns", "total_patterns"]
}
```

### Test Cases

```python
# Test 1: Get all patterns
async def test_get_all_patterns():
    result = await client.call_tool("get_learned_patterns", {})

    assert "patterns" in result.data
    assert result.data["total_patterns"] >= 0

# Test 2: Filter by prompt text
async def test_get_patterns_filtered():
    result = await client.call_tool("get_learned_patterns", {
        "prompt_filter": "Restart"
    })

    patterns = result.data["patterns"]
    assert all("Restart" in p["prompt_text"] for p in patterns)

# Test 3: Sort by occurrences
async def test_get_patterns_sorted():
    result = await client.call_tool("get_learned_patterns", {
        "sort_by": "occurrences"
    })

    patterns = result.data["patterns"]
    # Verify descending order
    for i in range(len(patterns) - 1):
        assert patterns[i]["total_occurrences"] >= patterns[i+1]["total_occurrences"]

# Test 4: Minimum occurrences filter
async def test_get_patterns_min_occurrences():
    result = await client.call_tool("get_learned_patterns", {
        "min_occurrences": 5
    })

    patterns = result.data["patterns"]
    assert all(p["total_occurrences"] >= 5 for p in patterns)

# Test 5: Verify pattern structure
async def test_pattern_structure():
    # Create a known pattern
    for _ in range(10):
        await client.call_tool("track_input_event", {
            "session_id": "abc123-def456-...",
            "prompt_text": "Continue? (yes/no)",
            "input_text": "no",
            "success": True,
            "input_source": "user_typed",
            "response_time_ms": 100
        })

    result = await client.call_tool("get_learned_patterns", {
        "prompt_filter": "Continue"
    })

    pattern = result.data["patterns"][0]
    assert pattern["total_occurrences"] == 10
    assert pattern["most_common_response"]["input_text"] == "no"
    assert pattern["most_common_response"]["success_rate"] == 1.0
```

---

## Tool: cleanup_old_sessions

**Purpose**: Clean up expired session data based on retention policy.

**MCP Tool Name**: `cleanup_old_sessions`

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "retention_days": {
      "type": "integer",
      "description": "Delete sessions older than N days",
      "default": 7,
      "minimum": 1,
      "maximum": 365
    },
    "dry_run": {
      "type": "boolean",
      "description": "Show what would be deleted without actually deleting",
      "default": false
    }
  }
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "deleted_sessions": {
      "type": "array",
      "items": {"type": "string"}
    },
    "total_deleted": {"type": "integer"},
    "bytes_freed": {"type": "integer"},
    "dry_run": {"type": "boolean"}
  },
  "required": ["deleted_sessions", "total_deleted", "bytes_freed", "dry_run"]
}
```

### Test Cases

```python
# Test 1: Dry run cleanup
async def test_cleanup_dry_run():
    result = await client.call_tool("cleanup_old_sessions", {
        "retention_days": 7,
        "dry_run": True
    })

    assert result.data["dry_run"] == True
    # Verify files still exist
    for session_id in result.data["deleted_sessions"]:
        assert os.path.exists(f"/tmp/ssk-sessions/{session_id}.log")

# Test 2: Actual cleanup
async def test_cleanup_execute():
    # Create old session (mock old timestamp)
    old_session_path = "/tmp/ssk-sessions/old-session.log"
    with open(old_session_path, "w") as f:
        f.write("Old content")

    # Set file mtime to 8 days ago
    eight_days_ago = time.time() - (8 * 24 * 60 * 60)
    os.utime(old_session_path, (eight_days_ago, eight_days_ago))

    result = await client.call_tool("cleanup_old_sessions", {
        "retention_days": 7,
        "dry_run": False
    })

    assert result.data["total_deleted"] >= 1
    assert not os.path.exists(old_session_path)

# Test 3: Retention days boundary
async def test_cleanup_retention_boundary():
    # Create session exactly 7 days old
    seven_days_ago = time.time() - (7 * 24 * 60 * 60)

    result = await client.call_tool("cleanup_old_sessions", {
        "retention_days": 7,
        "dry_run": True
    })

    # 7-day-old sessions should NOT be deleted (retention is "older than N")
    assert "7-day-old-session" not in result.data["deleted_sessions"]

# Test 4: Bytes freed calculation
async def test_cleanup_bytes_freed():
    result = await client.call_tool("cleanup_old_sessions", {
        "retention_days": 7,
        "dry_run": False
    })

    assert result.data["bytes_freed"] >= 0
```

---

**Contract Status**: ✅ Complete - Ready for test-first implementation
