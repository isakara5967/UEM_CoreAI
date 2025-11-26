# tests/test_empathy.py
"""
Empathy Module Tests

Tests for EmpathyOrchestrator v1 with:
- Weighted average empathy calculation
- Valence-based resonance
- Confidence scoring
- Edge cases (no experiences)

Author: UEM Project (Efe)
Date: 26 November 2025
"""

import pytest
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


# ============================================================================
# MOCK CLASSES
# ============================================================================

@dataclass
class MockEmotionCore:
    """Mock EmotionCore with valence."""
    valence: float = 0.0
    arousal: float = 0.0


class MockMemoryInterface:
    """Mock MemoryInterface for testing."""
    
    def __init__(self, experiences: Optional[List[Dict]] = None):
        self.experiences = experiences or []
        self.call_count = 0
    
    def get_similar_experiences(
        self,
        state_vector: tuple,
        tolerance: float = 0.3,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        self.call_count += 1
        return self.experiences[:limit]


class MockSelfSystem:
    """Mock SelfCore for testing."""
    
    def __init__(self, state_vector: tuple = (0.5, 0.0, 0.5)):
        self._state_vector = state_vector
    
    def get_state_vector(self):
        return self._state_vector


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def other_entity():
    """Create a test OtherEntity."""
    from core.empathy.empathy_orchestrator import OtherEntity
    return OtherEntity(
        entity_id="npc_001",
        state_vector=(0.3, 0.8, 0.2),  # Low resource, high threat, low wellbeing
        valence=-0.6,  # Negative emotion
        relationship=0.0,
    )


@pytest.fixture
def empathy_orchestrator():
    """Create basic EmpathyOrchestrator."""
    from core.empathy.empathy_orchestrator import EmpathyOrchestrator
    return EmpathyOrchestrator()


@pytest.fixture
def empathy_with_memory():
    """Create EmpathyOrchestrator with mock memory."""
    from core.empathy.empathy_orchestrator import EmpathyOrchestrator
    
    experiences = [
        {'similarity': 0.9, 'salience': 0.8, 'state_vector': (0.35, 0.75, 0.25)},
        {'similarity': 0.7, 'salience': 0.6, 'state_vector': (0.4, 0.7, 0.3)},
        {'similarity': 0.5, 'salience': 0.4, 'state_vector': (0.5, 0.5, 0.4)},
    ]
    
    memory = MockMemoryInterface(experiences)
    emotion = MockEmotionCore(valence=-0.5)  # Similar valence to other
    
    return EmpathyOrchestrator(
        memory_interface=memory,
        emotion_system=emotion,
    ), memory


# ============================================================================
# BASIC TESTS
# ============================================================================

class TestEmpathyBasic:
    """Basic EmpathyOrchestrator tests."""
    
    def test_create_orchestrator(self, empathy_orchestrator):
        """Should create orchestrator without errors."""
        assert empathy_orchestrator is not None
    
    def test_compute_returns_result(self, empathy_orchestrator, other_entity):
        """compute() should return EmpathyResult."""
        from core.empathy.empathy_orchestrator import EmpathyResult
        
        result = empathy_orchestrator.compute(other_entity)
        
        assert isinstance(result, EmpathyResult)
        assert hasattr(result, 'empathy_level')
        assert hasattr(result, 'resonance')
        assert hasattr(result, 'confidence')
    
    def test_result_has_other_entity(self, empathy_orchestrator, other_entity):
        """Result should contain the other entity."""
        result = empathy_orchestrator.compute(other_entity)
        
        assert result.other_entity == other_entity


# ============================================================================
# EMPATHY LEVEL TESTS
# ============================================================================

class TestEmpathyLevel:
    """Empathy level calculation tests."""
    
    def test_no_experiences_returns_zero(self, empathy_orchestrator, other_entity):
        """No similar experiences should return empathy=0."""
        result = empathy_orchestrator.compute(other_entity)
        
        assert result.empathy_level == 0.0
    
    def test_weighted_average_calculation(self, empathy_with_memory, other_entity):
        """Empathy should be weighted average of similarities."""
        orchestrator, memory = empathy_with_memory
        
        result = orchestrator.compute(other_entity)
        
        # Manual calculation:
        # exp1: sim=0.9, sal=0.8 → weighted=0.72, weight=0.8
        # exp2: sim=0.7, sal=0.6 → weighted=0.42, weight=0.6
        # exp3: sim=0.5, sal=0.4 → weighted=0.20, weight=0.4
        # sum_weighted = 1.34, sum_weight = 1.8
        # empathy = 1.34 / 1.8 = 0.744
        
        assert result.empathy_level == pytest.approx(0.744, rel=0.01)
    
    def test_empathy_clamped_to_0_1(self, empathy_with_memory, other_entity):
        """Empathy level should be clamped to [0, 1]."""
        orchestrator, _ = empathy_with_memory
        
        result = orchestrator.compute(other_entity)
        
        assert 0.0 <= result.empathy_level <= 1.0
    
    def test_high_salience_weights_more(self):
        """Higher salience experiences should have more weight."""
        from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
        
        # Two experiences with same similarity but different salience
        experiences = [
            {'similarity': 0.8, 'salience': 0.9, 'state_vector': (0.3, 0.8, 0.2)},
            {'similarity': 0.4, 'salience': 0.1, 'state_vector': (0.5, 0.5, 0.5)},
        ]
        
        memory = MockMemoryInterface(experiences)
        orchestrator = EmpathyOrchestrator(memory_interface=memory)
        other = OtherEntity(entity_id="test", state_vector=(0.3, 0.8, 0.2), valence=0.0)
        
        result = orchestrator.compute(other)
        
        # High salience (0.9) should dominate
        # Expected: (0.8*0.9 + 0.4*0.1) / (0.9 + 0.1) = 0.76
        assert result.empathy_level == pytest.approx(0.76, rel=0.01)


# ============================================================================
# RESONANCE TESTS
# ============================================================================

class TestResonance:
    """Resonance calculation tests."""
    
    def test_same_valence_high_resonance(self):
        """Same valence should give resonance=1."""
        from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
        
        emotion = MockEmotionCore(valence=0.5)
        orchestrator = EmpathyOrchestrator(emotion_system=emotion)
        
        other = OtherEntity(
            entity_id="test",
            state_vector=(0.5, 0.5, 0.5),
            valence=0.5,  # Same as self
        )
        
        result = orchestrator.compute(other)
        
        assert result.resonance == pytest.approx(1.0, rel=0.01)
    
    def test_opposite_valence_low_resonance(self):
        """Opposite valence should give low resonance."""
        from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
        
        emotion = MockEmotionCore(valence=1.0)  # Very positive
        orchestrator = EmpathyOrchestrator(emotion_system=emotion)
        
        other = OtherEntity(
            entity_id="test",
            state_vector=(0.5, 0.5, 0.5),
            valence=-1.0,  # Very negative
        )
        
        result = orchestrator.compute(other)
        
        # Difference = 2.0, normalized: 1 - (2/2) = 0
        assert result.resonance == pytest.approx(0.0, rel=0.01)
    
    def test_partial_valence_difference(self):
        """Partial valence difference should give partial resonance."""
        from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
        
        emotion = MockEmotionCore(valence=0.0)
        orchestrator = EmpathyOrchestrator(emotion_system=emotion)
        
        other = OtherEntity(
            entity_id="test",
            state_vector=(0.5, 0.5, 0.5),
            valence=-0.5,
        )
        
        result = orchestrator.compute(other)
        
        # Difference = 0.5, normalized: 1 - (0.5/2) = 0.75
        assert result.resonance == pytest.approx(0.75, rel=0.01)
    
    def test_no_emotion_system_defaults_to_neutral(self):
        """Without emotion system, valence defaults to 0."""
        from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
        
        orchestrator = EmpathyOrchestrator()  # No emotion system
        
        other = OtherEntity(
            entity_id="test",
            state_vector=(0.5, 0.5, 0.5),
            valence=0.0,
        )
        
        result = orchestrator.compute(other)
        
        # Both neutral → resonance = 1
        assert result.resonance == pytest.approx(1.0, rel=0.01)


# ============================================================================
# CONFIDENCE TESTS
# ============================================================================

class TestConfidence:
    """Confidence calculation tests."""
    
    def test_no_experiences_zero_confidence(self, empathy_orchestrator, other_entity):
        """No experiences should give confidence=0."""
        result = empathy_orchestrator.compute(other_entity)
        
        assert result.confidence == 0.0
    
    def test_confidence_increases_with_experiences(self):
        """More experiences should increase confidence."""
        from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
        
        other = OtherEntity(entity_id="test", state_vector=(0.5, 0.5, 0.5), valence=0.0)
        
        # Few experiences
        exp_few = [{'similarity': 0.8, 'salience': 0.5, 'state_vector': (0.5, 0.5, 0.5)}]
        mem_few = MockMemoryInterface(exp_few)
        orch_few = EmpathyOrchestrator(memory_interface=mem_few)
        result_few = orch_few.compute(other)
        
        # Many experiences
        exp_many = [
            {'similarity': 0.8, 'salience': 0.5, 'state_vector': (0.5, 0.5, 0.5)}
            for _ in range(5)
        ]
        mem_many = MockMemoryInterface(exp_many)
        orch_many = EmpathyOrchestrator(memory_interface=mem_many)
        result_many = orch_many.compute(other)
        
        assert result_many.confidence > result_few.confidence
    
    def test_confidence_clamped_to_0_1(self, empathy_with_memory, other_entity):
        """Confidence should be clamped to [0, 1]."""
        orchestrator, _ = empathy_with_memory
        
        result = orchestrator.compute(other_entity)
        
        assert 0.0 <= result.confidence <= 1.0
    
    def test_high_salience_increases_confidence(self):
        """Higher salience experiences should increase confidence."""
        from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
        
        other = OtherEntity(entity_id="test", state_vector=(0.5, 0.5, 0.5), valence=0.0)
        
        # Low salience
        exp_low = [{'similarity': 0.8, 'salience': 0.2, 'state_vector': (0.5, 0.5, 0.5)}]
        mem_low = MockMemoryInterface(exp_low)
        orch_low = EmpathyOrchestrator(memory_interface=mem_low)
        result_low = orch_low.compute(other)
        
        # High salience
        exp_high = [{'similarity': 0.8, 'salience': 0.9, 'state_vector': (0.5, 0.5, 0.5)}]
        mem_high = MockMemoryInterface(exp_high)
        orch_high = EmpathyOrchestrator(memory_interface=mem_high)
        result_high = orch_high.compute(other)
        
        assert result_high.confidence > result_low.confidence


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Edge case tests."""
    
    def test_zero_salience_handled(self):
        """Zero salience experiences should be handled."""
        from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
        
        experiences = [
            {'similarity': 0.8, 'salience': 0.0, 'state_vector': (0.5, 0.5, 0.5)},
        ]
        
        memory = MockMemoryInterface(experiences)
        orchestrator = EmpathyOrchestrator(memory_interface=memory)
        other = OtherEntity(entity_id="test", state_vector=(0.5, 0.5, 0.5), valence=0.0)
        
        result = orchestrator.compute(other)
        
        # Should not crash, empathy should be 0 (no weight)
        assert result.empathy_level == 0.0
    
    def test_missing_salience_defaults_to_half(self):
        """Missing salience should default to 0.5."""
        from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
        
        experiences = [
            {'similarity': 0.8, 'state_vector': (0.5, 0.5, 0.5)},  # No salience
        ]
        
        memory = MockMemoryInterface(experiences)
        orchestrator = EmpathyOrchestrator(memory_interface=memory)
        other = OtherEntity(entity_id="test", state_vector=(0.5, 0.5, 0.5), valence=0.0)
        
        result = orchestrator.compute(other)
        
        # Should use default salience 0.5
        # empathy = 0.8 * 0.5 / 0.5 = 0.8
        assert result.empathy_level == pytest.approx(0.8, rel=0.01)
    
    def test_result_to_dict(self, empathy_with_memory, other_entity):
        """to_dict() should return serializable dict."""
        orchestrator, _ = empathy_with_memory
        
        result = orchestrator.compute(other_entity)
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert 'empathy_level' in result_dict
        assert 'resonance' in result_dict
        assert 'confidence' in result_dict
        assert 'other_entity_id' in result_dict


# ============================================================================
# STATISTICS TESTS
# ============================================================================

class TestStatistics:
    """Statistics tracking tests."""
    
    def test_computation_count_tracked(self, empathy_with_memory, other_entity):
        """Computation count should be tracked."""
        orchestrator, _ = empathy_with_memory
        
        orchestrator.compute(other_entity)
        orchestrator.compute(other_entity)
        orchestrator.compute(other_entity)
        
        stats = orchestrator.get_stats()
        assert stats['computations'] == 3
    
    def test_zero_experience_count_tracked(self, empathy_orchestrator, other_entity):
        """Zero experience computations should be tracked."""
        orchestrator = empathy_orchestrator
        
        orchestrator.compute(other_entity)
        orchestrator.compute(other_entity)
        
        stats = orchestrator.get_stats()
        assert stats['zero_experience_count'] == 2
    
    def test_reset_stats(self, empathy_with_memory, other_entity):
        """reset_stats() should clear all statistics."""
        orchestrator, _ = empathy_with_memory
        
        orchestrator.compute(other_entity)
        orchestrator.reset_stats()
        
        stats = orchestrator.get_stats()
        assert stats['computations'] == 0


# ============================================================================
# FACTORY TESTS
# ============================================================================

class TestFactory:
    """Factory function tests."""
    
    def test_create_empathy_orchestrator(self):
        """Factory should create orchestrator."""
        from core.empathy.empathy_orchestrator import create_empathy_orchestrator
        
        orchestrator = create_empathy_orchestrator()
        assert orchestrator is not None
    
    def test_factory_with_dependencies(self):
        """Factory should accept dependencies."""
        from core.empathy.empathy_orchestrator import create_empathy_orchestrator
        
        memory = MockMemoryInterface()
        emotion = MockEmotionCore()
        
        orchestrator = create_empathy_orchestrator(
            memory_interface=memory,
            emotion_system=emotion,
        )
        
        assert orchestrator.memory_interface is memory
        assert orchestrator.emotion_system is emotion


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests."""
    
    def test_full_empathy_scenario(self):
        """Test realistic empathy scenario."""
        from core.empathy.empathy_orchestrator import (
            EmpathyOrchestrator,
            OtherEntity,
        )
        
        # Setup: UEM has experienced distress before
        past_experiences = [
            {
                'similarity': 0.85,
                'salience': 0.9,  # Very memorable
                'state_vector': (0.25, 0.85, 0.15),  # Past distress
            },
            {
                'similarity': 0.6,
                'salience': 0.5,
                'state_vector': (0.4, 0.6, 0.35),
            },
        ]
        
        memory = MockMemoryInterface(past_experiences)
        emotion = MockEmotionCore(valence=-0.3)  # Currently slightly negative
        
        orchestrator = EmpathyOrchestrator(
            memory_interface=memory,
            emotion_system=emotion,
        )
        
        # Observe: NPC in distress
        distressed_npc = OtherEntity(
            entity_id="injured_villager",
            state_vector=(0.2, 0.9, 0.1),  # Very distressed
            valence=-0.7,  # Very negative
            relationship=0.3,  # Friendly
        )
        
        result = orchestrator.compute(distressed_npc)
        
        # Assertions
        assert result.empathy_level > 0.7, "Should have high empathy (similar past)"
        assert result.resonance > 0.5, "Should have decent resonance (both negative)"
        assert result.confidence > 0.1, "Should have some confidence"
        assert len(result.similar_memories) == 2
    
    def test_low_empathy_unfamiliar_situation(self):
        """Test empathy for unfamiliar situation."""
        from core.empathy.empathy_orchestrator import (
            EmpathyOrchestrator,
            OtherEntity,
        )
        
        # Setup: No similar experiences
        memory = MockMemoryInterface([])  # Empty
        emotion = MockEmotionCore(valence=0.5)  # Happy
        
        orchestrator = EmpathyOrchestrator(
            memory_interface=memory,
            emotion_system=emotion,
        )
        
        # Observe: Entity in unusual state
        unusual_entity = OtherEntity(
            entity_id="alien",
            state_vector=(0.1, 0.1, 0.9),  # Unusual combination
            valence=0.0,  # Neutral
        )
        
        result = orchestrator.compute(unusual_entity)
        
        # Assertions
        assert result.empathy_level == 0.0, "No similar experiences = no empathy"
        assert result.confidence == 0.0, "No experiences = no confidence"
        assert result.resonance > 0.5, "Valence still somewhat similar"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
