"""
MemoryInterface Tests - Updated for v2 with Storage Backends
"""

import pytest
from core.memory.memory_interface import MemoryInterface, create_memory_interface
from core.memory.storage import MemoryStorage, StoredEvent, StoredSnapshot


# ============== Fixtures ==============

@pytest.fixture
def memory_interface():
    mi = create_memory_interface(storage_type="memory")
    yield mi
    mi.close()

@pytest.fixture
def sample_event():
    return {'source': 'world', 'target': 'agent', 'effect': (0.5, 0.2, 0.3), 'tick': 1}

@pytest.fixture
def sample_snapshot():
    return {'state_vector': (0.6, 0.3, 0.8), 'tick': 1}


# ============== Basic Tests ==============

class TestMemoryInterfaceBasic:
    
    def test_create_interface(self):
        mi = create_memory_interface()
        assert mi is not None
        mi.close()
    
    def test_create_with_storage_type(self):
        mi = create_memory_interface(storage_type="memory")
        assert mi.storage is not None
        assert isinstance(mi.storage, MemoryStorage)
        mi.close()
    
    def test_stats_initial(self, memory_interface):
        stats = memory_interface.get_stats()
        assert stats['events_stored'] == 0
        assert stats['snapshots_stored'] == 0
        assert 'storage' in stats
        assert stats['storage_type'] == 'MemoryStorage'


# ============== Event Storage Tests ==============

class TestEventStorage:
    
    def test_store_event_dict(self, memory_interface, sample_event):
        result = memory_interface.store_event(sample_event)
        assert result == True
        assert memory_interface.get_stats()['events_stored'] == 1
    
    def test_store_event_object(self, memory_interface):
        class MockEvent:
            source = 'test'
            target = 'agent'
            effect = (0.1, 0.2, 0.3)
            tick = 5
        
        result = memory_interface.store_event(MockEvent())
        assert result == True
    
    def test_store_multiple_events(self, memory_interface):
        for i in range(5):
            memory_interface.store_event({'source': f'src_{i}', 'target': 'agent', 'effect': (0.1*i, 0, 0), 'tick': i})
        
        assert memory_interface.get_stats()['events_stored'] == 5


# ============== Snapshot Storage Tests ==============

class TestSnapshotStorage:
    
    def test_store_snapshot_dict(self, memory_interface, sample_snapshot):
        result = memory_interface.store_state_snapshot(sample_snapshot)
        assert result == True
        assert memory_interface.get_stats()['snapshots_stored'] == 1
    
    def test_store_snapshot_object(self, memory_interface):
        class MockSnapshot:
            state_vector = (0.5, 0.5, 0.5)
            history = []
            goals = []
            tick = 1
        
        result = memory_interface.store_state_snapshot(MockSnapshot())
        assert result == True
    
    def test_store_multiple_snapshots(self, memory_interface):
        for i in range(5):
            memory_interface.store_state_snapshot({'state_vector': (0.1*i, 0.2, 0.3), 'tick': i})
        
        assert memory_interface.get_stats()['snapshots_stored'] == 5


# ============== Retrieval Tests ==============

class TestRetrieval:
    
    def test_get_recent_events_empty(self, memory_interface):
        events = memory_interface.get_recent_events(5)
        assert events == []
    
    def test_get_recent_events(self, memory_interface):
        for i in range(5):
            memory_interface.store_event({'source': f'src_{i}', 'target': 'agent', 'effect': (0.1, 0, 0), 'tick': i})
        
        events = memory_interface.get_recent_events(3)
        assert len(events) == 3
        assert events[0]['tick'] == 4  # Most recent first
    
    def test_get_recent_snapshots_empty(self, memory_interface):
        snapshots = memory_interface.get_recent_snapshots(5)
        assert snapshots == []
    
    def test_get_recent_snapshots(self, memory_interface):
        for i in range(5):
            memory_interface.store_state_snapshot({'state_vector': (0.1*i, 0, 0), 'tick': i})
        
        snapshots = memory_interface.get_recent_snapshots(3)
        assert len(snapshots) == 3


# ============== Similar Experiences Tests ==============

class TestSimilarExperiences:
    
    def test_get_similar_empty(self, memory_interface):
        similar = memory_interface.get_similar_experiences((0.5, 0.5, 0.5))
        assert similar == []
    
    def test_get_similar_with_data(self, memory_interface):
        # Store some snapshots
        memory_interface.store_state_snapshot({'state_vector': (0.5, 0.5, 0.5), 'tick': 1})
        memory_interface.store_state_snapshot({'state_vector': (0.9, 0.9, 0.9), 'tick': 2})
        
        # Find similar
        similar = memory_interface.get_similar_experiences((0.5, 0.5, 0.5), tolerance=0.3)
        assert len(similar) == 1
        assert similar[0]['similarity'] > 0.9
    
    def test_similarity_returns_score(self, memory_interface):
        memory_interface.store_state_snapshot({'state_vector': (0.5, 0.5, 0.5), 'tick': 1})
        
        similar = memory_interface.get_similar_experiences((0.5, 0.5, 0.5), tolerance=0.5)
        assert len(similar) == 1
        assert 'similarity' in similar[0]
        assert 'state_vector' in similar[0]


# ============== SELF Integration Tests ==============

class TestSelfIntegration:
    
    def test_self_can_use_interface(self, memory_interface):
        # Simulate SELF usage
        memory_interface.store_event({'source': 'world', 'target': 'self', 'effect': (0.1, 0.2, 0.3)})
        memory_interface.store_state_snapshot({'state_vector': (0.6, 0.3, 0.8)})
        
        events = memory_interface.get_recent_events(10)
        snapshots = memory_interface.get_recent_snapshots(10)
        
        assert len(events) == 1
        assert len(snapshots) == 1
    
    def test_empathy_use_case(self, memory_interface):
        # Store own experiences
        memory_interface.store_state_snapshot({'state_vector': (0.2, 0.8, 0.3), 'tick': 1})  # High threat
        memory_interface.store_state_snapshot({'state_vector': (0.8, 0.1, 0.9), 'tick': 2})  # Good state
        
        # Find similar to observed other (high threat)
        similar = memory_interface.get_similar_experiences((0.2, 0.7, 0.4), tolerance=0.4)
        assert len(similar) >= 1


# ============== Factory Tests ==============

class TestFactory:
    
    def test_create_memory_interface(self):
        mi = create_memory_interface()
        assert isinstance(mi, MemoryInterface)
        mi.close()
    
    def test_create_with_config(self):
        mi = create_memory_interface(config={'max_buffer_size': 500})
        assert mi.config.get('max_buffer_size') == 500
        mi.close()
    
    def test_create_with_agent_id(self):
        mi = create_memory_interface(agent_id="test-agent")
        assert mi.storage.agent_id == "test-agent"
        mi.close()


# ============== Health & Stats Tests ==============

class TestHealthAndStats:
    
    def test_health_check(self, memory_interface):
        assert memory_interface.health_check() == True
    
    def test_stats_after_operations(self, memory_interface):
        memory_interface.store_event({'source': 'a', 'target': 'b', 'effect': (0,0,0)})
        memory_interface.store_state_snapshot({'state_vector': (0.5, 0.5, 0.5)})
        memory_interface.get_recent_events(5)
        
        stats = memory_interface.get_stats()
        assert stats['events_stored'] == 1
        assert stats['snapshots_stored'] == 1
        assert stats['events_retrieved'] == 1
