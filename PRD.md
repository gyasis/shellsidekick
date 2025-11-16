# Product Requirements Document (PRD)
# ShellSidekick (ssk)
## AI-Powered Terminal Session Monitor

**Version:** 1.0
**Date:** November 14, 2025
**Author:** Gyasi + Claude
**Project Codename:** SSK
**Status:** Design Phase
**Repository:** github.com/yourusername/shellsidekick

---

## Executive Summary

**ShellSidekick (ssk)** is an MCP (Model Context Protocol) server that enables AI coding assistants (Claude Code, Cursor, Aider, etc.) to monitor interactive terminal sessions in real-time, detect when user input is needed, suggest appropriate inputs, and optionally inject commands—creating a "looking over your shoulder" experience where the AI can provide contextual help during live sessions.

**Tagline:** *"Your AI pair programmer for the terminal"*

---

## Problem Statement

### Current Limitations

AI assistants cannot maintain context during interactive sessions:

- When you run `ssh user@server`, the AI loses visibility
- Interactive commands (database CLIs, setup wizards, deployment scripts) require repeated context switching
- User must copy/paste terminal output to ask for help
- No real-time guidance during long-running operations
- Cannot track what inputs were provided and whether they succeeded

### User Pain Points

1. **Context Loss**: "Claude helped me write a deployment script, but now I'm stuck at a prompt and have to explain everything again"
2. **Delayed Assistance**: "I had to wait until the command failed to get help, wasting 10 minutes"
3. **Repetitive Copying**: "Constantly copying terminal output to Claude to ask 'what do I do next?'"
4. **Missed Patterns**: "I keep making the same input mistakes because there's no memory of what worked before"

### Why Existing Solutions Fall Short

| Solution | Limitation |
|----------|-----------|
| `script` command | Captures output but no intelligence layer |
| tmux logging | Same—just raw logs |
| SSH with heredoc | Only works for pre-planned commands |
| Expect scripts | Requires knowing prompts in advance |
| Screen recording | Too heavy, not machine-readable |

---

## Solution Overview

### Core Concept

A stateful MCP server that:

1. **Monitors** terminal sessions via log tailing
2. **Detects** when interactive input is expected
3. **Analyzes** context to infer appropriate responses
4. **Tracks** input history and success/failure patterns
5. **Provides** bidirectional communication (read + write)

### Key Innovation

**Intelligence Layer on Top of Session Logging**

Not just "tail -f" with extra steps:
- Understands prompt patterns (password, yes/no, paths, commands)
- Learns from user behavior over time
- Accessible to ANY CLI tool via standard MCP protocol

### Before vs After

#### ❌ Before ShellSidekick

```bash
$ ssh deploy@production
Enter passphrase for key: █
# *switches to Claude* "What's my SSH passphrase again?"
# *copies error messages* "Why is this failing?"
# *googles for 10 minutes*
```

#### ✅ After ShellSidekick

```bash
$ ssk start ssh deploy@production
🤝 ShellSidekick is watching...

$ # You type naturally
Enter passphrase for key: █

# Claude Code (via ShellSidekick) immediately:
# 💡 Detected: Password prompt for SSH key
# 💡 Typical pattern: You use your 'production-key' passphrase
# 💡 Last successful login: 2 hours ago
```

---

## Architecture Components

### 1. Core Session Monitoring

**SessionMonitor Class**
```
SessionMonitor
├── Start monitoring (script, tmux, ssh, file, pipe)
├── Track file position and read incremental updates
├── Manage subprocess lifecycle
└── Handle bidirectional pipes for command injection
```

**Responsibilities:**
- Initialize monitoring based on session type
- Maintain file position pointer for incremental reads
- Manage log file lifecycle (creation, rotation, cleanup)
- Handle process spawning and termination
- Support multiple monitoring backends (script, tmux, file, named pipes)

**Key Features:**
- Non-blocking I/O
- Incremental content updates (only new data)
- Subprocess management with proper cleanup
- Support for bidirectional communication

### 2. Prompt Detection Engine

**PromptDetector Class**
```
PromptDetector
├── Pattern matching for common prompts
│   ├── Password prompts
│   ├── Yes/No confirmations
│   ├── Multiple choice selections
│   ├── Path/file inputs
│   └── Command prompts ($, #, >)
├── Confidence scoring
└── Context-aware detection (last N lines)
```

**Detection Categories:**

| Prompt Type | Patterns | Examples |
|-------------|----------|----------|
| **Password** | `password:`, `passphrase:`, `enter password` | SSH keys, sudo, database login |
| **Yes/No** | `(y/n)`, `[y/N]`, `continue?`, `proceed?` | Confirmations, warnings |
| **Choice** | `[1-9]`, `select.*:`, `choose.*:` | Menu selections, configuration wizards |
| **Path** | `file path:`, `directory:`, `location:` | File operations, configuration |
| **Text** | `enter \w+:`, `input:`, `name:` | General text input |
| **Command** | `$`, `#`, `>` | Shell prompts, REPL environments |

**Detection Logic:**
```python
def detect(self, recent_output: str, num_lines: int = 10) -> Dict:
    """
    Returns:
    {
        "is_waiting": bool,
        "prompt_text": str,
        "prompt_type": str,
        "confidence": float (0.0-1.0),
        "detected_pattern": str
    }
    """
```

### 3. Input Inference Engine

**InputInferenceEngine Class**
```
InputInferenceEngine
├── Analyze prompt type
├── Suggest appropriate values
├── Provide validation patterns
└── Generate examples
```

**Inference Strategy:**

```python
def infer(self, prompt_text: str, context: str, prompt_type: str) -> Dict:
    """
    Returns:
    {
        "input_type": str,
        "suggested_values": List[str],
        "explanation": str,
        "validation_pattern": Optional[str],
        "examples": List[str]
    }
    """
```

**Inference Examples:**

| Prompt Type | Suggested Values | Explanation |
|-------------|-----------------|-------------|
| Password | `["<enter your password>"]` | "Password input (hidden). Cannot suggest actual value." |
| Yes/No | `["y", "n", "yes", "no"]` | "Binary yes/no choice" |
| Choice (1-3) | `["1", "2", "3"]` | "Select from options: 1, 2, 3" |
| Path | `["./", "/tmp/", "~/"]` | "File or directory path expected" |
| Email | `["<enter email>"]` | "Email address expected" (with regex validation) |

### 4. Input History & Learning

**InputEvent Tracking**
```python
@dataclass
class InputEvent:
    timestamp: float
    file_position: int
    prompt_text: str
    input_text: str
    was_successful: bool
    input_source: str  # "user_typed", "claude_suggested", "auto_injected"
    response_time_ms: Optional[int] = None
```

**Pattern Analysis**
```
Pattern Analysis
├── Common prompts identification
├── Typical response mapping
├── Error pattern detection
└── Success rate calculation
```

**Learning Capabilities:**
- Identify frequently encountered prompts
- Map prompts to successful responses
- Detect patterns that lead to errors
- Calculate success rates for different inputs
- Build user-specific knowledge base over time

---

## MCP Tool Functions

### Complete Tool Specification

| # | Function Name | Purpose | Status |
|---|---------------|---------|--------|
| 1 | `start_session_monitor` | Begin monitoring a session | Core |
| 2 | `get_session_updates` | Fetch new content since last check | Core |
| 3 | `detect_input_prompt` | Check if waiting for input | Core |
| 4 | `infer_expected_input` | Suggest what to type | Intelligence |
| 5 | `inject_command` | Send command to session | Control |
| 6 | `track_input_event` | Record input occurrence | History |
| 7 | `get_input_history` | Retrieve past inputs | History |
| 8 | `search_session_history` | Search through logs | Utility |
| 9 | `analyze_prompt_pattern` | Learn from history | Intelligence |
| 10 | `stop_session_monitor` | End monitoring | Core |
| 11 | `list_active_monitors` | Show all active sessions | Utility |

### Detailed Tool Specifications

#### 1. start_session_monitor

**Description:** Start monitoring a terminal session or log file in real-time

**Input Schema:**
```json
{
  "session_type": {
    "type": "string",
    "enum": ["script", "tmux", "ssh", "file", "pipe"],
    "description": "Type of session to monitor"
  },
  "target": {
    "type": "string",
    "description": "Path to log file, session name, or command to run"
  },
  "monitor_id": {
    "type": "string",
    "description": "Unique ID for this monitoring session"
  },
  "buffer_size": {
    "type": "integer",
    "default": 1000,
    "description": "Number of lines to keep in memory"
  },
  "update_interval": {
    "type": "integer",
    "default": 1,
    "description": "Seconds between checks"
  },
  "filters": {
    "type": "object",
    "properties": {
      "include_patterns": {
        "type": "array",
        "items": {"type": "string"}
      },
      "exclude_patterns": {
        "type": "array",
        "items": {"type": "string"}
      },
      "highlight_errors": {
        "type": "boolean",
        "default": true
      }
    }
  }
}
```

**Returns:**
```json
{
  "monitor_id": "string",
  "log_file": "string",
  "status": "started",
  "pid": "integer"
}
```

**Example Usage:**
```python
await use_mcp_tool("shellsidekick", "start_session_monitor", {
  "session_type": "ssh",
  "target": "user@production-server",
  "monitor_id": "prod-deploy-session",
  "filters": {
    "highlight_errors": True,
    "include_patterns": ["ERROR", "WARN", "Failed"]
  }
})
```

#### 2. get_session_updates

**Description:** Get new content from monitored session since last check

**Input Schema:**
```json
{
  "monitor_id": {
    "type": "string",
    "required": true
  },
  "since_position": {
    "type": "integer",
    "description": "File position to read from (optional, uses last known)"
  },
  "max_lines": {
    "type": "integer",
    "default": 50,
    "description": "Maximum lines to return"
  }
}
```

**Returns:**
```json
{
  "content": "string",
  "position": "integer",
  "has_more": "boolean",
  "timestamp": "float"
}
```

#### 3. detect_input_prompt

**Description:** Analyze session output to detect if it's waiting for input

**Input Schema:**
```json
{
  "monitor_id": {
    "type": "string",
    "required": true
  },
  "recent_lines": {
    "type": "integer",
    "default": 10,
    "description": "How many recent lines to analyze"
  },
  "prompt_indicators": {
    "type": "array",
    "items": {"type": "string"},
    "default": [":", "?", ">", "$", "#", "Enter", "input", "password", "continue"]
  }
}
```

**Returns:**
```json
{
  "is_waiting": "boolean",
  "prompt_text": "string",
  "confidence": "float",
  "prompt_type": "enum[text, password, yes_no, choice, path, number]",
  "detected_at_position": "integer",
  "detected_pattern": "string"
}
```

#### 4. infer_expected_input

**Description:** Analyze prompt context and suggest what input is expected

**Input Schema:**
```json
{
  "monitor_id": {
    "type": "string",
    "required": true
  },
  "prompt_text": {
    "type": "string",
    "required": true
  },
  "context_lines": {
    "type": "integer",
    "default": 20,
    "description": "Lines of context before prompt"
  },
  "use_llm_inference": {
    "type": "boolean",
    "default": true,
    "description": "Use LLM to infer expected input"
  }
}
```

**Returns:**
```json
{
  "input_type": "string",
  "suggested_values": ["array of strings"],
  "explanation": "string",
  "examples": ["array of strings"],
  "validation_pattern": "regex string or null"
}
```

#### 5. inject_command

**Description:** Send command to monitored session (if supported)

**Input Schema:**
```json
{
  "monitor_id": {
    "type": "string",
    "required": true
  },
  "command": {
    "type": "string",
    "required": true
  },
  "wait_for_completion": {
    "type": "boolean",
    "default": true
  },
  "timeout": {
    "type": "integer",
    "default": 30,
    "description": "Timeout in seconds"
  }
}
```

**Returns:**
```json
{
  "success": "boolean",
  "output": "string (if wait_for_completion=true)"
}
```

#### 6. track_input_event

**Description:** Record when user provided input and what it was

**Input Schema:**
```json
{
  "monitor_id": {
    "type": "string",
    "required": true
  },
  "input_text": {
    "type": "string",
    "required": true
  },
  "prompt_text": {
    "type": "string",
    "required": true
  },
  "timestamp": {
    "type": "number",
    "required": true
  },
  "file_position": {
    "type": "integer",
    "required": true
  },
  "was_successful": {
    "type": "boolean",
    "description": "Did the input work or cause error?"
  },
  "metadata": {
    "type": "object",
    "properties": {
      "input_source": {
        "type": "string",
        "enum": ["user_typed", "claude_suggested", "auto_injected"]
      },
      "response_time_ms": {
        "type": "integer"
      },
      "next_prompt_appeared": {
        "type": "boolean"
      }
    }
  }
}
```

**Returns:**
```json
{
  "event_id": "integer",
  "recorded": "boolean"
}
```

#### 7. get_input_history

**Description:** Retrieve history of all input events in this session

**Input Schema:**
```json
{
  "monitor_id": {
    "type": "string",
    "required": true
  },
  "filter_by_type": {
    "type": "string",
    "enum": ["all", "successful", "failed", "user_typed", "claude_suggested"],
    "default": "all"
  },
  "limit": {
    "type": "integer",
    "default": 50
  }
}
```

**Returns:**
```json
{
  "inputs": [
    {
      "timestamp": "float",
      "prompt": "string",
      "input": "string",
      "successful": "boolean",
      "source": "string"
    }
  ],
  "total_count": "integer",
  "success_rate": "float"
}
```

#### 8. search_session_history

**Description:** Search through session logs for specific patterns

**Input Schema:**
```json
{
  "monitor_id": {
    "type": "string",
    "required": true
  },
  "query": {
    "type": "string",
    "required": true
  },
  "context_lines": {
    "type": "integer",
    "default": 3
  }
}
```

**Returns:**
```json
{
  "results": [
    {
      "line_number": "integer",
      "match": "string",
      "context": ["array of strings"]
    }
  ],
  "total_matches": "integer"
}
```

#### 9. analyze_prompt_pattern

**Description:** Learn from past prompts to improve future detection

**Input Schema:**
```json
{
  "monitor_id": {
    "type": "string",
    "required": true
  },
  "learn_from_history": {
    "type": "boolean",
    "default": true
  }
}
```

**Returns:**
```json
{
  "common_prompts": [
    {
      "prompt": "string",
      "count": "integer"
    }
  ],
  "typical_responses": {
    "prompt_text": ["array of successful responses"]
  },
  "error_patterns": [
    {
      "prompt": "string",
      "failed_input": "string"
    }
  ]
}
```

#### 10. stop_session_monitor

**Description:** Stop monitoring a session

**Input Schema:**
```json
{
  "monitor_id": {
    "type": "string",
    "required": true
  },
  "save_log": {
    "type": "boolean",
    "default": true
  },
  "log_path": {
    "type": "string",
    "description": "Path to save log (optional)"
  }
}
```

**Returns:**
```json
{
  "status": "stopped",
  "log_saved": "boolean",
  "log_path": "string"
}
```

#### 11. list_active_monitors

**Description:** List all currently active monitoring sessions

**Input Schema:**
```json
{}
```

**Returns:**
```json
{
  "monitors": [
    {
      "monitor_id": "string",
      "session_type": "string",
      "target": "string",
      "started_at": "float",
      "log_file": "string"
    }
  ],
  "total_count": "integer"
}
```

---

## Technical Design Decisions

### Why MCP Server?

| Reason | Benefit |
|--------|---------|
| **Universal** | Works with any MCP-compatible client (Claude Code, Cursor, custom tools) |
| **Stateful** | Maintains session context across multiple tool calls |
| **Extensible** | Easy to add new detection patterns or monitoring backends |
| **Isolated** | Doesn't pollute main AI assistant with session state management |
| **Standard Protocol** | Leverages existing MCP infrastructure |

### Why File-Based Monitoring?

| Reason | Benefit |
|--------|---------|
| **Non-invasive** | Doesn't interfere with actual terminal session |
| **Reliable** | File system is source of truth, no message loss |
| **Debuggable** | Can inspect logs manually with standard tools |
| **Platform-agnostic** | Works on any Unix-like system |
| **Simple** | No complex IPC or network protocols needed |

### Why Pattern-Based Detection?

| Reason | Benefit |
|--------|---------|
| **Fast** | No LLM inference needed for common cases (~10ms vs ~1s) |
| **Reliable** | Regex patterns are deterministic and predictable |
| **Extensible** | Easy to add custom patterns per user/tool |
| **Fallback** | Can escalate to LLM for ambiguous cases |
| **Cost-effective** | No API calls for routine prompt detection |

### Session Monitoring Backends

#### 1. Script Command (`session_type: "script"`)
```bash
script -f /tmp/session.log -c "ssh user@host"
```
**Use case:** Start new interactive session with monitoring
**Pros:** Built-in on most Unix systems
**Cons:** Adds extra process layer

#### 2. Tmux Logging (`session_type: "tmux"`)
```bash
tmux pipe-pane -t session-name -o 'cat >> /tmp/session.log'
```
**Use case:** Monitor existing tmux session
**Pros:** Natural for tmux users
**Cons:** Requires tmux

#### 3. SSH Direct (`session_type: "ssh"`)
```bash
script -f /tmp/session.log -c "ssh user@host"
```
**Use case:** Monitor SSH sessions specifically
**Pros:** Most common use case
**Cons:** Same as script

#### 4. File Watching (`session_type: "file"`)
```bash
tail -f /var/log/deploy.log
```
**Use case:** Monitor existing log files
**Pros:** No process management needed
**Cons:** Read-only, no command injection

#### 5. Named Pipe (`session_type: "pipe"`)
```bash
mkfifo /tmp/session-pipe
tail -f /tmp/session-pipe | ssh user@host | tee /tmp/session.log
```
**Use case:** Bidirectional communication
**Pros:** Can inject commands
**Cons:** More complex setup

---

## Implementation Roadmap

### Phase 1: MVP (2-3 weeks)
**Goal:** Basic monitoring and prompt detection

**Deliverables:**
- ✅ Core `SessionMonitor` class
- ✅ Basic prompt detection (5 types: password, yes/no, choice, path, command)
- ✅ MCP server scaffolding with 3 core tools
  - `start_session_monitor`
  - `get_session_updates`
  - `detect_input_prompt`
- ✅ File-based monitoring with `script` command
- ✅ Basic CLI (`ssk start`, `ssk watch`, `ssk stop`)

**Success Criteria:**
- Can monitor an SSH session
- Detects password prompts with >80% accuracy
- Claude Code can call tools successfully
- No crashes during 10-minute session

**Testing:**
```bash
# Manual test
ssk start ssh user@testserver
# In another terminal:
ssk watch <monitor-id>
# Type password when prompted
# Verify detection in Claude Code
```

### Phase 2: Intelligence Layer (3-4 weeks)
**Goal:** Add inference and history tracking

**Deliverables:**
- ✅ `InputInferenceEngine` with context analysis
- ✅ Input event tracking system with persistence
- ✅ Pattern learning from history
- ✅ Search functionality across session history
- ✅ MCP tools:
  - `infer_expected_input`
  - `track_input_event`
  - `get_input_history`
  - `search_session_history`
  - `analyze_prompt_pattern`
- ✅ CLI commands: `ssk suggest`, `ssk history`, `ssk search`

**Success Criteria:**
- Suggests correct input for 70% of common prompts
- Learns user preferences after 5 sessions
- Can recall past successful inputs
- History persists across sessions

**Testing:**
```bash
# Run same SSH session 5 times
# Verify it learns typical responses
ssk history <monitor-id> --filter successful
```

### Phase 3: Bidirectional Control (2-3 weeks)
**Goal:** Enable command injection

**Deliverables:**
- ✅ Named pipe infrastructure for bidirectional communication
- ✅ Command injection with safety guards
- ✅ Confirmation prompts before destructive commands
- ✅ `inject_command` MCP tool with `wait_for_completion`
- ✅ Error recovery mechanisms (timeout, retry)
- ✅ CLI: `ssk inject <monitor-id> "command"`

**Success Criteria:**
- Can inject commands safely (>95% success rate)
- Detects if command succeeded vs failed
- Handles command timeout gracefully
- Blocks dangerous commands (rm -rf, mkfs, etc.) without confirmation

**Safety Features:**
```python
DANGEROUS_COMMANDS = [
    'rm -rf /',
    'mkfs',
    'dd if=/dev/zero',
    ':(){:|:&};:',  # Fork bomb
]

def inject_command(cmd):
    if any(danger in cmd for danger in DANGEROUS_COMMANDS):
        return {"error": "Dangerous command blocked. Add --confirm to override"}
```

### Phase 4: Advanced Features (Ongoing)

#### 4.1 LLM-Powered Inference
**Goal:** Handle ambiguous prompts

```python
async def llm_infer(prompt_text: str, context: str) -> Dict:
    """Use Claude to analyze unclear prompts"""
    response = await claude_api.complete(
        prompt=f"Analyze this terminal prompt and suggest input:\n{prompt_text}\nContext:\n{context}"
    )
    return parse_llm_response(response)
```

#### 4.2 Multi-Session Support
**Goal:** Monitor multiple terminals simultaneously

```bash
ssk start ssh prod1 --id prod1
ssk start ssh prod2 --id prod2
ssk start file /var/log/app.log --id app-logs
ssk list
# prod1    | ssh  | user@prod1  | 00:05:32
# prod2    | ssh  | user@prod2  | 00:02:15
# app-logs | file | /var/log... | 00:10:00
```

#### 4.3 Template Library
**Goal:** Pre-built patterns for common tools

```yaml
templates:
  docker:
    prompts:
      - pattern: "Are you sure you want to remove"
        response: "y"
        description: "Docker container removal confirmation"
  kubernetes:
    prompts:
      - pattern: "Do you want to continue"
        response: "yes"
        description: "kubectl apply confirmation"
```

#### 4.4 Visual Feedback (TUI)
**Goal:** Terminal UI showing what Claude sees

```
┌─ ShellSidekick Monitor ────────────────────────┐
│ Session: ssh user@prod                         │
│ Status:  🟢 Active (00:05:32)                  │
│ Detected: Password prompt (confidence: 0.95)   │
├────────────────────────────────────────────────┤
│ Last 10 lines:                                 │
│   [15:32:01] Connecting to production...       │
│   [15:32:03] Authenticated                     │
│   [15:32:04] Welcome to production server      │
│ > [15:32:05] Enter passphrase: ▂               │
├────────────────────────────────────────────────┤
│ 💡 Suggestion: Password prompt detected        │
│    Type your SSH key passphrase                │
└────────────────────────────────────────────────┘
```

#### 4.5 Session Replay
**Goal:** Recreate past sessions for debugging

```bash
ssk replay <monitor-id> --from "15:30:00" --to "15:35:00"
# Shows timeline of prompts, inputs, and outcomes
```

#### 4.6 Community Pattern Library
**Goal:** User-contributed prompt patterns

```bash
ssk patterns install docker-prompts
ssk patterns install kubernetes-prompts
ssk patterns share my-custom-patterns
```

---

## CLI Command Structure

### Core Commands

```bash
# Start monitoring
ssk start [session-type] [target] [options]

# Get real-time updates
ssk watch <monitor-id>

# Detect current prompt
ssk detect <monitor-id>

# Get input suggestions
ssk suggest <monitor-id> "prompt text"

# Inject command (requires confirmation)
ssk inject <monitor-id> "command"

# View input history
ssk history <monitor-id> [--filter successful|failed|all]

# Search session logs
ssk search <monitor-id> "query"

# Analyze patterns
ssk patterns <monitor-id>

# Stop monitoring
ssk stop <monitor-id>

# List active sessions
ssk list

# Configure MCP integration
ssk configure --mcp
```

### Example Usage

```bash
# Example 1: Basic SSH monitoring
ssk start ssh user@production
# Output: 🤝 ShellSidekick monitoring: ssh-production-1731614400
# Log: /tmp/ssk-ssh-production-1731614400.log

# Example 2: Monitor with filters
ssk start ssh user@prod --highlight-errors --filter "ERROR|WARN|CRITICAL"

# Example 3: Monitor existing log file
ssk start file /var/log/deploy.log --auto

# Example 4: Interactive mode (Claude watches in real-time)
ssk interactive ssh user@prod

# Example 5: View what happened
ssk history ssh-prod-123 --filter successful

# Example 6: Search for errors
ssk search ssh-prod-123 "connection refused"

# Example 7: Inject command (with safety check)
ssk inject ssh-prod-123 "systemctl restart nginx"
# ⚠️  This will execute a command in the session. Continue? [y/N]
```

### Quick Start Flow

```bash
# One-time setup
pip install shellsidekick
ssk configure --mcp

# Start using
ssk start ssh deploy@production --auto
# 🤝 Monitoring started. Claude Code can now see your session.
# Just ask Claude: "What's happening in my SSH session?"
```

---

## User Workflows

### Workflow 1: SSH Troubleshooting

**Scenario:** User gets stuck at SSH passphrase prompt

```
User: ssh deploy@production
[Session hangs at "Enter passphrase:"]
```

**ShellSidekick Actions:**
1. Detects prompt via `detect_input_prompt()` (confidence: 0.95)
2. Infers password needed via `infer_expected_input()`
3. Checks history: user typically uses "production-key" passphrase
4. Claude tells user: "Looks like SSH needs your key passphrase for production-key"

**User Types:** `[passphrase]`

```
[New prompt appears: "Warning: remote host identification changed. Continue (yes/no)?"]
```

**ShellSidekick Actions:**
1. Detects yes/no prompt (confidence: 0.90)
2. Searches history via `search_session_history()` for "host identification"
3. Finds previous known_hosts issue 2 weeks ago
4. Claude suggests: "Type 'yes' to continue, or check ~/.ssh/known_hosts if suspicious. Last time this happened, you removed the old key."

**Outcome:** User resolves issue in 30 seconds instead of 5 minutes

### Workflow 2: Database Migration

**Scenario:** Dangerous migration operation

```
User: python manage.py migrate
[Output scrolling...]
```

**ShellSidekick Actions:**
1. Monitors via `get_session_updates()` every second
2. Detects: "Migration will delete data from 3 tables. Type 'yes' to continue:"

**ShellSidekick Intelligence:**
1. Analyzes context (sees "delete data", "3 tables")
2. Searches history: no previous similar operation
3. Claude alerts: "⚠️ Destructive operation detected. This will delete data from: users_old, sessions_archive, temp_cache"
4. Shows table row counts: 15,234 rows will be deleted
5. Asks: "Should I input 'yes'? Or would you like to backup first?"

**User:** "yes, but make a backup first"

**ShellSidekick Actions:**
1. `inject_command("no")` to cancel current operation
2. User runs backup script (Claude helps)
3. User re-runs `python manage.py migrate`
4. This time when prompt appears, Claude suggests: "Backup complete. Safe to proceed with 'yes'"
5. `track_input_event()` records successful migration for future reference

**Outcome:** Prevented data loss, established safe pattern

### Workflow 3: Learning from History

**Scenario:** User about to deploy, wants to remember usual steps

```
User: "I'm about to deploy to prod. What do I usually do at the prompts?"
```

**ShellSidekick Actions:**
1. `analyze_prompt_pattern("production-deploy")`
2. `get_input_history(filter="successful", limit=50)`
3. Analyzes last 10 production deployments

**Claude Response:**
```
Based on your last 10 production deploys:

✅ Database backup? → You always type 'yes' (10/10)
✅ Run migrations? → You always type 'yes' (10/10)
❌ Restart services immediately? → You always type 'no' (10/10)
   (You manually restart after verifying logs)
⏱️  Post-deploy checks? → You always type 'yes' (10/10)

Typical timeline:
1. Backup: ~2 minutes
2. Migration: ~30 seconds
3. Deploy: ~5 minutes
4. Manual service restart: ~1 minute
5. Verification: ~3 minutes

Total: ~11 minutes on average

Common issue: 3 times you had to roll back because
of environment variable mismatch. Check .env.production first!
```

**Outcome:** User has checklist, avoids common pitfall

### Workflow 4: Setup Wizard Navigation

**Scenario:** Installing complex software with interactive setup

```
User: ./install-postgresql-cluster.sh
[Wizard starts with 20+ questions]
```

**ShellSidekick Actions:**
1. Detects multiple sequential prompts
2. For each prompt:
   - Identifies type (path, yes/no, port number, etc.)
   - Suggests defaults or common values
   - Warns about irreversible choices

**Example Sequence:**
```
Prompt: "Install directory [/usr/local/pgsql]:"
Claude: "Default is fine. Previous installs used /usr/local/pgsql"

Prompt: "Port number [5432]:"
Claude: "Standard PostgreSQL port. Use default unless conflict exists"

Prompt: "Enable SSL? (yes/no):"
Claude: "⚠️ Important security setting. Recommend 'yes' for production"

Prompt: "Initialize database cluster now? (yes/no):"
Claude: "Safe to say 'yes'. Creates empty cluster, no data loss risk"
```

**Outcome:** User completes 20-minute wizard in 5 minutes with confidence

---

## MCP Server Configuration

### Installing ShellSidekick MCP Server

**Add to `~/.config/claude/mcp.json`:**

```json
{
  "mcpServers": {
    "shellsidekick": {
      "command": "ssk",
      "args": ["mcp-server"],
      "env": {
        "SSK_LOG_DIR": "/tmp/ssk-sessions",
        "SSK_HISTORY_DIR": "~/.config/shellsidekick",
        "SSK_MAX_SESSIONS": "10",
        "SSK_LOG_RETENTION_DAYS": "7"
      }
    }
  }
}
```

**Auto-configuration:**
```bash
ssk configure --mcp
# Automatically adds ShellSidekick to MCP configuration
# Detects Claude Code, Cursor, or custom MCP clients
```

### Using from Claude Code

```typescript
// Claude Code automatically uses MCP tools

// Example 1: Start monitoring
await use_mcp_tool("shellsidekick", "start_session_monitor", {
  session_type: "ssh",
  target: "user@production-server",
  monitor_id: "prod-deploy-session",
  filters: {
    highlight_errors: true,
    include_patterns: ["ERROR", "WARN", "Failed"]
  }
});

// Example 2: Check for prompts
const detection = await use_mcp_tool("shellsidekick", "detect_input_prompt", {
  monitor_id: "prod-deploy-session"
});

if (detection.is_waiting && detection.prompt_type === "password") {
  // Inform user about password prompt
  console.log(`🔐 Password prompt detected: ${detection.prompt_text}`);
}

// Example 3: Get suggestions
const inference = await use_mcp_tool("shellsidekick", "infer_expected_input", {
  monitor_id: "prod-deploy-session",
  prompt_text: detection.prompt_text
});

console.log(`💡 Suggestion: ${inference.explanation}`);
console.log(`   Try: ${inference.suggested_values.join(' or ')}`);

// Example 4: Track what user typed
await use_mcp_tool("shellsidekick", "track_input_event", {
  monitor_id: "prod-deploy-session",
  input_text: user_input,
  prompt_text: detection.prompt_text,
  timestamp: Date.now(),
  file_position: detection.detected_at_position,
  was_successful: true,
  metadata: {
    input_source: "user_typed"
  }
});
```

---

## Security Considerations

### Sensitive Data Handling

**Problem:** Logs may contain passwords, keys, tokens

**Mitigations:**
- ✅ Store logs in secure temp directory (`/tmp` with user-only permissions)
- ✅ Clear logs on session end (configurable retention)
- ✅ Never log password input text (mask as `[PASSWORD]`)
- ✅ Detect common secrets (API keys, tokens) and redact
- ✅ Optional: Encrypt logs at rest

**Implementation:**
```python
SECRET_PATTERNS = [
    r'password["\s:=]+([^\s]+)',
    r'token["\s:=]+([^\s]+)',
    r'api[_-]?key["\s:=]+([^\s]+)',
]

def sanitize_log(content: str) -> str:
    for pattern in SECRET_PATTERNS:
        content = re.sub(pattern, r'\1[REDACTED]', content, flags=re.IGNORECASE)
    return content
```

### Command Injection Safety

**Problem:** Injecting wrong commands could be destructive

**Mitigations:**
- ✅ Require explicit user permission for `inject_command` (per-command or session-level)
- ✅ Dry-run mode for testing commands without execution
- ✅ Blocklist dangerous commands (`rm -rf /`, `mkfs`, fork bombs, etc.)
- ✅ Audit log of all injected commands with timestamps
- ✅ Undo/rollback for certain operations (where possible)

**Dangerous Command Blocklist:**
```python
BLOCKED_COMMANDS = [
    'rm -rf /',
    'rm -rf /*',
    'mkfs',
    'dd if=/dev/zero',
    ':(){:|:&};:',      # Fork bomb
    'chmod -R 777 /',
    '> /dev/sda',
    'sudo rm -rf',
]

def is_dangerous(cmd: str) -> bool:
    return any(danger in cmd for danger in BLOCKED_COMMANDS)
```

**Confirmation Flow:**
```bash
$ ssk inject session-123 "rm -rf /tmp/build"
⚠️  Potentially destructive command detected: 'rm -rf'
   This will delete: /tmp/build
   Type the monitor ID to confirm: ___
```

### Access Control

**Principle:** Least privilege

**Rules:**
- ✅ MCP server runs as user, never root
- ✅ Only monitor sessions started by user (no cross-user access)
- ✅ File permissions: 0600 (user read/write only)
- ✅ No remote access without explicit SSH tunnel

**File Permissions:**
```bash
/tmp/ssk-sessions/
├── monitor_123.log           # chmod 600
├── monitor_123_input.pipe    # chmod 600
└── monitor_123_history.json  # chmod 600

~/.config/shellsidekick/
├── patterns.json             # chmod 644
└── config.yaml               # chmod 644
```

### Privacy Considerations

**User Control:**
- ✅ Opt-in for pattern sharing (never share by default)
- ✅ Clear what data is stored and where
- ✅ Easy cleanup: `ssk cleanup --all`
- ✅ No telemetry without consent

---

## Data Storage

### Log Files

```
/tmp/ssk-sessions/
├── monitor_<id>.log              # Session output
├── monitor_<id>_input.pipe       # Input pipe (if bidirectional)
└── monitor_<id>_history.json     # Input event history
```

**Retention:**
- Default: 7 days
- Configurable: `SSK_LOG_RETENTION_DAYS` environment variable
- Manual cleanup: `ssk cleanup --older-than 7d`

### Configuration

```
~/.config/shellsidekick/
├── patterns.json         # Learned prompt patterns
├── config.yaml           # User preferences
└── mcp.json             # MCP integration settings
```

**Example config.yaml:**
```yaml
monitoring:
  default_session_type: script
  default_buffer_size: 1000
  update_interval: 1

detection:
  confidence_threshold: 0.7
  prompt_indicators:
    - ":"
    - "?"
    - ">"
    - "$"
    - "#"

inference:
  use_llm: false  # Enable for ambiguous prompts
  llm_provider: anthropic
  llm_model: claude-sonnet-4.5

history:
  max_events: 1000
  retention_days: 30

security:
  require_inject_confirmation: true
  dangerous_command_blocklist:
    - "rm -rf /"
    - "mkfs"
  mask_passwords: true
  redact_secrets: true

ui:
  show_confidence: true
  highlight_errors: true
  color_scheme: auto  # auto, light, dark
```

---

## Success Metrics

### Quantitative Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Detection Accuracy** | >85% | Prompts correctly identified vs manual review |
| **Suggestion Relevance** | >70% | Suggested inputs actually used by user |
| **Time Saved** | 5 min/session | Compare session duration with/without SSK |
| **Error Reduction** | 30% fewer | Failed inputs before/after SSK |
| **Adoption Rate** | 50%+ | SSH sessions with SSK vs without |
| **Response Time** | <500ms | Time from prompt to detection |
| **False Positive Rate** | <10% | Incorrectly detected prompts |

### Qualitative Metrics

| Metric | Success Indicator |
|--------|------------------|
| **User Satisfaction** | "Feels like pair programming during deployments" |
| **Confidence** | Users more comfortable with unfamiliar CLIs |
| **Learning** | Users discover better workflows from pattern analysis |
| **Trust** | Users rely on suggestions for routine operations |
| **Reduced Anxiety** | Less fear of destructive commands |

### Beta Testing Goals

**Phase 1 (MVP):**
- 5 users testing SSH monitoring
- 20+ monitored sessions
- Collect accuracy metrics
- Gather UX feedback

**Phase 2 (Intelligence):**
- 10 users with history tracking
- 50+ sessions across multiple tools
- Measure suggestion relevance
- Validate pattern learning

**Phase 3 (Production):**
- 50+ users in real workflows
- 500+ sessions monitored
- Measure time saved
- Collect testimonials

---

## Risk Assessment & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|-----------|
| **False positive prompt detection** | Medium | Medium | Confidence scoring; user can ignore; improve patterns over time |
| **Accidentally inject wrong command** | High | Low | Confirmation required; dry-run mode; blocklist dangerous commands |
| **Password leakage in logs** | High | Medium | Mask password inputs; secure log storage with 0600 permissions; auto-redaction |
| **Performance impact on long sessions** | Medium | Low | Circular buffer; log rotation; configurable update intervals |
| **Doesn't work on Windows native** | Medium | High | Document WSL support; Windows version as Phase 5 |
| **User doesn't trust AI injecting commands** | High | Medium | Transparency (show what will be executed); explicit permission per command; audit log |
| **Log files fill disk** | Medium | Low | Automatic cleanup after retention period; configurable limits |
| **Race conditions in file monitoring** | Low | Low | File locking; atomic reads; position tracking |
| **MCP server crashes** | Medium | Low | Process supervision; auto-restart; graceful degradation |

---

## Open Questions & Future Decisions

### 1. Command Injection Trust Model

**Question:** Should command injection require per-command confirmation or session-level trust?

**Options:**
- A. Per-command confirmation (safest, but annoying)
- B. Session-level trust after first confirmation
- C. Smart trust: safe commands auto-approved, dangerous ones ask
- D. User-configurable trust levels

**Recommendation:** Option C (smart trust)
- Safe commands: `ls`, `pwd`, `git status`, `docker ps` → auto-approved
- Moderate commands: `cd`, `echo`, `cat` → auto-approved after first use
- Dangerous commands: `rm`, `sudo`, `chmod` → always ask

### 2. Graphical CLI Tools

**Question:** How to handle graphical CLI tools like k9s, htop, vim?

**Options:**
- A. Not supported (Phase 1-3)
- B. Basic support via terminal snapshots (Phase 4)
- C. Full support via terminal emulator integration (Phase 5)

**Recommendation:** Option A initially, Option C long-term
- These tools use ncurses/TUI libraries
- Need terminal emulator cooperation (like iTerm2 integration)
- Defer to Phase 5 when we have resources

### 3. Community Pattern Library

**Question:** Should patterns be shared across users/community?

**Options:**
- A. No sharing (privacy-first, every user learns independently)
- B. Opt-in sharing (contribute anonymized patterns)
- C. Public pattern marketplace (like VSCode extensions)

**Recommendation:** Option B (opt-in sharing)
```bash
ssk patterns --share my-docker-prompts
ssk patterns --install community/kubernetes-common
```

### 4. Long-Running Sessions

**Question:** How to handle sessions that run for hours/days?

**Options:**
- A. No special handling (logs grow indefinitely)
- B. Checkpoint system (save state, reload on reconnect)
- C. Log rotation with circular buffer
- D. Streaming to external storage (S3, DB)

**Recommendation:** Options B + C
- Checkpoint every hour: save position, patterns learned, input history
- Circular buffer: keep last 10,000 lines in memory
- Full logs archived: compress logs older than 1 hour

### 5. Integration with Existing Tools

**Question:** Integration with existing logging tools (ELK, Splunk, Datadog)?

**Options:**
- A. No integration (standalone)
- B. Export format (JSON logs)
- C. Webhook support (real-time forwarding)
- D. Native integrations (plugins)

**Recommendation:** Option B initially, Option C in Phase 4
```bash
ssk export session-123 --format json > events.json
ssk configure --webhook https://logs.company.com/ingest
```

---

## Dependencies

### External Dependencies

| Dependency | Purpose | Criticality |
|------------|---------|-------------|
| **MCP Protocol** | Communication with AI assistants | Critical |
| **Python 3.9+** | Implementation language | Critical |
| **Unix `script` command** | Session recording | Critical |
| **Click** | CLI framework | High |
| **asyncio** | Async I/O | High |
| **PyYAML** | Configuration | Medium |
| **pytest** | Testing | Medium |

### Optional Dependencies

| Dependency | Purpose | Phase |
|------------|---------|-------|
| **tmux** | Tmux session monitoring | Phase 1 |
| **Anthropic API** | LLM-powered inference | Phase 4 |
| **Rich** | Terminal UI/TUI | Phase 4 |
| **pyinotify** | File system events (Linux) | Phase 2 |
| **watchdog** | Cross-platform file watching | Phase 2 |

### Platform Requirements

**Supported:**
- ✅ Linux (Ubuntu, Debian, Arch, Fedora, etc.)
- ✅ macOS (10.15+)
- ✅ WSL (Windows Subsystem for Linux)

**Not Supported (Yet):**
- ❌ Windows native (PowerShell) - Phase 5
- ❌ BSD variants - Community contribution welcome

---

## Package Structure

```
shellsidekick/
├── LICENSE                        # MIT License
├── README.md                      # Main documentation
├── PRD.md                        # This document
├── pyproject.toml                 # Package configuration
├── setup.py                       # Build script
│
├── docs/
│   ├── quickstart.md              # Getting started guide
│   ├── api-reference.md           # MCP tool reference
│   ├── architecture.md            # Technical architecture
│   ├── security.md                # Security guide
│   ├── troubleshooting.md         # Common issues
│   └── examples/
│       ├── ssh-deployment.md
│       ├── database-migration.md
│       └── kubernetes-ops.md
│
├── shellsidekick/
│   ├── __init__.py                # Package init
│   ├── __main__.py                # Entry point
│   ├── cli.py                     # CLI commands
│   ├── mcp_server.py              # MCP server implementation
│   ├── monitor.py                 # SessionMonitor class
│   ├── detector.py                # PromptDetector class
│   ├── inference.py               # InputInferenceEngine class
│   ├── history.py                 # InputEvent tracking
│   ├── config.py                  # Configuration management
│   ├── security.py                # Security utilities
│   └── utils/
│       ├── file_watcher.py
│       ├── process_manager.py
│       └── log_sanitizer.py
│
├── tests/
│   ├── __init__.py
│   ├── test_monitor.py            # Monitor tests
│   ├── test_detector.py           # Detection tests
│   ├── test_inference.py          # Inference tests
│   ├── test_history.py            # History tests
│   ├── test_security.py           # Security tests
│   ├── test_integration.py        # End-to-end tests
│   └── fixtures/
│       ├── sample_ssh_session.log
│       ├── sample_prompts.txt
│       └── expected_detections.json
│
└── examples/
    ├── basic_ssh.py               # Simple SSH monitoring
    ├── database_migration.py      # Database example
    ├── kubernetes_deploy.py       # K8s deployment
    └── custom_patterns.py         # Custom detection patterns
```

---

## Installation & Distribution

### PyPI Installation (Post-Release)

```bash
# Install from PyPI
pip install shellsidekick

# Verify installation
ssk --version

# Configure for Claude Code
ssk configure --mcp
```

### Development Installation

```bash
# Clone repository
git clone https://github.com/yourusername/shellsidekick.git
cd shellsidekick

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Verify CLI works
ssk --help
```

### Homebrew (Future)

```bash
brew install shellsidekick
```

---

## Development Workflow

### Contributing Guidelines

**Code Style:**
- Python: Black formatter, Ruff linter
- Type hints: Required for public APIs
- Docstrings: Google style
- Test coverage: >80%

**Git Workflow:**
```bash
# Feature branch
git checkout -b feature/better-prompt-detection

# Make changes
# ...

# Run tests
pytest
black shellsidekick/
ruff check shellsidekick/

# Commit
git commit -m "feat: improve password prompt detection"

# Push and create PR
git push origin feature/better-prompt-detection
```

**PR Requirements:**
- ✅ Tests pass
- ✅ Code formatted (Black)
- ✅ Lints clean (Ruff)
- ✅ Type checks pass (mypy)
- ✅ Documentation updated
- ✅ Changelog entry added

---

## Performance Specifications

### Latency Targets

| Operation | Target | Acceptable | Unacceptable |
|-----------|--------|-----------|--------------|
| **Prompt detection** | <100ms | <500ms | >1s |
| **Log polling** | 1s interval | 2s interval | >5s interval |
| **Input inference** | <500ms | <2s | >5s |
| **Command injection** | <200ms | <1s | >2s |
| **History search** | <100ms | <500ms | >1s |

### Resource Limits

| Resource | Limit | Reason |
|----------|-------|--------|
| **Memory per session** | <50MB | Keep it lightweight |
| **Max concurrent sessions** | 10 | Typical user workload |
| **Log file size** | 100MB before rotation | Balance storage vs history |
| **History retention** | 30 days default | Balance utility vs storage |
| **API calls (if using LLM)** | <10 per session | Cost control |

### Scalability Targets

- **Single-user workstation:** 10 concurrent sessions, no performance degradation
- **Log processing rate:** 10,000 lines/second
- **Pattern database:** 1,000 learned patterns with <10ms lookup
- **History database:** 10,000 input events with <100ms search

---

## Testing Strategy

### Unit Tests

```python
# test_detector.py
def test_password_prompt_detection():
    detector = PromptDetector()
    output = "Enter password for user@host: "
    result = detector.detect(output)

    assert result["is_waiting"] == True
    assert result["prompt_type"] == "password"
    assert result["confidence"] > 0.8
```

### Integration Tests

```python
# test_integration.py
async def test_full_ssh_session():
    monitor = SessionMonitor("test-ssh", "ssh", "user@localhost")
    await monitor.start()

    # Wait for password prompt
    await asyncio.sleep(2)
    detection = await monitor.detect_input_prompt()
    assert detection["is_waiting"] == True

    # Simulate input
    await monitor.inject_command("test_password")

    # Verify session continues
    updates = await monitor.get_updates()
    assert len(updates["content"]) > 0

    await monitor.stop()
```

### Manual Test Cases

**Test Case 1: SSH Session**
1. Run `ssk start ssh user@testserver`
2. Verify monitoring starts
3. Type password when prompted
4. Verify detection appears in Claude Code
5. Complete session
6. Check history: `ssk history <id>`

**Test Case 2: Database Migration**
1. Run `ssk start script "python manage.py migrate"`
2. Wait for confirmation prompt
3. Verify warning appears for destructive operation
4. Type 'yes'
5. Verify migration completes
6. Check event was tracked

**Test Case 3: Pattern Learning**
1. Run same SSH session 3 times
2. Use same password each time
3. On 4th run, verify suggestion includes "You usually use..."
4. Run `ssk patterns <id>`
5. Verify learned pattern appears

---

## Roadmap Timeline

```
Q1 2025
├─ Week 1-2: Setup, Architecture, Core Monitor
├─ Week 3-4: Prompt Detection
├─ Week 5-6: MCP Integration
└─ Week 7-8: MVP Testing

Q2 2025
├─ Week 1-3: Input Inference Engine
├─ Week 4-6: History & Learning
├─ Week 7-8: Beta Testing
└─ Week 9-10: Phase 2 Release

Q3 2025
├─ Week 1-4: Bidirectional Communication
├─ Week 5-6: Safety Features
├─ Week 7-8: Beta Testing
└─ Week 9-10: Phase 3 Release

Q4 2025
├─ LLM Inference (optional)
├─ Multi-session Support
├─ Template Library
└─ Community Launch
```

---

## Appendix

### A. Related Work & Inspiration

| Project | Relation | Difference |
|---------|----------|-----------|
| **asciinema** | Session recording | We add intelligence layer |
| **tmux logging** | Log capture | We analyze logs in real-time |
| **Warp terminal AI** | AI in terminal | Closed source, terminal-specific |
| **GitHub Copilot CLI** | Command suggestions | We focus on interactive sessions |
| **expect** | Automation | We provide AI assistance, not scripts |

### B. Technical References

- **MCP Protocol:** https://docs.anthropic.com/mcp
- **Python `subprocess`:** https://docs.python.org/3/library/subprocess.html
- **Unix `script` command:** `man script`
- **tmux logging:** https://tmuxguide.readthedocs.io/
- **Click CLI framework:** https://click.palletsprojects.com/

### C. Glossary

| Term | Definition |
|------|-----------|
| **MCP** | Model Context Protocol - Standard for AI assistant communication |
| **Session** | An interactive terminal session (SSH, script, etc.) |
| **Monitor** | An active monitoring instance tracking a session |
| **Prompt** | Terminal output requesting user input |
| **Detection** | Process of identifying prompts in output |
| **Inference** | Process of suggesting appropriate input |
| **Event** | A recorded input occurrence with metadata |
| **Pattern** | A learned prompt-response pair |

---

## Document Status

**Status:** ✅ Ready for Development
**Last Updated:** November 14, 2025
**Review Cycle:** Weekly during Phase 1
**Feedback Channel:** GitHub Issues or Email

**Approval Sign-off:**
- [ ] Technical Architecture Reviewed
- [ ] Security Review Completed
- [ ] UX Review Completed
- [ ] Resource Allocation Approved

---

*ShellSidekick PRD v1.0 - Your AI pair programmer for the terminal*
