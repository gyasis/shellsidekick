"""Shared session state to avoid circular imports."""

from typing import TYPE_CHECKING, Dict

from shellsidekick.core.patterns import PatternLearner

if TYPE_CHECKING:
    from shellsidekick.core.monitor import SessionMonitor

# In-memory session storage
# This module is imported by both session.py and detection.py
# to avoid circular import issues
active_sessions: Dict[str, "SessionMonitor"] = {}

# Global pattern learner for all sessions
pattern_learner = PatternLearner()
