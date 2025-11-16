# ShellSidekick Quick Start Guide

**Get up and running with AI-powered terminal session monitoring in 5 minutes!**

---

## Prerequisites

- Python 3.11+
- `uv` package manager
- Claude Code CLI or Claude Desktop
- Access to a terminal (SSH, script command, or any shell)

---

## Step 1: Install ShellSidekick MCP Server

```bash
# Clone the repository (if not already done)
cd /home/gyasis/Documents/code/shellsidekick

# Install dependencies
uv sync

# Generate and install MCP configuration
uv run fastmcp install src/shellsidekick/mcp/server.py
```

This command will create an MCP server configuration in your Claude settings directory.

**Expected output**:
```
✓ ShellSidekick MCP server installed successfully
  Configuration written to: ~/.config/claude-code/mcp_settings.json
```

---

## Step 2: Start a Terminal Session with Logging

ShellSidekick needs to monitor a log file of your terminal session. Here are three ways to create one:

### Option A: Using `script` command (recommended for SSH)

```bash
# Start a new shell session with logging
script -f /tmp/my-ssh-session.log
```

All terminal output will now be logged to `/tmp/my-ssh-session.log`.

**To stop logging**: Type `exit` or press `Ctrl+D`

### Option B: Using `tmux` (recommended for long sessions)

```bash
# Start tmux and enable logging
tmux new -s my-session
# Inside tmux, press: Ctrl+B then type: :pipe-pane -o 'cat >> /tmp/tmux-session.log'
```

### Option C: Manual log file (for testing)

```bash
# Create a test log file with some content
echo "Starting application..." > /tmp/test-session.log
echo "Password: " >> /tmp/test-session.log
sleep 1
echo "Connected successfully" >> /tmp/test-session.log
```

---

## Step 3: Use ShellSidekick from Claude Code

Now that you have a log file, you can ask Claude to monitor it!

### Example 1: Start Monitoring a Session

**Ask Claude**:
```
I'm running an SSH session in /tmp/my-ssh-session.log.
Can you start monitoring it for me?
```

**Claude will call** `start_session_monitor`:
```python
{
  "session_id": "ssh-prod-001",
  "session_type": "ssh",
  "log_file": "/tmp/my-ssh-session.log",
  "metadata": {
    "host": "production-server",
    "user": "admin"
  }
}
```

**You'll get back**:
```json
{
  "session_id": "ssh-prod-001",
  "status": "active",
  "file_position": 0,
  "start_time": "2025-01-15T10:30:00",
  "log_file": "/tmp/my-ssh-session.log"
}
```

---

### Example 2: Check for Prompts Waiting for Input

**Ask Claude**:
```
Is my SSH session (ssh-prod-001) waiting for input?
```

**Claude will call** `detect_input_prompt`:
```python
{
  "session_id": "ssh-prod-001",
  "min_confidence": 0.70
}
```

**If a prompt is detected**:
```json
{
  "detected": true,
  "prompt": {
    "prompt_text": "Password:",
    "confidence": 0.95,
    "prompt_type": "password",
    "matched_pattern": "(?i)password\\s*:?\\s*$",
    "is_dangerous": false
  }
}
```

---

### Example 3: Get AI Suggestions for What to Type

**Ask Claude**:
```
What should I type for this prompt: "Restart service? (yes/no)"
```

**Claude will call** `infer_expected_input`:
```python
{
  "prompt_text": "Restart service? (yes/no)",
  "prompt_type": "yes_no",
  "session_context": {
    "environment": "production"
  }
}
```

**Claude provides smart suggestions**:
```json
{
  "suggestions": [
    {
      "input_text": "yes",
      "confidence": 0.90,
      "source": "pattern_learning",
      "reasoning": "You've chosen 'yes' 15/20 times for similar prompts (93% success)"
    },
    {
      "input_text": "no",
      "confidence": 0.45,
      "source": "default",
      "reasoning": "Standard 'no' option for confirmation prompts"
    }
  ],
  "warnings": []
}
```

---

### Example 4: Track What You Typed (For Learning)

After you type something, tell Claude to learn from it:

**Ask Claude**:
```
I typed "yes" for the "Restart service?" prompt and it worked.
Can you learn from this?
```

**Claude will call** `track_input_event`:
```python
{
  "session_id": "ssh-prod-001",
  "prompt_text": "Restart service? (yes/no)",
  "input_text": "yes",
  "success": true,
  "input_source": "user_typed",
  "response_time_ms": 2500
}
```

**Result**:
```json
{
  "event_id": "event-abc-123",
  "recorded": true,
  "pattern_updated": true
}
```

*Now Claude will remember this pattern and suggest "yes" with higher confidence next time!*

---

### Example 5: Search Session History for Errors

**Ask Claude**:
```
Search my SSH session for any ERROR messages
```

**Claude will call** `search_session_history`:
```python
{
  "session_id": "ssh-prod-001",
  "query": "ERROR",
  "context_lines": 3,
  "max_results": 10
}
```

**You'll get matches with context**:
```json
{
  "matches": [
    {
      "session_id": "ssh-prod-001",
      "matched_text": "ERROR: Connection refused",
      "line_number": 42,
      "context_before": [
        "Connecting to database...",
        "Retrying connection (attempt 1/3)",
        "Retrying connection (attempt 2/3)"
      ],
      "context_after": [
        "Failed to establish database connection",
        "Check network settings",
        "Exiting application"
      ]
    }
  ],
  "total_matches": 1,
  "searched_sessions": ["ssh-prod-001"]
}
```

---

### Example 6: Clean Up Old Session Data

**Ask Claude**:
```
Clean up any session logs older than 7 days (dry run first)
```

**Claude will call** `cleanup_old_sessions`:
```python
{
  "retention_days": 7,
  "dry_run": true
}
```

**Preview what would be deleted**:
```json
{
  "deleted_sessions": [
    "old-session-abc.log",
    "old-session-def.log"
  ],
  "total_deleted": 2,
  "bytes_freed": 15360,
  "dry_run": true
}
```

Then confirm:
```
Looks good, run it for real this time
```

---

## All 9 MCP Tools

| # | Tool | Purpose |
|---|------|---------|
| 1 | `start_session_monitor` | Start monitoring a terminal session |
| 2 | `get_session_updates` | Get new content since last check |
| 3 | `stop_session_monitor` | Stop monitoring and cleanup |
| 4 | `detect_input_prompt` | Detect if terminal is waiting for input |
| 5 | `infer_expected_input` | Get AI suggestions for what to type |
| 6 | `track_input_event` | Record what you typed (for learning) |
| 7 | `get_learned_patterns` | See what patterns Claude has learned |
| 8 | `search_session_history` | Search logs for patterns/errors |
| 9 | `cleanup_old_sessions` | Clean up old session data |

---

## Real-World Use Cases

### Use Case 1: Database Migration Script

```bash
# Start monitoring
script -f /tmp/db-migration.log

# Run your migration
./migrate-database.sh

# Ask Claude to help
```

**Say to Claude**:
```
I'm running a database migration in /tmp/db-migration.log.
Monitor it and let me know if:
1. It's waiting for confirmation
2. Any errors occur
3. The migration completes successfully
```

Claude will:
- Detect the "Proceed with migration? (yes/no)" prompt
- Suggest "yes" (if you've done this before)
- Alert you if "ERROR" appears in the logs
- Confirm when it sees "Migration complete!"

---

### Use Case 2: SSH Session to Production Server

```bash
# Start SSH with logging
script -f /tmp/prod-ssh.log
ssh admin@prod-server.example.com
```

**Say to Claude**:
```
I'm SSH'd into production (log: /tmp/prod-ssh.log).
Help me navigate this session safely.
```

Claude will:
- Detect password prompts and mark them as `[REDACTED]`
- Warn you about dangerous commands (rm -rf, etc.)
- Learn your common commands and suggest them
- Search for error patterns if something goes wrong

---

### Use Case 3: Debugging a Flaky Script

```bash
# Run script with logging
script -f /tmp/flaky-script.log
./flaky-test-runner.sh
```

**Say to Claude**:
```
Search /tmp/flaky-script.log for all WARNING or ERROR messages
and show me the context around each one.
```

Claude shows you all errors with 3 lines of context before/after, making debugging much faster!

---

## Troubleshooting

### MCP Server Not Found

If Claude says "Tool not found":

1. Verify installation:
   ```bash
   uv run fastmcp install src/shellsidekick/mcp/server.py
   ```

2. Restart Claude Code/Desktop

3. Check MCP settings file:
   ```bash
   cat ~/.config/claude-code/mcp_settings.json
   ```

### Session Not Updating

If `get_session_updates` returns empty content:

- Make sure the log file is being written to (`tail -f /tmp/your-session.log`)
- Check file permissions (must be readable by the MCP server)
- Verify the session is still active (`ps aux | grep script`)

### Pattern Learning Not Working

If suggestions don't improve over time:

- Make sure you're calling `track_input_event` after each input
- Check learned patterns: Ask Claude "Show me all learned patterns"
- Patterns require 5+ occurrences before they significantly affect suggestions

---

## Next Steps

- **Phase 7 (Polish)**: Run formatters, add unit tests, improve documentation
- **Integration Tests**: Test full workflows (SSH session lifecycle, pattern learning)
- **Performance Validation**: Verify <500ms detection latency
- **Security Audit**: Password redaction, dangerous command detection

---

## Support

- **GitHub Issues**: https://github.com/gyasis/shellsidekick/issues
- **Documentation**: See `specs/001-mcp-session-monitor/` for detailed specs
- **Memory Bank**: See `memory-bank/` for project context and history

---

**Happy Terminal Monitoring! 🚀**
