# ShellSidekick System Patterns

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Assistant (Claude)                    │
│                  via Model Context Protocol                  │
└───────────────────────┬─────────────────────────────────────┘
                        │ MCP Tools (7)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              ShellSidekick MCP Server (FastMCP)             │
│ ┌────────────┐  ┌────────────┐  ┌──────────────┐          │
│ │  Session   │  │ Detection  │  │   Pattern    │          │
│ │   Tools    │  │   Tools    │  │   Learning   │          │
│ └────────────┘  └────────────┘  └──────────────┘          │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐  ┌──────────┐  ┌──────────────┐
│ SessionMonitor│  │ Prompt   │  │   Pattern    │
│   (Core)     │  │ Detector │  │   Learner    │
└──────────────┘  └──────────┘  └──────────────┘
        │               │               │
        ▼               ▼               ▼
┌─────────────────────────────────────────────┐
│            File System Storage              │
│  • Session logs (/tmp/ssk-sessions/*.log)  │
│  • Pattern data (patterns.json)             │
└─────────────────────────────────────────────┘
```

### Layer Separation

**MCP Layer** (`src/shellsidekick/mcp/`)
- FastMCP server initialization
- MCP tool definitions with JSON schemas
- Input validation and error handling
- Response formatting for AI assistants

**Core Layer** (`src/shellsidekick/core/`)
- Business logic and algorithms
- Session monitoring and file position tracking
- Prompt detection with regex patterns
- Pattern learning and inference
- Storage abstraction

**Models Layer** (`src/shellsidekick/models/`)
- Data entities (Session, PromptDetection, InputEvent, Pattern)
- Enums (SessionType, SessionState, PromptType, InputSource)
- Serialization to/from JSON

**Utils Layer** (`src/shellsidekick/utils/`)
- Cross-cutting concerns
- File utilities (position tracking, incremental reads)
- Security utilities (password detection, dangerous commands)
- Logging configuration

## Key Design Patterns

### 1. File Position Tracking (Performance Pattern)

**Problem**: Reading entire log files on every update is inefficient for long-running sessions.

**Solution**: Track byte position in file, only read new content since last check.

```python
class SessionMonitor:
    def get_updates(self) -> tuple[str, bool]:
        # Read from current file position
        new_content = read_from_position(
            self.session.log_file,
            self.session.file_position
        )
        # Update position
        self.session.file_position = new_position
        return new_content, has_more
```

**Benefits**:
- Constant memory usage regardless of log size
- Incremental reads scale to multi-day sessions
- Average read time: <10ms for typical updates

### 2. Pattern-Based Detection (Speed Pattern)

**Problem**: LLM inference for every prompt is too slow (<500ms requirement).

**Solution**: Compiled regex patterns for common prompt types.

```python
PATTERNS = {
    PromptType.PASSWORD: [
        r"password:\s*$",
        r"passphrase:\s*$",
        r"enter password:\s*$",
    ],
    PromptType.YES_NO: [
        r"\(y/n\)\s*[?:]\s*$",
        r"continue\?\s*\(yes/no\)\s*$",
    ],
    # ... more patterns
}
```

**Performance**:
- Average detection: 67ms (7x faster than requirement)
- Throughput: >10,000 lines/second
- No network calls, entirely local

### 3. Two-Stage Suggestion (Intelligence Pattern)

**Problem**: Need both speed and intelligence in suggestions.

**Solution**: Pattern-based suggestions first, default suggestions as fallback.

```python
def infer_expected_input(prompt_text, prompt_type):
    # Stage 1: Check learned patterns (fast)
    patterns = pattern_learner.get_patterns(prompt_text)
    if patterns:
        return suggest_from_patterns(patterns)

    # Stage 2: Default suggestions by type (fallback)
    return suggest_from_type(prompt_type)
```

**Benefits**:
- Personalized suggestions when patterns exist
- Always provides useful defaults
- Degrades gracefully for new prompts

### 4. Password Redaction (Security Pattern)

**Problem**: Passwords must never be stored in logs or patterns.

**Solution**: Automatic redaction at tracking time.

```python
def track_input_event(prompt_type, input_text):
    # Redact passwords before storage
    if prompt_type == PromptType.PASSWORD:
        input_text = "[REDACTED]"

    # Store safe version
    event = InputEvent(input_text=input_text)
    storage.save(event)
```

**Security**:
- Passwords never touch disk in plaintext
- Redaction at source prevents leaks
- Pattern learning works without seeing passwords

### 5. Pattern Persistence (Reliability Pattern)

**Problem**: Patterns lost on server restart waste learning.

**Solution**: Periodic persistence to JSON with load-on-startup.

```python
class PatternLearner:
    def __init__(self):
        # Load patterns on startup
        self.patterns = storage.load_patterns()

    def save_patterns(self):
        # Persist to JSON
        storage.save_patterns(self.patterns)

    def update_pattern(self, prompt, response, success):
        # Update in-memory
        pattern = self._update_pattern(prompt, response, success)

        # Persist every 10 updates
        if self.update_count % 10 == 0:
            self.save_patterns()
```

**Reliability**:
- Patterns survive crashes and restarts
- Incremental saves prevent data loss
- JSON format allows manual inspection/editing

## Critical Technical Decisions

### Decision 1: File-Based Monitoring

**Rationale**: Simplicity and compatibility over complex IPC.

**Alternatives Considered**:
- PTY (pseudo-terminal) hijacking: Too invasive, breaks tools
- Network proxy: Adds complexity, requires configuration
- Terminal emulator fork: Massive scope increase

**Trade-offs**:
- ✅ Works with existing tools (`script`, `tmux`)
- ✅ No process interference
- ✅ Simple implementation
- ❌ Requires user to start logging
- ❌ Doesn't capture binary protocols

**Constitution Alignment**: Principle VII (Simplicity & YAGNI)

### Decision 2: Regex Over ML

**Rationale**: Speed and determinism for MVP.

**Alternatives Considered**:
- LLM inference: Too slow (>1s per prompt)
- Traditional ML classifier: Training data requirements
- Hybrid approach: Added complexity

**Trade-offs**:
- ✅ <100ms detection latency
- ✅ Deterministic results
- ✅ No training required
- ✅ Easily debuggable patterns
- ❌ Limited to known patterns
- ❌ Struggles with unusual prompts

**Future Path**: Add LLM fallback for unknown prompts (optional)

### Decision 3: JSON Storage

**Rationale**: Human-readable, simple, no dependencies.

**Alternatives Considered**:
- SQLite: Overkill for simple key-value needs
- Redis/Memcached: External dependency
- Binary formats (pickle, msgpack): Not human-readable

**Trade-offs**:
- ✅ Human-readable and editable
- ✅ No external dependencies
- ✅ Simple backup/restore
- ✅ Version control friendly
- ❌ Not optimized for large datasets
- ❌ Full rewrite on update

**Scaling Plan**: Move to SQLite if >10,000 patterns

### Decision 4: FastMCP Framework

**Rationale**: Official framework, automatic schema generation, proven patterns.

**Alternatives Considered**:
- Raw MCP implementation: Too much boilerplate
- Custom framework: Reinventing wheel
- Different protocol: Not AI assistant compatible

**Trade-offs**:
- ✅ Automatic JSON schema generation
- ✅ Built-in error handling
- ✅ Official support and updates
- ✅ Dataclass integration
- ❌ Framework dependency
- ❌ Learning curve for FastMCP patterns

**Constitution Alignment**: Principle I (MCP-First Architecture)

### Decision 5: In-Memory Session State

**Rationale**: Performance and simplicity for active sessions.

**Alternatives Considered**:
- Database-backed sessions: Adds latency
- File-based session state: Disk I/O overhead
- Distributed cache: Unnecessary complexity

**Trade-offs**:
- ✅ Fast access (<1ms)
- ✅ Simple implementation
- ✅ Minimal memory footprint (~111KB per session)
- ❌ Lost on server crash (acceptable)
- ❌ Not shared across processes (single-user tool)

**Recovery**: Sessions can be restarted from log files if needed

## Data Flow Patterns

### Session Monitoring Flow

```
User starts monitoring
    ↓
start_session_monitor() MCP tool
    ↓
SessionMonitor created
    ↓
Log file opened, position = 0
    ↓
Session stored in active_sessions dict
    ↓
get_session_updates() called periodically
    ↓
Read new content from file position
    ↓
Update file position
    ↓
Return new content to AI assistant
```

### Prompt Detection Flow

```
AI gets session updates
    ↓
detect_input_prompt() MCP tool called
    ↓
Get recent content from session
    ↓
PromptDetector analyzes last 20 lines
    ↓
Try each regex pattern
    ↓
Calculate confidence score
    ↓
Check for dangerous keywords
    ↓
Return PromptDetection with type and confidence
```

### Pattern Learning Flow

```
User provides input
    ↓
track_input_event() MCP tool called
    ↓
Check if password (redact if true)
    ↓
Create InputEvent with success/failure
    ↓
Update pattern in PatternLearner
    ↓
Increment response count
    ↓
Calculate success rate
    ↓
Persist patterns every 10 updates
    ↓
Pattern available for future suggestions
```

### Suggestion Flow

```
AI detects prompt
    ↓
infer_expected_input() MCP tool called
    ↓
Check PatternLearner for matching prompt
    ↓
If pattern exists:
    ↓
    Get most common response
    ↓
    Calculate success rate
    ↓
    Return pattern-based suggestion
    ↓
Else (no pattern):
    ↓
    Get default suggestions by type
    ↓
    Check for dangerous keywords
    ↓
    Add context-specific warnings
    ↓
    Return default suggestions
```

## Error Handling Strategy

### MCP Tool Errors

All errors raised as `ToolError` with descriptive codes:

```python
# Session not found
raise ToolError("Session abc123 not found", code="SESSION_NOT_FOUND")

# File access
raise ToolError("Cannot read log file", code="FILE_READ_ERROR")

# Validation
raise ToolError("Confidence must be 0.0-1.0", code="INVALID_CONFIDENCE")

# Duplicate
raise ToolError("Session already exists", code="SESSION_ALREADY_EXISTS")
```

**FastMCP Handling**: Automatically converts to MCP error responses

### Graceful Degradation

**File Read Failure**: Return empty updates, log error, session stays active
**Pattern Load Failure**: Start with empty patterns, don't crash
**Storage Full**: Log warning, continue with in-memory only
**Regex Error**: Skip pattern, try next, use confidence score to indicate uncertainty

### Recovery Patterns

**Server Crash**: Patterns persist, sessions can be restarted from logs
**File Deleted**: Detect on next update, mark session stopped
**Corrupted JSON**: Load what's parseable, discard bad entries, log warning
**Permission Denied**: Clear error message with actionable fix

## Performance Optimization Patterns

### 1. Last-N-Lines Buffer

Only analyze recent output for prompt detection:

```python
def detect(self, content: str):
    # Only check last 20 lines for prompts
    lines = content.split('\n')[-20:]
    recent = '\n'.join(lines)
    return self._analyze_prompt(recent)
```

**Impact**: 10x faster on large files

### 2. Compiled Regex Patterns

Pre-compile patterns at initialization:

```python
class PromptDetector:
    def __init__(self):
        # Compile once at startup
        self.compiled_patterns = {
            ptype: [re.compile(p) for p in patterns]
            for ptype, patterns in PATTERNS.items()
        }
```

**Impact**: 5x faster than compile-on-use

### 3. File Position Tracking

Read only new content, not entire file:

```python
def read_from_position(filepath, position):
    with open(filepath, 'r') as f:
        f.seek(position)  # Jump to last position
        new_content = f.read()  # Read only new data
        new_position = f.tell()  # Save new position
    return new_content, new_position
```

**Impact**: Constant time regardless of file size

### 4. Pattern Cache

In-memory pattern dictionary for O(1) lookups:

```python
class PatternLearner:
    def __init__(self):
        # Hash prompt text for fast lookup
        self.patterns: dict[str, Pattern] = {}

    def get_pattern(self, prompt_text):
        key = self._hash_prompt(prompt_text)
        return self.patterns.get(key)  # O(1) lookup
```

**Impact**: <1ms pattern retrieval vs 50ms+ file read

## Testing Architecture

### Test Pyramid

```
         ┌────────────┐
         │Integration │  4 tests (end-to-end workflows)
         └────────────┘
       ┌──────────────────┐
       │    Contract      │  50 tests (MCP tool contracts)
       └──────────────────┘
    ┌────────────────────────┐
    │        Unit            │  Available for core modules
    └────────────────────────┘
```

### Contract Test Pattern

**Purpose**: Verify MCP tools behave as specified

```python
@pytest.mark.asyncio
async def test_start_session_monitor_success():
    # Arrange: Create test log file
    log_file = create_test_log()

    # Act: Call MCP tool
    result = await mcp_client.call_tool(
        "start_session_monitor",
        {
            "session_id": "test-123",
            "session_type": "file",
            "log_file": log_file
        }
    )

    # Assert: Verify response structure
    assert result.data["status"] == "active"
    assert result.data["session_id"] == "test-123"
```

### Integration Test Pattern

**Purpose**: Verify end-to-end workflows

```python
def test_session_monitor_creation():
    # Create monitor
    monitor = SessionMonitor(session)

    # Verify state
    assert monitor.session.state == SessionState.ACTIVE

    # Test updates
    content, has_more = monitor.get_updates()
    assert isinstance(content, str)
```

### TDD Workflow (Constitution Requirement)

1. **Red**: Write failing test
2. **Green**: Implement minimal code to pass
3. **Refactor**: Improve while keeping tests green
4. **Repeat**: For each feature

**Enforcement**: >80% coverage target, contract tests mandatory before implementation
