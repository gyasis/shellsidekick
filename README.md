# ShellSidekick

**AI-powered terminal session monitoring via MCP**

ShellSidekick is a Model Context Protocol (MCP) server that enables AI assistants to monitor terminal sessions in real-time, detect prompts waiting for input, and provide intelligent suggestions.

## 🎯 Status: Phase 5 Complete (Pattern Learning)

✅ **Real-time session monitoring** - Monitor SSH sessions and terminal output
✅ **Intelligent prompt detection** - Detect passwords, confirmations, file paths
✅ **Context-aware suggestions** - Suggest appropriate inputs with safety warnings
✅ **Pattern learning** - Learn from user behavior, improve suggestions over time
✅ **Persistent storage** - Patterns survive server restarts
✅ **Fast detection** - <500ms latency, >10k lines/second throughput
✅ **Secure by default** - Password redaction, dangerous command detection

## Features

### Implemented

- **Session Monitoring**: Monitor SSH, scripts, and terminal logs in real-time
- **Prompt Detection**: Automatically detect 7 prompt types (password, yes/no, choice, path, text, command, unknown)
- **Smart Suggestions**: Context-aware input suggestions with danger warnings
- **Pattern Learning**: Learn from user behavior to improve suggestions over time
- **Persistent Patterns**: Patterns saved to JSON, survive server restarts
- **High Performance**: <500ms detection latency, process >10,000 lines/second
- **Security**: Password redaction, dangerous operation detection, secure file permissions
- **MCP Integration**: 7 MCP tools for session management, detection, suggestions, and pattern learning

## Quick Start

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest -v

# Start MCP server
uv run python src/shellsidekick/mcp/server.py
```

## MCP Tools

### Session Management
1. **`start_session_monitor`** - Start monitoring a terminal session
2. **`get_session_updates`** - Get new content since last check
3. **`stop_session_monitor`** - Stop monitoring and cleanup

### Detection & Suggestions
4. **`detect_input_prompt`** - Detect if terminal is waiting for input
5. **`infer_expected_input`** - Suggest appropriate inputs (with pattern learning)

### Pattern Learning
6. **`track_input_event`** - Record user input to learn patterns
7. **`get_learned_patterns`** - Retrieve learned patterns with filtering

## Documentation

- **Full README**: See project documentation
- **Specification**: `specs/001-mcp-session-monitor/spec.md`
- **Implementation Plan**: `specs/001-mcp-session-monitor/plan.md`
- **Quick Start Guide**: `specs/001-mcp-session-monitor/quickstart.md`

## Development

```bash
# Run tests with coverage
uv run pytest --cov=src/shellsidekick

# Format code
uv run black src/ tests/

# Lint
uv run ruff check --fix src/ tests/
```

## License

MIT
