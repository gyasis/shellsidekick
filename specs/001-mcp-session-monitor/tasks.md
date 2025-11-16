# Tasks: MCP Session Monitor

**Feature**: ShellSidekick MCP Session Monitor
**Input**: Design documents from `/specs/001-mcp-session-monitor/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Constitution Compliance**: This feature follows Test-First Development (TDD). Contract tests are included per constitution requirement III.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- All file paths are absolute from repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure per plan.md in src/shellsidekick/
- [X] T002 Initialize pyproject.toml with uv, FastMCP >=0.5.0, and Python 3.11+ requirements
- [X] T003 [P] Add development dependencies: pytest, pytest-asyncio, black, ruff in pyproject.toml
- [X] T004 [P] Create all __init__.py files for Python package structure
- [X] T005 [P] Setup structured logging utility in src/shellsidekick/utils/logging.py
- [X] T006 [P] Configure pytest with asyncio_mode="auto" in pyproject.toml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Define SessionType, SessionState enums in src/shellsidekick/models/session.py
- [X] T008 [P] Define PromptType enum in src/shellsidekick/models/prompt.py
- [X] T009 [P] Define InputSource enum in src/shellsidekick/models/input_event.py
- [X] T010 Create Session dataclass with to_dict() method in src/shellsidekick/models/session.py
- [X] T011 [P] Create PromptDetection dataclass with to_dict() method in src/shellsidekick/models/prompt.py
- [X] T012 [P] Create InputEvent dataclass with to_dict() method in src/shellsidekick/models/input_event.py
- [X] T013 [P] Create Pattern and ResponseStats dataclasses in src/shellsidekick/models/pattern.py
- [X] T014 Initialize FastMCP server instance in src/shellsidekick/mcp/server.py
- [X] T015 [P] Implement file position tracking utility in src/shellsidekick/utils/file_utils.py
- [X] T016 [P] Implement password detection patterns in src/shellsidekick/utils/security.py
- [X] T017 [P] Implement dangerous command detection in src/shellsidekick/utils/security.py
- [X] T018 Create storage directory /tmp/ssk-sessions/ with secure permissions (chmod 700)
- [X] T019 [P] Implement JSON storage base utilities in src/shellsidekick/core/storage.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - AI Monitors SSH Session for Prompts (Priority: P1) 🎯 MVP

**Goal**: Enable AI to detect terminal prompts in real-time and notify developers within 500ms

**Independent Test**: Start SSH session, reach password prompt, verify AI detects prompt and suggests input within 500ms

### Contract Tests for User Story 1 (TDD Required by Constitution)

**⚠️ CRITICAL: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T020 [P] [US1] Contract test for start_session_monitor in tests/contract/test_session_tools.py
- [X] T021 [P] [US1] Contract test for get_session_updates in tests/contract/test_session_tools.py
- [X] T022 [P] [US1] Contract test for stop_session_monitor in tests/contract/test_session_tools.py
- [X] T023 [P] [US1] Contract test for detect_input_prompt in tests/contract/test_detection_tools.py
- [X] T024 [P] [US1] Performance test for <500ms detection in tests/contract/test_detection_tools.py
- [X] T025 [P] [US1] Contract test for 10k lines/sec throughput in tests/contract/test_detection_tools.py

### Core Implementation for User Story 1

- [X] T026 [P] [US1] Implement prompt detection regex patterns in src/shellsidekick/core/detector.py
- [X] T027 [P] [US1] Implement SessionMonitor class with file position tracking in src/shellsidekick/core/monitor.py
- [X] T028 [US1] Implement PromptDetector.detect() method using patterns in src/shellsidekick/core/detector.py
- [X] T029 [US1] Implement start_session_monitor MCP tool in src/shellsidekick/mcp/tools/session.py
- [X] T030 [US1] Implement get_session_updates MCP tool in src/shellsidekick/mcp/tools/session.py
- [X] T031 [US1] Implement stop_session_monitor MCP tool in src/shellsidekick/mcp/tools/session.py
- [X] T032 [US1] Implement detect_input_prompt MCP tool in src/shellsidekick/mcp/tools/detection.py
- [X] T033 [US1] Add error handling with FastMCP ToolError for all session tools
- [X] T034 [US1] Add session state validation (duplicate check, file exists check)
- [X] T035 [US1] Verify all US1 contract tests pass

### Integration Tests for User Story 1

- [X] T036 [P] [US1] Integration test for SSH session monitoring in tests/integration/test_ssh_monitoring.py
- [X] T037 [P] [US1] Integration test for script monitoring in tests/integration/test_script_monitoring.py
- [X] T038 [US1] End-to-end test: start session → detect prompt → stop session

**Checkpoint**: User Story 1 complete - AI can monitor sessions and detect prompts in <500ms

---

## Phase 4: User Story 2 - AI Suggests Inputs Based on Context (Priority: P2)

**Goal**: Provide intelligent input suggestions with context analysis and danger warnings

**Independent Test**: Run migration script with "Delete 3 tables?" prompt, verify AI warns about destructive operation

### Contract Tests for User Story 2

- [ ] T039 [P] [US2] Contract test for infer_expected_input in tests/contract/test_detection_tools.py
- [ ] T040 [P] [US2] Test dangerous operation warning detection in tests/contract/test_detection_tools.py
- [ ] T041 [P] [US2] Test context-based path suggestions in tests/contract/test_detection_tools.py

### Implementation for User Story 2

- [ ] T042 [P] [US2] Implement dangerous keyword patterns in src/shellsidekick/core/detector.py
- [ ] T043 [P] [US2] Implement context inference logic in src/shellsidekick/core/detector.py
- [ ] T044 [US2] Implement default suggestions by prompt type in src/shellsidekick/core/detector.py
- [ ] T045 [US2] Implement infer_expected_input MCP tool in src/shellsidekick/mcp/tools/detection.py
- [ ] T046 [US2] Add warning generation for dangerous operations
- [ ] T047 [US2] Add reasoning text for each suggestion
- [ ] T048 [US2] Verify all US2 contract tests pass

### Integration Tests for User Story 2

- [ ] T049 [US2] Integration test for dangerous operation detection in real migration script

**Checkpoint**: User Story 2 complete - AI provides contextual suggestions with safety warnings

---

## Phase 5: User Story 3 - AI Learns from Input History (Priority: P3)

**Goal**: Track user inputs and suggest based on learned patterns

**Independent Test**: Answer same prompt 5 times consistently, verify AI suggests pattern on 6th occurrence

### Contract Tests for User Story 3

- [ ] T050 [P] [US3] Contract test for track_input_event in tests/contract/test_detection_tools.py
- [ ] T051 [P] [US3] Test password redaction in tracked events in tests/contract/test_detection_tools.py
- [ ] T052 [P] [US3] Contract test for get_learned_patterns in tests/contract/test_history_tools.py
- [ ] T053 [P] [US3] Test pattern suggestion prioritization in tests/contract/test_detection_tools.py

### Implementation for User Story 3

- [ ] T054 [P] [US3] Implement pattern storage structure in src/shellsidekick/core/patterns.py
- [ ] T055 [P] [US3] Implement pattern update logic in src/shellsidekick/core/patterns.py
- [ ] T056 [US3] Implement pattern loading/saving from JSON in src/shellsidekick/core/storage.py
- [ ] T057 [US3] Implement track_input_event MCP tool in src/shellsidekick/mcp/tools/detection.py
- [ ] T058 [US3] Implement get_learned_patterns MCP tool in src/shellsidekick/mcp/tools/history.py
- [ ] T059 [US3] Add password redaction in track_input_event for PromptType.PASSWORD
- [ ] T060 [US3] Integrate pattern learning into infer_expected_input tool
- [ ] T061 [US3] Add pattern-based suggestions to inference engine
- [ ] T062 [US3] Verify all US3 contract tests pass

### Integration Tests for User Story 3

- [ ] T063 [US3] Integration test for pattern learning over multiple sessions in tests/integration/test_pattern_learning.py
- [ ] T064 [US3] Test pattern persistence across server restarts

**Checkpoint**: User Story 3 complete - AI learns from history and personalizes suggestions

---

## Phase 6: User Story 4 - AI Provides Session History Search (Priority: P4)

**Goal**: Enable searching session logs for debugging and pattern discovery

**Independent Test**: Generate session with "connection refused" errors, search for pattern, verify results with context

### Contract Tests for User Story 4

- [ ] T065 [P] [US4] Contract test for search_session_history in tests/contract/test_history_tools.py
- [ ] T066 [P] [US4] Test regex search functionality in tests/contract/test_history_tools.py
- [ ] T067 [P] [US4] Test context lines before/after matches in tests/contract/test_history_tools.py
- [ ] T068 [P] [US4] Test max results limiting in tests/contract/test_history_tools.py
- [ ] T069 [P] [US4] Contract test for cleanup_old_sessions in tests/contract/test_history_tools.py
- [ ] T070 [P] [US4] Test cleanup dry run mode in tests/contract/test_history_tools.py

### Implementation for User Story 4

- [ ] T071 [P] [US4] Implement log file search with regex in src/shellsidekick/core/storage.py
- [ ] T072 [P] [US4] Implement context extraction around matches in src/shellsidekick/core/storage.py
- [ ] T073 [US4] Implement search_session_history MCP tool in src/shellsidekick/mcp/tools/history.py
- [ ] T074 [US4] Implement cleanup_old_sessions MCP tool in src/shellsidekick/mcp/tools/history.py
- [ ] T075 [US4] Add session age calculation based on file mtime
- [ ] T076 [US4] Add dry run mode for cleanup preview
- [ ] T077 [US4] Verify all US4 contract tests pass

### Integration Tests for User Story 4

- [ ] T078 [US4] Integration test for multi-session search
- [ ] T079 [US4] Test cleanup with 7-day retention policy

**Checkpoint**: User Story 4 complete - Full session history search and cleanup functionality

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T080 [P] Add unit tests for PromptDetector patterns in tests/unit/test_detector.py
- [ ] T081 [P] Add unit tests for SessionMonitor in tests/unit/test_monitor.py
- [ ] T082 [P] Add unit tests for Pattern learning logic in tests/unit/test_patterns.py
- [ ] T083 [P] Add unit tests for security utilities in tests/unit/test_security.py
- [ ] T084 [P] Run black formatter on all source files
- [ ] T085 [P] Run ruff linter and fix issues
- [ ] T086 Verify >80% test coverage per constitution requirement
- [ ] T087 [P] Generate FastMCP configuration with `fastmcp install`
- [ ] T088 [P] Update README.md with MCP server setup instructions
- [ ] T089 [P] Document all 11 MCP tools with examples in README.md
- [ ] T090 Run quickstart.md validation workflow (TDD cycle verification)
- [ ] T091 Performance validation: <500ms detection, >10k lines/sec throughput
- [ ] T092 Security audit: password redaction, dangerous command detection
- [ ] T093 [P] Add agent context to .claude/CLAUDE.md (already exists, verify completeness)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 - Core monitoring capability (MVP)
- **User Story 2 (Phase 4)**: Depends on Phase 2 - Independent of US1 but builds on detection
- **User Story 3 (Phase 5)**: Depends on Phase 2 and US1 (needs track_input_event integration)
- **User Story 4 (Phase 6)**: Depends on Phase 2 - Independent search functionality
- **Polish (Phase 7)**: Depends on completion of desired user stories

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories ✅ MVP
- **User Story 2 (P2)**: Can start after Foundational - Enhances US1 but independently testable
- **User Story 3 (P3)**: Depends on US1 detect_input_prompt - Needs session lifecycle
- **User Story 4 (P4)**: Can start after Foundational - Independent search functionality

### Within Each User Story

**TDD Workflow (Constitution Requirement)**:
1. Contract tests MUST be written FIRST (marked with task IDs)
2. Run tests - verify they FAIL (Red phase)
3. Implement minimal code to pass tests (Green phase)
4. Refactor while keeping tests green
5. Verify all tests pass before marking story complete

### Parallel Opportunities

**Phase 1 (Setup)**: T003, T004, T005, T006 can run in parallel

**Phase 2 (Foundational)**:
- T007, T008, T009 (enums) can run in parallel
- T011, T012, T013 (dataclasses) can run in parallel after enums
- T015, T016, T017, T019 (utilities) can run in parallel

**User Story 1**:
- Contract tests T020-T025 can all run in parallel (write tests together)
- Models T026, T027 can run in parallel
- Integration tests T036, T037 can run in parallel

**User Story 2**:
- Contract tests T039-T041 can run in parallel
- Implementation T042, T043 can run in parallel

**User Story 3**:
- Contract tests T050-T053 can run in parallel
- Models T054, T055 can run in parallel

**User Story 4**:
- Contract tests T065-T070 can run in parallel
- Implementation T071, T072 can run in parallel

**Polish Phase**: T080-T085, T087-T089 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Step 1: Write all contract tests in parallel
Task T020: "Contract test for start_session_monitor"
Task T021: "Contract test for get_session_updates"
Task T022: "Contract test for stop_session_monitor"
Task T023: "Contract test for detect_input_prompt"
Task T024: "Performance test for <500ms detection"
Task T025: "Contract test for 10k lines/sec throughput"

# Step 2: Run tests - verify FAIL (Red)
uv run pytest tests/contract/test_session_tools.py -v
uv run pytest tests/contract/test_detection_tools.py -v

# Step 3: Implement core models in parallel
Task T026: "Implement prompt detection regex patterns"
Task T027: "Implement SessionMonitor class"

# Step 4: Implement MCP tools sequentially (depend on core)
Task T029: "Implement start_session_monitor MCP tool"
Task T030: "Implement get_session_updates MCP tool"
Task T031: "Implement stop_session_monitor MCP tool"
Task T032: "Implement detect_input_prompt MCP tool"

# Step 5: Run tests - verify PASS (Green)
uv run pytest tests/contract/ -v

# Step 6: Integration tests in parallel
Task T036: "Integration test for SSH session monitoring"
Task T037: "Integration test for script monitoring"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. ✅ Complete Phase 1: Setup (T001-T006)
2. ✅ Complete Phase 2: Foundational (T007-T019) - CRITICAL BLOCKING
3. ✅ Complete Phase 3: User Story 1 (T020-T038)
4. **STOP and VALIDATE**:
   - Run quickstart.md TDD workflow
   - Test real SSH session monitoring
   - Verify <500ms detection latency
   - Confirm 85% prompt detection accuracy
5. Deploy/demo if ready - MVP complete! 🎯

### Incremental Delivery

1. **Foundation** (Phases 1-2) → Project structure ready
2. **MVP** (Phase 3 - US1) → Basic monitoring working → Deploy/Demo ✅
3. **Intelligence** (Phase 4 - US2) → Context-aware suggestions → Deploy/Demo
4. **Learning** (Phase 5 - US3) → Pattern-based personalization → Deploy/Demo
5. **Debugging** (Phase 6 - US4) → History search capability → Deploy/Demo
6. **Production-Ready** (Phase 7) → Polish and documentation → Final Release

### Parallel Team Strategy

With multiple developers:

1. **Team** completes Setup + Foundational together (Phases 1-2)
2. **Once Foundational is done**:
   - **Developer A**: User Story 1 (P1) - Core monitoring
   - **Developer B**: User Story 4 (P4) - History search (independent)
   - **Developer C**: Polish setup, documentation
3. **After US1 complete**:
   - **Developer A**: User Story 2 (P2) - Context suggestions
   - **Developer B**: User Story 3 (P3) - Pattern learning
4. Stories complete and integrate independently

---

## Success Metrics (from spec.md)

Track these metrics during implementation:

- **SC-001**: >85% password prompt detection accuracy (measure during testing)
- **SC-002**: <500ms detection latency (automated test in T024)
- **SC-003**: 5min time saved per session (user feedback metric)
- **SC-004**: 70% suggestion acceptance rate (track via input_source)
- **SC-005**: 8+ hour session support (stress test)
- **SC-006**: <1s history search (automated test)
- **SC-007**: 80% pattern prediction accuracy after 5+ instances
- **SC-008**: >95% dangerous operation detection
- **SC-011**: Zero data loss (verify complete log capture)
- **SC-012**: 10 concurrent sessions without performance impact

---

## Notes

- **[P] tasks**: Different files, no dependencies - can run in parallel
- **[Story] label**: Maps task to specific user story for traceability
- **TDD Required**: Constitution principle III enforces test-first development
- **Constitution VII**: Simple file-based approach - no premature optimization
- **Constitution V**: Password redaction enforced in T051, T059
- **Constitution IV**: Dangerous command detection in T042, T046
- **File paths**: All paths relative to repository root `/home/gyasis/Documents/code/shellsidekick`
- **Verify tests fail**: Before implementing, confirm Red phase of TDD
- **Commit frequency**: After each task or logical group
- **Stop at checkpoints**: Validate story independently before proceeding
- **Performance**: Benchmark after US1 complete (T091)
- **Security**: Audit before final release (T092)

---

**Total Tasks**: 93
**MVP Tasks (US1)**: 19 contract/implementation + 19 foundational = 38 tasks
**Parallel Opportunities**: 42 tasks marked [P] across all phases
**Independent Stories**: US1, US2, US4 can start after Foundational; US3 depends on US1

**Constitution Compliance**: ✅ All 7 principles satisfied
- Test-first development enforced (contract tests before implementation)
- >80% coverage target (T086)
- Security built-in (password redaction, dangerous commands)
- Simple file-based approach (no complexity)
- MCP-first architecture (all 11 tools defined)
- Real-time monitoring (<500ms latency)
- Privacy by default (7-day retention, local storage)

**Ready for Implementation**: Run `uv run pytest` to begin TDD workflow 🚀
