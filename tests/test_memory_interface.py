# tests/test_memory_interface.py
"""
Memory Interface Tests

Tests for SELF ↔ Memory integration via MemoryInterface.

Author: UEM Project
Date: 26 November 2025
"""

import pytest
import time
from dataclasses import dataclass
from typing import Optional, List, Any, Dict


# ============================================================================
# MOCK CLASSES
# ============================================================================

@dataclass
class MockEvent:
    """Mock Event for testing."""
    source: str
    target: str
    effect: tuple
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class MockSelfEntity:
    """Mock SelfEntity for testing."""
    state_vector: tuple
    history: List[Any] = None
    goals: List[Any] = None
    
    def __post_init__(self):
        if self.history is None:
            self.history = []
        if self.goals is None:
            self.goals = []


@dataclass
class MockGoal:
    """Mock Goal for testing."""
    name: str
    priority: float = 1.0


class MockLTM:
    """Mock LongTermMemory for testing."""
    
    def __init__(self):
        self.stored_items: List[Dict] = []
        self.store_calls = 0
        self.retrieve_calls = 0
    
    def store(
        self,
        content: Any,
        memory_type: Any = None,
        salience: float = 0.5,
        source: str = "",
        **kwargs
    ) -> Any:
        self.store_calls += 1
        item = {
            'content': content,
            'memory_type': memory_type,
            'salience': salience,
            'source': source,
            'created_at': time.time(),
        }
        self.stored_items.append(item)
        return item
    
    def retrieve(
        self,
        memory_type: Any = None,
        limit: int = 10,
        update_access: bool = True,
        **kwargs
    ) -> List[Any]:
        self.retrieve_calls += 1
        
        # Return mock memory objects
        class MockMemory:
            def __init__(self, item):
                self.content = item['content']
                self.created_at = item['created_at']
        
        return [MockMemory(item) for item in self.stored_items[-limit:]]


class MockConsolidator:
    """Mock MemoryConsolidator for testing."""
    
    def __init__(self):
        self.pending_items: List[Dict] = []
        self.add_calls = 0
    
    def add_to_pending(
        self,
        content: Any,
        salience: float = 0.5,
        memory_type: Any = None,
        **kwargs
    ) -> None:
        self.add_calls += 1
        self.pending_items.append({
            'content': content,
            'salience': salience,
            'memory_type': memory_type,
        })


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def memory_interface():
    """Create a standalone MemoryInterface."""
    from core.memory.memory_interface import MemoryInterface
    return MemoryInterface()


@pytest.fixture
def memory_interface_with_ltm():
    """Create MemoryInterface with mock LTM."""
    from core.memory.memory_interface import MemoryInterface
    ltm = MockLTM()
    return MemoryInterface(ltm=ltm), ltm


@pytest.fixture
def memory_interface_with_consolidator():
    """Create MemoryInterface with mock consolidator."""
    from core.memory.memory_interface import MemoryInterface
    ltm = MockLTM()
    consolidator = MockConsolidator()
    return MemoryInterface(ltm=ltm, consolidator=consolidator), consolidator


# ============================================================================
# BASIC TESTS
# ============================================================================

class TestMemoryInterfaceBasic:
    """Basic MemoryInterface tests."""
    
    def test_create_interface(self, memory_interface):
        """Should create interface without errors."""
        assert memory_interface is not None
        assert memory_interface.ltm is None
        assert memory_interface.consolidator is None
    
    def test_create_with_ltm(self, memory_interface_with_ltm):
        """Should create interface with LTM."""
        interface, ltm = memory_interface_with_ltm
        assert interface.ltm is ltm
    
    def test_stats_initial(self, memory_interface):
        """Initial stats should be zero."""
        stats = memory_interface.get_stats()
        assert stats['events_stored'] == 0
        assert stats['snapshots_stored'] == 0
        assert stats['event_buffer_size'] == 0


# ============================================================================
# EVENT STORAGE TESTS
# ============================================================================

class TestEventStorage:
    """Event storage tests."""
    
    def test_store_event_dict(self, memory_interface):
        """Should store event as dict."""
        event = {
            'source': 'player',
            'target': 'enemy',
            'effect': (0.1, -0.2, 0.0),
        }
        
        result = memory_interface.store_event(event)
        
        assert result is True
        assert memory_interface.get_stats()['events_stored'] == 1
    
    def test_store_event_object(self, memory_interface):
        """Should store Event object."""
        event = MockEvent(
            source='world',
            target='self',
            effect=(-0.1, 0.3, -0.1),
        )
        
        result = memory_interface.store_event(event)
        
        assert result is True
        assert memory_interface.get_stats()['events_stored'] == 1
    
    def test_store_event_buffers_when_no_ltm(self, memory_interface):
        """Should buffer events when LTM not available."""
        event = {'source': 'test', 'target': 'test', 'effect': (0, 0, 0)}
        
        memory_interface.store_event(event)
        
        stats = memory_interface.get_stats()
        assert stats['event_buffer_size'] == 1
    
    def test_store_event_to_ltm(self, memory_interface_with_ltm):
        """Should store event to LTM when available."""
        interface, ltm = memory_interface_with_ltm
        
        event = {'source': 'test', 'target': 'test', 'effect': (0, 0, 0)}
        interface.store_event(event)
        
        assert ltm.store_calls == 1
        assert len(ltm.stored_items) == 1
    
    def test_store_event_via_consolidator(self, memory_interface_with_consolidator):
        """Should route events via consolidator when available."""
        interface, consolidator = memory_interface_with_consolidator
        
        event = {'source': 'test', 'target': 'test', 'effect': (0, 0, 0)}
        interface.store_event(event)
        
        assert consolidator.add_calls == 1


# ============================================================================
# SNAPSHOT STORAGE TESTS
# ============================================================================

class TestSnapshotStorage:
    """Snapshot storage tests."""
    
    def test_store_snapshot_dict(self, memory_interface):
        """Should store snapshot as dict."""
        snapshot = {
            'state_vector': (0.7, 0.2, 0.8),
            'history': [],
            'goals': [],
        }
        
        result = memory_interface.store_state_snapshot(snapshot)
        
        assert result is True
        assert memory_interface.get_stats()['snapshots_stored'] == 1
    
    def test_store_snapshot_object(self, memory_interface):
        """Should store SelfEntity object."""
        snapshot = MockSelfEntity(
            state_vector=(0.5, 0.1, 0.6),
            history=[],
            goals=[MockGoal(name='survive')],
        )
        
        result = memory_interface.store_state_snapshot(snapshot)
        
        assert result is True
    
    def test_store_snapshot_to_ltm(self, memory_interface_with_ltm):
        """Should store snapshot to LTM as semantic memory."""
        interface, ltm = memory_interface_with_ltm
        
        snapshot = {'state_vector': (0.5, 0.5, 0.5)}
        interface.store_state_snapshot(snapshot)
        
        assert ltm.store_calls == 1


# ============================================================================
# RETRIEVAL TESTS
# ============================================================================

class TestRetrieval:
    """Retrieval tests."""
    
    def test_get_recent_events_empty(self, memory_interface):
        """Should return empty list when no events."""
        events = memory_interface.get_recent_events(5)
        assert events == []
    
    def test_get_recent_events_from_buffer(self, memory_interface):
        """Should return events from buffer."""
        # Store some events
        for i in range(5):
            memory_interface.store_event({
                'source': f'source_{i}',
                'target': 'self',
                'effect': (0, 0, 0),
            })
        
        events = memory_interface.get_recent_events(3)
        
        assert len(events) == 3
    
    def test_get_recent_events_from_ltm(self, memory_interface_with_ltm):
        """Should retrieve events from LTM."""
        interface, ltm = memory_interface_with_ltm
        
        # Store events
        for i in range(3):
            interface.store_event({'source': f'source_{i}', 'target': 'self', 'effect': (0, 0, 0)})
        
        events = interface.get_recent_events(10)
        
        assert ltm.retrieve_calls >= 1


# ============================================================================
# SIMILARITY TESTS
# ============================================================================

class TestSimilarExperiences:
    """Similar experience search tests."""
    
    def test_get_similar_empty(self, memory_interface):
        """Should return empty when no experiences."""
        similar = memory_interface.get_similar_experiences((0.5, 0.5, 0.5))
        assert similar == []
    
    def test_get_similar_from_buffer(self, memory_interface):
        """Should find similar experiences in buffer."""
        # Store snapshots
        memory_interface.store_state_snapshot({
            'state_vector': (0.8, 0.2, 0.9),
        })
        memory_interface.store_state_snapshot({
            'state_vector': (0.3, 0.8, 0.2),
        })
        
        # Search for similar to (0.8, 0.2, 0.9)
        similar = memory_interface.get_similar_experiences(
            state_vector=(0.75, 0.25, 0.85),
            tolerance=0.3,
        )
        
        assert len(similar) >= 1
        assert similar[0]['similarity'] > 0.7
    
    def test_similarity_computation(self, memory_interface):
        """Test similarity computation directly."""
        # Identical states should have similarity 1.0
        sim1 = memory_interface._compute_similarity((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        assert sim1 == pytest.approx(1.0, rel=0.01)
        
        # Opposite states should have low similarity
        sim2 = memory_interface._compute_similarity((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
        assert sim2 < 0.5


# ============================================================================
# BUFFER MANAGEMENT TESTS
# ============================================================================

class TestBufferManagement:
    """Buffer management tests."""
    
    def test_buffer_max_size(self, memory_interface):
        """Buffer should not exceed max size."""
        memory_interface._max_buffer_size = 10
        
        for i in range(20):
            memory_interface.store_event({'source': f'event_{i}', 'target': 'self', 'effect': (0, 0, 0)})
        
        assert len(memory_interface._event_buffer) <= 10
    
    def test_flush_buffers_to_ltm(self, memory_interface):
        """Should flush buffers when LTM becomes available."""
        # Store without LTM
        for i in range(5):
            memory_interface.store_event({'source': f'event_{i}', 'target': 'self', 'effect': (0, 0, 0)})
        
        assert len(memory_interface._event_buffer) == 5
        
        # Add LTM and flush
        ltm = MockLTM()
        memory_interface.set_ltm(ltm)
        
        # Buffer should be flushed
        assert len(memory_interface._event_buffer) == 0
        assert ltm.store_calls == 5


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestSelfIntegration:
    """Test integration with SELF system."""
    
    def test_self_can_use_interface(self):
        """SELF should be able to use MemoryInterface."""
        from core.memory.memory_interface import MemoryInterface
        
        interface = MemoryInterface()
        
        # Simulate what SELF does
        event = MockEvent(source='action', target='world', effect=(0.1, 0, 0))
        interface.store_event(event)
        
        snapshot = MockSelfEntity(state_vector=(0.6, 0.2, 0.7))
        interface.store_state_snapshot(snapshot)
        
        stats = interface.get_stats()
        assert stats['events_stored'] == 1
        assert stats['snapshots_stored'] == 1
    
    def test_empathy_use_case(self):
        """Test empathy use case - finding similar past experiences."""
        from core.memory.memory_interface import MemoryInterface
        
        interface = MemoryInterface()
        
        # Store past experiences
        past_states = [
            (0.3, 0.8, 0.2),  # Low resource, high threat, low wellbeing
            (0.9, 0.1, 0.9),  # High resource, low threat, high wellbeing
            (0.5, 0.5, 0.5),  # Neutral
            (0.35, 0.75, 0.25),  # Similar to first
        ]
        
        for state in past_states:
            interface.store_state_snapshot({'state_vector': state})
        
        # OTHER agent is in distress: (0.3, 0.8, 0.2)
        other_state = (0.3, 0.8, 0.2)
        
        similar = interface.get_similar_experiences(
            state_vector=other_state,
            tolerance=0.2,
        )
        
        # Should find at least the exact match and similar one
        assert len(similar) >= 1
        assert similar[0]['similarity'] >= 0.8


# ============================================================================
# FACTORY TESTS
# ============================================================================

class TestFactory:
    """Factory function tests."""
    
    def test_create_memory_interface(self):
        """Should create interface via factory."""
        from core.memory.memory_interface import create_memory_interface
        
        interface = create_memory_interface()
        assert interface is not None
    
    def test_create_with_ltm(self):
        """Should create interface with LTM via factory."""
        from core.memory.memory_interface import create_memory_interface
        
        ltm = MockLTM()
        interface = create_memory_interface(ltm=ltm)
        
        assert interface.ltm is ltm


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
