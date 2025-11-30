# tests/test_perception_predata.py
"""
Tests for Perception PreData Calculator.

Author: UEM Project
Date: 30 November 2025
"""

import pytest
import sys
sys.path.insert(0, '.')

from core.perception.predata_calculator import (
    PerceptionPreDataCalculator,
    PerceptionPreDataConfig,
)


class TestPerceptionPreDataCalculator:
    
    def test_first_cycle_neutral_novelty(self):
        """First cycle should have neutral novelty score."""
        calc = PerceptionPreDataCalculator()
        result = calc.compute(
            objects=[{'type': 'rock', 'distance': 5}],
            agents=[],
            danger_level=0.0,
        )
        assert result['novelty_score'] == 0.5
    
    def test_novelty_increases_with_new_objects(self):
        """Novelty should increase when new object types appear."""
        calc = PerceptionPreDataCalculator()
        
        # First cycle
        calc.compute(objects=[{'type': 'rock'}], agents=[], danger_level=0.0)
        
        # Second cycle with new object type
        result = calc.compute(
            objects=[{'type': 'enemy'}],
            agents=[],
            danger_level=0.0,
        )
        assert result['novelty_score'] > 0.0
    
    def test_salience_map_danger(self):
        """High danger should appear in salience map."""
        calc = PerceptionPreDataCalculator()
        result = calc.compute(
            objects=[],
            agents=[],
            danger_level=0.8,
        )
        assert 'danger' in result['salience_map']
        assert result['salience_map']['danger'] >= 0.7
    
    def test_salience_map_hostile_agents(self):
        """Hostile agents should be salient."""
        calc = PerceptionPreDataCalculator()
        result = calc.compute(
            objects=[],
            agents=[{'id': 'enemy1', 'relation': 'hostile'}],
            danger_level=0.0,
        )
        assert 'hostile_agents' in result['salience_map']
    
    def test_attention_focus_danger_priority(self):
        """High danger should take attention focus priority."""
        calc = PerceptionPreDataCalculator()
        result = calc.compute(
            objects=[{'type': 'rock'}],
            agents=[{'id': 'friend', 'relation': 'friendly'}],
            danger_level=0.9,
        )
        assert result['attention_focus'] == "DANGER"
    
    def test_attention_focus_hostile_agent(self):
        """Hostile agent should be attention focus when danger is low."""
        calc = PerceptionPreDataCalculator()
        result = calc.compute(
            objects=[],
            agents=[{'id': 'enemy1', 'relation': 'hostile'}],
            danger_level=0.3,
        )
        assert "HOSTILE_AGENT" in result['attention_focus']
    
    def test_temporal_context_has_cycle(self):
        """Temporal context should include cycle number."""
        calc = PerceptionPreDataCalculator()
        result = calc.compute(objects=[], agents=[], danger_level=0.0)
        assert 'cycle_number' in result['temporal_context']
        assert result['temporal_context']['cycle_number'] == 1
    
    def test_temporal_context_time_delta(self):
        """Temporal context should track time between cycles."""
        calc = PerceptionPreDataCalculator()
        calc.compute(objects=[], agents=[], danger_level=0.0)
        result = calc.compute(objects=[], agents=[], danger_level=0.0)
        assert 'time_since_last' in result['temporal_context']
    
    def test_perception_confidence_base(self):
        """Perception confidence should start at base level."""
        calc = PerceptionPreDataCalculator()
        result = calc.compute(objects=[], agents=[], danger_level=0.0)
        assert result['perception_confidence'] >= 0.7
    
    def test_perception_confidence_with_noise(self):
        """Noise should reduce perception confidence."""
        calc = PerceptionPreDataCalculator()
        result = calc.compute(
            objects=[],
            agents=[],
            danger_level=0.0,
            environment={'noise_level': 0.5},
        )
        assert result['perception_confidence'] < 0.8
    
    def test_reset(self):
        """Reset should clear history."""
        calc = PerceptionPreDataCalculator()
        calc.compute(objects=[{'type': 'rock'}], agents=[], danger_level=0.0)
        calc.compute(objects=[{'type': 'tree'}], agents=[], danger_level=0.0)
        
        stats_before = calc.get_stats()
        assert stats_before['cycle_count'] == 2
        
        calc.reset()
        stats_after = calc.get_stats()
        assert stats_after['cycle_count'] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
