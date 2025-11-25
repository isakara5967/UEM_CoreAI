#!/usr/bin/env python3
"""
UEM Emotion → Planning Feedback Loop Demo

Bu demo, farklı duygusal durumlarda sistemin nasıl karar verdiğini gösterir.

Kullanım:
    python demo_emotion_planning.py
"""

import sys
sys.path.insert(0, '/home/claude/uem_project')

from core.planning.action_selection.emotional_action_selector import (
    EmotionalActionSelector,
    WorkingMemoryState,
)

class MockTarget:
    def __init__(self, id="box_1", distance=5.0):
        self.id = id
        self.distance = distance
        self.obj_type = "box"

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_emotion_state(selector):
    e = selector.current_emotion
    print(f"  PAD: valence={e.valence:+.2f}, arousal={e.arousal:+.2f}, dominance={e.dominance:+.2f}")
    print(f"  Emotion: {e.emotion_label.upper()}")
    print(f"  Danger threshold: {selector._compute_danger_threshold():.2f}")
    print(f"  Exploration willingness: {selector._compute_exploration_willingness():.2f}")
    print(f"  Escape urgency: {selector._compute_escape_urgency():.2f}")

def run_scenario(selector, wm, scenario_name):
    print(f"\n  Scenario: {scenario_name}")
    print(f"  World: danger={wm.danger_level:.2f}, target={'Yes' if wm.nearest_target else 'No'}, symbols={wm.symbols}")
    
    action = selector.select_action(wm)
    
    print(f"\n  → ACTION: {action.name}")
    print(f"    Confidence: {action.confidence:.2f}")
    print(f"    Emotion influence: {action.emotional_influence:.2f}")
    if action.params:
        for k, v in action.params.items():
            if k != 'symbols':
                print(f"    {k}: {v}")

def demo_fear():
    print_header("KORKU DURUMU (Fear)")
    
    selector = EmotionalActionSelector()
    selector.update_emotional_state({
        'valence': -0.7,
        'arousal': 0.8,
        'dominance': -0.4
    })
    print_emotion_state(selector)
    
    # Düşük tehlike - normalde kaçış olmaz
    wm = WorkingMemoryState(tick=1, danger_level=0.4, symbols=[])
    run_scenario(selector, wm, "Low danger (0.4)")
    
    # Hedef var ama korkuyor
    wm = WorkingMemoryState(tick=2, danger_level=0.2, nearest_target=MockTarget(), symbols=[])
    run_scenario(selector, wm, "Target visible, low danger")
    
    # Ajan görünce kaçınma
    wm = WorkingMemoryState(tick=3, danger_level=0.1, symbols=["AGENT_IN_SIGHT"])
    run_scenario(selector, wm, "Agent in sight")

def demo_excitement():
    print_header("HEYECAN DURUMU (Excitement)")
    
    selector = EmotionalActionSelector()
    selector.update_emotional_state({
        'valence': 0.8,
        'arousal': 0.7,
        'dominance': 0.3
    })
    print_emotion_state(selector)
    
    # Yüksek tehlike ama heyecanlı - risk al
    wm = WorkingMemoryState(tick=1, danger_level=0.75, nearest_target=MockTarget(), symbols=[])
    run_scenario(selector, wm, "High danger (0.75) + target")
    
    # Boş sahne - aktif keşif
    wm = WorkingMemoryState(tick=2, danger_level=0.1, symbols=[])
    run_scenario(selector, wm, "Empty scene - exploration")
    
    # Ajan görünce dostça selamlama
    wm = WorkingMemoryState(tick=3, danger_level=0.1, symbols=["AGENT_IN_SIGHT"])
    run_scenario(selector, wm, "Agent in sight - social")

def demo_anger():
    print_header("ÖFKE DURUMU (Anger)")
    
    selector = EmotionalActionSelector()
    selector.update_emotional_state({
        'valence': -0.6,
        'arousal': 0.7,
        'dominance': 0.5  # High dominance
    })
    print_emotion_state(selector)
    
    # Tehlike var - yüzleşme
    wm = WorkingMemoryState(tick=1, danger_level=0.6, symbols=[])
    run_scenario(selector, wm, "Danger present - confrontation")
    
    # Ajan görünce assertive
    wm = WorkingMemoryState(tick=2, danger_level=0.1, symbols=["AGENT_IN_SIGHT"])
    run_scenario(selector, wm, "Agent in sight - assertive")

def demo_calm():
    print_header("SAKİN DURUM (Calm)")
    
    selector = EmotionalActionSelector()
    selector.update_emotional_state({
        'valence': 0.1,
        'arousal': -0.4,  # Low arousal
        'dominance': 0.0
    })
    print_emotion_state(selector)
    
    # Düşük tehlike - dikkatli gözlem
    wm = WorkingMemoryState(tick=1, danger_level=0.3, symbols=[])
    run_scenario(selector, wm, "Low activity scene")
    
    # Normal yaklaşım
    wm = WorkingMemoryState(tick=2, danger_level=0.1, nearest_target=MockTarget(), symbols=[])
    run_scenario(selector, wm, "Target visible")

def demo_neutral_comparison():
    print_header("NÖTR VS KORKU - KARŞILAŞTIRMA")
    
    selector = EmotionalActionSelector()
    
    print("\n  Same scenario, different emotions:")
    print("  Danger level: 0.55 (between thresholds)")
    
    wm = WorkingMemoryState(tick=1, danger_level=0.55, symbols=[])
    
    # Neutral
    print("\n  [NEUTRAL]")
    selector.update_emotional_state({'valence': 0.0, 'arousal': 0.0, 'dominance': 0.0})
    action = selector.select_action(wm)
    print(f"    Threshold: {selector._compute_danger_threshold():.2f}")
    print(f"    Action: {action.name}")
    
    # Fear
    print("\n  [FEAR]")
    selector.update_emotional_state({'valence': -0.6, 'arousal': 0.7, 'dominance': -0.3})
    action = selector.select_action(wm)
    print(f"    Threshold: {selector._compute_danger_threshold():.2f}")
    print(f"    Action: {action.name}")
    
    # Excitement
    print("\n  [EXCITEMENT]")
    selector.update_emotional_state({'valence': 0.7, 'arousal': 0.6, 'dominance': 0.3})
    action = selector.select_action(wm)
    print(f"    Threshold: {selector._compute_danger_threshold():.2f}")
    print(f"    Action: {action.name}")

def main():
    print("\n" + "=" * 60)
    print("  UEM EMOTION → PLANNING FEEDBACK LOOP DEMO")
    print("=" * 60)
    print("""
  Bu demo, duygusal durumun karar verme sürecini
  nasıl etkilediğini gösterir.
  
  PAD Modeli:
  - Valence: -1 (negatif) → +1 (pozitif)
  - Arousal: -1 (sakin) → +1 (heyecanlı)
  - Dominance: -1 (boyun eğen) → +1 (baskın)
  
  Duygu etkisi:
  - Fear: Düşük eşik, erken kaçış, temkinli yaklaşım
  - Excitement: Yüksek eşik, risk alma, aktif keşif
  - Anger: Yüzleşme, assertive davranış
  - Calm: Normal eşikler, dikkatli karar
    """)
    
    demo_fear()
    demo_excitement()
    demo_anger()
    demo_calm()
    demo_neutral_comparison()
    
    print("\n" + "=" * 60)
    print("  DEMO COMPLETE")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
