# tests/test_core_integration.py
"""
IntegratedUEMCore Integration Tests

Tests for the complete SELF + ETHMOR integration in cognitive cycle:
- SELF state tracking through cycle
- ETHMOR action filtering
- Event logging
- End-to-end scenarios
"""

import pytest
import asyncio
from typing import Dict, Any, List


# =========================================================================
# FIXTURES
# =========================================================================

@pytest.fixture
def sample_ethmor_constraints() -> Dict[str, Any]:
    """Sample ETHMOR constraints for testing"""
    return {
        'ethmor': {
            'thresholds': {'allow_max': 0.3, 'flag_max': 0.7},
            'constraints': [
                {
                    'id': 'no_self_destruction',
                    'type': 'HARD',
                    'scope': 'SELF',
                    'condition': 'RESOURCE_LEVEL_after < 0.1',
                    'severity': 1.0,
                    'description': 'Cannot destroy self',
                },
                {
                    'id': 'avoid_high_risk',
                    'type': 'SOFT',
                    'scope': 'SELF',
                    'condition': 'THREAT_LEVEL_after > 0.8 and benefit < 0.2',
                    'severity': 0.5,
                    'description': 'Avoid unnecessary risk',
                },
            ]
        }
    }


@pytest.fixture
async def uem_core():
    """Create and start UEM Core"""
    from core.integrated_uem_core import IntegratedUEMCore
    
    core = IntegratedUEMCore(config={
        'tick_interval': 0.01,
    })
    await core.start()
    
    # Load default constraints if ETHMOR available
    if core.ethmor_system:
        core._load_default_ethmor_constraints()
    
    yield core
    
    await core.stop()


@pytest.fixture
def world_state_safe():
    """Safe world state"""
    from core.integrated_uem_core import WorldState
    
    return WorldState(
        tick=1,
        danger_level=0.1,
        player_health=0.9,
        player_energy=0.8,
    )


@pytest.fixture
def world_state_dangerous():
    """Dangerous world state"""
    from core.integrated_uem_core import WorldState
    
    return WorldState(
        tick=1,
        danger_level=0.9,
        player_health=0.3,
        player_energy=0.2,
    )


# =========================================================================
# BASIC CORE TESTS
# =========================================================================

class TestCoreBasics:
    """Basic core functionality tests"""
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Core should start and stop cleanly"""
        from core.integrated_uem_core import IntegratedUEMCore
        
        core = IntegratedUEMCore()
        
        assert not core.started
        
        await core.start()
        assert core.started
        assert core.workspace_manager is not None
        
        await core.stop()
        assert not core.started
    
    @pytest.mark.asyncio
    async def test_self_system_initialized(self, uem_core):
        """SELF system should be initialized"""
        # May be None if ontology not available
        if uem_core.self_system is not None:
            assert hasattr(uem_core.self_system, 'get_state_vector')
            assert hasattr(uem_core.self_system, 'get_ethmor_context')
    
    @pytest.mark.asyncio
    async def test_ethmor_system_initialized(self, uem_core):
        """ETHMOR system should be initialized"""
        if uem_core.ethmor_system is not None:
            stats = uem_core.ethmor_system.get_stats()
            assert 'total_constraints' in stats


# =========================================================================
# COGNITIVE CYCLE TESTS
# =========================================================================

class TestCognitiveCycle:
    """Cognitive cycle tests"""
    
    @pytest.mark.asyncio
    async def test_basic_cycle(self, uem_core, world_state_safe):
        """Basic cognitive cycle should complete"""
        from core.integrated_uem_core import ActionResult
        
        result = await uem_core.cognitive_cycle(world_state_safe)
        
        assert isinstance(result, ActionResult)
        assert result.action_name in ['wait', 'explore', 'flee', 'approach', 'rest', 'attack']
    
    @pytest.mark.asyncio
    async def test_cycle_updates_self_state(self, uem_core, world_state_safe):
        """Cycle should update SELF state vector"""
        if uem_core.self_system is None:
            pytest.skip("SELF system not available")
        
        await uem_core.cognitive_cycle(world_state_safe)
        
        state = uem_core.self_system.get_state_vector()
        assert state is not None
        assert len(state) == 16
    
    @pytest.mark.asyncio
    async def test_cycle_logs_event(self, uem_core, world_state_safe):
        """Cycle should log event"""
        initial_log_size = len(uem_core.event_log)
        
        await uem_core.cognitive_cycle(world_state_safe)
        
        assert len(uem_core.event_log) == initial_log_size + 1
        
        last_event = uem_core.event_log[-1]
        assert 'tick' in last_event
        assert 'final_action' in last_event
        assert 'ethmor_decision' in last_event
    
    @pytest.mark.asyncio
    async def test_multiple_cycles(self, uem_core):
        """Multiple cycles should work"""
        from core.integrated_uem_core import WorldState
        
        states = [
            WorldState(tick=i, danger_level=0.1 * i, player_health=1.0 - 0.05 * i)
            for i in range(5)
        ]
        
        results = await uem_core.run_cycles(states)
        
        assert len(results) == 5
        assert uem_core.total_cycles == 5


# =========================================================================
# SELF INTEGRATION TESTS
# =========================================================================

class TestSelfIntegration:
    """SELF system integration tests"""
    
    @pytest.mark.asyncio
    async def test_self_state_changes_with_world(self, uem_core):
        """SELF state should change as world changes"""
        from core.integrated_uem_core import WorldState
        
        if uem_core.self_system is None:
            pytest.skip("SELF system not available")
        
        # Safe state
        safe = WorldState(tick=1, danger_level=0.1, player_health=0.9, player_energy=0.9)
        await uem_core.cognitive_cycle(safe)
        safe_state = uem_core.self_system.get_state_vector()
        
        # Dangerous state
        danger = WorldState(tick=2, danger_level=0.8, player_health=0.3, player_energy=0.3)
        await uem_core.cognitive_cycle(danger)
        danger_state = uem_core.self_system.get_state_vector()
        
        assert safe_state is not None
        assert danger_state is not None
        
        # State vectors should be different after world change
        # Note: Exact values depend on SelfCore implementation
        # At minimum, threat level should increase with danger
        assert danger_state[1] >= safe_state[1]  # Threat should not decrease
    
    @pytest.mark.asyncio
    async def test_self_delta_computed(self, uem_core):
        """State delta should be computed after second cycle"""
        from core.integrated_uem_core import WorldState
        
        if uem_core.self_system is None:
            pytest.skip("SELF system not available")
        
        # First cycle
        state1 = WorldState(tick=1, danger_level=0.2, player_health=0.9)
        await uem_core.cognitive_cycle(state1)
        
        # No delta yet (no previous)
        delta1 = uem_core.self_system.get_state_delta()
        assert delta1 is None
        
        # Second cycle
        state2 = WorldState(tick=2, danger_level=0.5, player_health=0.7)
        await uem_core.cognitive_cycle(state2)
        
        # Now we should have delta
        delta2 = uem_core.self_system.get_state_delta()
        assert delta2 is not None
    
    @pytest.mark.asyncio
    async def test_goal_integration(self, uem_core):
        """Goals should be added to core"""
        uem_core.set_goal({
            'name': 'test_goal',
            'priority': 0.8,
            'target_resource': 1.0,
            'target_threat': 0.0,
            'target_wellbeing': 1.0,
        })
        
        # Goal should be in active_goals list
        assert len(uem_core.active_goals) > 0
        assert any(g.get('name') == 'test_goal' for g in uem_core.active_goals)


# =========================================================================
# ETHMOR INTEGRATION TESTS
# =========================================================================

class TestEthmorIntegration:
    """ETHMOR system integration tests"""
    
    @pytest.mark.asyncio
    async def test_ethmor_allows_safe_action(self, uem_core, world_state_safe):
        """ETHMOR should allow safe actions"""
        result = await uem_core.cognitive_cycle(world_state_safe)
        
        # Safe state should not trigger blocks
        assert result.ethmor_decision in ['ALLOW', 'FLAG']
        assert not result.blocked
    
    @pytest.mark.asyncio
    async def test_ethmor_result_in_stats(self, uem_core, world_state_safe):
        """ETHMOR result should be in stats"""
        await uem_core.cognitive_cycle(world_state_safe)
        
        stats = uem_core.get_stats()
        
        if 'ethmor' in stats:
            assert 'total_constraints' in stats['ethmor']
    
    @pytest.mark.asyncio
    async def test_cycle_history_has_ethmor(self, uem_core, world_state_safe):
        """Cycle history should have ETHMOR info"""
        await uem_core.cognitive_cycle(world_state_safe)
        
        assert len(uem_core.cycle_history) > 0
        
        last_cycle = uem_core.cycle_history[-1]
        assert hasattr(last_cycle, 'ethmor_decision')
        assert hasattr(last_cycle, 'ethmor_violation_score')


# =========================================================================
# EVENT LOGGING TESTS
# =========================================================================

class TestEventLogging:
    """Event logging tests"""
    
    @pytest.mark.asyncio
    async def test_event_log_structure(self, uem_core, world_state_safe):
        """Event log entries should have correct structure"""
        await uem_core.cognitive_cycle(world_state_safe)
        
        event = uem_core.get_event_log(n=1)[0]
        
        required_fields = [
            'tick', 'timestamp', 'candidate_action', 'final_action',
            'ethmor_decision', 'ethmor_violation_score', 'outcome',
        ]
        
        for field in required_fields:
            assert field in event, f"Missing field: {field}"
    
    @pytest.mark.asyncio
    async def test_event_log_accumulates(self, uem_core):
        """Event log should accumulate"""
        from core.integrated_uem_core import WorldState
        
        for i in range(5):
            state = WorldState(tick=i, danger_level=0.2)
            await uem_core.cognitive_cycle(state)
        
        events = uem_core.get_event_log()
        assert len(events) == 5
    
    @pytest.mark.asyncio
    async def test_event_log_n_limit(self, uem_core):
        """get_event_log(n) should limit results"""
        from core.integrated_uem_core import WorldState
        
        for i in range(10):
            state = WorldState(tick=i)
            await uem_core.cognitive_cycle(state)
        
        last_3 = uem_core.get_event_log(n=3)
        assert len(last_3) == 3
        assert last_3[-1]['tick'] == 9  # Last tick


# =========================================================================
# SCENARIO TESTS
# =========================================================================

class TestScenarios:
    """End-to-end scenario tests"""
    
    @pytest.mark.asyncio
    async def test_scenario_safe_exploration(self, uem_core):
        """Safe exploration scenario"""
        from core.integrated_uem_core import WorldState
        
        # Safe environment, should explore
        state = WorldState(
            tick=1,
            danger_level=0.1,
            player_health=0.9,
            player_energy=0.9,
        )
        
        result = await uem_core.cognitive_cycle(state)
        
        # Should be allowed to explore
        assert not result.blocked
        assert result.action_name in ['explore', 'wait', 'approach']
    
    @pytest.mark.asyncio
    async def test_scenario_flee_from_danger(self, uem_core):
        """Flee from danger scenario"""
        from core.integrated_uem_core import WorldState
        
        # High danger, should flee
        state = WorldState(
            tick=1,
            danger_level=0.9,
            player_health=0.8,
            player_energy=0.8,
        )
        
        result = await uem_core.cognitive_cycle(state)
        
        # Should flee
        assert result.action_name == 'flee'
        assert not result.blocked
    
    @pytest.mark.asyncio
    async def test_scenario_rest_when_low_health(self, uem_core):
        """Rest when low health scenario"""
        from core.integrated_uem_core import WorldState
        
        # Low health, low danger
        state = WorldState(
            tick=1,
            danger_level=0.1,
            player_health=0.2,
            player_energy=0.5,
        )
        
        result = await uem_core.cognitive_cycle(state)
        
        # Should rest
        assert result.action_name == 'rest'
    
    @pytest.mark.asyncio
    async def test_scenario_emotional_response(self, uem_core):
        """Emotional response to danger"""
        from core.integrated_uem_core import WorldState
        
        initial_valence = uem_core.current_emotion['valence']
        initial_arousal = uem_core.current_emotion['arousal']
        
        # Dangerous state
        state = WorldState(
            tick=1,
            danger_level=0.9,
            player_health=0.5,
        )
        
        await uem_core.cognitive_cycle(state)
        
        # Emotional response to danger:
        # - Valence should decrease (negative emotion)
        # - OR arousal should increase (alertness)
        valence_decreased = uem_core.current_emotion['valence'] < initial_valence
        arousal_increased = uem_core.current_emotion['arousal'] > initial_arousal
        
        assert valence_decreased or arousal_increased, \
            f"Expected emotional response to danger. Valence: {initial_valence} -> {uem_core.current_emotion['valence']}, Arousal: {initial_arousal} -> {uem_core.current_emotion['arousal']}"
    
    @pytest.mark.asyncio
    async def test_scenario_progressive_danger(self, uem_core):
        """Progressive danger increase"""
        from core.integrated_uem_core import WorldState
        
        if uem_core.self_system is None:
            pytest.skip("SELF system not available")
        
        # Start safe, gradually increase danger
        for i in range(5):
            state = WorldState(
                tick=i,
                danger_level=0.1 + i * 0.2,  # 0.1 → 0.9
                player_health=0.9 - i * 0.1,  # 0.9 → 0.5
            )
            result = await uem_core.cognitive_cycle(state)
        
        # By end, should be in fear state
        assert uem_core.current_emotion['arousal'] > 0.5
        
        # Should have history
        history = uem_core.self_system.get_state_history()
        assert len(history) == 5


# =========================================================================
# STATS TESTS
# =========================================================================

class TestStats:
    """Statistics tests"""
    
    @pytest.mark.asyncio
    async def test_get_stats_structure(self, uem_core, world_state_safe):
        """Stats should have correct structure"""
        await uem_core.cognitive_cycle(world_state_safe)
        
        stats = uem_core.get_stats()
        
        assert 'total_cycles' in stats
        assert 'current_tick' in stats
        assert 'current_emotion' in stats
        assert 'event_log_size' in stats
        
        assert stats['total_cycles'] == 1
    
    @pytest.mark.asyncio
    async def test_stats_include_self(self, uem_core, world_state_safe):
        """Stats should include SELF info"""
        if uem_core.self_system is None:
            pytest.skip("SELF system not available")
        
        await uem_core.cognitive_cycle(world_state_safe)
        
        stats = uem_core.get_stats()
        
        assert 'self' in stats
        assert 'self_state_vector' in stats


# =========================================================================
# RUN TESTS
# =========================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
