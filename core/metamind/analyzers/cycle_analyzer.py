"""
MetaMind v1.9 - Micro Cycle Analyzer
====================================

Tek cycle seviyesinde analiz:
- Threshold ihlalleri
- Anomaly detection
- MetaEvent emission

Analiz türleri:
- Valence/arousal spike detection
- Failure streak alerts
- Performance anomalies
- Coherence drops
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

from ..types import (
    MetaEvent, MetaState, MetricsSnapshot,
    EventType, Severity
)

logger = logging.getLogger("UEM.MetaMind.CycleAnalyzer")


@dataclass
class ThresholdConfig:
    """Anomaly detection threshold'ları."""
    # Valence thresholds
    valence_spike_positive: float = 0.8    # Ani pozitif spike
    valence_spike_negative: float = -0.8   # Ani negatif spike
    valence_change_threshold: float = 0.5  # Tek cycle'da değişim
    
    # Arousal thresholds
    arousal_high: float = 0.9
    arousal_low: float = 0.1
    arousal_change_threshold: float = 0.4
    
    # Performance thresholds
    cycle_time_warning_ms: float = 50.0
    cycle_time_critical_ms: float = 100.0
    
    # Coherence thresholds
    coherence_warning: float = 0.4
    coherence_critical: float = 0.2
    
    # Failure thresholds
    failure_streak_warning: int = 3
    failure_streak_critical: int = 5
    
    # Meta-state thresholds
    global_health_warning: float = 0.4
    global_health_critical: float = 0.2
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'ThresholdConfig':
        """Config dict'ten oluştur."""
        thresholds = config.get('thresholds', {})
        return cls(
            valence_spike_positive=thresholds.get('valence_spike_positive', 0.8),
            valence_spike_negative=thresholds.get('valence_spike_negative', -0.8),
            valence_change_threshold=thresholds.get('valence_change_threshold', 0.5),
            arousal_high=thresholds.get('arousal_high', 0.9),
            arousal_low=thresholds.get('arousal_low', 0.1),
            coherence_warning=thresholds.get('coherence_warning', 0.4),
            coherence_critical=thresholds.get('coherence_critical', 0.2),
            failure_streak_warning=thresholds.get('failure_streak_warning', 3),
            failure_streak_critical=thresholds.get('failure_streak_critical', 5),
            global_health_warning=thresholds.get('global_health_warning', 0.4),
            global_health_critical=thresholds.get('global_health_critical', 0.2),
        )


@dataclass
class AnomalyResult:
    """Tek bir anomaly sonucu."""
    anomaly_type: str
    severity: str
    message: str
    value: float
    threshold: float
    data: Dict[str, Any] = field(default_factory=dict)


class MicroCycleAnalyzer:
    """
    Tek cycle seviyesinde analiz.
    
    Her cycle'da:
    1. Threshold kontrolleri
    2. Değişim oranı kontrolü
    3. Anomaly detection
    4. MetaEvent emission
    
    Kullanım:
        analyzer = MicroCycleAnalyzer(thresholds, on_event=callback)
        anomalies = analyzer.analyze(cycle_data, snapshot, meta_state, cycle_id)
    """
    
    def __init__(
        self,
        thresholds: Optional[ThresholdConfig] = None,
        on_event: Optional[Callable[[MetaEvent], None]] = None,
    ):
        """
        Args:
            thresholds: ThresholdConfig instance
            on_event: Callback for emitted events
        """
        self.thresholds = thresholds or ThresholdConfig()
        self.on_event = on_event
        
        # History for change detection
        self._prev_valence: Optional[float] = None
        self._prev_arousal: Optional[float] = None
        self._prev_coherence: Optional[float] = None
        
        # Run context
        self._run_id: Optional[str] = None
        self._episode_id: Optional[str] = None
        
        logger.debug("MicroCycleAnalyzer initialized")
    
    def set_context(self, run_id: str, episode_id: Optional[str] = None) -> None:
        """Run context ayarla."""
        self._run_id = run_id
        self._episode_id = episode_id
    
    def analyze(
        self,
        cycle_data: Dict[str, Any],
        snapshot: Optional[MetricsSnapshot] = None,
        meta_state: Optional[MetaState] = None,
        cycle_id: int = 0,
    ) -> List[AnomalyResult]:
        """
        Tek cycle analiz et.
        
        Args:
            cycle_data: Raw cycle verileri
            snapshot: MetricsSnapshot (from adapter)
            meta_state: Current MetaState
            cycle_id: Cycle number
            
        Returns:
            List of detected anomalies
        """
        anomalies: List[AnomalyResult] = []
        
        # Valence analizi
        valence = cycle_data.get('valence', 0.0)
        anomalies.extend(self._check_valence(valence, cycle_id))
        
        # Arousal analizi
        arousal = cycle_data.get('arousal', 0.0)
        anomalies.extend(self._check_arousal(arousal, cycle_id))
        
        # Performance analizi
        cycle_time = cycle_data.get('cycle_time_ms', 0.0)
        anomalies.extend(self._check_performance(cycle_time, cycle_id))
        
        # Snapshot analizi
        if snapshot:
            anomalies.extend(self._check_snapshot(snapshot, cycle_id))
        
        # MetaState analizi
        if meta_state:
            anomalies.extend(self._check_meta_state(meta_state, cycle_id))
        
        # History güncelle
        self._prev_valence = valence
        self._prev_arousal = arousal
        if snapshot:
            self._prev_coherence = snapshot.coherence_score
        
        # Emit events
        for anomaly in anomalies:
            self._emit_event(anomaly, cycle_id)
        
        if anomalies:
            logger.debug(f"Cycle {cycle_id}: {len(anomalies)} anomalies detected")
        
        return anomalies
    
    def _check_valence(self, valence: float, cycle_id: int) -> List[AnomalyResult]:
        """Valence threshold kontrolü."""
        anomalies = []
        
        # Spike detection
        if valence >= self.thresholds.valence_spike_positive:
            anomalies.append(AnomalyResult(
                anomaly_type="valence_spike_positive",
                severity=Severity.INFO.value,
                message=f"Positive valence spike: {valence:.2f}",
                value=valence,
                threshold=self.thresholds.valence_spike_positive,
            ))
        elif valence <= self.thresholds.valence_spike_negative:
            anomalies.append(AnomalyResult(
                anomaly_type="valence_spike_negative",
                severity=Severity.WARNING.value,
                message=f"Negative valence spike: {valence:.2f}",
                value=valence,
                threshold=self.thresholds.valence_spike_negative,
            ))
        
        # Change detection
        if self._prev_valence is not None:
            change = abs(valence - self._prev_valence)
            if change >= self.thresholds.valence_change_threshold:
                anomalies.append(AnomalyResult(
                    anomaly_type="valence_rapid_change",
                    severity=Severity.INFO.value,
                    message=f"Rapid valence change: {self._prev_valence:.2f} → {valence:.2f}",
                    value=change,
                    threshold=self.thresholds.valence_change_threshold,
                    data={'prev': self._prev_valence, 'curr': valence},
                ))
        
        return anomalies
    
    def _check_arousal(self, arousal: float, cycle_id: int) -> List[AnomalyResult]:
        """Arousal threshold kontrolü."""
        anomalies = []
        
        # High arousal
        if arousal >= self.thresholds.arousal_high:
            anomalies.append(AnomalyResult(
                anomaly_type="arousal_high",
                severity=Severity.INFO.value,
                message=f"High arousal: {arousal:.2f}",
                value=arousal,
                threshold=self.thresholds.arousal_high,
            ))
        
        # Low arousal (potential disengagement)
        if arousal <= self.thresholds.arousal_low:
            anomalies.append(AnomalyResult(
                anomaly_type="arousal_low",
                severity=Severity.INFO.value,
                message=f"Low arousal: {arousal:.2f}",
                value=arousal,
                threshold=self.thresholds.arousal_low,
            ))
        
        # Change detection
        if self._prev_arousal is not None:
            change = abs(arousal - self._prev_arousal)
            if change >= self.thresholds.arousal_change_threshold:
                anomalies.append(AnomalyResult(
                    anomaly_type="arousal_rapid_change",
                    severity=Severity.INFO.value,
                    message=f"Rapid arousal change: {self._prev_arousal:.2f} → {arousal:.2f}",
                    value=change,
                    threshold=self.thresholds.arousal_change_threshold,
                ))
        
        return anomalies
    
    def _check_performance(self, cycle_time_ms: float, cycle_id: int) -> List[AnomalyResult]:
        """Performance threshold kontrolü."""
        anomalies = []
        
        if cycle_time_ms >= self.thresholds.cycle_time_critical_ms:
            anomalies.append(AnomalyResult(
                anomaly_type="cycle_time_critical",
                severity=Severity.CRITICAL.value,
                message=f"Critical cycle time: {cycle_time_ms:.1f}ms",
                value=cycle_time_ms,
                threshold=self.thresholds.cycle_time_critical_ms,
            ))
        elif cycle_time_ms >= self.thresholds.cycle_time_warning_ms:
            anomalies.append(AnomalyResult(
                anomaly_type="cycle_time_warning",
                severity=Severity.WARNING.value,
                message=f"Slow cycle time: {cycle_time_ms:.1f}ms",
                value=cycle_time_ms,
                threshold=self.thresholds.cycle_time_warning_ms,
            ))
        
        return anomalies
    
    def _check_snapshot(self, snapshot: MetricsSnapshot, cycle_id: int) -> List[AnomalyResult]:
        """MetricsSnapshot kontrolü."""
        anomalies = []
        
        # Coherence check
        if snapshot.coherence_score <= self.thresholds.coherence_critical:
            anomalies.append(AnomalyResult(
                anomaly_type="coherence_critical",
                severity=Severity.CRITICAL.value,
                message=f"Critical coherence: {snapshot.coherence_score:.2f}",
                value=snapshot.coherence_score,
                threshold=self.thresholds.coherence_critical,
            ))
        elif snapshot.coherence_score <= self.thresholds.coherence_warning:
            anomalies.append(AnomalyResult(
                anomaly_type="coherence_warning",
                severity=Severity.WARNING.value,
                message=f"Low coherence: {snapshot.coherence_score:.2f}",
                value=snapshot.coherence_score,
                threshold=self.thresholds.coherence_warning,
            ))
        
        # Failure streak check
        if snapshot.failure_streak >= self.thresholds.failure_streak_critical:
            anomalies.append(AnomalyResult(
                anomaly_type="failure_streak_critical",
                severity=Severity.CRITICAL.value,
                message=f"Critical failure streak: {snapshot.failure_streak}",
                value=float(snapshot.failure_streak),
                threshold=float(self.thresholds.failure_streak_critical),
            ))
        elif snapshot.failure_streak >= self.thresholds.failure_streak_warning:
            anomalies.append(AnomalyResult(
                anomaly_type="failure_streak_warning",
                severity=Severity.WARNING.value,
                message=f"Failure streak: {snapshot.failure_streak}",
                value=float(snapshot.failure_streak),
                threshold=float(self.thresholds.failure_streak_warning),
            ))
        
        # Critical alerts from alert manager
        if snapshot.critical_alerts > 0:
            anomalies.append(AnomalyResult(
                anomaly_type="critical_alerts",
                severity=Severity.CRITICAL.value,
                message=f"Critical alerts: {snapshot.critical_alerts}",
                value=float(snapshot.critical_alerts),
                threshold=0.0,
            ))
        
        return anomalies
    
    def _check_meta_state(self, meta_state: MetaState, cycle_id: int) -> List[AnomalyResult]:
        """MetaState kontrolü."""
        anomalies = []
        
        # Global health check
        health = meta_state.global_cognitive_health.value
        if health <= self.thresholds.global_health_critical:
            anomalies.append(AnomalyResult(
                anomaly_type="global_health_critical",
                severity=Severity.CRITICAL.value,
                message=f"Critical global health: {health:.2f}",
                value=health,
                threshold=self.thresholds.global_health_critical,
            ))
        elif health <= self.thresholds.global_health_warning:
            anomalies.append(AnomalyResult(
                anomaly_type="global_health_warning",
                severity=Severity.WARNING.value,
                message=f"Low global health: {health:.2f}",
                value=health,
                threshold=self.thresholds.global_health_warning,
            ))
        
        # Low confidence warnings
        low_conf = meta_state.get_low_confidence_metrics(0.5)
        if low_conf:
            anomalies.append(AnomalyResult(
                anomaly_type="low_confidence_metrics",
                severity=Severity.INFO.value,
                message=f"Low confidence metrics: {', '.join(low_conf)}",
                value=len(low_conf),
                threshold=0.0,
                data={'metrics': low_conf},
            ))
        
        return anomalies
    
    def _emit_event(self, anomaly: AnomalyResult, cycle_id: int) -> None:
        """Anomaly'den MetaEvent oluştur ve emit et."""
        event = MetaEvent(
            event_type=EventType.ANOMALY.value,
            severity=anomaly.severity,
            source="cycle_analyzer",
            message=anomaly.message,
            run_id=self._run_id,
            cycle_id=cycle_id,
            episode_id=self._episode_id,
            data={
                'anomaly_type': anomaly.anomaly_type,
                'value': anomaly.value,
                'threshold': anomaly.threshold,
                **anomaly.data,
            },
        )
        
        if self.on_event:
            try:
                self.on_event(event)
            except Exception as e:
                logger.error(f"Event callback failed: {e}")
    
    def reset(self) -> None:
        """Analyzer state sıfırla."""
        self._prev_valence = None
        self._prev_arousal = None
        self._prev_coherence = None
        logger.debug("CycleAnalyzer reset")


# ============================================================
# FACTORY
# ============================================================

def create_cycle_analyzer(
    config: Optional[Dict[str, Any]] = None,
    on_event: Optional[Callable[[MetaEvent], None]] = None,
) -> MicroCycleAnalyzer:
    """Factory function."""
    thresholds = ThresholdConfig.from_dict(config or {})
    return MicroCycleAnalyzer(thresholds=thresholds, on_event=on_event)


__all__ = ['MicroCycleAnalyzer', 'ThresholdConfig', 'AnomalyResult', 'create_cycle_analyzer']
