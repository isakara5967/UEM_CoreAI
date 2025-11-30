# tests/test_e2e_multiagent_modes.py
"""
E2E Tests - Multi-Agent Coordination Modes

Bu testler, farklı ajan konfigürasyonlarında coordination_mode'un
doğru hesaplandığını doğrular.

Modes:
- single: Ajan yok
- cooperative: İşbirliği (relation > 0.3 veya resonance > 0.7)
- competitive: Rekabet (relation < -0.3 veya resonance < 0.3)
- neutral: Nötr
- mixed: Karışık (çoklu ajanda farklı modlar)

Author: İsa Kara
Assisted by: 2 AI assistants
Date: 30 Kasım 2025
"""

import pytest
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from unittest.mock import MagicMock, patch


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
def mock_empathy_orchestrator():
    """Mock EmpathyOrchestrator that returns configurable results."""
    from core.empathy.empathy_orchestrator import EmpathyResult, OtherEntity
    
    class ConfigurableEmpathyOrchestrator:
        def __init__(self):
            self.results_queue = []
            self.default_result = None
        
        def set_results(self, results):
            """Set queue of results to return."""
            self.results_queue = list(results)
        
        def set_default(self, empathy_level=0.5, resonance=0.5, confidence=0.5):
            """Set default result."""
            self.default_result = {
                'empathy_level': empathy_level,
                'resonance': resonance,
                'confidence': confidence,
            }
        
        def compute(self, other_entity):
            if self.results_queue:
                r = self.results_queue.pop(0)
            elif self.default_result:
                r = self.default_result
            else:
                r = {'empathy_level': 0.5, 'resonance': 0.5, 'confidence': 0.5}
            
            return EmpathyResult(
                empathy_level=r.get('empathy_level', 0.5),
                resonance=r.get('resonance', 0.5),
                confidence=r.get('confidence', 0.5),
                other_entity=other_entity,
            )
    
    return ConfigurableEmpathyOrchestrator()


# ============================================================================
# SINGLE MODE TESTS
# ============================================================================

class TestSingleMode:
    """Tests for 'single' coordination mode (no other agents)."""
    
    def test_e2e_single_no_agents(self, core):
        """Ajan yoksa mode=single olmalı."""
        world = E2EWorldState(agents=[])
        
        result = core.cycle_sync(world)
        
        assert core._current_predata['ma_coordination_mode'] == 'single'
        assert core._current_predata['ma_agent_count'] == 1
        assert core._current_predata['empathy_score'] == 0.0
    
    def test_e2e_single_empty_agent_list(self, core):
        """Boş agents listesi → single."""
        world = E2EWorldState(agents=[])
        
        core.cycle_sync(world)
        
        assert core._current_predata['ma_coordination_mode'] == 'single'
    
    def test_e2e_single_null_agents(self, core):
        """agents=None → single."""
        world = E2EWorldState()
        world.agents = None
        
        # Should not crash
        result = core.cycle_sync(world)
        
        assert result is not None
        assert core._current_predata['ma_coordination_mode'] == 'single'


# ============================================================================
# COOPERATIVE MODE TESTS
# ============================================================================

class TestCooperativeMode:
    """Tests for 'cooperative' coordination mode."""
    
    def test_e2e_cooperative_high_relation(self, core, mock_empathy_orchestrator):
        """relation > 0.3 → cooperative."""
        mock_empathy_orchestrator.set_default(
            empathy_level=0.6,
            resonance=0.5,
            confidence=0.7
        )
        core.empathy = mock_empathy_orchestrator
        
        world = E2EWorldState(agents=[
            {'id': 'ally_001', 'relation': 0.8, 'valence': 0.3}
        ])
        
        core.cycle_sync(world)
        
        assert core._current_predata['ma_coordination_mode'] == 'cooperative'
        assert core._current_predata['ma_agent_count'] == 2
    
    def test_e2e_cooperative_high_resonance(self, core, mock_empathy_orchestrator):
        """resonance > 0.7 → cooperative (relation nötr olsa bile)."""
        mock_empathy_orchestrator.set_default(
            empathy_level=0.8,
            resonance=0.85,  # High resonance
            confidence=0.6
        )
        core.empathy = mock_empathy_orchestrator
        
        world = E2EWorldState(agents=[
            {'id': 'stranger', 'relation': 0.0, 'valence': 0.5}  # Neutral relation
        ])
        
        core.cycle_sync(world)
        
        assert core._current_predata['ma_coordination_mode'] == 'cooperative'
    
    def test_e2e_cooperative_multiple_allies(self, core, mock_empathy_orchestrator):
        """Birden fazla ally → cooperative."""
        mock_empathy_orchestrator.set_default(
            empathy_level=0.7,
            resonance=0.6,
            confidence=0.8
        )
        core.empathy = mock_empathy_orchestrator
        
        world = E2EWorldState(agents=[
            {'id': 'ally_001', 'relation': 0.7, 'valence': 0.2},
            {'id': 'ally_002', 'relation': 0.6, 'valence': 0.3},
            {'id': 'ally_003', 'relation': 0.8, 'valence': 0.1},
        ])
        
        core.cycle_sync(world)
        
        assert core._current_predata['ma_coordination_mode'] == 'cooperative'
        assert core._current_predata['ma_agent_count'] == 4  # 3 + self


# ============================================================================
# COMPETITIVE MODE TESTS
# ============================================================================

class TestCompetitiveMode:
    """Tests for 'competitive' coordination mode."""
    
    def test_e2e_competitive_negative_relation(self, core, mock_empathy_orchestrator):
        """relation < -0.3 → competitive."""
        mock_empathy_orchestrator.set_default(
            empathy_level=0.3,
            resonance=0.4,
            confidence=0.5
        )
        core.empathy = mock_empathy_orchestrator
        
        world = E2EWorldState(agents=[
            {'id': 'enemy_001', 'relation': -0.7, 'valence': -0.5}
        ])
        
        core.cycle_sync(world)
        
        assert core._current_predata['ma_coordination_mode'] == 'competitive'
    
    def test_e2e_competitive_low_resonance(self, core, mock_empathy_orchestrator):
        """resonance < 0.3 → competitive."""
        mock_empathy_orchestrator.set_default(
            empathy_level=0.2,
            resonance=0.15,  # Very low
            confidence=0.4
        )
        core.empathy = mock_empathy_orchestrator
        
        world = E2EWorldState(agents=[
            {'id': 'stranger', 'relation': 0.0, 'valence': -0.8}
        ])
        
        core.cycle_sync(world)
        
        assert core._current_predata['ma_coordination_mode'] == 'competitive'
    
    def test_e2e_competitive_multiple_enemies(self, core, mock_empathy_orchestrator):
        """Birden fazla düşman → competitive."""
        mock_empathy_orchestrator.set_default(
            empathy_level=0.2,
            resonance=0.25,
            confidence=0.6
        )
        core.empathy = mock_empathy_orchestrator
        
        world = E2EWorldState(agents=[
            {'id': 'enemy_001', 'relation': -0.6, 'valence': -0.3},
            {'id': 'enemy_002', 'relation': -0.8, 'valence': -0.5},
        ])
        
        core.cycle_sync(world)
        
        assert core._current_predata['ma_coordination_mode'] == 'competitive'


# ============================================================================
# NEUTRAL MODE TESTS
# ============================================================================

class TestNeutralMode:
    """Tests for 'neutral' coordination mode."""
    
    def test_e2e_neutral_zero_relation(self, core, mock_empathy_orchestrator):
        """relation=0, resonance orta → neutral."""
        mock_empathy_orchestrator.set_default(
            empathy_level=0.5,
            resonance=0.5,
            confidence=0.5
        )
        core.empathy = mock_empathy_orchestrator
        
        world = E2EWorldState(agents=[
            {'id': 'stranger', 'relation': 0.0, 'valence': 0.0}
        ])
        
        core.cycle_sync(world)
        
        assert core._current_predata['ma_coordination_mode'] == 'neutral'
    
    def test_e2e_neutral_mid_range_values(self, core, mock_empathy_orchestrator):
        """Orta değerler → neutral."""
        mock_empathy_orchestrator.set_default(
            empathy_level=0.5,
            resonance=0.5,  # Not high enough for cooperative
            confidence=0.5
        )
        core.empathy = mock_empathy_orchestrator
        
        world = E2EWorldState(agents=[
            {'id': 'passerby', 'relation': 0.1, 'valence': 0.0}  # Slightly positive but not enough
        ])
        
        core.cycle_sync(world)
        
        assert core._current_predata['ma_coordination_mode'] == 'neutral'


# ============================================================================
# MIXED MODE TESTS
# ============================================================================

class TestMixedMode:
    """Tests for 'mixed' coordination mode (multiple agents with different modes)."""
    
    def test_e2e_mixed_ally_and_enemy(self, core, mock_empathy_orchestrator):
        """Bir ally + bir enemy → mixed."""
        # First agent: cooperative (high relation)
        # Second agent: competitive (low relation)
        mock_empathy_orchestrator.set_results([
            {'empathy_level': 0.8, 'resonance': 0.7, 'confidence': 0.8},  # Ally
            {'empathy_level': 0.2, 'resonance': 0.2, 'confidence': 0.6},  # Enemy
        ])
        core.empathy = mock_empathy_orchestrator
        
        world = E2EWorldState(agents=[
            {'id': 'ally', 'relation': 0.8, 'valence': 0.5},
            {'id': 'enemy', 'relation': -0.7, 'valence': -0.5},
        ])
        
        core.cycle_sync(world)
        
        assert core._current_predata['ma_coordination_mode'] == 'mixed'
        assert core._current_predata['ma_agent_count'] == 3
    
    def test_e2e_mixed_three_different_agents(self, core, mock_empathy_orchestrator):
        """Üç farklı tip ajan → mixed."""
        mock_empathy_orchestrator.set_results([
            {'empathy_level': 0.9, 'resonance': 0.8, 'confidence': 0.9},  # Cooperative
            {'empathy_level': 0.5, 'resonance': 0.5, 'confidence': 0.5},  # Neutral
            {'empathy_level': 0.1, 'resonance': 0.1, 'confidence': 0.4},  # Competitive
        ])
        core.empathy = mock_empathy_orchestrator
        
        world = E2EWorldState(agents=[
            {'id': 'ally', 'relation': 0.9, 'valence': 0.6},
            {'id': 'stranger', 'relation': 0.0, 'valence': 0.0},
            {'id': 'enemy', 'relation': -0.8, 'valence': -0.7},
        ])
        
        core.cycle_sync(world)
        
        assert core._current_predata['ma_coordination_mode'] == 'mixed'
    
    def test_e2e_mixed_cooperative_and_neutral(self, core, mock_empathy_orchestrator):
        """Cooperative + Neutral → mixed."""
        mock_empathy_orchestrator.set_results([
            {'empathy_level': 0.8, 'resonance': 0.75, 'confidence': 0.8},  # Cooperative
            {'empathy_level': 0.5, 'resonance': 0.5, 'confidence': 0.5},   # Neutral
        ])
        core.empathy = mock_empathy_orchestrator
        
        world = E2EWorldState(agents=[
            {'id': 'ally', 'relation': 0.7, 'valence': 0.4},
            {'id': 'stranger', 'relation': 0.1, 'valence': 0.0},
        ])
        
        core.cycle_sync(world)
        
        assert core._current_predata['ma_coordination_mode'] == 'mixed'


# ============================================================================
# MODE TRANSITION TEST
# ============================================================================

class TestModeTransition:
    """Tests for mode changes across cycles."""
    
    def test_e2e_mode_transition_single_to_cooperative(self, core, mock_empathy_orchestrator):
        """single → cooperative geçişi."""
        mock_empathy_orchestrator.set_default(
            empathy_level=0.7,
            resonance=0.6,
            confidence=0.7
        )
        core.empathy = mock_empathy_orchestrator
        
        # Cycle 1: No agents
        world1 = E2EWorldState(tick=1, agents=[])
        core.cycle_sync(world1)
        mode1 = core._current_predata['ma_coordination_mode']
        
        # Cycle 2: Ally appears
        world2 = E2EWorldState(tick=2, agents=[
            {'id': 'new_ally', 'relation': 0.8, 'valence': 0.5}
        ])
        core.cycle_sync(world2)
        mode2 = core._current_predata['ma_coordination_mode']
        
        assert mode1 == 'single'
        assert mode2 == 'cooperative'
    
    def test_e2e_mode_transition_cooperative_to_competitive(self, core, mock_empathy_orchestrator):
        """cooperative → competitive geçişi (ilişki bozuldu)."""
        core.empathy = mock_empathy_orchestrator
        
        # Cycle 1: Ally
        mock_empathy_orchestrator.set_default(empathy_level=0.8, resonance=0.7, confidence=0.8)
        world1 = E2EWorldState(tick=1, agents=[
            {'id': 'agent_001', 'relation': 0.8, 'valence': 0.5}
        ])
        core.cycle_sync(world1)
        mode1 = core._current_predata['ma_coordination_mode']
        
        # Cycle 2: Same agent but now enemy (betrayal!)
        mock_empathy_orchestrator.set_default(empathy_level=0.2, resonance=0.2, confidence=0.6)
        world2 = E2EWorldState(tick=2, agents=[
            {'id': 'agent_001', 'relation': -0.8, 'valence': -0.6}  # Betrayed!
        ])
        core.cycle_sync(world2)
        mode2 = core._current_predata['ma_coordination_mode']
        
        assert mode1 == 'cooperative'
        assert mode2 == 'competitive'
