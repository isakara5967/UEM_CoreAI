"""
MetaMind v1.9 - Insight Generator
=================================

Human-readable insight ve rapor üretimi.

Insight türleri:
- CYCLE_SUMMARY: Tek cycle özeti
- EPISODE_HEALTH: Episode sağlık raporu
- ANOMALY_REPORT: Anomali özeti
- RUN_REPORT: Run sonu raporu (v2.0)

Her insight:
- Content: Human-readable text
- Data: Structured data
- Recommendations: Aksiyon önerileri
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..types import MetaInsight, MetaState, MetaPattern, InsightType, InsightScope
from ..evaluation import EpisodeHealthReport

logger = logging.getLogger("UEM.MetaMind.Insights")


@dataclass
class InsightGeneratorConfig:
    """Insight generator konfigürasyonu."""
    # Generation intervals
    cycle_summary_interval: int = 10      # Her N cycle'da summary
    anomaly_report_interval: int = 50     # Her N cycle'da anomaly report
    
    # Content settings
    max_recommendations: int = 5
    include_raw_data: bool = False
    verbose_mode: bool = False


class InsightGenerator:
    """
    Human-readable insight ve rapor üretici.
    
    Farklı scope'larda insight üretir:
    - Cycle: Kısa, anlık durum
    - Episode: Dönem analizi
    - Run: Genel değerlendirme (v2.0)
    
    Kullanım:
        generator = InsightGenerator(config)
        
        # Cycle summary
        insight = generator.generate_cycle_summary(cycle_id, meta_state, anomalies)
        
        # Episode report
        insight = generator.generate_episode_insight(episode_report)
        
        # Anomaly report
        insight = generator.generate_anomaly_report(anomalies)
    """
    
    def __init__(
        self,
        config: Optional[InsightGeneratorConfig] = None,
        storage=None,
    ):
        """
        Args:
            config: InsightGeneratorConfig instance
            storage: MetaMindStorage for persistence
        """
        self.config = config or InsightGeneratorConfig()
        self.storage = storage
        
        # Context
        self._run_id: Optional[str] = None
        self._episode_id: Optional[str] = None
        
        # Generated insights
        self._insights: List[MetaInsight] = []
        
        logger.debug("InsightGenerator initialized")
    
    def set_context(self, run_id: str, episode_id: Optional[str] = None) -> None:
        """Run/episode context ayarla."""
        self._run_id = run_id
        self._episode_id = episode_id
    
    def generate_cycle_summary(
        self,
        cycle_id: int,
        meta_state: Optional[MetaState] = None,
        anomalies: Optional[List[Dict]] = None,
        cycle_data: Optional[Dict[str, Any]] = None,
    ) -> MetaInsight:
        """
        Cycle summary insight üret.
        
        Args:
            cycle_id: Cycle number
            meta_state: Current MetaState
            anomalies: Detected anomalies
            cycle_data: Raw cycle data
            
        Returns:
            MetaInsight with cycle summary
        """
        # Build content
        content_parts = [f"Cycle {cycle_id} Summary:"]
        data = {'cycle_id': cycle_id}
        recommendations = []
        
        # MetaState info
        if meta_state:
            health = meta_state.global_cognitive_health.value
            health_conf = meta_state.global_cognitive_health.confidence
            
            status = self._get_health_status(health)
            content_parts.append(
                f"  Health: {status} ({health:.2f}, confidence: {health_conf:.0%})"
            )
            
            # Add key metrics
            content_parts.append(
                f"  Emotional stability: {meta_state.emotional_stability.value:.2f}"
            )
            content_parts.append(
                f"  Failure pressure: {meta_state.failure_pressure.value:.2f}"
            )
            
            data['meta_state'] = meta_state.to_summary_dict()
            
            # Low confidence warning
            low_conf = meta_state.get_low_confidence_metrics(0.5)
            if low_conf:
                content_parts.append(f"  ⚠️ Low confidence: {', '.join(low_conf)}")
            
            # Health-based recommendations
            if health < 0.4:
                recommendations.append("Health is low - consider intervention")
            if meta_state.failure_pressure.value > 0.7:
                recommendations.append("High failure pressure - review strategy")
        
        # Anomalies
        if anomalies:
            critical_count = sum(1 for a in anomalies if a.get('severity') == 'critical')
            warning_count = sum(1 for a in anomalies if a.get('severity') == 'warning')
            
            if critical_count > 0:
                content_parts.append(f"  🔴 {critical_count} critical anomalies")
                recommendations.append("Review critical anomalies immediately")
            if warning_count > 0:
                content_parts.append(f"  🟡 {warning_count} warnings")
            
            data['anomaly_count'] = len(anomalies)
            data['critical_anomalies'] = critical_count
        
        # Build final content
        content = "\n".join(content_parts)
        
        insight = MetaInsight(
            insight_type=InsightType.CYCLE_SUMMARY.value,
            scope=InsightScope.CYCLE.value,
            content=content,
            run_id=self._run_id,
            cycle_id=cycle_id,
            episode_id=self._episode_id,
            data=data,
            recommendations=recommendations[:self.config.max_recommendations],
        )
        
        self._insights.append(insight)
        self._persist_insight(insight)
        
        return insight
    
    def generate_episode_insight(
        self,
        episode_report: EpisodeHealthReport,
    ) -> MetaInsight:
        """
        Episode health insight üret.
        
        Args:
            episode_report: EpisodeHealthReport from evaluator
            
        Returns:
            MetaInsight with episode analysis
        """
        # Build content
        status = episode_report.get_health_status()
        
        content_parts = [
            f"Episode {episode_report.episode_id} Analysis:",
            f"  Status: {status.upper()} (overall health: {episode_report.overall_health:.2f})",
            f"  Duration: {episode_report.cycle_count} cycles, {episode_report.duration_seconds:.1f}s",
            "",
            "Health Breakdown:",
            f"  • Cognitive: {episode_report.cognitive_health:.2f}",
            f"  • Emotional: {episode_report.emotional_health:.2f}",
            f"  • Behavioral: {episode_report.behavioral_health:.2f}",
            "",
            "Trends:",
            f"  • Health: {episode_report.health_trend}",
            f"  • Valence: {episode_report.valence_trend}",
            f"  • Arousal: {episode_report.arousal_trend}",
        ]
        
        # Patterns
        if episode_report.dominant_action:
            content_parts.append("")
            content_parts.append("Behavior:")
            content_parts.append(f"  • Dominant action: {episode_report.dominant_action}")
            content_parts.append(f"  • Action diversity: {episode_report.action_diversity:.2f}")
            
            if episode_report.top_patterns:
                content_parts.append(f"  • Top patterns: {', '.join(episode_report.top_patterns[:3])}")
        
        # Issues
        if episode_report.anomaly_count > 0 or episode_report.failure_count > 0:
            content_parts.append("")
            content_parts.append("Issues:")
            if episode_report.anomaly_count > 0:
                content_parts.append(
                    f"  • Anomalies: {episode_report.anomaly_count} "
                    f"({episode_report.critical_anomaly_count} critical)"
                )
            if episode_report.failure_count > 0:
                content_parts.append(
                    f"  • Failures: {episode_report.failure_count} "
                    f"(max streak: {episode_report.max_failure_streak})"
                )
        
        # Confidence note
        if episode_report.overall_confidence < 0.5:
            content_parts.append("")
            content_parts.append(
                f"⚠️ Note: Low confidence ({episode_report.overall_confidence:.0%}) - "
                "metrics may be unreliable"
            )
        
        content = "\n".join(content_parts)
        
        insight = MetaInsight(
            insight_type=InsightType.EPISODE_HEALTH.value,
            scope=InsightScope.EPISODE.value,
            content=content,
            run_id=episode_report.run_id,
            episode_id=episode_report.episode_id,
            data=episode_report.to_dict(),
            recommendations=episode_report.recommendations[:self.config.max_recommendations],
        )
        
        self._insights.append(insight)
        self._persist_insight(insight)
        
        logger.info(f"Episode insight generated: {episode_report.episode_id}")
        return insight
    
    def generate_anomaly_report(
        self,
        anomalies: List[Dict],
        cycle_range: Optional[tuple] = None,
    ) -> MetaInsight:
        """
        Anomaly özet raporu üret.
        
        Args:
            anomalies: List of anomaly dicts
            cycle_range: Optional (start_cycle, end_cycle)
            
        Returns:
            MetaInsight with anomaly report
        """
        if not anomalies:
            content = "No anomalies detected in the specified period."
            return MetaInsight(
                insight_type=InsightType.ANOMALY_REPORT.value,
                scope=InsightScope.EPISODE.value,
                content=content,
                run_id=self._run_id,
                episode_id=self._episode_id,
                data={'anomaly_count': 0},
                recommendations=[],
            )
        
        # Categorize anomalies
        by_type: Dict[str, List] = {}
        by_severity: Dict[str, int] = {'critical': 0, 'warning': 0, 'info': 0}
        
        for anomaly in anomalies:
            atype = anomaly.get('anomaly_type', 'unknown')
            severity = anomaly.get('severity', 'info')
            
            if atype not in by_type:
                by_type[atype] = []
            by_type[atype].append(anomaly)
            
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Build content
        range_str = ""
        if cycle_range:
            range_str = f" (cycles {cycle_range[0]}-{cycle_range[1]})"
        
        content_parts = [
            f"Anomaly Report{range_str}:",
            f"  Total: {len(anomalies)} anomalies",
            f"  🔴 Critical: {by_severity['critical']}",
            f"  🟡 Warning: {by_severity['warning']}",
            f"  ℹ️ Info: {by_severity['info']}",
            "",
            "By Type:",
        ]
        
        # Sort by count
        sorted_types = sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True)
        
        for atype, instances in sorted_types[:5]:
            content_parts.append(f"  • {atype}: {len(instances)}")
        
        if len(sorted_types) > 5:
            content_parts.append(f"  • ... and {len(sorted_types) - 5} more types")
        
        # Recommendations
        recommendations = []
        
        if by_severity['critical'] > 0:
            recommendations.append(
                f"Address {by_severity['critical']} critical anomalies immediately"
            )
        
        if by_severity['critical'] > 5:
            recommendations.append(
                "High number of critical anomalies - consider pausing and reviewing"
            )
        
        # Most common type recommendation
        if sorted_types:
            most_common = sorted_types[0]
            if len(most_common[1]) >= 3:
                recommendations.append(
                    f"'{most_common[0]}' is recurring ({len(most_common[1])}x) - investigate root cause"
                )
        
        content = "\n".join(content_parts)
        
        insight = MetaInsight(
            insight_type=InsightType.ANOMALY_REPORT.value,
            scope=InsightScope.EPISODE.value,
            content=content,
            run_id=self._run_id,
            episode_id=self._episode_id,
            data={
                'anomaly_count': len(anomalies),
                'by_severity': by_severity,
                'by_type': {k: len(v) for k, v in by_type.items()},
            },
            recommendations=recommendations[:self.config.max_recommendations],
        )
        
        self._insights.append(insight)
        self._persist_insight(insight)
        
        return insight
    
    def generate_pattern_insight(
        self,
        patterns: List[MetaPattern],
    ) -> MetaInsight:
        """
        Pattern analiz insight'ı üret.
        
        Args:
            patterns: List of MetaPattern instances
            
        Returns:
            MetaInsight with pattern analysis
        """
        if not patterns:
            return MetaInsight(
                insight_type=InsightType.CYCLE_SUMMARY.value,
                scope=InsightScope.EPISODE.value,
                content="No patterns detected yet.",
                run_id=self._run_id,
                episode_id=self._episode_id,
                data={'pattern_count': 0},
                recommendations=["More data needed for pattern detection"],
            )
        
        # Categorize patterns
        by_type: Dict[str, List[MetaPattern]] = {}
        for pattern in patterns:
            ptype = pattern.pattern_type
            if ptype not in by_type:
                by_type[ptype] = []
            by_type[ptype].append(pattern)
        
        # Build content
        content_parts = [
            f"Pattern Analysis:",
            f"  Total patterns: {len(patterns)}",
            "",
        ]
        
        # Action frequency
        if 'action_frequency' in by_type:
            content_parts.append("Action Distribution:")
            for p in sorted(by_type['action_frequency'], key=lambda x: x.frequency, reverse=True)[:5]:
                pct = p.data.get('percentage', p.confidence * 100)
                content_parts.append(f"  • {p.pattern_key}: {pct:.1f}%")
            content_parts.append("")
        
        # Action sequences
        if 'action_sequence' in by_type:
            content_parts.append("Common Sequences:")
            for p in sorted(by_type['action_sequence'], key=lambda x: x.frequency, reverse=True)[:3]:
                content_parts.append(
                    f"  • {p.pattern_key} ({p.frequency}x, confidence: {p.confidence:.0%})"
                )
            content_parts.append("")
        
        # Emotion trends
        if 'emotion_trend' in by_type:
            content_parts.append("Emotion Trends:")
            for p in by_type['emotion_trend']:
                direction = p.data.get('direction', 'unknown')
                content_parts.append(
                    f"  • {p.pattern_key}: {direction} (confidence: {p.confidence:.0%})"
                )
        
        # Recommendations
        recommendations = []
        
        # Low diversity check
        if 'action_frequency' in by_type:
            top_action = by_type['action_frequency'][0] if by_type['action_frequency'] else None
            if top_action and top_action.confidence > 0.6:
                recommendations.append(
                    f"Action '{top_action.pattern_key}' dominates ({top_action.confidence:.0%}) - "
                    "consider encouraging diversity"
                )
        
        # Negative emotion trend
        if 'emotion_trend' in by_type:
            for p in by_type['emotion_trend']:
                if 'falling' in p.pattern_key and 'valence' in p.pattern_key:
                    recommendations.append(
                        "Valence trend is falling - agent may need positive reinforcement"
                    )
        
        content = "\n".join(content_parts)
        
        insight = MetaInsight(
            insight_type=InsightType.CYCLE_SUMMARY.value,
            scope=InsightScope.EPISODE.value,
            content=content,
            run_id=self._run_id,
            episode_id=self._episode_id,
            data={
                'pattern_count': len(patterns),
                'by_type': {k: len(v) for k, v in by_type.items()},
            },
            recommendations=recommendations[:self.config.max_recommendations],
        )
        
        self._insights.append(insight)
        return insight
    
    def _get_health_status(self, health: float) -> str:
        """Health değerine göre status string."""
        if health >= 0.8:
            return "EXCELLENT 🟢"
        elif health >= 0.6:
            return "GOOD 🟢"
        elif health >= 0.4:
            return "MODERATE 🟡"
        elif health >= 0.2:
            return "POOR 🟠"
        else:
            return "CRITICAL 🔴"
    
    def _persist_insight(self, insight: MetaInsight) -> None:
        """Insight'ı storage'a kaydet."""
        if not self.storage:
            return
        
        import asyncio
        try:
            # Storage'da save_insight metodu varsa kullan
            if hasattr(self.storage, 'save_insight'):
                asyncio.create_task(self.storage.save_insight(insight))
        except Exception as e:
            logger.debug(f"Failed to persist insight: {e}")
    
    def get_recent_insights(
        self,
        insight_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[MetaInsight]:
        """Son insight'ları getir."""
        insights = self._insights
        
        if insight_type:
            insights = [i for i in insights if i.insight_type == insight_type]
        
        return insights[-limit:]
    
    def reset(self) -> None:
        """Generator sıfırla."""
        self._insights.clear()
        logger.debug("InsightGenerator reset")


# ============================================================
# FACTORY
# ============================================================

def create_insight_generator(
    config: Optional[Dict[str, Any]] = None,
    storage=None,
) -> InsightGenerator:
    """Factory function."""
    return InsightGenerator(storage=storage)


__all__ = ['InsightGenerator', 'InsightGeneratorConfig', 'create_insight_generator']
