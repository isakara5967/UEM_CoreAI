# tests/test_predata_calculators.py
"""
PreData Calculators Birim Testleri

Bu testler, placeholder alanların gerçek hesaplamalarını doğrular.

Konsensüs: Claude (Opus 4.5) + Alice (GPT-5.1 Thinking)
Tarih: 30 Kasım 2025
"""

import pytest
from dataclasses import dataclass
from typing import Optional

# Test için mock import (gerçek projede relative import olacak)
import sys
# sys.path.insert(0, '/home/claude')
from core.predata.calculators import (
    calculate_empathy_score,
    calculate_empathy_score_from_result,
    calculate_conflict_score,
    calculate_conflict_score_from_result,
    estimate_goal_overlap,
    calculate_agent_count,
    calculate_coordination_mode,
    calculate_coordination_mode_single,
    aggregate_empathy_scores,
    aggregate_conflict_scores,
    aggregate_coordination_modes,
    calculate_all_multiagent_fields,
    COORDINATION_MODES,
)


# ============================================================================
# MOCK CLASSES
# ============================================================================

@dataclass
class MockOtherEntity:
    """Mock OtherEntity for testing."""
    entity_id: str = "test_entity"
    relationship: float = 0.0


@dataclass
class MockEmpathyResult:
    """Mock EmpathyResult for testing."""
    empathy_level: float = 0.5
    resonance: float = 0.5
    confidence: float = 0.5
    other_entity: Optional[MockOtherEntity] = None


# ============================================================================
# EMPATHY SCORE TESTS
# ============================================================================

class TestEmpathyScore:
    """Empathy score calculation tests."""
    
    def test_no_other_entity_returns_zero(self):
        """Başka varlık yoksa empati 0 olmalı."""
        score = calculate_empathy_score(
            empathy_level=0.8,
            resonance=0.7,
            confidence=0.9,
            has_other_entity=False
        )
        assert score == 0.0
    
    def test_weighted_formula(self):
        """Ağırlıklı formül doğru hesaplanmalı."""
        # 0.5 * 0.8 + 0.3 * 0.6 + 0.2 * 0.4 = 0.4 + 0.18 + 0.08 = 0.66
        score = calculate_empathy_score(
            empathy_level=0.8,
            resonance=0.6,
            confidence=0.4,
            has_other_entity=True
        )
        assert score == 0.66
    
    def test_clamp_upper_bound(self):
        """Skor 1.0'ı geçmemeli."""
        score = calculate_empathy_score(
            empathy_level=1.5,  # Invalid ama test için
            resonance=1.5,
            confidence=1.5,
            has_other_entity=True
        )
        assert score == 1.0
    
    def test_clamp_lower_bound(self):
        """Skor 0.0'ın altına düşmemeli."""
        score = calculate_empathy_score(
            empathy_level=-0.5,  # Invalid ama test için
            resonance=-0.5,
            confidence=-0.5,
            has_other_entity=True
        )
        assert score == 0.0
    
    def test_from_result_none(self):
        """Result None ise 0 döndürmeli."""
        score = calculate_empathy_score_from_result(None)
        assert score == 0.0
    
    def test_from_result_valid(self):
        """Valid result için doğru hesaplama."""
        result = MockEmpathyResult(
            empathy_level=0.8,
            resonance=0.6,
            confidence=0.4
        )
        score = calculate_empathy_score_from_result(result)
        assert score == 0.66
    
    def test_all_zeros(self):
        """Tüm değerler 0 ise skor 0 olmalı."""
        score = calculate_empathy_score(0.0, 0.0, 0.0, has_other_entity=True)
        assert score == 0.0
    
    def test_all_ones(self):
        """Tüm değerler 1 ise skor 1 olmalı."""
        score = calculate_empathy_score(1.0, 1.0, 1.0, has_other_entity=True)
        assert score == 1.0


# ============================================================================
# CONFLICT SCORE TESTS
# ============================================================================

class TestConflictScore:
    """Conflict score calculation tests."""
    
    def test_positive_relationship_no_conflict(self):
        """Pozitif ilişki çatışma skoru artırmamalı."""
        # relationship = +0.8 → relationship_conflict = 0
        score = calculate_conflict_score(
            resonance=0.5,
            relationship=0.8,
            goal_overlap=0.0
        )
        assert score == 0.0
    
    def test_negative_relationship_creates_conflict(self):
        """Negatif ilişki çatışma skorunu artırmalı."""
        # relationship_conflict = (1 - 0.5) * abs(min(0, -0.8)) = 0.5 * 0.8 = 0.4
        # goal_conflict = 0
        # total = 0.6 * 0.4 + 0.4 * 0 = 0.24
        score = calculate_conflict_score(
            resonance=0.5,
            relationship=-0.8,
            goal_overlap=0.0
        )
        assert score == 0.24
    
    def test_high_resonance_reduces_conflict(self):
        """Yüksek rezonans çatışmayı azaltmalı."""
        # relationship_conflict = (1 - 0.9) * 0.8 = 0.08
        # total = 0.6 * 0.08 = 0.048
        score = calculate_conflict_score(
            resonance=0.9,
            relationship=-0.8,
            goal_overlap=0.0
        )
        assert abs(score - 0.048) < 0.001
    
    def test_goal_overlap_adds_conflict(self):
        """Hedef çakışması çatışma eklemeli."""
        # relationship_conflict = 0 (positive rel)
        # goal_conflict = 0.8 * (1 - 0.5 * 0.5) = 0.8 * 0.75 = 0.6
        # total = 0.4 * 0.6 = 0.24
        score = calculate_conflict_score(
            resonance=0.5,
            relationship=0.5,  # Pozitif ilişki
            goal_overlap=0.8   # Yüksek hedef çakışması
        )
        assert score == 0.24
    
    def test_clamp_bounds(self):
        """Skor [0, 1] aralığında olmalı."""
        score = calculate_conflict_score(
            resonance=0.0,
            relationship=-1.0,
            goal_overlap=1.0
        )
        assert 0.0 <= score <= 1.0
    
    def test_from_result_none(self):
        """Result None ise 0 döndürmeli."""
        score = calculate_conflict_score_from_result(None)
        assert score == 0.0
    
    def test_from_result_valid(self):
        """Valid result için doğru hesaplama."""
        entity = MockOtherEntity(relationship=-0.8)
        result = MockEmpathyResult(
            resonance=0.5,
            other_entity=entity
        )
        score = calculate_conflict_score_from_result(result, goal_overlap=0.0)
        assert score == 0.24


# ============================================================================
# GOAL OVERLAP TESTS
# ============================================================================

class TestGoalOverlap:
    """Goal overlap estimation tests."""
    
    def test_placeholder_returns_zero(self):
        """V1.0: Placeholder olarak 0 döndürmeli."""
        overlap = estimate_goal_overlap()
        assert overlap == 0.0
    
    def test_with_parameters_still_zero(self):
        """V1.0: Parametrelerle bile 0 döndürmeli."""
        overlap = estimate_goal_overlap(
            my_action="eat",
            other_action="eat",
            shared_target="food"
        )
        assert overlap == 0.0


# ============================================================================
# AGENT COUNT TESTS
# ============================================================================

class TestAgentCount:
    """Agent count calculation tests."""
    
    def test_no_entities_returns_one(self):
        """Başka varlık yoksa sadece self = 1."""
        count = calculate_agent_count(None)
        assert count == 1
    
    def test_empty_list_returns_one(self):
        """Boş liste de 1 döndürmeli."""
        count = calculate_agent_count([])
        assert count == 1
    
    def test_one_entity(self):
        """Bir varlık varsa toplam 2."""
        count = calculate_agent_count(["entity1"])
        assert count == 2
    
    def test_multiple_entities(self):
        """Birden fazla varlık."""
        count = calculate_agent_count(["e1", "e2", "e3"])
        assert count == 4


# ============================================================================
# COORDINATION MODE TESTS
# ============================================================================

class TestCoordinationMode:
    """Coordination mode calculation tests."""
    
    def test_single_mode_no_entities(self):
        """Başka varlık yoksa 'single' modu."""
        mode = calculate_coordination_mode(None, None)
        assert mode == "single"
    
    def test_cooperative_high_relationship(self):
        """Yüksek pozitif ilişki → cooperative."""
        mode = calculate_coordination_mode_single(
            resonance=0.5,
            relationship=0.5
        )
        assert mode == "cooperative"
    
    def test_competitive_negative_relationship(self):
        """Negatif ilişki → competitive."""
        mode = calculate_coordination_mode_single(
            resonance=0.5,
            relationship=-0.5
        )
        assert mode == "competitive"
    
    def test_cooperative_high_resonance(self):
        """Nötr ilişki + yüksek rezonans → cooperative."""
        mode = calculate_coordination_mode_single(
            resonance=0.8,
            relationship=0.0
        )
        assert mode == "cooperative"
    
    def test_competitive_low_resonance(self):
        """Nötr ilişki + düşük rezonans → competitive."""
        mode = calculate_coordination_mode_single(
            resonance=0.2,
            relationship=0.0
        )
        assert mode == "competitive"
    
    def test_neutral_middle_values(self):
        """Orta değerler → neutral."""
        mode = calculate_coordination_mode_single(
            resonance=0.5,
            relationship=0.0
        )
        assert mode == "neutral"
    
    def test_mode_set_validity(self):
        """Tüm modlar geçerli mod setinde olmalı."""
        test_modes = ["single", "cooperative", "competitive", "neutral", "mixed"]
        for m in test_modes:
            assert m in COORDINATION_MODES


# ============================================================================
# AGGREGATION TESTS
# ============================================================================

class TestAggregation:
    """Multi-agent aggregation tests."""
    
    def test_aggregate_empathy_empty(self):
        """Boş liste için 0 döndürmeli."""
        score = aggregate_empathy_scores([])
        assert score == 0.0
    
    def test_aggregate_empathy_single(self):
        """Tek result için o result'ın skoru."""
        entity = MockOtherEntity(relationship=0.5)
        result = MockEmpathyResult(
            empathy_level=0.8,
            resonance=0.6,
            confidence=0.4,
            other_entity=entity
        )
        score = aggregate_empathy_scores([result])
        # Individual score = 0.66, weight = 0.5 * 0.4 = 0.2
        assert score == 0.66
    
    def test_aggregate_conflict_max(self):
        """Çatışma skorları için maksimum alınmalı."""
        entity1 = MockOtherEntity(relationship=-0.2)
        entity2 = MockOtherEntity(relationship=-0.8)
        
        result1 = MockEmpathyResult(resonance=0.5, other_entity=entity1)
        result2 = MockEmpathyResult(resonance=0.5, other_entity=entity2)
        
        score = aggregate_conflict_scores([result1, result2])
        # result2 daha yüksek conflict'e sahip olmalı
        individual_score2 = calculate_conflict_score_from_result(result2)
        assert score == individual_score2
    
    def test_aggregate_modes_same(self):
        """Aynı modlar → o mod."""
        modes = ["cooperative", "cooperative", "cooperative"]
        result = aggregate_coordination_modes(modes)
        assert result == "cooperative"
    
    def test_aggregate_modes_mixed(self):
        """Farklı modlar → mixed."""
        modes = ["cooperative", "competitive", "neutral"]
        result = aggregate_coordination_modes(modes)
        assert result == "mixed"
    
    def test_aggregate_modes_empty(self):
        """Boş liste → single."""
        result = aggregate_coordination_modes([])
        assert result == "single"


# ============================================================================
# UNIFIED CALCULATION TESTS
# ============================================================================

class TestUnifiedCalculation:
    """Unified calculate_all_multiagent_fields tests."""
    
    def test_no_entities(self):
        """Başka varlık yoksa default değerler."""
        result = calculate_all_multiagent_fields(None, None)
        assert result['empathy_score'] == 0.0
        assert result['ma_agent_count'] == 1
        assert result['ma_coordination_mode'] == 'single'
        assert result['ma_conflict_score'] == 0.0
    
    def test_single_entity(self):
        """Tek varlık için doğru hesaplama."""
        entity = MockOtherEntity(relationship=0.5)
        other = MockEmpathyResult(
            empathy_level=0.8,
            resonance=0.6,
            confidence=0.4,
            other_entity=entity
        )
        
        result = calculate_all_multiagent_fields(
            other_entities=[entity],
            empathy_results=[other]
        )
        
        assert result['ma_agent_count'] == 2
        assert result['empathy_score'] == 0.66
        assert result['ma_coordination_mode'] == 'cooperative'
        assert result['ma_conflict_score'] == 0.0  # Pozitif ilişki
    
    def test_multiple_entities(self):
        """Çoklu varlık için aggregation."""
        entity1 = MockOtherEntity(relationship=0.5)
        entity2 = MockOtherEntity(relationship=-0.5)
        
        result1 = MockEmpathyResult(
            empathy_level=0.8, resonance=0.7, confidence=0.6,
            other_entity=entity1
        )
        result2 = MockEmpathyResult(
            empathy_level=0.4, resonance=0.3, confidence=0.5,
            other_entity=entity2
        )
        
        result = calculate_all_multiagent_fields(
            other_entities=[entity1, entity2],
            empathy_results=[result1, result2]
        )
        
        assert result['ma_agent_count'] == 3
        assert result['ma_coordination_mode'] == 'mixed'  # cooperative + competitive
        assert result['ma_conflict_score'] > 0  # entity2 negatif ilişki


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Edge case tests."""
    
    def test_extreme_negative_relationship(self):
        """Çok düşük ilişki değeri."""
        score = calculate_conflict_score(
            resonance=0.0,
            relationship=-1.0,
            goal_overlap=0.0
        )
        # (1 - 0) * 1.0 = 1.0, total = 0.6 * 1.0 = 0.6
        assert score == 0.6
    
    def test_high_resonance_with_negative_relationship(self):
        """Negatif ilişki + yüksek rezonans (Alice'in örneği)."""
        # "Rakip kardeşler" senaryosu
        mode = calculate_coordination_mode_single(
            resonance=0.8,  # Yüksek duygusal uyum
            relationship=-0.5  # Ama rekabet ilişkisi
        )
        # İlişki öncelikli → competitive
        assert mode == "competitive"
    
    def test_zero_weight_aggregation(self):
        """Ağırlık 0 olduğunda hata vermemeli."""
        entity = MockOtherEntity(relationship=0.0)  # weight = 0
        result = MockEmpathyResult(
            empathy_level=0.5,
            resonance=0.5,
            confidence=0.0,  # weight = 0
            other_entity=entity
        )
        
        score = aggregate_empathy_scores([result])
        # Minimum ağırlık kullanılmalı, hata vermemeli
        assert score >= 0.0


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
