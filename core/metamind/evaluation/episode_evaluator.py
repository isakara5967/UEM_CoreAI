"""
MetaMind v1.9 - Episode Evaluator
=================================

Episode seviyesinde sağlık değerlendirmesi:
- Cycle verilerinden episode summary
- Health scoring
- Dominant patterns
- Recommendations

Episode kapandığında çalışır ve EpisodeHealthReport üretir.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..types import Episode, MetaState, MetaPattern, PatternType

logger = logging.getLogger("UEM.MetaMind.Evaluation")


@dataclass
class EpisodeHealthReport:
    """Episode sağlık raporu."""
    episode_id: str
    run_id: str
    
    # Basic info
    cycle_count: int = 0
    start_cycle: int = 0
    end_cycle: int = 0
    duration_seconds: float = 0.0
    
    # Health scores (0-1)
    overall_health: float = 0.0
    cognitive_health: float = 0.0
    emotional_health: float = 0.0
    behavioral_health: float = 0.0
    
    # Confidence
    overall_confidence: float = 0.0
    
    # Averages
    avg_coherence: float = 0.0
    avg_efficiency: float = 0.0
    avg_quality: float = 0.0
    avg_valence: float = 0.0
    avg_arousal: float = 0.0
    
    # Trends
    valence_trend: str = "stable"  # rising, falling, stable
    arousal_trend: str = "stable"
    health_trend: str = "stable"
    
    # Patterns
    dominant_action: Optional[str] = None
    action_diversity: float = 0.0
    top_patterns: List[str] = field(default_factory=list)
    
    # Issues
    anomaly_count: int = 0
    critical_anomaly_count: int = 0
    failure_count: int = 0
    max_failure_streak: int = 0
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    # Raw data
    meta_state_history: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Dict'e çevir."""
        return {
            'episode_id': self.episode_id,
            'run_id': self.run_id,
            'cycle_count': self.cycle_count,
            'start_cycle': self.start_cycle,
            'end_cycle': self.end_cycle,
            'duration_seconds': self.duration_seconds,
            'overall_health': self.overall_health,
            'overall_confidence': self.overall_confidence,
            'cognitive_health': self.cognitive_health,
            'emotional_health': self.emotional_health,
            'behavioral_health': self.behavioral_health,
            'avg_coherence': self.avg_coherence,
            'avg_efficiency': self.avg_efficiency,
            'avg_quality': self.avg_quality,
            'avg_valence': self.avg_valence,
            'avg_arousal': self.avg_arousal,
            'valence_trend': self.valence_trend,
            'arousal_trend': self.arousal_trend,
            'health_trend': self.health_trend,
            'dominant_action': self.dominant_action,
            'action_diversity': self.action_diversity,
            'top_patterns': self.top_patterns,
            'anomaly_count': self.anomaly_count,
            'critical_anomaly_count': self.critical_anomaly_count,
            'failure_count': self.failure_count,
            'max_failure_streak': self.max_failure_streak,
            'recommendations': self.recommendations,
        }
    
    def get_health_status(self) -> str:
        """Genel sağlık durumu string."""
        if self.overall_health >= 0.8:
            return "excellent"
        elif self.overall_health >= 0.6:
            return "good"
        elif self.overall_health >= 0.4:
            return "moderate"
        elif self.overall_health >= 0.2:
            return "poor"
        else:
            return "critical"
    
    def get_summary(self) -> str:
        """Human-readable summary."""
        status = self.get_health_status()
        conf_str = f"(confidence: {self.overall_confidence:.0%})"
        
        return (
            f"Episode {self.episode_id}: {status.upper()} {conf_str}\n"
            f"  Cycles: {self.cycle_count}, Duration: {self.duration_seconds:.1f}s\n"
            f"  Health: cognitive={self.cognitive_health:.2f}, "
            f"emotional={self.emotional_health:.2f}, behavioral={self.behavioral_health:.2f}\n"
            f"  Dominant action: {self.dominant_action or 'N/A'}, "
            f"Diversity: {self.action_diversity:.2f}\n"
            f"  Anomalies: {self.anomaly_count} ({self.critical_anomaly_count} critical)\n"
            f"  Recommendations: {len(self.recommendations)}"
        )


@dataclass
class EpisodeEvaluatorConfig:
    """Evaluator konfigürasyonu."""
    # Health thresholds
    health_excellent: float = 0.8
    health_good: float = 0.6
    health_moderate: float = 0.4
    health_poor: float = 0.2
    
    # Weights for overall health
    weight_cognitive: float = 0.4
    weight_emotional: float = 0.3
    weight_behavioral: float = 0.3
    
    # Recommendation thresholds
    recommend_on_low_health: float = 0.5
    recommend_on_high_failures: int = 3
    recommend_on_low_diversity: float = 0.3


class EpisodeEvaluator:
    """
    Episode seviyesinde sağlık değerlendirmesi.
    
    Episode kapandığında çağrılır ve:
    1. Tüm cycle verilerini analiz eder
    2. Health score'ları hesaplar
    3. Trend'leri belirler
    4. Recommendations üretir
    
    Kullanım:
        evaluator = EpisodeEvaluator(config)
        
        # Her cycle'da veri topla
        evaluator.add_cycle_data(cycle_id, meta_state, cycle_data)
        
        # Episode kapandığında evaluate et
        report = evaluator.evaluate(episode)
    """
    
    def __init__(
        self,
        config: Optional[EpisodeEvaluatorConfig] = None,
        pattern_miner=None,
    ):
        """
        Args:
            config: EpisodeEvaluatorConfig instance
            pattern_miner: PatternMiner for pattern data
        """
        self.config = config or EpisodeEvaluatorConfig()
        self.pattern_miner = pattern_miner
        
        # Cycle data collection
        self._cycle_data: List[Dict[str, Any]] = []
        self._meta_states: List[MetaState] = []
        self._anomalies: List[Dict] = []
        
        # Running stats
        self._failure_count: int = 0
        self._max_failure_streak: int = 0
        self._current_streak: int = 0
        
        logger.debug("EpisodeEvaluator initialized")
    
    def reset(self) -> None:
        """Evaluator'ı sıfırla (yeni episode için)."""
        self._cycle_data.clear()
        self._meta_states.clear()
        self._anomalies.clear()
        self._failure_count = 0
        self._max_failure_streak = 0
        self._current_streak = 0
        logger.debug("EpisodeEvaluator reset")
    
    def add_cycle_data(
        self,
        cycle_id: int,
        meta_state: Optional[MetaState] = None,
        cycle_data: Optional[Dict[str, Any]] = None,
        anomalies: Optional[List[Dict]] = None,
        success: bool = True,
    ) -> None:
        """
        Cycle verisi ekle.
        
        Args:
            cycle_id: Cycle number
            meta_state: MetaState snapshot
            cycle_data: Raw cycle data
            anomalies: Detected anomalies
            success: Action success status
        """
        # Store cycle data
        self._cycle_data.append({
            'cycle_id': cycle_id,
            'timestamp': datetime.utcnow().isoformat(),
            'data': cycle_data or {},
            'success': success,
        })
        
        # Store meta state
        if meta_state:
            self._meta_states.append(meta_state)
        
        # Store anomalies
        if anomalies:
            self._anomalies.extend(anomalies)
        
        # Track failures
        if not success:
            self._failure_count += 1
            self._current_streak += 1
            self._max_failure_streak = max(self._max_failure_streak, self._current_streak)
        else:
            self._current_streak = 0
    
    def evaluate(self, episode: Episode) -> EpisodeHealthReport:
        """
        Episode'u değerlendir ve rapor üret.
        
        Args:
            episode: Closed Episode instance
            
        Returns:
            EpisodeHealthReport
        """
        report = EpisodeHealthReport(
            episode_id=episode.episode_id,
            run_id=episode.run_id,
            cycle_count=episode.cycle_count or len(self._cycle_data),
            start_cycle=episode.start_cycle_id,
            end_cycle=episode.end_cycle_id or episode.start_cycle_id,
        )
        
        # Duration
        if episode.start_time and episode.end_time:
            report.duration_seconds = (episode.end_time - episode.start_time).total_seconds()
        
        # Calculate health scores
        self._calculate_health_scores(report)
        
        # Calculate averages
        self._calculate_averages(report)
        
        # Determine trends
        self._calculate_trends(report)
        
        # Get pattern info
        self._add_pattern_info(report)
        
        # Add anomaly info
        report.anomaly_count = len(self._anomalies)
        report.critical_anomaly_count = sum(
            1 for a in self._anomalies 
            if a.get('severity') == 'critical'
        )
        report.failure_count = self._failure_count
        report.max_failure_streak = self._max_failure_streak
        
        # Generate recommendations
        self._generate_recommendations(report)
        
        # Store meta state history (simplified)
        report.meta_state_history = [
            ms.to_summary_dict() for ms in self._meta_states[-10:]
        ]
        
        logger.info(f"Episode evaluated: {report.get_summary()}")
        return report
    
    def _calculate_health_scores(self, report: EpisodeHealthReport) -> None:
        """Health score'ları hesapla."""
        if not self._meta_states:
            report.overall_health = 0.5
            report.overall_confidence = 0.0
            return
        
        # Cognitive health (average of global_cognitive_health)
        cognitive_values = [ms.global_cognitive_health.value for ms in self._meta_states]
        cognitive_confidences = [ms.global_cognitive_health.confidence for ms in self._meta_states]
        report.cognitive_health = sum(cognitive_values) / len(cognitive_values)
        
        # Emotional health (average of emotional_stability)
        emotional_values = [ms.emotional_stability.value for ms in self._meta_states]
        report.emotional_health = sum(emotional_values) / len(emotional_values)
        
        # Behavioral health (based on exploration_bias and failure_pressure)
        exploration = [ms.exploration_bias.value for ms in self._meta_states]
        failure_pressure = [ms.failure_pressure.value for ms in self._meta_states]
        
        avg_exploration = sum(exploration) / len(exploration)
        avg_failure_pressure = sum(failure_pressure) / len(failure_pressure)
        
        # Behavioral health = good exploration + low failure pressure
        report.behavioral_health = (avg_exploration + (1.0 - avg_failure_pressure)) / 2
        
        # Overall health (weighted average)
        report.overall_health = (
            self.config.weight_cognitive * report.cognitive_health +
            self.config.weight_emotional * report.emotional_health +
            self.config.weight_behavioral * report.behavioral_health
        )
        
        # Overall confidence (average of all confidences)
        all_confidences = cognitive_confidences + [
            ms.emotional_stability.confidence for ms in self._meta_states
        ] + [
            ms.exploration_bias.confidence for ms in self._meta_states
        ]
        report.overall_confidence = sum(all_confidences) / len(all_confidences)
    
    def _calculate_averages(self, report: EpisodeHealthReport) -> None:
        """Ortalama değerleri hesapla."""
        if not self._cycle_data:
            return
        
        # Extract values from cycle data
        coherence_vals = []
        efficiency_vals = []
        quality_vals = []
        valence_vals = []
        arousal_vals = []
        
        for cd in self._cycle_data:
            data = cd.get('data', {})
            if 'coherence' in data:
                coherence_vals.append(data['coherence'])
            if 'efficiency' in data:
                efficiency_vals.append(data['efficiency'])
            if 'quality' in data:
                quality_vals.append(data['quality'])
            if 'valence' in data:
                valence_vals.append(data['valence'])
            if 'arousal' in data:
                arousal_vals.append(data['arousal'])
        
        # Calculate averages
        if coherence_vals:
            report.avg_coherence = sum(coherence_vals) / len(coherence_vals)
        if efficiency_vals:
            report.avg_efficiency = sum(efficiency_vals) / len(efficiency_vals)
        if quality_vals:
            report.avg_quality = sum(quality_vals) / len(quality_vals)
        if valence_vals:
            report.avg_valence = sum(valence_vals) / len(valence_vals)
        if arousal_vals:
            report.avg_arousal = sum(arousal_vals) / len(arousal_vals)
    
    def _calculate_trends(self, report: EpisodeHealthReport) -> None:
        """Trend'leri hesapla."""
        # Valence trend
        valence_vals = [
            cd.get('data', {}).get('valence', 0.0) 
            for cd in self._cycle_data 
            if 'valence' in cd.get('data', {})
        ]
        report.valence_trend = self._get_trend(valence_vals)
        
        # Arousal trend
        arousal_vals = [
            cd.get('data', {}).get('arousal', 0.0) 
            for cd in self._cycle_data 
            if 'arousal' in cd.get('data', {})
        ]
        report.arousal_trend = self._get_trend(arousal_vals)
        
        # Health trend
        health_vals = [
            ms.global_cognitive_health.value 
            for ms in self._meta_states
        ]
        report.health_trend = self._get_trend(health_vals)
    
    def _get_trend(self, values: List[float], threshold: float = 0.1) -> str:
        """Liste için trend belirle."""
        if len(values) < 4:
            return "stable"
        
        first_quarter = values[:len(values)//4]
        last_quarter = values[-len(values)//4:]
        
        if not first_quarter or not last_quarter:
            return "stable"
        
        avg_first = sum(first_quarter) / len(first_quarter)
        avg_last = sum(last_quarter) / len(last_quarter)
        
        diff = avg_last - avg_first
        
        if diff > threshold:
            return "rising"
        elif diff < -threshold:
            return "falling"
        else:
            return "stable"
    
    def _add_pattern_info(self, report: EpisodeHealthReport) -> None:
        """Pattern bilgilerini ekle."""
        if not self.pattern_miner:
            return
        
        # Dominant action
        report.dominant_action = self.pattern_miner.get_dominant_action()
        
        # Action diversity (from distribution)
        distribution = self.pattern_miner.get_action_distribution()
        if distribution:
            # Entropy-based diversity (normalized)
            import math
            entropy = -sum(p * math.log(p + 1e-10) for p in distribution.values())
            max_entropy = math.log(len(distribution) + 1e-10)
            report.action_diversity = entropy / max_entropy if max_entropy > 0 else 0.0
        
        # Top patterns
        top_patterns = self.pattern_miner.get_top_patterns(limit=5)
        report.top_patterns = [p.pattern_key for p in top_patterns]
    
    def _generate_recommendations(self, report: EpisodeHealthReport) -> None:
        """Öneriler üret."""
        recommendations = []
        
        # Low health
        if report.overall_health < self.config.recommend_on_low_health:
            if report.cognitive_health < 0.4:
                recommendations.append(
                    "Cognitive health is low. Consider reviewing decision-making patterns."
                )
            if report.emotional_health < 0.4:
                recommendations.append(
                    "Emotional stability is low. Agent may benefit from calmer scenarios."
                )
            if report.behavioral_health < 0.4:
                recommendations.append(
                    "Behavioral health is low. Consider increasing action diversity."
                )
        
        # High failures
        if self._max_failure_streak >= self.config.recommend_on_high_failures:
            recommendations.append(
                f"High failure streak ({self._max_failure_streak}) detected. "
                "Review action selection strategy."
            )
        
        # Low diversity
        if report.action_diversity < self.config.recommend_on_low_diversity:
            recommendations.append(
                f"Low action diversity ({report.action_diversity:.2f}). "
                "Agent may be stuck in repetitive patterns."
            )
        
        # Declining trends
        if report.health_trend == "falling":
            recommendations.append(
                "Health trend is declining. Monitor closely."
            )
        if report.valence_trend == "falling":
            recommendations.append(
                "Valence trend is declining. Agent may be experiencing negative states."
            )
        
        # Critical anomalies
        if report.critical_anomaly_count > 0:
            recommendations.append(
                f"{report.critical_anomaly_count} critical anomalies detected. "
                "Review anomaly logs for details."
            )
        
        # Low confidence warning
        if report.overall_confidence < 0.5:
            recommendations.append(
                f"Low confidence ({report.overall_confidence:.0%}) in health metrics. "
                "More data needed for reliable assessment."
            )
        
        report.recommendations = recommendations


# ============================================================
# FACTORY
# ============================================================

def create_episode_evaluator(
    config: Optional[Dict[str, Any]] = None,
    pattern_miner=None,
) -> EpisodeEvaluator:
    """Factory function."""
    return EpisodeEvaluator(
        config=EpisodeEvaluatorConfig() if not config else None,
        pattern_miner=pattern_miner,
    )


__all__ = ['EpisodeEvaluator', 'EpisodeEvaluatorConfig', 'EpisodeHealthReport', 'create_episode_evaluator']
