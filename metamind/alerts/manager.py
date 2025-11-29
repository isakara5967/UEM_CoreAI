"""Alert management system."""
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertCategory(Enum):
    """Alert categories."""
    STABILITY = "stability"      # Failure streaks, crashes
    PERFORMANCE = "performance"  # Slow cycles, inefficiency
    QUALITY = "quality"          # Low coherence, poor outcomes
    POLICY = "policy"            # ETHMOR blocks, violations
    ANOMALY = "anomaly"          # Unusual patterns
    RESOURCE = "resource"        # Memory, tool issues


@dataclass
class Alert:
    """An alert instance."""
    alert_id: str
    alert_type: str
    severity: AlertSeverity
    category: AlertCategory
    message: str
    run_id: Optional[str] = None
    cycle_id: Optional[int] = None
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)
    created_ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "run_id": self.run_id,
            "cycle_id": self.cycle_id,
            "threshold_value": self.threshold_value,
            "actual_value": self.actual_value,
            "context": self.context,
            "created_ts": self.created_ts.isoformat(),
            "acknowledged": self.acknowledged,
            "resolved": self.resolved,
        }


@dataclass
class AlertThreshold:
    """Threshold configuration for alerts."""
    alert_type: str
    metric_name: str
    threshold: float
    comparison: str  # "gt", "lt", "gte", "lte", "eq"
    severity: AlertSeverity
    category: AlertCategory
    message_template: str
    cooldown_cycles: int = 5  # Don't re-alert within N cycles


class AlertManager:
    """
    Manages alert generation, lifecycle, and notifications.
    
    Usage:
        manager = AlertManager()
        manager.register_threshold(AlertThreshold(...))
        alerts = manager.check(cycle_data)
    """
    
    # Default thresholds
    DEFAULT_THRESHOLDS = [
        AlertThreshold(
            alert_type="high_failure_streak",
            metric_name="failure_streak",
            threshold=5,
            comparison="gte",
            severity=AlertSeverity.WARNING,
            category=AlertCategory.STABILITY,
            message_template="Failure streak reached {actual_value} (threshold: {threshold})"
        ),
        AlertThreshold(
            alert_type="critical_failure_streak",
            metric_name="failure_streak",
            threshold=10,
            comparison="gte",
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.STABILITY,
            message_template="Critical failure streak: {actual_value} consecutive failures"
        ),
        AlertThreshold(
            alert_type="low_coherence",
            metric_name="coherence_score",
            threshold=0.3,
            comparison="lt",
            severity=AlertSeverity.WARNING,
            category=AlertCategory.QUALITY,
            message_template="Low coherence score: {actual_value:.2f} (threshold: {threshold})"
        ),
        AlertThreshold(
            alert_type="high_ethmor_block_rate",
            metric_name="ethmor_block_rate",
            threshold=0.5,
            comparison="gt",
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.POLICY,
            message_template="High ETHMOR block rate: {actual_value:.1%} of actions blocked"
        ),
        AlertThreshold(
            alert_type="slow_cycle",
            metric_name="cycle_time_ms",
            threshold=500,
            comparison="gt",
            severity=AlertSeverity.WARNING,
            category=AlertCategory.PERFORMANCE,
            message_template="Slow cycle detected: {actual_value:.0f}ms (threshold: {threshold}ms)"
        ),
        AlertThreshold(
            alert_type="very_slow_cycle",
            metric_name="cycle_time_ms",
            threshold=2000,
            comparison="gt",
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.PERFORMANCE,
            message_template="Very slow cycle: {actual_value:.0f}ms"
        ),
        AlertThreshold(
            alert_type="low_efficiency",
            metric_name="efficiency_score",
            threshold=0.3,
            comparison="lt",
            severity=AlertSeverity.WARNING,
            category=AlertCategory.PERFORMANCE,
            message_template="Low efficiency: {actual_value:.2f}"
        ),
        AlertThreshold(
            alert_type="high_adversarial",
            metric_name="adversarial_input_score",
            threshold=0.7,
            comparison="gt",
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.POLICY,
            message_template="High adversarial input score: {actual_value:.2f}"
        ),
        AlertThreshold(
            alert_type="action_stuck",
            metric_name="repeated_action_flag",
            threshold=1,
            comparison="eq",
            severity=AlertSeverity.WARNING,
            category=AlertCategory.ANOMALY,
            message_template="Agent appears stuck repeating same action"
        ),
    ]
    
    def __init__(self, use_defaults: bool = True):
        self._thresholds: Dict[str, AlertThreshold] = {}
        self._alerts: List[Alert] = []
        self._active_alerts: Dict[str, Alert] = {}
        self._cooldowns: Dict[str, int] = {}  # alert_type -> cycles until can fire again
        self._current_cycle = 0
        self._callbacks: List[Callable[[Alert], None]] = []
        
        if use_defaults:
            for threshold in self.DEFAULT_THRESHOLDS:
                self.register_threshold(threshold)
    
    def register_threshold(self, threshold: AlertThreshold) -> None:
        """Register an alert threshold."""
        self._thresholds[threshold.alert_type] = threshold
    
    def register_callback(self, callback: Callable[[Alert], None]) -> None:
        """Register callback for new alerts."""
        self._callbacks.append(callback)
    
    def check(
        self,
        metrics: Dict[str, Any],
        run_id: Optional[str] = None,
        cycle_id: Optional[int] = None
    ) -> List[Alert]:
        """Check metrics against thresholds and generate alerts."""
        self._current_cycle = cycle_id or self._current_cycle + 1
        new_alerts = []
        
        # Decrement cooldowns
        expired = [k for k, v in self._cooldowns.items() if v <= 0]
        for k in expired:
            del self._cooldowns[k]
        for k in self._cooldowns:
            self._cooldowns[k] -= 1
        
        for alert_type, threshold in self._thresholds.items():
            # Skip if in cooldown
            if alert_type in self._cooldowns:
                continue
            
            # Get metric value
            value = metrics.get(threshold.metric_name)
            if value is None:
                continue
            
            # Check threshold
            triggered = self._check_threshold(value, threshold.threshold, threshold.comparison)
            
            if triggered:
                alert = self._create_alert(
                    threshold=threshold,
                    actual_value=value,
                    run_id=run_id,
                    cycle_id=cycle_id,
                    context=metrics
                )
                
                new_alerts.append(alert)
                self._alerts.append(alert)
                self._active_alerts[alert.alert_id] = alert
                self._cooldowns[alert_type] = threshold.cooldown_cycles
                
                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback(alert)
                    except Exception:
                        pass
        
        return new_alerts
    
    def _check_threshold(self, value: float, threshold: float, comparison: str) -> bool:
        """Check if value triggers threshold."""
        if comparison == "gt":
            return value > threshold
        elif comparison == "lt":
            return value < threshold
        elif comparison == "gte":
            return value >= threshold
        elif comparison == "lte":
            return value <= threshold
        elif comparison == "eq":
            return value == threshold
        return False
    
    def _create_alert(
        self,
        threshold: AlertThreshold,
        actual_value: float,
        run_id: Optional[str],
        cycle_id: Optional[int],
        context: Dict[str, Any]
    ) -> Alert:
        """Create an alert instance."""
        message = threshold.message_template.format(
            actual_value=actual_value,
            threshold=threshold.threshold
        )
        
        return Alert(
            alert_id=f"alert_{uuid.uuid4().hex[:12]}",
            alert_type=threshold.alert_type,
            severity=threshold.severity,
            category=threshold.category,
            message=message,
            run_id=run_id,
            cycle_id=cycle_id,
            threshold_value=threshold.threshold,
            actual_value=actual_value,
            context={k: v for k, v in context.items() if k != threshold.metric_name}
        )
    
    def acknowledge(self, alert_id: str, by: str = "system") -> bool:
        """Acknowledge an alert."""
        if alert_id in self._active_alerts:
            alert = self._active_alerts[alert_id]
            alert.acknowledged = True
            alert.acknowledged_by = by
            alert.acknowledged_at = datetime.now(timezone.utc)
            return True
        return False
    
    def resolve(self, alert_id: str) -> bool:
        """Resolve an alert."""
        if alert_id in self._active_alerts:
            alert = self._active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now(timezone.utc)
            del self._active_alerts[alert_id]
            return True
        return False
    
    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        category: Optional[AlertCategory] = None
    ) -> List[Alert]:
        """Get active (unresolved) alerts."""
        alerts = list(self._active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if category:
            alerts = [a for a in alerts if a.category == category]
        
        # Sort by severity (critical first)
        severity_order = {AlertSeverity.CRITICAL: 0, AlertSeverity.WARNING: 1, AlertSeverity.INFO: 2}
        return sorted(alerts, key=lambda a: severity_order.get(a.severity, 3))
    
    def get_alert_counts(self) -> Dict[str, int]:
        """Get count of alerts by severity."""
        counts = {"critical": 0, "warning": 0, "info": 0, "total": 0}
        
        for alert in self._active_alerts.values():
            counts[alert.severity.value] += 1
            counts["total"] += 1
        
        return counts
    
    def get_all_alerts(self, limit: int = 100) -> List[Alert]:
        """Get all alerts (including resolved)."""
        return self._alerts[-limit:]
    
    def clear_resolved(self) -> int:
        """Clear resolved alerts from history."""
        before = len(self._alerts)
        self._alerts = [a for a in self._alerts if not a.resolved]
        return before - len(self._alerts)
    
    def reset(self) -> None:
        """Reset alert manager."""
        self._alerts.clear()
        self._active_alerts.clear()
        self._cooldowns.clear()
        self._current_cycle = 0
