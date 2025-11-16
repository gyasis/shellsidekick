# Implementation Plan: MCP Session Monitor

**Branch**: `001-mcp-session-monitor` | **Date**: 2025-11-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-mcp-session-monitor/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

ShellSidekick MCP Session Monitor provides real-time monitoring of terminal sessions with AI-powered prompt detection and contextual suggestions. The system monitors SSH sessions, interactive scripts, and database CLIs, detecting when the terminal is waiting for input and providing intelligent recommendations based on pattern learning and context analysis. Built as an MCP server using FastMCP framework with uv for environment isolation.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastMCP (latest via Context7), standard library (re, pathlib, json), uv for environment management
**Storage**: File-based (JSON for input history/patterns, text files for session logs with 7-day retention)
**Testing**: pytest with >80% coverage (TDD enforced by constitution)
**Target Platform**: Linux, macOS, WSL (Unix-like systems with script/tmux available)
**Project Type**: single (MCP server with CLI monitoring interface)
**Performance Goals**: <500ms prompt detection latency, >10,000 lines/sec log processing throughput
**Constraints**: <500ms end-to-end response time, <50MB memory per monitored session, file position-based incremental reads
**Scale/Scope**: 10 concurrent session monitors, 30-day history retention, 85% prompt detection accuracy

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Notes |
|-----------|------------------|-------|
| **I. MCP-First Architecture** | ✅ PASS | Feature spec defines 11 MCP tools (FR-016, FR-017, FR-018). All monitoring capabilities exposed via MCP. No CLI-exclusive functionality. |
| **II. Real-Time Monitoring & Detection** | ✅ PASS | Spec requires <500ms detection (FR-004), pattern-based regex detection (FR-003), file position tracking (FR-010), confidence scoring (FR-002). LLM inference not required for MVP. |
| **III. Test-First Development** | ✅ PASS | Constitution enforces TDD. Planning workflow includes Phase 1 contract generation for test boundaries. >80% coverage target in technical context. |
| **IV. Security by Default** | ✅ PASS | Spec includes dangerous operation detection (FR-008), warns users (User Story 2). Command injection deferred to post-MVP (out of scope). Security requirements clearly documented. |
| **V. Privacy & Data Minimization** | ✅ PASS | Spec requires password-safe logging, user-only permissions, 7-day retention, no external transmission (Privacy section). File-based storage with cleanup (FR-020). |
| **VI. Observability & Debugging** | ✅ PASS | Confidence scoring required (FR-002), pattern identification (FR-003), session history search (FR-009), detection history tracking (FR-005, FR-006). |
| **VII. Simplicity & YAGNI** | ✅ PASS | File-based monitoring via script/tmux (Assumptions), pattern-based detection (no ML), JSON storage for history (Storage), incremental file reads (FR-010). No unnecessary complexity. |

**GATE RESULT (Initial)**: ✅ **PASS** - All 7 principles satisfied. Proceed to Phase 0 research.

---

## Constitution Re-evaluation (Post-Phase 1 Design)

*Re-check after Phase 1 design artifacts complete.*

| Principle | Compliance Status | Design Verification |
|-----------|------------------|---------------------|
| **I. MCP-First Architecture** | ✅ PASS | 11 MCP tools defined with complete JSON schemas in contracts/. All session monitoring, detection, and history capabilities exposed via MCP. Tool contracts specify input/output schemas, error codes, and test cases. No CLI-exclusive functionality. |
| **II. Real-Time Monitoring & Detection** | ✅ PASS | research.md confirms regex-based detection with <100ms latency (benchmark: 67ms). File position tracking implemented in data-model.md (Session.file_position). Confidence scoring defined in PromptDetection entity. Performance test in detection-tools.md validates <500ms requirement. |
| **III. Test-First Development** | ✅ PASS | Contract files include comprehensive pytest test cases for all tools. quickstart.md documents TDD workflow (Red-Green-Refactor). Test structure defined: contract/, integration/, unit/. >80% coverage target in plan.md Technical Context. Agent context (.claude/CLAUDE.md) emphasizes TDD as NON-NEGOTIABLE. |
| **IV. Security by Default** | ✅ PASS | research.md defines dangerous command detection patterns (rm -rf, mkfs, format). data-model.md requires InputEvent.input_text = "[REDACTED]" for passwords. detection-tools.md includes is_dangerous flag in PromptDetection. Security test cases verify password redaction. File permissions (chmod 600) documented in research.md. |
| **V. Privacy & Data Minimization** | ✅ PASS | data-model.md specifies 7-day retention, JSON storage in /tmp/ssk-sessions/. history-tools.md defines cleanup_old_sessions tool with retention_days parameter. quickstart.md documents secure file permissions. No telemetry or external transmission. |
| **VI. Observability & Debugging** | ✅ PASS | PromptDetection includes confidence score, matched_pattern, timestamp. detection-tools.md returns reasoning in infer_expected_input suggestions. search_session_history supports context lines. quickstart.md includes debug logging setup. All tool contracts specify error codes and messages. |
| **VII. Simplicity & YAGNI** | ✅ PASS | research.md selects file-based monitoring via script (not complex IPC). Regex patterns only (no ML). JSON storage (not distributed DB). data-model.md uses Python dataclasses (simple, type-safe). No unnecessary abstractions or premature optimization. |

**GATE RESULT (Final)**: ✅ **PASS** - All 7 principles maintained through Phase 1 design. Design artifacts (research.md, data-model.md, contracts/, quickstart.md, agent context) fully comply with constitution.

**Design Quality Assessment**:
- ✅ All unknowns from spec resolved (FastMCP patterns, uv setup, storage strategy)
- ✅ Entity model complete with validation rules and relationships
- ✅ 11 MCP tools fully specified with JSON schemas, error cases, and test cases
- ✅ Performance benchmarks confirm <500ms latency, >10k lines/sec throughput
- ✅ Security patterns defined (password redaction, dangerous command detection)
- ✅ TDD workflow documented with FastMCP client testing examples
- ✅ Agent context established for future AI-assisted development

**Ready for Phase 2**: Generate tasks.md with dependency-ordered implementation tasks.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/shellsidekick/
├── __init__.py
├── mcp/
│   ├── __init__.py
│   ├── server.py           # FastMCP server initialization
│   ├── tools/               # MCP tool implementations
│   │   ├── __init__.py
│   │   ├── session.py       # Session lifecycle tools
│   │   ├── detection.py     # Prompt detection tools
│   │   ├── inference.py     # Input suggestion tools
│   │   └── history.py       # History search tools
│   └── schemas/             # JSON schemas for MCP tools
│       └── tools.json
├── core/
│   ├── __init__.py
│   ├── monitor.py           # SessionMonitor class
│   ├── detector.py          # PromptDetector with regex patterns
│   ├── patterns.py          # Pattern learning and storage
│   └── storage.py           # File I/O and JSON persistence
├── models/
│   ├── __init__.py
│   ├── session.py           # Session entity
│   ├── prompt.py            # PromptDetection entity
│   ├── input_event.py       # InputEvent entity
│   └── pattern.py           # Pattern entity
└── utils/
    ├── __init__.py
    ├── file_utils.py        # File position tracking, incremental reads
    ├── security.py          # Dangerous command detection, redaction
    └── logging.py           # Structured logging setup

tests/
├── contract/                # Contract tests from Phase 1 artifacts
│   ├── test_session_tools.py
│   ├── test_detection_tools.py
│   └── test_history_tools.py
├── integration/             # End-to-end session lifecycle tests
│   ├── test_ssh_monitoring.py
│   ├── test_script_monitoring.py
│   └── test_pattern_learning.py
└── unit/                    # Unit tests for detection patterns
    ├── test_monitor.py
    ├── test_detector.py
    ├── test_patterns.py
    └── test_security.py

pyproject.toml               # uv project configuration
uv.lock                      # Locked dependencies
README.md                    # MCP server setup and usage
```

**Structure Decision**: Single Python project with MCP server as primary interface. Using FastMCP framework for server implementation, uv for dependency management. Source code organized by layer: `mcp/` (MCP tool layer), `core/` (business logic), `models/` (entities), `utils/` (cross-cutting concerns). Test structure mirrors source with contract, integration, and unit test levels.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
