# Feature Specification: MCP Session Monitor

**Feature Branch**: `001-mcp-session-monitor`
**Created**: 2025-11-14
**Status**: Draft
**Input**: User description: "/home/gyasis/Documents/code/shellsidekick/PRD.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - AI Monitors SSH Session for Prompts (Priority: P1)

A developer runs an SSH session to deploy code to production. The AI assistant watches the session in real-time, detects when the terminal is waiting for input (password, confirmation, path), and alerts the developer with context-aware suggestions about what to enter.

**Why this priority**: This is the core value proposition - enabling AI to maintain context during interactive sessions. Without this, the project has no purpose.

**Independent Test**: Can be fully tested by starting an SSH session, reaching a password prompt, and verifying the AI assistant detects the prompt and suggests appropriate input within 500ms.

**Acceptance Scenarios**:

1. **Given** a developer starts monitoring an SSH session, **When** the SSH server prompts for a password, **Then** the AI assistant detects the password prompt within 500ms and notifies the developer
2. **Given** the terminal shows "Continue? (yes/no)", **When** the AI analyzes the output, **Then** it identifies this as a yes/no confirmation prompt and suggests valid responses
3. **Given** multiple prompts appear in sequence, **When** each prompt is detected, **Then** the AI tracks the detection history and can recall previous prompts

---

### User Story 2 - AI Suggests Inputs Based on Context (Priority: P2)

During an interactive database migration, the terminal prompts "Delete 3 tables? (yes/no)". The AI assistant analyzes the surrounding context, identifies this as a destructive operation, shows which tables will be affected, and warns the developer before they type "yes".

**Why this priority**: Intelligence layer adds significant value beyond basic detection. Prevents costly mistakes and builds user trust.

**Independent Test**: Can be tested by running a migration script that prompts for destructive operations and verifying the AI provides contextual warnings and explanations.

**Acceptance Scenarios**:

1. **Given** a prompt contains keywords like "delete", "remove", or "destroy", **When** the AI analyzes the prompt, **Then** it flags the operation as potentially dangerous and suggests caution
2. **Given** a prompt asks for a file path, **When** the AI infers the expected input type, **Then** it suggests common path patterns (e.g., "./", "/tmp/", "~/")
3. **Given** the prompt history shows the user previously entered "production-key" for SSH passphrases, **When** a similar passphrase prompt appears, **Then** the AI suggests using the same credential

---

### User Story 3 - AI Learns from Input History (Priority: P3)

A developer has deployed to production 10 times. Each time, when prompted "Restart services immediately?", they answer "no" because they prefer to restart manually after checking logs. On the 11th deployment, when the same prompt appears, the AI reminds them: "You always answer 'no' to this (10/10 times)".

**Why this priority**: Pattern learning creates a personalized experience and reduces cognitive load during routine operations.

**Independent Test**: Can be tested by simulating the same prompt 5 times with consistent user responses, then verifying the AI suggests the pattern on the 6th occurrence.

**Acceptance Scenarios**:

1. **Given** the user has responded to the same prompt 3+ times, **When** that prompt appears again, **Then** the AI shows the user's typical response and success rate
2. **Given** a prompt led to an error in the past, **When** the same prompt appears, **Then** the AI warns about the previous failure
3. **Given** a deployment workflow has a typical timeline, **When** the user starts a deployment, **Then** the AI shows expected duration based on previous sessions

---

### User Story 4 - AI Provides Session History Search (Priority: P4)

During a debugging session, a developer remembers seeing a "connection refused" error earlier but can't recall the exact message. They ask the AI to search the session history. The AI finds all instances of "connection refused" with surrounding context, helping the developer identify the root cause.

**Why this priority**: Valuable for debugging but not critical for basic monitoring functionality.

**Independent Test**: Can be tested by generating a session with known error patterns, then searching for those patterns and verifying results with context.

**Acceptance Scenarios**:

1. **Given** a session has run for 30 minutes with 5000 lines of output, **When** the user searches for "ERROR", **Then** the AI returns all matching lines with 3 lines of context before and after each match
2. **Given** multiple sessions are active, **When** the user searches across all sessions, **Then** the AI identifies which session contains each match
3. **Given** a search query with a typo, **When** no exact matches are found, **Then** the AI suggests similar terms found in the logs

---

### Edge Cases

- What happens when the terminal output is extremely fast (>10,000 lines/second)?
- How does the system handle sessions that run for multiple days without stopping?
- What if two prompts appear simultaneously (e.g., nested SSH sessions)?
- How does detection work with non-English prompts or custom shell configurations?
- What happens when log files fill the disk during monitoring?
- How does the system handle terminal escape codes and color formatting?
- What if the user types the wrong input and the same prompt reappears - does the AI learn from failures?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST monitor terminal session output in real-time without interfering with the actual session
- **FR-002**: System MUST detect when the terminal is waiting for user input with confidence scoring (0.0-1.0)
- **FR-003**: System MUST identify the type of prompt (password, yes/no, choice, path, text, command)
- **FR-004**: System MUST provide prompt detection results within 500ms of the prompt appearing
- **FR-005**: System MUST track which prompts appeared and what inputs were provided
- **FR-006**: System MUST distinguish between successful and failed input attempts
- **FR-007**: System MUST analyze prompt context to suggest appropriate responses
- **FR-008**: System MUST warn users about potentially dangerous operations (delete, remove, format)
- **FR-009**: System MUST search session history for specific patterns or keywords
- **FR-010**: System MUST maintain session state across multiple monitoring calls
- **FR-011**: System MUST support monitoring of SSH sessions, interactive scripts, database CLIs, and setup wizards
- **FR-012**: System MUST handle sessions with multiple sequential prompts without losing context
- **FR-013**: System MUST persist input history for pattern analysis across sessions
- **FR-014**: System MUST identify common prompts and typical user responses
- **FR-015**: System MUST calculate success rates for different input patterns
- **FR-016**: System MUST provide AI assistants with structured session data
- **FR-017**: System MUST allow AI assistants to query for new session updates incrementally
- **FR-018**: System MUST expose all monitoring capabilities through well-defined interfaces
- **FR-019**: System MUST handle graceful degradation when session monitoring fails
- **FR-020**: System MUST clean up resources when monitoring stops

### Key Entities

- **Session**: Represents an active terminal session being monitored. Attributes include unique identifier, session type (SSH, script, file), start time, current state (active, stopped), and path to output log.

- **Prompt Detection**: Represents a detected prompt waiting for input. Attributes include prompt text, confidence score, prompt type, detected pattern, file position, and timestamp.

- **Input Event**: Represents a recorded user input. Attributes include timestamp, prompt text, input text provided, success/failure status, input source (user-typed, AI-suggested, auto-injected), and response time.

- **Pattern**: Represents a learned prompt-response pattern. Attributes include prompt text, typical responses, success count, failure count, and last occurrence timestamp.

- **Session Update**: Represents incremental content from a monitored session. Attributes include new content since last check, current file position, and whether more content exists.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: AI assistant can detect password prompts with >85% accuracy (measured against manual review of 100+ SSH sessions)
- **SC-002**: Prompt detection completes within 500ms from prompt appearance to AI notification
- **SC-003**: Users save an average of 5 minutes per interactive session by receiving real-time guidance
- **SC-004**: 70% of suggested inputs are actually used by users (indicates relevance)
- **SC-005**: System successfully monitors sessions running for 8+ hours without memory leaks or performance degradation
- **SC-006**: AI assistant can recall and search session history from 30 days ago in under 1 second
- **SC-007**: Pattern learning achieves >80% prediction accuracy after observing 5+ instances of the same prompt
- **SC-008**: System correctly flags dangerous operations (delete, format, etc.) with >95% accuracy
- **SC-009**: Users report increased confidence when running unfamiliar interactive tools (qualitative metric via user surveys)
- **SC-010**: 50% reduction in failed input attempts after 10 sessions (users learn from AI warnings)
- **SC-011**: Zero data loss incidents from monitored sessions (session output must be completely captured)
- **SC-012**: Support for 10 concurrent session monitors on a standard workstation without performance impact

### User Experience Goals

- Users feel like they have an "AI pair programmer looking over their shoulder" during terminal sessions
- Users trust the AI's suggestions enough to follow them for routine operations
- Users understand why a prompt was detected or missed (explainability)
- Users can easily clean up old session data and understand what's stored

## Scope & Boundaries

### In Scope

- Real-time monitoring of terminal session output
- Pattern-based prompt detection for common prompt types
- Contextual analysis to suggest appropriate inputs
- Input history tracking and pattern learning
- Session history search functionality
- Support for SSH, interactive scripts, database CLIs, setup wizards
- Graceful handling of long-running sessions (hours to days)
- Cleanup of old session data based on retention policies

### Out of Scope

- Automatic command injection without explicit user permission (security concern)
- Support for graphical terminal applications (vim, htop, k9s) - deferred to future phase
- Native Windows PowerShell support (WSL only) - deferred to future phase
- Real-time LLM inference for every prompt (optional fallback only, not required for MVP)
- Cloud synchronization or multi-device session sharing
- Integration with external logging platforms (ELK, Splunk) - basic export only

## Assumptions

- Users primarily work in Unix-like environments (Linux, macOS, WSL)
- Terminal sessions produce text-based output (not binary protocols)
- Users have basic understanding of terminal operations
- Standard Unix tools like `script` or `tmux` are available
- File system has sufficient space for session logs (100MB per session expected)
- Users run monitoring on local workstation, not remote server
- Default 7-day retention is acceptable for most use cases
- Users prefer privacy-first approach (opt-in for any data sharing)

## Dependencies

- Unix `script` command or `tmux` for session recording
- File system with read/write permissions for log storage
- AI assistant must support Model Context Protocol (MCP) for integration

## Privacy & Security Considerations

- Session logs may contain sensitive data (passwords, API keys, confidential commands)
- Password input text must never be logged or transmitted
- Logs must be stored with restricted permissions (user-only access)
- Automatic cleanup after retention period to minimize data exposure
- No telemetry or external transmission without explicit user consent
- Users must have clear documentation of what data is stored and where
- Command injection (if added later) requires explicit confirmation to prevent accidents

## Future Enhancements

### Two-Pane TUI Monitor (Phase 4)

**Vision**: A split-pane terminal interface that provides real-time visual feedback alongside the monitored session.

**Layout**:
- **Left Pane**: Live terminal session running (SSH, scripts, interactive tools)
- **Right Pane**: Real-time AI feedback showing detected prompts, suggestions, confidence scores, and warnings

**Key Capabilities**:
- Event-driven updates as prompts are detected
- Visual indicators for prompt types (password, yes/no, dangerous operations)
- Live suggestion display with reasoning
- Session history timeline showing input/output flow
- Confidence score visualization
- Pattern learning insights displayed in real-time

**Why Deferred**:
- Requires terminal emulation/rendering infrastructure (ncurses, Rich, Textual, etc.)
- Complex event system for real-time synchronization
- Independent value proposition - core MCP monitoring works without visual interface
- Can be implemented after core detection and monitoring features are stable

**User Value**:
- "See what the AI sees" - developers can observe detection in real-time
- Faster learning curve - visual feedback builds trust in AI suggestions
- Debugging tool - verify prompt detection accuracy visually
- Enhanced developer experience for complex interactive sessions

**Implementation Considerations**:
- Terminal emulator choice impacts rendering performance
- Event architecture must handle high-frequency updates (>10k lines/second)
- Layout must be responsive to different terminal sizes
- Accessibility considerations for color schemes and text-only mode
- Graceful degradation when terminal doesn't support advanced rendering

**Success Metrics**:
- Visual feedback renders within 100ms of prompt detection
- Users report increased confidence in AI suggestions (measured via surveys)
- 50% reduction in "why wasn't this detected?" support questions
- TUI handles sessions with 10k+ lines without performance degradation
