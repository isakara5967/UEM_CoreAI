"""
UEM Demo: Global Workspace Entegrasyonu

Bu demo şunları gösterir:
1. Coalition competition
2. Conscious broadcast
3. Subscriber'lara yayılma
4. Conscious content → Planning etkisi

Author: UEM Project
"""

import asyncio
import logging
import sys
from dataclasses import dataclass
from typing import List

# Path setup
sys.path.insert(0, '/home/claude/uem')

from core.consciousness.global_workspace import (
    WorkspaceManager,
    ContentType,
    BroadcastMessage,
    Codelet,
    Coalition,
)
from core.integrated_uem_core import (
    IntegratedUEMCore,
    WorldState,
    ActionResult,
    create_uem_core,
)


# =========================================================================
# LOGGING SETUP
# =========================================================================

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(name)-25s │ %(message)s',
    )
    # Reduce noise
    logging.getLogger("WorkspaceManager.GW").setLevel(logging.WARNING)


# =========================================================================
# DEMO SCENARIOS
# =========================================================================

async def demo_basic_workspace():
    """Demo 1: Temel Workspace Cycle"""
    print("\n" + "=" * 70)
    print("  DEMO 1: BASIC WORKSPACE CYCLE")
    print("=" * 70)
    print("""
  Context verilir → Codelet'ler coalition üretir → Yarışma → Broadcast
    """)
    
    manager = WorkspaceManager(
        competition_threshold=0.3,
        logger=logging.getLogger("Demo1"),
    )
    
    # Test context - düşük tehlike
    context1 = {
        'perception': {
            'danger_level': 0.2,
            'symbols': ['TREE', 'ROCK'],
        },
        'emotion': {'arousal': 0.3, 'valence': 0.0},
        'agent_state': {'health': 0.9, 'energy': 0.8},
        'active_goals': [],
    }
    
    print("\n  [Context: Safe environment, no goals]")
    msg1 = await manager.cycle(context1)
    
    if msg1:
        print(f"  ✓ Broadcast: {msg1.content_type.value}")
        print(f"    Content: {msg1.content}")
    else:
        print("  ○ No broadcast (below threshold)")
    
    # Test context - yüksek tehlike
    context2 = {
        'perception': {
            'danger_level': 0.8,
            'symbols': ['ENEMY', 'FIRE'],
        },
        'emotion': {'arousal': 0.7, 'valence': -0.5, 'current': 'fear'},
        'agent_state': {'health': 0.4, 'energy': 0.6},
        'active_goals': [{'name': 'survive', 'priority': 0.9}],
    }
    
    print("\n  [Context: High danger, low health, survival goal]")
    msg2 = await manager.cycle(context2)
    
    if msg2:
        print(f"  ✓ Broadcast: {msg2.content_type.value} (priority: {msg2.priority.value})")
        print(f"    Content: {msg2.content}")
    
    print(f"\n  Stats: {manager.get_stats()['manager']}")


async def demo_broadcast_subscribers():
    """Demo 2: Broadcast → Subscriber yayılımı"""
    print("\n" + "=" * 70)
    print("  DEMO 2: BROADCAST TO SUBSCRIBERS")
    print("=" * 70)
    print("""
  Broadcast mesajları 4 modüle yayılır:
  - MemoryModule: Consolidation trigger
  - EmotionModule: Arousal modulation
  - PlanningModule: Conscious context
  - SelfModule: Meta-cognition tracking
    """)
    
    core = await create_uem_core(
        config={'tick_interval': 0.01},
        logger=logging.getLogger("Demo2"),
    )
    
    # Danger scenario
    danger_state = WorldState(
        tick=1,
        danger_level=0.75,
        symbols=['DANGER', 'ENEMY'],
        player_health=0.5,
        player_energy=0.7,
    )
    
    print("\n  [Running cognitive cycle with danger...]")
    result = await core.cognitive_cycle(danger_state)
    
    print(f"\n  Results:")
    print(f"    Action taken: {result.action_name}")
    print(f"    Conscious content: {result.conscious_content}")
    print(f"    Emotion: {result.metadata['emotion']}")
    
    # Subscriber stats
    print(f"\n  Subscriber Activity:")
    print(f"    Memory broadcasts received: {len(core.memory_subscriber.received_broadcasts)}")
    print(f"    Self attention patterns: {core.self_subscriber.attention_patterns}")
    
    await core.stop()


async def demo_conscious_influence():
    """Demo 3: Conscious Content → Planning etkisi"""
    print("\n" + "=" * 70)
    print("  DEMO 3: CONSCIOUS INFLUENCE ON PLANNING")
    print("=" * 70)
    print("""
  Workspace'deki conscious content, planning kararlarını etkiler.
  - URGENCY broadcast → flee eylemi tercih edilir
  - GOAL broadcast → goal-directed eylem
  - Normal → emotion-based karar
    """)
    
    core = await create_uem_core(
        config={'tick_interval': 0.01},
        logger=logging.getLogger("Demo3"),
    )
    
    # Scenario 1: Normal durum
    normal_state = WorldState(
        tick=1,
        danger_level=0.1,
        player_health=0.9,
    )
    
    print("\n  [Scenario 1: Normal state]")
    result1 = await core.cognitive_cycle(normal_state)
    print(f"    Action: {result1.action_name}")
    print(f"    Conscious: {result1.conscious_content}")
    print(f"    Conscious influence: {result1.metadata['conscious_influence']:.2f}")
    
    # Scenario 2: Urgency
    urgency_state = WorldState(
        tick=2,
        danger_level=0.9,
        player_health=0.2,  # Critical health
        symbols=['ENEMY', 'TRAP'],
    )
    
    print("\n  [Scenario 2: Urgency (high danger + low health)]")
    result2 = await core.cognitive_cycle(urgency_state)
    print(f"    Action: {result2.action_name}")
    print(f"    Conscious: {result2.conscious_content}")
    print(f"    Conscious influence: {result2.metadata['conscious_influence']:.2f}")
    
    # Scenario 3: Goal-driven
    core.set_goal({'name': 'find_treasure', 'priority': 0.8})
    
    goal_state = WorldState(
        tick=3,
        danger_level=0.2,
        player_health=0.8,
        symbols=['CHEST'],
    )
    
    print("\n  [Scenario 3: With active goal 'find_treasure']")
    result3 = await core.cognitive_cycle(goal_state)
    print(f"    Action: {result3.action_name}")
    print(f"    Conscious: {result3.conscious_content}")
    print(f"    Conscious influence: {result3.metadata['conscious_influence']:.2f}")
    
    await core.stop()


async def demo_multi_cycle():
    """Demo 4: Çoklu cycle + attention shift"""
    print("\n" + "=" * 70)
    print("  DEMO 4: MULTI-CYCLE ATTENTION DYNAMICS")
    print("=" * 70)
    print("""
  10 cycle boyunca attention shift'leri izle.
  Dikkat en çok hangi content type'a gidiyor?
    """)
    
    core = await create_uem_core(
        config={'tick_interval': 0.01},
        logger=logging.getLogger("Demo4"),
    )
    
    # Varying scenarios
    scenarios = [
        WorldState(tick=1, danger_level=0.1, player_health=0.9, symbols=['TREE']),
        WorldState(tick=2, danger_level=0.3, player_health=0.8, symbols=['ROCK', 'KEY']),
        WorldState(tick=3, danger_level=0.7, player_health=0.6, symbols=['ENEMY']),
        WorldState(tick=4, danger_level=0.9, player_health=0.3, symbols=['ENEMY', 'TRAP']),
        WorldState(tick=5, danger_level=0.4, player_health=0.5, symbols=['DOOR']),
        WorldState(tick=6, danger_level=0.2, player_health=0.6, symbols=['FOOD']),
        WorldState(tick=7, danger_level=0.1, player_health=0.8, symbols=['CHEST']),
        WorldState(tick=8, danger_level=0.5, player_health=0.7, symbols=['ENEMY']),
        WorldState(tick=9, danger_level=0.3, player_health=0.9, symbols=['NPC']),
        WorldState(tick=10, danger_level=0.1, player_health=1.0, symbols=['HOME']),
    ]
    
    print("\n  Running 10 cycles...\n")
    print("  Tick │ Danger │ Health │ Conscious Content │ Action")
    print("  ─────┼────────┼────────┼───────────────────┼────────")
    
    for state in scenarios:
        result = await core.cognitive_cycle(state)
        conscious = result.conscious_content or "none"
        print(
            f"    {state.tick:2d} │  {state.danger_level:.1f}   │  {state.player_health:.1f}   │ "
            f"{conscious:17s} │ {result.action_name}"
        )
    
    # Final stats
    print("\n  Attention Patterns (total broadcasts per type):")
    for content_type, count in core.self_subscriber.attention_patterns.items():
        print(f"    {content_type}: {count}")
    
    stats = core.get_stats()
    print(f"\n  Performance:")
    print(f"    Total cycles: {stats['total_cycles']}")
    print(f"    Avg cycle time: {stats['avg_cycle_time']*1000:.2f}ms")
    print(f"    Somatic markers learned: {stats['somatic_markers']}")
    
    await core.stop()


async def demo_custom_codelet():
    """Demo 5: Custom Codelet ekleme"""
    print("\n" + "=" * 70)
    print("  DEMO 5: CUSTOM CODELET")
    print("=" * 70)
    print("""
  Özel codelet: 'KEY' ve 'DOOR' birlikte görülünce INSIGHT üret.
    """)
    
    # Custom codelet tanımla
    class InsightCodelet(Codelet):
        def __init__(self, logger=None):
            super().__init__("insight_key_door", priority=0.85, logger=logger)
        
        def run(self, context):
            self.run_count += 1
            symbols = context.get('perception', {}).get('symbols', [])
            
            if 'KEY' in symbols and 'DOOR' in symbols:
                return self._create_coalition(
                    content={'insight': 'Use KEY to open DOOR!'},
                    content_type=ContentType.INSIGHT,
                    activation=0.85,
                    salience=0.9,
                    context={'type': 'object_relation'},
                )
            return None
    
    core = await create_uem_core(
        config={'tick_interval': 0.01},
        logger=logging.getLogger("Demo5"),
    )
    
    # Custom codelet'i kaydet
    core.workspace_manager.register_codelet(InsightCodelet())
    
    # Test 1: KEY ve DOOR yok
    state1 = WorldState(tick=1, symbols=['TREE', 'ROCK'])
    
    print("\n  [Without KEY and DOOR]")
    result1 = await core.cognitive_cycle(state1)
    print(f"    Conscious: {result1.conscious_content}")
    
    # Test 2: KEY ve DOOR var
    state2 = WorldState(tick=2, symbols=['KEY', 'DOOR', 'CHEST'])
    
    print("\n  [With KEY and DOOR present]")
    result2 = await core.cognitive_cycle(state2)
    print(f"    Conscious: {result2.conscious_content}")
    
    # İçerik detayı
    content = core.get_conscious_content()
    if content:
        print(f"    Content detail: {content['content']}")
    
    await core.stop()


# =========================================================================
# MAIN
# =========================================================================

async def main():
    setup_logging()
    
    print("\n" + "█" * 70)
    print("  UEM: GLOBAL WORKSPACE INTEGRATION DEMO")
    print("█" * 70)
    print("""
  Bu demo, LIDA tarzı Global Workspace'in UEM Core'a
  entegrasyonunu gösterir.
  
  Temel mekanizma:
  1. Codelet'ler context'i analiz eder → Coalition üretir
  2. Coalition'lar workspace erişimi için yarışır
  3. Kazanan içerik "conscious" olur
  4. Conscious content tüm modüllere broadcast edilir
  5. Modüller broadcast'a göre davranışlarını ayarlar
    """)
    
    await demo_basic_workspace()
    await demo_broadcast_subscribers()
    await demo_conscious_influence()
    await demo_multi_cycle()
    await demo_custom_codelet()
    
    print("\n" + "=" * 70)
    print("  DEMO TAMAMLANDI")
    print("=" * 70)
    print("""
  Sonraki adımlar:
  - [ ] Perception module entegrasyonu
  - [ ] Tam memory system bağlantısı
  - [ ] Ethical evaluation (ETHMOR)
  - [ ] Self-model güncelleme
    """)


if __name__ == "__main__":
    asyncio.run(main())
