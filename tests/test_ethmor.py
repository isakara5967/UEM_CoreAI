# tests/test_ethmor.py
"""
ETHMOR System Tests

Tests for the Ethics & Morality Reasoning System:
- Constraint loading
- Condition evaluation
- Violation scoring
- Action decisions (ALLOW/FLAG/BLOCK)
"""

import pytest
from typing import Dict, Any


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_constraints() -> Dict[str, Any]:
    """Sample constraints for testing."""
    return {
        'ethmor': {
            'version': '0.1.0',
            'thresholds': {
                'allow_max': 0.3,
                'flag_max': 0.7,
            },
            'constraints': [
                {
                    'id': 'no_self_destruction',
                    'type': 'HARD',
                    'scope': 'SELF',
                    'condition': 'RESOURCE_LEVEL_after < 0.1',
                    'severity': 1.0,
                    'description': 'Cannot destroy self',
                },
                {
                    'id': 'no_pure_malice',
                    'type': 'HARD',
                    'scope': 'OTHER',
                    'condition': 'WELLBEING_other_delta < -0.5 and benefit < 0.1',
                    'severity': 1.0,
                    'description': 'Cannot harm others without benefit',
                },
                {
                    'id': 'avoid_high_risk',
                    'type': 'SOFT',
                    'scope': 'SELF',
                    'condition': 'THREAT_LEVEL_after > 0.7 and benefit < 0.3',
                    'severity': 0.6,
                    'description': 'Avoid unnecessary risk',
                },
                {
                    'id': 'prefer_low_cost',
                    'type': 'SOFT',
                    'scope': 'SELF',
                    'condition': 'cost > 0.4',
                    'severity': 0.4,
                    'description': 'Prefer low cost actions',
                },
            ]
        }
    }


@pytest.fixture
def ethmor_system(sample_constraints):
    """Create EthmorSystem with sample constraints."""
    from core.ethmor import EthmorSystem
    
    system = EthmorSystem()
    system.load_constraints_from_dict(sample_constraints)
    return system


# ============================================================================
# CONSTRAINT STORE TESTS
# ============================================================================

class TestConstraintStore:
    """ConstraintStore tests."""
    
    def test_load_from_dict(self, sample_constraints):
        """Should load constraints from dict."""
        from core.ethmor import ConstraintStore
        
        store = ConstraintStore()
        store.load_from_dict(sample_constraints)
        
        assert len(store.constraints) == 4
    
    def test_get_hard_constraints(self, sample_constraints):
        """Should filter HARD constraints."""
        from core.ethmor import ConstraintStore
        
        store = ConstraintStore()
        store.load_from_dict(sample_constraints)
        
        hard = store.get_hard_constraints()
        assert len(hard) == 2
        assert all(c.id in ['no_self_destruction', 'no_pure_malice'] for c in hard)
    
    def test_get_soft_constraints(self, sample_constraints):
        """Should filter SOFT constraints."""
        from core.ethmor import ConstraintStore
        
        store = ConstraintStore()
        store.load_from_dict(sample_constraints)
        
        soft = store.get_soft_constraints()
        assert len(soft) == 2
    
    def test_thresholds_loaded(self, sample_constraints):
        """Should load thresholds."""
        from core.ethmor import ConstraintStore
        
        store = ConstraintStore()
        store.load_from_dict(sample_constraints)
        
        assert store.thresholds['allow_max'] == 0.3
        assert store.thresholds['flag_max'] == 0.7


# ============================================================================
# CONSTRAINT EVALUATOR TESTS
# ============================================================================

class TestConstraintEvaluator:
    """ConstraintEvaluator tests."""
    
    def test_evaluate_simple_condition(self, ethmor_system):
        """Should evaluate simple condition."""
        from core.ethmor import EthmorContext
        
        # RESOURCE_LEVEL_after < 0.1 should trigger
        context = EthmorContext()
        context.RESOURCE_LEVEL_after = 0.05
        
        result = ethmor_system.evaluate(context)
        
        triggered_ids = [v.constraint_id for v in result.triggered_constraints]
        assert 'no_self_destruction' in triggered_ids
    
    def test_evaluate_compound_condition(self, ethmor_system):
        """Should evaluate compound AND condition."""
        from core.ethmor import EthmorContext
        
        # WELLBEING_other_delta < -0.5 AND benefit < 0.1
        context = EthmorContext()
        context.WELLBEING_other_delta = -0.6
        context.benefit = 0.05
        
        result = ethmor_system.evaluate(context)
        
        triggered_ids = [v.constraint_id for v in result.triggered_constraints]
        assert 'no_pure_malice' in triggered_ids
    
    def test_compound_condition_not_triggered(self, ethmor_system):
        """Compound condition should not trigger if one part fails."""
        from core.ethmor import EthmorContext
        
        # WELLBEING_other_delta < -0.5 BUT benefit > 0.1 (has benefit)
        context = EthmorContext()
        context.WELLBEING_other_delta = -0.6
        context.benefit = 0.5  # Has benefit, so not pure malice
        
        result = ethmor_system.evaluate(context)
        
        triggered_ids = [v.constraint_id for v in result.triggered_constraints]
        assert 'no_pure_malice' not in triggered_ids


# ============================================================================
# ACTION DECISION TESTS
# ============================================================================

class TestActionDecision:
    """Action decision tests."""
    
    def test_allow_when_no_violations(self, ethmor_system):
        """Should ALLOW when no violations."""
        from core.ethmor import EthmorContext, ActionDecision
        
        context = EthmorContext()
        context.RESOURCE_LEVEL_after = 0.8
        context.THREAT_LEVEL_after = 0.2
        context.WELLBEING_other_delta = 0.0
        context.benefit = 0.5
        context.cost = 0.1
        
        result = ethmor_system.evaluate(context)
        
        assert result.decision == ActionDecision.ALLOW
        assert result.violation_score < 0.3
    
    def test_block_on_hard_violation(self, ethmor_system):
        """Should BLOCK on HARD constraint violation."""
        from core.ethmor import EthmorContext, ActionDecision
        
        context = EthmorContext()
        context.RESOURCE_LEVEL_after = 0.05  # Critical self-damage
        
        result = ethmor_system.evaluate(context)
        
        assert result.decision == ActionDecision.BLOCK
        assert result.hard_violation is True
        assert result.violation_score >= 0.7
    
    def test_flag_on_soft_violation(self, ethmor_system):
        """Should FLAG on moderate soft violation."""
        from core.ethmor import EthmorContext, ActionDecision
        
        context = EthmorContext()
        context.RESOURCE_LEVEL_after = 0.5
        context.THREAT_LEVEL_after = 0.8  # High risk
        context.benefit = 0.1  # Low benefit
        context.cost = 0.5  # High cost
        
        result = ethmor_system.evaluate(context)
        
        # Multiple soft violations should push to FLAG or higher
        assert result.decision in [ActionDecision.FLAG, ActionDecision.BLOCK]
    
    def test_violation_score_calculation(self, ethmor_system):
        """Violation score should be computed correctly."""
        from core.ethmor import EthmorContext
        
        context = EthmorContext()
        context.cost = 0.5  # Triggers 'prefer_low_cost' (severity 0.4)
        
        result = ethmor_system.evaluate(context)
        
        # Should have some violation score
        assert result.violation_score > 0


# ============================================================================
# ETHMOR CONTEXT TESTS
# ============================================================================

class TestEthmorContext:
    """EthmorContext tests."""
    
    def test_from_self_context(self):
        """Should build from SelfCore context."""
        from core.ethmor import EthmorContext
        
        self_context = {
            'RESOURCE_LEVEL': 0.8,
            'THREAT_LEVEL': 0.2,
            'WELLBEING': 0.7,
            'RESOURCE_LEVEL_before': 0.9,
            'THREAT_LEVEL_before': 0.1,
            'WELLBEING_before': 0.6,
        }
        
        predicted_state = (0.6, 0.4, 0.5)  # After action
        
        ctx = EthmorContext.from_self_context(
            self_context,
            predicted_state=predicted_state,
            action_name="attack",
        )
        
        assert ctx.RESOURCE_LEVEL == 0.8
        assert ctx.RESOURCE_LEVEL_after == 0.6
        assert ctx.action_name == "attack"
    
    def test_benefit_cost_computed(self):
        """Benefit and cost should be auto-computed."""
        from core.ethmor import EthmorContext
        
        self_context = {
            'RESOURCE_LEVEL': 0.8,
            'WELLBEING': 0.5,
            'RESOURCE_LEVEL_before': 0.9,
            'WELLBEING_before': 0.4,
        }
        
        predicted_state = (0.6, 0.3, 0.7)  # Resource down, wellbeing up
        
        ctx = EthmorContext.from_self_context(
            self_context,
            predicted_state=predicted_state,
        )
        
        # Benefit = positive wellbeing delta = 0.7 - 0.4 = 0.3
        assert ctx.benefit == pytest.approx(0.3, rel=0.01)
        
        # Cost = negative resource delta = 0.9 - 0.6 = 0.3
        assert ctx.cost == pytest.approx(0.3, rel=0.01)
    
    def test_to_eval_dict(self):
        """Should convert to evaluation dict."""
        from core.ethmor import EthmorContext
        
        ctx = EthmorContext()
        ctx.RESOURCE_LEVEL = 0.5
        ctx.action_name = "test"
        
        eval_dict = ctx.to_eval_dict()
        
        assert eval_dict['RESOURCE_LEVEL'] == 0.5
        assert eval_dict['action_name'] == "test"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestEthmorIntegration:
    """Integration tests."""
    
    def test_check_constraint_breach_protocol(self, ethmor_system):
        """Should implement EthmorLike protocol."""
        from dataclasses import dataclass
        
        @dataclass
        class MockEvent:
            source: str = "SELF"
            target: str = "SELF"
            effect: tuple = (-0.5, 0.3, -0.2)  # Resource loss, threat up, wellbeing down
        
        event = MockEvent()
        context = {
            'RESOURCE_LEVEL': 0.6,
            'THREAT_LEVEL': 0.2,
            'WELLBEING': 0.5,
        }
        
        violation = ethmor_system.check_constraint_breach(event, context)
        
        # Should return float 0-1
        assert isinstance(violation, float)
        assert 0.0 <= violation <= 1.0
    
    def test_filter_action_convenience(self, ethmor_system):
        """filter_action should return just the decision."""
        from core.ethmor import EthmorContext, ActionDecision
        
        context = EthmorContext()
        context.RESOURCE_LEVEL_after = 0.8
        
        decision = ethmor_system.filter_action(context)
        
        assert isinstance(decision, ActionDecision)
    
    def test_explain_last_decision(self, ethmor_system):
        """Should explain last decision."""
        from core.ethmor import EthmorContext
        
        context = EthmorContext()
        context.RESOURCE_LEVEL_after = 0.05  # Triggers violation
        
        ethmor_system.evaluate(context)
        explanation = ethmor_system.explain_last_decision()
        
        assert "no_self_destruction" in explanation
    
    def test_get_stats(self, ethmor_system):
        """Should return stats."""
        stats = ethmor_system.get_stats()
        
        assert stats['total_constraints'] == 4
        assert stats['hard_constraints'] == 2
        assert stats['soft_constraints'] == 2


# ============================================================================
# SCENARIO TESTS
# ============================================================================

class TestEthicalScenarios:
    """Real-world ethical scenario tests."""
    
    def test_scenario_flee_from_danger(self, ethmor_system):
        """Fleeing from danger should be ALLOWED."""
        from core.ethmor import EthmorContext, ActionDecision
        
        # Current: high threat, low resources
        # After flee: lower threat, slightly lower resources
        context = EthmorContext()
        context.RESOURCE_LEVEL = 0.4
        context.RESOURCE_LEVEL_before = 0.4
        context.RESOURCE_LEVEL_after = 0.35  # Small cost
        
        context.THREAT_LEVEL = 0.8
        context.THREAT_LEVEL_before = 0.8
        context.THREAT_LEVEL_after = 0.3  # Much safer
        
        context.benefit = 0.2
        context.cost = 0.05
        
        result = ethmor_system.evaluate(context)
        
        assert result.decision == ActionDecision.ALLOW
    
    def test_scenario_suicidal_attack(self, ethmor_system):
        """Suicidal attack should be BLOCKED."""
        from core.ethmor import EthmorContext, ActionDecision
        
        context = EthmorContext()
        context.RESOURCE_LEVEL = 0.3
        context.RESOURCE_LEVEL_before = 0.3
        context.RESOURCE_LEVEL_after = 0.05  # Near death
        
        context.benefit = 0.1  # Small benefit
        
        result = ethmor_system.evaluate(context)
        
        assert result.decision == ActionDecision.BLOCK
        assert result.hard_violation is True
    
    def test_scenario_help_other(self, ethmor_system):
        """Helping another agent should be ALLOWED."""
        from core.ethmor import EthmorContext, ActionDecision
        
        context = EthmorContext()
        context.RESOURCE_LEVEL_after = 0.7
        context.THREAT_LEVEL_after = 0.2
        context.WELLBEING_other_delta = 0.3  # Helping other
        context.benefit = 0.1
        context.cost = 0.1
        
        result = ethmor_system.evaluate(context)
        
        assert result.decision == ActionDecision.ALLOW
    
    def test_scenario_pure_malice(self, ethmor_system):
        """Pure malice (harm without benefit) should be BLOCKED."""
        from core.ethmor import EthmorContext, ActionDecision
        
        context = EthmorContext()
        context.RESOURCE_LEVEL_after = 0.8
        context.WELLBEING_other_delta = -0.6  # Severe harm to other
        context.benefit = 0.02  # Negligible benefit
        
        result = ethmor_system.evaluate(context)
        
        assert result.decision == ActionDecision.BLOCK
        assert result.hard_violation is True


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
