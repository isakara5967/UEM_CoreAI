#!/usr/bin/env python3
"""
UEM Memory Consolidation Demo

STM → LTM emotion-tagged transfer gösterisi.

Senaryolar:
1. Yüksek salience item → immediate consolidation
2. Emotionally significant item → boosted consolidation
3. Frequently accessed item → consolidation via repetition
4. Somatic marker integration
5. Emotional memory retrieval
"""

import asyncio
import sys
import time

# Windows için event loop policy
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, '/home/claude/uem_project')

from core.memory.consolidation.memory_consolidation import (
    LongTermMemory,
    MemoryConsolidator,
    ConsolidatedMemory,
    MemoryType,
    EmotionTag,
    ActivationCalculator,
)


def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_memory(memory: ConsolidatedMemory, prefix=""):
    emotion_str = ""
    if memory.emotion_tag:
        emotion_str = f" | emotion: {memory.emotion_tag.emotion_label} (v={memory.emotion_tag.valence:+.2f})"
    
    print(f"{prefix}📝 {memory.memory_id[:8]}: {memory.content}")
    print(f"{prefix}   type: {memory.memory_type.value} | activation: {memory.total_activation:.3f}{emotion_str}")


async def demo_basic_consolidation():
    """Temel konsolidasyon gösterisi"""
    print_header("TEMEL KONSOLİDASYON")
    
    print("""
  STM'den LTM'ye geçiş kriterleri:
  1. Yüksek salience (önem) → threshold: 0.6
  2. Duygusal yoğunluk → +0.2 bonus
  3. Sık erişim → +0.05 per access (after 3)
    """)
    
    # Setup
    ltm = LongTermMemory()
    consolidator = MemoryConsolidator(
        ltm=ltm,
        consolidation_threshold=0.6,
        emotion_boost=0.2,
        access_threshold=3,
    )
    
    print("  [SENARYO 1: Yüksek Salience]")
    print("  Agent kritik bir olay yaşıyor...\n")
    
    # Yüksek salience item
    consolidator.add_to_pending(
        content="Discovered enemy base at coordinates (45, 78)",
        salience=0.8,
        context_hash="exploration_001",
        memory_type=MemoryType.EPISODIC,
    )
    
    # Düşük salience item
    consolidator.add_to_pending(
        content="Saw a random rock on the path",
        salience=0.2,
        context_hash="exploration_001",
        memory_type=MemoryType.EPISODIC,
    )
    
    # Orta salience item
    consolidator.add_to_pending(
        content="Found a health potion in chest",
        salience=0.5,
        context_hash="exploration_001",
        memory_type=MemoryType.EPISODIC,
    )
    
    print(f"  Pending items: 3")
    print(f"  Consolidation threshold: {consolidator.consolidation_threshold}")
    
    # Run consolidation
    result = await consolidator.consolidation_cycle()
    
    print(f"\n  📊 Sonuç:")
    print(f"     Consolidated: {result['consolidated']}")
    print(f"     Rejected: {result['rejected']}")
    
    print(f"\n  LTM'deki anılar ({ltm.get_stats()['total_memories']}):")
    for memory in ltm.memories.values():
        print_memory(memory, "  ")


async def demo_emotional_consolidation():
    """Duygusal konsolidasyon gösterisi"""
    print_header("DUYGUSAL KONSOLİDASYON")
    
    print("""
  Duygusal olaylar daha kolay hatırlanır.
  Emotion boost: salience'a +0.3 * intensity eklenir.
    """)
    
    ltm = LongTermMemory()
    consolidator = MemoryConsolidator(
        ltm=ltm,
        consolidation_threshold=0.55,  # Slightly lower to show emotion effect
        emotion_boost=0.3,  # Higher boost
    )
    
    print("  [Düşük salience + Yüksek emotion]")
    
    # Düşük salience ama güçlü korku
    consolidator.add_to_pending(
        content="Almost fell into a trap",
        salience=0.4,  # Normalde yetersiz
        emotion_state={
            'valence': -0.8,
            'arousal': 0.9,
            'emotion': 'fear',
        },
        memory_type=MemoryType.EMOTIONAL,
    )
    
    # Düşük salience + nötr emotion
    consolidator.add_to_pending(
        content="Walked past a tree",
        salience=0.4,
        emotion_state={
            'valence': 0.0,
            'arousal': 0.1,
            'emotion': 'neutral',
        },
        memory_type=MemoryType.EPISODIC,
    )
    
    # Düşük salience + mutluluk
    consolidator.add_to_pending(
        content="Made a new friend NPC",
        salience=0.4,
        emotion_state={
            'valence': 0.7,
            'arousal': 0.7,
            'emotion': 'joy',
        },
        memory_type=MemoryType.EMOTIONAL,
    )
    
    print(f"  Base salience'lar: 0.40, 0.40, 0.40 (threshold: 0.55)")
    print(f"  Fear: 0.40 + 0.3 * (0.8 * 0.9) = 0.62 ✓")
    print(f"  Neutral: 0.40 + 0.3 * (0.0 * 0.5) = 0.40 ✗")
    print(f"  Joy: 0.40 + 0.3 * (0.7 * 0.7) = 0.55 ✓")
    
    result = await consolidator.consolidation_cycle()
    
    print(f"\n  📊 Sonuç:")
    print(f"     Consolidated: {result['consolidated']} (emotion boost ile)")
    print(f"     Rejected: {result['rejected']} (emotion yetersiz)")
    
    print(f"\n  LTM'deki duygusal anılar:")
    for memory in ltm.memories.values():
        print_memory(memory, "  ")


async def demo_repetition_consolidation():
    """Tekrar ile konsolidasyon"""
    print_header("TEKRAR İLE KONSOLİDASYON")
    
    print("""
  Sık erişilen bilgiler konsolide edilir.
  Access threshold: 3 (sonrası bonus)
    """)
    
    ltm = LongTermMemory()
    consolidator = MemoryConsolidator(
        ltm=ltm,
        consolidation_threshold=0.6,
        access_threshold=3,
    )
    
    # Düşük salience ama çok erişilen
    consolidator.add_to_pending(
        content="The merchant is at the town square",
        salience=0.4,
        access_count=5,  # 5 kez erişilmiş
        memory_type=MemoryType.SEMANTIC,
    )
    
    # Düşük salience, az erişilen
    consolidator.add_to_pending(
        content="There was a bird on the roof",
        salience=0.4,
        access_count=1,
        memory_type=MemoryType.EPISODIC,
    )
    
    print(f"  Item 1: salience=0.4, access_count=5 → score ≈ 0.5")
    print(f"  Item 2: salience=0.4, access_count=1 → score = 0.4")
    
    result = await consolidator.consolidation_cycle()
    
    print(f"\n  📊 Sonuç: consolidated={result['consolidated']}, rejected={result['rejected']}")
    
    if ltm.memories:
        print(f"\n  LTM'ye eklenen (tekrar ile):")
        for memory in ltm.memories.values():
            print_memory(memory, "  ")


async def demo_activation_retrieval():
    """Aktivasyon tabanlı retrieval"""
    print_header("AKTİVASYON TABANLI ERİŞİM")
    
    print("""
  ACT-R tarzı activation hesaplama:
  B_i = ln(sum(t_j^-d))
  
  Son erişilen ve sık erişilen anılar
  daha yüksek aktivasyona sahip.
    """)
    
    ltm = LongTermMemory()
    
    # Eski anı
    old_memory = ltm.store(
        content="An old adventure from long ago",
        memory_type=MemoryType.EPISODIC,
        salience=0.7,
    )
    
    # Simüle: eski anının erişim zamanlarını geçmişe kaydır
    ltm.access_history[old_memory.memory_id] = [
        time.time() - 3600,  # 1 saat önce
        time.time() - 7200,  # 2 saat önce
    ]
    
    # Yeni anı
    new_memory = ltm.store(
        content="Something that just happened",
        memory_type=MemoryType.EPISODIC,
        salience=0.7,
    )
    
    # Sık erişilen anı
    frequent_memory = ltm.store(
        content="Important location I visit often",
        memory_type=MemoryType.SEMANTIC,
        salience=0.6,
    )
    # Simüle: çok erişim
    ltm.access_history[frequent_memory.memory_id] = [
        time.time() - 60,   # 1 dk önce
        time.time() - 120,  # 2 dk önce
        time.time() - 180,  # 3 dk önce
        time.time() - 240,  # 4 dk önce
        time.time() - 300,  # 5 dk önce
    ]
    
    print("  Anılar oluşturuldu:")
    print("  - old_adventure: 2 erişim, 1-2 saat önce")
    print("  - just_happened: 1 erişim, şimdi")
    print("  - important_location: 5 erişim, son 5 dk")
    
    # Retrieve all
    print("\n  📊 Aktivasyon sıralaması (retrieval):")
    memories = ltm.retrieve(limit=10, update_access=False)
    
    for i, memory in enumerate(memories, 1):
        content_short = str(memory.content)[:40]
        print(f"  {i}. activation={memory.total_activation:.3f}: {content_short}...")


async def demo_emotional_retrieval():
    """Duygusal retrieval"""
    print_header("DUYGUSAL BELLEK ERİŞİMİ")
    
    print("""
  Duygu bazlı bellek arama:
  - retrieve_by_emotion(): Benzer valence
  - retrieve_emotional_memories(): Güçlü duygular
    """)
    
    ltm = LongTermMemory()
    
    # Farklı duygusal anılar oluştur
    ltm.store(
        content="Victory celebration after winning the battle",
        memory_type=MemoryType.EMOTIONAL,
        emotion_tag=EmotionTag(valence=0.9, arousal=0.8, emotion_label='joy'),
    )
    
    ltm.store(
        content="Lost a valuable item to a thief",
        memory_type=MemoryType.EMOTIONAL,
        emotion_tag=EmotionTag(valence=-0.7, arousal=0.6, emotion_label='sadness'),
    )
    
    ltm.store(
        content="Scary encounter with a monster",
        memory_type=MemoryType.EMOTIONAL,
        emotion_tag=EmotionTag(valence=-0.8, arousal=0.9, emotion_label='fear'),
    )
    
    ltm.store(
        content="Regular day, nothing special",
        memory_type=MemoryType.EPISODIC,
        emotion_tag=EmotionTag(valence=0.1, arousal=0.2, emotion_label='neutral'),
    )
    
    ltm.store(
        content="Peaceful moment by the lake",
        memory_type=MemoryType.EMOTIONAL,
        emotion_tag=EmotionTag(valence=0.5, arousal=0.2, emotion_label='calm'),
    )
    
    print(f"  {ltm.get_stats()['total_memories']} anı oluşturuldu.")
    
    # Pozitif anıları getir
    print("\n  🌟 Pozitif anılar (valence >= 0.4):")
    positive = ltm.retrieve_emotional_memories(valence_threshold=0.4, positive=True)
    for m in positive:
        print(f"     [{m.emotion_tag.emotion_label}] {m.content[:50]}...")
    
    # Negatif anıları getir
    print("\n  ⚠️ Negatif anılar (valence <= -0.5):")
    negative = ltm.retrieve_emotional_memories(valence_threshold=0.5, positive=False)
    for m in negative:
        print(f"     [{m.emotion_tag.emotion_label}] {m.content[:50]}...")
    
    # Benzer valence ile arama
    print("\n  🔍 Şu anki ruh haline benzer anılar (valence ≈ -0.6):")
    similar = ltm.retrieve_by_emotion(target_valence=-0.6, tolerance=0.3)
    for m in similar:
        print(f"     [{m.emotion_tag.valence:+.1f}] {m.content[:50]}...")


async def demo_somatic_integration():
    """Somatic marker entegrasyonu"""
    print_header("SOMATİK MARKER ENTEGRASYONU")
    
    print("""
  Somatic Marker → LTM bağlantısı.
  Deneyimlerden öğrenilen "gut feeling" kalıcı hale gelir.
    """)
    
    ltm = LongTermMemory()
    consolidator = MemoryConsolidator(ltm=ltm)
    
    # Somatic marker simülasyonu
    somatic_markers = [
        {
            'action': 'APPROACH_DARK_CAVE',
            'valence': -0.8,
            'original_outcome': 'ambushed',
            'strength': 0.7,
        },
        {
            'action': 'EXPLORE_FOREST',
            'valence': 0.6,
            'original_outcome': 'found_treasure',
            'strength': 0.8,
        },
        {
            'action': 'TALK_TO_STRANGER',
            'valence': -0.3,
            'original_outcome': 'scammed',
            'strength': 0.5,
        },
    ]
    
    print("  Somatic marker'lar konsolide ediliyor...\n")
    
    for marker in somatic_markers:
        # Simulate somatic marker event
        consolidator.add_to_pending(
            content={
                'type': 'somatic_marker',
                'action': marker['action'],
                'original_outcome': marker['original_outcome'],
            },
            salience=0.7 + (abs(marker['valence']) * 0.3),
            emotion_state={
                'valence': marker['valence'],
                'arousal': 0.5,
                'emotion': 'somatic',
            },
            memory_type=MemoryType.EMOTIONAL,
            source='somatic_marker',
        )
        
        symbol = "⚠️" if marker['valence'] < 0 else "✓"
        print(f"  {symbol} {marker['action']}: {marker['original_outcome']} (v={marker['valence']:+.1f})")
    
    result = await consolidator.consolidation_cycle()
    
    print(f"\n  📊 Konsolidasyon: {result['consolidated']} marker LTM'ye aktarıldı")
    
    print("\n  LTM'deki somatic anılar:")
    emotional_memories = ltm.retrieve(memory_type=MemoryType.EMOTIONAL, limit=10)
    for m in emotional_memories:
        action = m.content.get('action', 'unknown')
        outcome = m.content.get('original_outcome', '')
        valence = m.emotion_tag.valence if m.emotion_tag else 0
        print(f"     [{valence:+.1f}] {action} → {outcome}")


async def demo_statistics():
    """İstatistik gösterimi"""
    print_header("SİSTEM İSTATİSTİKLERİ")
    
    ltm = LongTermMemory()
    consolidator = MemoryConsolidator(ltm=ltm)
    
    # Birkaç consolidation cycle simülasyonu
    for i in range(3):
        for j in range(5):
            consolidator.add_to_pending(
                content=f"Memory {i*5+j}",
                salience=0.3 + (j * 0.15),
                emotion_state={'valence': (j - 2) * 0.3, 'arousal': 0.5, 'emotion': 'mixed'},
                memory_type=MemoryType.EPISODIC if j % 2 == 0 else MemoryType.SEMANTIC,
            )
        await consolidator.consolidation_cycle()
    
    stats = consolidator.get_stats()
    
    print(f"""
  Consolidator Stats:
  ├─ Cycles: {stats['consolidation_cycles']}
  ├─ Items consolidated: {stats['items_consolidated']}
  ├─ Items rejected: {stats['items_rejected']}
  ├─ Consolidation rate: {stats['consolidation_rate']:.1%}
  └─ Pending: {stats['pending_count']}

  LTM Stats:
  ├─ Total memories: {stats['ltm_stats']['total_memories']}
  ├─ Episodic: {stats['ltm_stats']['episodic_count']}
  ├─ Semantic: {stats['ltm_stats']['semantic_count']}
  ├─ Emotional: {stats['ltm_stats']['emotional_count']}
  ├─ Retrievals: {stats['ltm_stats']['total_retrievals']}
  └─ Stores: {stats['ltm_stats']['total_stores']}
    """)


async def main():
    print("\n" + "=" * 60)
    print("  UEM MEMORY CONSOLIDATION DEMO")
    print("=" * 60)
    print("""
  Bu demo, STM → LTM konsolidasyonu ve
  emotion-tagged memory retrieval sistemini gösterir.
  
  ACT-R aktivasyon modeli + Damasio duygusal bellek teorisi
  
  Yapı:
  ┌─────────┐    ┌──────────────┐    ┌─────────┐
  │   STM   │───→│ Consolidator │───→│   LTM   │
  └─────────┘    └──────────────┘    └─────────┘
        │              │
        │         ┌────┴────┐
        │         │ Emotion │
        └────────→│  Tag    │
                  └─────────┘
    """)
    
    await demo_basic_consolidation()
    await demo_emotional_consolidation()
    await demo_repetition_consolidation()
    await demo_activation_retrieval()
    await demo_emotional_retrieval()
    await demo_somatic_integration()
    await demo_statistics()
    
    print("\n" + "=" * 60)
    print("  DEMO COMPLETE")
    print("=" * 60)
    print("""
  Memory Consolidation tamamlandı!
  
  Entegrasyon noktaları:
  1. STM'den pending queue'ya otomatik ekleme
  2. EmotionCore → emotion tag güncelleme
  3. SomaticMarker → emotional memory kaydı
  4. Planning → memory retrieval for context
    """)


if __name__ == "__main__":
    asyncio.run(main())
