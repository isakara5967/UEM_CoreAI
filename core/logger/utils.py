"""Utility functions for UEM Logger."""
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def generate_checksum(data: Dict[str, Any]) -> str:
    """Generate MD5 checksum for config/data."""
    json_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.md5(json_str.encode()).hexdigest()


def now_utc() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


def iso_now() -> str:
    """Get current UTC timestamp as ISO string."""
    return now_utc().isoformat()


def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp value to range."""
    return max(min_val, min(max_val, value))


def safe_json_dumps(data: Any) -> Optional[str]:
    """Safely convert to JSON string."""
    if data is None:
        return None
    try:
        return json.dumps(data, default=str)
    except (TypeError, ValueError):
        return None


def extract_denorm_fields(payload: Dict[str, Any], module_name: str) -> Dict[str, Any]:
    """Extract denormalized fields from payload based on module."""
    denorm = {}
    
    if module_name == "emotion":
        denorm["emotion_valence"] = payload.get("valence")
    
    elif module_name == "planner":
        denorm["action_name"] = payload.get("action") or payload.get("action_name")
    
    elif module_name == "ethmor":
        decision = payload.get("decision") or payload.get("intervention_type")
        denorm["ethmor_decision"] = decision
    
    elif module_name == "execution":
        denorm["success_flag_explicit"] = payload.get("success")
        denorm["cycle_time_ms"] = payload.get("duration_ms") or payload.get("cycle_time_ms")
    
    elif module_name == "perception":
        denorm["input_language"] = payload.get("language") or payload.get("input_language")
        denorm["input_quality_score"] = payload.get("quality_score") or payload.get("input_quality_score")
    
    return {k: v for k, v in denorm.items() if v is not None}


class MetricValidator:
    """Validates metric values against registry definitions."""
    
    # Cached registry
    _registry: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    async def load_registry(cls, db) -> None:
        """Load metric registry from database."""
        rows = await db.fetch("SELECT * FROM core.metric_registry")
        cls._registry = {r["metric_id"]: dict(r) for r in rows}
    
    @classmethod
    def validate(cls, metric_id: str, value: Any) -> bool:
        """Validate a metric value."""
        if metric_id not in cls._registry:
            return True  # Unknown metrics pass
        
        spec = cls._registry[metric_id]
        value_type = spec.get("value_type")
        
        if value is None:
            return True
        
        type_checks = {
            "float": lambda v: isinstance(v, (int, float)),
            "int": lambda v: isinstance(v, int),
            "text": lambda v: isinstance(v, str),
            "boolean": lambda v: isinstance(v, bool),
            "json": lambda v: isinstance(v, dict),
            "array": lambda v: isinstance(v, list),
            "enum": lambda v: isinstance(v, str),
        }
        
        checker = type_checks.get(value_type, lambda v: True)
        return checker(value)
    
    @classmethod
    def get_metric_info(cls, metric_id: str) -> Optional[Dict[str, Any]]:
        """Get metric definition."""
        return cls._registry.get(metric_id)
