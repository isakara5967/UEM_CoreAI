"""
MetaMind v1.9 - Metrics Adapter
===============================

Mevcut scorer'ları wrap ederek MetaMind'a normalleştirilmiş
MetricsSnapshot sağlar.

Wrap edilen scorer'lar (core/metamind/metrics/):
- CoherenceScorer
- EfficiencyScorer
- QualityScorer
- TrustAggregator
- FailureTracker
- ActionAnalyzer
- TrendAnalyzer
- AlertManager
- BehaviorClusterer

⚠️ ÖNEMLİ: Mevcut metrics/ klasörü DEĞİŞMEYECEK
Bu adapter sadece wrap eder, 641 test bozulmaz.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from ..types import MetricsSnapshot

logger = logging.getLogger("UEM.MetaMind.Adapter")


class MetricsAdapter:
    """
    Mevcut MetaMind scorer'larını wrap eden adapter.
    
    Bu adapter:
    1. Mevcut scorer instance'larını alır
    2. Her cycle'da güncel verileri toplar
    3. Normalleştirilmiş MetricsSnapshot döndürür
    
    Kullanım:
        adapter = MetricsAdapter(
            coherence_scorer=coherence_scorer,
            efficiency_scorer=efficiency_scorer,
            ...
        )
        
        snapshot = adapter.get_snapshot(cycle_data, cycle_id)
    """
    
    def __init__(
        self,
        coherence_scorer=None,
        efficiency_scorer=None,
        quality_scorer=None,
        trust_aggregator=None,
        failure_tracker=None,
        action_analyzer=None,
        valence_trend=None,
        arousal_trend=None,
        alert_manager=None,
        behavior_clusterer=None,
    ):
        """
        Args:
            Tüm argümanlar mevcut scorer instance'ları
            None geçilebilir, bu durumda default değerler kullanılır
        """
        self._coherence_scorer = coherence_scorer
        self._efficiency_scorer = efficiency_scorer
        self._quality_scorer = quality_scorer
        self._trust_aggregator = trust_aggregator
        self._failure_tracker = failure_tracker
        self._action_analyzer = action_analyzer
        self._valence_trend = valence_trend
        self._arousal_trend = arousal_trend
        self._alert_manager = alert_manager
        self._behavior_clusterer = behavior_clusterer
        
        # Data point tracking (for confidence calculation)
        self._data_point_counts: Dict[str, int] = {
            'coherence': 0,
            'efficiency': 0,
            'quality': 0,
            'trust': 0,
            'failure': 0,
            'action': 0,
            'valence': 0,
            'arousal': 0,
        }
        
        self._initialized = False
        logger.debug("MetricsAdapter created")
    
    def initialize(self) -> bool:
        """
        Adapter'ı initialize et.
        
        Returns:
            True if at least one scorer is available
        """
        available = []
        
        if self._coherence_scorer:
            available.append('coherence')
        if self._efficiency_scorer:
            available.append('efficiency')
        if self._quality_scorer:
            available.append('quality')
        if self._trust_aggregator:
            available.append('trust')
        if self._failure_tracker:
            available.append('failure')
        if self._action_analyzer:
            available.append('action')
        if self._valence_trend:
            available.append('valence_trend')
        if self._arousal_trend:
            available.append('arousal_trend')
        if self._alert_manager:
            available.append('alerts')
        if self._behavior_clusterer:
            available.append('clustering')
        
        self._initialized = len(available) > 0
        
        if self._initialized:
            logger.info(f"MetricsAdapter initialized with: {', '.join(available)}")
        else:
            logger.warning("MetricsAdapter: No scorers available, using defaults")
        
        return self._initialized
    
    def get_snapshot(
        self,
        cycle_data: Dict[str, Any],
        cycle_id: int,
    ) -> MetricsSnapshot:
        """
        Tüm scorer'lardan veri toplayıp MetricsSnapshot döndür.
        
        Args:
            cycle_data: Cycle'dan gelen veriler (valence, arousal, action, success, etc.)
            cycle_id: Current cycle number
            
        Returns:
            Normalleştirilmiş MetricsSnapshot
        """
        snapshot = MetricsSnapshot(
            timestamp=datetime.utcnow(),
            cycle_id=cycle_id,
        )
        
        # === SCORING METRICS ===
        
        # Coherence
        if self._coherence_scorer:
            try:
                if hasattr(self._coherence_scorer, 'calculate'):
                    snapshot.coherence_score = self._coherence_scorer.calculate(cycle_data)
                elif hasattr(self._coherence_scorer, 'get_score'):
                    snapshot.coherence_score = self._coherence_scorer.get_score()
                self._data_point_counts['coherence'] += 1
            except Exception as e:
                logger.debug(f"Coherence scorer error: {e}")
                snapshot.coherence_score = 0.5  # Default
        else:
            snapshot.coherence_score = 0.5
        
        # Efficiency
        if self._efficiency_scorer:
            try:
                if hasattr(self._efficiency_scorer, 'calculate'):
                    snapshot.efficiency_score = self._efficiency_scorer.calculate(cycle_data)
                elif hasattr(self._efficiency_scorer, 'get_score'):
                    snapshot.efficiency_score = self._efficiency_scorer.get_score()
                self._data_point_counts['efficiency'] += 1
            except Exception as e:
                logger.debug(f"Efficiency scorer error: {e}")
                snapshot.efficiency_score = 0.5
        else:
            snapshot.efficiency_score = 0.5
        
        # Quality
        if self._quality_scorer:
            try:
                if hasattr(self._quality_scorer, 'calculate'):
                    snapshot.quality_score = self._quality_scorer.calculate(cycle_data)
                elif hasattr(self._quality_scorer, 'get_score'):
                    snapshot.quality_score = self._quality_scorer.get_score()
                self._data_point_counts['quality'] += 1
            except Exception as e:
                logger.debug(f"Quality scorer error: {e}")
                snapshot.quality_score = 0.5
        else:
            snapshot.quality_score = 0.5
        
        # Trust
        if self._trust_aggregator:
            try:
                if hasattr(self._trust_aggregator, 'get_average_trust'):
                    snapshot.trust_score = self._trust_aggregator.get_average_trust()
                elif hasattr(self._trust_aggregator, 'get_score'):
                    snapshot.trust_score = self._trust_aggregator.get_score()
                self._data_point_counts['trust'] += 1
            except Exception as e:
                logger.debug(f"Trust aggregator error: {e}")
                snapshot.trust_score = 0.5
        else:
            snapshot.trust_score = 0.5
        
        # === PATTERN METRICS ===
        
        # Failure streak
        if self._failure_tracker:
            try:
                if hasattr(self._failure_tracker, 'current_streak'):
                    snapshot.failure_streak = self._failure_tracker.current_streak
                elif hasattr(self._failure_tracker, 'get_streak'):
                    snapshot.failure_streak = self._failure_tracker.get_streak()
                self._data_point_counts['failure'] += 1
            except Exception as e:
                logger.debug(f"Failure tracker error: {e}")
                snapshot.failure_streak = 0
        else:
            # Fallback: cycle_data'dan success bilgisi
            snapshot.failure_streak = 0
        
        # Action diversity
        if self._action_analyzer:
            try:
                if hasattr(self._action_analyzer, 'get_diversity_score'):
                    snapshot.action_diversity = self._action_analyzer.get_diversity_score()
                elif hasattr(self._action_analyzer, 'diversity_score'):
                    snapshot.action_diversity = self._action_analyzer.diversity_score
                self._data_point_counts['action'] += 1
            except Exception as e:
                logger.debug(f"Action analyzer error: {e}")
                snapshot.action_diversity = 0.5
        else:
            snapshot.action_diversity = 0.5
        
        # Valence trend
        if self._valence_trend:
            try:
                if hasattr(self._valence_trend, 'get_trend_value'):
                    snapshot.valence_trend = self._valence_trend.get_average() if hasattr(self._valence_trend, 'get_average') else 0.0
                elif hasattr(self._valence_trend, 'trend'):
                    snapshot.valence_trend = self._valence_trend.trend
                self._data_point_counts['valence'] += 1
            except Exception as e:
                logger.debug(f"Valence trend error: {e}")
                snapshot.valence_trend = 0.0
        else:
            # Fallback: cycle_data'dan
            snapshot.valence_trend = cycle_data.get('valence', 0.0)
        
        # Arousal trend
        if self._arousal_trend:
            try:
                if hasattr(self._arousal_trend, 'get_trend_value'):
                    snapshot.arousal_trend = self._arousal_trend.get_average() if hasattr(self._arousal_trend, 'get_average') else 0.0
                elif hasattr(self._arousal_trend, 'trend'):
                    snapshot.arousal_trend = self._arousal_trend.trend
                self._data_point_counts['arousal'] += 1
            except Exception as e:
                logger.debug(f"Arousal trend error: {e}")
                snapshot.arousal_trend = 0.0
        else:
            snapshot.arousal_trend = cycle_data.get('arousal', 0.0)
        
        # === CLUSTERING ===
        
        if self._behavior_clusterer:
            try:
                if hasattr(self._behavior_clusterer, 'assign_cluster'):
                    snapshot.behavior_cluster_id = self._behavior_clusterer.assign_cluster(cycle_data)
                elif hasattr(self._behavior_clusterer, 'current_cluster'):
                    snapshot.behavior_cluster_id = self._behavior_clusterer.current_cluster
            except Exception as e:
                logger.debug(f"Behavior clusterer error: {e}")
                snapshot.behavior_cluster_id = None
        
        # === ALERTS ===
        
        if self._alert_manager:
            try:
                if hasattr(self._alert_manager, 'check'):
                    alerts = self._alert_manager.check(cycle_data, cycle_id=cycle_id)
                    snapshot.alert_count = len(alerts) if alerts else 0
                    snapshot.critical_alerts = sum(
                        1 for a in (alerts or []) 
                        if getattr(a, 'severity', '') == 'critical'
                    )
                elif hasattr(self._alert_manager, 'get_alert_count'):
                    snapshot.alert_count = self._alert_manager.get_alert_count()
                    snapshot.critical_alerts = self._alert_manager.get_critical_count()
            except Exception as e:
                logger.debug(f"Alert manager error: {e}")
                snapshot.alert_count = 0
                snapshot.critical_alerts = 0
        
        # Data point counts (for confidence calculation)
        snapshot.data_point_counts = dict(self._data_point_counts)
        
        return snapshot
    
    def get_data_point_count(self, metric_name: str) -> int:
        """
        Belirli bir metrik için toplanan veri sayısı.
        
        Args:
            metric_name: Metrik adı
            
        Returns:
            Data point count
        """
        return self._data_point_counts.get(metric_name, 0)
    
    def get_total_data_points(self) -> int:
        """Toplam data point sayısı."""
        return sum(self._data_point_counts.values())
    
    def reset_counts(self) -> None:
        """Data point sayaçlarını sıfırla."""
        self._data_point_counts = {k: 0 for k in self._data_point_counts}
        logger.debug("MetricsAdapter counts reset")
    
    def update_scorers(
        self,
        cycle_data: Dict[str, Any],
        action_result: Any = None,
    ) -> None:
        """
        Scorer'ları güncelle (record new data).
        
        Bu method unified_core'dan her cycle'da çağrılabilir.
        
        Args:
            cycle_data: Cycle verileri
            action_result: ActionResult (optional)
        """
        # Failure tracker update
        if self._failure_tracker and action_result:
            try:
                success = getattr(action_result, 'success', True)
                if hasattr(self._failure_tracker, 'record'):
                    self._failure_tracker.record(success)
            except Exception as e:
                logger.debug(f"Failure tracker update error: {e}")
        
        # Action analyzer update
        if self._action_analyzer:
            try:
                action = cycle_data.get('action') or getattr(action_result, 'action_name', None)
                if action and hasattr(self._action_analyzer, 'record'):
                    self._action_analyzer.record(action)
            except Exception as e:
                logger.debug(f"Action analyzer update error: {e}")
        
        # Trend analyzers update
        valence = cycle_data.get('valence', 0.0)
        arousal = cycle_data.get('arousal', 0.0)
        
        if self._valence_trend:
            try:
                if hasattr(self._valence_trend, 'add'):
                    self._valence_trend.add(valence)
            except Exception as e:
                logger.debug(f"Valence trend update error: {e}")
        
        if self._arousal_trend:
            try:
                if hasattr(self._arousal_trend, 'add'):
                    self._arousal_trend.add(arousal)
            except Exception as e:
                logger.debug(f"Arousal trend update error: {e}")


# ============================================================
# FACTORY
# ============================================================

def create_metrics_adapter(
    coherence_scorer=None,
    efficiency_scorer=None,
    quality_scorer=None,
    trust_aggregator=None,
    failure_tracker=None,
    action_analyzer=None,
    valence_trend=None,
    arousal_trend=None,
    alert_manager=None,
    behavior_clusterer=None,
) -> MetricsAdapter:
    """
    MetricsAdapter factory.
    
    unified_core.py'den mevcut scorer'lar ile çağrılacak.
    """
    adapter = MetricsAdapter(
        coherence_scorer=coherence_scorer,
        efficiency_scorer=efficiency_scorer,
        quality_scorer=quality_scorer,
        trust_aggregator=trust_aggregator,
        failure_tracker=failure_tracker,
        action_analyzer=action_analyzer,
        valence_trend=valence_trend,
        arousal_trend=arousal_trend,
        alert_manager=alert_manager,
        behavior_clusterer=behavior_clusterer,
    )
    adapter.initialize()
    return adapter


__all__ = ['MetricsAdapter', 'create_metrics_adapter']
