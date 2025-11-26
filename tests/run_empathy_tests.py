#!/usr/bin/env python3
# tests/run_empathy_tests.py
"""
Manual test runner for Empathy module.
Runs without pytest dependency.

Author: UEM Project (Efe)
Date: 26 November 2025
"""

import sys
import traceback
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# Add parent to path
sys.path.insert(0, '/home/claude')


# ============================================================================
# MOCK CLASSES
# ============================================================================

@dataclass
class MockEmotionCore:
    valence: float = 0.0
    arousal: float = 0.0


class MockMemoryInterface:
    def __init__(self, experiences: Optional[List[Dict]] = None):
        self.experiences = experiences or []
        self.call_count = 0
    
    def get_similar_experiences(
        self,
        state_vector: tuple,
        tolerance: float = 0.3,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        self.call_count += 1
        return self.experiences[:limit]


# ============================================================================
# TEST FRAMEWORK
# ============================================================================

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

def assert_true(condition, msg="Assertion failed"):
    if not condition:
        raise AssertionError(msg)

def assert_equal(a, b, msg=None):
    if a != b:
        raise AssertionError(msg or f"Expected {b}, got {a}")

def assert_approx(a, b, rel=0.01, msg=None):
    if abs(a - b) > rel * max(abs(a), abs(b), 0.01):
        raise AssertionError(msg or f"Expected ~{b}, got {a}")


# ============================================================================
# TESTS
# ============================================================================

def test_create_orchestrator():
    """Should create orchestrator without errors."""
    from core.empathy.empathy_orchestrator import EmpathyOrchestrator
    orchestrator = EmpathyOrchestrator()
    assert_true(orchestrator is not None, "Orchestrator should be created")
    print("  ✓ test_create_orchestrator")


def test_compute_returns_result():
    """compute() should return EmpathyResult."""
    from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity, EmpathyResult
    
    orchestrator = EmpathyOrchestrator()
    other = OtherEntity(entity_id="test", state_vector=(0.5, 0.5, 0.5), valence=0.0)
    
    result = orchestrator.compute(other)
    
    assert_true(isinstance(result, EmpathyResult), "Should return EmpathyResult")
    assert_true(hasattr(result, 'empathy_level'), "Should have empathy_level")
    assert_true(hasattr(result, 'resonance'), "Should have resonance")
    assert_true(hasattr(result, 'confidence'), "Should have confidence")
    print("  ✓ test_compute_returns_result")


def test_no_experiences_zero_empathy():
    """No experiences should return empathy=0."""
    from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
    
    orchestrator = EmpathyOrchestrator()
    other = OtherEntity(entity_id="test", state_vector=(0.3, 0.8, 0.2), valence=-0.5)
    
    result = orchestrator.compute(other)
    
    assert_equal(result.empathy_level, 0.0, "Empathy should be 0 with no experiences")
    assert_equal(result.confidence, 0.0, "Confidence should be 0 with no experiences")
    print("  ✓ test_no_experiences_zero_empathy")


def test_weighted_average_calculation():
    """Empathy should be weighted average."""
    from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
    
    experiences = [
        {'similarity': 0.9, 'salience': 0.8, 'state_vector': (0.35, 0.75, 0.25)},
        {'similarity': 0.7, 'salience': 0.6, 'state_vector': (0.4, 0.7, 0.3)},
        {'similarity': 0.5, 'salience': 0.4, 'state_vector': (0.5, 0.5, 0.4)},
    ]
    
    memory = MockMemoryInterface(experiences)
    orchestrator = EmpathyOrchestrator(memory_interface=memory)
    other = OtherEntity(entity_id="test", state_vector=(0.3, 0.8, 0.2), valence=0.0)
    
    result = orchestrator.compute(other)
    
    # Manual: (0.9*0.8 + 0.7*0.6 + 0.5*0.4) / (0.8+0.6+0.4) = 1.34/1.8 = 0.744
    assert_approx(result.empathy_level, 0.744, rel=0.01, msg="Weighted average calculation")
    print("  ✓ test_weighted_average_calculation")


def test_same_valence_high_resonance():
    """Same valence should give high resonance."""
    from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
    
    emotion = MockEmotionCore(valence=0.5)
    orchestrator = EmpathyOrchestrator(emotion_system=emotion)
    other = OtherEntity(entity_id="test", state_vector=(0.5, 0.5, 0.5), valence=0.5)
    
    result = orchestrator.compute(other)
    
    assert_approx(result.resonance, 1.0, rel=0.01, msg="Same valence = resonance 1")
    print("  ✓ test_same_valence_high_resonance")


def test_opposite_valence_low_resonance():
    """Opposite valence should give low resonance."""
    from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
    
    emotion = MockEmotionCore(valence=1.0)
    orchestrator = EmpathyOrchestrator(emotion_system=emotion)
    other = OtherEntity(entity_id="test", state_vector=(0.5, 0.5, 0.5), valence=-1.0)
    
    result = orchestrator.compute(other)
    
    assert_approx(result.resonance, 0.0, rel=0.01, msg="Opposite valence = resonance 0")
    print("  ✓ test_opposite_valence_low_resonance")


def test_confidence_increases_with_experiences():
    """More experiences should increase confidence."""
    from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
    
    other = OtherEntity(entity_id="test", state_vector=(0.5, 0.5, 0.5), valence=0.0)
    
    # Few experiences
    exp_few = [{'similarity': 0.8, 'salience': 0.5, 'state_vector': (0.5, 0.5, 0.5)}]
    orch_few = EmpathyOrchestrator(memory_interface=MockMemoryInterface(exp_few))
    result_few = orch_few.compute(other)
    
    # Many experiences
    exp_many = [{'similarity': 0.8, 'salience': 0.5, 'state_vector': (0.5, 0.5, 0.5)} for _ in range(5)]
    orch_many = EmpathyOrchestrator(memory_interface=MockMemoryInterface(exp_many))
    result_many = orch_many.compute(other)
    
    assert_true(result_many.confidence > result_few.confidence, "More experiences = higher confidence")
    print("  ✓ test_confidence_increases_with_experiences")


def test_high_salience_weights_more():
    """Higher salience should have more weight."""
    from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
    
    experiences = [
        {'similarity': 0.8, 'salience': 0.9, 'state_vector': (0.3, 0.8, 0.2)},
        {'similarity': 0.4, 'salience': 0.1, 'state_vector': (0.5, 0.5, 0.5)},
    ]
    
    memory = MockMemoryInterface(experiences)
    orchestrator = EmpathyOrchestrator(memory_interface=memory)
    other = OtherEntity(entity_id="test", state_vector=(0.3, 0.8, 0.2), valence=0.0)
    
    result = orchestrator.compute(other)
    
    # (0.8*0.9 + 0.4*0.1) / (0.9 + 0.1) = 0.76
    assert_approx(result.empathy_level, 0.76, rel=0.01, msg="High salience dominates")
    print("  ✓ test_high_salience_weights_more")


def test_missing_salience_defaults():
    """Missing salience should default to 0.5."""
    from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
    
    experiences = [{'similarity': 0.8, 'state_vector': (0.5, 0.5, 0.5)}]  # No salience
    
    memory = MockMemoryInterface(experiences)
    orchestrator = EmpathyOrchestrator(memory_interface=memory)
    other = OtherEntity(entity_id="test", state_vector=(0.5, 0.5, 0.5), valence=0.0)
    
    result = orchestrator.compute(other)
    
    # empathy = 0.8 * 0.5 / 0.5 = 0.8
    assert_approx(result.empathy_level, 0.8, rel=0.01, msg="Default salience 0.5")
    print("  ✓ test_missing_salience_defaults")


def test_statistics_tracking():
    """Statistics should be tracked."""
    from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
    
    orchestrator = EmpathyOrchestrator()
    other = OtherEntity(entity_id="test", state_vector=(0.5, 0.5, 0.5), valence=0.0)
    
    orchestrator.compute(other)
    orchestrator.compute(other)
    orchestrator.compute(other)
    
    stats = orchestrator.get_stats()
    assert_equal(stats['computations'], 3, "Should track computation count")
    print("  ✓ test_statistics_tracking")


def test_factory_function():
    """Factory should create orchestrator."""
    from core.empathy.empathy_orchestrator import create_empathy_orchestrator
    
    orchestrator = create_empathy_orchestrator()
    assert_true(orchestrator is not None, "Factory should create orchestrator")
    print("  ✓ test_factory_function")


def test_result_to_dict():
    """to_dict should return serializable dict."""
    from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
    
    memory = MockMemoryInterface([{'similarity': 0.8, 'salience': 0.5, 'state_vector': (0.5, 0.5, 0.5)}])
    orchestrator = EmpathyOrchestrator(memory_interface=memory)
    other = OtherEntity(entity_id="test", state_vector=(0.5, 0.5, 0.5), valence=0.0)
    
    result = orchestrator.compute(other)
    result_dict = result.to_dict()
    
    assert_true(isinstance(result_dict, dict), "Should return dict")
    assert_true('empathy_level' in result_dict, "Should have empathy_level")
    assert_true('resonance' in result_dict, "Should have resonance")
    assert_true('confidence' in result_dict, "Should have confidence")
    print("  ✓ test_result_to_dict")


def test_full_scenario():
    """Full realistic empathy scenario."""
    from core.empathy.empathy_orchestrator import EmpathyOrchestrator, OtherEntity
    
    # Past distress experiences
    experiences = [
        {'similarity': 0.85, 'salience': 0.9, 'state_vector': (0.25, 0.85, 0.15)},
        {'similarity': 0.6, 'salience': 0.5, 'state_vector': (0.4, 0.6, 0.35)},
    ]
    
    memory = MockMemoryInterface(experiences)
    emotion = MockEmotionCore(valence=-0.3)
    orchestrator = EmpathyOrchestrator(memory_interface=memory, emotion_system=emotion)
    
    # Distressed NPC
    distressed_npc = OtherEntity(
        entity_id="injured_villager",
        state_vector=(0.2, 0.9, 0.1),
        valence=-0.7,
        relationship=0.3,
    )
    
    result = orchestrator.compute(distressed_npc)
    
    assert_true(result.empathy_level > 0.7, f"Should have high empathy, got {result.empathy_level}")
    assert_true(result.resonance > 0.5, f"Should have decent resonance, got {result.resonance}")
    assert_true(result.confidence > 0.1, f"Should have some confidence, got {result.confidence}")
    print("  ✓ test_full_scenario")


# ============================================================================
# MAIN
# ============================================================================

def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  EMPATHY MODULE TESTS")
    print("=" * 60 + "\n")
    
    tests = [
        test_create_orchestrator,
        test_compute_returns_result,
        test_no_experiences_zero_empathy,
        test_weighted_average_calculation,
        test_same_valence_high_resonance,
        test_opposite_valence_low_resonance,
        test_confidence_increases_with_experiences,
        test_high_salience_weights_more,
        test_missing_salience_defaults,
        test_statistics_tracking,
        test_factory_function,
        test_result_to_dict,
        test_full_scenario,
    ]
    
    result = TestResult()
    
    for test in tests:
        try:
            test()
            result.passed += 1
        except Exception as e:
            result.failed += 1
            result.errors.append((test.__name__, str(e), traceback.format_exc()))
            print(f"  ✗ {test.__name__}: {e}")
    
    print("\n" + "-" * 60)
    print(f"  Results: {result.passed} passed, {result.failed} failed")
    print("-" * 60)
    
    if result.errors:
        print("\nErrors:")
        for name, error, tb in result.errors:
            print(f"\n  {name}:")
            print(f"    {error}")
    
    return result.failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
