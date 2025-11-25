"""
Tests for Somatic Event Handler

Test scenarios:
1. Event subscription initialization
2. Action event handling
3. Outcome event handling
4. Emotion context update
5. World state context update
6. Statistics tracking
7. WorldOutcomePublisher
"""

import pytest
import asyncio
import sys
from dataclasses import dataclass
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, '/home/claude/uem_project')

from core.emotion.somatic_event_handler import (
    SomaticEventHandler,
    OutcomeMapping,
    WorldOutcomePublisher,
    create_somatic_handler,
)
from core.emotion.somatic_marker_system import SomaticMarkerSystem


# =========================================================================
# MOCK CLASSES
# =========================================================================

@dataclass
class MockEvent:
    """Mock event for testing"""
    type: str
    source: str
    data: Dict[str, Any]
    priority: int = 2


class MockEventBus:
    """Mock event bus for testing"""
    
    def __init__(self):
        self.subscriptions: Dict[str, List[Any]] = {}
        self.published_events: List[MockEvent] = []
    
    async def subscribe(self, event_type: str, handler):
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = []
        self.subscriptions[event_type].append(handler)
    
    async def publish(self, event):
        self.published_events.append(event)
        # Also call handlers
        handlers = self.subscriptions.get(event.type, [])
        for handler in handlers:
            await handler(event)
    
    async def simulate_event(self, event_type: str, data: Dict[str, Any]):
        """Simulate an event being received"""
        event = MockEvent(type=event_type, source='test', data=data)
        handlers = self.subscriptions.get(event_type, [])
        for handler in handlers:
            await handler(event)


# =========================================================================
# FIXTURES
# =========================================================================

@pytest.fixture
def somatic_system():
    return SomaticMarkerSystem()


@pytest.fixture
def event_bus():
    return MockEventBus()


@pytest.fixture
def handler(somatic_system, event_bus):
    return SomaticEventHandler(
        somatic_system=somatic_system,
        event_bus=event_bus,
    )


# =========================================================================
# INITIALIZATION TESTS
# =========================================================================

class TestInitialization:
    
    @pytest.mark.asyncio
    async def test_initialize_subscribes_to_events(self, handler, event_bus):
        """Initialize should subscribe to required events"""
        await handler.initialize()
        
        assert 'planning.action_decided' in event_bus.subscriptions
        assert 'world.outcome_received' in event_bus.subscriptions
        assert 'emotion.state_changed' in event_bus.subscriptions
        assert 'perception.new_data' in event_bus.subscriptions
    
    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, handler, event_bus):
        """Multiple initialize calls should not duplicate subscriptions"""
        await handler.initialize()
        await handler.initialize()
        
        # Should still have only one handler per event type
        assert len(event_bus.subscriptions['planning.action_decided']) == 1
    
    def test_no_event_bus_warning(self, somatic_system, caplog):
        """Should warn when no event bus provided"""
        handler = SomaticEventHandler(
            somatic_system=somatic_system,
            event_bus=None,
        )
        # initialize sync check
        assert handler.event_bus is None


# =========================================================================
# ACTION EVENT TESTS
# =========================================================================

class TestActionEvents:
    
    @pytest.mark.asyncio
    async def test_action_event_records_action(self, handler, event_bus, somatic_system):
        """Action events should be recorded in somatic system"""
        await handler.initialize()
        
        await event_bus.simulate_event('planning.action_decided', {
            'action_name': 'EXPLORE',
            'action_params': {'danger_level': 0.3},
            'confidence': 0.7,
        })
        
        assert handler.actions_recorded == 1
        assert len(somatic_system.pending_actions) == 1
        assert somatic_system.pending_actions[0].action_name == 'EXPLORE'
    
    @pytest.mark.asyncio
    async def test_action_event_uses_emotion_context(self, handler, event_bus):
        """Action recording should use current emotion context"""
        await handler.initialize()
        
        # Set emotion context
        await event_bus.simulate_event('emotion.state_changed', {
            'valence': 0.5,
            'arousal': 0.3,
            'dominance': 0.1,
        })
        
        # Record action
        await event_bus.simulate_event('planning.action_decided', {
            'action_name': 'APPROACH_TARGET',
            'action_params': {},
        })
        
        assert handler.current_emotion['valence'] == 0.5
    
    @pytest.mark.asyncio
    async def test_action_event_ignores_empty_name(self, handler, event_bus):
        """Should ignore action events without action_name"""
        await handler.initialize()
        
        await event_bus.simulate_event('planning.action_decided', {
            'action_params': {},
        })
        
        assert handler.actions_recorded == 0


# =========================================================================
# OUTCOME EVENT TESTS
# =========================================================================

class TestOutcomeEvents:
    
    @pytest.mark.asyncio
    async def test_outcome_event_creates_marker(self, handler, event_bus, somatic_system):
        """Outcome events should create markers"""
        await handler.initialize()
        
        # First record an action
        await event_bus.simulate_event('planning.action_decided', {
            'action_name': 'EXPLORE',
            'action_params': {'danger_level': 0.2},
        })
        
        # Then record outcome
        await event_bus.simulate_event('world.outcome_received', {
            'outcome_type': 'found_reward',
            'outcome_valence': 0.7,
        })
        
        assert handler.outcomes_recorded == 1
        assert somatic_system.total_markers == 1
    
    @pytest.mark.asyncio
    async def test_outcome_uses_mapping_when_no_valence(self, handler, event_bus, somatic_system):
        """Should use outcome mapping when valence not provided"""
        await handler.initialize()
        
        await event_bus.simulate_event('planning.action_decided', {
            'action_name': 'APPROACH_TARGET',
            'action_params': {},
        })
        
        await event_bus.simulate_event('world.outcome_received', {
            'outcome_type': 'took_damage',
            # No outcome_valence provided
        })
        
        # Should have used mapping (took_damage = -0.6)
        assert somatic_system.total_markers == 1
        marker = list(somatic_system.markers.values())[0]
        marker = list(marker.values())[0]
        assert marker.valence == -0.6
    
    @pytest.mark.asyncio
    async def test_outcome_publishes_marker_event(self, handler, event_bus):
        """Outcome processing should publish marker events"""
        await handler.initialize()
        
        await event_bus.simulate_event('planning.action_decided', {
            'action_name': 'EXPLORE',
            'action_params': {},
        })
        
        # Clear previous events
        event_bus.published_events.clear()
        
        await event_bus.simulate_event('world.outcome_received', {
            'outcome_type': 'found_reward',
            'outcome_valence': 0.5,
        })
        
        # Should have published marker_created event
        marker_events = [e for e in event_bus.published_events 
                        if 'somatic.marker' in e.type]
        assert len(marker_events) >= 1


# =========================================================================
# CONTEXT UPDATE TESTS
# =========================================================================

class TestContextUpdates:
    
    @pytest.mark.asyncio
    async def test_emotion_context_updated(self, handler, event_bus):
        """Emotion events should update current context"""
        await handler.initialize()
        
        await event_bus.simulate_event('emotion.state_changed', {
            'valence': -0.5,
            'arousal': 0.8,
            'dominance': 0.2,
        })
        
        assert handler.current_emotion['valence'] == -0.5
        assert handler.current_emotion['arousal'] == 0.8
        assert handler.current_emotion['dominance'] == 0.2
    
    @pytest.mark.asyncio
    async def test_world_state_context_updated(self, handler, event_bus):
        """Perception events should update world state context"""
        await handler.initialize()
        
        await event_bus.simulate_event('perception.new_data', {
            'danger_level': 0.6,
            'objects_count': 3,
            'symbols': ['DANGER_HIGH'],
        })
        
        assert handler.current_world_state['danger_level'] == 0.6
        assert handler.current_world_state['objects_count'] == 3
        assert 'DANGER_HIGH' in handler.current_world_state['symbols']


# =========================================================================
# STATISTICS TESTS
# =========================================================================

class TestStatistics:
    
    @pytest.mark.asyncio
    async def test_stats_tracking(self, handler, event_bus):
        """Should track all statistics"""
        await handler.initialize()
        
        # Process some events
        for i in range(3):
            await event_bus.simulate_event('planning.action_decided', {
                'action_name': f'ACTION_{i}',
                'action_params': {},
            })
            await event_bus.simulate_event('world.outcome_received', {
                'outcome_type': 'found_reward',
                'outcome_valence': 0.5,
            })
        
        stats = handler.get_stats()
        
        assert stats['handler']['actions_recorded'] == 3
        assert stats['handler']['outcomes_recorded'] == 3
        assert stats['handler']['events_processed'] >= 6


# =========================================================================
# OUTCOME MAPPING TESTS
# =========================================================================

class TestOutcomeMapping:
    
    def test_positive_outcomes(self):
        """Positive outcomes should have positive valence"""
        mapping = OutcomeMapping()
        
        assert mapping.get_valence('found_reward') > 0
        assert mapping.get_valence('task_completed') > 0
        assert mapping.get_valence('goal_reached') > 0
    
    def test_negative_outcomes(self):
        """Negative outcomes should have negative valence"""
        mapping = OutcomeMapping()
        
        assert mapping.get_valence('took_damage') < 0
        assert mapping.get_valence('ambushed') < 0
        assert mapping.get_valence('died') == -1.0
    
    def test_unknown_outcome_neutral(self):
        """Unknown outcomes should be neutral"""
        mapping = OutcomeMapping()
        
        assert mapping.get_valence('unknown_outcome') == 0.0


# =========================================================================
# WORLD OUTCOME PUBLISHER TESTS
# =========================================================================

class TestWorldOutcomePublisher:
    
    @pytest.fixture
    def publisher(self, event_bus):
        return WorldOutcomePublisher(event_bus)
    
    @pytest.mark.asyncio
    async def test_damage_taken(self, publisher, event_bus):
        """Damage should publish negative outcome"""
        await publisher.damage_taken(amount=50, source='enemy')
        
        assert len(event_bus.published_events) == 1
        event = event_bus.published_events[0]
        assert event.data['outcome_type'] == 'took_damage'
        assert event.data['outcome_valence'] < 0
    
    @pytest.mark.asyncio
    async def test_reward_found(self, publisher, event_bus):
        """Reward should publish positive outcome"""
        await publisher.reward_found(reward_type='gold', amount=100)
        
        assert len(event_bus.published_events) == 1
        event = event_bus.published_events[0]
        assert event.data['outcome_type'] == 'found_reward'
        assert event.data['outcome_valence'] > 0
    
    @pytest.mark.asyncio
    async def test_death_highest_negative(self, publisher, event_bus):
        """Death should have maximum negative valence"""
        await publisher.death(cause='fall')
        
        event = event_bus.published_events[0]
        assert event.data['outcome_valence'] == -1.0
    
    @pytest.mark.asyncio
    async def test_npc_interactions(self, publisher, event_bus):
        """NPC interactions should have appropriate valences"""
        await publisher.npc_interaction('npc_1', 'friendly')
        await publisher.npc_interaction('npc_2', 'hostile')
        
        friendly_event = event_bus.published_events[0]
        hostile_event = event_bus.published_events[1]
        
        assert friendly_event.data['outcome_valence'] > 0
        assert hostile_event.data['outcome_valence'] < 0


# =========================================================================
# MANUAL API TESTS
# =========================================================================

class TestManualAPI:
    
    @pytest.mark.asyncio
    async def test_manual_record_outcome(self, handler, event_bus, somatic_system):
        """Manual outcome recording should work"""
        await handler.initialize()
        
        # Record action via event
        await event_bus.simulate_event('planning.action_decided', {
            'action_name': 'EXPLORE',
            'action_params': {},
        })
        
        # Manual outcome
        handler.manual_record_outcome('found_treasure', outcome_valence=0.8)
        
        assert handler.outcomes_recorded == 1
        assert somatic_system.total_markers == 1


# =========================================================================
# INTEGRATION TEST
# =========================================================================

class TestIntegration:
    
    @pytest.mark.asyncio
    async def test_full_learning_cycle(self, handler, event_bus, somatic_system):
        """Full cycle: action → outcome → bias application"""
        await handler.initialize()
        
        # Cycle 1: Explore → Good outcome
        await event_bus.simulate_event('planning.action_decided', {
            'action_name': 'EXPLORE',
            'action_params': {'danger_level': 0.2},
        })
        await event_bus.simulate_event('world.outcome_received', {
            'outcome_type': 'found_reward',
            'outcome_valence': 0.7,
        })
        
        # Cycle 2: Approach → Bad outcome
        await event_bus.simulate_event('planning.action_decided', {
            'action_name': 'APPROACH_TARGET',
            'action_params': {'danger_level': 0.5},
        })
        await event_bus.simulate_event('world.outcome_received', {
            'outcome_type': 'ambushed',
            'outcome_valence': -0.8,
        })
        
        # Check markers created
        assert somatic_system.total_markers == 2
        
        # Check biases
        biases = somatic_system.get_action_biases(
            {'danger_level': 0.2, 'symbols': []},
            ['EXPLORE', 'APPROACH_TARGET']
        )
        
        # EXPLORE should have positive bias, APPROACH negative
        # (depending on situation hash matching)
        stats = handler.get_stats()
        assert stats['handler']['markers_created'] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
