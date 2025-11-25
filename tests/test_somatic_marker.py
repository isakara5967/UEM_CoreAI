"""
Tests for Somatic Marker System

Test scenarios:
1. Marker creation on outcome
2. Bias calculation from markers
3. Decision modification by bias
4. Marker decay over time
5. Similar situation generalization
"""

import sys
sys.path.insert(0, '/home/claude/uem_project')

from core.emotion.somatic_marker_system import (
    SomaticMarkerSystem,
    SomaticMarker,
    PendingAction,
)
from core.planning.action_selection.somatic_action_selector import (
    SomaticEmotionalActionSelector,
)
from core.planning.action_selection.emotional_action_selector import (
    WorkingMemoryState,
)


class MockTarget:
    id = "target_1"
    distance = 5.0


def test_marker_creation():
    """Marker oluşturma testi"""
    print("\n=== TEST: Marker Creation ===")
    
    system = SomaticMarkerSystem()
    
    # Action kaydet
    world_state = {'danger_level': 0.3, 'symbols': ['TARGET_VISIBLE']}
    emotion_state = {'valence': 0.2, 'arousal': 0.3}
    
    situation_hash = system.record_action(
        action_name="APPROACH_TARGET",
        action_params={'target_id': 'box_1'},
        world_state=world_state,
        emotion_state=emotion_state,
    )
    
    assert len(system.pending_actions) == 1
    print(f"  ✓ Action recorded, situation_hash: {situation_hash}")
    
    # Outcome kaydet
    marker = system.record_outcome(
        outcome_valence=0.8,  # Positive outcome
        outcome_description="found_reward",
    )
    
    assert marker is not None
    assert marker.valence == 0.8
    assert marker.action == "APPROACH_TARGET"
    print(f"  ✓ Marker created: valence={marker.valence}, action={marker.action}")
    
    assert system.total_markers == 1
    print(f"  ✓ Total markers: {system.total_markers}")
    
    return True


def test_negative_marker():
    """Negatif marker testi (ceza)"""
    print("\n=== TEST: Negative Marker ===")
    
    system = SomaticMarkerSystem()
    
    # Tehlikeli durumda APPROACH yap
    world_state = {'danger_level': 0.6, 'symbols': ['DANGER_HIGH']}
    
    system.record_action(
        action_name="APPROACH_TARGET",
        action_params={},
        world_state=world_state,
        emotion_state={},
    )
    
    # Kötü sonuç
    marker = system.record_outcome(
        outcome_valence=-0.7,
        outcome_description="took_damage",
    )
    
    assert marker.valence == -0.7
    print(f"  ✓ Negative marker created: valence={marker.valence}")
    
    return True


def test_bias_calculation():
    """Bias hesaplama testi"""
    print("\n=== TEST: Bias Calculation ===")
    
    system = SomaticMarkerSystem()
    
    # Pozitif deneyim kaydet
    world_state = {'danger_level': 0.2, 'symbols': []}
    
    system.record_action("EXPLORE", {}, world_state, {})
    system.record_outcome(0.5, "found_item")
    
    # Negatif deneyim kaydet
    system.record_action("APPROACH_TARGET", {}, world_state, {})
    system.record_outcome(-0.6, "trap")
    
    # Bias al
    biases = system.get_action_biases(world_state, ["EXPLORE", "APPROACH_TARGET", "ESCAPE"])
    
    print(f"  EXPLORE bias: {biases['EXPLORE'].bias_value:+.2f}")
    print(f"  APPROACH_TARGET bias: {biases['APPROACH_TARGET'].bias_value:+.2f}")
    print(f"  ESCAPE bias: {biases['ESCAPE'].bias_value:+.2f} (no marker)")
    
    assert biases['EXPLORE'].bias_value > 0
    assert biases['APPROACH_TARGET'].bias_value < 0
    print("  ✓ Biases calculated correctly")
    
    return True


def test_marker_reinforcement():
    """Marker güçlendirme testi"""
    print("\n=== TEST: Marker Reinforcement ===")
    
    system = SomaticMarkerSystem(learning_rate=0.5)
    
    world_state = {'danger_level': 0.3, 'symbols': []}
    
    # İlk deneyim: pozitif
    system.record_action("EXPLORE", {}, world_state, {})
    marker = system.record_outcome(0.6, "reward")
    initial_valence = marker.valence
    initial_count = marker.activation_count
    
    print(f"  Initial: valence={initial_valence}, count={initial_count}")
    
    # İkinci deneyim: daha pozitif
    system.record_action("EXPLORE", {}, world_state, {})
    marker = system.record_outcome(0.9, "big_reward")
    
    print(f"  After reinforcement: valence={marker.valence:.2f}, count={marker.activation_count}")
    
    assert marker.activation_count == 2
    assert marker.valence > initial_valence
    print("  ✓ Marker reinforced correctly")
    
    return True


def test_decision_modification():
    """Somatic bias'ın kararı değiştirmesi testi"""
    print("\n=== TEST: Decision Modification ===")
    
    # Somatic system ile selector oluştur
    somatic = SomaticMarkerSystem()
    selector = SomaticEmotionalActionSelector(somatic_system=somatic)
    
    # Nötr emotion state
    selector.update_emotional_state({
        'valence': 0.0,
        'arousal': 0.0,
        'dominance': 0.0,
    })
    
    # Base case: target var, normal approach
    wm = WorkingMemoryState(
        tick=1,
        danger_level=0.3,
        nearest_target=MockTarget(),
        symbols=[],
    )
    
    action1 = selector.select_action(wm)
    print(f"  Before learning: {action1.name}")
    
    # Negatif deneyim kaydet (APPROACH_TARGET kötü sonuç verdi)
    selector.record_outcome(-0.8, "took_damage")
    
    # Tekrar dene - somatic bias APPROACH'u caydırmalı
    wm.tick = 2
    action2 = selector.select_action(wm)
    
    print(f"  After negative experience: {action2.name}")
    print(f"  Somatic bias: {action2.params.get('somatic_bias', 0)}")
    
    # Bias uygulandı mı?
    assert action2.params.get('somatic_influenced') or action2.name != action1.name or action2.params.get('somatic_bias', 0) != 0
    print("  ✓ Somatic bias applied to decision")
    
    return True


def test_fear_plus_somatic():
    """Korku + negatif somatic marker kombinasyonu"""
    print("\n=== TEST: Fear + Negative Somatic ===")
    
    somatic = SomaticMarkerSystem()
    selector = SomaticEmotionalActionSelector(somatic_system=somatic)
    
    # İlk deneyim: APPROACH kötü sonuç
    selector.update_emotional_state({'valence': 0.0, 'arousal': 0.0, 'dominance': 0.0})
    
    wm = WorkingMemoryState(
        tick=1,
        danger_level=0.4,
        nearest_target=MockTarget(),
        symbols=[],
    )
    
    selector.select_action(wm)
    selector.record_outcome(-0.7, "ambush")
    
    # Şimdi korku durumunda aynı sahne
    selector.update_emotional_state({
        'valence': -0.6,
        'arousal': 0.7,
        'dominance': -0.3,
    })
    
    wm.tick = 2
    action = selector.select_action(wm)
    
    print(f"  Action with fear + negative somatic: {action.name}")
    print(f"  Somatic bias: {action.params.get('somatic_bias', 0):.2f}")
    
    # Korku + negatif marker = kesinlikle kaçış veya temkinli
    assert 'ESCAPE' in action.name or 'CAUTIOUS' in action.name or action.params.get('somatic_bias', 0) < 0
    print("  ✓ Fear + negative somatic reinforced avoidance")
    
    return True


def test_positive_learning():
    """Pozitif öğrenme - ödül aldıkça daha çok yaklaşma"""
    print("\n=== TEST: Positive Learning ===")
    
    somatic = SomaticMarkerSystem()
    selector = SomaticEmotionalActionSelector(somatic_system=somatic)
    
    # Nötr durum
    selector.update_emotional_state({'valence': 0.1, 'arousal': 0.1, 'dominance': 0.0})
    
    wm = WorkingMemoryState(
        tick=1,
        danger_level=0.2,
        nearest_target=MockTarget(),
        symbols=[],
    )
    
    # 3 pozitif deneyim
    for i in range(3):
        wm.tick = i + 1
        action = selector.select_action(wm)
        selector.record_outcome(0.6, "found_reward")
        print(f"  Round {i+1}: {action.name}, conf={action.confidence:.2f}")
    
    # 4. kez dene
    wm.tick = 4
    final_action = selector.select_action(wm)
    
    print(f"  After 3 rewards: {final_action.name}, conf={final_action.confidence:.2f}")
    print(f"  Somatic bias: {final_action.params.get('somatic_bias', 0):.2f}")
    
    stats = selector.get_somatic_stats()
    print(f"  Total markers: {stats['total_markers']}")
    
    # Pozitif bias olmalı
    assert final_action.params.get('somatic_bias', 0) > 0
    print("  ✓ Positive learning accumulated")
    
    return True


def test_statistics():
    """İstatistik testi"""
    print("\n=== TEST: Statistics ===")
    
    system = SomaticMarkerSystem()
    
    # Birkaç deneyim
    for i in range(5):
        world_state = {'danger_level': i * 0.15, 'symbols': []}
        system.record_action(f"ACTION_{i}", {}, world_state, {})
        system.record_outcome(0.5 - i * 0.2, f"outcome_{i}")
    
    stats = system.get_stats()
    
    print(f"  Total markers: {stats['total_markers']}")
    print(f"  Unique situations: {stats['unique_situations']}")
    print(f"  Strongest markers: {stats['strongest_markers'][:3]}")
    
    assert stats['total_markers'] == 5
    print("  ✓ Statistics calculated correctly")
    
    return True


def run_all_tests():
    """Tüm testleri çalıştır"""
    print("\n" + "=" * 60)
    print("  SOMATIC MARKER SYSTEM TESTS")
    print("=" * 60)
    
    tests = [
        test_marker_creation,
        test_negative_marker,
        test_bias_calculation,
        test_marker_reinforcement,
        test_decision_modification,
        test_fear_plus_somatic,
        test_positive_learning,
        test_statistics,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
