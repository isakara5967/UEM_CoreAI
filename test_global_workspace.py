"""
UEM Global Workspace Tests

pytest ile çalıştır:
    pytest test_global_workspace.py -v

Author: UEM Project
"""

import pytest
import asyncio
import sys
sys.path.insert(0, '.')

from core.consciousness.global_workspace import (
    WorkspaceManager,
    GlobalWorkspace,
    Coalition,
    BroadcastMessage,
    ContentType,
    Codelet,
    WorkspaceSubscriber,
    create_workspace_manager,
)
from core.integrated_uem_core import (
    IntegratedUEMCore,
    WorldState,
    ActionResult,
    create_uem_core,
)


# =========================================================================
# FIXTURES
# =========================================================================

@pytest.fixture
def workspace_manager():
    """Fresh WorkspaceManager"""
    return create_workspace_manager()


@pytest.fixture
async def uem_core():
    """Fresh IntegratedUEMCore"""
    core = await create_uem_core()
    yield core
    await core.stop()


# =========================================================================
# WORKSPACE TESTS
# =========================================================================

class TestWorkspaceManager:
    """WorkspaceManager testleri"""
    
    def test_creation(self, workspace_manager):
        """WorkspaceManager oluşturulabilmeli"""
        assert workspace_manager is not None
        assert workspace_manager.workspace is not None
        assert workspace_manager.attention is not None
    
    def test_default_codelets(self, workspace_manager):
        """6 default codelet kayıtlı olmalı"""
        stats = workspace_manager.get_stats()
        assert stats['workspace']['codelet_count'] == 6
    
    @pytest.mark.asyncio
    async def test_cycle_safe_context(self, workspace_manager):
        """Güvenli context'te broadcast olmayabilir"""
        context = {
            'perception': {'danger_level': 0.1, 'symbols': []},
            'emotion': {'arousal': 0.3, 'valence': 0.0},
            'agent_state': {'health': 0.9, 'energy': 0.8},
            'active_goals': [],
        }
        
        message = await workspace_manager.cycle(context)
        # Threshold altında kalabilir
        assert message is None or isinstance(message, BroadcastMessage)
    
    @pytest.mark.asyncio
    async def test_cycle_danger_context(self, workspace_manager):
        """Tehlikeli context'te URGENCY broadcast olmalı"""
        context = {
            'perception': {'danger_level': 0.8, 'symbols': ['ENEMY']},
            'emotion': {'arousal': 0.7, 'valence': -0.5},
            'agent_state': {'health': 0.5, 'energy': 0.6},
            'active_goals': [],
        }
        
        message = await workspace_manager.cycle(context)
        
        assert message is not None
        assert message.content_type == ContentType.URGENCY
    
    @pytest.mark.asyncio
    async def test_attention_goal(self, workspace_manager):
        """Attention goal ayarlanabilmeli"""
        workspace_manager.set_attention_goal(
            goal_type='test',
            target='goal',
            priority=0.8,
        )
        
        stats = workspace_manager.get_stats()
        assert stats['attention']['goals_count'] == 1


class TestGlobalWorkspace:
    """GlobalWorkspace testleri"""
    
    def test_codelet_registration(self):
        """Codelet kayıt edilebilmeli"""
        ws = GlobalWorkspace()
        
        class TestCodelet(Codelet):
            def run(self, context):
                return None
        
        ws.register_codelet(TestCodelet("test"))
        assert len(ws.codelets) == 1
    
    def test_subscriber_registration(self):
        """Subscriber kayıt edilebilmeli"""
        ws = GlobalWorkspace()
        
        class TestSubscriber(WorkspaceSubscriber):
            @property
            def subscriber_name(self):
                return "test"
            
            async def receive_broadcast(self, message):
                pass
        
        ws.register_subscriber(TestSubscriber())
        assert len(ws.subscribers) == 1
    
    @pytest.mark.asyncio
    async def test_competition(self):
        """Coalition competition çalışmalı"""
        ws = GlobalWorkspace(competition_threshold=0.3)
        
        # Manuel coalition ekle
        coalition = Coalition(
            id="test_1",
            content={'test': True},
            content_type=ContentType.PERCEPT,
            activation=0.8,
            salience=0.7,
            source="test",
        )
        ws.coalition_queue.append(coalition)
        
        # Cycle
        message = await ws.cycle({})
        
        assert message is not None
        assert message.coalition.id == "test_1"


# =========================================================================
# INTEGRATED CORE TESTS
# =========================================================================

class TestIntegratedUEMCore:
    """IntegratedUEMCore testleri"""
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Core start/stop çalışmalı"""
        core = IntegratedUEMCore()
        
        assert not core.started
        
        await core.start()
        assert core.started
        assert core.workspace_manager is not None
        
        await core.stop()
        assert not core.started
    
    @pytest.mark.asyncio
    async def test_cognitive_cycle(self, uem_core):
        """Cognitive cycle çalışmalı"""
        world_state = WorldState(
            tick=1,
            danger_level=0.3,
            player_health=0.8,
        )
        
        result = await uem_core.cognitive_cycle(world_state)
        
        assert isinstance(result, ActionResult)
        assert result.action_name in ['wait', 'explore', 'flee', 'approach', 'rest']
    
    @pytest.mark.asyncio
    async def test_danger_response(self, uem_core):
        """Tehlike durumunda flee seçilmeli"""
        world_state = WorldState(
            tick=1,
            danger_level=0.9,
            player_health=0.3,
        )
        
        result = await uem_core.cognitive_cycle(world_state)
        
        assert result.action_name == 'flee'
        assert result.conscious_content == 'urgency'
    
    @pytest.mark.asyncio
    async def test_emotion_update(self, uem_core):
        """Emotion state güncellenmeli"""
        initial_emotion = uem_core.current_emotion.copy()
        
        danger_state = WorldState(
            tick=1,
            danger_level=0.8,
        )
        
        await uem_core.cognitive_cycle(danger_state)
        
        # Danger → negative valence
        assert uem_core.current_emotion['valence'] < initial_emotion['valence']
    
    @pytest.mark.asyncio
    async def test_goal_setting(self, uem_core):
        """Goal eklenebilmeli"""
        uem_core.set_goal({
            'name': 'test_goal',
            'priority': 0.7,
        })
        
        assert len(uem_core.active_goals) == 1
        assert uem_core.active_goals[0]['name'] == 'test_goal'
    
    @pytest.mark.asyncio
    async def test_subscribers_receive_broadcast(self, uem_core):
        """Subscriber'lar broadcast almalı"""
        danger_state = WorldState(
            tick=1,
            danger_level=0.8,
        )
        
        await uem_core.cognitive_cycle(danger_state)
        
        # Memory subscriber broadcast almış olmalı
        assert len(uem_core.memory_subscriber.received_broadcasts) > 0
        
        # Self subscriber pattern kaydetmiş olmalı
        assert len(uem_core.self_subscriber.attention_patterns) > 0
    
    @pytest.mark.asyncio
    async def test_multi_cycle(self, uem_core):
        """Çoklu cycle çalışmalı"""
        states = [
            WorldState(tick=i, danger_level=0.1 * i)
            for i in range(1, 6)
        ]
        
        results = await uem_core.run_cycles(states)
        
        assert len(results) == 5
        assert uem_core.total_cycles == 5
    
    @pytest.mark.asyncio
    async def test_stats(self, uem_core):
        """Stats doğru dönmeli"""
        await uem_core.cognitive_cycle(WorldState(tick=1))
        
        stats = uem_core.get_stats()
        
        assert 'total_cycles' in stats
        assert 'workspace' in stats
        assert 'memory' in stats
        assert stats['total_cycles'] == 1


# =========================================================================
# CUSTOM CODELET TEST
# =========================================================================

class TestCustomCodelet:
    """Custom codelet testleri"""
    
    @pytest.mark.asyncio
    async def test_custom_codelet_integration(self):
        """Custom codelet entegre edilebilmeli"""
        
        class InsightCodelet(Codelet):
            def __init__(self):
                super().__init__("insight_test", priority=0.9)
            
            def run(self, context):
                symbols = context.get('perception', {}).get('symbols', [])
                if 'SPECIAL' in symbols:
                    return self._create_coalition(
                        content={'insight': 'Special detected!'},
                        content_type=ContentType.INSIGHT,
                        activation=0.9,
                        salience=0.9,
                    )
                return None
        
        core = await create_uem_core()
        core.workspace_manager.register_codelet(InsightCodelet())
        
        # SPECIAL symbol ile test
        state = WorldState(tick=1, symbols=['SPECIAL'])
        result = await core.cognitive_cycle(state)
        
        assert result.conscious_content == 'insight'
        
        await core.stop()


# =========================================================================
# SOMATIC MARKER TEST
# =========================================================================

class TestSomaticIntegration:
    """Somatic marker entegrasyon testleri"""
    
    @pytest.mark.asyncio
    async def test_somatic_learning(self, uem_core):
        """Somatic marker öğrenmeli"""
        # İlk cycle
        state1 = WorldState(tick=1, danger_level=0.8)
        await uem_core.cognitive_cycle(state1)
        
        # Marker oluşmuş olmalı
        assert len(uem_core.somatic_system.markers) > 0


# =========================================================================
# RUN TESTS
# =========================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
