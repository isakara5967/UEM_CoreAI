"""
MetaMind v1.9 - Domain Types
============================

Bu modül MetaMind'ın temel veri yapılarını tanımlar:
- MetaEvent: Anomali, threshold ihlali, pattern tespiti
- MetaPattern: Aksiyon dizileri, duygu döngüleri, korelasyonlar
- MetaInsight: İnsan okunabilir raporlar
- Episode: Zaman dilimleri (100 cycle = 1 episode)
- MetaState: 6 meta-bilişsel değişken + confidence

⚠️ Alice Notları:
- Her MetaState değişkeninin confidence değeri olmalı
- memory_health ve ethical_alignment başlangıçta düşük confidence olacak
- to_log_string() her zaman confidence ile loglama yapmalı
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import uuid4
from enum import Enum


# ============================================================
# ENUMS
# ============================================================

class EventType(str, Enum):
    """MetaEvent türleri."""
    ANOMALY = "anomaly"
    THRESHOLD_BREACH = "threshold_breach"
    PATTERN_DETECTED = "pattern_detected"
    EPISODE_BOUNDARY = "episode_boundary"
    PERFORMANCE_WARNING = "performance_warning"


class Severity(str, Enum):
    """Event önem seviyesi."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class PatternType(str, Enum):
    """MetaPattern türleri."""
    ACTION_SEQUENCE = "action_sequence"      # flee->wait->flee
    ACTION_FREQUENCY = "action_frequency"    # flee: 38%
    EMOTION_TREND = "emotion_trend"          # valence declining
    EMOTION_CYCLE = "emotion_cycle"          # anxiety->relief->anxiety
    CORRELATION = "correlation"              # danger>0.7 -> flee 85%


class InsightType(str, Enum):
    """MetaInsight türleri."""
    CYCLE_SUMMARY = "cycle_summary"
    EPISODE_HEALTH = "episode_health"
    ANOMALY_REPORT = "anomaly_report"
    RUN_REPORT = "run_report"  # v2.0


class InsightScope(str, Enum):
    """Insight kapsamı."""
    CYCLE = "cycle"
    EPISODE = "episode"
    RUN = "run"


class BoundaryReason(str, Enum):
    """Episode boundary nedeni."""
    TIME_WINDOW = "time_window"
    EVENT_OVERRIDE = "event_override"
    RUN_END = "run_end"
    GOAL_COMPLETE = "goal_complete"  # v2.0


class JobMode(str, Enum):
    """Scheduler job modu."""
    ONLINE = "online"              # Cycle path içinde
    ONLINE_ASYNC = "online_async"  # Cycle sonrası async
    OFFLINE_BATCH = "offline_batch"  # Run sonu veya manuel


# ============================================================
# META EVENT
# ============================================================

@dataclass
class MetaEvent:
    """
    MetaMind tarafından üretilen olaylar.
    
    Örnekler:
    - Anomali tespit edildi
    - Threshold aşıldı  
    - Yeni pattern bulundu
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    event_type: str = EventType.ANOMALY.value
    severity: str = Severity.INFO.value
    source: str = ""  # "cycle_analyzer" | "pattern_miner" | ...
    message: str = ""
    run_id: Optional[str] = None
    cycle_id: Optional[int] = None
    episode_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """DB kayıt için dict'e çevir."""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'event_type': self.event_type,
            'severity': self.severity,
            'source': self.source,
            'message': self.message,
            'run_id': self.run_id,
            'cycle_id': self.cycle_id,
            'episode_id': self.episode_id,
            'data': self.data,
        }


# ============================================================
# META PATTERN
# ============================================================

@dataclass
class MetaPattern:
    """
    Tespit edilen davranış pattern'leri.
    
    Örnekler:
    - action_sequence: "flee->wait->flee" (frequency=15, confidence=0.8)
    - emotion_trend: "valence_declining" (duration=50 cycles)
    - correlation: "danger>0.7 -> flee" (confidence=0.85)
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    pattern_type: str = PatternType.ACTION_SEQUENCE.value
    pattern_key: str = ""  # e.g. "flee->wait->flee"
    frequency: int = 0
    confidence: float = 0.0
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    run_id: Optional[str] = None
    episode_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """DB kayıt için dict'e çevir."""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'pattern_type': self.pattern_type,
            'pattern_key': self.pattern_key,
            'frequency': self.frequency,
            'confidence': self.confidence,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'run_id': self.run_id,
            'episode_id': self.episode_id,
            'data': self.data,
        }
    
    def update_seen(self) -> None:
        """Pattern tekrar görüldüğünde güncelle."""
        self.frequency += 1
        self.last_seen = datetime.utcnow()


# ============================================================
# META INSIGHT
# ============================================================

@dataclass
class MetaInsight:
    """
    İnsan okunabilir analiz raporları.
    
    Örnekler:
    - cycle_summary: "Son cycle'da coherence=0.8, anomali yok"
    - episode_health: "Episode sağlıklı, dominant emotion: curious"
    - anomaly_report: "3 kritik anomali tespit edildi"
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    insight_type: str = InsightType.CYCLE_SUMMARY.value
    scope: str = InsightScope.CYCLE.value
    content: str = ""  # Human-readable
    run_id: Optional[str] = None
    cycle_id: Optional[int] = None
    episode_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """DB kayıt için dict'e çevir."""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'insight_type': self.insight_type,
            'scope': self.scope,
            'content': self.content,
            'run_id': self.run_id,
            'cycle_id': self.cycle_id,
            'episode_id': self.episode_id,
            'data': self.data,
            'recommendations': self.recommendations,
        }


# ============================================================
# EPISODE
# ============================================================

@dataclass
class Episode:
    """
    Zaman dilimi - cycle grupları.
    
    Episode ID formatı: "{run_id}:{episode_seq}"
    
    Boundary (⚠️ Alice notu: 100 config'ten gelecek, hardcode YASAK):
    - Time-based: Her N cycle (config.episode.window_cycles)
    - Event-based: Manuel override (v2.0)
    """
    episode_id: str = ""  # "{run_id}:{seq}"
    run_id: str = ""
    episode_seq: int = 0
    start_cycle_id: int = 0
    end_cycle_id: Optional[int] = None  # None if ongoing
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    semantic_tag: str = "auto_window"
    boundary_reason: str = BoundaryReason.TIME_WINDOW.value
    cycle_count: int = 0
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Episode ID oluştur."""
        if not self.episode_id and self.run_id:
            self.episode_id = f"{self.run_id}:{self.episode_seq}"
    
    @property
    def is_active(self) -> bool:
        """Episode hala açık mı?"""
        return self.end_cycle_id is None
    
    def close(self, end_cycle_id: int, summary: Optional[Dict] = None) -> None:
        """Episode'u kapat."""
        self.end_cycle_id = end_cycle_id
        self.end_time = datetime.utcnow()
        self.cycle_count = end_cycle_id - self.start_cycle_id + 1
        if summary:
            self.summary = summary
    
    def to_dict(self) -> Dict[str, Any]:
        """DB kayıt için dict'e çevir."""
        return {
            'episode_id': self.episode_id,
            'run_id': self.run_id,
            'episode_seq': self.episode_seq,
            'start_cycle_id': self.start_cycle_id,
            'end_cycle_id': self.end_cycle_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'semantic_tag': self.semantic_tag,
            'boundary_reason': self.boundary_reason,
            'cycle_count': self.cycle_count,
            'summary': self.summary,
        }


# ============================================================
# METRIC WITH CONFIDENCE
# ============================================================

@dataclass
class MetricWithConfidence:
    """
    Tek bir metrik + güvenilirlik skoru.
    
    ⚠️ Alice notu: Confidence her zaman loglanmalı
    """
    value: float = 0.0
    confidence: float = 0.0
    data_points: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_log_string(self, name: str) -> str:
        """
        Log formatı: "metric=0.750 (confidence=0.80)"
        ⚠️ Alice notu: Her metriği confidence ile logla
        """
        return f"{name}={self.value:.3f} (confidence={self.confidence:.2f})"
    
    def is_low_confidence(self, threshold: float = 0.5) -> bool:
        """Confidence düşük mü?"""
        return self.confidence < threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Dict'e çevir."""
        return {
            'value': self.value,
            'confidence': self.confidence,
            'data_points': self.data_points,
            'last_updated': self.last_updated.isoformat(),
        }


# ============================================================
# META STATE
# ============================================================

@dataclass
class MetaState:
    """
    MetaMind'ın 6 temel meta-bilişsel değişkeni.
    
    Her değişken için:
    - value: 0.0 - 1.0 arası skor
    - confidence: Güvenilirlik skoru
    - data_points: Hesaplamada kullanılan veri sayısı
    
    ⚠️ Alice notu: memory_health ve ethical_alignment başlangıçta
    düşük confidence ile gelecek - bu normal, veri olgunlaşınca artacak.
    
    Formüller (Final Consensus):
    - global_cognitive_health = coherence*0.25 + efficiency*0.20 + quality*0.25 + success_rate*0.30
    - emotional_stability = 1.0 - arousal_volatility
    - ethical_alignment = 1.0 - ethmor_block_rate
    - exploration_bias = action_diversity_score
    - failure_pressure = min(1.0, failure_streak/5.0)
    - memory_health = consolidation_success_rate
    """
    # 6 ana metrik
    global_cognitive_health: MetricWithConfidence = field(default_factory=MetricWithConfidence)
    emotional_stability: MetricWithConfidence = field(default_factory=MetricWithConfidence)
    ethical_alignment: MetricWithConfidence = field(default_factory=MetricWithConfidence)
    exploration_bias: MetricWithConfidence = field(default_factory=MetricWithConfidence)
    failure_pressure: MetricWithConfidence = field(default_factory=MetricWithConfidence)
    memory_health: MetricWithConfidence = field(default_factory=MetricWithConfidence)
    
    # Meta bilgi
    timestamp: datetime = field(default_factory=datetime.utcnow)
    run_id: Optional[str] = None
    cycle_id: Optional[int] = None
    episode_id: Optional[str] = None
    
    def to_log_string(self) -> str:
        """
        Tüm metrikleri confidence ile logla.
        
        Örnek çıktı:
        "MetaState: global_health=0.750 (confidence=0.85), 
         emotional_stability=0.600 (confidence=0.70), ..."
        """
        metrics = [
            self.global_cognitive_health.to_log_string("global_health"),
            self.emotional_stability.to_log_string("emotional_stability"),
            self.ethical_alignment.to_log_string("ethical_alignment"),
            self.exploration_bias.to_log_string("exploration_bias"),
            self.failure_pressure.to_log_string("failure_pressure"),
            self.memory_health.to_log_string("memory_health"),
        ]
        return "MetaState: " + ", ".join(metrics)
    
    def get_low_confidence_metrics(self, threshold: float = 0.5) -> List[str]:
        """Düşük confidence'lı metrikleri listele."""
        low = []
        if self.global_cognitive_health.is_low_confidence(threshold):
            low.append("global_cognitive_health")
        if self.emotional_stability.is_low_confidence(threshold):
            low.append("emotional_stability")
        if self.ethical_alignment.is_low_confidence(threshold):
            low.append("ethical_alignment")
        if self.exploration_bias.is_low_confidence(threshold):
            low.append("exploration_bias")
        if self.failure_pressure.is_low_confidence(threshold):
            low.append("failure_pressure")
        if self.memory_health.is_low_confidence(threshold):
            low.append("memory_health")
        return low
    
    def to_dict(self) -> Dict[str, Any]:
        """DB kayıt için dict'e çevir (tüm confidence'lar dahil)."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'run_id': self.run_id,
            'cycle_id': self.cycle_id,
            'episode_id': self.episode_id,
            # Values
            'global_cognitive_health': self.global_cognitive_health.value,
            'emotional_stability': self.emotional_stability.value,
            'ethical_alignment': self.ethical_alignment.value,
            'exploration_bias': self.exploration_bias.value,
            'failure_pressure': self.failure_pressure.value,
            'memory_health': self.memory_health.value,
            # Confidences
            'global_health_confidence': self.global_cognitive_health.confidence,
            'emotional_stability_confidence': self.emotional_stability.confidence,
            'ethical_alignment_confidence': self.ethical_alignment.confidence,
            'exploration_bias_confidence': self.exploration_bias.confidence,
            'failure_pressure_confidence': self.failure_pressure.confidence,
            'memory_health_confidence': self.memory_health.confidence,
        }
    
    def to_summary_dict(self) -> Dict[str, float]:
        """Sadece value'ları içeren basit dict."""
        return {
            'global_cognitive_health': self.global_cognitive_health.value,
            'emotional_stability': self.emotional_stability.value,
            'ethical_alignment': self.ethical_alignment.value,
            'exploration_bias': self.exploration_bias.value,
            'failure_pressure': self.failure_pressure.value,
            'memory_health': self.memory_health.value,
        }


# ============================================================
# SCHEDULER JOB
# ============================================================

@dataclass
class Job:
    """MetaMind scheduler job tanımı."""
    name: str
    period_cycles: int = 1
    period_episodes: int = 0
    period_runs: int = 0
    mode: str = JobMode.ONLINE.value
    target_ms: float = 1.0
    enabled: bool = True
    last_run_cycle: int = 0
    last_duration_ms: float = 0.0
    
    def should_run(self, current_cycle: int) -> bool:
        """Bu cycle'da çalışmalı mı?"""
        if not self.enabled:
            return False
        if self.period_cycles > 0:
            return (current_cycle - self.last_run_cycle) >= self.period_cycles
        return False
    
    def record_run(self, cycle: int, duration_ms: float) -> None:
        """Çalışma kaydı."""
        self.last_run_cycle = cycle
        self.last_duration_ms = duration_ms
    
    def is_over_budget(self) -> bool:
        """Target süreyi aştı mı?"""
        return self.last_duration_ms > self.target_ms


# ============================================================
# METRICS SNAPSHOT
# ============================================================

@dataclass
class MetricsSnapshot:
    """
    MetricsAdapter'dan gelen normalleştirilmiş metrik snapshot'ı.
    Mevcut scorer'lardan toplanan veriler.
    """
    timestamp: datetime = field(default_factory=datetime.utcnow)
    cycle_id: int = 0
    
    # Scoring metrics (from existing scorers)
    coherence_score: float = 0.0
    efficiency_score: float = 0.0
    quality_score: float = 0.0
    trust_score: float = 0.0
    
    # Pattern metrics
    failure_streak: int = 0
    action_diversity: float = 0.0
    valence_trend: float = 0.0  # -1 to 1 (falling to rising)
    arousal_trend: float = 0.0
    
    # Clustering
    behavior_cluster_id: Optional[str] = None
    
    # Alerts
    alert_count: int = 0
    critical_alerts: int = 0
    
    # Raw data point counts (for confidence calculation)
    data_point_counts: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Dict'e çevir."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'cycle_id': self.cycle_id,
            'coherence_score': self.coherence_score,
            'efficiency_score': self.efficiency_score,
            'quality_score': self.quality_score,
            'trust_score': self.trust_score,
            'failure_streak': self.failure_streak,
            'action_diversity': self.action_diversity,
            'valence_trend': self.valence_trend,
            'arousal_trend': self.arousal_trend,
            'behavior_cluster_id': self.behavior_cluster_id,
            'alert_count': self.alert_count,
            'critical_alerts': self.critical_alerts,
        }


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Enums
    'EventType',
    'Severity', 
    'PatternType',
    'InsightType',
    'InsightScope',
    'BoundaryReason',
    'JobMode',
    # Dataclasses
    'MetaEvent',
    'MetaPattern',
    'MetaInsight',
    'Episode',
    'MetricWithConfidence',
    'MetaState',
    'Job',
    'MetricsSnapshot',
]
