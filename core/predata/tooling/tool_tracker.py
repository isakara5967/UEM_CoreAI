"""Tool usage tracking."""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ToolStatus(Enum):
    """Tool execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"


@dataclass
class ToolUsage:
    """Record of a single tool usage."""
    tool_name: str
    status: ToolStatus = ToolStatus.PENDING
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "error": self.error,
        }


class ToolTracker:
    """
    Tracks tool usage during cognitive cycles.
    
    Usage:
        tracker = ToolTracker()
        tracker.start_tool("web_search")
        # ... tool executes ...
        tracker.end_tool("web_search", success=True)
        summary = tracker.get_summary()
    """
    
    def __init__(self):
        self._active_tools: Dict[str, ToolUsage] = {}
        self._completed: List[ToolUsage] = []
        self._cycle_tools: List[ToolUsage] = []
    
    def start_tool(self, tool_name: str, input_summary: Optional[str] = None) -> None:
        """Mark tool as started."""
        usage = ToolUsage(
            tool_name=tool_name,
            status=ToolStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            input_summary=input_summary,
        )
        self._active_tools[tool_name] = usage
    
    def end_tool(
        self,
        tool_name: str,
        success: bool = True,
        output_summary: Optional[str] = None,
        error: Optional[str] = None
    ) -> Optional[ToolUsage]:
        """Mark tool as completed."""
        if tool_name not in self._active_tools:
            return None
        
        usage = self._active_tools.pop(tool_name)
        usage.ended_at = datetime.now(timezone.utc)
        usage.status = ToolStatus.SUCCESS if success else ToolStatus.FAILED
        usage.output_summary = output_summary
        usage.error = error
        
        if usage.started_at and usage.ended_at:
            delta = usage.ended_at - usage.started_at
            usage.duration_ms = delta.total_seconds() * 1000
        
        self._completed.append(usage)
        self._cycle_tools.append(usage)
        return usage
    
    def block_tool(self, tool_name: str, reason: str) -> ToolUsage:
        """Record a blocked tool attempt."""
        usage = ToolUsage(
            tool_name=tool_name,
            status=ToolStatus.BLOCKED,
            error=reason,
        )
        self._completed.append(usage)
        self._cycle_tools.append(usage)
        return usage
    
    def get_summary(self) -> Dict[str, Any]:
        """Get tool usage summary for current cycle."""
        if not self._cycle_tools:
            return {"tools_used": 0, "tools": []}
        
        success_count = sum(1 for t in self._cycle_tools if t.status == ToolStatus.SUCCESS)
        failed_count = sum(1 for t in self._cycle_tools if t.status == ToolStatus.FAILED)
        blocked_count = sum(1 for t in self._cycle_tools if t.status == ToolStatus.BLOCKED)
        
        total_time = sum(t.duration_ms or 0 for t in self._cycle_tools)
        
        tool_names = list(set(t.tool_name for t in self._cycle_tools))
        
        return {
            "tools_used": len(self._cycle_tools),
            "unique_tools": tool_names,
            "success_count": success_count,
            "failed_count": failed_count,
            "blocked_count": blocked_count,
            "total_time_ms": total_time,
            "tools": [t.to_dict() for t in self._cycle_tools],
        }
    
    def reset_cycle(self) -> Dict[str, Any]:
        """Reset cycle tracking and return summary."""
        summary = self.get_summary()
        self._cycle_tools = []
        return summary
    
    def get_all_completed(self) -> List[ToolUsage]:
        """Get all completed tool usages."""
        return self._completed.copy()
