"""Tests for uem_logger module - Phase A."""
import pytest
import asyncio
import sys
sys.path.insert(0, '.')

from uem_logger import (
    LoggerConfig, DatabaseManager, RunManager,
    CycleManager, EventLogger, EventData, FallbackLogger
)


class TestLoggerConfig:
    """Config tests."""
    
    def test_default_config(self):
        config = LoggerConfig()
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "uem_memory"
        assert config.user == "uem"
    
    def test_dsn_format(self):
        config = LoggerConfig()
        assert "postgresql://" in config.dsn
        assert "uem_memory" in config.dsn


class TestDatabaseManager:
    """Database connection tests."""
    
    @pytest.mark.asyncio
    async def test_connect(self):
        db = DatabaseManager()
        connected = await db.connect()
        assert connected is True
        assert db.is_connected is True
        await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        db = DatabaseManager()
        await db.connect()
        health = await db.health_check()
        assert health["status"] == "healthy"
        assert "PostgreSQL" in health["version"]
        await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_execute_query(self):
        db = DatabaseManager()
        await db.connect()
        result = await db.fetchval("SELECT 1 + 1")
        assert result == 2
        await db.disconnect()


class TestRunManager:
    """Run management tests."""
    
    @pytest.mark.asyncio
    async def test_generate_run_id(self):
        run_id = RunManager.generate_run_id()
        assert run_id.startswith("run_")
        assert len(run_id) > 20
    
    @pytest.mark.asyncio
    async def test_start_and_end_run(self):
        db = DatabaseManager()
        await db.connect()
        
        run_mgr = RunManager(db)
        run_id = await run_mgr.start_run(config={"test": True})
        
        assert run_id is not None
        
        run = await run_mgr.get_run(run_id)
        assert run["status"] == "running"
        
        await run_mgr.end_run(run_id, status="completed")
        
        run = await run_mgr.get_run(run_id)
        assert run["status"] == "completed"
        
        await db.disconnect()


class TestCycleManager:
    """Cycle management tests."""
    
    @pytest.mark.asyncio
    async def test_start_and_end_cycle(self):
        db = DatabaseManager()
        await db.connect()
        
        run_mgr = RunManager(db)
        run_id = await run_mgr.start_run()
        
        cycle_mgr = CycleManager(db)
        await cycle_mgr.start_cycle(run_id, cycle_id=1)
        
        cycle = await cycle_mgr.get_cycle(run_id, 1)
        assert cycle["status"] == "running"
        
        await cycle_mgr.end_cycle(run_id, 1, status="completed")
        
        cycle = await cycle_mgr.get_cycle(run_id, 1)
        assert cycle["status"] == "completed"
        
        await run_mgr.end_run(run_id)
        await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_cycle_count(self):
        db = DatabaseManager()
        await db.connect()
        
        run_mgr = RunManager(db)
        run_id = await run_mgr.start_run()
        
        cycle_mgr = CycleManager(db)
        for i in range(1, 6):
            await cycle_mgr.start_cycle(run_id, cycle_id=i)
        
        count = await cycle_mgr.get_cycle_count(run_id)
        assert count == 5
        
        await run_mgr.end_run(run_id)
        await db.disconnect()


class TestEventLogger:
    """Event logging tests."""
    
    @pytest.mark.asyncio
    async def test_log_single_event(self):
        db = DatabaseManager()
        await db.connect()
        
        run_mgr = RunManager(db)
        run_id = await run_mgr.start_run()
        
        cycle_mgr = CycleManager(db)
        await cycle_mgr.start_cycle(run_id, 1)
        
        event_logger = EventLogger(db)
        event = EventData(
            run_id=run_id,
            cycle_id=1,
            event_type="perception_complete",
            module_name="perception",
            payload={"novelty": 0.8},
            emotion_valence=0.3,
        )
        
        event_id = await event_logger.log_event(event)
        assert event_id > 0
        
        await run_mgr.end_run(run_id)
        await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_log_batch_events(self):
        db = DatabaseManager()
        await db.connect()
        
        run_mgr = RunManager(db)
        run_id = await run_mgr.start_run()
        
        cycle_mgr = CycleManager(db)
        await cycle_mgr.start_cycle(run_id, 1)
        
        event_logger = EventLogger(db)
        events = [
            EventData(run_id=run_id, cycle_id=1, event_type=f"event_{i}", module_name="planner")
            for i in range(10)
        ]
        
        count = await event_logger.log_events_batch(events)
        assert count == 10
        
        total = await event_logger.get_event_count(run_id)
        assert total >= 10
        
        await run_mgr.end_run(run_id)
        await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_query_events_with_filters(self):
        db = DatabaseManager()
        await db.connect()
        
        run_mgr = RunManager(db)
        run_id = await run_mgr.start_run()
        
        cycle_mgr = CycleManager(db)
        await cycle_mgr.start_cycle(run_id, 1)
        
        event_logger = EventLogger(db)
        
        # Log different event types
        await event_logger.log_event(EventData(
            run_id=run_id, cycle_id=1, event_type="action_selected", module_name="planner"
        ))
        await event_logger.log_event(EventData(
            run_id=run_id, cycle_id=1, event_type="ethmor_check", module_name="ethmor"
        ))
        
        # Query by type
        planner_events = await event_logger.get_events(run_id, module_name="planner")
        assert len(planner_events) >= 1
        
        await run_mgr.end_run(run_id)
        await db.disconnect()


class TestFallbackLogger:
    """Fallback file logger tests."""
    
    def test_fallback_log_event(self, tmp_path):
        fallback = FallbackLogger(fallback_dir=str(tmp_path))
        
        event = {
            "run_id": "test_run",
            "cycle_id": 1,
            "event_type": "test",
            "payload": {"data": "test"}
        }
        
        result = fallback.log_event(event)
        assert result is True
        
        files = fallback.get_pending_files()
        assert len(files) == 1
    
    def test_fallback_read_events(self, tmp_path):
        fallback = FallbackLogger(fallback_dir=str(tmp_path))
        
        for i in range(5):
            fallback.log_event({"run_id": "test", "cycle_id": i, "event_type": "test"})
        
        files = fallback.get_pending_files()
        events = fallback.read_fallback_file(files[0])
        assert len(events) == 5
    
    def test_fallback_stats(self, tmp_path):
        fallback = FallbackLogger(fallback_dir=str(tmp_path))
        
        for i in range(3):
            fallback.log_event({"run_id": "test", "event_type": "test"})
        
        stats = fallback.get_stats()
        assert stats["pending_files"] == 1
        assert stats["total_pending_events"] == 3


class TestUEMLoggerFacade:
    """UEMLogger facade tests."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        from uem_logger import UEMLogger
        
        logger = UEMLogger()
        await logger.connect()
        assert logger.is_connected
        
        # Full workflow
        run_id = await logger.start_run(config={"test": True})
        await logger.start_cycle(run_id, 1)
        
        event_id = await logger.log_event(
            run_id, 1, "perception", "test_event",
            payload={"novelty": 0.5}
        )
        assert event_id > 0
        
        await logger.end_cycle(run_id, 1)
        await logger.end_run(run_id)
        
        summary = await logger.get_run_summary(run_id)
        assert summary["status"] == "completed"
        assert summary["cycle_count"] == 1
        
        await logger.disconnect()
    
    @pytest.mark.asyncio
    async def test_denormalization(self):
        from uem_logger import UEMLogger
        
        logger = UEMLogger()
        await logger.connect()
        
        run_id = await logger.start_run()
        await logger.start_cycle(run_id, 1)
        
        # Log with denormalizable fields
        await logger.log_event(run_id, 1, "emotion", "state", {
            "valence": 0.7,
            "arousal": 0.5
        })
        
        await logger.log_event(run_id, 1, "planner", "action", {
            "action": "explore",
            "utility": 0.8
        })
        
        await logger.log_event(run_id, 1, "ethmor", "check", {
            "decision": "allow"
        })
        
        events = await logger.get_cycle_events(run_id, 1)
        
        emotion_ev = next(e for e in events if e["module_name"] == "emotion")
        assert emotion_ev["emotion_valence"] == 0.7
        
        planner_ev = next(e for e in events if e["module_name"] == "planner")
        assert planner_ev["action_name"] == "explore"
        
        ethmor_ev = next(e for e in events if e["module_name"] == "ethmor")
        assert ethmor_ev["ethmor_decision"] == "allow"
        
        await logger.end_run(run_id)
        await logger.disconnect()
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        from uem_logger import UEMLogger
        
        logger = UEMLogger()
        await logger.connect()
        
        health = await logger.health_check()
        assert health["database"]["status"] == "healthy"
        assert "fallback" in health
        
        await logger.disconnect()


class TestMetricRegistry:
    """metric_registry tests."""
    
    @pytest.mark.asyncio
    async def test_registry_populated(self):
        from uem_logger import DatabaseManager
        
        db = DatabaseManager()
        await db.connect()
        
        count = await db.fetchval("SELECT COUNT(*) FROM core.metric_registry")
        assert count == 51
        
        await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_registry_groups(self):
        from uem_logger import DatabaseManager
        
        db = DatabaseManager()
        await db.connect()
        
        groups = await db.fetch(
            "SELECT DISTINCT metric_group FROM core.metric_registry ORDER BY metric_group"
        )
        group_names = [g["metric_group"] for g in groups]
        
        assert "PreData.Core.Planner" in group_names
        assert "PreData.Core.ETHMOR" in group_names
        assert "PreData.Core.Emotion" in group_names
        assert "PreData.DataQuality" in group_names
        
        await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_metric_lookup(self):
        from uem_logger import DatabaseManager
        
        db = DatabaseManager()
        await db.connect()
        
        metric = await db.fetchrow(
            "SELECT * FROM core.metric_registry WHERE metric_id = $1",
            "utility_breakdown"
        )
        
        assert metric is not None
        assert metric["owner_module"] == "planner"
        assert metric["value_type"] == "json"
        
        await db.disconnect()


class TestUtils:
    """Utils tests."""
    
    def test_generate_checksum(self):
        from uem_logger import generate_checksum
        
        data = {"a": 1, "b": 2}
        checksum1 = generate_checksum(data)
        checksum2 = generate_checksum({"b": 2, "a": 1})  # Different order
        
        assert checksum1 == checksum2  # Should be same (sorted keys)
        assert len(checksum1) in [32, 64]  # MD5 or SHA256 hex length
    
    def test_clamp(self):
        from uem_logger import clamp
        
        assert clamp(0.5) == 0.5
        assert clamp(-0.5) == 0.0
        assert clamp(1.5) == 1.0
        assert clamp(0.5, 0.2, 0.8) == 0.5
        assert clamp(0.1, 0.2, 0.8) == 0.2
    
    def test_extract_denorm_fields(self):
        from uem_logger import extract_denorm_fields
        
        # Emotion
        result = extract_denorm_fields({"valence": 0.5}, "emotion")
        assert result["emotion_valence"] == 0.5
        
        # Planner
        result = extract_denorm_fields({"action": "flee"}, "planner")
        assert result["action_name"] == "flee"
        
        # ETHMOR
        result = extract_denorm_fields({"decision": "block"}, "ethmor")
        assert result["ethmor_decision"] == "block"
