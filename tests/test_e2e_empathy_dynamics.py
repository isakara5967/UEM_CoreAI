# tests/test_e2e_empathy_dynamics.py
"""
E2E Tests - Empathy Dynamics

Bu testler, empati hesaplamalarının farklı senaryolarda
doğru çalıştığını doğrular.

Test edilenler:
- empathy_level hesaplama
- resonance hesaplama
- confidence hesaplama
- Çoklu ajan aggregation
- Empati → Planning akışı

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
def core():
    """Create UnifiedUEMCore for E2E tests."""
    from core.unified_core import create_unified_core
    return create_unified_core(storage_type="memory")


@pytest.fixture
def mock_empathy():
    """Configurable mock empathy orchestrator."""
    from core.empathy.empathy_orchestrator import EmpathyResult, OtherEntity
    
    class MockEmpathy:
        def __init__(self):
            self.results = []
            self.call_count = 0
        
        def queue_result(self, empathy_level, resonance, confidence):
            self.results.append({
                'empathy_level': empathy_level,
                'resonance': resonance,
                'confidence': confidence,
            })
        
        def compute(self, other_entity):
            self.call_count += 1
            if self.results:
                r = self.results.pop(0)
            else:
                r = {'empathy_level': 0.5, 'resonance': 0.5, 'confidence': 0.5}
            
            return EmpathyResult(
                empathy_level=r['empathy_level'],
                resonance=r['resonance'],
                confidence=r['confidence'],
                other_entity=other_entity,
            )
    
    return MockEmpathy()


# ============================================================================
# HIGH/LOW EMPATHY TESTS
# ============================================================================

class TestEmpathyLevels:
    """Tests for empathy_level calculation."""
    
    def test_e2e_high_empathy_similar_experience(self, core, mock_empathy):
        """Benzer deneyim → yüksek empati."""
        mock_empathy.queue_result(
            empathy_level=0.85,
            resonance=0.8,
            confidence=0.9
        )
        core.empathy = mock_empathy
        
        world = E2EWorldState(agents=[
            {'id': 'suffering_npc', 'relation': 0.3, 'valence': -0.7}
        ])
        
        core.cycle_sync(world)
        
        # empathy_score = 0.5 * 0.85 + 0.3 * 0.8 + 0.2 * 0.9 = 0.425 + 0.24 + 0.18 = 0.845
        assert core._current_predata['empathy_score'] > 0.7
    
    def test_e2e_low_empathy_unfamiliar_state(self, core, mock_empathy):
        """Tanımadık durum → düşük empati."""
        mock_empathy.queue_result(
            empathy_level=0.15,
            resonance=0.3,
            confidence=0.2
        )
        core.empathy = mock_empathy
        
        world = E2EWorldState(agents=[
            {'id': 'alien_entity', 'relation': 0.0, 'valence': 0.0}
        ])
        
        core.cycle_sync(world)
        
        assert core._current_predata['empathy_score'] < 0.3
    
    def test_e2e_zero_empathy_no_agents(self, core):
        """Ajan yoksa empathy_score = 0."""
        world = E2EWorldState(agents=[])
        
        core.cycle_sync(world)
        
        assert core._current_predata['empathy_score'] == 0.0


# ============================================================================
# RESONANCE TESTS
# ============================================================================

class TestResonance:
    """Tests for emotional resonance calculation."""
    
    def test_e2e_high_resonance_same_valence(self, core, mock_empathy):
        """Aynı duygu durumu → yüksek resonance."""
        mock_empathy.queue_result(
            empathy_level=0.6,
            resonance=0.95,  # Almost perfect resonance
            confidence=0.7
        )
        core.empathy = mock_empathy
        
        # Self is in fear, other is also in fear
        world = E2EWorldState(
            danger_level=0.8,  # Self is afraid
            agents=[
                {'id': 'fellow_scared', 'relation': 0.2, 'valence': -0.7}  # Also scared
            ]
        )
        
        core.cycle_sync(world)
        
        # Check resonance contributes to empathy_score
        assert core._current_predata['empathy_score'] > 0.5
    
    def test_e2e_low_resonance_opposite_valence(self, core, mock_empathy):
        """Zıt duygu durumu → düşük resonance."""
        mock_empathy.queue_result(
            empathy_level=0.5,
            resonance=0.1,  # Very low - opposite emotions
            confidence=0.6
        )
        core.empathy = mock_empathy
        
        # Self is happy, other is angry
        world = E2EWorldState(
            danger_level=0.0,
            player_health=1.0,
            agents=[
                {'id': 'angry_npc', 'relation': -0.2, 'valence': -0.9}
            ]
        )
        
        core.cycle_sync(world)
        
        # Low resonance should reduce empathy_score
        assert core._current_predata['empathy_score'] < 0.5


# ============================================================================
# CONFIDENCE TESTS
# ============================================================================

class TestConfidence:
    """Tests for empathy confidence calculation."""
    
    def test_e2e_high_confidence_many_memories(self, core, mock_empathy):
        """Çok deneyim → yüksek confidence."""
        mock_empathy.queue_result(
            empathy_level=0.7,
            resonance=0.6,
            confidence=0.95  # Very confident (many similar experiences)
        )
        core.empathy = mock_empathy
        
        world = E2EWorldState(agents=[
            {'id': 'familiar_situation', 'relation': 0.4, 'valence': -0.3}
        ])
        
        core.cycle_sync(world)
        
        assert core._current_predata['empathy_score'] > 0.6
    
    def test_e2e_low_confidence_first_encounter(self, core, mock_empathy):
        """İlk karşılaşma → düşük confidence."""
        mock_empathy.queue_result(
            empathy_level=0.5,
            resonance=0.5,
            confidence=0.05  # Very low - no prior experience
        )
        core.empathy = mock_empathy
        
        world = E2EWorldState(agents=[
            {'id': 'never_seen_before', 'relation': 0.0, 'valence': 0.0}
        ])
        
        core.cycle_sync(world)
        
        # Low confidence should reduce overall empathy_score
        assert core._current_predata['empathy_score'] < 0.5


# ============================================================================
# AGGREGATION TESTS
# ============================================================================

class TestEmpathyAggregation:
    """Tests for multi-agent empathy aggregation."""
    
    def test_e2e_aggregation_weighted_average(self, core, mock_empathy):
        """Çoklu ajan → ağırlıklı ortalama."""
        # Agent 1: High empathy, high relationship weight
        mock_empathy.queue_result(empathy_level=0.9, resonance=0.8, confidence=0.9)
        # Agent 2: Low empathy, low relationship weight
        mock_empathy.queue_result(empathy_level=0.2, resonance=0.3, confidence=0.4)
        
        core.empathy = mock_empathy
        
        world = E2EWorldState(agents=[
            {'id': 'close_friend', 'relation': 0.9, 'valence': 0.5},   # High weight
            {'id': 'acquaintance', 'relation': 0.1, 'valence': 0.0},  # Low weight
        ])
        
        core.cycle_sync(world)
        
        # Weighted toward high empathy agent
        assert core._current_predata['empathy_score'] > 0.5
    
    def test_e2e_aggregation_three_agents(self, core, mock_empathy):
        """Üç ajan aggregation."""
        mock_empathy.queue_result(empathy_level=0.8, resonance=0.7, confidence=0.8)
        mock_empathy.queue_result(empathy_level=0.5, resonance=0.5, confidence=0.5)
        mock_empathy.queue_result(empathy_level=0.3, resonance=0.4, confidence=0.6)
        
        core.empathy = mock_empathy
        
        world = E2EWorldState(agents=[
            {'id': 'agent_1', 'relation': 0.6, 'valence': 0.3},
            {'id': 'agent_2', 'relation': 0.3, 'valence': 0.0},
            {'id': 'agent_3', 'relation': 0.4, 'valence': -0.2},
        ])
        
        core.cycle_sync(world)
        
        # Should be somewhere in the middle
        score = core._current_predata['empathy_score']
        assert 0.3 < score < 0.8
        assert core._current_predata['ma_agent_count'] == 4


# ============================================================================
# EMPATHY FLOW TESTS
# ============================================================================

class TestEmpathyFlow:
    """Tests for empathy data flow through the system."""
    
    def test_e2e_empathy_updates_each_cycle(self, core, mock_empathy):
        """Her cycle'da empathy güncellenmeli."""
        core.empathy = mock_empathy
        
        scores = []
        
        # Cycle 1: High empathy
        mock_empathy.queue_result(empathy_level=0.9, resonance=0.8, confidence=0.9)
        world1 = E2EWorldState(tick=1, agents=[{'id': 'a1', 'relation': 0.5, 'valence': 0.0}])
        core.cycle_sync(world1)
        scores.append(core._current_predata['empathy_score'])
        
        # Cycle 2: Medium empathy
        mock_empathy.queue_result(empathy_level=0.5, resonance=0.5, confidence=0.5)
        world2 = E2EWorldState(tick=2, agents=[{'id': 'a2', 'relation': 0.3, 'valence': 0.0}])
        core.cycle_sync(world2)
        scores.append(core._current_predata['empathy_score'])
        
        # Cycle 3: Low empathy
        mock_empathy.queue_result(empathy_level=0.2, resonance=0.3, confidence=0.4)
        world3 = E2EWorldState(tick=3, agents=[{'id': 'a3', 'relation': 0.1, 'valence': 0.0}])
        core.cycle_sync(world3)
        scores.append(core._current_predata['empathy_score'])
        
        # All scores should be different
        assert scores[0] > scores[1] > scores[2]
    
    def test_e2e_empathy_persists_to_planning(self, core, mock_empathy):
        """Empathy sonucu Planning'e ulaşmalı."""
        mock_empathy.queue_result(empathy_level=0.8, resonance=0.7, confidence=0.8)
        core.empathy = mock_empathy
        
        world = E2EWorldState(agents=[
            {'id': 'distressed_npc', 'relation': 0.5, 'valence': -0.8}
        ])
        
        result = core.cycle_sync(world)
        
        # Empathy result should have been passed to planning
        assert len(core._empathy_results) > 0
        assert core._empathy_results[0].empathy_level == 0.8
    
    def test_e2e_empathy_affects_action_selection(self, core, mock_empathy):
        """Yüksek empati → help action daha olası."""
        # This tests the flow, not the actual planning decision
        mock_empathy.queue_result(empathy_level=0.95, resonance=0.9, confidence=0.9)
        core.empathy = mock_empathy
        
        world = E2EWorldState(
            danger_level=0.2,  # Low danger
            agents=[
                {'id': 'hurt_npc', 'relation': 0.6, 'valence': -0.9}  # Clearly in distress
            ]
        )
        
        result = core.cycle_sync(world)
        
        # At minimum, empathy data should be captured
        assert core._current_predata['empathy_score'] > 0.8
        # Action should be returned (actual action depends on planner)
        assert result is not None
        assert hasattr(result, 'action_name')
