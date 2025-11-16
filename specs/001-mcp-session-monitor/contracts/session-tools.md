# MCP Tool Contract: Session Management

**Category**: Session Lifecycle
**Generated**: 2025-11-14
**Status**: Design Complete

## Tool: start_session_monitor

**Purpose**: Start monitoring a terminal session.

**MCP Tool Name**: `start_session_monitor`

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "session_id": {
      "type": "string",
      "description": "Unique identifier for the session (UUID4 recommended)",
      "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    },
    "session_type": {
      "type": "string",
      "enum": ["ssh", "script", "file"],
      "description": "Type of session being monitored"
    },
    "log_file": {
      "type": "string",
      "description": "Absolute path to the session output log file"
    },
    "metadata": {
      "type": "object",
      "description": "Optional session metadata (e.g., SSH host, user)",
      "additionalProperties": {"type": "string"}
    }
  },
  "required": ["session_id", "session_type", "log_file"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "session_id": {"type": "string"},
    "status": {"type": "string", "enum": ["active", "stopped"]},
    "file_position": {"type": "integer"},
    "start_time": {"type": "string", "format": "date-time"},
    "log_file": {"type": "string"}
  },
  "required": ["session_id", "status", "file_position", "start_time", "log_file"]
}
```

### Error Cases

| Error Code | Condition | HTTP Status | Response |
|------------|-----------|-------------|----------|
| `SESSION_ALREADY_EXISTS` | Session ID already active | 409 | `{"error": "Session {id} already exists", "code": "SESSION_ALREADY_EXISTS"}` |
| `FILE_NOT_FOUND` | Log file doesn't exist | 404 | `{"error": "Log file not found: {path}", "code": "FILE_NOT_FOUND"}` |
| `FILE_NOT_READABLE` | Log file permissions invalid | 403 | `{"error": "Cannot read log file: {path}", "code": "FILE_NOT_READABLE"}` |
| `INVALID_SESSION_ID` | Session ID not UUID4 format | 400 | `{"error": "Invalid session_id format", "code": "INVALID_SESSION_ID"}` |

### Test Cases

```python
# Test 1: Successful session start
async def test_start_session_monitor_success():
    result = await client.call_tool("start_session_monitor", {
        "session_id": "abc123-def456-...",
        "session_type": "ssh",
        "log_file": "/tmp/ssk-sessions/test.log",
        "metadata": {"host": "prod-server", "user": "admin"}
    })

    assert result.data["session_id"] == "abc123-def456-..."
    assert result.data["status"] == "active"
    assert result.data["file_position"] == 0
    assert "start_time" in result.data

# Test 2: Duplicate session error
async def test_start_session_duplicate_error():
    # Start first session
    await client.call_tool("start_session_monitor", {...})

    # Try to start with same ID
    with pytest.raises(ToolError) as exc:
        await client.call_tool("start_session_monitor", {...})

    assert exc.value.code == "SESSION_ALREADY_EXISTS"

# Test 3: File not found error
async def test_start_session_file_not_found():
    with pytest.raises(ToolError) as exc:
        await client.call_tool("start_session_monitor", {
            "session_id": "abc123-def456-...",
            "session_type": "file",
            "log_file": "/nonexistent/path.log"
        })

    assert exc.value.code == "FILE_NOT_FOUND"
```

---

## Tool: get_session_updates

**Purpose**: Retrieve new content from monitored session since last check.

**MCP Tool Name**: `get_session_updates`

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "session_id": {
      "type": "string",
      "description": "Session ID to get updates from"
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
    "session_id": {"type": "string"},
    "new_content": {
      "type": "string",
      "description": "New content since last check (may be empty)"
    },
    "file_position": {
      "type": "integer",
      "description": "Current file position after reading"
    },
    "has_more": {
      "type": "boolean",
      "description": "Whether more content is immediately available"
    }
  },
  "required": ["session_id", "new_content", "file_position", "has_more"]
}
```

### Error Cases

| Error Code | Condition | HTTP Status | Response |
|------------|-----------|-------------|----------|
| `SESSION_NOT_FOUND` | Session ID not active | 404 | `{"error": "Session {id} not found", "code": "SESSION_NOT_FOUND"}` |
| `FILE_READ_ERROR` | Cannot read log file | 500 | `{"error": "Failed to read log file", "code": "FILE_READ_ERROR"}` |

### Test Cases

```python
# Test 1: Get updates with new content
async def test_get_session_updates_new_content():
    # Start session
    await client.call_tool("start_session_monitor", {...})

    # Append content to log file
    with open("/tmp/ssk-sessions/test.log", "a") as f:
        f.write("New log line\n")

    # Get updates
    result = await client.call_tool("get_session_updates", {
        "session_id": "abc123-def456-..."
    })

    assert "New log line" in result.data["new_content"]
    assert result.data["file_position"] > 0

# Test 2: No new content
async def test_get_session_updates_empty():
    result = await client.call_tool("get_session_updates", {
        "session_id": "abc123-def456-..."
    })

    assert result.data["new_content"] == ""
    assert result.data["has_more"] == False

# Test 3: Session not found
async def test_get_session_updates_not_found():
    with pytest.raises(ToolError) as exc:
        await client.call_tool("get_session_updates", {
            "session_id": "nonexistent-id"
        })

    assert exc.value.code == "SESSION_NOT_FOUND"
```

---

## Tool: stop_session_monitor

**Purpose**: Stop monitoring a session and cleanup resources.

**MCP Tool Name**: `stop_session_monitor`

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "session_id": {
      "type": "string",
      "description": "Session ID to stop"
    },
    "save_log": {
      "type": "boolean",
      "description": "Whether to preserve log file (default: false)",
      "default": false
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
    "session_id": {"type": "string"},
    "status": {"type": "string", "enum": ["stopped"]},
    "total_bytes_processed": {"type": "integer"},
    "session_duration_seconds": {"type": "number"}
  },
  "required": ["session_id", "status", "total_bytes_processed", "session_duration_seconds"]
}
```

### Error Cases

| Error Code | Condition | HTTP Status | Response |
|------------|-----------|-------------|----------|
| `SESSION_NOT_FOUND` | Session ID not active | 404 | `{"error": "Session {id} not found", "code": "SESSION_NOT_FOUND"}` |

### Test Cases

```python
# Test 1: Stop session successfully
async def test_stop_session_monitor():
    # Start session
    await client.call_tool("start_session_monitor", {...})

    # Stop session
    result = await client.call_tool("stop_session_monitor", {
        "session_id": "abc123-def456-...",
        "save_log": False
    })

    assert result.data["status"] == "stopped"
    assert result.data["total_bytes_processed"] >= 0
    assert result.data["session_duration_seconds"] > 0

# Test 2: Session not found
async def test_stop_session_not_found():
    with pytest.raises(ToolError) as exc:
        await client.call_tool("stop_session_monitor", {
            "session_id": "nonexistent-id"
        })

    assert exc.value.code == "SESSION_NOT_FOUND"

# Test 3: Log file cleanup
async def test_stop_session_log_cleanup():
    log_path = "/tmp/ssk-sessions/test.log"

    # Start session
    await client.call_tool("start_session_monitor", {...})
    assert os.path.exists(log_path)

    # Stop without saving
    await client.call_tool("stop_session_monitor", {
        "session_id": "abc123-def456-...",
        "save_log": False
    })

    # Log should be deleted
    assert not os.path.exists(log_path)
```

---

**Contract Status**: ✅ Complete - Ready for test-first implementation
