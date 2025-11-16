# ShellSidekick Project Brief

## Project Identity

**Name**: ShellSidekick
**Type**: MCP Server (Model Context Protocol)
**Primary Language**: Python 3.11+
**Framework**: FastMCP
**Repository**: `/home/gyasis/Documents/code/shellsidekick`
**Current Branch**: `001-mcp-session-monitor`

## One-Line Description

AI-powered terminal session monitoring via MCP that enables real-time prompt detection, context-aware suggestions, and pattern learning for SSH sessions, interactive scripts, and database CLIs.

## Project Purpose

ShellSidekick provides AI assistants with the ability to "pair program" during terminal sessions by monitoring session output, detecting when the terminal is waiting for input, and suggesting appropriate responses based on context and learned patterns. This creates an "AI looking over your shoulder" experience during complex interactive operations like deployments, database migrations, and system administration tasks.

## Core Value Proposition

- **Real-time Awareness**: AI assistants can see what's happening in terminal sessions without breaking user flow
- **Intelligent Detection**: Pattern-based prompt detection (<500ms latency) for passwords, confirmations, paths, and dangerous operations
- **Context-Aware Help**: Suggests appropriate inputs with safety warnings for destructive operations
- **Pattern Learning**: Learns from user behavior to provide personalized suggestions over time
- **Privacy First**: All data stays local, password redaction, secure file permissions, automatic cleanup

## Target Users

- **DevOps Engineers**: Deploying to production, managing infrastructure
- **Database Administrators**: Running migrations, managing schemas
- **System Administrators**: SSH sessions, configuration management
- **Developers**: Interactive debugging, deployment scripts

## Key Constraints

- Unix-like environments only (Linux, macOS, WSL)
- File-based monitoring (via `script` or `tmux`)
- No automatic command injection (security requirement)
- 7-day default retention with automatic cleanup
- <50MB memory per session, <500ms detection latency
- Test-first development (TDD mandatory)

## Success Metrics

- >85% prompt detection accuracy
- <500ms detection latency (currently: ~67ms)
- >10,000 lines/second throughput
- 70% suggestion acceptance rate
- Zero data loss incidents
- Support 10 concurrent sessions without performance degradation

## Project Status

**Phase 5 Complete**: Pattern Learning System
**Implementation Level**: Production-ready MVP
**Test Coverage**: >80% for core modules
**MCP Tools**: 7 tools implemented (3 session management, 2 detection, 2 pattern learning)
