"""
UEM Logger - PostgreSQL-based logging system for UEM_CoreAI
Version: 1.0 (Phase A + C)
"""

from .config import LoggerConfig
from .db import DatabaseManager, get_db_manager
from .runs import RunManager
from .cycles import CycleManager
from .events import EventLogger, EventData
from .fallback import FallbackLogger
from .logger import UEMLogger, get_logger
from .experiments import ExperimentRepository
from .config_snapshots import ConfigSnapshotRepository, generate_config_id, generate_checksum
from .utils import (
    generate_checksum as utils_checksum,
    now_utc,
    iso_now,
    clamp,
    safe_json_dumps,
    extract_denorm_fields,
    MetricValidator,
)

__version__ = "1.0.0"
__all__ = [
    # Config
    "LoggerConfig",
    # Database
    "DatabaseManager",
    "get_db_manager",
    # Managers
    "RunManager",
    "CycleManager",
    "EventLogger",
    "EventData",
    "FallbackLogger",
    # Main facade
    "UEMLogger",
    "get_logger",
    # Experiments & Config
    "ExperimentRepository",
    "ConfigSnapshotRepository",
    "generate_config_id",
    "generate_checksum",
    # Utils
    "now_utc",
    "iso_now",
    "clamp",
    "safe_json_dumps",
    "extract_denorm_fields",
    "MetricValidator",
]
