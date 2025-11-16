<!--
  SYNC IMPACT REPORT
  ==================
  Version Change: N/A → 1.0.0 (Initial Constitution)

  Modified Principles: N/A (Initial creation)
  Added Sections:
    - Core Principles (I-VII)
    - Architecture Standards
    - Development Workflow
    - Governance

  Removed Sections: N/A

  Templates Requiring Updates:
    ✅ spec-template.md - Compatible (user story focus aligns with Test-First)
    ✅ plan-template.md - Compatible (constitution check section exists)
    ✅ tasks-template.md - Compatible (test-focused task structure aligns)
    ✅ checklist-template.md - UPDATED (added constitution compliance, security, privacy, testing sections)

  Follow-up TODOs: None
-->

# ShellSidekick Constitution

## Core Principles

### I. MCP-First Architecture

Every feature MUST be exposed as an MCP tool with proper JSON schema. The MCP server is the primary interface for AI assistants.

**Rationale**: ShellSidekick's value proposition is enabling AI pair programming during terminal sessions. Without MCP tools, the project fails its core mission.

**Requirements**:
- All session monitoring, detection, and inference capabilities exposed as MCP tools
- JSON schemas MUST include descriptions, types, and validation
- Tool responses MUST be structured and machine-readable
- No functionality exclusive to CLI that cannot be accessed via MCP

### II. Real-Time Monitoring & Detection

Pattern-based prompt detection MUST be fast (<100ms) and deterministic. LLM inference is optional fallback only.

**Rationale**: Users expect instant feedback during interactive sessions. Slow detection breaks the "pair programming" experience.

**Requirements**:
- Regex-based detection for common prompts (password, yes/no, choice, path)
- Confidence scoring (0.0-1.0) for all detections
- File-based monitoring with incremental reads (file position tracking)
- Non-blocking I/O throughout monitoring pipeline
- Optional LLM inference only for ambiguous cases (user-configurable)

### III. Test-First Development (NON-NEGOTIABLE)

TDD is mandatory: Tests written → User approved → Tests fail → Then implement. Red-Green-Refactor cycle strictly enforced.

**Rationale**: Prompt detection and command injection are safety-critical. Bugs can lead to data loss or security breaches.

**Requirements**:
- Unit tests for all detection patterns before implementation
- Integration tests for session monitoring lifecycle
- Security tests for command injection safety guards
- Test coverage >80% for core modules (monitor, detector, inference, security)
- Manual test cases documented for real SSH/interactive sessions

### IV. Security by Default

All command injection MUST be opt-in with confirmation. Dangerous commands MUST be blocked unless explicitly overridden.

**Rationale**: Injecting wrong commands can destroy systems. Users must maintain full control and awareness.

**Requirements**:
- Blocklist for dangerous commands (rm -rf /, mkfs, fork bombs, etc.)
- Confirmation prompt before EVERY injected command (unless in trusted session mode)
- Password redaction in logs (mask as `[PASSWORD]`)
- Secret pattern detection and redaction (API keys, tokens)
- Log files with user-only permissions (chmod 600)
- No cross-user session access
- Audit log for all injected commands with timestamps

### V. Privacy & Data Minimization

Logs MUST be stored securely and deleted after retention period. No telemetry without explicit consent.

**Rationale**: Terminal sessions contain sensitive data (passwords, keys, confidential commands). Privacy is non-negotiable.

**Requirements**:
- Logs in secure temp directory (`/tmp/ssk-sessions` or user-configured)
- Default retention: 7 days (configurable via `SSK_LOG_RETENTION_DAYS`)
- Automatic cleanup of expired logs
- No cloud sync or external transmission without user opt-in
- Clear documentation of what data is stored and where
- Easy cleanup: `ssk cleanup --all`

### VI. Observability & Debugging

All detection decisions MUST be explainable. Users must understand why a prompt was detected or missed.

**Rationale**: When detection fails, users need to understand why to improve patterns or report bugs.

**Requirements**:
- Confidence scores for all detections
- Show matched pattern/regex in detection results
- Debug mode: `ssk watch --debug <monitor-id>` shows detection reasoning
- Structured logging with severity levels (DEBUG, INFO, WARN, ERROR)
- CLI commands for inspection: `ssk history`, `ssk search`, `ssk patterns`

### VII. Simplicity & YAGNI

Start with file-based monitoring and pattern matching. Avoid complex IPC, network protocols, or ML until proven necessary.

**Rationale**: Phase 1-3 must deliver value quickly. Over-engineering delays user feedback and increases bug surface.

**Requirements**:
- File-based monitoring (via `script`, `tmux pipe-pane`, or file watching)
- Regex patterns for detection (no ML in MVP)
- Synchronous command injection with timeout (no complex async orchestration)
- SQLite or JSON for history storage (no distributed database)
- Incremental complexity: only add features when current solution is proven insufficient

## Architecture Standards

### MCP Tool Design

- Tool names: `snake_case` (e.g., `start_session_monitor`, `detect_input_prompt`)
- Input validation: JSON Schema with required/optional parameters clearly marked
- Error handling: Return `{"error": "message", "code": "ERROR_CODE"}` for failures
- Idempotency: Tools like `start_session_monitor` must handle re-start gracefully
- Documentation: Each tool MUST have description, parameter descriptions, and return type

### Session Lifecycle

1. **Start** → `start_session_monitor()` creates log file, spawns process, returns `monitor_id`
2. **Monitor** → `get_session_updates()` returns incremental content since last check
3. **Detect** → `detect_input_prompt()` analyzes recent output for prompts
4. **Infer** → `infer_expected_input()` suggests appropriate responses
5. **Track** → `track_input_event()` records what user typed and success/failure
6. **Stop** → `stop_session_monitor()` cleans up process, optionally saves log

### Error Recovery

- File not found → Return clear error with suggested action
- Process crash → Clean up stale PID files, allow restart
- Permission denied → Return actionable error (e.g., "Run with user permissions")
- Timeout → Kill subprocess gracefully, return timeout error
- Invalid input → Validate early, return schema violation details

## Development Workflow

### Feature Development Process

1. **Specification** → Create spec in `.specify/specs/[###-feature]/spec.md` with user stories
2. **Planning** → Run `/speckit.plan` to generate design artifacts (research, data-model, contracts)
3. **Constitution Check** → Verify alignment with all principles (documented in plan.md)
4. **Task Generation** → Run `/speckit.tasks` to generate dependency-ordered tasks
5. **Test Writing** → Write tests for P1 user story FIRST, get user approval
6. **Implementation** → Implement feature following Red-Green-Refactor
7. **Integration Testing** → Test with real SSH/interactive sessions
8. **Documentation** → Update README, MCP tool reference, examples

### Testing Strategy

- **Unit Tests**: All detection patterns, inference logic, security checks
- **Integration Tests**: Full session lifecycle (start → detect → inject → stop)
- **Security Tests**: Dangerous command blocking, secret redaction, permission checks
- **Manual Tests**: Real SSH sessions, database CLIs, deployment scripts
- **Performance Tests**: Detection latency (<100ms), log processing rate (>10k lines/sec)

### Git Workflow

- Feature branches: `[###-feature-name]` (e.g., `001-password-detection`)
- Commit messages: Conventional Commits (e.g., `feat: add password prompt detection`)
- PR requirements: Tests pass, code formatted (Black), lints clean (Ruff), docs updated
- No direct commits to `main` without PR review

## Governance

### Amendment Process

1. Propose change via GitHub Issue or PR with rationale
2. Review by maintainers for compatibility with project mission
3. If principle added/removed: MAJOR version bump (e.g., 1.0.0 → 2.0.0)
4. If principle expanded/refined: MINOR version bump (e.g., 1.0.0 → 1.1.0)
5. If typo/clarification: PATCH version bump (e.g., 1.0.0 → 1.0.1)
6. Update templates and commands to reflect changes
7. Document migration path for existing features if backward incompatible

### Compliance Review

- All PRs MUST include constitution compliance checklist:
  - [ ] MCP tool with JSON schema (if feature adds functionality)
  - [ ] Tests written before implementation (TDD)
  - [ ] Security review for command injection or secrets handling
  - [ ] Privacy review for data storage
  - [ ] Observability (debug mode, structured logs)
  - [ ] Simplicity check (YAGNI - no unnecessary complexity)

### Exceptions

Exceptions to principles MUST be documented in PR description with:
- Which principle is being deviated from
- Why deviation is necessary (technical or user requirement)
- Mitigation plan to minimize impact
- Timeline to return to compliance (if temporary)

### Living Document

This constitution supersedes all other practices. When in conflict, constitution wins.

Development guidance (e.g., coding style, tool choices) should be documented in `docs/contributing.md` or `.claude/CLAUDE.md`, not here.

**Version**: 1.0.0 | **Ratified**: 2025-11-14 | **Last Amended**: 2025-11-14
