"""Tests for core/logger_integration.py"""
import pytest
import sys
sys.path.insert(0, '.')

from core.logger_integration import CoreLoggerIntegration, CycleLogData
from uem_logger import UEMLogger


class TestCycleLogData:
    """CycleLogData dataclass tests."""
    
    def test_create_minimal(self):
        data = CycleLogData(tick=1, cycle_id=1)
        assert data.tick == 1
        assert data.novelty_score is None
        assert data.action_name is None
    
    def test_create_full(self):
        data = CycleLogData(
            tick=5,
            cycle_id=5,
            novelty_score=0.8,
            valence=0.5,
            arousal=0.6,
            action_name="explore",
            ethmor_decision="allow"
        )
        assert data.novelty_score == 0.8
        assert data.action_name == "explore"


class TestCoreLoggerIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_disabled_mode(self):
        """Test that disabled mode doesn't error."""
        integration = CoreLoggerIntegration(enabled=False)
        
        run_id = await integration.start()
        assert run_id is None
        
        integration.on_cycle_start(1)
        integration.on_perception(novelty_score=0.5)
        integration.on_emotion(valence=0.3)
        integration.on_planning(action="wait")
        await integration.on_cycle_end(success=True)
        await integration.stop()
        
        # Should complete without errors
    
    @pytest.mark.asyncio
    async def test_full_cycle_logging(self):
        """Test complete cycle logging flow."""
        integration = CoreLoggerIntegration()
        run_id = await integration.start(run_config={"test": "full_cycle"})
        
        assert run_id is not None
        assert integration.run_id == run_id
        
        # Log one complete cycle
        integration.on_cycle_start(tick=1)
        integration.on_perception(novelty_score=0.7, attention_focus="test")
        integration.on_emotion(valence=0.5, arousal=0.6, label="curious")
        integration.on_workspace(coalition_strength=0.8)
        integration.on_planning(action="explore", utility=0.75, candidates=["explore", "wait"])
        integration.on_ethmor(decision="allow", risk_level=0.1)
        await integration.on_cycle_end(success=True)
        
        await integration.stop(summary={"test": True})
        
        # Verify
        logger = UEMLogger()
        await logger.connect()
        
        summary = await logger.get_run_summary(run_id)
        assert summary["cycle_count"] == 1
        assert summary["event_count"] == 6  # perception, emotion, workspace, planner, ethmor, execution
        
        await logger.disconnect()
    
    @pytest.mark.asyncio
    async def test_multiple_cycles(self):
        """Test multiple cycle logging."""
        integration = CoreLoggerIntegration()
        run_id = await integration.start()
        
        for i in range(1, 4):
            integration.on_cycle_start(tick=i)
            integration.on_planning(action=f"action_{i}", utility=0.5)
            await integration.on_cycle_end(success=i % 2 == 0)
        
        await integration.stop()
        
        # Verify
        logger = UEMLogger()
        await logger.connect()
        
        summary = await logger.get_run_summary(run_id)
        assert summary["cycle_count"] == 3
        
        await logger.disconnect()
    
    @pytest.mark.asyncio
    async def test_partial_data(self):
        """Test logging with partial data (not all phases)."""
        integration = CoreLoggerIntegration()
        run_id = await integration.start()
        
        integration.on_cycle_start(tick=1)
        # Only log perception and planning
        integration.on_perception(novelty_score=0.5)
        integration.on_planning(action="wait")
        await integration.on_cycle_end()
        
        await integration.stop()
        
        # Verify - should have 3 events (perception, planner, execution)
        logger = UEMLogger()
        await logger.connect()
        
        events = await logger.get_cycle_events(run_id, 1)
        module_names = [e["module_name"] for e in events]
        
        assert "perception" in module_names
        assert "planner" in module_names
        assert "execution" in module_names
        assert "emotion" not in module_names  # Not logged
        
        await logger.disconnect()
    
    @pytest.mark.asyncio
    async def test_cycle_time_measurement(self):
        """Test that cycle time is measured."""
        import time
        
        integration = CoreLoggerIntegration()
        run_id = await integration.start()
        
        integration.on_cycle_start(tick=1)
        time.sleep(0.05)  # 50ms delay
        integration.on_planning(action="test")
        await integration.on_cycle_end()
        
        await integration.stop()
        
        # Verify cycle time
        logger = UEMLogger()
        await logger.connect()
        
        events = await logger.get_cycle_events(run_id, 1)
        exec_event = next(e for e in events if e["module_name"] == "execution")
        
        assert exec_event["cycle_time_ms"] >= 50  # At least 50ms
        
        await logger.disconnect()
