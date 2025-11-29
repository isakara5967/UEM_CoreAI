"""Tests for metamind module - Phase D."""
import pytest
import sys
sys.path.insert(0, '.')

from metamind import (
    CoherenceScorer, EfficiencyScorer, QualityScorer, TrustAggregator,
    FailureTracker, ActionAnalyzer, TrendAnalyzer,
    AlertManager, Alert, AlertSeverity, AlertCategory,
)
from metamind.pattern.trend import TrendDirection


# ==================== Scoring Tests ====================

class TestCoherenceScorer:
    """CoherenceScorer tests."""
    
    def test_calculate_basic(self):
        scorer = CoherenceScorer()
        score = scorer.calculate({
            "action_name": "explore",
            "utility": 0.7,
            "valence": 0.3,
            "action_success": True
        })
        assert 0.0 <= score <= 1.0
    
    def test_high_coherence(self):
        scorer = CoherenceScorer()
        score = scorer.calculate({
            "action_name": "explore",
            "utility": 0.9,
            "valence": 0.5,
            "arousal": 0.3,
            "action_success": True,
            "ethmor_decision": "allow",
            "memory_relevance": 0.8
        })
        assert score > 0.5
    
    def test_temporal_consistency(self):
        scorer = CoherenceScorer()
        prev = {"valence": 0.5, "action_name": "wait"}
        curr = {"valence": 0.55, "action_name": "explore", "utility": 0.6}
        
        score = scorer.calculate(curr, previous_cycle=prev)
        assert 0.0 <= score <= 1.0
    
    def test_get_average(self):
        scorer = CoherenceScorer()
        scorer.calculate({"utility": 0.5})
        scorer.calculate({"utility": 0.7})
        
        avg = scorer.get_average()
        assert 0.0 <= avg <= 1.0


class TestEfficiencyScorer:
    """EfficiencyScorer tests."""
    
    def test_calculate_basic(self):
        scorer = EfficiencyScorer()
        score = scorer.calculate({"cycle_time_ms": 50})
        assert 0.0 <= score <= 1.0
    
    def test_fast_cycle_high_efficiency(self):
        scorer = EfficiencyScorer()
        score = scorer.calculate({
            "cycle_time_ms": 30,
            "candidate_plans": ["a", "b"],
            "action_success": True,
            "utility": 0.8
        })
        assert score > 0.6
    
    def test_slow_cycle_low_efficiency(self):
        scorer = EfficiencyScorer()
        score = scorer.calculate({
            "cycle_time_ms": 1000,
            "candidate_plans": ["a", "b", "c", "d", "e", "f", "g"],
            "tool_usage_summary": {"tools_used": 10}
        })
        assert score < 0.6
    
    def test_average_cycle_time(self):
        scorer = EfficiencyScorer()
        scorer.calculate({"cycle_time_ms": 100})
        scorer.calculate({"cycle_time_ms": 200})
        
        avg = scorer.get_average_cycle_time()
        assert avg == 150.0


class TestQualityScorer:
    """QualityScorer tests."""
    
    def test_successful_outcome(self):
        scorer = QualityScorer()
        score = scorer.calculate({
            "action_success": True,
            "utility": 0.8,
            "ethmor_decision": "allow"
        })
        assert score > 0.6
    
    def test_failed_outcome(self):
        scorer = QualityScorer()
        score = scorer.calculate({
            "action_success": False,
            "utility": 0.3
        })
        assert score < 0.5
    
    def test_blocked_action(self):
        scorer = QualityScorer()
        score = scorer.calculate({
            "ethmor_decision": "block",
            "risk_level": 0.8
        })
        assert score < 0.4
    
    def test_success_rate(self):
        scorer = QualityScorer()
        scorer.calculate({"action_success": True})
        scorer.calculate({"action_success": True})
        scorer.calculate({"action_success": False})
        
        rate = scorer.get_success_rate()
        assert rate == pytest.approx(2/3, rel=0.01)


class TestTrustAggregator:
    """TrustAggregator tests."""
    
    def test_update_new_source(self):
        aggregator = TrustAggregator()
        score = aggregator.update("source_1", 0.8)
        assert score == 0.8
    
    def test_update_existing_source(self):
        aggregator = TrustAggregator(decay_factor=0.5)
        aggregator.update("source_1", 0.8)
        score = aggregator.update("source_1", 0.6)
        # Should be weighted average
        assert 0.6 <= score <= 0.8
    
    def test_get_average_trust(self):
        aggregator = TrustAggregator()
        aggregator.update("source_1", 0.8)
        aggregator.update("source_2", 0.6)
        
        avg = aggregator.get_average_trust()
        assert avg == 0.7
    
    def test_low_trust_sources(self):
        aggregator = TrustAggregator()
        aggregator.update("good", 0.9)
        aggregator.update("bad", 0.2)
        
        low = aggregator.get_low_trust_sources(threshold=0.4)
        assert "bad" in low
        assert "good" not in low


# ==================== Pattern Tests ====================

class TestFailureTracker:
    """FailureTracker tests."""
    
    def test_record_success(self):
        tracker = FailureTracker()
        result = tracker.record(success=True, action_name="explore")
        
        assert result["success"] is True
        assert tracker.current_streak == 0
    
    def test_record_failure(self):
        tracker = FailureTracker()
        result = tracker.record(success=False, action_name="attack")
        
        assert result["success"] is False
        assert tracker.current_streak == 1
    
    def test_failure_streak(self):
        tracker = FailureTracker()
        
        for i in range(5):
            tracker.record(success=False, action_name="fail")
        
        assert tracker.current_streak == 5
        assert tracker.max_streak == 5
    
    def test_streak_broken(self):
        tracker = FailureTracker()
        tracker.record(success=False)
        tracker.record(success=False)
        result = tracker.record(success=True)
        
        assert result["streak_broken"] is True
        assert tracker.current_streak == 0
    
    def test_alert_threshold(self):
        tracker = FailureTracker(streak_alert_threshold=3)
        
        tracker.record(success=False)
        tracker.record(success=False)
        result = tracker.record(success=False)
        
        assert result["alert"] is True
    
    def test_failure_rate(self):
        tracker = FailureTracker()
        tracker.record(success=True)
        tracker.record(success=False)
        tracker.record(success=True)
        tracker.record(success=False)
        
        rate = tracker.get_failure_rate()
        assert rate == 0.5


class TestActionAnalyzer:
    """ActionAnalyzer tests."""
    
    def test_record_action(self):
        analyzer = ActionAnalyzer()
        analyzer.record("explore")
        analyzer.record("wait")
        
        assert analyzer.get_dominant_action() in ["explore", "wait"]
    
    def test_is_repeated(self):
        analyzer = ActionAnalyzer()
        analyzer.record("wait")
        analyzer.record("wait")
        analyzer.record("wait")
        
        assert analyzer.is_repeated(threshold=3) is True
    
    def test_not_repeated(self):
        analyzer = ActionAnalyzer()
        analyzer.record("explore")
        analyzer.record("wait")
        analyzer.record("flee")
        
        assert analyzer.is_repeated() is False
    
    def test_diversity_score(self):
        analyzer = ActionAnalyzer()
        analyzer.record("a")
        analyzer.record("b")
        analyzer.record("c")
        analyzer.record("d")
        
        diversity = analyzer.get_diversity_score()
        assert diversity == 1.0
    
    def test_low_diversity(self):
        analyzer = ActionAnalyzer()
        for _ in range(5):
            analyzer.record("same")
        
        diversity = analyzer.get_diversity_score()
        assert diversity == 0.2
    
    def test_is_stuck(self):
        analyzer = ActionAnalyzer()
        for _ in range(6):
            analyzer.record("stuck_action")
        
        assert analyzer.is_stuck(threshold=5) is True
    
    def test_detect_sequences(self):
        analyzer = ActionAnalyzer()
        # Create pattern: a, b, a, b, a, b
        for _ in range(3):
            analyzer.record("a")
            analyzer.record("b")
        
        patterns = analyzer.detect_sequences(length=2)
        assert len(patterns) > 0


class TestTrendAnalyzer:
    """TrendAnalyzer tests."""
    
    def test_rising_trend(self):
        analyzer = TrendAnalyzer(stability_threshold=0.05, volatility_threshold=0.5)
        for i in range(10):
            analyzer.add(i * 0.1)  # 0.0, 0.1, 0.2, ... 0.9
        
        assert analyzer.get_trend() == TrendDirection.RISING
    
    def test_falling_trend(self):
        analyzer = TrendAnalyzer(stability_threshold=0.05, volatility_threshold=0.5)
        for i in range(10):
            analyzer.add(1.0 - i * 0.1)  # 1.0, 0.9, 0.8, ... 0.1
        
        assert analyzer.get_trend() == TrendDirection.FALLING
    
    def test_stable_trend(self):
        analyzer = TrendAnalyzer(stability_threshold=0.05, volatility_threshold=0.5)
        for _ in range(10):
            analyzer.add(0.5)
        
        assert analyzer.get_trend() == TrendDirection.STABLE
    
    def test_volatile_trend(self):
        analyzer = TrendAnalyzer(volatility_threshold=0.2)
        values = [0.1, 0.9, 0.2, 0.8, 0.3, 0.7, 0.2, 0.9, 0.1, 0.8]
        for v in values:
            analyzer.add(v)
        
        assert analyzer.get_trend() == TrendDirection.VOLATILE
    
    def test_get_slope(self):
        analyzer = TrendAnalyzer(volatility_threshold=0.5)
        analyzer.add(0.0)
        analyzer.add(0.5)
        analyzer.add(1.0)
        
        slope = analyzer.get_slope()
        assert slope > 0
    
    def test_get_summary(self):
        analyzer = TrendAnalyzer(volatility_threshold=0.5)
        analyzer.add(0.5)
        analyzer.add(0.6)
        
        summary = analyzer.get_summary()
        assert "trend" in summary
        assert "slope" in summary
        assert "volatility" in summary


# ==================== Alert Tests ====================

class TestAlertManager:
    """AlertManager tests."""
    
    def test_check_no_alerts(self):
        manager = AlertManager()
        alerts = manager.check({"coherence_score": 0.8, "cycle_time_ms": 50})
        assert len(alerts) == 0
    
    def test_check_failure_streak_alert(self):
        manager = AlertManager()
        alerts = manager.check({"failure_streak": 5})
        
        assert len(alerts) == 1
        assert alerts[0].alert_type == "high_failure_streak"
        assert alerts[0].severity == AlertSeverity.WARNING
    
    def test_check_critical_failure_streak(self):
        manager = AlertManager()
        alerts = manager.check({"failure_streak": 12})
        
        # Should trigger both warning and critical
        types = [a.alert_type for a in alerts]
        assert "critical_failure_streak" in types
    
    def test_check_slow_cycle(self):
        manager = AlertManager()
        alerts = manager.check({"cycle_time_ms": 600})
        
        assert len(alerts) == 1
        assert alerts[0].category == AlertCategory.PERFORMANCE
    
    def test_check_low_coherence(self):
        manager = AlertManager()
        alerts = manager.check({"coherence_score": 0.2})
        
        assert len(alerts) == 1
        assert alerts[0].alert_type == "low_coherence"
    
    def test_cooldown(self):
        manager = AlertManager()
        
        # First check triggers alert
        alerts1 = manager.check({"failure_streak": 5}, cycle_id=1)
        assert len(alerts1) == 1
        
        # Second check within cooldown - no alert
        alerts2 = manager.check({"failure_streak": 5}, cycle_id=2)
        assert len(alerts2) == 0
    
    def test_acknowledge_alert(self):
        manager = AlertManager()
        alerts = manager.check({"failure_streak": 5})
        
        success = manager.acknowledge(alerts[0].alert_id, by="test")
        assert success is True
        
        alert = manager.get_active_alerts()[0]
        assert alert.acknowledged is True
    
    def test_resolve_alert(self):
        manager = AlertManager()
        alerts = manager.check({"failure_streak": 5})
        alert_id = alerts[0].alert_id
        
        manager.resolve(alert_id)
        
        active = manager.get_active_alerts()
        assert len(active) == 0
    
    def test_get_alert_counts(self):
        manager = AlertManager()
        manager.check({"failure_streak": 5})  # warning
        manager.check({"failure_streak": 12}, cycle_id=10)  # critical (avoid cooldown)
        
        counts = manager.get_alert_counts()
        assert counts["total"] >= 1
    
    def test_callback(self):
        manager = AlertManager()
        received_alerts = []
        
        manager.register_callback(lambda a: received_alerts.append(a))
        manager.check({"failure_streak": 5})
        
        assert len(received_alerts) == 1
    
    def test_alert_to_dict(self):
        manager = AlertManager()
        alerts = manager.check({"failure_streak": 5})
        
        d = alerts[0].to_dict()
        assert "alert_id" in d
        assert "severity" in d
        assert d["severity"] == "warning"
