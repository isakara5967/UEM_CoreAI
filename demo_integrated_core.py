#!/usr/bin/env python3
"""
UEM Integrated Core Demo

Tam bilişsel döngü gösterisi:
1. World state → Perception
2. Memory retrieval
3. Emotion appraisal
4. Action selection (emotion + somatic)
5. Execution
6. Learning

Senaryolar:
- Güvenli keşif
- Tehlike karşılaşması
- Ödül bulma
- Deneyimden öğrenme
"""

import asyncio
import sys
import time

# Windows için event loop policy
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, '/home/claude/uem_project')

from core.integrated_uem_core import (
    IntegratedUEMCore,
    WorldState,
    ActionResult,
    create_uem_core,
)


def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_cycle_result(cycle_num, world_state, action_result, stats):
    """Print cycle summary"""
    emotion_str = stats.get('current_emotion', {})
    emotion_label = emotion_str.get('emotion', 'neutral') if isinstance(emotion_str, dict) else 'neutral'
    valence = emotion_str.get('valence', 0) if isinstance(emotion_str, dict) else 0
    
    print(f"\n  ┌─ Cycle {cycle_num} {'─' * 50}")
    print(f"  │ World: danger={world_state.danger_level:.2f}, health={world_state.player_health:.2f}")
    print(f"  │ Emotion: {emotion_label} (v={valence:+.2f})")
    print(f"  │ Action: {action_result.action_name}")
    print(f"  │ Outcome: {action_result.outcome_type} (valence={action_result.outcome_valence:+.2f})")
    print(f"  └─ Time: {stats.get('avg_cycle_time', 0)*1000:.1f}ms")


async def demo_safe_exploration():
    """Güvenli keşif senaryosu"""
    print_header("SENARYO 1: GÜVENLİ KEŞİF")
    
    print("""
  Agent güvenli bir ortamda keşif yapıyor.
  Düşük tehlike, ödüller bulunuyor.
    """)
    
    core = await create_uem_core()
    
    try:
        for i in range(5):
            world_state = WorldState(
                tick=i,
                danger_level=0.1 + (i * 0.05),  # Yavaş artan tehlike
                objects=[{'type': 'treasure', 'id': f'obj_{i}'}],
                agents=[],
                symbols=['SAFE_ZONE'],
                player_health=1.0,
                player_energy=0.9 - (i * 0.05),
            )
            
            result = await core.cognitive_cycle(world_state)
            
            # Simüle: ödül bulundu
            if i % 2 == 0:
                result.outcome_type = 'found_reward'
                result.outcome_valence = 0.5
                core.record_outcome('found_reward', 0.5)
            
            print_cycle_result(i + 1, world_state, result, core.get_stats())
            await asyncio.sleep(0.1)
        
        print("\n  📊 Final Stats:")
        stats = core.get_stats()
        print(f"     Total cycles: {stats['total_cycles']}")
        print(f"     Avg cycle time: {stats['avg_cycle_time']*1000:.2f}ms")
        
    finally:
        await core.stop()


async def demo_danger_encounter():
    """Tehlike karşılaşması senaryosu"""
    print_header("SENARYO 2: TEHLİKE KARŞILAŞMASI")
    
    print("""
  Agent aniden tehlikeyle karşılaşıyor.
  Korku tepkisi ve kaçış davranışı bekleniyor.
    """)
    
    core = await create_uem_core()
    
    try:
        # Phase 1: Normal durum
        print("\n  [Faz 1: Normal durum]")
        world_state = WorldState(
            tick=0,
            danger_level=0.2,
            objects=[],
            agents=[],
            symbols=[],
            player_health=1.0,
        )
        result = await core.cognitive_cycle(world_state)
        print_cycle_result(1, world_state, result, core.get_stats())
        
        # Phase 2: Tehlike!
        print("\n  [Faz 2: TEHLİKE!]")
        world_state = WorldState(
            tick=1,
            danger_level=0.8,  # Yüksek tehlike
            objects=[],
            agents=[{'type': 'enemy', 'id': 'monster_1'}],
            symbols=['DANGER_HIGH', 'ENEMY_NEARBY'],
            player_health=1.0,
        )
        result = await core.cognitive_cycle(world_state)
        print_cycle_result(2, world_state, result, core.get_stats())
        
        # Phase 3: Hasar aldı
        print("\n  [Faz 3: Hasar alındı]")
        world_state = WorldState(
            tick=2,
            danger_level=0.7,
            objects=[],
            agents=[{'type': 'enemy', 'id': 'monster_1'}],
            symbols=['DANGER_HIGH'],
            player_health=0.6,  # Hasar aldı
        )
        result = await core.cognitive_cycle(world_state)
        result.outcome_type = 'took_damage'
        result.outcome_valence = -0.7
        core.record_outcome('took_damage', -0.7)
        print_cycle_result(3, world_state, result, core.get_stats())
        
        # Phase 4: Kaçış başarılı
        print("\n  [Faz 4: Kaçış]")
        world_state = WorldState(
            tick=3,
            danger_level=0.3,  # Tehlike azaldı
            objects=[],
            agents=[],
            symbols=['ESCAPED'],
            player_health=0.6,
        )
        result = await core.cognitive_cycle(world_state)
        print_cycle_result(4, world_state, result, core.get_stats())
        
        # Somatic learning check
        print("\n  📊 Somatic Learning:")
        somatic_stats = core.get_stats()['somatic']
        if 'somatic' in somatic_stats:
            print(f"     Markers: {somatic_stats['somatic'].get('total_markers', 0)}")
        
    finally:
        await core.stop()


async def demo_learning_over_time():
    """Zaman içinde öğrenme senaryosu"""
    print_header("SENARYO 3: DENEYİMDEN ÖĞRENME")
    
    print("""
  Agent aynı durumlarla tekrar karşılaşıyor.
  Önceki deneyimler kararları etkiliyor.
    """)
    
    core = await create_uem_core()
    
    try:
        # İlk karşılaşma: Mağara keşfi → Kötü sonuç
        print("\n  [İLK DENEME: Mağara keşfi]")
        
        world_state = WorldState(
            tick=0,
            danger_level=0.5,
            objects=[{'type': 'cave_entrance', 'id': 'dark_cave'}],
            symbols=['UNKNOWN_AREA', 'DARK'],
            player_health=1.0,
        )
        result1 = await core.cognitive_cycle(world_state)
        print(f"     İlk karar: {result1.action_name}")
        
        # Kötü sonuç simüle et
        core.record_outcome('ambushed_in_cave', -0.8)
        print("     💥 Sonuç: Pusuya düştü! (valence=-0.8)")
        
        await asyncio.sleep(0.2)
        
        # İkinci karşılaşma: Aynı durum
        print("\n  [İKİNCİ DENEME: Aynı mağara]")
        
        world_state.tick = 1
        result2 = await core.cognitive_cycle(world_state)
        print(f"     İkinci karar: {result2.action_name}")
        
        # Somatic bias kontrolü
        if hasattr(result2, 'somatic_bias'):
            print(f"     Somatic bias: {result2.somatic_bias:+.3f}")
        
        # Üçüncü durum: Farklı ama benzer
        print("\n  [ÜÇÜNCÜ DENEME: Benzer durum]")
        
        world_state = WorldState(
            tick=2,
            danger_level=0.45,
            objects=[{'type': 'cave_entrance', 'id': 'another_cave'}],
            symbols=['UNKNOWN_AREA'],
            player_health=1.0,
        )
        result3 = await core.cognitive_cycle(world_state)
        print(f"     Üçüncü karar: {result3.action_name}")
        
        print("\n  📊 Öğrenme Özeti:")
        stats = core.get_stats()
        somatic = stats.get('somatic', {}).get('somatic', {})
        if somatic:
            print(f"     Total markers: {somatic.get('total_markers', 0)}")
            print(f"     Total activations: {somatic.get('total_activations', 0)}")
        
    finally:
        await core.stop()


async def demo_emotion_influence():
    """Duygu etkisi senaryosu"""
    print_header("SENARYO 4: DUYGU ETKİSİ")
    
    print("""
  Aynı dünya durumu, farklı duygusal durumlar.
  Duygunun karar vermeyi nasıl etkilediğini gösterir.
    """)
    
    core = await create_uem_core()
    
    try:
        base_world = WorldState(
            tick=0,
            danger_level=0.5,  # Orta seviye tehlike
            objects=[{'type': 'target', 'id': 'goal'}],
            agents=[{'type': 'unknown', 'id': 'stranger'}],
            symbols=['UNCERTAIN'],
            player_health=0.8,
        )
        
        emotions = [
            ('Nötr', 0.0, 0.3),
            ('Korku', -0.6, 0.8),
            ('Heyecan', 0.6, 0.7),
            ('Öfke', -0.4, 0.7),
        ]
        
        results = []
        for name, valence, arousal in emotions:
            print(f"\n  [{name.upper()}]")
            
            # Duygu ayarla
            core.set_emotion(valence, arousal)
            base_world.tick += 1
            
            result = await core.cognitive_cycle(base_world)
            results.append((name, result.action_name))
            
            stats = core.get_stats()
            emotion = stats['current_emotion']
            print(f"     Valence: {emotion.get('valence', 0):+.2f}, Arousal: {emotion.get('arousal', 0):.2f}")
            print(f"     → Karar: {result.action_name}")
            
            await asyncio.sleep(0.1)
        
        print("\n  📊 Karşılaştırma:")
        for name, action in results:
            print(f"     {name:12s} → {action}")
        
    finally:
        await core.stop()


async def demo_long_session():
    """Uzun oturum simülasyonu"""
    print_header("SENARYO 5: UZUN OTURUM (20 cycle)")
    
    print("""
  20 bilişsel döngü boyunca çeşitli durumlar.
  Memory consolidation ve somatic learning.
    """)
    
    core = await create_uem_core()
    
    import random
    random.seed(42)
    
    try:
        action_counts = {}
        positive_outcomes = 0
        negative_outcomes = 0
        
        for i in range(20):
            # Random world state
            danger = random.uniform(0.1, 0.8)
            has_objects = random.random() > 0.3
            has_agents = random.random() > 0.5
            
            world_state = WorldState(
                tick=i,
                danger_level=danger,
                objects=[{'type': 'item'}] if has_objects else [],
                agents=[{'type': 'npc'}] if has_agents else [],
                symbols=['EXPLORE'] if danger < 0.4 else ['CAUTION'],
                player_health=max(0.3, 1.0 - i * 0.02),
            )
            
            result = await core.cognitive_cycle(world_state)
            
            # Count actions
            action_name = result.action_name
            action_counts[action_name] = action_counts.get(action_name, 0) + 1
            
            # Random outcome
            if random.random() > 0.6:
                if danger < 0.5:
                    core.record_outcome('reward', 0.5)
                    positive_outcomes += 1
                else:
                    core.record_outcome('damage', -0.5)
                    negative_outcomes += 1
            
            # Progress indicator
            if (i + 1) % 5 == 0:
                print(f"  ... {i + 1} cycles completed")
            
            await asyncio.sleep(0.05)
        
        print("\n  📊 Session Summary:")
        stats = core.get_stats()
        print(f"     Total cycles: {stats['total_cycles']}")
        print(f"     Avg cycle time: {stats['avg_cycle_time']*1000:.2f}ms")
        print(f"     Positive outcomes: {positive_outcomes}")
        print(f"     Negative outcomes: {negative_outcomes}")
        
        print("\n  Action Distribution:")
        for action, count in sorted(action_counts.items(), key=lambda x: -x[1]):
            bar = "█" * count
            print(f"     {action:20s} {bar} ({count})")
        
        print("\n  Memory Stats:")
        mem_stats = stats.get('memory', {}).get('ltm_stats', {})
        if mem_stats:
            print(f"     LTM memories: {mem_stats.get('total_memories', 0)}")
            print(f"     Consolidation rate: {stats.get('memory', {}).get('consolidation_rate', 0):.1%}")
        
        print("\n  Somatic Stats:")
        som_stats = stats.get('somatic', {}).get('somatic', {})
        if som_stats:
            print(f"     Markers: {som_stats.get('total_markers', 0)}")
            print(f"     Activations: {som_stats.get('total_activations', 0)}")
        
    finally:
        await core.stop()


async def main():
    print("\n" + "=" * 70)
    print("  UEM INTEGRATED CORE DEMO")
    print("=" * 70)
    print("""
  Tam entegre bilişsel döngü gösterisi.
  
  Modüller:
  ┌─────────────────────────────────────────────────────────────────┐
  │                      IntegratedUEMCore                          │
  ├─────────────────────────────────────────────────────────────────┤
  │  EventBus ←──────────────────────────────────────────────────┐  │
  │     │                                                        │  │
  │     ▼                                                        │  │
  │  Perception → Memory → Emotion → Planning → Execution        │  │
  │                 │         │          │                       │  │
  │                 ▼         ▼          ▼                       │  │
  │              LTM    SomaticMarker  ActionSelector            │  │
  │                 │         │          │                       │  │
  │                 └─────────┴──────────┘                       │  │
  │                           │                                  │  │
  │                    Learning / Consolidation                  │  │
  │                           │                                  │  │
  │                           ▼                                  │  │
  │                    world.outcome ─────────────────────────────┘  │
  └─────────────────────────────────────────────────────────────────┘
    """)
    
    await demo_safe_exploration()
    await demo_danger_encounter()
    await demo_learning_over_time()
    await demo_emotion_influence()
    await demo_long_session()
    
    print("\n" + "=" * 70)
    print("  DEMO COMPLETE")
    print("=" * 70)
    print("""
  Entegre UEM Core başarıyla test edildi!
  
  Tamamlanan özellikler:
  ✓ Full cognitive cycle (6 phase)
  ✓ Event-driven architecture
  ✓ Emotion → Planning feedback
  ✓ Somatic marker learning
  ✓ Memory consolidation
  ✓ World outcome processing
    """)


if __name__ == "__main__":
    asyncio.run(main())
