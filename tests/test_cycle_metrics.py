"""
Sprint 0C: CycleMetrics Extended Tests
"""
import pytest
from core.unified_core import create_unified_core
from core.unified_types import CycleMetrics
from core.integrated_uem_core import WorldState


class TestCycleMetricsExtended:
    """Sprint 0C CycleMetrics testleri"""
    
    def test_metrics_has_new_fields(self):
        """CycleMetrics yeni alanlara sahip olmalı"""
        m = CycleMetrics()
        assert hasattr(m, 'action_taken')
        assert hasattr(m, 'action_success')
        assert hasattr(m, 'emotion_valence')
        assert hasattr(m, 'emotion_arousal')
        assert hasattr(m, 'emotion_label')
        assert hasattr(m, 'conscious_type')
        assert hasattr(m, 'conscious_activation')
    
    def test_metrics_to_dict_extended(self):
        """to_dict() tüm alanları içermeli"""
        m = CycleMetrics(
            tick=5,
            action_taken="flee",
            action_success=True,
            emotion_label="fear",
        )
        d = m.to_dict()
        assert d['tick'] == 5
        assert d['action_taken'] == "flee"
        assert d['action_success'] == True
        assert d['emotion_label'] == "fear"
    
    def test_metrics_collected_after_cycle(self):
        """Cycle sonrası extended metrics toplanmalı"""
        core = create_unified_core(collect_metrics=True)
        
        world = WorldState(
            tick=1,
            danger_level=0.8,
            player_health=0.5,
            player_energy=0.5,
        )
        
        core.cycle_sync(world)
        
        assert core.last_metrics is not None
        assert core.last_metrics.action_taken is not None
        assert core.last_metrics.emotion_label is not None
    
    def test_metrics_history_grows(self):
        """metrics_history büyümeli"""
        core = create_unified_core(collect_metrics=True)
        
        for i in range(5):
            world = WorldState(tick=i+1, danger_level=0.1 * i)
            core.cycle_sync(world)
        
        assert len(core.metrics_history) == 5
    
    def test_metrics_history_max_100(self):
        """metrics_history max 100 tutmalı"""
        core = create_unified_core(collect_metrics=True)
        
        # 105 cycle
        for i in range(105):
            world = WorldState(tick=i+1, danger_level=0.1)
            core.cycle_sync(world)
        
        assert len(core.metrics_history) <= 100
    
    def test_get_metrics_summary(self):
        """get_metrics_summary çalışmalı"""
        core = create_unified_core(collect_metrics=True)
        
        for i in range(10):
            world = WorldState(tick=i+1, danger_level=0.5)
            core.cycle_sync(world)
        
        summary = core.get_metrics_summary(last_n=5)
        
        assert 'total_cycles' in summary
        assert 'success_rate' in summary
        assert 'avg_valence' in summary
        assert 'action_distribution' in summary
        assert summary['total_cycles'] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
