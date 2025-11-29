"""
UEM Logger - PostgreSQL-based logging system for UEM_CoreAI
Version: 1.0 (Phase A)
"""

from .config import LoggerConfig
from .db import DatabaseManager, get_db_manager
from .runs import RunManager
from .cycles import CycleManager
from .events import EventLogger, EventData
from .fallback import FallbackLogger

__version__ = "1.0.0"
__all__ = [
    "LoggerConfig",
    "DatabaseManager",
    "get_db_manager",
    "RunManager",
    "CycleManager",
    "EventLogger",
    "EventData",
    "FallbackLogger",
]
