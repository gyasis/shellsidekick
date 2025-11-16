"""Shared session state to avoid circular imports."""

from typing import Dict
from shellsidekick.core.patterns import PatternLearner

# In-memory session storage
# This module is imported by both session.py and detection.py
# to avoid circular import issues
active_sessions: Dict[str, "SessionMonitor"] = {}  # type: ignore

# Global pattern learner for all sessions
pattern_learner = PatternLearner()
