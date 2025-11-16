# Data Model: MCP Session Monitor

**Branch**: `001-mcp-session-monitor` | **Date**: 2025-11-14
**Phase**: 1 (Design) | **Status**: Complete

## Overview

This document defines the core entities for the MCP Session Monitor feature. All entities use Python dataclasses for type safety and automatic JSON schema generation with FastMCP.

## Entity Diagram

```
┌─────────────┐
│   Session   │──────┐
└─────────────┘      │
      │              │
      │ 1:N          │ 1:N
      ▼              ▼
┌─────────────────┐  ┌─────────────┐
│ PromptDetection │  │ InputEvent  │
└─────────────────┘  └─────────────┘
                          │
                          │ N:1
                          ▼
                     ┌─────────────┐
                     │   Pattern   │
                     └─────────────┘
```

## Core Entities

### Session

Represents an active terminal session being monitored.

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class SessionType(str, Enum):
    """Type of session being monitored."""
    SSH = "ssh"
    SCRIPT = "script"
    FILE = "file"

class SessionState(str, Enum):
    """Current state of the session."""
    ACTIVE = "active"
    STOPPED = "stopped"

@dataclass
class Session:
    """
    Represents a monitored terminal session.

    Attributes:
        session_id: Unique identifier (UUID4 recommended)
        session_type: Type of session (SSH, script, file)
        log_file: Absolute path to session output log
        file_position: Current read position in log file (bytes)
        start_time: When monitoring started (ISO 8601)
        state: Current session state (active, stopped)
        metadata: Optional session metadata (e.g., SSH host, user)
    """
    session_id: str
    session_type: SessionType
    log_file: str
    file_position: int
    start_time: datetime
    state: SessionState
    metadata: dict[str, str] | None = None

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict for MCP responses."""
        return {
            "session_id": self.session_id,
            "session_type": self.session_type.value,
            "log_file": self.log_file,
            "file_position": self.file_position,
            "start_time": self.start_time.isoformat(),
            "state": self.state.value,
            "metadata": self.metadata or {}
        }
```

**Storage**: In-memory dict (`active_sessions[session_id] = Session(...)`)

**Lifecycle**:
1. Create → `start_session_monitor()` MCP tool
2. Update → `get_session_updates()` increments `file_position`
3. Delete → `stop_session_monitor()` removes from active sessions

### PromptDetection

Represents a detected prompt waiting for user input.

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class PromptType(str, Enum):
    """Type of detected prompt."""
    PASSWORD = "password"
    YES_NO = "yes_no"
    CHOICE = "choice"
    PATH = "path"
    TEXT = "text"
    COMMAND = "command"
    UNKNOWN = "unknown"

@dataclass
class PromptDetection:
    """
    Represents a detected terminal prompt.

    Attributes:
        prompt_text: The text of the detected prompt
        confidence: Detection confidence score (0.0-1.0)
        prompt_type: Type of prompt detected
        matched_pattern: Regex pattern that matched (for debugging)
        file_position: Position in log file where detected (bytes)
        timestamp: When prompt was detected (ISO 8601)
        is_dangerous: Whether prompt involves dangerous operations
    """
    prompt_text: str
    confidence: float
    prompt_type: PromptType
    matched_pattern: str
    file_position: int
    timestamp: datetime
    is_dangerous: bool = False

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict for MCP responses."""
        return {
            "prompt_text": self.prompt_text,
            "confidence": self.confidence,
            "prompt_type": self.prompt_type.value,
            "matched_pattern": self.matched_pattern,
            "file_position": self.file_position,
            "timestamp": self.timestamp.isoformat(),
            "is_dangerous": self.is_dangerous
        }
```

**Storage**: Not persisted (ephemeral detection results)

**Usage**: Returned by `detect_input_prompt()` MCP tool

### InputEvent

Represents a recorded user input in response to a prompt.

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class InputSource(str, Enum):
    """Source of the input."""
    USER_TYPED = "user_typed"
    AI_SUGGESTED = "ai_suggested"
    AUTO_INJECTED = "auto_injected"

@dataclass
class InputEvent:
    """
    Represents a user input event.

    Attributes:
        event_id: Unique event identifier (UUID4)
        session_id: Associated session ID
        timestamp: When input was provided (ISO 8601)
        prompt_text: The prompt that triggered input
        input_text: The text user provided (REDACTED for passwords)
        success: Whether input was accepted (True) or rejected (False)
        input_source: How input was provided
        response_time_ms: Time between prompt and input (milliseconds)
    """
    event_id: str
    session_id: str
    timestamp: datetime
    prompt_text: str
    input_text: str  # "[REDACTED]" for passwords
    success: bool
    input_source: InputSource
    response_time_ms: int

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict for storage."""
        return {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "prompt_text": self.prompt_text,
            "input_text": self.input_text,
            "success": self.success,
            "input_source": self.input_source.value,
            "response_time_ms": self.response_time_ms
        }
```

**Storage**: JSON file per session (`/tmp/ssk-sessions/history/{session_id}.json`)

**Security**: Password inputs MUST be stored as `"[REDACTED]"` (never plaintext)

### Pattern

Represents a learned prompt-response pattern.

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ResponseStats:
    """Statistics for a specific response to a prompt."""
    count: int
    success_count: int

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0-1.0)."""
        return self.success_count / self.count if self.count > 0 else 0.0

@dataclass
class Pattern:
    """
    Represents a learned prompt-response pattern.

    Attributes:
        pattern_id: Unique pattern identifier (hash of prompt_text)
        prompt_text: The prompt text (normalized)
        responses: Map of response text → statistics
        total_occurrences: Total times this prompt appeared
        last_seen: Last time this prompt was detected (ISO 8601)
        created_at: When pattern was first learned (ISO 8601)
    """
    pattern_id: str
    prompt_text: str
    responses: dict[str, ResponseStats]
    total_occurrences: int
    last_seen: datetime
    created_at: datetime

    def get_most_common_response(self) -> tuple[str, ResponseStats] | None:
        """Get the most frequently used response."""
        if not self.responses:
            return None
        return max(self.responses.items(), key=lambda x: x[1].count)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict for storage."""
        return {
            "pattern_id": self.pattern_id,
            "prompt_text": self.prompt_text,
            "responses": {
                text: {"count": stats.count, "success_count": stats.success_count}
                for text, stats in self.responses.items()
            },
            "total_occurrences": self.total_occurrences,
            "last_seen": self.last_seen.isoformat(),
            "created_at": self.created_at.isoformat()
        }
```

**Storage**: Global JSON file (`/tmp/ssk-sessions/patterns.json`)

**Update Strategy**:
- Load patterns on server start
- Update in-memory during session
- Persist on graceful shutdown or every 100 events

## Data Relationships

### Session → PromptDetection (1:N)

- One session can have multiple prompt detections
- Detections are ephemeral (not persisted)
- Accessed via `detect_input_prompt(session_id)` tool

### Session → InputEvent (1:N)

- One session records multiple input events
- Events are persisted to session history file
- Accessed via `track_input_event(session_id, ...)` tool

### InputEvent → Pattern (N:1)

- Multiple input events contribute to one pattern
- Pattern learning aggregates across all sessions
- Accessed via `infer_expected_input(prompt_text)` tool

## Data Storage Layout

```
/tmp/ssk-sessions/
├── session-{uuid}.log          # Active session logs (ephemeral)
├── history/
│   ├── session-{uuid}.json     # Input event history per session
│   └── ...
└── patterns.json               # Global pattern learning data
```

### Example: Session History File

```json
{
  "session_id": "abc123-def456-...",
  "events": [
    {
      "event_id": "evt-001",
      "session_id": "abc123-def456-...",
      "timestamp": "2025-11-14T10:30:00Z",
      "prompt_text": "Password:",
      "input_text": "[REDACTED]",
      "success": true,
      "input_source": "user_typed",
      "response_time_ms": 250
    },
    {
      "event_id": "evt-002",
      "session_id": "abc123-def456-...",
      "timestamp": "2025-11-14T10:31:00Z",
      "prompt_text": "Continue? (yes/no)",
      "input_text": "yes",
      "success": true,
      "input_source": "ai_suggested",
      "response_time_ms": 150
    }
  ]
}
```

### Example: Global Patterns File

```json
{
  "patterns": [
    {
      "pattern_id": "hash-restart-services",
      "prompt_text": "Restart services immediately?",
      "responses": {
        "no": {
          "count": 10,
          "success_count": 10
        },
        "yes": {
          "count": 0,
          "success_count": 0
        }
      },
      "total_occurrences": 10,
      "last_seen": "2025-11-14T10:00:00Z",
      "created_at": "2025-11-01T09:00:00Z"
    }
  ]
}
```

## Validation Rules

### Session Validation

- `session_id`: Must be valid UUID4
- `log_file`: Must be absolute path, file must exist and be readable
- `file_position`: Must be >= 0, <= file size
- `start_time`: Must be valid ISO 8601 datetime

### PromptDetection Validation

- `confidence`: Must be 0.0 <= confidence <= 1.0
- `prompt_text`: Must not be empty
- `matched_pattern`: Must be valid regex pattern
- `file_position`: Must be >= 0

### InputEvent Validation

- `event_id`: Must be valid UUID4
- `session_id`: Must reference existing session
- `input_text`: If prompt is password, must be "[REDACTED]"
- `success`: Must be boolean
- `response_time_ms`: Must be >= 0

### Pattern Validation

- `pattern_id`: Must be unique hash
- `total_occurrences`: Must equal sum of all response counts
- `responses`: Each ResponseStats.success_count <= ResponseStats.count

## Performance Considerations

### Memory Footprint (Per Session)

```
Session object:          ~1KB
Last 1000 lines buffer:  ~100KB
Pattern cache:           ~10KB
Total:                   ~111KB per session
```

**Target**: <50MB per session (current: 111KB = well within budget)

### Disk Usage (Per Session, 7-day retention)

```
Session log (8 hours):   ~5MB (assuming 1000 lines/hour, 100 chars/line)
History JSON:            ~50KB (assuming 100 events)
Global patterns:         ~100KB (shared across all sessions)
Total:                   ~5.15MB per session
```

**Scaling**: 10 concurrent sessions × 7 days = ~360MB total disk usage (acceptable)

## Schema Evolution Strategy

### Version 1.0 (Current)

Initial schema with all core entities.

### Future Enhancements

**Version 1.1** (Potential):
- Add `Session.parent_session_id` for nested SSH sessions
- Add `PromptDetection.suggested_inputs: list[str]` for AI-generated suggestions
- Add `Pattern.context: dict` for environmental context (time of day, user, host)

**Migration Strategy**:
- Dataclass fields with defaults for backward compatibility
- JSON schema versioning in storage files: `{"schema_version": "1.0", "data": ...}`

---

**Data Model Complete**: All entities defined with validation rules and storage strategy. Ready for contract generation.
