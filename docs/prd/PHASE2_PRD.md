# Product Requirements Document: ShellSidekick Phase 2
## Intelligent Event Detection & Smart Catch-Up System

**Version**: 2.0
**Date**: 2025-11-16
**Status**: Planning
**Previous Phase**: Phase 1 Complete (v0.1.0 - Session Monitoring & Prompt Detection)

---

## Executive Summary

Phase 2 transforms ShellSidekick from a **reactive prompt detector** into an **intelligent session assistant** that can catch up on events (errors, warnings, critical failures) while the AI is away, provide smart context based on event type, and avoid wasting tokens on repetitive content.

**Vision**: "Delayed broadcast" - The LLM doesn't need real-time monitoring. It can check in periodically and get a smart summary of what happened, focusing only on important events (prompts, errors, warnings) with relevant context.

### Key Capabilities (Phase 2)
1. **Multi-Event Detection**: Detect errors, warnings, critical failures (not just prompts)
2. **Smart Context Extraction**: Event-specific context (error = command+trace, prompt = interaction)
3. **Content Deduplication**: Don't re-send content the LLM has already seen
4. **Event Timeline**: Track what happened while LLM was away
5. **Severity-Based Filtering**: Skip LOW priority noise, focus on HIGH/CRITICAL events
6. **Smart Catch-Up Tool**: Single MCP tool for intelligent session updates

---

## Problem Statement

### Current Limitations (Phase 1)

**What Phase 1 Does Well**:
- ✅ Detects prompts (6 types: password, yes/no, path, choice, command, text)
- ✅ Incremental file reading (no data loss)
- ✅ Dangerous operation detection
- ✅ Pattern learning from user inputs
- ✅ 89% test coverage, production-ready

**What Phase 1 Misses**:
- ❌ **Only detects prompts** - Misses errors, warnings, critical failures
- ❌ **No event identifiers** - Can't tell LLM "you've seen this error before"
- ❌ **Fixed context window** - 3 lines regardless of event type
- ❌ **No deduplication** - Sends all new content, including repetitive logs
- ❌ **No timeline** - LLM can't ask "what happened in the last 5 minutes?"
- ❌ **No severity filtering** - All events treated equally

### Real-World Scenario

**Without Phase 2**:
```
User: "Monitor my deployment script"
AI: Starts monitoring...
[5 minutes pass - script outputs 1000 lines]
AI: Checks in
    → Gets 1000 lines of logs (99% noise)
    → Misses the error buried in line 847
    → Wastes tokens on "Processing file 1/100..." repeated 100 times
```

**With Phase 2**:
```
User: "Monitor my deployment script"
AI: Starts monitoring...
[5 minutes pass - script outputs 1000 lines]
AI: Calls smart_catchup(min_severity="MEDIUM")
    → Gets summary: "Processed 100 files, 2 warnings, 1 error"
    → Error: "Failed to connect to database" (with context)
    → Warning: "Deprecated API usage" (with context)
    → Skips repetitive "Processing..." logs
    → Uses 50 tokens instead of 5000
```

---

## User Stories

### Epic 1: Intelligent Event Detection

**US-201: Error Detection**
```
AS an AI assistant monitoring a terminal session
I WANT to detect errors, exceptions, and failures
SO THAT I can alert the user immediately when things go wrong

ACCEPTANCE CRITERIA:
- Detects "Error:", "Exception:", "Failed:", "Traceback"
- Detects "command not found", "permission denied"
- Assigns HIGH severity to errors
- Extracts error message and context
```

**US-202: Warning Detection**
```
AS an AI assistant
I WANT to detect warnings and notices
SO THAT I can inform users of potential issues

ACCEPTANCE CRITERIA:
- Detects "Warning:", "WARN:", "Deprecated:", "Notice:"
- Assigns MEDIUM severity to warnings
- Includes warning message and context
```

**US-203: Critical Event Detection**
```
AS an AI assistant
I WANT to detect critical failures and crashes
SO THAT I can prioritize urgent issues

ACCEPTANCE CRITERIA:
- Detects "CRITICAL:", "FATAL:", "PANIC:", "segmentation fault"
- Assigns CRITICAL severity
- Includes full crash context (stack trace, core dump info)
```

**US-204: Status Change Detection**
```
AS an AI assistant
I WANT to track state transitions
SO THAT I can understand session progress

ACCEPTANCE CRITERIA:
- Detects "Connecting...", "Connected", "Disconnected"
- Detects "Starting...", "Started", "Stopped"
- Assigns LOW-MEDIUM severity based on importance
```

---

### Epic 2: Smart Context Extraction

**US-205: Error Context Extraction**
```
AS an AI assistant analyzing an error
I WANT semantic context (command + output + error + trace)
SO THAT I can provide accurate troubleshooting advice

ACCEPTANCE CRITERIA:
- Extracts last command that caused error
- Includes full error message
- Includes stack trace (if present)
- Stops at semantic boundary (blank line or next command)
```

**US-206: Prompt Context Extraction**
```
AS an AI assistant responding to a prompt
I WANT recent interaction history
SO THAT my suggestions are contextually relevant

ACCEPTANCE CRITERIA:
- Includes last 10 lines or until previous prompt
- Includes user's recent commands
- Includes prompt question text
```

**US-207: Warning Context Extraction**
```
AS an AI assistant reviewing a warning
I WANT time-windowed context (last 1 minute of logs)
SO THAT I understand what led to the warning

ACCEPTANCE CRITERIA:
- Includes logs from last 60 seconds
- Includes related operations
- Stops at semantic boundary
```

---

### Epic 3: Content Deduplication

**US-208: Hash-Based Tracking**
```
AS an AI assistant
I WANT to track content I've already analyzed
SO THAT I don't waste tokens on repeated information

ACCEPTANCE CRITERIA:
- Generates SHA-256 hash of content chunks
- Stores sent hashes in memory
- Filters out previously-sent chunks
- Force-includes new events (even if similar)
```

**US-209: Repetitive Log Compression**
```
AS an AI assistant
I WANT repetitive logs compressed
SO THAT token usage is minimized

ACCEPTANCE CRITERIA:
- Detects patterns like "Processing file 1/100..."
- Compresses to summary: "[Processed 100 files (lines 1-100)]"
- Includes first/last occurrence for verification
```

---

### Epic 4: Event Timeline & Catch-Up

**US-210: Event Timeline Tracking**
```
AS an AI assistant
I WANT a timeline of important events
SO THAT I can catch up on what happened while I was idle

ACCEPTANCE CRITERIA:
- Stores all detected events with timestamps
- Tracks last LLM check-in time
- Filters events by time range
- Filters events by severity
```

**US-211: Smart Catch-Up Tool**
```
AS an AI assistant checking in after idle period
I WANT a smart summary of important events
SO THAT I can quickly understand session status

ACCEPTANCE CRITERIA:
- Returns events since last check-in
- Filters by minimum severity (default: MEDIUM)
- Limits to top N most important events
- Includes summary statistics
- Includes smart context for each event
- Marks content as "seen" to avoid repeats
```

**US-212: Severity-Based Filtering**
```
AS an AI assistant
I WANT to filter events by importance
SO THAT I focus on what matters

ACCEPTANCE CRITERIA:
- 4 severity levels: LOW, MEDIUM, HIGH, CRITICAL
- Can request only HIGH+ events
- Can request full history (all severities)
- Critical events always included
```

---

## Functional Requirements

### FR-201: Unified Event Model

**Description**: Create a unified event model that represents all types of events (prompts, errors, warnings, etc.)

**Specification**:
```python
class EventType(Enum):
    PROMPT = "prompt"           # User input needed
    ERROR = "error"             # Execution error
    WARNING = "warning"         # Non-fatal warning
    CRITICAL = "critical"       # Critical failure
    STATUS_CHANGE = "status"    # State transition

class Severity(Enum):
    LOW = 1       # Info, debug
    MEDIUM = 2    # Warnings, notices
    HIGH = 3      # Errors, prompts
    CRITICAL = 4  # Fatal errors, crashes

@dataclass
class Event:
    event_id: str                # UUID
    event_type: EventType
    severity: Severity
    timestamp: datetime
    file_position: int
    content: str                 # Matched text
    context: list[str]           # Smart context
    matched_pattern: str
    metadata: dict
```

**Priority**: HIGH
**Dependencies**: None

---

### FR-202: Multi-Pattern Event Detector

**Description**: Detect all event types using configurable regex patterns

**Specification**:
```python
class EventDetector:
    ERROR_PATTERNS = [
        (re.compile(r"error\s*:", re.I), Severity.HIGH),
        (re.compile(r"exception\s*:", re.I), Severity.HIGH),
        (re.compile(r"failed\s*:", re.I), Severity.HIGH),
        (re.compile(r"traceback", re.I), Severity.HIGH),
        (re.compile(r"command not found", re.I), Severity.MEDIUM),
        (re.compile(r"permission denied", re.I), Severity.HIGH),
    ]

    WARNING_PATTERNS = [
        (re.compile(r"warning\s*:", re.I), Severity.MEDIUM),
        (re.compile(r"warn\s*:", re.I), Severity.MEDIUM),
        (re.compile(r"deprecated", re.I), Severity.LOW),
    ]

    CRITICAL_PATTERNS = [
        (re.compile(r"critical\s*:", re.I), Severity.CRITICAL),
        (re.compile(r"fatal\s*:", re.I), Severity.CRITICAL),
        (re.compile(r"segmentation fault", re.I), Severity.CRITICAL),
    ]

    def detect_all(self, content: str, file_position: int) -> list[Event]:
        """Detect all events in content."""
```

**Priority**: HIGH
**Dependencies**: FR-201

---

### FR-203: Smart Context Extractor

**Description**: Extract event-specific context based on event type

**Specification**:
```python
class ContextBoundary(Enum):
    FIXED_LINES = "fixed"       # N lines before/after
    TIME_WINDOW = "time"        # Last N minutes
    SEMANTIC = "semantic"       # Until blank line or delimiter
    COMMAND_BLOCK = "command"   # Last command + output

class SmartContextExtractor:
    def extract_error_context(self, content: str, event: Event) -> str:
        # Find last command (backwards search for $ or #)
        # Include error message
        # Include stack trace (until blank line)
        return "$ command\n...output...\nError: message\nTraceback..."

    def extract_prompt_context(self, content: str, event: Event) -> str:
        # Include last 10 lines or until previous prompt
        return "...recent interaction...\nPrompt: ?"

    def extract_warning_context(self, content: str, event: Event) -> str:
        # Include last 60 seconds of logs
        return "...related logs...\nWarning: message"
```

**Priority**: MEDIUM
**Dependencies**: FR-201, FR-202

---

### FR-204: Content Deduplication System

**Description**: Track and filter content already sent to LLM

**Specification**:
```python
class ContentDeduplicator:
    def __init__(self):
        self.sent_hashes: Set[str] = set()

    def hash_content(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def is_new(self, content: str) -> bool:
        return self.hash_content(content) not in self.sent_hashes

    def mark_as_sent(self, content: str):
        self.sent_hashes.add(self.hash_content(content))

    def get_diff(self, new_content: str, force_events: list[Event]) -> str:
        # Split into chunks
        # Filter out seen chunks
        # Always include force_events
        return filtered_content
```

**Priority**: MEDIUM
**Dependencies**: FR-201

---

### FR-205: Event Timeline

**Description**: Maintain timeline of events for catch-up queries

**Specification**:
```python
class EventTimeline:
    def __init__(self):
        self.events: list[Event] = []
        self.last_llm_checkin: datetime = datetime.now()

    def add_event(self, event: Event):
        self.events.append(event)

    def get_events_since(
        self,
        since: datetime = None,
        min_severity: Severity = Severity.MEDIUM
    ) -> list[Event]:
        # Filter by timestamp and severity
        return filtered_events

    def get_summary(self, since: datetime = None) -> dict:
        return {
            "total_events": count,
            "by_type": {...},
            "by_severity": {...},
            "critical_events": [...],
        }
```

**Priority**: HIGH
**Dependencies**: FR-201

---

### FR-206: Smart Catch-Up MCP Tool

**Description**: Primary tool for delayed broadcast pattern

**Specification**:
```python
@mcp.tool()
def smart_catchup(
    session_id: str,
    since: str = None,           # ISO timestamp or "last_checkin"
    min_severity: str = "MEDIUM",
    include_context: bool = True,
    max_events: int = 20
) -> dict:
    """
    Returns:
        {
            "events": [Event],
            "summary": {
                "total_events": 15,
                "errors": 2,
                "warnings": 3,
                "prompts": 1
            },
            "new_content_hash": "abc123",
            "time_range": {...}
        }
    """
```

**Priority**: CRITICAL
**Dependencies**: FR-201, FR-202, FR-203, FR-204, FR-205

---

## Non-Functional Requirements

### NFR-201: Performance

**Requirement**: Event detection must complete within 500ms (same as Phase 1)

**Rationale**: Adding more event types shouldn't slow down detection

**Validation**:
- Unit tests: `test_detection_latency_all_events()`
- Performance threshold: <500ms for 10,000 lines with 50 events

---

### NFR-202: Memory Efficiency

**Requirement**: Event timeline storage ≤ 10MB per session for 24 hours

**Rationale**: Long-running sessions shouldn't consume excessive memory

**Calculation**:
- Average event: ~1KB (content + context + metadata)
- 10,000 events/day = ~10MB
- Acceptable for 24-hour retention

**Validation**:
- Memory profiling tests
- Automatic cleanup of old events (>24 hours)

---

### NFR-203: Deduplication Accuracy

**Requirement**: Hash collision rate < 0.001% for 10,000 chunks

**Rationale**: SHA-256 truncated to 16 chars is sufficient

**Validation**:
- Statistical tests with large datasets
- Collision detection in production logs

---

### NFR-204: Context Extraction Accuracy

**Requirement**: 95% accuracy for semantic context boundaries

**Rationale**: Context should include relevant information, not arbitrary cutoffs

**Validation**:
- Manual review of 100 error contexts
- User feedback metrics

---

## Technical Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ShellSidekick Phase 2                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │              MCP Tools Layer                       │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │  smart_catchup()                             │  │   │
│  │  │  - Get events since last check-in            │  │   │
│  │  │  - Filter by severity                        │  │   │
│  │  │  - Include smart context                     │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │  detect_events() [Enhanced]                  │  │   │
│  │  │  - Detect all event types                    │  │   │
│  │  │  - Return with severity                      │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │              Core Logic Layer                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │   │
│  │  │EventDetector │  │EventTimeline │  │Dedup     │ │   │
│  │  │- detect_all()│  │- add_event() │  │- is_new()│ │   │
│  │  │- patterns    │  │- get_since() │  │- mark()  │ │   │
│  │  └──────────────┘  └──────────────┘  └──────────┘ │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │  SmartContextExtractor                       │  │   │
│  │  │  - extract_error_context()                   │  │   │
│  │  │  - extract_prompt_context()                  │  │   │
│  │  │  - extract_warning_context()                 │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │              Data Models Layer                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │   │
│  │  │Event     │  │EventType │  │Severity          │ │   │
│  │  │          │  │Enum      │  │Enum              │ │   │
│  │  └──────────┘  └──────────┘  └──────────────────┘ │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### File Structure (New/Modified)

```
src/shellsidekick/
├── models/
│   ├── event.py                  # NEW: Event, EventType, Severity
│   └── prompt.py                 # EXISTING (no changes)
├── core/
│   ├── event_detector.py         # NEW: Multi-event detection
│   ├── context_extractor.py      # NEW: Smart context
│   ├── deduplicator.py           # NEW: Content dedup
│   ├── timeline.py               # NEW: Event timeline
│   ├── detector.py               # MODIFIED: Use Event model
│   └── monitor.py                # EXISTING (no changes)
└── mcp/tools/
    ├── catchup.py                # NEW: smart_catchup tool
    └── detection.py              # MODIFIED: Enhanced event detection
```

---

## Implementation Phases

### Phase 2A: Foundation (Days 1-3)

**Goal**: Unified event model and basic multi-event detection

**Tasks**:
1. Create `Event`, `EventType`, `Severity` models
2. Implement `EventDetector` with error/warning/critical patterns
3. Add unit tests for all event types (35 tests)
4. Update `PromptDetector` to use `Event` model

**Deliverables**:
- `src/shellsidekick/models/event.py`
- `src/shellsidekick/core/event_detector.py`
- `tests/unit/test_event_detector.py`
- All tests passing (211+ total)

**Success Criteria**:
- ✅ Detects 4+ error patterns
- ✅ Detects 3+ warning patterns
- ✅ Detects 3+ critical patterns
- ✅ Test coverage ≥ 85%

---

### Phase 2B: Smart Context (Days 4-5)

**Goal**: Event-specific context extraction

**Tasks**:
1. Implement `ContextBoundary` strategies
2. Create `SmartContextExtractor` with event-specific methods
3. Add tests for context extraction (20 tests)
4. Integrate with `EventDetector`

**Deliverables**:
- `src/shellsidekick/core/context_extractor.py`
- `tests/unit/test_context_extractor.py`
- All tests passing (231+ total)

**Success Criteria**:
- ✅ Error context includes command + trace
- ✅ Prompt context includes recent interaction
- ✅ Warning context includes time window
- ✅ 95% semantic boundary accuracy

---

### Phase 2C: Deduplication (Days 6-7)

**Goal**: Avoid re-sending content to LLM

**Tasks**:
1. Implement hash-based content tracking
2. Create `ContentDeduplicator` with diff logic
3. Add tests for deduplication (15 tests)
4. Integrate with session monitoring

**Deliverables**:
- `src/shellsidekick/core/deduplicator.py`
- `tests/unit/test_deduplicator.py`
- All tests passing (246+ total)

**Success Criteria**:
- ✅ Hash collision rate < 0.001%
- ✅ Correctly identifies new vs. seen content
- ✅ Force-includes important events

---

### Phase 2D: Event Timeline (Days 8-9)

**Goal**: Track events for catch-up queries

**Tasks**:
1. Create `EventTimeline` class
2. Add event tracking, filtering, summarization
3. Add tests for timeline (12 tests)
4. Integrate with all event detectors

**Deliverables**:
- `src/shellsidekick/core/timeline.py`
- `tests/unit/test_timeline.py`
- All tests passing (258+ total)

**Success Criteria**:
- ✅ Stores events with timestamps
- ✅ Filters by time range and severity
- ✅ Generates summary statistics
- ✅ Memory usage ≤ 10MB per session

---

### Phase 2E: Smart Catch-Up Tool (Days 10-12)

**Goal**: Primary MCP tool for delayed broadcast pattern

**Tasks**:
1. Implement `smart_catchup()` MCP tool
2. Integrate all components (detector, extractor, deduplicator, timeline)
3. Add comprehensive contract tests (25 tests)
4. Performance testing and optimization
5. Update documentation

**Deliverables**:
- `src/shellsidekick/mcp/tools/catchup.py`
- `tests/contract/test_catchup_tool.py`
- `tests/integration/test_smart_catchup.py`
- Updated `README.md` and `PHASE2_QUICKSTART.md`
- All tests passing (283+ total)

**Success Criteria**:
- ✅ Returns events since last check-in
- ✅ Filters by severity correctly
- ✅ Includes smart context
- ✅ Deduplicates content
- ✅ Generates accurate summary
- ✅ Detection latency < 500ms

---

## Testing Strategy

### Unit Tests (New: 82 tests)

**Event Detection** (35 tests):
- Error pattern detection (12 tests)
- Warning pattern detection (8 tests)
- Critical pattern detection (8 tests)
- Status change detection (7 tests)

**Context Extraction** (20 tests):
- Error context accuracy (8 tests)
- Prompt context accuracy (6 tests)
- Warning context accuracy (6 tests)

**Deduplication** (15 tests):
- Hash generation (3 tests)
- Content tracking (5 tests)
- Diff generation (4 tests)
- Edge cases (3 tests)

**Timeline** (12 tests):
- Event storage (3 tests)
- Time-based filtering (4 tests)
- Severity filtering (3 tests)
- Summary generation (2 tests)

### Contract Tests (New: 25 tests)

**smart_catchup Tool** (25 tests):
- Basic functionality (5 tests)
- Severity filtering (5 tests)
- Time range queries (5 tests)
- Context inclusion (5 tests)
- Edge cases (5 tests)

### Integration Tests (New: 10 tests)

**End-to-End Scenarios**:
- Error detection → catch-up (3 tests)
- Multi-event session (3 tests)
- Long-running session (2 tests)
- Deduplication accuracy (2 tests)

**Total Phase 2 Tests**: 117 new tests
**Total Project Tests**: 283+ tests

---

## Success Metrics

### Quantitative Metrics

| Metric | Phase 1 | Phase 2 Target |
|--------|---------|----------------|
| Event types detected | 6 (prompts only) | 20+ (all types) |
| Test coverage | 89% | ≥ 85% |
| Detection latency | <100ms | <500ms |
| Token efficiency | Baseline | 80% reduction for repetitive logs |
| Memory per session | 111KB | <10MB (for 24h) |

### Qualitative Metrics

**User Experience**:
- ✅ LLM can catch up on sessions without reading full logs
- ✅ Errors and warnings detected automatically
- ✅ Context is relevant and concise
- ✅ Repetitive logs compressed

**Developer Experience**:
- ✅ Easy to add new event patterns
- ✅ Clear separation of concerns
- ✅ Comprehensive test coverage
- ✅ Well-documented APIs

---

## Risks & Mitigations

### Risk 1: Pattern Coverage Gaps

**Risk**: Not all error/warning formats detected

**Impact**: HIGH
**Probability**: MEDIUM

**Mitigation**:
- Extensive testing with real-world logs
- User feedback for pattern refinement
- Easy pattern addition (just add regex to list)

---

### Risk 2: Context Extraction Accuracy

**Risk**: Semantic boundaries incorrectly detected

**Impact**: MEDIUM
**Probability**: MEDIUM

**Mitigation**:
- 95% accuracy threshold
- Manual review of 100 samples
- Fallback to fixed-line context if semantic fails

---

### Risk 3: Memory Growth

**Risk**: Event timeline grows unbounded

**Impact**: MEDIUM
**Probability**: LOW

**Mitigation**:
- 24-hour retention policy
- Automatic cleanup of old events
- Memory profiling in tests

---

### Risk 4: Hash Collisions

**Risk**: Deduplication incorrectly filters new content

**Impact**: HIGH
**Probability**: VERY LOW

**Mitigation**:
- SHA-256 (truncated to 16 chars)
- Collision rate < 0.001%
- Force-include important events (bypass dedup)

---

## Dependencies & Prerequisites

### Technical Dependencies

**New Python Packages**: None (all stdlib)

**Existing Dependencies**:
- FastMCP (already installed)
- pytest (already installed)

### Prerequisites

**Phase 1 Completion**:
- ✅ All 176 tests passing
- ✅ Core monitoring system working
- ✅ MCP integration tested
- ✅ Security audit complete

---

## Documentation Updates

### New Documentation

1. **Phase 2 Quickstart Guide**
   - How to use smart_catchup
   - Example workflows
   - Event severity guide

2. **Event Pattern Reference**
   - All supported patterns
   - How to add custom patterns
   - Severity assignment rules

3. **API Documentation**
   - EventDetector API
   - SmartContextExtractor API
   - ContentDeduplicator API
   - EventTimeline API

### Updated Documentation

1. **README.md**
   - Add Phase 2 features
   - Update usage examples

2. **MCP Tool Reference**
   - Add smart_catchup tool
   - Update detect_input_prompt tool

---

## Future Enhancements (Phase 3+)

### Phase 3: Advanced Features

**Compression & Summarization**:
- Automatic log summarization
- Repetitive pattern detection
- AI-powered event clustering

**Multi-Session Management**:
- Cross-session event correlation
- Fleet-wide monitoring
- Centralized event dashboard

**Custom Event Types**:
- User-defined patterns
- Application-specific events
- Domain-specific severity rules

### Phase 4: Production Hardening

**Performance Optimization**:
- Parallel event detection
- Incremental context extraction
- Streaming event processing

**Reliability Improvements**:
- Event persistence (disk storage)
- Crash recovery
- Event replay

---

## Appendix A: Event Pattern Catalog

### Error Patterns (12 patterns)

```python
ERROR_PATTERNS = [
    (re.compile(r"error\s*:", re.I), Severity.HIGH),
    (re.compile(r"exception\s*:", re.I), Severity.HIGH),
    (re.compile(r"failed\s*:", re.I), Severity.HIGH),
    (re.compile(r"failure\s*:", re.I), Severity.HIGH),
    (re.compile(r"traceback", re.I), Severity.HIGH),
    (re.compile(r"command not found", re.I), Severity.MEDIUM),
    (re.compile(r"permission denied", re.I), Severity.HIGH),
    (re.compile(r"access denied", re.I), Severity.HIGH),
    (re.compile(r"cannot\s+\w+", re.I), Severity.MEDIUM),
    (re.compile(r"unable to\s+\w+", re.I), Severity.MEDIUM),
    (re.compile(r"invalid\s+\w+", re.I), Severity.MEDIUM),
    (re.compile(r"not found\s*:", re.I), Severity.MEDIUM),
]
```

### Warning Patterns (8 patterns)

```python
WARNING_PATTERNS = [
    (re.compile(r"warning\s*:", re.I), Severity.MEDIUM),
    (re.compile(r"warn\s*:", re.I), Severity.MEDIUM),
    (re.compile(r"deprecated", re.I), Severity.LOW),
    (re.compile(r"notice\s*:", re.I), Severity.LOW),
    (re.compile(r"caution\s*:", re.I), Severity.MEDIUM),
    (re.compile(r"attention\s*:", re.I), Severity.MEDIUM),
    (re.compile(r"skipping\s+\w+", re.I), Severity.LOW),
    (re.compile(r"retrying\s+\w+", re.I), Severity.LOW),
]
```

### Critical Patterns (6 patterns)

```python
CRITICAL_PATTERNS = [
    (re.compile(r"critical\s*:", re.I), Severity.CRITICAL),
    (re.compile(r"fatal\s*:", re.I), Severity.CRITICAL),
    (re.compile(r"panic\s*:", re.I), Severity.CRITICAL),
    (re.compile(r"segmentation fault", re.I), Severity.CRITICAL),
    (re.compile(r"core dumped", re.I), Severity.CRITICAL),
    (re.compile(r"out of memory", re.I), Severity.CRITICAL),
]
```

---

## Appendix B: Smart Catch-Up Examples

### Example 1: Error Catch-Up

**Request**:
```python
smart_catchup(
    session_id="deploy-001",
    since="last_checkin",
    min_severity="HIGH"
)
```

**Response**:
```json
{
  "events": [
    {
      "event_id": "abc123",
      "event_type": "error",
      "severity": "HIGH",
      "timestamp": "2025-11-16T10:15:30",
      "content": "Error: Failed to connect to database",
      "context": [
        "$ python manage.py migrate",
        "Running migrations...",
        "Applying app.0001_initial...",
        "Error: Failed to connect to database",
        "  Connection refused (port 5432)"
      ]
    }
  ],
  "summary": {
    "total_events": 5,
    "errors": 1,
    "warnings": 2,
    "prompts": 0,
    "status_changes": 2
  }
}
```

### Example 2: Multi-Event Catch-Up

**Request**:
```python
smart_catchup(
    session_id="build-001",
    since="2025-11-16T10:00:00",
    min_severity="MEDIUM",
    max_events=10
)
```

**Response**:
```json
{
  "events": [
    {
      "event_type": "prompt",
      "severity": "HIGH",
      "content": "Continue with deployment? (yes/no):",
      "context": ["...recent build output..."]
    },
    {
      "event_type": "warning",
      "severity": "MEDIUM",
      "content": "Warning: Deprecated API usage",
      "context": ["...API call stack..."]
    },
    {
      "event_type": "error",
      "severity": "HIGH",
      "content": "Error: Test suite failed (3/100 tests)",
      "context": ["...test output..."]
    }
  ],
  "summary": {
    "total_events": 15,
    "errors": 1,
    "warnings": 4,
    "prompts": 1,
    "compressed_logs": "Built 47 files (lines 1-250)"
  }
}
```

---

## Approval & Sign-Off

**PRD Author**: AI Assistant (Claude Code)
**Date**: 2025-11-16

**Approvals Required**:
- [ ] Product Owner: User (gyasis)
- [ ] Tech Lead: User (gyasis)
- [ ] QA Lead: (Covered by automated tests)

**Status**: DRAFT - Awaiting approval

---

**Document Version**: 2.0
**Last Updated**: 2025-11-16
**Next Review**: Upon Phase 2 implementation start
