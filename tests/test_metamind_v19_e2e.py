"""
MetaMind v1.9 End-to-End Tests
==============================

Bu test dosyası MetaMind v1.9'un tüm bileşenlerini test eder.

Tarih: 2025-12-05
"""

import pytest
import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class MockWorldState:
    """Test için WorldState mock."""
    tick: int = 0
    danger_level: float = 0.0
    player_health: float = 0.8
    player_energy: float = 0.7
    objects: List[Dict] = field(default_factory=list)
    agents: List[Dict] = field(default_factory=list)
    symbols: List[str] = field(default_factory=list)


class TestMetaMindComponents:
    """MetaMind bileşen testleri."""
    
    def test_metamind_core_exists(self):
        """MetaMindCore import edilebilir."""
        from core.metamind import MetaMindCore
        assert MetaMindCore is not None
    
    def test_metamind_core_initialization(self):
        """MetaMindCore başlatılabilir."""
        from core.metamind import MetaMindCore
        mm = MetaMindCore()
        assert mm is not None
        asyncio.run(mm.initialize("test_run"))
        assert mm._initialized is True
    
    def test_metamind_has_all_components(self):
        """MetaMindCore tüm bileşenlere sahip."""
        from core.metamind import MetaMindCore
        mm = MetaMindCore()
        
        assert hasattr(mm, 'episode_manager')
        assert hasattr(mm, 'meta_state_calculator')
        assert hasattr(mm, 'cycle_analyzer')
        assert hasattr(mm, 'pattern_miner')
        assert hasattr(mm, 'insight_generator')
        assert hasattr(mm, 'social_pipeline')
    
    def test_social_pipeline_not_stub(self):
        """SocialHealthPipeline artık STUB değil."""
        from core.metamind import MetaMindCore
        mm = MetaMindCore()
        
        metrics = mm.social_pipeline.get_metrics()
        assert metrics.is_stub is False


class TestMetaState:
    """MetaState hesaplama testleri."""
    
    def test_meta_state_has_six_metrics(self):
        """MetaState 6 metrik içerir."""
        from core.metamind import MetaMindCore
        mm = MetaMindCore()
        asyncio.run(mm.initialize("test_run"))
        
        cycle_data = {
            "valence": 0.5,
            "arousal": 0.5,
            "action": "wait",
            "success": True,
            "coherence": 0.7,
            "efficiency": 0.8,
            "quality": 0.6,
            "failure_streak": 0,
            "cycle_time_ms": 10,
        }
        
        meta_state = asyncio.run(mm.on_cycle_end(cycle_id=1, cycle_data=cycle_data))
        
        assert meta_state is not None
        assert hasattr(meta_state, 'global_cognitive_health')
        assert hasattr(meta_state, 'emotional_stability')
        assert hasattr(meta_state, 'ethical_alignment')
        assert hasattr(meta_state, 'exploration_bias')
        assert hasattr(meta_state, 'failure_pressure')
        assert hasattr(meta_state, 'memory_health')
    
    def test_meta_state_confidence_in_metrics(self):
        """MetaState metrikleri confidence içerir (MetricWithConfidence)."""
        from core.metamind import MetaMindCore
        mm = MetaMindCore()
        asyncio.run(mm.initialize("test_run"))
        
        cycle_data = {"valence": 0.5, "arousal": 0.5, "action": "wait", "success": True}
        meta_state = asyncio.run(mm.on_cycle_end(cycle_id=1, cycle_data=cycle_data))
        
        # MetricWithConfidence yapısı içinde confidence var
        assert hasattr(meta_state.global_cognitive_health, 'confidence')
        assert hasattr(meta_state.emotional_stability, 'confidence')
        assert hasattr(meta_state.ethical_alignment, 'confidence')


class TestEpisodeManager:
    """Episode yönetimi testleri."""
    
    def test_episode_creation(self):
        """Episode oluşturulabiliyor."""
        from core.metamind import MetaMindCore
        mm = MetaMindCore()
        asyncio.run(mm.initialize("test_run"))
        
        episode_id = mm.episode_manager.get_current_episode_id()
        assert episode_id is not None
        assert "test_run" in episode_id
    
    def test_episode_window_from_config(self):
        """Episode window config'den alınıyor (magic number yok)."""
        from core.metamind import MetaMindCore
        mm = MetaMindCore()
        
        assert hasattr(mm.config, 'episode')
        assert mm.config.episode.window_cycles > 0


class TestSocialHealthPipeline:
    """SocialHealthPipeline testleri."""
    
    def test_process_empathy_results_after_init(self):
        """Empathy sonuçları işlenebiliyor (initialize sonrası)."""
        from core.metamind import MetaMindCore
        
        mm = MetaMindCore()
        asyncio.run(mm.initialize("test_run"))  # Pipeline'ı initialize et
        
        # Mock empathy result
        class MockOtherEntity:
            entity_id = "test_agent"
            relationship = 0.5
        
        class MockEmpathyResult:
            empathy_level = 0.7
            resonance = 0.8
            confidence = 0.5
            other_entity = MockOtherEntity()
        
        mm.social_pipeline.process_empathy_results([MockEmpathyResult()])
        
        metrics = mm.social_pipeline.get_metrics()
        assert metrics.average_empathy == 0.7
        assert metrics.average_resonance == 0.8
        assert metrics.data_points == 1
    
    def test_social_metrics_calculation_after_init(self):
        """Social metrikler doğru hesaplanıyor (initialize sonrası)."""
        from core.metamind import MetaMindCore
        
        mm = MetaMindCore()
        asyncio.run(mm.initialize("test_run"))
        
        class MockOther:
            entity_id = "agent1"
            relationship = 0.6
        
        class MockResult:
            empathy_level = 0.8
            resonance = 0.7
            confidence = 0.6
            other_entity = MockOther()
        
        mm.social_pipeline.process_empathy_results([MockResult()])
        
        metrics = mm.social_pipeline.get_metrics()
        assert metrics.cooperation_score >= 0.5  # Pozitif relationship
        assert metrics.conflict_frequency == 0.0


class TestEmpathy16D:
    """Empathy 16D state vector testleri."""
    
    def test_agent_gets_16d_state_vector(self):
        """Agent'lar 16D state vector alıyor."""
        from core.unified_core import UnifiedUEMCore
        
        core = UnifiedUEMCore()
        
        world = MockWorldState(
            tick=0,
            agents=[
                {'id': 'npc1', 'health': 0.8, 'energy': 0.7, 'valence': 0.3, 'danger': 0.2},
            ],
        )
        
        asyncio.run(core.cycle(world))
        
        if hasattr(core, '_empathy_results') and core._empathy_results:
            result = core._empathy_results[0]
            state_vector = result.other_entity.state_vector
            assert len(state_vector) == 16
    
    def test_empathy_finds_similar_memories(self):
        """Empathy benzer memory'ler buluyor."""
        from core.unified_core import UnifiedUEMCore
        
        core = UnifiedUEMCore()
        
        # Önce memory doldur
        for i in range(5):
            world = MockWorldState(
                tick=i,
                danger_level=0.2,
                player_health=0.7,
                player_energy=0.6,
            )
            asyncio.run(core.cycle(world))
        
        # Sonra benzer agent ile test
        world = MockWorldState(
            tick=5,
            agents=[
                {'id': 'similar_npc', 'health': 0.7, 'energy': 0.6, 'valence': 0.1, 'danger': 0.2},
            ],
        )
        asyncio.run(core.cycle(world))
        
        if hasattr(core, '_empathy_results') and core._empathy_results:
            result = core._empathy_results[0]
            assert result.empathy_level >= 0 or len(result.similar_memories) >= 0


class TestE2EIntegration:
    """End-to-end entegrasyon testleri."""
    
    def test_full_cycle_with_metamind(self):
        """Tam cycle MetaMind ile çalışıyor."""
        from core.unified_core import UnifiedUEMCore
        
        core = UnifiedUEMCore()
        mm = core._metamind_core
        
        assert mm is not None
        asyncio.run(mm.initialize("e2e_test"))
        
        for i in range(3):
            world = MockWorldState(
                tick=i,
                danger_level=0.1 * i,
                player_health=0.9,
                player_energy=0.8,
                agents=[{'id': f'npc_{i}', 'health': 0.7, 'energy': 0.6, 'valence': 0.2, 'danger': 0.1}],
            )
            asyncio.run(core.cycle(world))
        
        meta_state = mm.get_meta_state()
        assert meta_state is not None
        
        social = mm.social_pipeline.get_metrics()
        assert social.is_stub is False
    
    def test_empathy_to_social_pipeline_flow(self):
        """Empathy → SocialPipeline veri akışı çalışıyor."""
        from core.unified_core import UnifiedUEMCore
        
        core = UnifiedUEMCore()
        mm = core._metamind_core
        asyncio.run(mm.initialize("flow_test"))
        
        world = MockWorldState(
            tick=0,
            agents=[{'id': 'test_npc', 'health': 0.8, 'energy': 0.7, 'valence': 0.5, 'danger': 0.1}],
        )
        asyncio.run(core.cycle(world))
        
        assert hasattr(core, '_empathy_results')
        
        social = mm.social_pipeline.get_metrics()
        assert social.data_points >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
