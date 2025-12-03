"""
MetaMind v1.9 - Social Health Pipeline (IMPLEMENTED)
=====================================================

Multi-agent ortamda sosyal dinamiklerin meta-analizi.

EmpathyOrchestrator'dan gelen verileri kullanarak:
- Trust level
- Cooperation score
- Social engagement
- Conflict frequency
- Dominant/Isolated agent ratio

Veri Kaynağı: unified_core._empathy_results (her cycle'da dolu)
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger("UEM.MetaMind.Social")


@dataclass
class SocialHealthMetrics:
    """
    Social health metrikleri.
    
    3 temel metrik:
    1. trust_level: Ajanlara duyulan güven (0-1)
    2. cooperation_score: İşbirliği kalitesi (0-1)
    3. social_engagement: Sosyal etkileşim seviyesi (0-1)
    
    Ek metrikler:
    - conflict_frequency: Çatışma sıklığı (0-1)
    - dominant_agent_ratio: Baskın ajan oranı (0-1)
    - isolated_agent_ratio: İzole ajan oranı (0-1)
    """
    # Core metrics
    trust_level: float = 0.5
    cooperation_score: float = 0.5
    social_engagement: float = 0.5
    
    # Extended metrics
    conflict_frequency: float = 0.0
    dominant_agent_ratio: float = 0.0
    isolated_agent_ratio: float = 0.0
    average_empathy: float = 0.0
    average_resonance: float = 0.0
    
    # Confidence
    trust_confidence: float = 0.0
    cooperation_confidence: float = 0.0
    engagement_confidence: float = 0.0
    
    # Meta
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data_points: int = 0
    agent_count: int = 0
    is_stub: bool = False  # Artık gerçek implementasyon
    
    def to_dict(self) -> Dict[str, Any]:
        """Dict'e çevir."""
        return {
            'trust_level': round(self.trust_level, 4),
            'cooperation_score': round(self.cooperation_score, 4),
            'social_engagement': round(self.social_engagement, 4),
            'conflict_frequency': round(self.conflict_frequency, 4),
            'dominant_agent_ratio': round(self.dominant_agent_ratio, 4),
            'isolated_agent_ratio': round(self.isolated_agent_ratio, 4),
            'average_empathy': round(self.average_empathy, 4),
            'average_resonance': round(self.average_resonance, 4),
            'trust_confidence': round(self.trust_confidence, 4),
            'cooperation_confidence': round(self.cooperation_confidence, 4),
            'engagement_confidence': round(self.engagement_confidence, 4),
            'timestamp': self.timestamp.isoformat(),
            'data_points': self.data_points,
            'agent_count': self.agent_count,
            'is_stub': self.is_stub,
        }
    
    @property
    def overall_social_health(self) -> float:
        """Genel sosyal sağlık skoru."""
        return (self.trust_level + self.cooperation_score + self.social_engagement) / 3
    
    @property
    def overall_confidence(self) -> float:
        """Genel confidence."""
        return (self.trust_confidence + self.cooperation_confidence + self.engagement_confidence) / 3
    
    def get_status(self) -> str:
        """Durum string'i."""
        health = self.overall_social_health
        if health >= 0.7:
            return "HEALTHY 🟢"
        elif health >= 0.4:
            return "MODERATE 🟡"
        else:
            return "POOR 🔴"


class SocialHealthPipeline:
    """
    Social Health analiz pipeline'ı.
    
    EmpathyOrchestrator sonuçlarını alıp social health metrikleri hesaplar.
    
    Kullanım:
        pipeline = SocialHealthPipeline()
        pipeline.initialize(run_id)
        
        # Her cycle'da empathy sonuçlarını ekle
        pipeline.process_empathy_results(empathy_results)
        
        # Metrikleri al
        metrics = pipeline.get_metrics()
    """
    
    # Thresholds
    DOMINANT_THRESHOLD = 0.7  # Bu üstü empathy = dominant
    ISOLATED_THRESHOLD = 0.3  # Bu altı resonance = isolated
    CONFLICT_THRESHOLD = -0.3  # Bu altı relationship = conflict
    COOPERATIVE_THRESHOLD = 0.3  # Bu üstü relationship = cooperative
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: Pipeline konfigürasyonu
        """
        self.config = config or {}
        self._run_id: Optional[str] = None
        self._initialized: bool = False
        
        # Empathy result history
        self._empathy_history: List[List[Any]] = []  # Her cycle için empathy_results listesi
        self._agent_stats: Dict[str, Dict] = defaultdict(lambda: {
            'empathy_sum': 0.0,
            'resonance_sum': 0.0,
            'relationship_sum': 0.0,
            'interaction_count': 0,
        })
        
        # Current metrics
        self._current_metrics = SocialHealthMetrics()
        self._cycle_count = 0
        
        logger.info("SocialHealthPipeline created (v2.0 - Full Implementation)")
    
    def initialize(self, run_id: str) -> None:
        """Pipeline'ı initialize et."""
        self._run_id = run_id
        self._empathy_history.clear()
        self._agent_stats.clear()
        self._current_metrics = SocialHealthMetrics()
        self._cycle_count = 0
        self._initialized = True
        
        logger.debug(f"SocialHealthPipeline initialized for run: {run_id}")
    
    def process_empathy_results(self, empathy_results: List[Any]) -> SocialHealthMetrics:
        """
        Empathy sonuçlarını işle ve metrikleri güncelle.
        
        Args:
            empathy_results: EmpathyOrchestrator'dan dönen sonuç listesi
            
        Returns:
            Güncellenmiş SocialHealthMetrics
        """
        if not self._initialized:
            logger.warning("SocialHealthPipeline not initialized")
            return self._current_metrics
        
        self._cycle_count += 1
        
        if not empathy_results:
            # Ajan yok - izole durum
            self._current_metrics.agent_count = 0
            self._current_metrics.social_engagement = 0.0
            return self._current_metrics
        
        # Store history
        self._empathy_history.append(empathy_results)
        if len(self._empathy_history) > 100:  # Son 100 cycle
            self._empathy_history.pop(0)
        
        # Per-agent stats güncelle
        for result in empathy_results:
            self._update_agent_stats(result)
        
        # Metrikleri hesapla
        self._calculate_metrics(empathy_results)
        
        return self._current_metrics
    
    def _update_agent_stats(self, empathy_result: Any) -> None:
        """Tek bir empathy result için agent stats güncelle."""
        other = getattr(empathy_result, 'other_entity', None)
        if not other:
            return
        
        agent_id = getattr(other, 'entity_id', 'unknown')
        stats = self._agent_stats[agent_id]
        
        stats['empathy_sum'] += getattr(empathy_result, 'empathy_level', 0.0)
        stats['resonance_sum'] += getattr(empathy_result, 'resonance', 0.0)
        stats['relationship_sum'] += getattr(other, 'relationship', 0.0)
        stats['interaction_count'] += 1
    
    def _calculate_metrics(self, empathy_results: List[Any]) -> None:
        """Tüm metrikleri hesapla."""
        n = len(empathy_results)
        if n == 0:
            return
        
        # Değerleri topla
        empathy_values = []
        resonance_values = []
        relationship_values = []
        confidence_values = []
        
        for result in empathy_results:
            empathy_values.append(getattr(result, 'empathy_level', 0.0))
            resonance_values.append(getattr(result, 'resonance', 0.0))
            confidence_values.append(getattr(result, 'confidence', 0.0))
            
            other = getattr(result, 'other_entity', None)
            if other:
                relationship_values.append(getattr(other, 'relationship', 0.0))
        
        # === CORE METRICS ===
        
        # Trust Level: Average empathy * average confidence
        avg_empathy = sum(empathy_values) / n
        avg_confidence = sum(confidence_values) / n if confidence_values else 0.0
        self._current_metrics.trust_level = avg_empathy * (0.5 + 0.5 * avg_confidence)
        self._current_metrics.trust_confidence = avg_confidence
        
        # Cooperation Score: Pozitif relationship oranı
        if relationship_values:
            cooperative_count = sum(1 for r in relationship_values if r > self.COOPERATIVE_THRESHOLD)
            self._current_metrics.cooperation_score = cooperative_count / len(relationship_values)
            self._current_metrics.cooperation_confidence = min(1.0, len(relationship_values) / 5)
        
        # Social Engagement: Average resonance
        avg_resonance = sum(resonance_values) / n
        self._current_metrics.social_engagement = avg_resonance
        self._current_metrics.engagement_confidence = min(1.0, n / 3)
        
        # === EXTENDED METRICS ===
        
        # Conflict Frequency: Negatif relationship oranı
        if relationship_values:
            conflict_count = sum(1 for r in relationship_values if r < self.CONFLICT_THRESHOLD)
            self._current_metrics.conflict_frequency = conflict_count / len(relationship_values)
        
        # Dominant Agent Ratio: Yüksek empathy alanların oranı
        dominant_count = sum(1 for e in empathy_values if e > self.DOMINANT_THRESHOLD)
        self._current_metrics.dominant_agent_ratio = dominant_count / n
        
        # Isolated Agent Ratio: Düşük resonance olanların oranı
        isolated_count = sum(1 for r in resonance_values if r < self.ISOLATED_THRESHOLD)
        self._current_metrics.isolated_agent_ratio = isolated_count / n
        
        # Averages
        self._current_metrics.average_empathy = avg_empathy
        self._current_metrics.average_resonance = avg_resonance
        
        # Meta
        self._current_metrics.timestamp = datetime.utcnow()
        self._current_metrics.data_points = self._cycle_count
        self._current_metrics.agent_count = n
    
    def get_metrics(self) -> SocialHealthMetrics:
        """Current social health metrics'i döndür."""
        return self._current_metrics
    
    def get_trust_level(self, agent_id: Optional[str] = None) -> float:
        """Trust level döndür."""
        if agent_id and agent_id in self._agent_stats:
            stats = self._agent_stats[agent_id]
            if stats['interaction_count'] > 0:
                return stats['empathy_sum'] / stats['interaction_count']
        return self._current_metrics.trust_level
    
    def get_cooperation_score(self) -> float:
        """Cooperation score döndür."""
        return self._current_metrics.cooperation_score
    
    def get_social_engagement(self) -> float:
        """Social engagement döndür."""
        return self._current_metrics.social_engagement
    
    def get_dominant_agent_ratio(self) -> float:
        """Dominant agent ratio döndür."""
        return self._current_metrics.dominant_agent_ratio
    
    def get_isolated_agent_ratio(self) -> float:
        """Isolated agent ratio döndür."""
        return self._current_metrics.isolated_agent_ratio
    
    def get_average_empathy_score(self) -> float:
        """Average empathy score döndür."""
        return self._current_metrics.average_empathy
    
    def get_interaction_summary(self) -> Dict[str, Any]:
        """Interaction özeti döndür."""
        return {
            'total_cycles': self._cycle_count,
            'unique_agents': len(self._agent_stats),
            'current_agent_count': self._current_metrics.agent_count,
            'overall_health': self._current_metrics.overall_social_health,
            'status': self._current_metrics.get_status(),
            'is_stub': False,
        }
    
    def get_agent_report(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Belirli bir ajan için rapor."""
        if agent_id not in self._agent_stats:
            return None
        
        stats = self._agent_stats[agent_id]
        n = stats['interaction_count']
        
        if n == 0:
            return None
        
        return {
            'agent_id': agent_id,
            'interaction_count': n,
            'average_empathy': stats['empathy_sum'] / n,
            'average_resonance': stats['resonance_sum'] / n,
            'average_relationship': stats['relationship_sum'] / n,
        }
    
    def reset(self) -> None:
        """Pipeline sıfırla."""
        self._empathy_history.clear()
        self._agent_stats.clear()
        self._current_metrics = SocialHealthMetrics()
        self._cycle_count = 0
        logger.debug("SocialHealthPipeline reset")


# ============================================================
# FACTORY
# ============================================================

def create_social_pipeline(
    config: Optional[Dict[str, Any]] = None,
) -> SocialHealthPipeline:
    """Factory function."""
    return SocialHealthPipeline(config=config)


__all__ = ['SocialHealthPipeline', 'SocialHealthMetrics', 'create_social_pipeline']
