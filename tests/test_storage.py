"""
Storage Implementation Tests
"""

import pytest
from datetime import datetime
from core.memory.storage import (
    MemoryStorage, FileStorage, StoredEvent, StoredSnapshot, get_storage
)

# ============== Fixtures ==============

@pytest.fixture
def memory_storage():
    storage = MemoryStorage()
    yield storage
    storage.close()

@pytest.fixture
def file_storage(tmp_path):
    storage = FileStorage(data_dir=str(tmp_path / "test_storage"))
    yield storage
    storage.clear()

@pytest.fixture
def sample_event():
    return StoredEvent(
        source='world',
        target='agent',
        effect=(0.5, 0.2, 0.3, 0, 0, 0, 0, 0),
        tick=1,
        salience=0.7
    )

@pytest.fixture
def sample_snapshot():
    return StoredSnapshot(
        state_vector=(0.6, 0.3, 0.8, 0, 0, 0, 0, 0),
        tick=1,
        salience=0.8
    )

# ============== MemoryStorage Tests ==============

class TestMemoryStorage:
    
    def test_store_event(self, memory_storage, sample_event):
        event_id = memory_storage.store_event(sample_event)
        assert event_id == 1
        assert memory_storage.get_stats()['events_stored'] == 1
    
    def test_store_snapshot(self, memory_storage, sample_snapshot):
        snap_id = memory_storage.store_snapshot(sample_snapshot)
        assert snap_id == 1
        assert memory_storage.get_stats()['snapshots_stored'] == 1
    
    def test_get_recent_events(self, memory_storage):
        for i in range(5):
            e = StoredEvent(source=f'src_{i}', target='agent', effect=(0.1*i,0,0,0,0,0,0,0), tick=i)
            memory_storage.store_event(e)
        
        events = memory_storage.get_recent_events(3)
        assert len(events) == 3
        assert events[0].tick == 4  # Most recent first
    
    def test_get_recent_snapshots(self, memory_storage):
        for i in range(5):
            s = StoredSnapshot(state_vector=(0.1*i,0,0,0,0,0,0,0), tick=i)
            memory_storage.store_snapshot(s)
        
        snapshots = memory_storage.get_recent_snapshots(3)
        assert len(snapshots) == 3
        assert snapshots[0].tick == 4
    
    def test_similar_experiences(self, memory_storage):
        memory_storage.store_snapshot(StoredSnapshot(state_vector=(0.5, 0.5, 0.5, 0,0,0,0,0), tick=1))
        memory_storage.store_snapshot(StoredSnapshot(state_vector=(0.9, 0.9, 0.9, 0,0,0,0,0), tick=2))
        
        similar = memory_storage.get_similar_experiences(
            (0.5, 0.5, 0.5, 0,0,0,0,0), 
            tolerance=0.3
        )
        assert len(similar) == 1
        assert similar[0].tick == 1
    
    def test_clear(self, memory_storage, sample_event, sample_snapshot):
        memory_storage.store_event(sample_event)
        memory_storage.store_snapshot(sample_snapshot)
        memory_storage.clear()
        
        assert len(memory_storage.get_all_events()) == 0
        assert len(memory_storage.get_all_snapshots()) == 0

# ============== FileStorage Tests ==============

class TestFileStorage:
    
    def test_store_event(self, file_storage, sample_event):
        event_id = file_storage.store_event(sample_event)
        assert event_id == 1
    
    def test_store_snapshot(self, file_storage, sample_snapshot):
        snap_id = file_storage.store_snapshot(sample_snapshot)
        assert snap_id == 1
    
    def test_persistence(self, tmp_path):
        # Sabit agent_id kullan
        agent_id = "test-agent-123"
        data_dir = str(tmp_path / "persist_test")
        
        # İlk storage
        storage1 = FileStorage(agent_id=agent_id, data_dir=data_dir)
        storage1.store_event(StoredEvent(source='test', target='agent', effect=(0.1,0,0,0,0,0,0,0), tick=1))
        storage1.store_snapshot(StoredSnapshot(state_vector=(0.5,0,0,0,0,0,0,0), tick=1))
        
        # Yeni storage aynı path ve agent_id ile
        storage2 = FileStorage(agent_id=agent_id, data_dir=data_dir)
        
        events = storage2.get_recent_events(10)
        snapshots = storage2.get_recent_snapshots(10)
        
        assert len(events) == 1
        assert len(snapshots) == 1
    
    def test_similar_experiences(self, file_storage):
        file_storage.store_snapshot(StoredSnapshot(state_vector=(0.5, 0.5, 0.5, 0,0,0,0,0), tick=1))
        file_storage.store_snapshot(StoredSnapshot(state_vector=(0.9, 0.9, 0.9, 0,0,0,0,0), tick=2))
        
        similar = file_storage.get_similar_experiences(
            (0.5, 0.5, 0.5, 0,0,0,0,0), 
            tolerance=0.3
        )
        assert len(similar) == 1

# ============== Factory Tests ==============

class TestFactory:
    
    def test_get_memory_storage(self):
        storage = get_storage("memory")
        assert isinstance(storage, MemoryStorage)
        storage.close()
    
    def test_get_file_storage(self, tmp_path):
        storage = get_storage("file", data_dir=str(tmp_path))
        assert isinstance(storage, FileStorage)
        storage.close()
    
    def test_invalid_type(self):
        with pytest.raises(ValueError):
            get_storage("invalid")

# ============== Base Methods Tests ==============

class TestBaseMethods:
    
    def test_compute_distance(self, memory_storage):
        v1 = (0, 0, 0, 0, 0, 0, 0, 0)
        v2 = (1, 0, 0, 0, 0, 0, 0, 0)
        assert memory_storage.compute_distance(v1, v2) == 1.0
    
    def test_compute_similarity(self, memory_storage):
        v1 = (0.5, 0.5, 0.5, 0, 0, 0, 0, 0)
        v2 = (0.5, 0.5, 0.5, 0, 0, 0, 0, 0)
        assert memory_storage.compute_similarity(v1, v2) == 1.0
    
    def test_health_check(self, memory_storage):
        assert memory_storage.health_check() == True
    
    def test_stats(self, memory_storage, sample_event):
        memory_storage.store_event(sample_event)
        stats = memory_storage.get_stats()
        
        assert 'events_stored' in stats
        assert stats['events_stored'] == 1

# ============== PostgresStorage Tests ==============

@pytest.mark.postgres
class TestPostgresStorage:
    
    @pytest.fixture
    def pg_storage(self):
        from core.memory.storage import PostgresStorage
        storage = PostgresStorage()
        storage.initialize()
        yield storage
        storage.close()
    
    def test_health_check(self, pg_storage):
        assert pg_storage.health_check() == True
    
    def test_store_and_retrieve(self, pg_storage):
        event = StoredEvent(source='test', target='agent', effect=(0.1,0,0,0,0,0,0,0), tick=999)
        event_id = pg_storage.store_event(event)
        assert event_id > 0
        
        events = pg_storage.get_recent_events(10)
        assert len(events) >= 1
