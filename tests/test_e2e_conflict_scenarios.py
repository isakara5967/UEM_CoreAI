# tests/test_e2e_conflict_scenarios.py
"""
E2E Tests - Conflict Scenarios

Bu testler, ma_conflict_score hesaplamalarının farklı
ilişki ve goal_overlap kombinasyonlarında doğru çalıştığını doğrular.

Formül:
    relationship_conflict = (1 - resonance) × abs(min(0, relationship))
    goal_conflict = goal_overlap × (1 - 0.5 × resonance)
    conflict = 0.6 × relationship_conflict + 0.4 × goal_conflict

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
        
        def queue_result(self, empathy_level, resonance, confidence, relationship=0.0):
            self.results.append({
                'empathy_level': empathy_level,
                'resonance': resonance,
                'confidence': confidence,
                'relationship': relationship,
            })
        
        def compute(self, other_entity):
            if self.results:
                r = self.results.pop(0)
            else:
                r = {'empathy_level': 0.5, 'resonance': 0.5, 'confidence': 0.5, 'relationship': 0.0}
            
            # Override other_entity's relationship with queued value
            other_entity.relationship = r.get('relationship', other_entity.relationship)
            
            return EmpathyResult(
                empathy_level=r['empathy_level'],
                resonance=r['resonance'],
                confidence=r['confidence'],
                other_entity=other_entity,
            )
    
    return MockEmpathy()


# ============================================================================
# RELATIONSHIP-BASED CONFLICT TESTS
# ============================================================================

class TestRelationshipConflict:
    """Tests for relationship-based conflict component."""
    
    def test_e2e_conflict_positive_relation_zero(self, core, mock_empathy):
        """Pozitif ilişki → conflict_score ≈ 0."""
        mock_empathy.queue_result(
            empathy_level=0.7,
            resonance=0.6,
            confidence=0.7,
            relationship=0.8  # Very positive
        )
        core.empathy = mock_empathy
        
        world = E2EWorldState(agents=[
            {'id': 'best_friend', 'relation': 0.8, 'valence': 0.5}
        ])
        
        core.cycle_sync(world)
        
        # Positive relationship should not create conflict
        # relationship_conflict = (1-0.6) * abs(min(0, 0.8)) = 0.4 * 0 = 0
        assert core._current_predata['ma_conflict_score'] < 0.1
    
    def test_e2e_conflict_negative_relation_high(self, core, mock_empathy):
        """Negatif ilişki → yüksek conflict_score."""
        mock_empathy.queue_result(
            empathy_level=0.3,
            resonance=0.3,
            confidence=0.5,
            relationship=-0.8  # Very negative
        )
        core.empathy = mock_empathy
        
        world = E2EWorldState(agents=[
            {'id': 'arch_enemy', 'relation': -0.8, 'valence': -0.6}
        ])
        
        core.cycle_sync(world)
        
        # relationship_conflict = (1-0.3) * abs(min(0, -0.8)) = 0.7 * 0.8 = 0.56
        # total (with 0 goal_overlap) = 0.6 * 0.56 = 0.336
        assert core._current_predata['ma_conflict_score'] > 0.2
    
    def test_e2e_conflict_neutral_relation(self, core, mock_empathy):
        """Nötr ilişki → düşük conflict."""
        mock_empathy.queue_result(
            empathy_level=0.5,
            resonance=0.5,
            confidence=0.5,
            relationship=0.0  # Neutral
        )
        core.empathy = mock_empathy
        
        world = E2EWorldState(agents=[
            {'id': 'stranger', 'relation': 0.0, 'valence': 0.0}
        ])
        
        core.cycle_sync(world)
        
        # relationship_conflict = (1-0.5) * abs(min(0, 0)) = 0.5 * 0 = 0
        assert core._current_predata['ma_conflict_score'] < 0.15


# ============================================================================
# GOAL OVERLAP CONFLICT TESTS
# ============================================================================

class TestGoalOverlapConflict:
    """Tests for goal_overlap-based conflict component."""
    
    def test_e2e_conflict_same_action_overlap(self, core, mock_empathy):
        """Aynı aksiyon → goal_overlap=0.5 → conflict artışı."""
        mock_empathy.queue_result(
            empathy_level=0.5,
            resonance=0.5,
            confidence=0.5,
            relationship=0.0
        )
        core.empathy = mock_empathy
        
        # Not directly testable without Planner integration
        # This test verifies the formula with known values
        from core.predata.calculators import calculate_conflict_score
        
        # Same action → goal_overlap = 0.5
        conflict = calculate_conflict_score(
            resonance=0.5,
            relationship=0.0,
            goal_overlap=0.5  # Same action
        )
        
        # goal_conflict = 0.5 * (1 - 0.5 * 0.5) = 0.5 * 0.75 = 0.375
        # total = 0.4 * 0.375 = 0.15
        assert 0.1 < conflict < 0.2
    
    def test_e2e_conflict_shared_target_overlap(self, core, mock_empathy):
        """Paylaşılan hedef → goal_overlap=0.7 → daha yüksek conflict."""
        from core.predata.calculators import calculate_conflict_score
        
        # Shared target → goal_overlap = 0.7
        conflict = calculate_conflict_score(
            resonance=0.5,
            relationship=0.0,
            goal_overlap=0.7  # Shared target
        )
        
        # goal_conflict = 0.7 * (1 - 0.5 * 0.5) = 0.7 * 0.75 = 0.525
        # total = 0.4 * 0.525 = 0.21
        assert conflict > 0.2


# ============================================================================
# COMBINED CONFLICT TESTS
# ============================================================================

class TestCombinedConflict:
    """Tests for combined relationship + goal_overlap conflict."""
    
    def test_e2e_conflict_enemy_same_goal(self, core, mock_empathy):
        """Düşman + aynı hedef → maksimum conflict."""
        from core.predata.calculators import calculate_conflict_score
        
        conflict = calculate_conflict_score(
            resonance=0.2,  # Low resonance
            relationship=-0.9,  # Enemy
            goal_overlap=0.7  # Competing for same target
        )
        
        # relationship_conflict = (1-0.2) * 0.9 = 0.72
        # goal_conflict = 0.7 * (1 - 0.5 * 0.2) = 0.7 * 0.9 = 0.63
        # total = 0.6 * 0.72 + 0.4 * 0.63 = 0.432 + 0.252 = 0.684
        assert conflict > 0.6
    
    def test_e2e_conflict_resonance_reduces(self, core, mock_empathy):
        """Yüksek resonance conflict'i azaltmalı."""
        from core.predata.calculators import calculate_conflict_score
        
        # Low resonance
        conflict_low_res = calculate_conflict_score(
            resonance=0.2,
            relationship=-0.6,
            goal_overlap=0.5
        )
        
        # High resonance
        conflict_high_res = calculate_conflict_score(
            resonance=0.9,
            relationship=-0.6,
            goal_overlap=0.5
        )
        
        # High resonance should reduce conflict
        assert conflict_high_res < conflict_low_res


# ============================================================================
# AGGREGATION TESTS
# ============================================================================

class TestConflictAggregation:
    """Tests for multi-agent conflict aggregation (max strategy)."""
    
    def test_e2e_conflict_aggregation_max(self, core, mock_empathy):
        """Çoklu ajan → max(conflict_scores)."""
        # Agent 1: Low conflict (ally)
        mock_empathy.queue_result(
            empathy_level=0.8, resonance=0.8, confidence=0.8, relationship=0.7
        )
        # Agent 2: High conflict (enemy)
        mock_empathy.queue_result(
            empathy_level=0.2, resonance=0.2, confidence=0.5, relationship=-0.8
        )
        
        core.empathy = mock_empathy
        
        world = E2EWorldState(agents=[
            {'id': 'ally', 'relation': 0.7, 'valence': 0.3},
            {'id': 'enemy', 'relation': -0.8, 'valence': -0.5},
        ])
        
        core.cycle_sync(world)
        
        # Should take max (enemy's high conflict)
        assert core._current_predata['ma_conflict_score'] > 0.2
    
    def test_e2e_conflict_all_allies_low(self, core, mock_empathy):
        """Tüm ally'ler → düşük conflict."""
        mock_empathy.queue_result(empathy_level=0.8, resonance=0.7, confidence=0.8, relationship=0.6)
        mock_empathy.queue_result(empathy_level=0.7, resonance=0.8, confidence=0.7, relationship=0.7)
        mock_empathy.queue_result(empathy_level=0.9, resonance=0.9, confidence=0.9, relationship=0.8)
        
        core.empathy = mock_empathy
        
        world = E2EWorldState(agents=[
            {'id': 'ally_1', 'relation': 0.6, 'valence': 0.3},
            {'id': 'ally_2', 'relation': 0.7, 'valence': 0.4},
            {'id': 'ally_3', 'relation': 0.8, 'valence': 0.5},
        ])
        
        core.cycle_sync(world)
        
        # All allies → all low conflict → max is still low
        assert core._current_predata['ma_conflict_score'] < 0.15
