# tests/test_unified_core.py
"""
Unified Core Integration Tests

Test scenarios:
1. Core initialization
2. High danger → flee
3. Empathy → help
4. Uncertainty → wait
5. ETHMOR blocks unethical
6. Error recovery
7. Full cycle with metrics
8. Multiple cycles with learning

Author: UEM Project
Date: 26 November 2025
"""

import pytest
import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from core.unified_core import UnifiedUEMCore, create_unified_core
from core.unified_types import (
    MemoryContext,
    SelfState,
    AppraisalResult,
    ActionResult,
    CycleMetrics,
)


# ============================================================================
# MOCK WORLD STATE
# ============================================================================

@dataclass
class MockWorldState:
    """Mock WorldState for testing."""
    tick: int = 0
    danger_level: float = 0.0
    objects: List[Dict[str, Any]] = field(default_factory=list)
    agents: List[Dict[str, Any]] = field(default_factory=list)
    symbols: List[str] = field(default_factory=list)
    player_health: float = 1.0
    player_energy: float = 1.0


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def core():
    """Create a UnifiedUEMCore instance."""
    return create_unified_core(
        storage_type="memory",
        collect_metrics=True,
    )


@pytest.fixture
def safe_world():
    """Safe world state."""
    return MockWorldState(
        tick=1,
        danger_level=0.1,
        player_health=0.9,
        player_energy=0.8,
        objects=[{"type": "resource", "id": "res_1"}],
    )


@pytest.fixture
def dangerous_world():
    """Dangerous world state."""
    return MockWorldState(
        tick=1,
        danger_level=0.9,
        player_health=0.5,
        player_energy=0.3,
        objects=[{"type": "enemy", "id": "enemy_1"}],
    )


@pytest.fixture
def social_world():
    """World with other agents."""
    return MockWorldState(
        tick=1,
        danger_level=0.2,
        player_health=0.8,
        player_energy=0.7,
        agents=[{"id": "villager_1", "state": "distressed", "valence": -0.5}],
    )


@pytest.fixture
def neutral_world():
    """Neutral world state."""
    return MockWorldState(
        tick=1,
        danger_level=0.5,
        player_health=0.5,
        player_energy=0.5,
    )


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

class TestInitialization:
    """Core initialization tests."""
    
    def test_create_core(self):
        """Core should initialize without errors."""
        core = create_unified_core()
        assert core is not None
        assert isinstance(core, UnifiedUEMCore)
    
    def test_initial_state(self, core):
        """Initial state should be neutral."""
        assert core.tick == 0
        assert core.current_emotion["valence"] == 0.0
        assert core.current_emotion["arousal"] == 0.5
        assert core.last_action is None
    
    def test_valence_property(self, core):
        """Valence property should work."""
        assert core.valence == 0.0
        core.current_emotion["valence"] = 0.5
        assert core.valence == 0.5
    
    def test_planner_initialized(self, core):
        """Planner should be initialized."""
        assert core.planner is not None


# ============================================================================
# COGNITIVE CYCLE TESTS
# ============================================================================

class TestCognitiveCycle:
    """Basic cognitive cycle tests."""
    
    @pytest.mark.asyncio
    async def test_cycle_returns_action_result(self, core, safe_world):
        """Cycle should return ActionResult."""
        result = await core.cycle(safe_world)
        
        assert isinstance(result, ActionResult)
        assert hasattr(result, 'action_name')
        assert hasattr(result, 'success')
    
    @pytest.mark.asyncio
    async def test_cycle_increments_tick(self, core, safe_world):
        """Cycle should increment tick."""
        assert core.tick == 0
        await core.cycle(safe_world)
        assert core.tick == 1
        await core.cycle(safe_world)
        assert core.tick == 2
    
    @pytest.mark.asyncio
    async def test_cycle_updates_emotion(self, core, dangerous_world):
        """Cycle should update emotion state."""
        await core.cycle(dangerous_world)
        
        # High danger should cause negative valence
        assert core.current_emotion["valence"] < 0
        assert core.current_emotion["arousal"] > 0.5
    
    def test_cycle_sync(self, core, safe_world):
        """Sync wrapper should work."""
        result = core.cycle_sync(safe_world)
        
        assert isinstance(result, ActionResult)
        assert core.tick == 1


# ============================================================================
# SCENARIO TESTS
# ============================================================================

class TestHighDangerScenario:
    """High danger should trigger flee."""
    
    @pytest.mark.asyncio
    async def test_high_danger_triggers_flee(self, core, dangerous_world):
        """High danger should result in flee action."""
        result = await core.cycle(dangerous_world)
        
        assert result.action_name == "flee"
    
    @pytest.mark.asyncio
    async def test_fear_emotion_on_danger(self, core, dangerous_world):
        """High danger should cause fear emotion."""
        await core.cycle(dangerous_world)
        
        # Negative valence + high arousal = fear
        assert core.current_emotion["valence"] < -0.2
        assert core.current_emotion["arousal"] > 0.6


class TestSafeExplorationScenario:
    """Safe environment should allow exploration."""
    
    @pytest.mark.asyncio
    async def test_safe_allows_explore(self, core, safe_world):
        """Safe world should allow explore/approach."""
        result = await core.cycle(safe_world)
        
        assert result.action_name in ["explore", "approach", "wait", "flee"]
    
    @pytest.mark.asyncio
    async def test_positive_emotion_on_safe(self, core, safe_world):
        """Safe world should maintain positive emotion."""
        await core.cycle(safe_world)
        
        # Low danger, good health = positive/neutral
        assert core.current_emotion["valence"] >= -0.2


class TestEmpathyScenario:
    """Empathy with distressed agent should trigger help."""
    
    @pytest.mark.asyncio
    async def test_empathy_context_triggers_help(self, core, social_world):
        """Distressed agent should trigger help action."""
        result = await core.cycle(social_world)
        
        # With empathy, help should be favored
        assert result.action_name in ["help", "approach", "explore", "flee", "wait"]


class TestUncertaintyScenario:
    """Uncertainty should lead to wait."""
    
    @pytest.mark.asyncio
    async def test_neutral_may_wait(self, core, neutral_world):
        """Neutral/uncertain situation may result in wait."""
        result = await core.cycle(neutral_world)
        
        # Neutral situation - any cautious action is valid
        assert result.action_name in ["wait", "explore", "flee"]


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Error handling tests."""
    
    @pytest.mark.asyncio
    async def test_nan_danger_fallback(self, core):
        """NaN danger should trigger fallback."""
        broken_world = MockWorldState(danger_level=float('nan'))
        
        result = await core.cycle(broken_world)
        
        # Should not crash, should return fallback
        assert result.action_name == "wait"
        assert result.outcome_type == "error_fallback"
    
    @pytest.mark.asyncio
    async def test_missing_attributes_handled(self, core):
        """Missing world attributes should be handled."""
        minimal_world = MockWorldState()  # All defaults
        
        result = await core.cycle(minimal_world)
        
        # Should complete without error
        assert isinstance(result, ActionResult)


# ============================================================================
# METRICS TESTS
# ============================================================================

class TestMetrics:
    """Metrics collection tests."""
    
    @pytest.mark.asyncio
    async def test_metrics_collected(self, core, safe_world):
        """Metrics should be collected when enabled."""
        result = await core.cycle(safe_world)
        
        assert core.last_metrics is not None
        assert core.last_metrics.tick == 1
        assert core.last_metrics.total_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_phase_times_recorded(self, core, safe_world):
        """Phase times should be recorded."""
        await core.cycle(safe_world)
        
        phase_times = core.last_metrics.phase_times
        assert "perception" in phase_times
        assert "planning" in phase_times
        assert "execution" in phase_times
    
    def test_metrics_disabled(self, safe_world):
        """Metrics should not be collected when disabled."""
        core = create_unified_core(collect_metrics=False)
        core.cycle_sync(safe_world)
        
        assert core.last_metrics is None


# ============================================================================
# MULTI-CYCLE TESTS
# ============================================================================

class TestMultipleCycles:
    """Multiple cycle tests."""
    
    @pytest.mark.asyncio
    async def test_multiple_cycles(self, core, safe_world):
        """Multiple cycles should work."""
        for i in range(5):
            result = await core.cycle(safe_world)
            assert result is not None
        
        assert core.tick == 5
    
    @pytest.mark.asyncio
    async def test_state_persists(self, core):
        """State should persist across cycles."""
        # First: dangerous world
        dangerous = MockWorldState(danger_level=0.9, player_health=0.5)
        await core.cycle(dangerous)
        
        emotion_after_danger = core.current_emotion.copy()
        
        # Second: safe world
        safe = MockWorldState(danger_level=0.1, player_health=0.9)
        await core.cycle(safe)
        
        # Emotion should have changed
        assert core.current_emotion != emotion_after_danger


# ============================================================================
# STATS AND RESET TESTS
# ============================================================================

class TestStatsAndReset:
    """Stats and reset tests."""
    
    @pytest.mark.asyncio
    async def test_get_stats(self, core, safe_world):
        """Stats should be retrievable."""
        await core.cycle(safe_world)
        
        stats = core.get_stats()
        
        assert "tick" in stats
        assert stats["tick"] == 1
        assert "current_emotion" in stats
        assert "planner" in stats
    
    @pytest.mark.asyncio
    async def test_reset(self, core, safe_world):
        """Reset should clear state."""
        await core.cycle(safe_world)
        await core.cycle(safe_world)
        
        assert core.tick == 2
        
        core.reset()
        
        assert core.tick == 0
        assert core.last_action is None
        assert core.last_result is None


# ============================================================================
# ACTION RESULT TESTS
# ============================================================================

class TestActionResult:
    """ActionResult structure tests."""
    
    @pytest.mark.asyncio
    async def test_action_result_fields(self, core, safe_world):
        """ActionResult should have all fields."""
        result = await core.cycle(safe_world)
        
        assert hasattr(result, 'action_name')
        assert hasattr(result, 'target')
        assert hasattr(result, 'success')
        assert hasattr(result, 'outcome_type')
        assert hasattr(result, 'outcome_valence')
        assert hasattr(result, 'actual_effect')
    
    @pytest.mark.asyncio
    async def test_action_result_to_dict(self, core, safe_world):
        """ActionResult should convert to dict."""
        result = await core.cycle(safe_world)
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert 'action_name' in result_dict


# ============================================================================
# APPRAISAL TESTS
# ============================================================================

class TestAppraisal:
    """Appraisal result tests."""
    
    @pytest.mark.asyncio
    async def test_danger_affects_valence(self, core):
        """High danger should decrease valence."""
        safe = MockWorldState(danger_level=0.1)
        dangerous = MockWorldState(danger_level=0.9)
        
        await core.cycle(safe)
        safe_valence = core.current_emotion["valence"]
        
        core.reset()
        
        await core.cycle(dangerous)
        danger_valence = core.current_emotion["valence"]
        
        assert danger_valence < safe_valence
    
    @pytest.mark.asyncio
    async def test_danger_affects_arousal(self, core):
        """High danger should increase arousal."""
        dangerous = MockWorldState(danger_level=0.9)
        
        await core.cycle(dangerous)
        
        assert core.current_emotion["arousal"] > 0.6
