# ShellSidekick Product Context

## Why This Project Exists

### The Problem

When developers run interactive terminal sessions (SSH deployments, database migrations, system administration), AI assistants lose context because:

1. **Terminal sessions are opaque**: AI can't see what's happening in an active terminal
2. **Prompts require immediate response**: Users must context-switch to answer prompts (passwords, confirmations, paths)
3. **Dangerous operations go unnoticed**: No warnings before destructive commands like "Delete production database? (yes/no)"
4. **Patterns repeat but aren't learned**: Users answer the same prompts the same way every time, manually
5. **History is scattered**: Session logs are hard to search when debugging issues

### The Solution

ShellSidekick acts as an "AI pair programmer" that:

- **Monitors sessions in real-time**: Watches terminal output without interfering
- **Detects prompts intelligently**: Uses regex patterns to identify 7 prompt types (password, yes/no, choice, path, text, command, unknown)
- **Warns about dangers**: Flags destructive operations like "rm -rf" or "DROP TABLE"
- **Learns patterns**: Tracks user responses and suggests based on past behavior
- **Enables AI assistance**: Exposes monitoring capabilities via MCP tools for AI assistants

## Problems Solved

### For DevOps Engineers

**Before**: Deploying to production requires constant attention to prompts, easy to miss warnings, no record of what was confirmed
**After**: AI monitors deployment, warns about dangerous steps, suggests typical responses, logs all decisions

### For Database Administrators

**Before**: Migration scripts prompt for confirmations, no warning if about to delete production data, hard to recall what was executed
**After**: AI detects migration prompts, warns about destructive operations, learns typical migration patterns, searchable history

### For System Administrators

**Before**: SSH sessions require manual password entry, prompts interrupt workflow, no assistance with unfamiliar tools
**After**: AI detects SSH prompts, suggests appropriate responses, learns server-specific patterns, provides context-aware help

## What Makes This Different

### vs Traditional Logging

- **Real-time detection**: Not just recording, but actively analyzing for prompts
- **Pattern learning**: Builds intelligence over time, not just passive storage
- **AI integration**: Designed for AI assistants via MCP, not just human review

### vs Command History

- **Context preservation**: Captures full session output, not just commands
- **Prompt detection**: Identifies when terminal is waiting for input
- **Searchable**: Find patterns and errors across all sessions

### vs Terminal Multiplexers

- **Intelligence layer**: Not just session management, but AI-powered analysis
- **Pattern recognition**: Learns from behavior, suggests appropriate inputs
- **Safety warnings**: Actively protects against dangerous operations

## User Journey

### 1. Start Monitoring

User begins SSH session or interactive script:
```bash
# AI assistant starts monitoring
start_session_monitor(session_id="deploy-123", session_type="ssh", log_file="/tmp/deploy.log")
```

### 2. Detect Prompts

Terminal asks for input, AI detects immediately:
```
Password: _
```
AI response: "Detected PASSWORD prompt (confidence: 0.95) - input will be redacted from logs"

### 3. Context-Aware Suggestions

Terminal shows dangerous operation:
```
Delete 3 production tables? (yes/no)
```
AI response: "WARNING: Destructive operation detected! This will delete: users, orders, payments. Suggest: 'no' (review first)"

### 4. Pattern Learning

After 5 deployments, AI learns:
```
Restart services immediately? (yes/no)
```
AI response: "Pattern learned: You always answer 'no' (5/5 times, 100% success). Suggestion: 'no'"

### 5. History Search

Debugging production issue:
```
search_session_history(query="connection refused", context_lines=3)
```
AI finds all connection errors with surrounding context for root cause analysis

## Key Insights Driving Design

### 1. Speed Matters

**Insight**: Users expect instant feedback during interactive sessions. Slow detection breaks the flow.
**Design Decision**: Pattern-based regex detection (<100ms) instead of LLM inference. Performance target: <500ms end-to-end.

### 2. Privacy is Critical

**Insight**: Terminal sessions contain sensitive data (passwords, keys, confidential commands).
**Design Decision**: All storage local, password redaction, secure file permissions (chmod 600), 7-day auto-cleanup, no telemetry.

### 3. Safety First

**Insight**: Wrong command injection can destroy systems. Users must maintain control.
**Design Decision**: Detection-only in MVP (no auto-injection), dangerous operation warnings, explicit confirmation required for future injection features.

### 4. Simplicity Wins

**Insight**: Complex IPC and network protocols delay MVP and increase bug surface.
**Design Decision**: File-based monitoring via `script`/`tmux`, regex patterns (no ML in MVP), JSON storage (no distributed database).

### 5. Test-First Required

**Insight**: Prompt detection and command suggestions are safety-critical. Bugs lead to data loss or security breaches.
**Design Decision**: TDD enforced by project constitution, >80% test coverage, contract tests before implementation.

## Market Positioning

**Target Niche**: Developers and operators who work in terminal sessions and want AI assistance without cloud dependency

**Not For**:
- Users who only use GUIs
- Teams requiring cloud-based collaboration features
- Windows PowerShell environments (WSL only)

**Unique Position**: Privacy-first AI terminal assistant with pattern learning, running entirely local via MCP
