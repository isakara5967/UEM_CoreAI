#!/usr/bin/env python3
"""
UEM Scenario Runner
===================
Gerçek test senaryolarını çalıştırır.

Kullanım:
    python scenarios/scenario_runner.py scenarios/combat_ambush.yaml
    python scenarios/scenario_runner.py scenarios/ --all
    python scenarios/scenario_runner.py scenarios/social_trust.yaml --verbose
"""

import asyncio
import argparse
import yaml
import sys
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

# Project root'u path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.unified_core import UnifiedUEMCore, WorldState


@dataclass
class ScenarioResult:
    """Senaryo sonucu."""
    name: str
    total_cycles: int
    duration_ms: float
    actions: List[str] = field(default_factory=list)
    empathy_scores: List[float] = field(default_factory=list)
    final_empathy: float = 0.0
    final_trust: float = 0.0
    final_cooperation: float = 0.0
    meta_state: Dict[str, float] = field(default_factory=dict)
    anomalies: List[str] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None


def load_scenario(filepath: str) -> Dict[str, Any]:
    """YAML senaryo dosyasını yükle."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def build_world_state(cycle_def: Dict[str, Any], tick: int) -> WorldState:
    """Cycle tanımından WorldState oluştur."""
    agents = []
    for agent_def in cycle_def.get('agents', []):
        agents.append({
            'id': agent_def.get('id', f'agent_{len(agents)}'),
            'health': agent_def.get('health', 0.5),
            'energy': agent_def.get('energy', 0.5),
            'valence': agent_def.get('valence', 0.0),
            'arousal': agent_def.get('arousal', 0.5),
            'danger': agent_def.get('danger', 0.0),
            'relation': agent_def.get('relation', agent_def.get('relationship', 0.0)),
        })
    
    return WorldState(
        tick=tick,
        danger_level=cycle_def.get('danger_level', 0.0),
        player_health=cycle_def.get('player_health', 1.0),
        player_energy=cycle_def.get('player_energy', 1.0),
        agents=agents,
        objects=cycle_def.get('objects', []),
    )


def interpolate_cycles(scenario: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Keyframe'ler arasını doldur.
    
    Senaryo 'keyframes' içeriyorsa, aradaki cycle'ları interpolate eder.
    'cycles' içeriyorsa direkt kullanır.
    """
    if 'cycles' in scenario:
        return scenario['cycles']
    
    if 'keyframes' not in scenario:
        return []
    
    keyframes = scenario['keyframes']
    cycles = []
    
    for i, kf in enumerate(keyframes):
        start_tick = kf['tick']
        
        # Son keyframe mi?
        if i == len(keyframes) - 1:
            cycles.append(kf)
            break
        
        next_kf = keyframes[i + 1]
        end_tick = next_kf['tick']
        
        # Bu keyframe'den sonrakine kadar interpolate et
        for t in range(start_tick, end_tick):
            progress = (t - start_tick) / (end_tick - start_tick)
            
            interpolated = {'tick': t}
            
            # Scalar değerleri interpolate et
            for key in ['danger_level', 'player_health', 'player_energy']:
                if key in kf and key in next_kf:
                    interpolated[key] = kf[key] + (next_kf[key] - kf[key]) * progress
                elif key in kf:
                    interpolated[key] = kf[key]
            
            # Agent'ları interpolate et
            if 'agents' in kf:
                interpolated['agents'] = []
                for j, agent in enumerate(kf['agents']):
                    new_agent = {'id': agent['id']}
                    
                    # Sonraki keyframe'de aynı agent var mı?
                    next_agent = None
                    if 'agents' in next_kf:
                        for na in next_kf['agents']:
                            if na['id'] == agent['id']:
                                next_agent = na
                                break
                    
                    for key in ['health', 'energy', 'valence', 'arousal', 'danger', 'relation']:
                        if key in agent:
                            if next_agent and key in next_agent:
                                new_agent[key] = agent[key] + (next_agent[key] - agent[key]) * progress
                            else:
                                new_agent[key] = agent[key]
                    
                    interpolated['agents'].append(new_agent)
            
            cycles.append(interpolated)
    
    return cycles


async def run_scenario(filepath: str, verbose: bool = False) -> ScenarioResult:
    """Tek bir senaryoyu çalıştır."""
    import time
    
    scenario = load_scenario(filepath)
    name = scenario.get('name', Path(filepath).stem)
    description = scenario.get('description', '')
    
    print(f"\n{'='*60}")
    print(f"🎬 Senaryo: {name}")
    print(f"📝 {description}")
    print(f"{'='*60}")
    
    result = ScenarioResult(name=name, total_cycles=0, duration_ms=0)
    
    try:
        core = UnifiedUEMCore()
        await core.start_logging()
        
        cycles = interpolate_cycles(scenario)
        result.total_cycles = len(cycles)
        
        start_time = time.perf_counter()
        
        for i, cycle_def in enumerate(cycles):
            tick = cycle_def.get('tick', i)
            world = build_world_state(cycle_def, tick)
            
            action_result = await core.cycle(world)
            result.actions.append(action_result.action_name)
            
            # Empathy skoru
            if core._empathy_results:
                avg_empathy = sum(r.empathy_level for r in core._empathy_results) / len(core._empathy_results)
                result.empathy_scores.append(avg_empathy)
            else:
                result.empathy_scores.append(0.0)
            
            if verbose:
                emp = result.empathy_scores[-1]
                agents = ', '.join([a['id'] for a in cycle_def.get('agents', [])])
                print(f"  Tick {tick:3d}: action={action_result.action_name:12s} empathy={emp:.3f} agents=[{agents}]")
        
        result.duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Final metrikleri al
        if core._empathy_results:
            result.final_empathy = sum(r.empathy_level for r in core._empathy_results) / len(core._empathy_results)
        
        if core._metamind_core:
            social = core._metamind_core.social_pipeline.get_metrics()
            result.final_trust = social.trust_level
            result.final_cooperation = social.cooperation_score
            
            meta = core._metamind_core.get_meta_state()
            if meta:
                result.meta_state = {
                    'global_health': meta.global_cognitive_health,
                    'emotional_stability': meta.emotional_stability,
                    'ethical_alignment': meta.ethical_alignment,
                    'exploration_bias': meta.exploration_bias,
                }
        
        await asyncio.sleep(0.5)
        await core.stop_logging()
        
    except Exception as e:
        result.success = False
        result.error = str(e)
        print(f"❌ Hata: {e}")
    
    return result


def print_result(result: ScenarioResult):
    """Sonucu yazdır."""
    status = "✅ BAŞARILI" if result.success else "❌ BAŞARISIZ"
    
    print(f"\n📊 Sonuçlar:")
    print(f"   Status: {status}")
    print(f"   Cycles: {result.total_cycles}")
    print(f"   Süre: {result.duration_ms:.1f}ms ({result.duration_ms/result.total_cycles:.2f}ms/cycle)")
    
    # Action dağılımı
    action_counts = {}
    for a in result.actions:
        action_counts[a] = action_counts.get(a, 0) + 1
    print(f"   Actions: {action_counts}")
    
    # Empathy trendi
    if result.empathy_scores:
        first_5 = sum(result.empathy_scores[:5]) / min(5, len(result.empathy_scores))
        last_5 = sum(result.empathy_scores[-5:]) / min(5, len(result.empathy_scores))
        trend = "📈" if last_5 > first_5 else "📉" if last_5 < first_5 else "➡️"
        print(f"   Empathy: {first_5:.3f} → {last_5:.3f} {trend}")
    
    print(f"   Final Trust: {result.final_trust:.3f}")
    print(f"   Final Cooperation: {result.final_cooperation:.3f}")
    
    if result.meta_state:
        print(f"   MetaState:")
        for k, v in result.meta_state.items():
            print(f"      {k}: {getattr(v, "value", v):.3f}")
    
    if result.error:
        print(f"   Error: {result.error}")


async def run_all_scenarios(directory: str, verbose: bool = False) -> List[ScenarioResult]:
    """Klasördeki tüm senaryoları çalıştır."""
    results = []
    
    yaml_files = sorted(Path(directory).glob("*.yaml"))
    
    print(f"\n🚀 {len(yaml_files)} senaryo bulundu")
    
    for filepath in yaml_files:
        result = await run_scenario(str(filepath), verbose)
        print_result(result)
        results.append(result)
    
    # Özet
    print(f"\n{'='*60}")
    print(f"📋 ÖZET")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results if r.success)
    print(f"Toplam: {len(results)} senaryo, {success_count} başarılı")
    
    total_cycles = sum(r.total_cycles for r in results)
    total_time = sum(r.duration_ms for r in results)
    print(f"Toplam cycle: {total_cycles}, Süre: {total_time:.1f}ms")
    
    avg_empathy = sum(r.final_empathy for r in results if r.success) / max(1, success_count)
    avg_trust = sum(r.final_trust for r in results if r.success) / max(1, success_count)
    print(f"Ortalama empathy: {avg_empathy:.3f}, trust: {avg_trust:.3f}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="UEM Scenario Runner")
    parser.add_argument("path", help="Senaryo dosyası veya klasör")
    parser.add_argument("--all", action="store_true", help="Klasördeki tüm senaryoları çalıştır")
    parser.add_argument("--verbose", "-v", action="store_true", help="Detaylı çıktı")
    
    args = parser.parse_args()
    
    if args.all or os.path.isdir(args.path):
        asyncio.run(run_all_scenarios(args.path, args.verbose))
    else:
        result = asyncio.run(run_scenario(args.path, args.verbose))
        print_result(result)


if __name__ == "__main__":
    main()
