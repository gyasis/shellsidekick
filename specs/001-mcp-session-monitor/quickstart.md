# Quick Start: MCP Session Monitor

**Feature**: `001-mcp-session-monitor`
**Status**: Phase 1 Complete - Ready for Implementation
**Last Updated**: 2025-11-14

## Overview

This guide walks you through setting up the ShellSidekick MCP Session Monitor development environment and running your first tests.

## Prerequisites

- Python 3.11 or later
- [uv](https://github.com/astral-sh/uv) package manager
- Unix-like system (Linux, macOS, or WSL)
- `script` command (standard on most Unix systems)

## Project Setup

### 1. Initialize Project with uv

```bash
# Navigate to project root
cd /home/gyasis/Documents/code/shellsidekick

# Initialize uv project (if not already done)
uv init

# Add FastMCP framework
uv add fastmcp

# Add development dependencies
uv add --dev pytest pytest-asyncio black ruff
```

### 2. Verify Installation

```bash
# Check uv environment
uv run python --version  # Should show Python 3.11+

# Verify FastMCP installation
uv run python -c "import fastmcp; print(fastmcp.__version__)"
```

## Project Structure

The project follows the structure defined in `plan.md`:

```
shellsidekick/
├── src/shellsidekick/
│   ├── __init__.py
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── server.py           # FastMCP server entry point
│   │   ├── tools/               # MCP tool implementations
│   │   │   ├── __init__.py
│   │   │   ├── session.py       # start_session_monitor, etc.
│   │   │   ├── detection.py     # detect_input_prompt, etc.
│   │   │   └── history.py       # search_session_history, etc.
│   │   └── schemas/
│   │       └── tools.json       # JSON schemas for MCP tools
│   ├── core/
│   │   ├── __init__.py
│   │   ├── monitor.py           # SessionMonitor class
│   │   ├── detector.py          # PromptDetector with regex patterns
│   │   ├── patterns.py          # Pattern learning logic
│   │   └── storage.py           # File I/O and JSON persistence
│   ├── models/
│   │   ├── __init__.py
│   │   ├── session.py           # Session dataclass
│   │   ├── prompt.py            # PromptDetection dataclass
│   │   ├── input_event.py       # InputEvent dataclass
│   │   └── pattern.py           # Pattern dataclass
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py        # File position tracking
│       ├── security.py          # Dangerous command detection
│       └── logging.py           # Structured logging
├── tests/
│   ├── contract/                # Contract tests (from Phase 1)
│   ├── integration/             # End-to-end tests
│   └── unit/                    # Unit tests
├── pyproject.toml               # uv configuration
└── README.md
```

## Development Workflow (TDD)

Following the constitution's Test-First Development principle:

### Step 1: Write Tests FIRST

**Example**: Implementing `start_session_monitor` tool

```bash
# Create test file first
touch tests/contract/test_session_tools.py
```

**tests/contract/test_session_tools.py**:
```python
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

@pytest.fixture
async def mcp_client():
    """Create FastMCP client for testing."""
    from shellsidekick.mcp.server import mcp
    async with Client(mcp) as client:
        yield client

async def test_start_session_monitor_success(mcp_client):
    """Test successful session start."""
    result = await mcp_client.call_tool("start_session_monitor", {
        "session_id": "test-session-123",
        "session_type": "file",
        "log_file": "/tmp/test.log"
    })

    assert result.data["session_id"] == "test-session-123"
    assert result.data["status"] == "active"
    assert result.data["file_position"] == 0

async def test_start_session_duplicate_error(mcp_client):
    """Test error when starting duplicate session."""
    # Start first session
    await mcp_client.call_tool("start_session_monitor", {
        "session_id": "duplicate-test",
        "session_type": "file",
        "log_file": "/tmp/test.log"
    })

    # Try to start again with same ID
    with pytest.raises(ToolError) as exc:
        await mcp_client.call_tool("start_session_monitor", {
            "session_id": "duplicate-test",
            "session_type": "file",
            "log_file": "/tmp/test.log"
        })

    assert exc.value.code == "SESSION_ALREADY_EXISTS"
```

### Step 2: Run Tests (Should FAIL - Red)

```bash
uv run pytest tests/contract/test_session_tools.py -v

# Expected output: FAILED (tools not implemented yet)
```

### Step 3: Implement Minimal Code (Green)

**src/shellsidekick/mcp/server.py**:
```python
from fastmcp import FastMCP

mcp = FastMCP(
    name="ShellSidekick",
    on_duplicate_tools="error"
)

# Import tool modules (will be created next)
from shellsidekick.mcp.tools import session, detection, history

if __name__ == "__main__":
    mcp.run()
```

**src/shellsidekick/mcp/tools/session.py**:
```python
from datetime import datetime
from fastmcp.exceptions import ToolError
from shellsidekick.mcp.server import mcp
from shellsidekick.models.session import Session, SessionType, SessionState

# In-memory session storage
active_sessions: dict[str, Session] = {}

@mcp.tool
def start_session_monitor(
    session_id: str,
    session_type: str,
    log_file: str,
    metadata: dict[str, str] | None = None
) -> dict:
    """Start monitoring a terminal session.

    Args:
        session_id: Unique identifier for the session
        session_type: Type of session (ssh, script, file)
        log_file: Path to the session output log file
        metadata: Optional session metadata

    Returns:
        Session status with monitor_id and file_position
    """
    # Check for duplicate
    if session_id in active_sessions:
        raise ToolError(
            f"Session {session_id} already exists",
            code="SESSION_ALREADY_EXISTS"
        )

    # Validate file exists
    import os
    if not os.path.exists(log_file):
        raise ToolError(
            f"Log file not found: {log_file}",
            code="FILE_NOT_FOUND"
        )

    # Create session
    session = Session(
        session_id=session_id,
        session_type=SessionType(session_type),
        log_file=log_file,
        file_position=0,
        start_time=datetime.now(),
        state=SessionState.ACTIVE,
        metadata=metadata
    )

    active_sessions[session_id] = session

    return session.to_dict()
```

### Step 4: Run Tests Again (Should PASS - Green)

```bash
uv run pytest tests/contract/test_session_tools.py -v

# Expected output: PASSED
```

### Step 5: Refactor (If Needed)

Improve code quality while keeping tests green.

## Running the MCP Server

### Development Mode (Auto-reload)

```bash
# Run with FastMCP dev server
uv run fastmcp dev src/shellsidekick/mcp/server.py
```

### Production Mode

```bash
# Run as standalone server
uv run python src/shellsidekick/mcp/server.py
```

### Generate MCP Configuration

```bash
# Generate claude_desktop_config.json entry
uv run fastmcp install src/shellsidekick/mcp/server.py

# Output:
# {
#   "shellsidekick": {
#     "command": "uv",
#     "args": ["run", "python", "src/shellsidekick/mcp/server.py"]
#   }
# }
```

## Testing the MCP Server

### Using FastMCP Client (Python)

```python
import asyncio
from fastmcp import Client

async def test_server():
    config = {
        "mcpServers": {
            "shellsidekick": {
                "command": "uv",
                "args": ["run", "python", "src/shellsidekick/mcp/server.py"]
            }
        }
    }

    async with Client(config) as client:
        # List available tools
        tools = await client.list_tools()
        print("Available tools:", [t.name for t in tools])

        # Start a session
        result = await client.call_tool("start_session_monitor", {
            "session_id": "demo-session",
            "session_type": "file",
            "log_file": "/tmp/demo.log"
        })
        print("Session started:", result.data)

asyncio.run(test_server())
```

### Using Claude Desktop

1. Add ShellSidekick to Claude Desktop config:

**~/.config/claude/claude_desktop_config.json** (Linux/macOS):
```json
{
  "mcpServers": {
    "shellsidekick": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "/home/gyasis/Documents/code/shellsidekick/src/shellsidekick/mcp/server.py"
      ]
    }
  }
}
```

2. Restart Claude Desktop

3. Test in conversation:
```
User: Start monitoring my SSH session at /tmp/ssh-session.log
Claude: [Uses start_session_monitor tool]
```

## Running Tests

### Run All Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/shellsidekick --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run Specific Test Categories

```bash
# Contract tests only
uv run pytest tests/contract/

# Integration tests only
uv run pytest tests/integration/

# Unit tests only
uv run pytest tests/unit/

# Specific test file
uv run pytest tests/contract/test_session_tools.py -v
```

### Run Tests with FastMCP Dev Server

```bash
# Watch mode (auto-reload on file changes)
uv run fastmcp dev src/shellsidekick/mcp/server.py --reload
```

## Code Quality Tools

### Formatting (Black)

```bash
# Format all code
uv run black src/ tests/

# Check formatting without changes
uv run black --check src/ tests/
```

### Linting (Ruff)

```bash
# Lint all code
uv run ruff check src/ tests/

# Auto-fix issues
uv run ruff check --fix src/ tests/
```

### Pre-commit Workflow

Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
uv run black --check src/ tests/ || exit 1
uv run ruff check src/ tests/ || exit 1
uv run pytest tests/contract/ || exit 1
```

## Debugging Tips

### Enable Debug Logging

**src/shellsidekick/utils/logging.py**:
```python
import logging

def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

# In server.py
from shellsidekick.utils.logging import setup_logging
setup_logging("DEBUG")  # Enable debug logs
```

### Test with Real SSH Session

```bash
# Start recording SSH session
script -f /tmp/ssh-test.log
ssh user@server

# In another terminal, test detection
uv run python -c "
from shellsidekick.mcp.tools.session import start_session_monitor
from shellsidekick.mcp.tools.detection import detect_input_prompt

# Start monitoring
start_session_monitor('ssh-test', 'ssh', '/tmp/ssh-test.log')

# Detect prompts
result = detect_input_prompt('ssh-test')
print(result)
"
```

## Next Steps

1. **Phase 2: Task Generation**
   - Run `/speckit.tasks` to generate ordered task list
   - Begin implementation following TDD workflow

2. **Phase 3: Implementation**
   - Implement tools one by one (following priority order)
   - P1 tools first: session management, prompt detection
   - P2 tools: pattern learning, suggestions
   - P3 tools: history search
   - P4 tools: cleanup utilities

3. **Integration Testing**
   - Test with real SSH sessions
   - Test with interactive scripts (e.g., database migrations)
   - Test pattern learning over multiple sessions

4. **Documentation**
   - Update README.md with usage examples
   - Document MCP tool reference
   - Create video demo

## Troubleshooting

### "Module not found" errors

```bash
# Ensure uv environment is activated
uv sync

# Verify package installation
uv pip list | grep fastmcp
```

### FastMCP server not responding

```bash
# Check server logs
uv run python src/shellsidekick/mcp/server.py --verbose

# Verify port not in use
lsof -i :8000  # If using HTTP transport
```

### Tests failing with "Session already exists"

```bash
# Clean up test sessions between runs
rm -rf /tmp/ssk-sessions/*

# Or use pytest fixtures with cleanup
@pytest.fixture(autouse=True)
def cleanup_sessions():
    yield
    active_sessions.clear()
```

## Resources

- [FastMCP Documentation](https://gofastmcp.com)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [uv Documentation](https://github.com/astral-sh/uv)
- [Project Constitution](.specify/memory/constitution.md)
- [Feature Spec](./spec.md)
- [Technical Research](./research.md)
- [Data Model](./data-model.md)

---

**Quick Start Complete**: Development environment ready for test-first implementation.
