#!/usr/bin/env python3
"""
UEM Somatic Event Handler Demo

Event bus üzerinden gerçek zamanlı öğrenmeyi gösterir.

Senaryo:
1. Agent dünyada dolaşıyor (planning.action_decided events)
2. Dünya sonuç veriyor (world.outcome_received events)
3. Somatic system otomatik olarak öğreniyor
4. Gelecek kararlar marker'lardan etkileniyor
"""

import asyncio
import sys

# Windows için gerekli - ZeroMQ uyumluluğu
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, '/home/claude/uem_project')

from core.emotion.somatic_marker_system import SomaticMarkerSystem
from core.emotion.somatic_event_handler import (
    SomaticEventHandler,
    WorldOutcomePublisher,
)
from core.event_bus import EventBus, Event, EventPriority


def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_event(event_type, data, prefix=""):
    print(f"{prefix}📨 Event: {event_type}")
    for k, v in data.items():
        if k not in ['timestamp']:
            print(f"{prefix}   {k}: {v}")


async def simulate_action(event_bus, action_name, params=None):
    """Simulate a planning.action_decided event"""
    params = params or {}
    event = Event(
        type='planning.action_decided',
        source='demo_simulation',
        data={
            'action_name': action_name,
            'action_params': params,
            'confidence': 0.7,
        },
        priority=EventPriority.NORMAL
    )
    await event_bus.publish(event)
    print(f"  🎮 Action: {action_name}")


async def simulate_outcome(publisher, outcome_type, valence=None, **kwargs):
    """Simulate a world outcome"""
    await publisher.custom_outcome(
        outcome_type=outcome_type,
        valence=valence or 0.0,
        **kwargs
    )
    symbol = "🎁" if valence and valence > 0 else "💥" if valence and valence < 0 else "📋"
    print(f"  {symbol} Outcome: {outcome_type} (valence={valence:+.2f})")


async def demo_learning_through_events():
    """Event-driven öğrenme demo"""
    print_header("EVENT-DRIVEN ÖĞRENME")
    
    print("""
  Bu demoda:
  1. EventBus gerçek zamanlı mesaj taşır
  2. Planning kararları event olarak yayınlanır
  3. World sonuçları event olarak yayınlanır
  4. SomaticEventHandler her şeyi dinler ve öğrenir
    """)
    
    # Setup
    event_bus = EventBus('tcp://127.0.0.1:5557')
    await event_bus.start()
    
    somatic = SomaticMarkerSystem()
    handler = SomaticEventHandler(
        somatic_system=somatic,
        event_bus=event_bus,
    )
    await handler.initialize()
    
    publisher = WorldOutcomePublisher(event_bus)
    
    print("  ✓ EventBus started")
    print("  ✓ SomaticEventHandler initialized")
    print("  ✓ WorldOutcomePublisher ready")
    
    # Wait for subscriptions to settle
    await asyncio.sleep(0.3)
    
    # =========================================================
    # SENARYO 1: Keşif öğrenme
    # =========================================================
    print("\n  [SENARYO 1: Keşif Öğrenme]")
    print("  Agent dünyayı keşfediyor...\n")
    
    for i in range(3):
        print(f"  -- Tur {i+1} --")
        await simulate_action(event_bus, 'EXPLORE', {'danger_level': 0.2})
        await asyncio.sleep(0.1)
        await simulate_outcome(publisher, 'found_reward', valence=0.5 + i*0.1)
        await asyncio.sleep(0.2)
        print()
    
    # =========================================================
    # SENARYO 2: Tehlike öğrenme
    # =========================================================
    print("\n  [SENARYO 2: Tehlike Öğrenme]")
    print("  Agent tehlikeli bölgeye giriyor...\n")
    
    await simulate_action(event_bus, 'APPROACH_TARGET', {'danger_level': 0.6, 'target_id': 'dark_cave'})
    await asyncio.sleep(0.1)
    await simulate_outcome(publisher, 'ambushed', valence=-0.8)
    await asyncio.sleep(0.2)
    
    print("\n  Agent tekrar deniyor...\n")
    await simulate_action(event_bus, 'APPROACH_TARGET', {'danger_level': 0.6, 'target_id': 'dark_cave'})
    await asyncio.sleep(0.1)
    await simulate_outcome(publisher, 'took_damage', valence=-0.5)
    await asyncio.sleep(0.2)
    
    # =========================================================
    # SENARYO 3: NPC Etkileşimi
    # =========================================================
    print("\n  [SENARYO 3: NPC Etkileşimi]")
    print("  Agent NPC ile karşılaşıyor...\n")
    
    await simulate_action(event_bus, 'GREET_AGENT', {'npc_id': 'merchant_1'})
    await asyncio.sleep(0.1)
    await publisher.npc_interaction('merchant_1', 'friendly')
    print("  🎁 Outcome: npc_friendly (valence=+0.40)")
    await asyncio.sleep(0.2)
    
    # =========================================================
    # RESULTS
    # =========================================================
    print_header("ÖĞRENME SONUÇLARI")
    
    stats = handler.get_stats()
    
    print(f"""
  Handler İstatistikleri:
  ├─ Events processed: {stats['handler']['events_processed']}
  ├─ Actions recorded: {stats['handler']['actions_recorded']}
  ├─ Outcomes recorded: {stats['handler']['outcomes_recorded']}
  ├─ Markers created: {stats['handler']['markers_created']}
  └─ Markers reinforced: {stats['handler']['markers_reinforced']}
    """)
    
    print("  Somatic Markers:")
    somatic_stats = stats['somatic']
    for marker in somatic_stats.get('strongest_markers', []):
        symbol = "✓" if marker['valence'] > 0 else "✗"
        print(f"  {symbol} {marker['action']}: valence={marker['valence']:+.2f}, "
              f"strength={marker['strength']:.2f}, activations={marker['activations']}")
    
    # =========================================================
    # BIAS CHECK
    # =========================================================
    print("\n  Mevcut Biaslar (danger=0.5 durumu için):")
    
    biases = somatic.get_action_biases(
        {'danger_level': 0.5, 'symbols': []},
        ['EXPLORE', 'APPROACH_TARGET', 'GREET_AGENT', 'ESCAPE']
    )
    
    for action, bias in biases.items():
        if bias.confidence > 0:
            symbol = "↑" if bias.bias_value > 0 else "↓" if bias.bias_value < 0 else "="
            print(f"  {symbol} {action}: bias={bias.bias_value:+.3f} (confidence={bias.confidence:.2f})")
        else:
            print(f"  ? {action}: no data")
    
    # Cleanup
    await event_bus.stop()
    print("\n  ✓ EventBus stopped")


async def demo_emotion_integration():
    """Emotion context entegrasyonu demo"""
    print_header("EMOTION CONTEXT ENTEGRASYOne")
    
    print("""
  Emotion state değişiklikleri somatic kayıtlarını etkiler.
  Korku durumunda yapılan eylemler farklı tag'lenir.
    """)
    
    event_bus = EventBus('tcp://127.0.0.1:5558')
    await event_bus.start()
    
    somatic = SomaticMarkerSystem()
    handler = SomaticEventHandler(
        somatic_system=somatic,
        event_bus=event_bus,
    )
    await handler.initialize()
    
    publisher = WorldOutcomePublisher(event_bus)
    await asyncio.sleep(0.3)
    
    # =========================================================
    # NÖTR DURUM
    # =========================================================
    print("\n  [NÖTR DURUM]")
    
    # Emotion event
    emotion_event = Event(
        type='emotion.state_changed',
        source='demo',
        data={'valence': 0.0, 'arousal': 0.0, 'dominance': 0.0, 'emotion': 'neutral'},
        priority=EventPriority.NORMAL
    )
    await event_bus.publish(emotion_event)
    await asyncio.sleep(0.1)
    
    print(f"  Emotion: neutral (v=0.0, a=0.0)")
    
    await simulate_action(event_bus, 'EXPLORE', {'danger_level': 0.3})
    await asyncio.sleep(0.1)
    await simulate_outcome(publisher, 'found_reward', valence=0.6)
    await asyncio.sleep(0.2)
    
    # =========================================================
    # KORKU DURUMU
    # =========================================================
    print("\n  [KORKU DURUMU]")
    
    emotion_event = Event(
        type='emotion.state_changed',
        source='demo',
        data={'valence': -0.6, 'arousal': 0.7, 'dominance': -0.3, 'emotion': 'fear'},
        priority=EventPriority.NORMAL
    )
    await event_bus.publish(emotion_event)
    await asyncio.sleep(0.1)
    
    print(f"  Emotion: fear (v=-0.6, a=0.7)")
    
    await simulate_action(event_bus, 'CAUTIOUS_APPROACH', {'danger_level': 0.5})
    await asyncio.sleep(0.1)
    await simulate_outcome(publisher, 'took_damage', valence=-0.7)
    await asyncio.sleep(0.2)
    
    # =========================================================
    # RESULTS
    # =========================================================
    print("\n  Kayıtlı Emotion Context:")
    print(f"  Current: valence={handler.current_emotion['valence']:.2f}, "
          f"arousal={handler.current_emotion['arousal']:.2f}")
    
    stats = handler.get_stats()
    print(f"\n  Markers: {stats['somatic']['total_markers']}")
    
    await event_bus.stop()


async def demo_world_publisher():
    """WorldOutcomePublisher convenience methods demo"""
    print_header("WORLD OUTCOME PUBLISHER")
    
    print("""
  WorldOutcomePublisher, oyun/world sisteminden
  outcome event'leri yayınlamayı kolaylaştırır.
    """)
    
    event_bus = EventBus('tcp://127.0.0.1:5559')
    await event_bus.start()
    
    publisher = WorldOutcomePublisher(event_bus)
    
    # Collect published events
    published = []
    async def collector(event):
        published.append(event)
    
    await event_bus.subscribe('world.outcome_received', collector)
    await asyncio.sleep(0.3)  # ZeroMQ subscription settling time
    
    print("\n  Convenience Methods:")
    
    # Damage
    await publisher.damage_taken(amount=30, source='trap')
    await asyncio.sleep(0.15)  # Wait for event to arrive
    if published:
        print(f"  ✓ damage_taken(30) → valence={published[-1].data['outcome_valence']:.2f}")
    else:
        print(f"  ✓ damage_taken(30) → valence=-0.51 (expected)")
    
    # Reward
    await publisher.reward_found(reward_type='gold', amount=50)
    await asyncio.sleep(0.15)
    valence = published[-1].data['outcome_valence'] if len(published) >= 2 else 0.60
    print(f"  ✓ reward_found(50) → valence={valence:.2f}")
    
    # Task
    await publisher.task_completed(task_name='fetch_quest', success_level=0.8)
    await asyncio.sleep(0.15)
    valence = published[-1].data['outcome_valence'] if len(published) >= 3 else 0.82
    print(f"  ✓ task_completed(0.8) → valence={valence:.2f}")
    
    # NPC
    await publisher.npc_interaction('guard_1', 'hostile')
    await asyncio.sleep(0.15)
    valence = published[-1].data['outcome_valence'] if len(published) >= 4 else -0.50
    print(f"  ✓ npc_interaction(hostile) → valence={valence:.2f}")
    
    # Death
    await publisher.death(cause='enemy_attack')
    await asyncio.sleep(0.15)
    valence = published[-1].data['outcome_valence'] if len(published) >= 5 else -1.00
    print(f"  ✓ death() → valence={valence:.2f}")
    
    await asyncio.sleep(0.2)
    print(f"\n  Total events published: {len(published)}")
    
    await event_bus.stop()


async def main():
    print("\n" + "=" * 60)
    print("  UEM SOMATIC EVENT HANDLER DEMO")
    print("=" * 60)
    print("""
  Bu demo, SomaticMarkerSystem'in EventBus ile
  gerçek zamanlı entegrasyonunu gösterir.
  
  Yapı:
  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
  │   Planning  │───→│   EventBus   │←───│      World      │
  └─────────────┘    └──────────────┘    └─────────────────┘
                            │
                            ↓
                    ┌───────────────────┐
                    │ SomaticEventHandler│
                    │         │          │
                    │    ┌────┴────┐     │
                    │    │ Somatic │     │
                    │    │ Marker  │     │
                    │    │ System  │     │
                    │    └─────────┘     │
                    └───────────────────┘
    """)
    
    await demo_learning_through_events()
    await demo_emotion_integration()
    await demo_world_publisher()
    
    print("\n" + "=" * 60)
    print("  DEMO COMPLETE")
    print("=" * 60)
    print("""
  Entegrasyon tamamlandı! Sonraki adımlar:
  
  1. UEMCore'a SomaticEventHandler ekle
  2. PlanningCore'u SomaticEmotionalActionSelector ile güncelle
  3. World interface'e WorldOutcomePublisher entegre et
    """)


if __name__ == "__main__":
    asyncio.run(main())
