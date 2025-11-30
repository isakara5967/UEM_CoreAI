"""File-based fallback when database is unavailable."""
import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

logger = logging.getLogger("uem_logger.fallback")


class FallbackLogger:
    """Logs to JSON files when PostgreSQL is unavailable."""
    
    def __init__(self, fallback_dir: str = "data/fallback"):
        self.fallback_dir = Path(fallback_dir)
        self.fallback_dir.mkdir(parents=True, exist_ok=True)
        self._current_file: Optional[Path] = None
        self._event_buffer: List[Dict[str, Any]] = []
        self._buffer_size = 100
    
    def _get_file_path(self, run_id: str) -> Path:
        """Get fallback file path for a run."""
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        return self.fallback_dir / f"{run_id}_{date_str}.jsonl"
    
    def log_event(self, event_data: Dict[str, Any]) -> bool:
        """Log event to file."""
        try:
            event_data["_logged_at"] = datetime.now(timezone.utc).isoformat()
            
            run_id = event_data.get("run_id", "unknown")
            file_path = self._get_file_path(run_id)
            
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_data, default=str) + "\n")
            
            return True
        except Exception as e:
            logger.error(f"Fallback log failed: {e}")
            return False
    
    def log_events_batch(self, events: List[Dict[str, Any]]) -> int:
        """Log multiple events to file."""
        count = 0
        for event in events:
            if self.log_event(event):
                count += 1
        return count
    
    def read_fallback_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read events from fallback file."""
        events = []
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        return events
    
    def get_pending_files(self) -> List[Path]:
        """Get all pending fallback files."""
        return sorted(self.fallback_dir.glob("*.jsonl"))
    
    def mark_as_synced(self, file_path: Path) -> None:
        """Mark fallback file as synced (rename)."""
        synced_path = file_path.with_suffix(".synced")
        file_path.rename(synced_path)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get fallback stats."""
        pending = self.get_pending_files()
        total_events = 0
        for f in pending:
            total_events += sum(1 for _ in open(f))
        
        return {
            "pending_files": len(pending),
            "total_pending_events": total_events,
            "fallback_dir": str(self.fallback_dir),
        }
