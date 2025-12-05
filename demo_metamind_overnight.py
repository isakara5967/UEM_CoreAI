"""
MetaMind v1.9 Overnight Demo
============================

Gece boyunca çalışacak kapsamlı test.
- 500 cycle (5 episode)
- Farklı senaryolar (savaş, huzur, stres, keşif, sosyal)
- Progress bar
- Sonunda detaylı rapor

Kullanım:
    python demo_metamind_overnight.py
    
Ctrl+C ile durdurunca da rapor verir.
"""

import asyncio
import signal
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime
import random

# Graceful shutdown için
shutdown_requested = False

def signal_handler(sig, frame):
    global shutdown_requested
    print("\n\n⚠️  Durdurma sinyali alındı, rapor hazırlanıyor...")
    shutdown_requested = True

signal.signal(signal.SIGINT, signal_handler)


@dataclass
class MockWorldState:
    tick: int = 0
    danger_level: float = 0.0
    player_health: float = 0.8
    player_energy: float = 0.7
    objects: List[Dict] = field(default_factory=list)
    agents: List[Dict] = field(default_factory=list)
    symbols: List[str] = field(default_factory=list)


class ScenarioGenerator:
    """Farklı senaryolar üretir."""
    
    def __init__(self):
        self.phase = "intro"
        self.phase_cycle = 0
        
    def get_scenario(self, cycle: int) -> Dict[str, Any]:
        """Cycle'a göre senaryo döndür."""
        
        # Her 100 cycle'da yeni episode
        episode = cycle // 100
        cycle_in_episode = cycle % 100
        
        # Episode bazlı tema
        themes = ["exploration", "combat", "social", "survival", "recovery"]
        theme = themes[episode % len(themes)]
        
        # Tema bazlı senaryo
        if theme == "exploration":
            return self._exploration_scenario(cycle_in_episode)
        elif theme == "combat":
            return self._combat_scenario(cycle_in_episode)
        elif theme == "social":
            return self._social_scenario(cycle_in_episode)
        elif theme == "survival":
            return self._survival_scenario(cycle_in_episode)
        else:  # recovery
            return self._recovery_scenario(cycle_in_episode)
    
    def _exploration_scenario(self, c: int) -> Dict:
        """Keşif senaryosu - düşük tehlike, yüksek enerji."""
        return {
            "danger": 0.1 + random.uniform(0, 0.2),
            "health": 0.8 + random.uniform(0, 0.15),
            "energy": 0.7 + random.uniform(0, 0.2),
            "agents": self._random_neutral_agents(random.randint(0, 2)),
            "theme": "exploration"
        }
    
    def _combat_scenario(self, c: int) -> Dict:
        """Savaş senaryosu - yüksek tehlike, düşen sağlık."""
        intensity = min(1.0, 0.3 + (c / 100) * 0.7)  # Zamanla yoğunlaşır
        return {
            "danger": 0.5 + intensity * 0.4,
            "health": max(0.2, 0.8 - intensity * 0.5),
            "energy": max(0.1, 0.7 - intensity * 0.4),
            "agents": self._random_enemy_agents(random.randint(1, 3)),
            "theme": "combat"
        }
    
    def _social_scenario(self, c: int) -> Dict:
        """Sosyal senaryo - çok NPC, düşük tehlike."""
        return {
            "danger": 0.1 + random.uniform(0, 0.1),
            "health": 0.7 + random.uniform(0, 0.2),
            "energy": 0.6 + random.uniform(0, 0.2),
            "agents": self._random_mixed_agents(random.randint(2, 5)),
            "theme": "social"
        }
    
    def _survival_scenario(self, c: int) -> Dict:
        """Hayatta kalma - kritik durum, kaynak kıtlığı."""
        crisis = (c % 30) < 15  # 15 cycle kriz, 15 cycle toparlanma
        if crisis:
            return {
                "danger": 0.7 + random.uniform(0, 0.25),
                "health": 0.2 + random.uniform(0, 0.2),
                "energy": 0.1 + random.uniform(0, 0.2),
                "agents": self._random_enemy_agents(random.randint(0, 2)),
                "theme": "survival_crisis"
            }
        else:
            return {
                "danger": 0.3 + random.uniform(0, 0.2),
                "health": 0.4 + random.uniform(0, 0.2),
                "energy": 0.3 + random.uniform(0, 0.2),
                "agents": [],
                "theme": "survival_recover"
            }
    
    def _recovery_scenario(self, c: int) -> Dict:
        """Toparlanma - güvenli, iyileşme."""
        progress = c / 100  # 0 -> 1
        return {
            "danger": max(0.05, 0.3 - progress * 0.25),
            "health": min(0.95, 0.5 + progress * 0.4),
            "energy": min(0.9, 0.4 + progress * 0.45),
            "agents": self._random_friendly_agents(random.randint(0, 2)),
            "theme": "recovery"
        }
    
    def _random_enemy_agents(self, count: int) -> List[Dict]:
        agents = []
        for i in range(count):
            agents.append({
                "id": f"enemy_{i}",
                "health": 0.7 + random.uniform(0, 0.3),
                "energy": 0.8 + random.uniform(0, 0.2),
                "valence": -0.5 - random.uniform(0, 0.4),
                "danger": 0.7 + random.uniform(0, 0.3),
                "relationship": -0.5 - random.uniform(0, 0.3),
            })
        return agents
    
    def _random_friendly_agents(self, count: int) -> List[Dict]:
        agents = []
        for i in range(count):
            agents.append({
                "id": f"friend_{i}",
                "health": 0.6 + random.uniform(0, 0.3),
                "energy": 0.5 + random.uniform(0, 0.3),
                "valence": 0.4 + random.uniform(0, 0.4),
                "danger": 0.05 + random.uniform(0, 0.1),
                "relationship": 0.5 + random.uniform(0, 0.3),
            })
        return agents
    
    def _random_neutral_agents(self, count: int) -> List[Dict]:
        agents = []
        for i in range(count):
            agents.append({
                "id": f"neutral_{i}",
                "health": 0.5 + random.uniform(0, 0.3),
                "energy": 0.5 + random.uniform(0, 0.3),
                "valence": -0.1 + random.uniform(0, 0.2),
                "danger": 0.2 + random.uniform(0, 0.2),
                "relationship": 0.0,
            })
        return agents
    
    def _random_mixed_agents(self, count: int) -> List[Dict]:
        agents = []
        for i in range(count):
            agent_type = random.choice(["friend", "neutral", "enemy"])
            if agent_type == "friend":
                agents.extend(self._random_friendly_agents(1))
            elif agent_type == "enemy":
                agents.extend(self._random_enemy_agents(1))
            else:
                agents.extend(self._random_neutral_agents(1))
        return agents


def print_progress(cycle: int, total: int, theme: str, meta_state):
    """Progress bar göster."""
    pct = (cycle + 1) / total * 100
    bar_len = 40
    filled = int(bar_len * (cycle + 1) / total)
    bar = "█" * filled + "░" * (bar_len - filled)
    
    # MetaState özeti
    if meta_state:
        health = meta_state.global_cognitive_health.value
        stability = meta_state.emotional_stability.value
        conf = meta_state.global_cognitive_health.confidence
        status = f"H:{health:.2f} S:{stability:.2f} C:{conf:.0%}"
    else:
        status = "..."
    
    episode = cycle // 100 + 1
    print(f"\r[{bar}] {pct:5.1f}% | Cycle {cycle+1}/{total} | Ep:{episode} | {theme:15} | {status}", end="", flush=True)


def print_report(mm, run_id: str, total_cycles: int, start_time: datetime):
    """Final rapor yazdır."""
    duration = datetime.now() - start_time
    
    print("\n")
    print("=" * 70)
    print("📊 METAMIND OVERNIGHT DEMO - FİNAL RAPOR")
    print("=" * 70)
    
    print(f"\n🕐 Süre: {duration}")
    print(f"🔄 Toplam Cycle: {total_cycles}")
    print(f"📁 Run ID: {run_id}")
    
    # MetaState
    print("\n" + "-" * 70)
    print("📈 META-STATE (Son Durum)")
    print("-" * 70)
    meta = mm.get_meta_state()
    if meta:
        metrics = [
            ("Global Health", meta.global_cognitive_health),
            ("Emotional Stability", meta.emotional_stability),
            ("Ethical Alignment", meta.ethical_alignment),
            ("Exploration Bias", meta.exploration_bias),
            ("Failure Pressure", meta.failure_pressure),
            ("Memory Health", meta.memory_health),
        ]
        for name, m in metrics:
            bar_len = 20
            filled = int(bar_len * m.value)
            bar = "▓" * filled + "░" * (bar_len - filled)
            print(f"  {name:22} [{bar}] {m.value:.3f} (conf: {m.confidence:.0%})")
    
    # Social Health
    print("\n" + "-" * 70)
    print("🤝 SOCIAL HEALTH")
    print("-" * 70)
    social = mm.social_pipeline.get_metrics()
    print(f"  Average Empathy:    {social.average_empathy:.3f}")
    print(f"  Average Resonance:  {social.average_resonance:.3f}")
    print(f"  Trust Level:        {social.trust_level:.3f}")
    print(f"  Cooperation Score:  {social.cooperation_score:.3f}")
    print(f"  Conflict Frequency: {social.conflict_frequency:.3f}")
    print(f"  Total Interactions: {social.data_points}")
    
    # Patterns
    print("\n" + "-" * 70)
    print("🔍 TOP PATTERNS")
    print("-" * 70)
    patterns = mm.pattern_miner.get_top_patterns(limit=10)
    if patterns:
        for p in patterns[:10]:
            print(f"  {p.pattern_type:20} | {p.pattern_key:15} | freq: {p.frequency:3} | conf: {p.confidence:.2f}")
    else:
        print("  (Pattern yok)")
    
    # Performance
    print("\n" + "-" * 70)
    print("⚡ PERFORMANCE")
    print("-" * 70)
    stats = mm.get_performance_stats()
    avg_time = stats['total_online_time_ms'] / max(1, stats['cycles_processed'])
    print(f"  Total Cycles:    {stats['cycles_processed']}")
    print(f"  Avg Cycle Time:  {avg_time:.2f}ms")
    print(f"  Budget:          {stats['budget_ms']}ms")
    print(f"  Status:          {'✅ Budget içinde' if avg_time < stats['budget_ms'] else '⚠️ Budget aşıldı'}")
    
    # Episodes
    print("\n" + "-" * 70)
    print("📁 EPISODES")
    print("-" * 70)
    episode_count = total_cycles // 100 + (1 if total_cycles % 100 > 0 else 0)
    print(f"  Toplam Episode: {episode_count}")
    print(f"  Window Size:    {mm.config.episode.window_cycles} cycles")
    
    print("\n" + "=" * 70)
    print("✅ DEMO TAMAMLANDI")
    print("=" * 70)


async def main():
    global shutdown_requested
    
    print("=" * 70)
    print("🌙 METAMIND v1.9 OVERNIGHT DEMO")
    print("=" * 70)
    print("\nBu demo gece boyunca çalışacak şekilde tasarlandı.")
    print("Durdurmak için Ctrl+C (rapor yine de gösterilir)")
    print()
    
    # Config
    TOTAL_CYCLES = 500  # 5 episode
    
    from core.unified_core import UnifiedUEMCore
    
    core = UnifiedUEMCore()
    mm = core._metamind_core
    
    print("🚀 Başlatılıyor...")
    run_id = await core.start_logging({
        "demo": "overnight",
        "total_cycles": TOTAL_CYCLES,
        "started_at": datetime.now().isoformat(),
    })
    print(f"📁 Run ID: {run_id}\n")
    
    scenario_gen = ScenarioGenerator()
    start_time = datetime.now()
    completed_cycles = 0
    
    try:
        for cycle in range(TOTAL_CYCLES):
            if shutdown_requested:
                break
            
            # Senaryo al
            scenario = scenario_gen.get_scenario(cycle)
            
            # WorldState oluştur
            world = MockWorldState(
                tick=cycle,
                danger_level=scenario["danger"],
                player_health=scenario["health"],
                player_energy=scenario["energy"],
                agents=scenario["agents"],
                symbols=[scenario["theme"]],
            )
            
            # Cycle çalıştır
            await core.cycle(world)
            completed_cycles = cycle + 1
            
            # Progress göster
            print_progress(cycle, TOTAL_CYCLES, scenario["theme"], mm.get_meta_state())
            
            # Her episode sonunda mini özet
            if (cycle + 1) % 100 == 0:
                print(f"\n\n📌 Episode {(cycle + 1) // 100} tamamlandı")
                meta = mm.get_meta_state()
                if meta:
                    print(f"   Health: {meta.global_cognitive_health.value:.3f}, "
                          f"Stability: {meta.emotional_stability.value:.3f}, "
                          f"Confidence: {meta.global_cognitive_health.confidence:.0%}")
                print()
            
            # Küçük bekleme (gerçekçi simülasyon için)
            await asyncio.sleep(0.05)
    
    except Exception as e:
        print(f"\n\n❌ Hata: {e}")
    
    finally:
        # Her durumda rapor göster
        await asyncio.sleep(0.5)
        await core.stop_logging({"completed_cycles": completed_cycles})
        print_report(mm, run_id, completed_cycles, start_time)


if __name__ == "__main__":
    asyncio.run(main())
