# tests/test_predata_calculators.py
"""
Tests for PreData Calculator modules.

Author: UEM Project
Date: 30 November 2025
"""

import pytest
import sys
sys.path.insert(0, '.')

from core.emotion.predata_calculator import (
    EmotionPreDataCalculator,
    EmotionPreDataConfig,
)
from core.planning.predata_calculator import (
    PlannerPreDataCalculator,
    UtilityBreakdown,
)
from core.predata.module_calculators import (
    WorkspacePreDataCalculator,
    MemoryPreDataCalculator,
    SelfPreDataCalculator,
)


class TestEmotionPreDataCalculator:
    
    def test_first_cycle_no_delta(self):
        calc = EmotionPreDataCalculator()
        result = calc.compute(valence=0.5, arousal=0.6)
        assert result['valence_delta'] is None
        assert result['arousal_volatility'] is None
    
    def test_valence_delta_calculation(self):
        calc = EmotionPreDataCalculator()
        calc.compute(valence=0.5, arousal=0.5)
        result = calc.compute(valence=0.7, arousal=0.5)
        assert result['valence_delta'] == pytest.approx(0.2, abs=0.001)
    
    def test_arousal_volatility_after_history(self):
        calc = EmotionPreDataCalculator()
        for a in [0.3, 0.5, 0.7, 0.4, 0.6]:
            result = calc.compute(valence=0.5, arousal=a)
        assert result['arousal_volatility'] is not None
        assert 0.0 <= result['arousal_volatility'] <= 0.5
    
    def test_engagement_with_attention(self):
        calc = EmotionPreDataCalculator()
        result = calc.compute(valence=0.5, arousal=0.6, attention_focus=0.8)
        assert result['engagement'] == pytest.approx(0.68, abs=0.01)
    
    def test_mood_baseline_after_history(self):
        calc = EmotionPreDataCalculator()
        for v in [0.4, 0.5, 0.6, 0.5, 0.4, 0.5]:
            result = calc.compute(valence=v, arousal=0.5)
        assert result['mood_baseline'] is not None


class TestPlannerPreDataCalculator:
    
    def test_add_candidates(self):
        calc = PlannerPreDataCalculator()
        calc.add_candidate("flee", 0.8, "Danger")
        calc.add_candidate("attack", 0.5, "Enemy")
        predata = calc.get_predata()
        assert len(predata['candidate_plans']) == 2
        assert predata['candidate_plans'][0]['action'] == "flee"
    
    def test_utility_breakdown(self):
        calc = PlannerPreDataCalculator()
        calc.set_utility_breakdown(base=0.5, goal=0.2, emotion=0.1)
        predata = calc.get_predata()
        assert predata['utility_breakdown']['total'] == pytest.approx(0.8, abs=0.01)
    
    def test_reset(self):
        calc = PlannerPreDataCalculator()
        calc.add_candidate("flee", 0.8)
        calc.reset()
        predata = calc.get_predata()
        assert len(predata['candidate_plans']) == 0


class TestWorkspacePreDataCalculator:
    
    def test_no_competition_single_coalition(self):
        intensity = WorkspacePreDataCalculator.compute_competition_intensity(0.8, 0.8, 1)
        assert intensity == 0.0
    
    def test_high_competition(self):
        intensity = WorkspacePreDataCalculator.compute_competition_intensity(0.3, 1.0, 5)
        assert intensity > 0.5


class TestMemoryPreDataCalculator:
    
    def test_working_memory_load(self):
        load = MemoryPreDataCalculator.compute_working_memory_load(5, 7)
        assert load == pytest.approx(0.714, abs=0.01)
    
    def test_memory_relevance(self):
        relevance = MemoryPreDataCalculator.compute_memory_relevance([0.8, 0.6, 0.7])
        assert relevance == pytest.approx(0.7, abs=0.01)


class TestSelfPreDataCalculator:
    
    def test_confidence_needs_history(self):
        calc = SelfPreDataCalculator()
        calc.record_outcome(True)
        assert calc.compute_confidence_score() is None
    
    def test_confidence_with_successes(self):
        calc = SelfPreDataCalculator()
        for _ in range(5):
            calc.record_outcome(True, 0.1)
        confidence = calc.compute_confidence_score()
        assert confidence is not None
        assert confidence > 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
