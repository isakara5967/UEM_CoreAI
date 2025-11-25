#!/usr/bin/env python3
# tests/run_memory_tests.py
"""
Manual test runner for Memory Interface.
Runs without pytest dependency.
"""

import sys
import time
import traceback
from dataclasses import dataclass
from typing import List, Any, Dict

# Add parent to path
sys.path.insert(0, '/home/claude')


# ============================================================================
# MOCK CLASSES
# ============================================================================

@dataclass
class MockEvent:
    source: str
    target: str
    effect: tuple
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class MockSelfEntity:
    state_vector: tuple
    history: List[Any] = None
    goals: List[Any] = None
    
    def __post_init__(self):
        if self.history is None:
            self.history = []
        if self.goals is None:
            self.goals = []


@dataclass  
class MockEmotionCore:
    valence: float = 0.0


class MockLTM:
    def __init__(self):
        self.stored_items = []
        self.store_calls = 0
        self.retrieve_calls = 0
    
    def store(self, content, memory_type=None, salience=0.5, source="", **kwargs):
        self.store_calls += 1
        item = {'content': content, 'memory_type': memory_type, 'salience': salience}
        self.stored_items.append(item)
        return item
    
    def retrieve(self, memory_type=None, limit=10, update_access=True, **kwargs):
        self.retrieve_calls += 1
        class MockMemory:
            def __init__(self, item):
                self.content = item['content']
                self.created_at = time.time()
        return [MockMemory(item) for item in self.stored_items[-limit:]]


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
    if abs(a - b) > rel * max(abs(a), abs(b), 1):
        raise AssertionError(msg or f"Expected ~{b}, got {a}")


# ============================================================================
# TESTS
# ============================================================================

def test_create_interface():
    """Should create interface without errors."""
    from core.memory.memory_interface import MemoryInterface
    interface = MemoryInterface()
    assert_true(interface is not None, "Interface should be created")
    assert_true(interface.ltm is None, "LTM should be None initially")
    print("  ✓ test_create_interface")

def test_store_event_dict():
    """Should store event as dict."""
    from core.memory.memory_interface import MemoryInterface
    interface = MemoryInterface()
    
    event = {'source': 'player', 'target': 'enemy', 'effect': (0.1, -0.2, 0.0)}
    result = interface.store_event(event)
    
    assert_true(result, "store_event should return True")
    assert_equal(interface.get_stats()['events_stored'], 1, "Should have 1 event stored")
    print("  ✓ test_store_event_dict")

def test_store_event_object():
    """Should store Event object."""
    from core.memory.memory_interface import MemoryInterface
    interface = MemoryInterface()
    
    event = MockEvent(source='world', target='self', effect=(-0.1, 0.3, -0.1))
    result = interface.store_event(event)
    
    assert_true(result, "store_event should return True")
    print("  ✓ test_store_event_object")

def test_store_event_buffers():
    """Should buffer events when LTM not available."""
    from core.memory.memory_interface import MemoryInterface
    interface = MemoryInterface()
    
    interface.store_event({'source': 'test', 'target': 'test', 'effect': (0, 0, 0)})
    
    stats = interface.get_stats()
    assert_equal(stats['event_buffer_size'], 1, "Buffer should have 1 item")
    print("  ✓ test_store_event_buffers")

def test_store_event_to_ltm():
    """Should store event to LTM when available."""
    from core.memory.memory_interface import MemoryInterface
    
    ltm = MockLTM()
    interface = MemoryInterface(ltm=ltm)
    
    interface.store_event({'source': 'test', 'target': 'test', 'effect': (0, 0, 0)})
    
    assert_equal(ltm.store_calls, 1, "LTM store should be called once")
    print("  ✓ test_store_event_to_ltm")

def test_store_snapshot():
    """Should store snapshot."""
    from core.memory.memory_interface import MemoryInterface
    interface = MemoryInterface()
    
    snapshot = {'state_vector': (0.7, 0.2, 0.8), 'history': [], 'goals': []}
    result = interface.store_state_snapshot(snapshot)
    
    assert_true(result, "store_state_snapshot should return True")
    assert_equal(interface.get_stats()['snapshots_stored'], 1, "Should have 1 snapshot")
    print("  ✓ test_store_snapshot")

def test_similarity_computation():
    """Test similarity computation."""
    from core.memory.memory_interface import MemoryInterface
    interface = MemoryInterface()
    
    # Identical states
    sim1 = interface._compute_similarity((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    assert_approx(sim1, 1.0, rel=0.01, msg="Identical states should have similarity 1.0")
    
    # Different states
    sim2 = interface._compute_similarity((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
    assert_true(sim2 < 0.5, "Opposite states should have low similarity")
    print("  ✓ test_similarity_computation")

def test_get_similar_experiences():
    """Should find similar experiences."""
    from core.memory.memory_interface import MemoryInterface
    interface = MemoryInterface()
    
    # Store experiences
    interface.store_state_snapshot({'state_vector': (0.8, 0.2, 0.9)})
    interface.store_state_snapshot({'state_vector': (0.3, 0.8, 0.2)})
    
    # Search
    similar = interface.get_similar_experiences((0.75, 0.25, 0.85), tolerance=0.3)
    
    assert_true(len(similar) >= 1, "Should find at least 1 similar experience")
    assert_true(similar[0]['similarity'] > 0.7, "First match should have high similarity")
    print("  ✓ test_get_similar_experiences")

def test_flush_buffers():
    """Should flush buffers when LTM becomes available."""
    from core.memory.memory_interface import MemoryInterface
    interface = MemoryInterface()
    
    # Store without LTM
    for i in range(5):
        interface.store_event({'source': f'event_{i}', 'target': 'self', 'effect': (0, 0, 0)})
    
    assert_equal(len(interface._event_buffer), 5, "Should have 5 buffered events")
    
    # Add LTM
    ltm = MockLTM()
    interface.set_ltm(ltm)
    
    # Buffer should be flushed
    assert_equal(len(interface._event_buffer), 0, "Buffer should be empty after flush")
    assert_equal(ltm.store_calls, 5, "LTM should receive all buffered events")
    print("  ✓ test_flush_buffers")

def test_self_core_with_memory():
    """Test SelfCore with MemoryInterface."""
    from core.self.self_core import SelfCore
    from core.memory.memory_interface import MemoryInterface
    
    memory = MemoryInterface()
    emotion = MockEmotionCore(valence=0.3)
    
    core = SelfCore(
        memory_system=memory,
        emotion_system=emotion,
        config={'memory_write_interval': 1}  # Write every tick for testing
    )
    
    # Simulate updates
    for i in range(3):
        core.update(dt=0.1, world_snapshot={
            'player_health': 0.8 - i * 0.1,
            'player_energy': 0.7,
            'danger_level': 0.2 + i * 0.1,
        })
    
    # Check memory writes
    stats = memory.get_stats()
    assert_true(stats['snapshots_stored'] >= 1, "Should have stored snapshots")
    print("  ✓ test_self_core_with_memory")

def test_self_record_event_writes_to_memory():
    """SELF record_event should write to memory."""
    from core.self.self_core import SelfCore
    from core.memory.memory_interface import MemoryInterface
    
    memory = MemoryInterface()
    emotion = MockEmotionCore()
    
    core = SelfCore(memory_system=memory, emotion_system=emotion)
    
    # Create and record event
    core.create_and_record_event(source='action', target='world', effect=(0.1, 0, 0))
    
    stats = memory.get_stats()
    assert_equal(stats['events_stored'], 1, "Should have stored 1 event")
    print("  ✓ test_self_record_event_writes_to_memory")

def test_factory_function():
    """Test factory function."""
    from core.memory.memory_interface import create_memory_interface
    
    interface = create_memory_interface()
    assert_true(interface is not None, "Factory should create interface")
    
    ltm = MockLTM()
    interface2 = create_memory_interface(ltm=ltm)
    assert_true(interface2.ltm is ltm, "Factory should accept ltm parameter")
    print("  ✓ test_factory_function")


# ============================================================================
# MAIN
# ============================================================================

def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 60)
    print("  MEMORY INTERFACE TESTS")
    print("=" * 60 + "\n")
    
    tests = [
        test_create_interface,
        test_store_event_dict,
        test_store_event_object,
        test_store_event_buffers,
        test_store_event_to_ltm,
        test_store_snapshot,
        test_similarity_computation,
        test_get_similar_experiences,
        test_flush_buffers,
        test_self_core_with_memory,
        test_self_record_event_writes_to_memory,
        test_factory_function,
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
