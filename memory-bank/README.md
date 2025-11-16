# Memory Bank - ShellSidekick Session Continuity

This folder contains structured documentation that enables seamless project continuation across sessions. Each file builds upon the others to provide complete context for AI assistants and developers joining the project.

## File Structure

### Core Files (Read in Order)

1. **projectbrief.md** - Foundation document
   - Project identity and purpose
   - One-line description
   - Target users and constraints
   - Current status snapshot

2. **productContext.md** - Why the project exists
   - Problems being solved
   - User value proposition
   - Market positioning
   - Key insights driving design

3. **activeContext.md** - Current work focus
   - What just happened (recent work)
   - What works right now
   - What's not done yet
   - Active considerations
   - Immediate next steps

4. **systemPatterns.md** - Architecture and technical decisions
   - High-level architecture
   - Design patterns used
   - Critical technical decisions
   - Data flow patterns
   - Error handling strategy

5. **techContext.md** - Technologies, setup, constraints
   - Technology stack
   - Project setup instructions
   - Development workflow
   - Platform constraints
   - Configuration options

6. **progress.md** - What works, what's left, current status
   - Phase-by-phase completion status
   - Implementation milestones
   - Test coverage summary
   - Performance benchmarks
   - Known issues and workarounds
   - Success metrics tracking

## How to Use This Documentation

### For AI Assistants Resuming Work

1. Read **projectbrief.md** first to understand project identity
2. Skim **productContext.md** to understand the "why"
3. Focus on **activeContext.md** to see current status and next steps
4. Reference **systemPatterns.md** when making architecture decisions
5. Use **techContext.md** for implementation details and setup
6. Check **progress.md** to understand what's complete and what's pending

### For New Developers

1. Start with **projectbrief.md** for quick orientation
2. Read **productContext.md** to understand user problems
3. Follow **techContext.md** setup instructions
4. Study **systemPatterns.md** to learn architecture
5. Check **progress.md** to see what's implemented
6. Review **activeContext.md** to find where to contribute

### For Project Resumption After Break

1. Jump to **activeContext.md** → "What Just Happened" section
2. Check **progress.md** → "Current Status" for completion level
3. Review **activeContext.md** → "Immediate Next Steps" for options
4. Reference other files as needed for technical details

## Document Hierarchy

```
projectbrief.md          ← Start here (Project identity)
    ↓
productContext.md        ← Why it exists (User problems)
    ↓
activeContext.md         ← Current focus (What's happening now)
    ↓
systemPatterns.md        ← How it works (Architecture)
    ↓
techContext.md           ← How to build it (Technologies)
    ↓
progress.md              ← What's done (Implementation status)
```

## Maintenance Guidelines

### When to Update

- **activeContext.md**: After every significant work session
- **progress.md**: When phases/milestones complete
- **systemPatterns.md**: When architectural decisions are made
- **techContext.md**: When dependencies or setup changes
- **productContext.md**: Rarely (only if user problems change)
- **projectbrief.md**: Rarely (only if project identity changes)

### Who Updates

- **Memory Bank Keeper Agent**: Exclusive editor of memory-bank folder
- **No other agents**: Should not modify memory-bank files directly
- **User**: Can review and approve updates

### Update Triggers

Automatic updates when:
- User explicitly mentions "memory-bank"
- Major milestones are reached
- Significant architecture changes
- New patterns or insights discovered
- Project resumption after break

## Current Project Status

**Phase**: Pattern Learning System (Phase 5) - COMPLETE
**Status**: Production-ready MVP
**Completion**: 75% (MVP features complete, history search optional)
**Test Coverage**: >80% for core modules
**MCP Tools**: 7 implemented
**Last Updated**: 2025-11-15

## Quick Reference

**Repository**: `/home/gyasis/Documents/code/shellsidekick`
**Branch**: `001-mcp-session-monitor`
**Language**: Python 3.11+
**Framework**: FastMCP
**Documentation**: `specs/001-mcp-session-monitor/`
**Constitution**: `.specify/memory/constitution.md`

## Related Documentation

- **Feature Spec**: `/specs/001-mcp-session-monitor/spec.md`
- **Implementation Plan**: `/specs/001-mcp-session-monitor/plan.md`
- **Task List**: `/specs/001-mcp-session-monitor/tasks.md`
- **Quick Start**: `/specs/001-mcp-session-monitor/quickstart.md`
- **Agent Context**: `/.claude/CLAUDE.md`
- **Constitution**: `/.specify/memory/constitution.md`

---

**Memory Bank Version**: 1.0
**Created**: 2025-11-15
**Total Documentation**: ~2000 lines across 6 core files
