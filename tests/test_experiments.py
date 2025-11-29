"""Tests for uem_logger experiments and config_snapshots - Phase C."""
import pytest
import sys
sys.path.insert(0, '.')

from uem_logger import (
    DatabaseManager, ExperimentRepository, ConfigSnapshotRepository,
    generate_config_id, generate_checksum
)


class TestExperimentRepository:
    """ExperimentRepository database tests."""
    
    @pytest.mark.asyncio
    async def test_create_experiment(self):
        db = DatabaseManager()
        await db.connect()
        
        repo = ExperimentRepository(db)
        exp_id = await repo.create(
            experiment_id="test_exp_001",
            name="Test Experiment",
            description="Testing experiment CRUD",
            hypothesis="This will work",
            owner="pytest",
            config={"param1": "value1"},
            tags=["test", "phase_c"]
        )
        
        assert exp_id == "test_exp_001"
        
        # Verify
        exp = await repo.get("test_exp_001")
        assert exp is not None
        assert exp["name"] == "Test Experiment"
        assert exp["status"] == "planned"
        
        # Cleanup
        await repo.delete("test_exp_001")
        await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_experiment_lifecycle(self):
        db = DatabaseManager()
        await db.connect()
        
        repo = ExperimentRepository(db)
        exp_id = "lifecycle_test_001"
        
        await repo.create(experiment_id=exp_id, name="Lifecycle Test")
        
        # Start
        await repo.start(exp_id)
        exp = await repo.get(exp_id)
        assert exp["status"] == "running"
        assert exp["start_ts"] is not None
        
        # Pause
        await repo.pause(exp_id)
        exp = await repo.get(exp_id)
        assert exp["status"] == "paused"
        
        # Complete
        await repo.complete(exp_id)
        exp = await repo.get(exp_id)
        assert exp["status"] == "completed"
        assert exp["end_ts"] is not None
        
        # Cleanup
        await repo.delete(exp_id)
        await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_list_experiments(self):
        db = DatabaseManager()
        await db.connect()
        
        repo = ExperimentRepository(db)
        
        # Create test experiments
        for i in range(3):
            await repo.create(
                experiment_id=f"list_test_{i}",
                name=f"List Test {i}",
                owner="pytest"
            )
        
        # List all
        experiments = await repo.list(owner="pytest")
        assert len(experiments) >= 3
        
        # Cleanup
        for i in range(3):
            await repo.delete(f"list_test_{i}")
        
        await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_add_tags(self):
        db = DatabaseManager()
        await db.connect()
        
        repo = ExperimentRepository(db)
        exp_id = "tag_test_001"
        
        await repo.create(experiment_id=exp_id, name="Tag Test", tags=["initial"])
        await repo.add_tags(exp_id, ["new_tag", "another"])
        
        exp = await repo.get(exp_id)
        assert "initial" in exp["tags"]
        assert "new_tag" in exp["tags"]
        
        await repo.delete(exp_id)
        await db.disconnect()


class TestConfigSnapshotRepository:
    """ConfigSnapshotRepository database tests."""
    
    @pytest.mark.asyncio
    async def test_create_snapshot(self):
        db = DatabaseManager()
        await db.connect()
        
        repo = ConfigSnapshotRepository(db)
        
        config_blob = {
            "planner": {"algorithm": "utility_based"},
            "ethmor": {"rules_version": "1.0"},
            "emotion": {"decay_rate": 0.95}
        }
        
        config_id = await repo.create(
            config_blob=config_blob,
            core_version="1.9.0",
            model_version="test",
            policy_set_id="default",
            description="Test config"
        )
        
        assert config_id.startswith("cfg_")
        
        # Verify
        config = await repo.get(config_id)
        assert config is not None
        assert config["core_version"] == "1.9.0"
        
        await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_verify_checksum(self):
        db = DatabaseManager()
        await db.connect()
        
        repo = ConfigSnapshotRepository(db)
        
        config_blob = {"key": "value", "number": 42}
        config_id = await repo.create(
            config_blob=config_blob,
            core_version="1.0"
        )
        
        # Verify should pass
        is_valid = await repo.verify(config_id)
        assert is_valid is True
        
        await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_find_or_create(self):
        db = DatabaseManager()
        await db.connect()
        
        repo = ConfigSnapshotRepository(db)
        
        config_blob = {"unique_key": "unique_value_12345"}
        
        # First call creates
        id1 = await repo.find_or_create(config_blob, core_version="1.0")
        
        # Second call finds existing
        id2 = await repo.find_or_create(config_blob, core_version="1.0")
        
        assert id1 == id2
        
        await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_list_snapshots(self):
        db = DatabaseManager()
        await db.connect()
        
        repo = ConfigSnapshotRepository(db)
        
        # Create with specific version
        for i in range(3):
            await repo.create(
                config_blob={"index": i},
                core_version="test_list_version"
            )
        
        # List by version
        snapshots = await repo.list(core_version="test_list_version")
        assert len(snapshots) >= 3
        
        await db.disconnect()
    
    @pytest.mark.asyncio
    async def test_get_latest(self):
        db = DatabaseManager()
        await db.connect()
        
        repo = ConfigSnapshotRepository(db)
        
        # Create a config
        await repo.create(
            config_blob={"latest_test": True},
            core_version="latest_test_version"
        )
        
        latest = await repo.get_latest(core_version="latest_test_version")
        assert latest is not None
        
        await db.disconnect()


class TestConfigHelpers:
    """Test helper functions."""
    
    def test_generate_config_id(self):
        config = {"key": "value"}
        id1 = generate_config_id(config)
        id2 = generate_config_id(config)
        
        # Should be deterministic (same hash part)
        assert id1.split("_")[2] == id2.split("_")[2]
        assert id1.startswith("cfg_")
    
    def test_generate_checksum(self):
        config = {"a": 1, "b": 2}
        
        checksum1 = generate_checksum(config)
        checksum2 = generate_checksum({"b": 2, "a": 1})  # Different order
        
        # Should be same (sorted keys)
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA256 hex length
