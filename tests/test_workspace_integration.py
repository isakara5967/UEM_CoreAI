"""
Sprint 0B: GlobalWorkspace Integration Tests
"""
import pytest
import asyncio
from core.unified_core import create_unified_core, UnifiedUEMCore
from core.integrated_uem_core import WorldState


class TestWorkspaceIntegration:
    """UnifiedUEMCore + WorkspaceManager entegrasyon testleri"""
    
    def test_workspace_manager_loaded(self):
        """WorkspaceManager yüklenmeli"""
        core = create_unified_core()
        assert core.workspace_manager is not None
        
    def test_get_conscious_content_api(self):
        """get_conscious_content API mevcut olmalı"""
        core = create_unified_core()
        # İlk başta None
        assert core.get_conscious_content() is None
        
    def test_workspace_cycle_runs(self):
        """Workspace cycle çalışmalı ve conscious üretmeli"""
        core = create_unified_core()
        
        # Tehlikeli world state
        world = WorldState(
            tick=1,
            danger_level=0.8,
            player_health=0.3,
            player_energy=0.5,
            symbols=['ENEMY'],
        )
        
        result = core.cycle_sync(world)
        conscious = core.get_conscious_content()
        
        # Cycle tamamlanmalı
        assert result is not None
        # Yüksek tehlikede conscious content üretilmeli
        assert conscious is not None
        
    def test_conscious_content_structure(self):
        """Conscious content doğru yapıda olmalı"""
        core = create_unified_core()
        
        world = WorldState(
            tick=1,
            danger_level=0.9,
            player_health=0.2,
            player_energy=0.3,
        )
        
        core.cycle_sync(world)
        conscious = core.get_conscious_content()
        
        if conscious:
            # BroadcastMessage yapısı
            assert hasattr(conscious, 'content_type')
            assert hasattr(conscious, 'coalition')
            assert hasattr(conscious.coalition, 'activation')
            
    def test_subscribers_registered(self):
        """3 subscriber kayıtlı olmalı"""
        core = create_unified_core()
        
        assert hasattr(core, '_perception_subscriber')
        assert hasattr(core, '_memory_subscriber')
        assert hasattr(core, '_planning_subscriber')
        
    def test_urgency_on_danger(self):
        """Yüksek tehlikede URGENCY broadcast olmalı"""
        core = create_unified_core()
        
        world = WorldState(
            tick=1,
            danger_level=0.85,
            player_health=1.0,
            player_energy=1.0,
        )
        
        core.cycle_sync(world)
        conscious = core.get_conscious_content()
        
        if conscious:
            assert conscious.content_type.name == "URGENCY"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
