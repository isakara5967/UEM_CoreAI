# tests/test_empathy_integration.py
"""
Empathy → unified_core.py Entegrasyon Testleri

Bu testler, _phase_empathy metodunun çoklu ajan desteğini doğrular.

Author: İsa Kara
Assisted by: 2 AI assistants
Date: 30 Kasım 2025
"""

import pytest
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from unittest.mock import MagicMock, patch


# ============================================================================
# MOCK CLASSES
# ============================================================================

@dataclass
class MockWorldState:
    """Mock WorldState for testing."""
    tick: int = 1
    danger_level: float = 0.0
    player_health: float = 1.0
    player_energy: float = 1.0
    agents: List[Dict] = None
    
    def __post_init__(self):
        if self.agents is None:
            self.agents = []


@dataclass
class MockEmpathyResult:
    """Mock EmpathyResult for testing."""
    empathy_level: float = 0.5
    resonance: float = 0.5
    confidence: float = 0.5
    other_entity: Any = None


class MockEmpathyOrchestrator:
    """Mock EmpathyOrchestrator for testing."""
    
    def __init__(self):
        self.compute_calls = []
    
    def compute(self, other_entity):
        self.compute_calls.append(other_entity)
        return MockEmpathyResult(
            empathy_level=0.6,
            resonance=0.7,
            confidence=0.8,
            other_entity=other_entity,
        )


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def world_state_no_agents():
    """WorldState with no agents."""
    return MockWorldState(agents=[])


@pytest.fixture
def world_state_single_agent():
    """WorldState with single agent."""
    return MockWorldState(agents=[
        {'id': 'npc_001', 'valence': -0.5, 'relation': 0.3}
    ])


@pytest.fixture
def world_state_multi_agents():
    """WorldState with multiple agents."""
    return MockWorldState(agents=[
        {'id': 'npc_001', 'valence': -0.5, 'relation': 0.3},
        {'id': 'npc_002', 'valence': 0.2, 'relation': -0.4},
        {'id': 'player_001', 'valence': 0.0, 'relation': 0.8},
    ])


# ============================================================================
# TESTS: _empathy_results Population
# ============================================================================

class TestEmpathyResultsPopulation:
    """Tests for _empathy_results list population."""
    
    def test_no_agents_empty_results(self, world_state_no_agents):
        """Ajan yoksa _empathy_results boş olmalı."""
        from core.unified_core import create_unified_core
        
        core = create_unified_core(storage_type="memory")
        core._phase_empathy(None, world_state_no_agents)
        
        assert hasattr(core, '_empathy_results')
        assert core._empathy_results == []
    
    def test_single_agent_one_result(self, world_state_single_agent):
        """Tek ajan için tek sonuç olmalı."""
        from core.unified_core import create_unified_core
        
        core = create_unified_core(storage_type="memory")
        
        # Mock empathy orchestrator
        mock_empathy = MockEmpathyOrchestrator()
        core.empathy = mock_empathy
        
        result = core._phase_empathy(None, world_state_single_agent)
        
        assert len(core._empathy_results) == 1
        assert len(mock_empathy.compute_calls) == 1
        assert mock_empathy.compute_calls[0].entity_id == 'npc_001'
    
    def test_multi_agents_all_processed(self, world_state_multi_agents):
        """Çoklu ajanlar için tümü işlenmeli."""
        from core.unified_core import create_unified_core
        
        core = create_unified_core(storage_type="memory")
        
        # Mock empathy orchestrator
        mock_empathy = MockEmpathyOrchestrator()
        core.empathy = mock_empathy
        
        result = core._phase_empathy(None, world_state_multi_agents)
        
        assert len(core._empathy_results) == 3
        assert len(mock_empathy.compute_calls) == 3
        
        # Check all agent IDs
        processed_ids = [call.entity_id for call in mock_empathy.compute_calls]
        assert 'npc_001' in processed_ids
        assert 'npc_002' in processed_ids
        assert 'player_001' in processed_ids
    
    def test_empathy_results_reset_each_cycle(self, world_state_single_agent):
        """Her cycle'da _empathy_results sıfırlanmalı."""
        from core.unified_core import create_unified_core
        
        core = create_unified_core(storage_type="memory")
        
        # Mock empathy orchestrator
        mock_empathy = MockEmpathyOrchestrator()
        core.empathy = mock_empathy
        
        # First call
        core._phase_empathy(None, world_state_single_agent)
        assert len(core._empathy_results) == 1
        
        # Second call - should reset
        core._phase_empathy(None, world_state_single_agent)
        assert len(core._empathy_results) == 1  # Still 1, not 2
    
    def test_backward_compatibility_returns_first(self, world_state_multi_agents):
        """Backward compatibility: İlk sonuç döndürülmeli."""
        from core.unified_core import create_unified_core
        
        core = create_unified_core(storage_type="memory")
        
        # Mock empathy orchestrator
        mock_empathy = MockEmpathyOrchestrator()
        core.empathy = mock_empathy
        
        result = core._phase_empathy(None, world_state_multi_agents)
        
        # Should return first result (not None, not list)
        assert result is not None
        assert hasattr(result, 'empathy_level')


# ============================================================================
# TESTS: Integration with calculate_all_multiagent_fields
# ============================================================================

class TestMultiAgentFieldsIntegration:
    """Tests for integration with calculators."""
    
    def test_empathy_results_used_in_calculation(self, world_state_multi_agents):
        """_empathy_results, calculate_all_multiagent_fields'a geçmeli."""
        from core.unified_core import create_unified_core
        from core.predata.calculators import calculate_all_multiagent_fields
        
        core = create_unified_core(storage_type="memory")
        
        # Mock empathy orchestrator
        mock_empathy = MockEmpathyOrchestrator()
        core.empathy = mock_empathy
        
        # Run empathy phase
        core._phase_empathy(None, world_state_multi_agents)
        
        # Calculate multi-agent fields
        ma_fields = calculate_all_multiagent_fields(
            other_entities=world_state_multi_agents.agents,
            empathy_results=core._empathy_results,
            goal_overlap=0.0,
        )
        
        # Should have real calculations, not defaults
        assert ma_fields['ma_agent_count'] == 4  # 3 agents + self
        assert ma_fields['empathy_score'] > 0.0  # Not default
        assert ma_fields['ma_coordination_mode'] != 'single'


# ============================================================================
# TESTS: Error Handling
# ============================================================================

class TestEmpathyErrorHandling:
    """Tests for error handling in empathy phase."""
    
    def test_invalid_agent_data_skipped(self):
        """Geçersiz ajan verisi atlanmalı."""
        from core.unified_core import create_unified_core
        
        core = create_unified_core(storage_type="memory")
        
        # Mock empathy that fails on second agent
        call_count = [0]
        def mock_compute(other):
            call_count[0] += 1
            if call_count[0] == 2:
                raise ValueError("Invalid agent")
            return MockEmpathyResult(other_entity=other)
        
        mock_empathy = MagicMock()
        mock_empathy.compute = mock_compute
        core.empathy = mock_empathy
        
        world_state = MockWorldState(agents=[
            {'id': 'good_1'},
            {'id': 'bad_agent'},  # Will fail
            {'id': 'good_2'},
        ])
        
        result = core._phase_empathy(None, world_state)
        
        # Should have 2 results (skipped the failing one)
        assert len(core._empathy_results) == 2
    
    def test_no_empathy_system_returns_none(self, world_state_single_agent):
        """Empathy sistemi yoksa None döndürmeli."""
        from core.unified_core import create_unified_core
        
        core = create_unified_core(storage_type="memory")
        core.empathy = None
        
        result = core._phase_empathy(None, world_state_single_agent)
        
        assert result is None
        assert core._empathy_results == []
