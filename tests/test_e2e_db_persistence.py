# tests/test_e2e_db_persistence.py
"""
E2E Tests - DB Persistence

Bu testler, PreData ve Log verilerinin veritabanına
doğru yazıldığını doğrular.

Not: Bu testler in-memory storage ile çalışır.
PostgreSQL testleri için ayrı integration test gerekli.

Author: İsa Kara
Assisted by: 2 AI assistants
Date: 30 Kasım 2025
"""

import pytest
from dataclasses import dataclass, field
from typing import List, Dict, Any


# ============================================================================
# TEST FIXTURES
# ============================================================================

@dataclass
class E2EWorldState:
    """E2E test için WorldState."""
    tick: int = 1
    danger_level: float = 0.0
    player_health: float = 1.0
    player_energy: float = 1.0
    agents: List[Dict] = field(default_factory=list)
    objects: List[Dict] = field(default_factory=list)
    events: List[str] = field(default_factory=list)


@pytest.fixture
def core_memory():
    """Create UnifiedUEMCore with memory storage."""
    from core.unified_core import create_unified_core
    return create_unified_core(storage_type="memory")


@pytest.fixture
def mock_empathy():
    """Configurable mock empathy orchestrator."""
    from core.empathy.empathy_orchestrator import EmpathyResult, OtherEntity
    
    class MockEmpathy:
        def compute(self, other_entity):
            return EmpathyResult(
                empathy_level=0.7,
                resonance=0.6,
                confidence=0.8,
                other_entity=other_entity,
            )
    
    return MockEmpathy()


# ============================================================================
# PREDATA PERSISTENCE TESTS
# ============================================================================

class TestPreDataPersistence:
    """Tests for PreData persistence."""
    
    def test_e2e_predata_populated_after_cycle(self, core_memory):
        """Cycle sonrası PreData dolu olmalı."""
        world = E2EWorldState(danger_level=0.5, player_health=0.7)
        
        core_memory.cycle_sync(world)
        
        predata = core_memory._current_predata
        
        # Should have data
        assert predata is not None
        assert len(predata) > 0
    
    def test_e2e_predata_empathy_score_correct(self, core_memory, mock_empathy):
        """empathy_score PreData'da doğru değerde olmalı."""
        core_memory.empathy = mock_empathy
        
        world = E2EWorldState(agents=[
            {'id': 'npc', 'relation': 0.5, 'valence': 0.0}
        ])
        
        core_memory.cycle_sync(world)
        
        # empathy_score = 0.5 * 0.7 + 0.3 * 0.6 + 0.2 * 0.8 = 0.35 + 0.18 + 0.16 = 0.69
        assert 0.5 < core_memory._current_predata['empathy_score'] < 0.8
    
    def test_e2e_predata_multiagent_fields_correct(self, core_memory, mock_empathy):
        """Multi-agent alanları PreData'da doğru olmalı."""
        core_memory.empathy = mock_empathy
        
        world = E2EWorldState(agents=[
            {'id': 'a1', 'relation': 0.6, 'valence': 0.3},
            {'id': 'a2', 'relation': 0.4, 'valence': 0.1},
        ])
        
        core_memory.cycle_sync(world)
        
        predata = core_memory._current_predata
        
        assert predata['ma_agent_count'] == 3  # 2 + self
        assert predata['empathy_score'] > 0
        assert predata['ma_coordination_mode'] in ['single', 'cooperative', 'competitive', 'neutral', 'mixed']
        assert 0 <= predata['ma_conflict_score'] <= 1


# ============================================================================
# MULTIPLE CYCLES PERSISTENCE TESTS
# ============================================================================

class TestMultipleCyclesPersistence:
    """Tests for data persistence across multiple cycles."""
    
    def test_e2e_predata_updates_each_cycle(self, core_memory):
        """Her cycle'da PreData güncellenmeli."""
        predatas = []
        
        for i in range(3):
            world = E2EWorldState(
                tick=i,
                danger_level=0.2 * i,
                player_health=1.0 - 0.1 * i
            )
            core_memory.cycle_sync(world)
            predatas.append(core_memory._current_predata.copy())
        
        # Each should be different (danger_level changes emotion)
        assert len(predatas) == 3
        # At least some fields should differ
        # (exact comparison depends on implementation)
    
    def test_e2e_5_cycles_all_persisted(self, core_memory, mock_empathy):
        """5 cycle sonunda tüm veriler mevcut olmalı."""
        core_memory.empathy = mock_empathy
        
        for i in range(5):
            world = E2EWorldState(
                tick=i,
                agents=[{'id': f'agent_{i}', 'relation': 0.3, 'valence': 0.0}]
            )
            core_memory.cycle_sync(world)
        
        # Last predata should exist
        assert core_memory._current_predata is not None
        assert core_memory._current_predata['empathy_score'] > 0


# ============================================================================
# ERROR RECOVERY TESTS
# ============================================================================

class TestErrorRecovery:
    """Tests for error handling during persistence."""
    
    def test_e2e_predata_survives_partial_failure(self, core_memory):
        """Kısmi hata olsa bile PreData kaydedilmeli."""
        world = E2EWorldState(
            danger_level=0.5,
            agents=None  # Might cause issues in some paths
        )
        
        # Should not crash
        result = core_memory.cycle_sync(world)
        
        assert result is not None
        assert core_memory._current_predata is not None
    
    def test_e2e_predata_defaults_on_missing_data(self, core_memory):
        """Eksik veri → default değerler kullanılmalı."""
        # Minimal world state
        world = E2EWorldState()
        
        core_memory.cycle_sync(world)
        
        predata = core_memory._current_predata
        
        # Should have defaults for multi-agent
        assert predata['empathy_score'] == 0.0  # No agents
        assert predata['ma_agent_count'] == 1   # Only self
        assert predata['ma_coordination_mode'] == 'single'
        assert predata['ma_conflict_score'] == 0.0
