#!/usr/bin/env python3
"""
UEM Somatic Marker System Demo

Geçmiş deneyimlerden öğrenme ve karar vermeye etkisini gösterir.

Senaryo:
1. Agent karanlık mağaraya girer → saldırıya uğrar → negatif marker
2. Agent ormanda keşif yapar → ödül bulur → pozitif marker
3. Gelecekte benzer durumlarda marker'lar kararları etkiler
"""

import sys
sys.path.insert(0, '/home/claude/uem_project')

from core.emotion.somatic_marker_system import SomaticMarkerSystem
from core.planning.action_selection.somatic_action_selector import (
    SomaticEmotionalActionSelector,
)
from core.planning.action_selection.emotional_action_selector import (
    WorkingMemoryState,
)


class MockTarget:
    def __init__(self, id="target", distance=5.0):
        self.id = id
        self.distance = distance


def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_action(action, prefix=""):
    print(f"{prefix}→ ACTION: {action.name}")
    print(f"{prefix}  Confidence: {action.confidence:.2f}")
    print(f"{prefix}  Emotion influence: {action.emotional_influence:.2f}")
    somatic_bias = action.params.get('somatic_bias', 0)
    if somatic_bias != 0:
        print(f"{prefix}  Somatic bias: {somatic_bias:+.3f}")
    if action.params.get('somatic_influenced'):
        print(f"{prefix}  ⚡ Decision influenced by past experience!")


def demo_learning_from_danger():
    """Tehlikeden öğrenme senaryosu"""
    print_header("SENARYO 1: Tehlikeden Öğrenme")
    
    print("""
  Agent karanlık mağaraya yaklaşıyor...
  İlk denemede ne olacağını bilmiyor.
    """)
    
    somatic = SomaticMarkerSystem()
    selector = SomaticEmotionalActionSelector(somatic_system=somatic)
    
    # Nötr duygusal durum
    selector.update_emotional_state({
        'valence': 0.0,
        'arousal': 0.1,
        'dominance': 0.0,
    })
    
    # Karanlık mağara senaryosu
    wm = WorkingMemoryState(
        tick=1,
        danger_level=0.4,
        nearest_target=MockTarget("dark_cave"),
        symbols=['DANGER_LOW'],
    )
    
    print("  [İLK KARŞILAŞMA]")
    print(f"  Durum: danger={wm.danger_level}, target=dark_cave")
    
    action1 = selector.select_action(wm)
    print_action(action1, "  ")
    
    print("\n  💥 Agent saldırıya uğradı! (outcome: -0.8)")
    selector.record_outcome(-0.8, "ambushed_in_cave")
    
    # İkinci karşılaşma
    print("\n  [İKİNCİ KARŞILAŞMA - Aynı durum]")
    wm.tick = 2
    
    action2 = selector.select_action(wm)
    print_action(action2, "  ")
    
    # Üçüncü karşılaşma - korku ekle
    print("\n  [ÜÇÜNCÜ KARŞILAŞMA - Korku durumunda]")
    selector.update_emotional_state({
        'valence': -0.5,
        'arousal': 0.6,
        'dominance': -0.2,
    })
    wm.tick = 3
    
    action3 = selector.select_action(wm)
    print_action(action3, "  ")
    
    print("\n  📊 Öğrenme özeti:")
    stats = selector.get_somatic_stats()
    print(f"     Toplam marker: {stats['total_markers']}")
    if stats['strongest_markers']:
        m = stats['strongest_markers'][0]
        print(f"     En güçlü marker: {m['action']} → valence={m['valence']}")


def demo_positive_reinforcement():
    """Pozitif pekiştirme senaryosu"""
    print_header("SENARYO 2: Pozitif Pekiştirme")
    
    print("""
  Agent ormanda keşif yapıyor...
  Her keşifte ödül buluyor, EXPLORE davranışı güçleniyor.
    """)
    
    somatic = SomaticMarkerSystem()
    selector = SomaticEmotionalActionSelector(somatic_system=somatic)
    
    selector.update_emotional_state({
        'valence': 0.2,
        'arousal': 0.3,
        'dominance': 0.1,
    })
    
    wm = WorkingMemoryState(
        tick=1,
        danger_level=0.1,
        symbols=[],
    )
    
    rewards = [0.4, 0.6, 0.5, 0.7, 0.8]
    
    for i, reward in enumerate(rewards):
        print(f"\n  [KEŞİF #{i+1}]")
        wm.tick = i + 1
        
        action = selector.select_action(wm)
        print_action(action, "  ")
        
        print(f"  🎁 Ödül bulundu! (outcome: +{reward})")
        selector.record_outcome(reward, f"found_treasure_{i+1}")
    
    print("\n  [SON KEŞİF - Güçlenmiş davranış]")
    wm.tick = 10
    final_action = selector.select_action(wm)
    print_action(final_action, "  ")
    
    print("\n  📊 Öğrenme özeti:")
    stats = selector.get_somatic_stats()
    print(f"     Toplam marker: {stats['total_markers']}")
    print(f"     Toplam aktivasyon: {stats['total_activations']}")
    if stats['strongest_markers']:
        for m in stats['strongest_markers'][:2]:
            print(f"     {m['action']}: valence={m['valence']:+.2f}, strength={m['strength']:.2f}")


def demo_conflict_resolution():
    """Çatışma çözümü - pozitif vs negatif deneyim"""
    print_header("SENARYO 3: Çatışan Deneyimler")
    
    print("""
  Agent aynı durumda hem iyi hem kötü deneyimler yaşadı.
  Somatic system nasıl dengeleyecek?
    """)
    
    somatic = SomaticMarkerSystem(learning_rate=0.4)
    selector = SomaticEmotionalActionSelector(somatic_system=somatic)
    
    selector.update_emotional_state({
        'valence': 0.0,
        'arousal': 0.2,
        'dominance': 0.0,
    })
    
    wm = WorkingMemoryState(
        tick=1,
        danger_level=0.3,
        nearest_target=MockTarget("mysterious_chest"),
        symbols=[],
    )
    
    # Deneyim dizisi: +, -, +, -, +
    experiences = [
        (0.6, "treasure"),
        (-0.5, "trap"),
        (0.7, "rare_item"),
        (-0.3, "minor_damage"),
        (0.8, "jackpot"),
    ]
    
    print("  [DENEYİM DİZİSİ]")
    for i, (outcome, desc) in enumerate(experiences):
        wm.tick = i + 1
        action = selector.select_action(wm)
        selector.record_outcome(outcome, desc)
        
        symbol = "🎁" if outcome > 0 else "💥"
        print(f"  {i+1}. {symbol} {desc}: outcome={outcome:+.1f}")
    
    print("\n  [FİNAL KARAR]")
    wm.tick = 10
    final_action = selector.select_action(wm)
    print_action(final_action, "  ")
    
    print("\n  📊 Dengeleme sonucu:")
    stats = selector.get_somatic_stats()
    if stats['strongest_markers']:
        m = stats['strongest_markers'][0]
        print(f"     Net valence: {m['valence']:+.2f} (5 deneyim ortalaması)")
        print(f"     Güç: {m['strength']:.2f}")


def demo_emotion_somatic_interaction():
    """Duygu ve somatic etkileşimi"""
    print_header("SENARYO 4: Duygu × Somatic Etkileşimi")
    
    print("""
  Aynı durum, farklı duygusal durumlar + somatic marker.
  Duygu ve deneyim nasıl birleşiyor?
    """)
    
    somatic = SomaticMarkerSystem()
    selector = SomaticEmotionalActionSelector(somatic_system=somatic)
    
    wm = WorkingMemoryState(
        tick=1,
        danger_level=0.5,
        nearest_target=MockTarget("enemy_camp"),
        symbols=['DANGER_LOW'],
    )
    
    # Önce negatif deneyim oluştur
    selector.update_emotional_state({'valence': 0.0, 'arousal': 0.0, 'dominance': 0.0})
    selector.select_action(wm)
    selector.record_outcome(-0.6, "defeated")
    
    print("  Geçmiş deneyim: enemy_camp'te yenilgi (valence=-0.6)\n")
    
    emotions = [
        ("NÖTR", {'valence': 0.0, 'arousal': 0.0, 'dominance': 0.0}),
        ("KORKU", {'valence': -0.6, 'arousal': 0.7, 'dominance': -0.3}),
        ("HEYECAN", {'valence': 0.7, 'arousal': 0.8, 'dominance': 0.4}),
        ("ÖFKE", {'valence': -0.5, 'arousal': 0.7, 'dominance': 0.5}),
    ]
    
    for emotion_name, emotion_state in emotions:
        print(f"  [{emotion_name}]")
        selector.update_emotional_state(emotion_state)
        wm.tick += 1
        
        action = selector.select_action(wm)
        somatic_bias = action.params.get('somatic_bias', 0)
        
        print(f"    Duygu etkisi: {action.emotional_influence:.2f}")
        print(f"    Somatic bias: {somatic_bias:+.3f}")
        print(f"    → {action.name}\n")


def main():
    print("\n" + "=" * 60)
    print("  UEM SOMATIC MARKER SYSTEM DEMO")
    print("=" * 60)
    print("""
  Damasio'nun Somatic Marker Hypothesis'inden esinlenilmiştir.
  
  Sistem nasıl çalışır:
  1. Eylem yapılır → Sonuç gözlemlenir
  2. Durum + Eylem + Sonuç = Marker kaydedilir
  3. Gelecekte benzer durumda marker aktive olur
  4. Pozitif marker → o eyleme bias (teşvik)
  5. Negatif marker → o eylemden kaçınma bias
  
  Bu, "gut feeling" veya "sezgi"nin mekanik modelidir.
    """)
    
    demo_learning_from_danger()
    demo_positive_reinforcement()
    demo_conflict_resolution()
    demo_emotion_somatic_interaction()
    
    print("\n" + "=" * 60)
    print("  DEMO COMPLETE")
    print("=" * 60)
    print("""
  Sonraki adımlar:
  - Marker persistence (diske kaydetme)
  - Event bus entegrasyonu (gerçek zamanlı)
  - Memory consolidation ile birleşim
    """)


if __name__ == "__main__":
    main()
