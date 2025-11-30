"""Tests for multi-agent placeholder - Phase E."""
import pytest
import sys
sys.path.insert(0, '.')

from uem_predata.multi_agent import MultiAgentCoordinator, CoordinationMode


class TestMultiAgentCoordinator:
    """MultiAgentCoordinator tests."""
    
    def test_initial_state(self):
        coordinator = MultiAgentCoordinator()
        assert coordinator.agent_count == 0
        assert coordinator.coordination_mode == CoordinationMode.NONE
        assert coordinator.get_conflict_score() == 0.0
    
    def test_register_agent(self):
        coordinator = MultiAgentCoordinator()
        coordinator.register_agent("agent_1")
        coordinator.register_agent("agent_2", role="helper")
        
        assert coordinator.agent_count == 2
    
    def test_unregister_agent(self):
        coordinator = MultiAgentCoordinator()
        coordinator.register_agent("agent_1")
        
        result = coordinator.unregister_agent("agent_1")
        assert result is True
        assert coordinator.agent_count == 0
        
        result = coordinator.unregister_agent("nonexistent")
        assert result is False
    
    def test_coordination_mode(self):
        coordinator = MultiAgentCoordinator(mode=CoordinationMode.COOPERATIVE)
        assert coordinator.coordination_mode == CoordinationMode.COOPERATIVE
        
        coordinator.set_coordination_mode(CoordinationMode.COMPETITIVE)
        assert coordinator.coordination_mode == CoordinationMode.COMPETITIVE
    
    def test_record_conflict(self):
        coordinator = MultiAgentCoordinator()
        coordinator.register_agent("agent_1")
        coordinator.register_agent("agent_2")
        
        coordinator.record_conflict(
            agent_ids=["agent_1", "agent_2"],
            conflict_type="resource",
            severity=0.7
        )
        
        assert coordinator.get_conflict_score() == 0.7
    
    def test_conflict_score_average(self):
        coordinator = MultiAgentCoordinator()
        
        coordinator.record_conflict(["a", "b"], "type1", severity=0.4)
        coordinator.record_conflict(["a", "b"], "type2", severity=0.6)
        coordinator.record_conflict(["a", "b"], "type3", severity=0.8)
        
        score = coordinator.get_conflict_score()
        assert score == pytest.approx(0.6, rel=0.01)
    
    def test_clear_conflicts(self):
        coordinator = MultiAgentCoordinator()
        coordinator.record_conflict(["a", "b"], "test", 0.5)
        
        coordinator.clear_conflicts()
        assert coordinator.get_conflict_score() == 0.0
    
    def test_get_summary(self):
        coordinator = MultiAgentCoordinator(mode=CoordinationMode.HIERARCHICAL)
        coordinator.register_agent("leader", role="leader")
        coordinator.register_agent("follower", role="follower")
        
        summary = coordinator.get_summary()
        
        assert summary["ma_agent_count"] == 2
        assert summary["ma_coordination_mode"] == "hierarchical"
        assert summary["ma_conflict_score"] == 0.0
        assert "leader" in summary["agent_ids"]
    
    def test_reset(self):
        coordinator = MultiAgentCoordinator(mode=CoordinationMode.COOPERATIVE)
        coordinator.register_agent("agent_1")
        coordinator.record_conflict(["a"], "test", 0.5)
        
        coordinator.reset()
        
        assert coordinator.agent_count == 0
        assert coordinator.coordination_mode == CoordinationMode.NONE
        assert coordinator.get_conflict_score() == 0.0


class TestCoordinationMode:
    """CoordinationMode enum tests."""
    
    def test_all_modes_exist(self):
        modes = [
            CoordinationMode.NONE,
            CoordinationMode.INDEPENDENT,
            CoordinationMode.COOPERATIVE,
            CoordinationMode.COMPETITIVE,
            CoordinationMode.HIERARCHICAL,
        ]
        assert len(modes) == 5
    
    def test_mode_values(self):
        assert CoordinationMode.NONE.value == "none"
        assert CoordinationMode.COOPERATIVE.value == "cooperative"
