# tests/test_e2e_edge_cases.py
"""
E2E Tests - Edge Cases

Bu testler, sınır durumlarında sistemin
graceful degradation yapabildiğini doğrular.

Test edilenler:
- Boş/null değerler
- Ekstrem değerler
- Unicode karakterler
- Çok sayıda ajan
- Hızlı ardışık cycle'lar

Author: İsa Kara
Assisted by: 2 AI assistants
Date: 30 Kasım 2025
"""

import pytest
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


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
    agents: Optional[List[Dict]] = field(default_factory=list)
    objects: Optional[List[Dict]] = field(default_factory=list)
    events: Optional[List[str]] = field(default_factory=list)


@pytest.fixture
def core():
    """Create UnifiedUEMCore for E2E tests."""
    from core.unified_core import create_unified_core
    return create_unified_core(storage_type="memory")


@pytest.fixture
def mock_empathy():
    """Fast mock empathy for performance tests."""
    from core.empathy.empathy_orchestrator import EmpathyResult, OtherEntity
    
    class FastMockEmpathy:
        def compute(self, other_entity):
            return EmpathyResult(
                empathy_level=0.5,
                resonance=0.5,
                confidence=0.5,
                other_entity=other_entity,
            )
    
    return FastMockEmpathy()


# ============================================================================
# EMPTY/NULL VALUE TESTS
# ============================================================================

class TestEmptyNullValues:
    """Tests for empty and null value handling."""
    
    def test_e2e_edge_empty_world(self, core):
        """Boş world_state → crash yok."""
        world = E2EWorldState()
        
        result = core.cycle_sync(world)
        
        assert result is not None
        assert hasattr(result, 'action_name')
    
    def test_e2e_edge_null_agents(self, core):
        """agents=None → graceful handling."""
        world = E2EWorldState()
        world.agents = None
        
        result = core.cycle_sync(world)
        
        assert result is not None
        assert core._current_predata['ma_agent_count'] == 1
        assert core._current_predata['ma_coordination_mode'] == 'single'
    
    def test_e2e_edge_null_objects_events(self, core):
        """objects=None, events=None → graceful handling."""
        world = E2EWorldState()
        world.objects = None
        world.events = None
        
        result = core.cycle_sync(world)
        
        assert result is not None
    
    def test_e2e_edge_empty_agent_dict(self, core, mock_empathy):
        """Boş agent dict → handle edilmeli."""
        core.empathy = mock_empathy
        
        world = E2EWorldState(agents=[
            {},  # Empty dict
            {'id': 'valid', 'relation': 0.5}
        ])
        
        result = core.cycle_sync(world)
        
        assert result is not None


# ============================================================================
# EXTREME VALUE TESTS
# ============================================================================

class TestExtremeValues:
    """Tests for extreme value handling."""
    
    def test_e2e_edge_extreme_danger(self, core):
        """danger_level > 1.0 → clamp edilmeli."""
        world = E2EWorldState(danger_level=999.0)
        
        result = core.cycle_sync(world)
        
        assert result is not None
        # Emotion should reflect high danger
        assert core.current_emotion['arousal'] > 0.5
    
    def test_e2e_edge_negative_health(self, core):
        """player_health < 0 → handle edilmeli."""
        world = E2EWorldState(player_health=-0.5)
        
        result = core.cycle_sync(world)
        
        assert result is not None
    
    def test_e2e_edge_extreme_relation(self, core, mock_empathy):
        """relation dışı aralık → clamp edilmeli."""
        core.empathy = mock_empathy
        
        world = E2EWorldState(agents=[
            {'id': 'extreme', 'relation': 999.0, 'valence': -999.0}
        ])
        
        result = core.cycle_sync(world)
        
        assert result is not None
        # Should not crash, values should be clamped


# ============================================================================
# UNICODE AND SPECIAL CHARACTER TESTS
# ============================================================================

class TestUnicodeHandling:
    """Tests for unicode and special character handling."""
    
    def test_e2e_edge_unicode_agent_id(self, core, mock_empathy):
        """Unicode agent ID → handle edilmeli."""
        core.empathy = mock_empathy
        
        world = E2EWorldState(agents=[
            {'id': '日本語エージェント', 'relation': 0.5, 'valence': 0.0},
            {'id': 'агент_кириллица', 'relation': 0.3, 'valence': 0.1},
            {'id': 'emoji_agent_🤖', 'relation': 0.4, 'valence': 0.2},
        ])
        
        result = core.cycle_sync(world)
        
        assert result is not None
        assert core._current_predata['ma_agent_count'] == 4
    
    def test_e2e_edge_special_chars_event(self, core):
        """Special characters in events → handle edilmeli."""
        world = E2EWorldState(events=[
            'NORMAL_EVENT',
            'EVENT_WITH_UNICODE_日本語',
            'EVENT<with>XML&chars',
            "EVENT'with\"quotes"
        ])
        
        result = core.cycle_sync(world)
        
        assert result is not None


# ============================================================================
# PERFORMANCE EDGE CASES
# ============================================================================

class TestPerformanceEdgeCases:
    """Tests for performance edge cases."""
    
    def test_e2e_edge_many_agents(self, core, mock_empathy):
        """50 ajan → reasonable time içinde bitmeli."""
        core.empathy = mock_empathy
        
        agents = [
            {'id': f'agent_{i}', 'relation': (i % 10) / 10 - 0.5, 'valence': 0.0}
            for i in range(50)
        ]
        
        world = E2EWorldState(agents=agents)
        
        start = time.time()
        result = core.cycle_sync(world)
        elapsed = time.time() - start
        
        assert result is not None
        assert elapsed < 5.0  # Should complete in 5 seconds
        assert core._current_predata['ma_agent_count'] == 51
    
    def test_e2e_edge_rapid_cycles(self, core):
        """50 cycle hızlıca → stabil kalmalı."""
        results = []
        
        start = time.time()
        for i in range(50):
            world = E2EWorldState(tick=i, danger_level=0.1 * (i % 10))
            result = core.cycle_sync(world)
            results.append(result)
        elapsed = time.time() - start
        
        # All should complete
        assert len(results) == 50
        assert all(r is not None for r in results)
        
        # Should be reasonably fast (< 10 seconds for 50 cycles)
        assert elapsed < 10.0
    
    def test_e2e_edge_100_agents_no_crash(self, core, mock_empathy):
        """100 ajan → crash yok."""
        core.empathy = mock_empathy
        
        agents = [
            {'id': f'agent_{i}', 'relation': 0.0, 'valence': 0.0}
            for i in range(100)
        ]
        
        world = E2EWorldState(agents=agents)
        
        result = core.cycle_sync(world)
        
        assert result is not None
        assert core._current_predata['ma_agent_count'] == 101
