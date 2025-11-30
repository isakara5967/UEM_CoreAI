"""
E2E Test: Full cycle → DB write → Query
Tests the complete data flow from cognitive cycle to PostgreSQL.
"""
import pytest
import asyncio

from core.unified_core import create_unified_core


class MockWorldState:
    """Simple world state for testing."""
    def __init__(self, tick=1, danger_level=0.3):
        self.tick = tick
        self.danger_level = danger_level
        self.objects = [{'type': 'food', 'x': 5, 'y': 5}]
        self.agents = [{'type': 'neutral', 'x': 10, 'y': 10}]
        self.symbols = ['test_symbol']
        self.events = []


@pytest.mark.asyncio
async def test_e2e_full_cycle_db_write():
    """Test: Run cycles → Write to DB → Query back."""
    core = create_unified_core(storage_type="memory")
    
    run_id = await core.start_logging({
        'experiment': 'e2e_test',
        'description': 'Full cycle DB write test',
    })
    
    if run_id is None:
        pytest.skip("Database not available")
    
    try:
        # Run 3 cycles
        for i in range(3):
            world = MockWorldState(tick=i+1, danger_level=0.2 * (i+1))
            result = await core.cycle(world)
            assert result is not None
        
        # Direct DB query (more reliable)
        logger = core.log_integration.logger
        events = await logger.db.fetch(
            "SELECT * FROM core.events WHERE run_id = $1 AND event_type = $2",
            run_id, 'cycle_predata'
        )
        
        assert len(events) >= 3, f"Expected 3 PreData events, got {len(events)}"
        
        # Verify payload exists
        for event in events:
            assert event['payload'] is not None
        
    finally:
        await core.stop_logging()


@pytest.mark.asyncio
async def test_e2e_metamind_written():
    """Test: MetaMind summary is written to DB."""
    core = create_unified_core(storage_type="memory")
    
    run_id = await core.start_logging({'experiment': 'metamind_test'})
    if run_id is None:
        pytest.skip("Database not available")
    
    try:
        for i in range(5):
            world = MockWorldState(tick=i+1)
            await core.cycle(world)
        
        logger = core.log_integration.logger
        events = await logger.db.fetch(
            "SELECT * FROM core.events WHERE run_id = $1 AND event_type = $2",
            run_id, 'cycle_summary'
        )
        
        # MetaMind writes every cycle
        assert len(events) >= 1, f"Expected MetaMind summaries, got {len(events)}"
    
    finally:
        await core.stop_logging()


@pytest.mark.asyncio
async def test_e2e_denormalized_columns():
    """Test: Denormalized columns are populated."""
    core = create_unified_core(storage_type="memory")
    
    run_id = await core.start_logging({'experiment': 'denorm_test'})
    if run_id is None:
        pytest.skip("Database not available")
    
    try:
        world = MockWorldState(tick=1, danger_level=0.5)
        await core.cycle(world)
        
        logger = core.log_integration.logger
        events = await logger.db.fetch(
            "SELECT * FROM core.events WHERE run_id = $1 AND event_type = $2",
            run_id, 'cycle_predata'
        )
        
        assert len(events) >= 1
        event = dict(events[0])
        
        # Check denormalized columns exist
        assert 'emotion_valence' in event
        assert 'action_name' in event
    
    finally:
        await core.stop_logging()


@pytest.mark.asyncio
async def test_e2e_all_event_types():
    """Test: All event types are written per cycle."""
    core = create_unified_core(storage_type="memory")
    
    run_id = await core.start_logging({'experiment': 'event_types_test'})
    if run_id is None:
        pytest.skip("Database not available")
    
    try:
        world = MockWorldState(tick=1)
        await core.cycle(world)
        
        logger = core.log_integration.logger
        events = await logger.db.fetch(
            "SELECT event_type FROM core.events WHERE run_id = $1 AND cycle_id = 1",
            run_id
        )
        
        event_types = [e['event_type'] for e in events]
        
        # Expected event types per cycle
        expected = ['perception_complete', 'emotion_updated', 'action_selected', 
                    'ethmor_check', 'cycle_complete', 'cycle_predata']
        
        for et in expected:
            assert et in event_types, f"Missing event type: {et}"
    
    finally:
        await core.stop_logging()
