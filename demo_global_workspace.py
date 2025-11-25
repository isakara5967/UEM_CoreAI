#!/usr/bin/env python3
"""
UEM Global Workspace Demo

LIDA tarzı conscious broadcast mekanizmasının gösterimi.

Senaryolar:
1. Normal algı akışı - coalition yarışması
2. Tehlike durumu - urgency kazanır
3. Güçlü duygu - emotion broadcast
4. Yenilik tespiti - novelty broadcast
5. Top-down attention - hedef odaklı
6. Çoklu modül entegrasyonu
"""

import asyncio
import sys
import logging

# Windows için event loop policy
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, '/home/claude/uem_project')

from core.consciousness.global_workspace import (
    GlobalWorkspace,
    WorkspaceManager,
    WorkspaceSubscriber,
    BroadcastMessage,
    ContentType,
    Coalition,
    Codelet,
    create_workspace_manager,
)


# =========================================================================
# SAMPLE SUBSCRIBERS
# =========================================================================

class MemorySubscriber(WorkspaceSubscriber):
    """Memory modülü - broadcast'leri hafızaya kaydeder"""
    
    def __init__(self):
        self.received_broadcasts = []
    
    @property
    def subscriber_name(self) -> str:
        return "MemoryModule"
    
    async def receive_broadcast(self, message: BroadcastMessage) -> None:
        self.received_broadcasts.append({
            'type': message.content_type.value,
            'activation': message.activation,
            'timestamp': message.timestamp,
        })
        print(f"     📝 [Memory] Received: {message.content_type.value}")


class PlanningSubscriber(WorkspaceSubscriber):
    """Planning modülü - broadcast'lere göre plan günceller"""
    
    def __init__(self):
        self.current_priority = None
        self.action_queue = []
    
    @property
    def subscriber_name(self) -> str:
        return "PlanningModule"
    
    async def receive_broadcast(self, message: BroadcastMessage) -> None:
        # Broadcast türüne göre aksiyon
        if message.content_type == ContentType.URGENCY:
            self.current_priority = "ESCAPE"
            print(f"     🎯 [Planning] Priority set to ESCAPE!")
        elif message.content_type == ContentType.PERCEPT:
            self.current_priority = "INVESTIGATE"
            print(f"     🎯 [Planning] Priority set to INVESTIGATE")
        else:
            print(f"     🎯 [Planning] Received: {message.content_type.value}")


class EmotionSubscriber(WorkspaceSubscriber):
    """Emotion modülü - broadcast'lerden duygusal tepki"""
    
    def __init__(self):
        self.emotional_response = None
    
    @property
    def subscriber_name(self) -> str:
        return "EmotionModule"
    
    async def receive_broadcast(self, message: BroadcastMessage) -> None:
        # Broadcast'in duygusal yüküne tepki
        charge = message.source_coalition.emotional_charge
        if charge < -0.3:
            self.emotional_response = "anxious"
            print(f"     💔 [Emotion] Feeling anxious")
        elif charge > 0.3:
            self.emotional_response = "curious"
            print(f"     💚 [Emotion] Feeling curious")
        else:
            print(f"     💙 [Emotion] Neutral response")


# =========================================================================
# HELPER FUNCTIONS
# =========================================================================

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_competition_result(message, context_desc=""):
    if message:
        print(f"\n  🏆 WINNER: {message.content_type.value.upper()}")
        print(f"     Activation: {message.activation:.3f}")
        print(f"     Priority: {message.priority.name}")
        if context_desc:
            print(f"     Context: {context_desc}")
    else:
        print("\n  ❌ No broadcast (threshold not met)")


def print_stats(manager):
    stats = manager.get_stats()
    ws = stats['workspace']
    att = stats['attention']
    
    print("\n  📊 Statistics:")
    print(f"     Cycles: {stats['manager']['cycle_count']}")
    print(f"     Broadcasts: {stats['manager']['broadcast_count']}")
    print(f"     Current focus: {att['current_focus']}")
    
    if ws['winners_by_type']:
        print("     Winners by type:")
        for ctype, count in sorted(ws['winners_by_type'].items(), key=lambda x: -x[1]):
            bar = "█" * count
            print(f"       {ctype:12s} {bar} ({count})")


# =========================================================================
# DEMO SCENARIOS
# =========================================================================

async def demo_basic_competition():
    """Temel coalition yarışması"""
    print_header("SENARYO 1: TEMEL COALITION YARIŞMASI")
    
    print("""
  Farklı türde coalition'lar yarışıyor.
  En yüksek aktivasyonlu kazanır.
    """)
    
    manager = create_workspace_manager()
    
    # Subscribers ekle
    memory_sub = MemorySubscriber()
    planning_sub = PlanningSubscriber()
    emotion_sub = EmotionSubscriber()
    
    manager.register_subscriber(memory_sub)
    manager.register_subscriber(planning_sub)
    manager.register_subscriber(emotion_sub)
    
    # Normal algı context'i
    context = {
        'perception': {
            'danger_level': 0.3,
            'symbols': ['TREE', 'PATH'],
            'novelty': 0.2,
        },
        'emotion': {
            'valence': 0.1,
            'arousal': 0.3,
            'emotion': 'neutral',
        },
        'agent_state': {
            'health': 0.9,
        },
    }
    
    print("\n  Context: Low danger, neutral emotion")
    print("  Expected: PERCEPT should win (most salient)")
    
    message = await manager.cycle(context)
    print_competition_result(message, "Normal perception")
    
    # Subscribers'ın aldığı
    print(f"\n  Subscribers received broadcast:")
    print(f"     Memory stored: {len(memory_sub.received_broadcasts)} items")
    print(f"     Planning priority: {planning_sub.current_priority}")
    print(f"     Emotion response: {emotion_sub.emotional_response}")


async def demo_urgency_wins():
    """Acil durum - urgency her zaman kazanır"""
    print_header("SENARYO 2: ACİL DURUM - URGENCY KAZANIR")
    
    print("""
  Yüksek tehlike durumu.
  URGENCY coalition en yüksek aktivasyona sahip.
    """)
    
    manager = create_workspace_manager()
    
    planning_sub = PlanningSubscriber()
    manager.register_subscriber(planning_sub)
    
    # Tehlikeli durum
    context = {
        'perception': {
            'danger_level': 0.85,
            'symbols': ['ENEMY', 'DANGER'],
            'novelty': 0.5,
        },
        'emotion': {
            'valence': -0.6,
            'arousal': 0.8,
            'emotion': 'fear',
        },
        'agent_state': {
            'health': 0.4,
        },
    }
    
    print("\n  Context: HIGH danger (0.85), low health (0.4)")
    print("  Expected: URGENCY should win")
    
    message = await manager.cycle(context)
    print_competition_result(message, "Critical danger detected")
    
    print(f"\n  Planning response: {planning_sub.current_priority}")


async def demo_emotion_broadcast():
    """Güçlü duygu broadcast'i"""
    print_header("SENARYO 3: GÜÇLÜ DUYGU BROADCAST'İ")
    
    print("""
  Güçlü negatif duygu (korku).
  EMOTION coalition yarışmayı kazanabilir.
    """)
    
    manager = create_workspace_manager()
    
    emotion_sub = EmotionSubscriber()
    manager.register_subscriber(emotion_sub)
    
    # Güçlü korku
    context = {
        'perception': {
            'danger_level': 0.4,  # Orta tehlike
            'symbols': ['SHADOW'],
            'novelty': 0.3,
        },
        'emotion': {
            'valence': -0.8,
            'arousal': 0.9,
            'emotion': 'fear',
        },
        'agent_state': {
            'health': 0.7,
        },
    }
    
    print("\n  Context: Strong fear (v=-0.8, a=0.9)")
    print("  Expected: EMOTION should compete strongly")
    
    message = await manager.cycle(context)
    print_competition_result(message)
    
    print(f"\n  Emotional response: {emotion_sub.emotional_response}")


async def demo_novelty_detection():
    """Yenilik tespiti"""
    print_header("SENARYO 4: YENİLİK TESPİTİ")
    
    print("""
  İlk kez karşılaşılan pattern.
  NOVELTY codelet coalition oluşturur.
    """)
    
    manager = create_workspace_manager()
    
    memory_sub = MemorySubscriber()
    manager.register_subscriber(memory_sub)
    
    # İlk karşılaşma
    context1 = {
        'perception': {
            'danger_level': 0.2,
            'symbols': ['ANCIENT_RUNE', 'GLOWING_CRYSTAL'],
            'novelty': 0.7,
        },
        'emotion': {
            'valence': 0.3,
            'arousal': 0.5,
            'emotion': 'curiosity',
        },
        'agent_state': {
            'health': 1.0,
        },
    }
    
    print("\n  [İLK KARŞILAŞMA]")
    print("  Context: New pattern (ANCIENT_RUNE, GLOWING_CRYSTAL)")
    
    message1 = await manager.cycle(context1)
    print_competition_result(message1, "First encounter")
    
    # Aynı pattern tekrar
    print("\n  [AYNI PATTERN TEKRAR]")
    print("  Context: Same symbols again")
    
    message2 = await manager.cycle(context1)
    print_competition_result(message2, "Known pattern")
    
    # Yeni pattern
    context2 = {
        'perception': {
            'danger_level': 0.2,
            'symbols': ['MYSTERIOUS_DOOR', 'HIDDEN_KEY'],
            'novelty': 0.8,
        },
        'emotion': {
            'valence': 0.4,
            'arousal': 0.6,
            'emotion': 'curiosity',
        },
        'agent_state': {
            'health': 1.0,
        },
    }
    
    print("\n  [YENİ PATTERN]")
    print("  Context: New pattern (MYSTERIOUS_DOOR, HIDDEN_KEY)")
    
    message3 = await manager.cycle(context2)
    print_competition_result(message3, "New discovery")


async def demo_top_down_attention():
    """Top-down dikkat yönlendirmesi"""
    print_header("SENARYO 5: TOP-DOWN DİKKAT")
    
    print("""
  Hedef belirlenerek dikkat yönlendiriliyor.
  Hedefle uyumlu içerikler boost alır.
    """)
    
    manager = create_workspace_manager()
    
    # İlk cycle - hedef yok
    context = {
        'perception': {
            'danger_level': 0.3,
            'symbols': ['TREASURE'],
            'novelty': 0.3,
        },
        'current_goal': {
            'type': 'find_treasure',
            'importance': 0.8,
        },
        'emotion': {
            'valence': 0.2,
            'arousal': 0.4,
            'emotion': 'neutral',
        },
        'agent_state': {
            'health': 0.8,
        },
    }
    
    print("\n  [HEDEF YOK]")
    message1 = await manager.cycle(context)
    print_competition_result(message1)
    
    # Attention goal belirle
    manager.set_attention_goal(
        goal_type="search",
        target="goal",  # GOAL türündeki içeriklere dikkat
        priority=0.8,
    )
    
    print("\n  [HEDEF BELİRLENDİ: goal türüne dikkat]")
    message2 = await manager.cycle(context)
    print_competition_result(message2)
    
    print(f"\n  Current attention focus: {manager.get_current_focus()}")


async def demo_long_session():
    """Uzun oturum - istatistikler"""
    print_header("SENARYO 6: UZUN OTURUM (20 cycle)")
    
    print("""
  20 cycle boyunca çeşitli durumlar.
  Coalition yarışması ve broadcast istatistikleri.
    """)
    
    manager = create_workspace_manager()
    
    memory_sub = MemorySubscriber()
    planning_sub = PlanningSubscriber()
    manager.register_subscriber(memory_sub)
    manager.register_subscriber(planning_sub)
    
    import random
    random.seed(42)
    
    for i in range(20):
        danger = random.uniform(0.1, 0.9)
        valence = random.uniform(-0.8, 0.8)
        arousal = random.uniform(0.2, 0.9)
        health = max(0.3, 1.0 - i * 0.02)
        
        context = {
            'perception': {
                'danger_level': danger,
                'symbols': [f'SYM_{i % 5}'],
                'novelty': 0.3,
            },
            'emotion': {
                'valence': valence,
                'arousal': arousal,
                'emotion': 'mixed',
            },
            'agent_state': {
                'health': health,
            },
        }
        
        await manager.cycle(context)
        
        if (i + 1) % 5 == 0:
            print(f"  ... {i + 1} cycles completed")
    
    print_stats(manager)
    
    print(f"\n  Memory received {len(memory_sub.received_broadcasts)} broadcasts")


async def demo_custom_codelet():
    """Özel codelet ekleme"""
    print_header("SENARYO 7: ÖZEL CODELET")
    
    print("""
  Kullanıcı tanımlı codelet ekleniyor.
  INSIGHT türünde coalition oluşturur.
    """)
    
    # Özel codelet
    class InsightCodelet(Codelet):
        """Belirli pattern'lerde insight oluşturur"""
        
        def __init__(self, logger=None):
            super().__init__("insight_codelet", priority=0.7, logger=logger)
        
        def run(self, context):
            symbols = context.get('perception', {}).get('symbols', [])
            
            # "KEY" ve "DOOR" birlikte görülünce insight
            if 'KEY' in symbols and 'DOOR' in symbols:
                return self._create_coalition(
                    content={'insight': 'Use KEY to open DOOR'},
                    content_type=ContentType.INSIGHT,
                    activation=0.8,
                    salience=0.9,
                    context={'type': 'object_relation'},
                )
            return None
    
    manager = create_workspace_manager()
    manager.register_codelet(InsightCodelet())
    
    # KEY ve DOOR olmadan
    context1 = {
        'perception': {
            'danger_level': 0.2,
            'symbols': ['TREE', 'ROCK'],
        },
        'agent_state': {'health': 1.0},
    }
    
    print("\n  [KEY ve DOOR YOK]")
    message1 = await manager.cycle(context1)
    print_competition_result(message1)
    
    # KEY ve DOOR var
    context2 = {
        'perception': {
            'danger_level': 0.2,
            'symbols': ['KEY', 'DOOR'],
        },
        'agent_state': {'health': 1.0},
    }
    
    print("\n  [KEY ve DOOR MEVCUT]")
    message2 = await manager.cycle(context2)
    print_competition_result(message2, "Insight generated!")


async def main():
    print("\n" + "=" * 70)
    print("  UEM GLOBAL WORKSPACE DEMO")
    print("=" * 70)
    print("""
  LIDA tarzı conscious broadcast mekanizması.
  
  Yapı:
  ┌─────────────────────────────────────────────────────────────────┐
  │                    GLOBAL WORKSPACE                              │
  ├─────────────────────────────────────────────────────────────────┤
  │                                                                  │
  │  Codelets:                                                       │
  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
  │  │Perception│ │ Memory   │ │ Emotion  │ │ Urgency  │ ...        │
  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘            │
  │       │            │            │            │                   │
  │       ▼            ▼            ▼            ▼                   │
  │  ┌─────────────────────────────────────────────────┐            │
  │  │           COALITION QUEUE                        │            │
  │  │  [Percept:0.65] [Emotion:0.52] [Urgency:0.89]   │            │
  │  └───────────────────────┬─────────────────────────┘            │
  │                          │                                       │
  │                          ▼ COMPETITION                           │
  │                    ┌───────────┐                                 │
  │                    │  WINNER   │ → activation > threshold       │
  │                    └─────┬─────┘                                 │
  │                          │                                       │
  │                          ▼ BROADCAST                             │
  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
  │  │ Memory   │ │ Planning │ │ Emotion  │ │  Self    │            │
  │  │Subscriber│ │Subscriber│ │Subscriber│ │Subscriber│            │
  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘            │
  └─────────────────────────────────────────────────────────────────┘
    """)
    
    await demo_basic_competition()
    await demo_urgency_wins()
    await demo_emotion_broadcast()
    await demo_novelty_detection()
    await demo_top_down_attention()
    await demo_long_session()
    await demo_custom_codelet()
    
    print("\n" + "=" * 70)
    print("  DEMO COMPLETE")
    print("=" * 70)
    print("""
  Global Workspace başarıyla test edildi!
  
  Tamamlanan özellikler:
  ✓ Coalition-based competition
  ✓ Activation-based winner selection
  ✓ Conscious broadcast to subscribers
  ✓ Built-in codelets (perception, emotion, urgency, novelty, goal)
  ✓ Top-down attention modulation
  ✓ Custom codelet support
  ✓ Statistics and history tracking
    """)


if __name__ == "__main__":
    asyncio.run(main())
