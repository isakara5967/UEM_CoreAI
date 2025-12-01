# tests/test_self_extended.py
"""
SELF Module Extended Tests

Tests for the extended SelfCore with:
- StateVector tracking
- State delta computation
- Event history
- Goal management
- ETHMOR context building
"""

import pytest
import time
from dataclasses import dataclass
from typing import Optional


# =========================================================================
# MOCK CLASSES
# =========================================================================

@dataclass
class MockEmotionCore:
    """Mock EmotionCore with valence."""
    valence: float = 0.0


@dataclass
class MockWorldState:
    """Mock WorldState."""
    player_health: float = 1.0
    player_energy: float = 1.0
    danger_level: float = 0.0
    tick: int = 0


class MockMemorySystem:
    """Mock memory system."""
    pass


class MockPlanningSystem:
    """Mock planning system."""
    pass


# =========================================================================
# FIXTURES
# =========================================================================

@pytest.fixture
def emotion_system():
    return MockEmotionCore(valence=0.0)


@pytest.fixture
def self_core(emotion_system):
    """Create a SelfCore instance without starting submodules."""
    from core.self.self_core import SelfCore
    
    core = SelfCore(
        memory_system=None,
        emotion_system=emotion_system,
        cognition_system=None,
        planning_system=None,
        metamind_system=None,
        ethmor_system=None,
        config={'history_size': 50, 'goal_limit': 5},
    )
    return core


# =========================================================================
# STATE VECTOR TESTS
# =========================================================================

class TestStateVectorTracking:
    """State vector computation and tracking tests."""
    
    def test_initial_state_is_none(self, self_core):
        """Initial state vector should be None."""
        assert self_core.get_state_vector() is None
        assert self_core.get_previous_state_vector() is None
    
    def test_update_computes_state_vector(self, self_core):
        """Update with world snapshot should compute state vector."""
        world = {
            'player_health': 0.8,
            'player_energy': 0.6,
            'danger_level': 0.3,
        }
        
        self_core.update(dt=0.1, world_snapshot=world)
        
        state = self_core.get_state_vector()
        assert state is not None
        assert len(state) == 16
        
        # RESOURCE_LEVEL = (0.8 + 0.6) / 2 = 0.7
        assert state[0] == pytest.approx(0.7, rel=0.01)
        
        # THREAT_LEVEL = 0.3
        assert state[1] == pytest.approx(0.3, rel=0.01)
        
        # WELLBEING = (0.0 + 1) / 2 = 0.5 (valence=0)
        assert state[2] == pytest.approx(0.5, rel=0.01)
    
    def test_state_history_accumulates(self, self_core):
        """State history should accumulate over updates."""
        for i in range(5):
            world = {
                'player_health': 1.0 - i * 0.1,
                'player_energy': 1.0,
                'danger_level': i * 0.1,
            }
            self_core.update(dt=0.1, world_snapshot=world)
        
        history = self_core.get_state_history()
        assert len(history) == 5
    
    def test_state_history_limit(self, self_core):
        """State history should respect size limit."""
        # Config has history_size=50
        for i in range(60):
            world = {'player_health': 1.0, 'player_energy': 1.0, 'danger_level': 0.0}
            self_core.update(dt=0.1, world_snapshot=world)
        
        history = self_core.get_state_history()
        assert len(history) == 50


# =========================================================================
# STATE DELTA TESTS
# =========================================================================

class TestStateDelta:
    """State delta computation tests."""
    
    def test_no_delta_on_first_update(self, self_core):
        """First update should have no delta (no previous state)."""
        world = {'player_health': 1.0, 'player_energy': 1.0, 'danger_level': 0.0}
        self_core.update(dt=0.1, world_snapshot=world)
        
        delta = self_core.get_state_delta()
        assert delta is None  # No previous state
    
    def test_delta_computed_after_second_update(self, self_core):
        """Delta should be computed after second update."""
        # First update
        world1 = {'player_health': 1.0, 'player_energy': 1.0, 'danger_level': 0.0}
        self_core.update(dt=0.1, world_snapshot=world1)
        
        # Second update with changes
        world2 = {'player_health': 0.8, 'player_energy': 0.6, 'danger_level': 0.5}
        self_core.update(dt=0.1, world_snapshot=world2)
        
        delta = self_core.get_state_delta()
        assert delta is not None
        
        # RESOURCE: (1+1)/2=1.0 → (0.8+0.6)/2=0.7, delta=-0.3
        assert delta[0] == pytest.approx(-0.3, rel=0.01)
        
        # THREAT: 0.0 → 0.5, delta=+0.5
        assert delta[1] == pytest.approx(0.5, rel=0.01)
    
    def test_negative_delta_indicates_loss(self, self_core):
        """Negative resource delta indicates resource loss."""
        world1 = {'player_health': 1.0, 'player_energy': 1.0, 'danger_level': 0.0}
        self_core.update(dt=0.1, world_snapshot=world1)
        
        # Lose health
        world2 = {'player_health': 0.5, 'player_energy': 0.5, 'danger_level': 0.0}
        self_core.update(dt=0.1, world_snapshot=world2)
        
        delta = self_core.get_state_delta()
        assert delta[0] < 0  # Resource loss


# =========================================================================
# EVENT HISTORY TESTS
# =========================================================================

class TestEventHistory:
    """Event recording and history tests."""
    
    def test_record_event(self, self_core):
        """Should be able to record events."""
        from core.ontology.types import Event
        
        event = Event(
            source="ENVIRONMENT",
            target="SELF",
            effect=(-0.1, 0.2, -0.05),
            timestamp=time.time(),
        )
        
        self_core.record_event(event)
        
        history = self_core.get_event_history()
        assert len(history) == 1
        assert history[0].source == "ENVIRONMENT"
    
    def test_create_and_record_event(self, self_core):
        """Should create event from current state change."""
        # Setup state
        world1 = {'player_health': 1.0, 'player_energy': 1.0, 'danger_level': 0.0}
        self_core.update(dt=0.1, world_snapshot=world1)
        
        world2 = {'player_health': 0.8, 'player_energy': 0.8, 'danger_level': 0.3}
        self_core.update(dt=0.1, world_snapshot=world2)
        
        # Create event
        event = self_core.create_and_record_event(
            source="SELF",
            target="SELF",
        )
        
        assert event is not None
        assert event.source == "SELF"
        assert event.effect is not None
    
    def test_event_history_limit(self, self_core):
        """Event history should respect size limit."""
        from core.ontology.types import Event
        
        for i in range(60):
            event = Event(
                source="TEST",
                target="SELF",
                effect=(0.0, 0.0, 0.0),
                timestamp=float(i),
            )
            self_core.record_event(event)
        
        history = self_core.get_event_history()
        assert len(history) == 50  # Config limit


# =========================================================================
# GOAL MANAGEMENT TESTS
# =========================================================================

class TestGoalManagement:
    """Goal management tests."""
    
    def test_default_survival_goal(self, self_core):
        """Should have default survival goal after start."""
        # Note: start() initializes goals, but we're not calling it
        # because it tries to import submodules
        self_core._init_default_goals()
        
        goals = self_core.get_goals()
        assert len(goals) == 1
        assert goals[0].name == "survive"
    
    def test_add_goal(self, self_core):
        """Should be able to add goals."""
        from core.ontology.types import Goal
        
        goal = Goal(
            name="explore",
            target_state=(0.8, 0.2, 0.8),
            priority=0.7,
        )
        
        result = self_core.add_goal(goal)
        assert result is True
        
        goals = self_core.get_goals()
        assert any(g.name == "explore" for g in goals)
    
    def test_goals_sorted_by_priority(self, self_core):
        """Goals should be sorted by priority."""
        from core.ontology.types import Goal
        
        self_core.add_goal(Goal("low", (0.5, 0.5, 0.5), priority=0.3))
        self_core.add_goal(Goal("high", (0.5, 0.5, 0.5), priority=0.9))
        self_core.add_goal(Goal("mid", (0.5, 0.5, 0.5), priority=0.5))
        
        goals = self_core.get_goals()
        assert goals[0].name == "high"
        assert goals[1].name == "mid"
        assert goals[2].name == "low"
    
    def test_primary_goal(self, self_core):
        """Primary goal should be highest priority."""
        from core.ontology.types import Goal
        
        self_core.add_goal(Goal("low", (0.5, 0.5, 0.5), priority=0.3))
        self_core.add_goal(Goal("high", (0.5, 0.5, 0.5), priority=0.9))
        
        primary = self_core.get_primary_goal()
        assert primary.name == "high"
    
    def test_remove_goal(self, self_core):
        """Should be able to remove goals."""
        from core.ontology.types import Goal
        
        self_core.add_goal(Goal("temp", (0.5, 0.5, 0.5), priority=0.5))
        
        result = self_core.remove_goal("temp")
        assert result is True
        
        goals = self_core.get_goals()
        assert not any(g.name == "temp" for g in goals)
    
    def test_goal_limit_enforced(self, self_core):
        """Goal limit should be enforced."""
        from core.ontology.types import Goal
        
        # Config has goal_limit=5
        for i in range(10):
            self_core.add_goal(Goal(f"goal_{i}", (0.5, 0.5, 0.5), priority=0.1 * i))
        
        goals = self_core.get_goals()
        assert len(goals) == 5


# =========================================================================
# SELF ENTITY TESTS
# =========================================================================

class TestSelfEntity:
    """SelfEntity building tests."""
    
    def test_build_self_entity_without_state(self, self_core):
        """Should build entity with default state if not computed."""
        entity = self_core.build_self_entity()
        
        assert entity is not None
        assert entity.state_vector == (0.5, 0.0, 0.5)  # Neutral default
    
    def test_build_self_entity_with_state(self, self_core):
        """Should build entity with current state."""
        world = {'player_health': 0.8, 'player_energy': 0.6, 'danger_level': 0.3}
        self_core.update(dt=0.1, world_snapshot=world)
        
        entity = self_core.build_self_entity()
        
        assert entity is not None
        assert entity.state_vector[0] == pytest.approx(0.7, rel=0.01)
    
    def test_build_self_entity_includes_goals(self, self_core):
        """Entity should include goals."""
        from core.ontology.types import Goal
        
        self_core.add_goal(Goal("test", (0.5, 0.5, 0.5), priority=0.5))
        
        entity = self_core.build_self_entity()
        
        assert len(entity.goals) == 1
        assert entity.goals[0].name == "test"


# =========================================================================
# ETHMOR CONTEXT TESTS
# =========================================================================

class TestEthmorContext:
    """ETHMOR context building tests."""
    
    def test_ethmor_context_structure(self, self_core):
        """Context should have required fields."""
        world = {'player_health': 0.8, 'player_energy': 0.6, 'danger_level': 0.3}
        self_core.update(dt=0.1, world_snapshot=world)
        
        context = self_core.get_ethmor_context()
        
        assert 'self_entity' in context
        assert 'state_vector' in context
        assert 'RESOURCE_LEVEL' in context
        assert 'THREAT_LEVEL' in context
        assert 'WELLBEING' in context
    
    def test_ethmor_context_before_after(self, self_core):
        """Context should have before/after values after two updates."""
        world1 = {'player_health': 1.0, 'player_energy': 1.0, 'danger_level': 0.0}
        self_core.update(dt=0.1, world_snapshot=world1)
        
        world2 = {'player_health': 0.8, 'player_energy': 0.6, 'danger_level': 0.3}
        self_core.update(dt=0.1, world_snapshot=world2)
        
        context = self_core.get_ethmor_context()
        
        assert 'RESOURCE_LEVEL_before' in context
        assert 'RESOURCE_LEVEL_delta' in context
        assert context['RESOURCE_LEVEL_before'] == pytest.approx(1.0, rel=0.01)
        assert context['RESOURCE_LEVEL_delta'] == pytest.approx(-0.3, rel=0.01)


# =========================================================================
# PREDICTION TESTS
# =========================================================================

class TestStatePrediction:
    """State prediction tests."""
    
    def test_predict_state_after_action(self, self_core):
        """Should predict state after action effects."""
        world = {'player_health': 0.8, 'player_energy': 0.8, 'danger_level': 0.3}
        self_core.update(dt=0.1, world_snapshot=world)
        
        predicted = self_core.predict_state_after_action(
            action_name="flee",
            predicted_effects={
                'health_delta': -0.1,
                'energy_delta': -0.2,
                'danger_delta': -0.3,
            }
        )
        
        assert predicted is not None
        # Original resource: (0.8+0.8)/2 = 0.8
        # After: 0.8 + (-0.1 + -0.2)/2 = 0.8 - 0.15 = 0.65
        assert predicted[0] == pytest.approx(0.65, rel=0.05)
        
        # Threat: 0.3 - 0.3 = 0.0
        assert predicted[1] == pytest.approx(0.0, rel=0.01)


# =========================================================================
# INTEGRATION TESTS
# =========================================================================

class TestSelfCoreIntegration:
    """Integration tests for SelfCore."""
    
    def test_full_update_cycle(self, self_core):
        """Full update cycle should work."""
        from core.ontology.types import Goal
        
        # Add goal
        self_core.add_goal(Goal("survive", (1.0, 0.0, 1.0), priority=1.0))
        
        # Multiple updates
        states = [
            {'player_health': 1.0, 'player_energy': 1.0, 'danger_level': 0.0},
            {'player_health': 0.9, 'player_energy': 0.8, 'danger_level': 0.2},
            {'player_health': 0.7, 'player_energy': 0.6, 'danger_level': 0.5},
        ]
        
        for world in states:
            self_core.update(dt=0.1, world_snapshot=world)
        
        # Check state
        stats = self_core.get_stats()
        assert stats['tick_count'] == 3
        assert stats['state_history_size'] == 3
        
        # Check entity
        entity = self_core.build_self_entity()
        assert entity is not None
        assert len(entity.goals) >= 1
    
    def test_get_self_state_includes_ontology(self, self_core):
        """get_self_state should include ontology section."""
        world = {'player_health': 0.8, 'player_energy': 0.6, 'danger_level': 0.3}
        self_core.update(dt=0.1, world_snapshot=world)
        
        state = self_core.get_self_state()
        
        assert 'ontology' in state
        assert state['ontology']['state_vector'] is not None
        assert state['ontology']['tick'] == 1


# =========================================================================
# RUN TESTS
# =========================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
