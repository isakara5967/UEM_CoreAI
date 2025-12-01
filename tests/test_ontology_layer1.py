# tests/test_ontology_layer1.py
"""
UEM Ontology Layer 1 - Unit Tests

Tests for the 12 core concepts:
- ENTITY: SELF, OTHER, EVENT
- STATE: RESOURCE_LEVEL, THREAT_LEVEL, WELLBEING
- VALUE: BENEFIT, COST, VIOLATION
- RELATION: CAUSES, AFFECTS, SIMILAR
"""

import pytest
import math
from dataclasses import dataclass
from typing import Dict, Any


# =========================================================================
# MOCK CLASSES (WorldState ve EmotionCore benzerleri)
# =========================================================================

@dataclass
class MockWorldState:
    """WorldStateLike protocol'ü implemente eden mock"""
    player_health: float = 1.0
    player_energy: float = 1.0
    danger_level: float = 0.0


@dataclass
class MockEmotionCore:
    """EmotionCoreLike protocol'ü implemente eden mock"""
    valence: float = 0.0  # -1 to +1


class MockEthmor:
    """EthmorLike protocol'ü implemente eden mock"""
    
    def __init__(self, violation_level: float = 0.0):
        self._violation = violation_level
    
    def check_constraint_breach(self, event: Any, context: Dict[str, Any]) -> float:
        return self._violation


# =========================================================================
# IMPORT TESTS
# =========================================================================

class TestOntologyImports:
    """Ontology modülünün import edilebilirliğini test et"""
    
    def test_import_types(self):
        """types.py import edilebilmeli"""
        from core.ontology.types import (
            StateVector,
            StateDelta,
            Event,
            Goal,
            SelfEntity,
            OtherEntity,
        )
        assert StateVector is not None
        assert Event is not None
    
    def test_import_functions(self):
        """Fonksiyonlar import edilebilmeli"""
        from core.ontology.types import (
            build_state_vector,
            compute_state_delta,
            compute_benefit,
            compute_cost,
            similar,
        )
        assert callable(build_state_vector)
        assert callable(similar)
    
    def test_import_protocols(self):
        """Protocol'ler import edilebilmeli"""
        from core.ontology.types import (
            WorldStateLike,
            EmotionCoreLike,
            EthmorLike,
        )
        assert WorldStateLike is not None


# =========================================================================
# STATE VECTOR TESTS
# =========================================================================

class TestStateVector:
    """StateVector oluşturma ve hesaplama testleri"""
    
    def test_build_state_vector_neutral(self):
        """Nötr durumda state vector hesaplama"""
        from core.ontology.types import build_state_vector
        
        world = MockWorldState(player_health=1.0, player_energy=1.0, danger_level=0.0)
        emotion = MockEmotionCore(valence=0.0)
        
        state = build_state_vector(world, emotion)
        
        assert len(state) == 16
        assert state[0] == 1.0  # RESOURCE_LEVEL = (1+1)/2
        assert state[1] == 0.0  # THREAT_LEVEL = 0
        assert state[2] == 0.5  # WELLBEING = (0+1)/2
    
    def test_build_state_vector_danger(self):
        """Tehlike durumunda state vector hesaplama"""
        from core.ontology.types import build_state_vector
        
        world = MockWorldState(player_health=0.3, player_energy=0.5, danger_level=0.8)
        emotion = MockEmotionCore(valence=-0.6)  # Negative emotion
        
        state = build_state_vector(world, emotion)
        
        assert state[0] == pytest.approx(0.4, rel=0.01)  # (0.3+0.5)/2
        assert state[1] == pytest.approx(0.8, rel=0.01)  # danger_level
        assert state[2] == pytest.approx(0.2, rel=0.01)  # (-0.6+1)/2
    
    def test_build_state_vector_clamping(self):
        """State vector değerleri 0-1 arasında clamp edilmeli"""
        from core.ontology.types import build_state_vector
        
        # Extreme values
        world = MockWorldState(player_health=1.5, player_energy=1.5, danger_level=1.5)
        emotion = MockEmotionCore(valence=1.5)
        
        state = build_state_vector(world, emotion)
        
        assert 0.0 <= state[0] <= 1.0
        assert 0.0 <= state[1] <= 1.0
        assert 0.0 <= state[2] <= 1.0
    
    def test_compute_state_delta(self):
        """İki state vector arasındaki delta hesaplama"""
        from core.ontology.types import compute_state_delta
        
        before = (0.8, 0.2, 0.6)
        after = (0.5, 0.7, 0.4)
        
        delta = compute_state_delta(before, after)
        
        assert delta[0] == pytest.approx(-0.3, rel=0.01)  # resource decreased
        assert delta[1] == pytest.approx(0.5, rel=0.01)   # threat increased
        assert delta[2] == pytest.approx(-0.2, rel=0.01)  # wellbeing decreased


# =========================================================================
# ENTITY TESTS
# =========================================================================

class TestEntities:
    """Entity dataclass testleri"""
    
    def test_self_entity_creation(self):
        """SelfEntity oluşturulabilmeli"""
        from core.ontology.types import SelfEntity, Goal
        
        entity = SelfEntity(
            state_vector=(0.8, 0.1, 0.7),
            history=[],
            goals=[Goal(name="survive", target_state=(1.0, 0.0, 1.0), priority=1.0)]
        )
        
        assert entity.state_vector == (0.8, 0.1, 0.7)
        assert len(entity.goals) == 1
        assert entity.goals[0].name == "survive"
    
    def test_other_entity_creation(self):
        """OtherEntity oluşturulabilmeli"""
        from core.ontology.types import OtherEntity
        
        other = OtherEntity(
            id="enemy_1",
            observed_state=(0.5, 0.9, 0.2),
            predicted_state=(0.4, 0.95, 0.1)
        )
        
        assert other.id == "enemy_1"
        assert other.observed_state[1] == 0.9  # High threat
    
    def test_event_creation(self):
        """Event oluşturulabilmeli"""
        from core.ontology.types import Event
        
        event = Event(
            source="ENVIRONMENT",
            target="SELF",
            effect=(-0.2, 0.3, -0.1),
            timestamp=1234.5
        )
        
        assert event.source == "ENVIRONMENT"
        assert event.effect[0] == -0.2  # Resource loss


# =========================================================================
# VALUE FUNCTION TESTS
# =========================================================================

class TestValueFunctions:
    """VALUE hesaplama fonksiyonları testleri"""
    
    def test_compute_benefit_positive(self):
        """Pozitif wellbeing değişimi = benefit"""
        from core.ontology.types import compute_benefit
        
        benefit = compute_benefit(wellbeing_before=0.3, wellbeing_after=0.7)
        assert benefit == pytest.approx(0.4, rel=0.01)
    
    def test_compute_benefit_negative_returns_zero(self):
        """Negatif wellbeing değişimi = 0 benefit"""
        from core.ontology.types import compute_benefit
        
        benefit = compute_benefit(wellbeing_before=0.7, wellbeing_after=0.3)
        assert benefit == 0.0
    
    def test_compute_cost_positive(self):
        """Pozitif resource kaybı = cost"""
        from core.ontology.types import compute_cost
        
        cost = compute_cost(resource_before=0.8, resource_after=0.5)
        assert cost == pytest.approx(0.3, rel=0.01)
    
    def test_compute_cost_negative_returns_zero(self):
        """Resource artışı = 0 cost"""
        from core.ontology.types import compute_cost
        
        cost = compute_cost(resource_before=0.5, resource_after=0.8)
        assert cost == 0.0
    
    def test_compute_violation(self):
        """ETHMOR violation hesaplama"""
        from core.ontology.types import compute_violation, Event
        
        ethmor = MockEthmor(violation_level=0.7)
        event = Event(source="SELF", target="OTHER:1", effect=(0, 0, -0.5), timestamp=0)
        
        violation = compute_violation(ethmor, event, context={})
        assert violation == 0.7


# =========================================================================
# RELATION FUNCTION TESTS
# =========================================================================

class TestRelationFunctions:
    """RELATION fonksiyonları testleri"""
    
    def test_causes(self):
        """CAUSES: Event → StateDelta"""
        from core.ontology.types import causes, Event
        
        event = Event(
            source="SELF",
            target="SELF",
            effect=(-0.1, 0.2, -0.15),
            timestamp=100.0
        )
        
        delta = causes(event)
        assert delta == (-0.1, 0.2, -0.15)
    
    def test_affects(self):
        """AFFECTS: wellbeing delta hesaplama"""
        from core.ontology.types import affects, SelfEntity, Event
        
        entity = SelfEntity(state_vector=(0.5, 0.3, 0.6), history=[], goals=[])
        event = Event(source="ENV", target="SELF", effect=(0, 0, 0), timestamp=0)
        
        delta = affects(entity, event, wellbeing_before=0.6, wellbeing_after=0.4)
        assert delta == pytest.approx(-0.2, rel=0.01)
    
    def test_similar_identical(self):
        """SIMILAR: Aynı vektörler = 1.0"""
        from core.ontology.types import similar
        
        state_a = (0.5, 0.3, 0.7)
        state_b = (0.5, 0.3, 0.7)
        
        sim = similar(state_a, state_b)
        assert sim == pytest.approx(1.0, rel=0.01)
    
    def test_similar_orthogonal(self):
        """SIMILAR: Farklı vektörler < 1.0"""
        from core.ontology.types import similar
        
        state_a = (1.0, 0.0, 0.0)
        state_b = (0.0, 1.0, 0.0)
        
        sim = similar(state_a, state_b)
        assert sim == pytest.approx(0.0, rel=0.01)
    
    def test_similar_opposite(self):
        """SIMILAR: Zıt yönlü vektörler"""
        from core.ontology.types import similar
        
        # Not truly opposite since values are 0-1, but different
        state_a = (0.9, 0.1, 0.8)
        state_b = (0.1, 0.9, 0.2)
        
        sim = similar(state_a, state_b)
        assert 0.0 < sim < 1.0  # Some similarity due to all positive
    
    def test_similar_zero_vector(self):
        """SIMILAR: Sıfır vektör = 0 similarity"""
        from core.ontology.types import similar
        
        state_a = (0.0, 0.0, 0.0)
        state_b = (0.5, 0.5, 0.5)
        
        sim = similar(state_a, state_b)
        assert sim == 0.0


# =========================================================================
# GROUNDING TESTS
# =========================================================================

class TestGrounding:
    """grounding.py fonksiyonları testleri"""
    
    def test_world_to_state_vector(self):
        """WorldState → StateVector dönüşümü"""
        from core.ontology.grounding import world_to_state_vector
        
        world = MockWorldState(player_health=0.6, player_energy=0.8, danger_level=0.4)
        emotion = MockEmotionCore(valence=0.2)
        
        state = world_to_state_vector(world, emotion)
        
        assert state[0] == pytest.approx(0.7, rel=0.01)   # (0.6+0.8)/2
        assert state[1] == pytest.approx(0.4, rel=0.01)   # danger
        assert state[2] == pytest.approx(0.6, rel=0.01)   # (0.2+1)/2


# =========================================================================
# SELF_CORE INTEGRATION TESTS
# =========================================================================

class TestSelfCoreOntologyIntegration:
    """SelfCore ontology entegrasyonu testleri"""
    
    def test_self_core_has_ontology_methods(self):
        """SelfCore ontology API'leri mevcut olmalı"""
        from core.self.self_core import SelfCore
        
        # Mock systems
        core = SelfCore(
            memory_system=None,
            emotion_system=MockEmotionCore(valence=0.0),
            cognition_system=None,
            planning_system=None,
            metamind_system=None,
            ethmor_system=None,
        )
        
        assert hasattr(core, 'get_state_vector')
        assert hasattr(core, 'build_self_entity')
        assert callable(core.get_state_vector)
        assert callable(core.build_self_entity)
    
    def test_build_self_entity_returns_valid_entity(self):
        """build_self_entity geçerli SelfEntity döndürmeli"""
        from core.self.self_core import SelfCore
        from core.ontology.types import SelfEntity
        
        core = SelfCore(
            memory_system=None,
            emotion_system=MockEmotionCore(valence=0.0),
            cognition_system=None,
            planning_system=None,
            metamind_system=None,
            ethmor_system=None,
        )
        
        entity = core.build_self_entity()
        
        # Should return entity with neutral state
        assert entity is not None
        assert hasattr(entity, 'state_vector')
        assert len(entity.state_vector) == 3


# =========================================================================
# EDGE CASE TESTS
# =========================================================================

class TestEdgeCases:
    """Edge case testleri"""
    
    def test_state_vector_with_negative_values(self):
        """Negatif değerler 0'a clamp edilmeli"""
        from core.ontology.types import build_state_vector
        
        world = MockWorldState(player_health=-0.5, player_energy=-0.5, danger_level=-0.5)
        emotion = MockEmotionCore(valence=-2.0)  # Below -1
        
        state = build_state_vector(world, emotion)
        
        assert state[0] >= 0.0
        assert state[1] >= 0.0
        assert state[2] >= 0.0
    
    def test_goal_default_priority(self):
        """Goal default priority = 1.0"""
        from core.ontology.types import Goal
        
        goal = Goal(name="test", target_state=(1.0, 0.0, 1.0))
        assert goal.priority == 1.0
    
    def test_self_entity_empty_history(self):
        """SelfEntity boş history ile oluşturulabilmeli"""
        from core.ontology.types import SelfEntity
        
        entity = SelfEntity(state_vector=(0.5, 0.5, 0.5))
        assert entity.history == []
        assert entity.goals == []


# =========================================================================
# RUN TESTS
# =========================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
