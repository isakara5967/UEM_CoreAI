"""
MetaMind v1.9 - MetaState Calculator
====================================

6 meta-bilişsel değişkeni hesaplar:
1. global_cognitive_health
2. emotional_stability
3. ethical_alignment
4. exploration_bias
5. failure_pressure
6. memory_health

⚠️ Alice Notları:
- Her metrik için confidence hesaplanmalı
- memory_health ve ethical_alignment başlangıçta düşük confidence
- Formüller Final Consensus'tan alındı
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .types import MetaState, MetricWithConfidence, MetricsSnapshot

logger = logging.getLogger("UEM.MetaMind.MetaState")


@dataclass
class MetaStateConfig:
    """MetaState hesaplama konfigürasyonu."""
    # Ağırlıklar (global_health için)
    weight_coherence: float = 0.25
    weight_efficiency: float = 0.20
    weight_quality: float = 0.25
    weight_success_rate: float = 0.30
    
    # Confidence hesaplama
    min_data_points: int = 10
    low_confidence_threshold: float = 0.5
    decay_factor: float = 0.95
    
    # Failure pressure
    failure_streak_max: int = 5
    
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'MetaStateConfig':
        """Config dict'ten oluştur."""
        meta_state_config = config.get('meta_state', {})
        weights = meta_state_config.get('weights', {}).get('global_health', {})
        confidence = meta_state_config.get('confidence', {})
        
        return cls(
            weight_coherence=weights.get('coherence', 0.25),
            weight_efficiency=weights.get('efficiency', 0.20),
            weight_quality=weights.get('quality', 0.25),
            weight_success_rate=weights.get('success_rate', 0.30),
            min_data_points=confidence.get('min_data_points', 10),
            low_confidence_threshold=confidence.get('low_threshold', 0.5),
            decay_factor=confidence.get('decay_factor', 0.95),
        )


class MetaStateCalculator:
    """
    MetaState değişkenlerini hesaplar.
    
    Formüller (Final Consensus):
    - global_cognitive_health = coherence*0.25 + efficiency*0.20 + quality*0.25 + success_rate*0.30
    - emotional_stability = 1.0 - arousal_volatility
    - ethical_alignment = 1.0 - ethmor_block_rate
    - exploration_bias = action_diversity_score
    - failure_pressure = min(1.0, failure_streak/5.0)
    - memory_health = consolidation_success_rate
    
    Kullanım:
        calculator = MetaStateCalculator(config)
        meta_state = calculator.compute_full_state(metrics_snapshot, history)
    """
    
    def __init__(self, config: Optional[MetaStateConfig] = None):
        """
        Args:
            config: MetaStateConfig instance veya None (defaults kullanılır)
        """
        self.config = config or MetaStateConfig()
        self._data_point_counts: Dict[str, int] = {
            'global_health': 0,
            'emotional_stability': 0,
            'ethical_alignment': 0,
            'exploration_bias': 0,
            'failure_pressure': 0,
            'memory_health': 0,
        }
        
        # Running averages for volatility calculation
        self._valence_history: list = []
        self._arousal_history: list = []
        self._ethmor_block_count: int = 0
        self._ethmor_total_count: int = 0
        self._consolidation_success: int = 0
        self._consolidation_total: int = 0
    
    def compute_full_state(
        self,
        snapshot: MetricsSnapshot,
        run_id: Optional[str] = None,
        cycle_id: Optional[int] = None,
        episode_id: Optional[str] = None,
    ) -> MetaState:
        """
        Tüm meta-state değişkenlerini hesapla.
        
        Args:
            snapshot: MetricsSnapshot from MetricsAdapter
            run_id: Current run ID
            cycle_id: Current cycle ID
            episode_id: Current episode ID
            
        Returns:
            Complete MetaState with all 6 variables + confidences
        """
        # Her değişkeni hesapla
        global_health = self.calculate_global_health(snapshot)
        emotional_stability = self.calculate_emotional_stability(snapshot)
        ethical_alignment = self.calculate_ethical_alignment(snapshot)
        exploration_bias = self.calculate_exploration_bias(snapshot)
        failure_pressure = self.calculate_failure_pressure(snapshot)
        memory_health = self.calculate_memory_health(snapshot)
        
        # MetaState oluştur
        meta_state = MetaState(
            global_cognitive_health=global_health,
            emotional_stability=emotional_stability,
            ethical_alignment=ethical_alignment,
            exploration_bias=exploration_bias,
            failure_pressure=failure_pressure,
            memory_health=memory_health,
            run_id=run_id,
            cycle_id=cycle_id,
            episode_id=episode_id,
        )
        
        # Log with confidence (⚠️ Alice notu)
        self._log_with_confidence(meta_state)
        
        return meta_state
    
    def calculate_global_health(self, snapshot: MetricsSnapshot) -> MetricWithConfidence:
        """
        Global cognitive health hesapla.
        
        Formül: coherence*0.25 + efficiency*0.20 + quality*0.25 + success_rate*0.30
        """
        # Success rate'i coherence'dan türet (basitleştirme)
        success_rate = snapshot.coherence_score  # Proxy
        
        value = (
            self.config.weight_coherence * snapshot.coherence_score +
            self.config.weight_efficiency * snapshot.efficiency_score +
            self.config.weight_quality * snapshot.quality_score +
            self.config.weight_success_rate * success_rate
        )
        
        # Clamp to [0, 1]
        value = max(0.0, min(1.0, value))
        
        # Data points güncelle
        self._data_point_counts['global_health'] += 1
        data_points = self._data_point_counts['global_health']
        
        # Confidence hesapla
        confidence = self._calculate_confidence('global_health', data_points)
        
        return MetricWithConfidence(
            value=value,
            confidence=confidence,
            data_points=data_points,
        )
    
    def calculate_emotional_stability(self, snapshot: MetricsSnapshot) -> MetricWithConfidence:
        """
        Emotional stability hesapla.
        
        Formül: 1.0 - arousal_volatility
        """
        # Arousal history güncelle
        self._arousal_history.append(snapshot.arousal_trend)
        if len(self._arousal_history) > 50:
            self._arousal_history.pop(0)
        
        # Volatility hesapla (standard deviation proxy)
        if len(self._arousal_history) >= 2:
            mean = sum(self._arousal_history) / len(self._arousal_history)
            variance = sum((x - mean) ** 2 for x in self._arousal_history) / len(self._arousal_history)
            volatility = min(1.0, variance ** 0.5)  # Std dev, capped at 1
        else:
            volatility = 0.5  # Default
        
        value = 1.0 - volatility
        value = max(0.0, min(1.0, value))
        
        # Data points güncelle
        self._data_point_counts['emotional_stability'] += 1
        data_points = self._data_point_counts['emotional_stability']
        
        confidence = self._calculate_confidence('emotional_stability', data_points)
        
        return MetricWithConfidence(
            value=value,
            confidence=confidence,
            data_points=data_points,
        )
    
    def calculate_ethical_alignment(self, snapshot: MetricsSnapshot) -> MetricWithConfidence:
        """
        Ethical alignment hesapla.
        
        Formül: 1.0 - ethmor_block_rate
        
        ⚠️ Alice notu: Başlangıçta düşük confidence olacak
        """
        # ETHMOR data'yı snapshot'tan al (varsa)
        # Şimdilik placeholder - gerçek ETHMOR entegrasyonu Phase 4'te
        ethmor_block_rate = snapshot.data.get('ethmor_block_rate', 0.0) if hasattr(snapshot, 'data') else 0.0
        
        # Running average güncelle
        self._ethmor_total_count += 1
        if ethmor_block_rate > 0.5:  # Block olarak say
            self._ethmor_block_count += 1
        
        if self._ethmor_total_count > 0:
            actual_block_rate = self._ethmor_block_count / self._ethmor_total_count
        else:
            actual_block_rate = 0.0
        
        value = 1.0 - actual_block_rate
        value = max(0.0, min(1.0, value))
        
        # Data points güncelle
        self._data_point_counts['ethical_alignment'] += 1
        data_points = self._data_point_counts['ethical_alignment']
        
        # ⚠️ Ethical alignment için extra low confidence başlangıçta
        confidence = self._calculate_confidence('ethical_alignment', data_points, penalty=0.2)
        
        return MetricWithConfidence(
            value=value,
            confidence=confidence,
            data_points=data_points,
        )
    
    def calculate_exploration_bias(self, snapshot: MetricsSnapshot) -> MetricWithConfidence:
        """
        Exploration bias hesapla.
        
        Formül: action_diversity_score
        """
        value = snapshot.action_diversity
        value = max(0.0, min(1.0, value))
        
        # Data points güncelle
        self._data_point_counts['exploration_bias'] += 1
        data_points = self._data_point_counts['exploration_bias']
        
        confidence = self._calculate_confidence('exploration_bias', data_points)
        
        return MetricWithConfidence(
            value=value,
            confidence=confidence,
            data_points=data_points,
        )
    
    def calculate_failure_pressure(self, snapshot: MetricsSnapshot) -> MetricWithConfidence:
        """
        Failure pressure hesapla.
        
        Formül: min(1.0, failure_streak / 5.0)
        """
        value = min(1.0, snapshot.failure_streak / self.config.failure_streak_max)
        value = max(0.0, min(1.0, value))
        
        # Data points güncelle
        self._data_point_counts['failure_pressure'] += 1
        data_points = self._data_point_counts['failure_pressure']
        
        confidence = self._calculate_confidence('failure_pressure', data_points)
        
        return MetricWithConfidence(
            value=value,
            confidence=confidence,
            data_points=data_points,
        )
    
    def calculate_memory_health(self, snapshot: MetricsSnapshot) -> MetricWithConfidence:
        """
        Memory health hesapla.
        
        Formül: consolidation_success_rate
        
        ⚠️ Alice notu: Başlangıçta düşük confidence olacak (LTM data erken)
        """
        # Memory consolidation data'yı snapshot'tan al (varsa)
        # Şimdilik placeholder - gerçek LTM entegrasyonu Phase 4'te
        consolidation_success = snapshot.data.get('consolidation_success', True) if hasattr(snapshot, 'data') else True
        
        # Running average güncelle
        self._consolidation_total += 1
        if consolidation_success:
            self._consolidation_success += 1
        
        if self._consolidation_total > 0:
            value = self._consolidation_success / self._consolidation_total
        else:
            value = 1.0  # Default healthy
        
        value = max(0.0, min(1.0, value))
        
        # Data points güncelle
        self._data_point_counts['memory_health'] += 1
        data_points = self._data_point_counts['memory_health']
        
        # ⚠️ Memory health için extra low confidence başlangıçta
        confidence = self._calculate_confidence('memory_health', data_points, penalty=0.3)
        
        return MetricWithConfidence(
            value=value,
            confidence=confidence,
            data_points=data_points,
        )
    
    def _calculate_confidence(
        self, 
        metric_name: str, 
        data_points: int,
        penalty: float = 0.0
    ) -> float:
        """
        Confidence skoru hesapla.
        
        Data point sayısı arttıkça confidence artar.
        Min data points'e ulaşana kadar düşük kalır.
        
        Args:
            metric_name: Metrik adı
            data_points: Toplanan veri sayısı
            penalty: Ek düşürme (ethical_alignment, memory_health için)
        """
        min_points = self.config.min_data_points
        
        if data_points >= min_points:
            # Yeterli veri var
            base_confidence = min(1.0, data_points / (min_points * 2))
        else:
            # Yetersiz veri
            base_confidence = data_points / min_points * 0.5
        
        # Penalty uygula
        confidence = base_confidence - penalty
        
        # Clamp
        return max(0.1, min(1.0, confidence))
    
    def _log_with_confidence(self, meta_state: MetaState) -> None:
        """
        MetaState'i confidence ile logla.
        
        ⚠️ Alice notu: Her metriği confidence ile logla
        """
        log_msg = meta_state.to_log_string()
        
        # Low confidence uyarısı
        low_conf = meta_state.get_low_confidence_metrics(self.config.low_confidence_threshold)
        if low_conf:
            log_msg += f" [LOW CONFIDENCE: {', '.join(low_conf)}]"
            logger.warning(log_msg)
        else:
            logger.debug(log_msg)
    
    def reset(self) -> None:
        """Calculator state'ini sıfırla (yeni run için)."""
        self._data_point_counts = {k: 0 for k in self._data_point_counts}
        self._valence_history.clear()
        self._arousal_history.clear()
        self._ethmor_block_count = 0
        self._ethmor_total_count = 0
        self._consolidation_success = 0
        self._consolidation_total = 0
        logger.debug("MetaStateCalculator reset")


# ============================================================
# FACTORY
# ============================================================

def create_meta_state_calculator(config: Optional[Dict[str, Any]] = None) -> MetaStateCalculator:
    """Factory function."""
    if config:
        meta_config = MetaStateConfig.from_dict(config)
    else:
        meta_config = MetaStateConfig()
    return MetaStateCalculator(meta_config)


__all__ = ['MetaStateCalculator', 'MetaStateConfig', 'create_meta_state_calculator']
