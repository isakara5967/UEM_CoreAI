#!/usr/bin/env python3
"""
UEM Ontology Layer 1 - Demo

Bu demo, Katman 1 ontolojisinin temel işlevlerini gösterir:
1. StateVector oluşturma
2. Entity'ler (SELF, OTHER, EVENT)
3. VALUE hesaplamaları (BENEFIT, COST)
4. RELATION fonksiyonları (CAUSES, AFFECTS, SIMILAR)
5. SelfCore entegrasyonu

Author: UEM Project
"""

import sys
sys.path.insert(0, '.')

from dataclasses import dataclass


# =========================================================================
# MOCK CLASSES (Gerçek modüller yerine)
# =========================================================================

@dataclass
class MockWorldState:
    player_health: float = 1.0
    player_energy: float = 1.0
    danger_level: float = 0.0
    tick: int = 0


@dataclass
class MockEmotionCore:
    valence: float = 0.0


# =========================================================================
# DEMO FUNCTIONS
# =========================================================================

def demo_state_vector():
    """Demo 1: StateVector oluşturma"""
    print("\n" + "=" * 60)
    print("  DEMO 1: StateVector Oluşturma")
    print("=" * 60)
    
    from core.ontology.types import build_state_vector
    
    # Senaryo 1: Güvenli durum
    world_safe = MockWorldState(player_health=1.0, player_energy=0.9, danger_level=0.1)
    emotion_happy = MockEmotionCore(valence=0.5)
    
    state_safe = build_state_vector(world_safe, emotion_happy)
    
    print(f"""
  Güvenli Senaryo:
    Health: {world_safe.player_health}, Energy: {world_safe.player_energy}
    Danger: {world_safe.danger_level}, Valence: {emotion_happy.valence}
    
    → StateVector:
      RESOURCE_LEVEL: {state_safe[0]:.2f}
      THREAT_LEVEL:   {state_safe[1]:.2f}
      WELLBEING:      {state_safe[2]:.2f}
    """)
    
    # Senaryo 2: Tehlike durumu
    world_danger = MockWorldState(player_health=0.3, player_energy=0.4, danger_level=0.8)
    emotion_fear = MockEmotionCore(valence=-0.7)
    
    state_danger = build_state_vector(world_danger, emotion_fear)
    
    print(f"""  Tehlike Senaryosu:
    Health: {world_danger.player_health}, Energy: {world_danger.player_energy}
    Danger: {world_danger.danger_level}, Valence: {emotion_fear.valence}
    
    → StateVector:
      RESOURCE_LEVEL: {state_danger[0]:.2f}
      THREAT_LEVEL:   {state_danger[1]:.2f}
      WELLBEING:      {state_danger[2]:.2f}
    """)
    
    return state_safe, state_danger


def demo_entities():
    """Demo 2: Entity oluşturma"""
    print("\n" + "=" * 60)
    print("  DEMO 2: Entity Oluşturma")
    print("=" * 60)
    
    from core.ontology.types import SelfEntity, OtherEntity, Event, Goal
    
    # SELF entity
    self_entity = SelfEntity(
        state_vector=(0.85, 0.15, 0.72),
        history=[],
        goals=[
            Goal(name="survive", target_state=(1.0, 0.0, 1.0), priority=1.0),
            Goal(name="explore", target_state=(0.8, 0.2, 0.8), priority=0.6),
        ]
    )
    
    print(f"""
  SELF Entity:
    State: {self_entity.state_vector}
    Goals: {[g.name for g in self_entity.goals]}
    History: {len(self_entity.history)} events
    """)
    
    # OTHER entity (düşman)
    enemy = OtherEntity(
        id="enemy_goblin",
        observed_state=(0.7, 0.9, 0.3),  # Yüksek tehdit
        predicted_state=(0.6, 0.95, 0.2)  # Daha da tehlikeli olacak
    )
    
    print(f"""  OTHER Entity (Enemy):
    ID: {enemy.id}
    Observed State: {enemy.observed_state}
    Predicted State: {enemy.predicted_state}
    """)
    
    # EVENT
    attack_event = Event(
        source="OTHER:enemy_goblin",
        target="SELF",
        effect=(-0.2, 0.3, -0.25),  # Resource loss, threat up, wellbeing down
        timestamp=1234.56
    )
    
    print(f"""  EVENT (Attack):
    Source: {attack_event.source}
    Target: {attack_event.target}
    Effect: {attack_event.effect}
    Time: {attack_event.timestamp}
    """)
    
    return self_entity, enemy, attack_event


def demo_values(state_before, state_after):
    """Demo 3: VALUE hesaplamaları"""
    print("\n" + "=" * 60)
    print("  DEMO 3: VALUE Hesaplamaları")
    print("=" * 60)
    
    from core.ontology.types import compute_benefit, compute_cost
    
    # State transition
    print(f"""
  State Transition:
    Before: {state_before}
    After:  {state_after}
    """)
    
    # BENEFIT (wellbeing artışı)
    benefit = compute_benefit(state_before[2], state_after[2])
    
    # COST (resource kaybı)
    cost = compute_cost(state_before[0], state_after[0])
    
    print(f"""  VALUE Calculations:
    BENEFIT (wellbeing gain): {benefit:.3f}
    COST (resource loss):     {cost:.3f}
    
    Net assessment: {"Positive" if benefit > cost else "Negative" if cost > benefit else "Neutral"}
    """)
    
    return benefit, cost


def demo_relations(state_safe, state_danger):
    """Demo 4: RELATION fonksiyonları"""
    print("\n" + "=" * 60)
    print("  DEMO 4: RELATION Fonksiyonları")
    print("=" * 60)
    
    from core.ontology.types import similar, causes, Event
    
    # SIMILAR: İki state arasındaki benzerlik
    similarity = similar(state_safe, state_danger)
    
    print(f"""
  SIMILAR Fonksiyonu:
    State A (safe):   {state_safe}
    State B (danger): {state_danger}
    
    Cosine Similarity: {similarity:.3f}
    Interpretation: {"Very similar" if similarity > 0.9 else "Somewhat similar" if similarity > 0.5 else "Different"}
    """)
    
    # CAUSES: Event'in etkisi
    event = Event(
        source="ENVIRONMENT",
        target="SELF",
        effect=(-0.1, 0.2, -0.15),
        timestamp=0
    )
    
    delta = causes(event)
    
    print(f"""  CAUSES Fonksiyonu:
    Event: {event.source} → {event.target}
    
    StateDelta: {delta}
      Resource change: {delta[0]:+.2f}
      Threat change:   {delta[1]:+.2f}
      Wellbeing change:{delta[2]:+.2f}
    """)
    
    return similarity


def demo_empathy_scenario():
    """Demo 5: Empati senaryosu - SIMILAR kullanımı"""
    print("\n" + "=" * 60)
    print("  DEMO 5: Empati Senaryosu")
    print("=" * 60)
    
    from core.ontology.types import similar, SelfEntity, OtherEntity
    
    # UEM'in mevcut durumu
    self_state = (0.7, 0.3, 0.6)  # Orta kaynak, düşük tehdit, iyi wellbeing
    
    # Gözlemlenen diğer agent
    other_state = (0.3, 0.8, 0.2)  # Düşük kaynak, yüksek tehdit, düşük wellbeing
    
    # UEM'in geçmiş deneyimi (tehlikeli anı)
    past_experience = (0.35, 0.75, 0.25)
    
    # Benzerlik hesapla
    similarity_self_other = similar(self_state, other_state)
    similarity_past_other = similar(past_experience, other_state)
    
    print(f"""
  Empati Analizi:
  
  SELF current state:     {self_state}
  OTHER observed state:   {other_state}
  SELF past experience:   {past_experience}
  
  Similarity (self ↔ other):        {similarity_self_other:.3f}
  Similarity (past exp ↔ other):    {similarity_past_other:.3f}
    """)
    
    # Empati kararı
    if similarity_past_other > 0.8:
        empathy_level = "HIGH"
        reasoning = "OTHER's state çok benzer bir deneyimimi hatırlatıyor"
    elif similarity_past_other > 0.5:
        empathy_level = "MEDIUM"
        reasoning = "OTHER's state kısmen tanıdık geliyor"
    else:
        empathy_level = "LOW"
        reasoning = "OTHER's state benim deneyimlerimden farklı"
    
    print(f"""  Empati Sonucu:
    Level: {empathy_level}
    Reasoning: {reasoning}
    
    → Eğer empati yüksekse, UEM diğer agent'a yardım etmeye daha meyilli olabilir
    """)


def demo_self_core_integration():
    """Demo 6: SelfCore entegrasyonu"""
    print("\n" + "=" * 60)
    print("  DEMO 6: SelfCore Ontology Entegrasyonu")
    print("=" * 60)
    
    from core.self.self_core import SelfCore
    
    # Mock emotion system
    emotion = MockEmotionCore(valence=0.3)
    
    # SelfCore oluştur (minimal)
    core = SelfCore(
        memory_system=None,
        emotion_system=emotion,
        cognition_system=None,
        planning_system=None,
        metamind_system=None,
        ethmor_system=None,
    )
    
    print("""
  SelfCore oluşturuldu (start() çağrılmadan)
    """)
    
    # Ontology API'lerini test et
    state_vector = core.get_state_vector()
    print(f"  get_state_vector(): {state_vector}")
    
    self_entity = core.build_self_entity()
    print(f"  build_self_entity(): {self_entity}")
    
    # World snapshot ile güncelle
    world_snapshot = {
        'player_health': 0.8,
        'player_energy': 0.7,
        'danger_level': 0.2,
    }
    
    core._update_ontology_state_vector(world_snapshot)
    
    updated_state = core.get_state_vector()
    print(f"""
  World snapshot ile güncelleme sonrası:
    Snapshot: {world_snapshot}
    State Vector: {updated_state}
    """)
    
    if updated_state:
        print(f"""  Detay:
    RESOURCE_LEVEL: {updated_state[0]:.2f} (health+energy)/2
    THREAT_LEVEL:   {updated_state[1]:.2f} (danger_level)
    WELLBEING:      {updated_state[2]:.2f} (valence+1)/2
    """)


# =========================================================================
# MAIN
# =========================================================================

def main():
    print("\n" + "=" * 60)
    print("  UEM ONTOLOGY LAYER 1 - DEMO")
    print("  12 Core Concepts: ENTITY / STATE / VALUE / RELATION")
    print("=" * 60)
    
    try:
        # Demo 1: StateVector
        state_safe, state_danger = demo_state_vector()
        
        # Demo 2: Entities
        self_entity, enemy, event = demo_entities()
        
        # Demo 3: Values
        demo_values(state_safe, state_danger)
        
        # Demo 4: Relations
        demo_relations(state_safe, state_danger)
        
        # Demo 5: Empathy scenario
        demo_empathy_scenario()
        
        # Demo 6: SelfCore integration
        demo_self_core_integration()
        
        print("\n" + "=" * 60)
        print("  ✓ Tüm demolar başarıyla tamamlandı!")
        print("=" * 60 + "\n")
        
    except ImportError as e:
        print(f"\n  ✗ Import hatası: {e}")
        print("    Ontology modülü henüz entegre edilmemiş olabilir.")
        print("    core/ontology/__init__.py dosyasını kontrol edin.\n")
        return 1
    
    except Exception as e:
        print(f"\n  ✗ Hata: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
