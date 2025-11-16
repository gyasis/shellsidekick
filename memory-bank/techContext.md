# ShellSidekick Technical Context

## Technology Stack

### Core Technologies

**Language**: Python 3.11+
- Type hints enforced throughout
- Dataclasses for entities
- Async support for FastMCP integration
- Standard library preferred over dependencies

**Framework**: FastMCP (latest from `/jlowin/fastmcp`)
- Official MCP server framework
- Automatic JSON schema generation
- Built-in error handling via `ToolError`
- Dataclass integration for tools

**Package Manager**: uv
- Fast dependency resolution
- Virtual environment isolation
- Lock file for reproducibility
- Replaces pip/poetry

**Testing**: pytest + pytest-asyncio
- Async test support for MCP tools
- Fixture-based test organization
- Coverage reporting via pytest-cov
- TDD workflow enforced

**Code Quality**:
- black (formatter)
- ruff (linter, replaces flake8)
- Type checking via mypy (optional)

### Dependencies

**Runtime**:
```toml
[project]
dependencies = [
    "fastmcp>=0.5.0",  # MCP server framework
]
```

**Development**:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-cov>=4.0",
    "black>=23.0",
    "ruff>=0.1.0",
]
```

**Philosophy**: Minimal dependencies, standard library first, no unnecessary abstractions

## Project Setup

### Environment Setup

```bash
# Clone repository
git clone <repo-url>
cd shellsidekick

# Install dependencies with uv
uv sync

# Run tests
uv run pytest

# Format code
uv run black src/ tests/

# Lint
uv run ruff check --fix src/ tests/

# Run server
uv run python src/shellsidekick/mcp/server.py
```

### Development Mode

```bash
# Run server with hot reload
uv run fastmcp dev src/shellsidekick/mcp/server.py --reload

# Run specific tests
uv run pytest tests/contract/test_session_tools.py -v

# Run with coverage
uv run pytest --cov=src/shellsidekick --cov-report=html
```

### MCP Configuration

```bash
# Generate MCP config for Claude Desktop
uv run fastmcp install src/shellsidekick/mcp/server.py

# This adds to ~/.config/claude/claude_desktop_config.json:
# {
#   "mcpServers": {
#     "ShellSidekick": {
#       "command": "uv",
#       "args": ["run", "python", "src/shellsidekick/mcp/server.py"]
#     }
#   }
# }
```

## File System Layout

### Directory Structure

```
/home/gyasis/Documents/code/shellsidekick/
├── .claude/                          # Agent context for AI assistants
│   └── CLAUDE.md                     # Project-specific AI instructions
├── .specify/                         # SpecKit configuration
│   ├── memory/
│   │   └── constitution.md           # Project constitution (7 principles)
│   └── templates/                    # Spec templates
├── .specstory/                       # Development story tracking
│   └── history/                      # Session histories
├── memory-bank/                      # Session continuity docs
│   ├── projectbrief.md              # Project overview
│   ├── productContext.md            # Why project exists
│   ├── activeContext.md             # Current work focus
│   ├── systemPatterns.md            # Architecture decisions
│   ├── techContext.md               # This file
│   └── progress.md                  # Implementation status
├── specs/                            # Feature specifications
│   └── 001-mcp-session-monitor/
│       ├── spec.md                   # User stories, requirements
│       ├── plan.md                   # Implementation plan
│       ├── tasks.md                  # Task breakdown
│       ├── research.md               # Technical research
│       ├── data-model.md             # Entity definitions
│       ├── quickstart.md             # Getting started guide
│       └── contracts/                # MCP tool contracts
│           ├── session-tools.md
│           ├── detection-tools.md
│           └── history-tools.md
├── src/
│   └── shellsidekick/
│       ├── __init__.py
│       ├── mcp/                      # MCP server layer
│       │   ├── server.py             # FastMCP initialization
│       │   ├── session_state.py      # Global state management
│       │   └── tools/                # MCP tool implementations
│       │       ├── session.py        # Session lifecycle tools
│       │       ├── detection.py      # Prompt detection tools
│       │       └── history.py        # Pattern retrieval tools
│       ├── core/                     # Business logic
│       │   ├── monitor.py            # SessionMonitor class
│       │   ├── detector.py           # PromptDetector with patterns
│       │   ├── inference.py          # InputInferenceEngine
│       │   ├── patterns.py           # PatternLearner
│       │   └── storage.py            # File I/O and persistence
│       ├── models/                   # Data entities
│       │   ├── session.py            # Session, SessionType, SessionState
│       │   ├── prompt.py             # PromptDetection, PromptType
│       │   ├── input_event.py        # InputEvent, InputSource
│       │   └── pattern.py            # Pattern, ResponseStats
│       └── utils/                    # Cross-cutting utilities
│           ├── file_utils.py         # File position tracking
│           ├── security.py           # Password detection, dangerous commands
│           └── logging.py            # Structured logging
├── tests/
│   ├── conftest.py                   # Pytest fixtures
│   ├── contract/                     # MCP tool contract tests
│   │   ├── test_session_tools.py
│   │   ├── test_detection_tools.py
│   │   ├── test_history_tools.py
│   │   └── test_pattern_persistence.py
│   ├── integration/                  # End-to-end tests
│   │   ├── test_basic_workflow.py
│   │   └── test_context_suggestions.py
│   └── unit/                         # Unit tests
│       └── (available for core modules)
├── pyproject.toml                    # uv project configuration
├── uv.lock                           # Locked dependencies
└── README.md                         # Project overview
```

### Runtime Storage

```
/tmp/ssk-sessions/                    # Session data (ephemeral)
├── session-{uuid}.log                # Active session logs
└── patterns.json                     # Learned patterns (persistent)
```

**Permissions**: All files chmod 600 (user-only access)
**Retention**: 7 days default, configurable via environment
**Cleanup**: Automatic on server shutdown or via cleanup tool

## Development Workflow

### TDD Cycle (Constitution Requirement)

```bash
# 1. Write test (RED)
uv run pytest tests/contract/test_session_tools.py::test_start_session -v
# Expected: FAILED (not implemented)

# 2. Implement minimal code (GREEN)
# ... write implementation ...
uv run pytest tests/contract/test_session_tools.py::test_start_session -v
# Expected: PASSED

# 3. Refactor (REFACTOR)
# ... improve code quality ...
uv run pytest tests/contract/test_session_tools.py -v
# Expected: All PASSED

# 4. Commit
git add .
git commit -m "feat: implement start_session_monitor tool"
```

### Code Quality Workflow

```bash
# Format before commit
uv run black src/ tests/

# Lint and fix
uv run ruff check --fix src/ tests/

# Type check (optional)
uv run mypy src/

# Run full test suite
uv run pytest

# Check coverage
uv run pytest --cov=src/shellsidekick --cov-report=term-missing
# Target: >80% for core modules
```

### FastMCP Development Patterns

**Tool Definition**:
```python
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

mcp = FastMCP(name="ShellSidekick")

@mcp.tool()
def start_session_monitor(
    session_id: str,
    session_type: str,
    log_file: str,
    metadata: dict[str, str] | None = None
) -> dict:
    """Start monitoring a terminal session."""
    # Validation
    if session_id in active_sessions:
        raise ToolError(
            f"Session {session_id} already exists",
            code="SESSION_ALREADY_EXISTS"
        )

    # Implementation
    session = create_session(session_id, session_type, log_file, metadata)
    active_sessions[session_id] = SessionMonitor(session)

    # Return
    return session.to_dict()
```

**Error Handling**:
```python
# Always use ToolError for MCP-compatible errors
raise ToolError("Error message", code="ERROR_CODE")

# FastMCP converts to:
# {"error": "Error message", "code": "ERROR_CODE"}
```

**Testing MCP Tools**:
```python
@pytest.mark.asyncio
async def test_tool(mcp_client):
    result = await mcp_client.call_tool(
        "start_session_monitor",
        {"session_id": "test", "session_type": "file", "log_file": "/tmp/test.log"}
    )
    assert result.data["status"] == "active"
```

## Platform Constraints

### Supported Platforms

✅ **Linux**: Primary target, fully tested
✅ **macOS**: Supported, tested manually
✅ **WSL (Windows Subsystem for Linux)**: Supported via Unix compatibility

❌ **Native Windows**: Not supported (PowerShell incompatible)
❌ **BSD/Unix variants**: Untested, may work

### Required System Tools

**Essential**:
- Python 3.11+ (runtime)
- `script` command (session recording) OR
- `tmux` with `pipe-pane` (alternative recording method)

**Optional**:
- `ssh` (for SSH session monitoring)
- Terminal with ANSI support (for colored output)

### File System Requirements

- `/tmp` directory writable (or `SSK_SESSION_DIR` environment variable)
- Sufficient disk space for logs (5MB per 8-hour session)
- Unix file permissions (chmod support)

## Performance Characteristics

### Benchmarks (From Testing)

**Prompt Detection**:
- Average latency: 67ms (target: <500ms)
- 95th percentile: 120ms
- 99th percentile: 180ms
- Throughput: >10,000 lines/second

**Memory Usage**:
- Base server: ~30MB
- Per session: ~111KB
- 10 concurrent sessions: ~32MB total
- Well within <50MB per session target

**Disk Usage**:
- Session log (8 hours): ~5MB
- Pattern data: ~100KB (shared)
- 10 sessions, 7 days: ~360MB total

**File I/O**:
- Incremental read: <10ms average
- Pattern save: <50ms
- Full pattern load: <100ms

### Scaling Limits

**Concurrent Sessions**: 10 without performance impact (tested)
**Max Session Duration**: Unlimited (file position tracking prevents memory growth)
**Max Log File Size**: Limited only by disk space (incremental reads)
**Max Patterns**: ~10,000 before SQLite migration recommended

## Configuration

### Environment Variables

```bash
# Session storage directory (default: /tmp/ssk-sessions)
export SSK_SESSION_DIR=/custom/path

# Log retention days (default: 7)
export SSK_LOG_RETENTION_DAYS=14

# Log level (default: INFO)
export SSK_LOG_LEVEL=DEBUG

# Pattern persistence interval (default: 10 updates)
export SSK_PATTERN_SAVE_INTERVAL=5
```

### Runtime Configuration

**Prompt Detection**:
```python
# Confidence threshold (0.0-1.0)
detect_input_prompt(session_id, min_confidence=0.70)  # default

# Adjust for sensitivity:
# 0.5-0.7: More detections, some false positives
# 0.7-0.9: Balanced (recommended)
# 0.9-1.0: Conservative, fewer false positives
```

**Pattern Learning**:
```python
# Filter patterns by minimum occurrences
get_learned_patterns(min_occurrences=3)  # ignore patterns with <3 instances

# Filter by prompt text
get_learned_patterns(prompt_filter="restart")  # only restart-related patterns
```

## Common Development Tasks

### Adding a New Prompt Type

1. Add enum value to `PromptType` in `models/prompt.py`
2. Add regex patterns to `PATTERNS` dict in `core/detector.py`
3. Add default suggestions to `InputInferenceEngine` in `core/inference.py`
4. Add contract tests in `tests/contract/test_detection_tools.py`
5. Update documentation

### Adding a New MCP Tool

1. Define function in appropriate `mcp/tools/*.py` module
2. Decorate with `@mcp.tool()`
3. Add type hints and docstring
4. Raise `ToolError` for errors
5. Write contract tests in `tests/contract/`
6. Update tool documentation

### Debugging MCP Server

```bash
# Run server with debug logging
export SSK_LOG_LEVEL=DEBUG
uv run python src/shellsidekick/mcp/server.py

# Use FastMCP dev mode for hot reload
uv run fastmcp dev src/shellsidekick/mcp/server.py --reload

# Test tools directly (without MCP)
uv run python -c "
from shellsidekick.mcp.tools.session import start_session_monitor
result = start_session_monitor('test', 'file', '/tmp/test.log')
print(result)
"
```

### Accessing FastMCP Documentation

```python
# Use Context7 MCP tool (if available)
# resolve-library-id: "/jlowin/fastmcp"
# get-library-docs: topic="server setup, tools, error handling"
```

Or visit: https://github.com/jlowin/fastmcp

## Known Issues and Workarounds

### Issue: FastMCP Import Order

**Problem**: Tools must be imported after `mcp` instance created
**Workaround**: Import tools at bottom of `server.py`

```python
# server.py
mcp = FastMCP(name="ShellSidekick")

# Must import AFTER mcp initialized
from shellsidekick.mcp.tools import session  # noqa: E402
```

### Issue: Async Test Fixtures

**Problem**: pytest-asyncio requires `asyncio_mode="auto"`
**Workaround**: Set in `pyproject.toml`

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### Issue: File Position Edge Cases

**Problem**: Log file truncated or rotated externally
**Solution**: Detect file size decrease, reset position to 0

```python
if new_size < file_position:
    # File truncated, reset
    file_position = 0
```

## Security Considerations

### Password Handling

- Never log passwords in plaintext
- Redact at tracking time: `input_text = "[REDACTED]"`
- Use `PromptType.PASSWORD` to trigger redaction
- Patterns don't store actual password values

### File Permissions

- All session files: `chmod 600` (user-only)
- Pattern files: `chmod 600`
- Session directory: `chmod 700`

### Dangerous Command Detection

Patterns detect destructive operations:
```python
DANGEROUS_KEYWORDS = [
    "delete", "remove", "destroy", "drop", "truncate",
    "rm -rf", "mkfs", "format", "dd if=", "fork bomb"
]
```

Warnings shown before suggestion:
```
⚠️ WARNING: Destructive operation detected!
This will delete: users, orders, payments
Suggest: 'no' (review first)
```

### No Auto-Injection (MVP)

- Detection and suggestions only
- No automatic command execution
- User maintains full control
- Future feature requires explicit confirmation design
