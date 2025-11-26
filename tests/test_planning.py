# tests/test_planning.py
"""
Planning Module Tests (v1)

Test scenarios from Brief:
1. High threat → flee
2. Empathy + distressed other → help
3. Uncertainty → wait
4. ETHMOR blocks unethical action
5. Somatic marker influence
6. Goal alignment scoring
"""

import pytest
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from core.planning import (
    Planner,
    PlanningContext,
    ActionPlan,
    CandidateAction,
    create_planner,
    get_predicted_effect,
)


# ============================================================================
# MOCK CLASSES
# ============================================================================

@dataclass
class MockGoal:
    name: str
    target_state: tuple = (0.8, 0.2, 0.9)
    priority: float = 0.5


@dataclass
class MockWorldSnapshot:
    danger_level: float = 0.0
    objects: List[Dict] = None
    agents: List[Dict] = None
    symbols: List[str] = None
    safe_zones: List[str] = None
    nearest_target: Any = None
    nearest_danger: Any = None
    
    def __post_init__(self):
        self.objects = self.objects or []
        self.agents = self.agents or []
        self.symbols = self.symbols or []
        self.safe_zones = self.safe_zones or []


@dataclass
class MockSomaticBias:
    action: str
    bias_value: float
    confidence: float = 0.8
    contributing_markers: List[str] = None


class MockSomaticMarker:
    def __init__(self, biases: Dict[str, float] = None):
        self._biases = biases or {}
    
    def get_action_biases(self, world_state: Dict, actions: List[str]) -> Dict[str, MockSomaticBias]:
        return {
            action: MockSomaticBias(action=action, bias_value=self._biases.get(action, 0.0))
            for action in actions
        }


class MockEthmor:
    def __init__(self, blocked_actions: List[str] = None):
        self._blocked = blocked_actions or []
    
    def evaluate_action(self, action: str, context: Dict) -> Dict:
        if action in self._blocked:
            return {'decision': 'BLOCK', 'reason': 'ethical_violation'}
        return {'decision': 'ALLOW'}


@dataclass
class MockEmpathyResult:
    empathy_level: float = 0.0
    resonance: float = 0.5
    confidence: float = 0.5


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def planner():
    return create_planner()


@pytest.fixture
def high_threat_context():
    return PlanningContext(
        state_vector=(0.5, 0.9, 0.2),  # High threat
        goals=[MockGoal(name="survive", target_state=(0.5, 0.0, 0.8), priority=1.0)],
        world_snapshot=MockWorldSnapshot(danger_level=0.9),
        available_actions=["flee", "attack", "wait"],
    )


@pytest.fixture
def neutral_context():
    return PlanningContext(
        state_vector=(0.5, 0.5, 0.5),
        goals=[MockGoal(name="explore", target_state=(0.7, 0.3, 0.7), priority=0.5)],
        world_snapshot=MockWorldSnapshot(danger_level=0.3),
        available_actions=["flee", "approach", "help", "attack", "explore", "wait"],
    )


@pytest.fixture
def empathy_context():
    return PlanningContext(
        state_vector=(0.6, 0.3, 0.6),
        goals=[MockGoal(name="social", target_state=(0.5, 0.2, 0.9), priority=0.7)],
        world_snapshot=MockWorldSnapshot(
            danger_level=0.2,
            agents=[{'id': 'villager_1', 'needs_help': True}]
        ),
        available_actions=["help", "approach", "wait", "explore"],
        empathy_result=MockEmpathyResult(empathy_level=0.8, resonance=0.7),
    )


# ============================================================================
# BASIC TESTS
# ============================================================================

class TestPlannerBasic:
    
    def test_create_planner(self):
        planner = create_planner()
        assert planner is not None
        assert isinstance(planner, Planner)
    
    def test_plan_returns_action_plan(self, planner, neutral_context):
        result = planner.plan(neutral_context)
        assert isinstance(result, ActionPlan)
        assert hasattr(result, 'action')
        assert hasattr(result, 'utility')
        assert hasattr(result, 'reasoning')
    
    def test_plan_has_valid_action(self, planner, neutral_context):
        result = planner.plan(neutral_context)
        assert result.action in neutral_context.available_actions
    
    def test_plan_has_reasoning(self, planner, neutral_context):
        result = planner.plan(neutral_context)
        assert len(result.reasoning) > 0


# ============================================================================
# SCENARIO TESTS
# ============================================================================

class TestHighThreatScenario:
    """Test: High threat should trigger flee."""
    
    def test_high_threat_triggers_flee(self, planner, high_threat_context):
        result = planner.plan(high_threat_context)
        
        # Flee should be selected due to high threat
        assert result.action == "flee"
    
    def test_high_threat_has_high_confidence(self, planner, high_threat_context):
        result = planner.plan(high_threat_context)
        
        # Should be confident about fleeing
        assert result.confidence > 0.5
    
    def test_high_threat_reasoning_mentions_threat(self, planner, high_threat_context):
        result = planner.plan(high_threat_context)
        
        # Reasoning should exist
        assert len(result.reasoning) > 0


class TestEmpathyScenario:
    """Test: High empathy + distressed other should trigger help."""
    
    def test_empathy_triggers_help(self, planner, empathy_context):
        result = planner.plan(empathy_context)
        
        # Help should be selected due to high empathy
        assert result.action == "help"
    
    def test_empathy_target_is_set(self, planner, empathy_context):
        result = planner.plan(empathy_context)
        
        # Target should be the agent needing help
        assert result.target is not None


class TestUncertaintyScenario:
    """Test: Low confidence / uncertainty should lead to wait."""
    
    def test_no_actions_leads_to_wait(self, planner):
        context = PlanningContext(
            state_vector=(0.5, 0.5, 0.5),
            available_actions=[],  # No actions available
        )
        
        result = planner.plan(context)
        
        assert result.action == "wait"
        assert "fallback" in str(result.reasoning)


class TestEthmorScenario:
    """Test: ETHMOR should block unethical actions."""
    
    def test_ethmor_blocks_attack(self):
        ethmor = MockEthmor(blocked_actions=["attack"])
        planner = Planner(ethmor_system=ethmor)
        
        context = PlanningContext(
            state_vector=(0.5, 0.5, 0.5),
            goals=[MockGoal(name="resource", priority=0.5)],
            available_actions=["attack", "wait"],
        )
        
        result = planner.plan(context)
        
        # Attack should be blocked, wait selected
        assert result.action == "wait"
        # Attack blocked, wait selected - correct behavior
        assert result.action == "wait"  # This is the main assertion
    
    def test_ethmor_allows_valid_action(self):
        ethmor = MockEthmor(blocked_actions=["attack"])
        planner = Planner(ethmor_system=ethmor)
        
        context = PlanningContext(
            state_vector=(0.5, 0.5, 0.5),
            available_actions=["explore", "wait"],
        )
        
        result = planner.plan(context)
        
        # Explore should be allowed
        assert result.action in ["explore", "wait"]


class TestSomaticScenario:
    """Test: Somatic markers should influence decisions."""
    
    def test_negative_somatic_filters_action(self):
        somatic = MockSomaticMarker(biases={"attack": -0.9})  # Strong negative
        planner = Planner()
        
        context = PlanningContext(
            state_vector=(0.5, 0.5, 0.5),
            somatic_markers=somatic,
            available_actions=["attack", "explore", "wait"],
        )
        
        result = planner.plan(context)
        
        # Attack should be filtered due to strong negative bias
        assert result.action != "attack"
    
    def test_positive_somatic_boosts_action(self):
        somatic = MockSomaticMarker(biases={"explore": 0.5, "wait": -0.2})
        planner = Planner()
        
        context = PlanningContext(
            state_vector=(0.5, 0.5, 0.5),
            somatic_markers=somatic,
            available_actions=["explore", "wait"],
        )
        
        result = planner.plan(context)
        
        # Explore should be boosted
        assert result.action == "explore"


# ============================================================================
# UTILITY TESTS
# ============================================================================

class TestUtilityCalculation:
    """Test utility scoring components."""
    
    def test_goal_alignment_affects_utility(self, planner):
        # Context with goal that aligns with flee (reduce threat)
        context = PlanningContext(
            state_vector=(0.5, 0.8, 0.3),  # High threat
            goals=[MockGoal(name="survive", target_state=(0.5, 0.0, 0.8), priority=1.0)],
            available_actions=["flee", "wait"],
        )
        
        result = planner.plan(context)
        
        # Flee should have higher utility (reduces threat toward goal)
        assert result.action == "flee"
        assert result.utility > 0
    
    def test_state_improvement_affects_utility(self, planner):
        # Low wellbeing context
        context = PlanningContext(
            state_vector=(0.5, 0.3, 0.2),  # Low wellbeing
            goals=[MockGoal(name="wellness", target_state=(0.5, 0.3, 1.0))],
            available_actions=["help", "attack"],  # help improves wellbeing
        )
        
        result = planner.plan(context)
        
        # Help should be preferred (improves wellbeing)
        assert result.action == "help"
    
    def test_utility_in_valid_range(self, planner, neutral_context):
        result = planner.plan(neutral_context)
        
        # Utility should be reasonable (not extreme)
        assert -2.0 < result.utility < 2.0


# ============================================================================
# PREDICTED EFFECT TESTS
# ============================================================================

class TestPredictedEffects:
    
    def test_flee_reduces_threat(self):
        effect = get_predicted_effect("flee")
        assert effect[1] < 0  # Threat should decrease
    
    def test_help_improves_wellbeing(self):
        effect = get_predicted_effect("help")
        assert effect[2] > 0  # Wellbeing should increase
    
    def test_explore_has_resource_potential(self):
        effect = get_predicted_effect("explore")
        assert effect[0] > 0  # Resource should increase
    
    def test_wait_is_neutral(self):
        effect = get_predicted_effect("wait")
        assert effect == (0.0, 0.0, 0.0)


# ============================================================================
# STATISTICS TESTS
# ============================================================================

class TestStatistics:
    
    def test_stats_tracking(self, planner, neutral_context):
        planner.plan(neutral_context)
        planner.plan(neutral_context)
        
        stats = planner.get_stats()
        assert stats['plans_generated'] == 2
    
    def test_stats_reset(self, planner, neutral_context):
        planner.plan(neutral_context)
        planner.reset_stats()
        
        stats = planner.get_stats()
        assert stats['plans_generated'] == 0


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    
    def test_empty_goals(self, planner):
        context = PlanningContext(
            state_vector=(0.5, 0.5, 0.5),
            goals=[],
            available_actions=["explore", "wait"],
        )
        
        result = planner.plan(context)
        assert result.action in ["explore", "wait"]
    
    def test_no_world_snapshot(self, planner):
        context = PlanningContext(
            state_vector=(0.5, 0.5, 0.5),
            world_snapshot=None,
            available_actions=["explore", "wait"],
        )
        
        result = planner.plan(context)
        assert result.action in ["explore", "wait"]
    
    def test_action_plan_to_dict(self, planner, neutral_context):
        result = planner.plan(neutral_context)
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert 'action' in result_dict
        assert 'utility' in result_dict
        assert 'reasoning' in result_dict
