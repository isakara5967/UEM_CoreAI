"""Tests for uem_predata/session module - Phase C."""
import pytest
import sys
sys.path.insert(0, '.')

from core.predata.session import (
    SessionStageDetector, SessionStage,
    GoalClarityScorer,
    InteractionModeClassifier, InteractionMode,
    EngagementTracker, EngagementLevel,
    ExperimentManager,
)
from core.predata.session.experiment import Experiment


# ==================== Session Stage Tests ====================

class TestSessionStageDetector:
    """SessionStageDetector tests."""
    
    def test_init_stage(self):
        detector = SessionStageDetector()
        stage = detector.detect(cycle_count=1)
        assert stage == SessionStage.INIT
    
    def test_early_stage(self):
        detector = SessionStageDetector()
        stage = detector.detect(cycle_count=3)
        assert stage == SessionStage.EARLY
    
    def test_mid_stage(self):
        detector = SessionStageDetector()
        stage = detector.detect(cycle_count=10)
        assert stage == SessionStage.MID
    
    def test_late_stage(self):
        detector = SessionStageDetector()
        stage = detector.detect(cycle_count=25)
        assert stage == SessionStage.LATE
    
    def test_closing_signal_english(self):
        detector = SessionStageDetector()
        detector.detect(cycle_count=5)  # Set to EARLY
        stage = detector.detect(user_message="Thanks, goodbye!")
        assert stage == SessionStage.CLOSING
    
    def test_closing_signal_turkish(self):
        detector = SessionStageDetector()
        detector.detect(cycle_count=5)
        stage = detector.detect(user_message="Teşekkürler, görüşürüz")
        assert stage == SessionStage.CLOSING
    
    def test_transitions_recorded(self):
        detector = SessionStageDetector()
        detector.detect(cycle_count=1)
        detector.detect(cycle_count=6)
        detector.detect(cycle_count=25)
        
        assert len(detector.transitions) >= 2
    
    def test_reset(self):
        detector = SessionStageDetector()
        detector.detect(cycle_count=10)
        detector.reset()
        
        assert detector.current_stage == SessionStage.INIT
        assert len(detector.transitions) == 0


# ==================== Goal Clarity Tests ====================

class TestGoalClarityScorer:
    """GoalClarityScorer tests."""
    
    def test_clear_message(self):
        scorer = GoalClarityScorer()
        score = scorer.score("Please write a Python function that sorts a list of integers in ascending order")
        assert score > 0.5
    
    def test_vague_message(self):
        scorer = GoalClarityScorer()
        score = scorer.score("Can you help me with something?")
        assert score < 0.6
    
    def test_empty_message(self):
        scorer = GoalClarityScorer()
        score = scorer.score("")
        assert score == 0.0
    
    def test_very_short_message(self):
        scorer = GoalClarityScorer()
        score = scorer.score("Hi")
        assert score < 0.5
    
    def test_message_with_code(self):
        scorer = GoalClarityScorer()
        score = scorer.score("Fix this code: ```python\ndef foo(): pass```", context={"has_code": True})
        assert score > 0.5
    
    def test_get_average(self):
        scorer = GoalClarityScorer()
        scorer.score("Clear message with specific details")
        scorer.score("Another clear request")
        avg = scorer.get_average()
        assert 0.0 <= avg <= 1.0
    
    def test_get_trend(self):
        scorer = GoalClarityScorer()
        # Not enough data
        assert scorer.get_trend() == "insufficient_data"
        
        # Add data
        for _ in range(6):
            scorer.score("Some message here")
        
        trend = scorer.get_trend()
        assert trend in ["improving", "declining", "stable"]


# ==================== Interaction Mode Tests ====================

class TestInteractionModeClassifier:
    """InteractionModeClassifier tests."""
    
    def test_chat_mode(self):
        classifier = InteractionModeClassifier()
        mode = classifier.classify("Hi, how are you today?")
        assert mode == InteractionMode.CHAT
    
    def test_task_mode(self):
        classifier = InteractionModeClassifier()
        mode = classifier.classify("Please write a function to calculate factorial")
        assert mode == InteractionMode.TASK
    
    def test_exploration_mode(self):
        classifier = InteractionModeClassifier()
        mode = classifier.classify("What is machine learning and how does it work?")
        assert mode == InteractionMode.EXPLORATION
    
    def test_debugging_mode(self):
        classifier = InteractionModeClassifier()
        mode = classifier.classify("I'm getting an error in my code, it's not working")
        assert mode == InteractionMode.DEBUGGING
    
    def test_analysis_mode(self):
        classifier = InteractionModeClassifier()
        mode = classifier.classify("Can you analyze this data and summarize the results?")
        assert mode == InteractionMode.ANALYSIS
    
    def test_get_dominant_mode(self):
        classifier = InteractionModeClassifier()
        classifier.classify("What is X?")
        classifier.classify("How does Y work?")
        classifier.classify("Explain Z")
        
        dominant = classifier.get_dominant_mode()
        assert dominant == InteractionMode.EXPLORATION
    
    def test_mode_distribution(self):
        classifier = InteractionModeClassifier()
        classifier.classify("Hello")
        classifier.classify("What is AI?")
        
        dist = classifier.get_mode_distribution()
        assert sum(dist.values()) == pytest.approx(1.0)


# ==================== Engagement Tests ====================

class TestEngagementTracker:
    """EngagementTracker tests."""
    
    def test_high_engagement(self):
        tracker = EngagementTracker()
        level = tracker.update(
            message="This is a very detailed message with lots of context and specific requirements that I need help with",
            response_time_ms=2000
        )
        assert level in [EngagementLevel.MEDIUM, EngagementLevel.HIGH, EngagementLevel.VERY_HIGH]  # Long message with fast response
    
    def test_low_engagement(self):
        tracker = EngagementTracker()
        level = tracker.update(
            message="ok",
            response_time_ms=120000  # 2 minutes
        )
        assert level in [EngagementLevel.LOW, EngagementLevel.DISENGAGED]
    
    def test_code_increases_engagement(self):
        tracker = EngagementTracker()
        level = tracker.update(message="Here's my code:\n```python\ndef foo(): pass\n```")
        assert level.value in ["medium", "high", "very_high"]
    
    def test_current_level(self):
        tracker = EngagementTracker()
        tracker.update(message="Test message")
        assert tracker.current_level is not None
    
    def test_average_level(self):
        tracker = EngagementTracker()
        tracker.update(message="Short")
        tracker.update(message="A longer message with more details")
        
        avg = tracker.get_average_level()
        assert avg in list(EngagementLevel)
    
    def test_trend(self):
        tracker = EngagementTracker()
        
        # Not enough data
        assert tracker.get_trend() == "insufficient_data"
        
        # Add increasing engagement
        for i in range(6):
            tracker.update(message="x" * (10 * (i + 1)))
        
        trend = tracker.get_trend()
        assert trend in ["increasing", "decreasing", "stable"]


# ==================== Experiment Manager Tests ====================

class TestExperimentManager:
    """ExperimentManager tests."""
    
    def test_register_experiment(self):
        manager = ExperimentManager()
        exp = Experiment(
            experiment_id="exp_001",
            name="Test Experiment",
            buckets=["control", "treatment"]
        )
        manager.register_experiment(exp)
        
        assert manager.get_experiment("exp_001") is not None
    
    def test_assign_bucket(self):
        manager = ExperimentManager(seed=42)
        exp = Experiment(
            experiment_id="exp_001",
            name="Test",
            buckets=["control", "treatment"]
        )
        manager.register_experiment(exp)
        
        bucket = manager.assign("exp_001", user_id="user_123")
        assert bucket in ["control", "treatment"]
    
    def test_consistent_assignment(self):
        manager = ExperimentManager()
        exp = Experiment(
            experiment_id="exp_001",
            name="Test",
            buckets=["a", "b", "c"]
        )
        manager.register_experiment(exp)
        
        # Same user should get same bucket
        bucket1 = manager.assign("exp_001", user_id="user_123")
        bucket2 = manager.assign("exp_001", user_id="user_123")
        assert bucket1 == bucket2
    
    def test_different_users_vary(self):
        manager = ExperimentManager()
        exp = Experiment(
            experiment_id="exp_001",
            name="Test",
            buckets=["a", "b"]
        )
        manager.register_experiment(exp)
        
        # Assign many users
        buckets = set()
        for i in range(20):
            bucket = manager.assign("exp_001", user_id=f"user_{i}")
            buckets.add(bucket)
        
        # Should have variation
        assert len(buckets) == 2
    
    def test_weighted_buckets(self):
        manager = ExperimentManager(seed=42)
        exp = Experiment(
            experiment_id="exp_001",
            name="Test",
            buckets=["control", "treatment"],
            weights=[0.9, 0.1]  # 90% control
        )
        manager.register_experiment(exp)
        
        counts = {"control": 0, "treatment": 0}
        for i in range(100):
            bucket = manager.assign("exp_001", user_id=f"user_{i}")
            counts[bucket] += 1
        
        # Control should be much higher
        assert counts["control"] > counts["treatment"]
    
    def test_force_bucket(self):
        manager = ExperimentManager()
        exp = Experiment(
            experiment_id="exp_001",
            name="Test",
            buckets=["a", "b"]
        )
        manager.register_experiment(exp)
        
        bucket = manager.assign("exp_001", user_id="user_123", force_bucket="b")
        assert bucket == "b"
    
    def test_disabled_experiment(self):
        manager = ExperimentManager()
        exp = Experiment(
            experiment_id="exp_001",
            name="Test",
            buckets=["a", "b"],
            enabled=False
        )
        manager.register_experiment(exp)
        
        bucket = manager.assign("exp_001", user_id="user_123")
        assert bucket is None
    
    def test_get_all_assignments(self):
        manager = ExperimentManager()
        
        for i in range(3):
            exp = Experiment(
                experiment_id=f"exp_{i}",
                name=f"Test {i}",
                buckets=["a", "b"]
            )
            manager.register_experiment(exp)
            manager.assign(f"exp_{i}", user_id="user_123")
        
        assignments = manager.get_all_assignments("user_123")
        assert len(assignments) == 3
    
    def test_experiment_stats(self):
        manager = ExperimentManager()
        exp = Experiment(
            experiment_id="exp_001",
            name="Test",
            buckets=["control", "treatment"]
        )
        manager.register_experiment(exp)
        
        for i in range(10):
            manager.assign("exp_001", user_id=f"user_{i}")
        
        stats = manager.get_experiment_stats("exp_001")
        assert stats["total_assignments"] == 10
        assert sum(stats["bucket_counts"].values()) == 10
