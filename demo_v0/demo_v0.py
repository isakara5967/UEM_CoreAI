#!/usr/bin/env python3
# demo_v0/demo_v0.py
"""
UEM Demo v0 - Main Entry Point

Runs cognitive cycles with UnifiedUEMCore in a simulated environment.

Usage:
    python -m demo_v0.demo_v0 --scenario survival
    python -m demo_v0.demo_v0 --scenario exploration --ticks 30
    python -m demo_v0.demo_v0 --scenario social --verbose
    python -m demo_v0.demo_v0 --scenario survival --seed 42
"""

import argparse
import asyncio
import sys
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, '.')

# Import UEM Core
from core.unified_core import UnifiedUEMCore, create_unified_core

# Import demo modules
from .scenarios import get_scenario, list_scenarios
from .world_generator import WorldGenerator, GeneratedEvent
from .world_state_builder import WorldStateBuilder, WorldStateSnapshot
from .outcome_simulator import OutcomeSimulator
from .formatting import (
    format_header,
    format_cycle_minimal,
    format_verbose_phase,
    format_summary,
    format_error,
    Colors,
    colored,
)


# ============================================================================
# DEMO RUNNER
# ============================================================================

class DemoRunner:
    """
    Main Demo v0 runner.
    
    Orchestrates:
    - Scenario loading
    - World generation
    - UnifiedUEMCore cycles
    - Outcome simulation
    - Output formatting
    """
    
    def __init__(
        self,
        scenario_name: str,
        ticks: int = 20,
        verbose: bool = False,
        seed: int = None,
    ):
        self.scenario_name = scenario_name
        self.ticks = ticks
        self.verbose = verbose
        self.seed = seed
        
        # Load scenario
        self.config = get_scenario(scenario_name)
        
        # Override tick count if specified
        if ticks != self.config.get("tick_count", 20):
            self.ticks = ticks
        
        # Initialize components
        self.world_generator = WorldGenerator(self.config, seed=seed)
        self.world_builder = WorldStateBuilder(self.config.get("initial_world", {}))
        self.outcome_simulator = OutcomeSimulator(seed=seed)
        
        # Statistics
        self.action_counts: Dict[str, int] = {}
        self.valence_history: List[float] = []
        self.arousal_history: List[float] = []
        self.success_count: int = 0
    
    async def run(self) -> None:
        """Run the demo."""
        # Print header
        print(format_header(self.scenario_name, self.ticks))
        
        # Create UnifiedUEMCore
        try:
            core = create_unified_core(
                storage_type="memory",
                collect_metrics=self.verbose,
            )
        except Exception as e:
            print(format_error(f"Failed to create UnifiedUEMCore: {e}"))
            return
        
        # Initialize world state
        world_state = self.world_builder.create_initial_state()
        
        # Run cognitive cycles
        for tick in range(1, self.ticks + 1):
            try:
                await self._run_cycle(core, tick)
            except KeyboardInterrupt:
                print(colored("\n\n  Demo interrupted by user.", Colors.YELLOW))
                break
            except Exception as e:
                print(format_error(f"Cycle {tick} failed: {e}"))
                if self.verbose:
                    import traceback
                    traceback.print_exc()
                continue
        
        # Print summary
        self._print_summary()
    
    async def _run_cycle(self, core: UnifiedUEMCore, tick: int) -> None:
        """Run a single cognitive cycle."""
        
        # 1. Generate event
        event = self.world_generator.generate_event()
        
        # 2. Update world state
        world_state = self.world_builder.apply_event(tick, event)
        
        # 3. Convert to Core WorldState format
        core_world_dict = world_state.to_core_worldstate()
        
        # Create WorldState object for core
        # UnifiedUEMCore expects its own WorldState class
        from core.unified_core import UnifiedUEMCore
        CoreWorldState = None
        
        # Try to get WorldState class from unified_core
        try:
            # Access the nested WorldState class
            import importlib
            module = importlib.import_module('core.unified_core')
            # WorldState is defined inside unified_core.py
            from dataclasses import dataclass, field
            from typing import List, Dict, Any
            
            @dataclass
            class CoreWorldState:
                tick: int = 0
                danger_level: float = 0.0
                objects: List[Dict[str, Any]] = field(default_factory=list)
                agents: List[Dict[str, Any]] = field(default_factory=list)
                symbols: List[str] = field(default_factory=list)
                player_health: float = 1.0
                player_energy: float = 1.0
        except Exception:
            pass
        
        # Build world state for core
        core_world = CoreWorldState(
            tick=core_world_dict["tick"],
            danger_level=core_world_dict["danger_level"],
            objects=core_world_dict["objects"],
            agents=core_world_dict["agents"],
            symbols=core_world_dict["symbols"],
            player_health=core_world_dict["player_health"],
            player_energy=core_world_dict["player_energy"],
        )
        
        # 4. Run cognitive cycle
        cycle_result = await core.cycle(core_world)
        
        # 5. Extract action plan from result
        action_name = getattr(cycle_result, 'action_name', 'wait')
        target = getattr(cycle_result, 'target', None)
        reasoning = getattr(cycle_result, 'reasoning', [])
        
        # Handle if cycle_result is ActionResult or has action_plan
        if hasattr(cycle_result, 'action'):
            action_name = cycle_result.action
        if hasattr(cycle_result, 'action_plan'):
            action_plan = cycle_result.action_plan
            action_name = action_plan.action
            target = action_plan.target
            reasoning = action_plan.reasoning
        
        # 6. Simulate outcome
        from core.planning.types import ActionPlan
        action_plan = ActionPlan(
            action=action_name,
            target=target,
            reasoning=reasoning if isinstance(reasoning, list) else [],
        )
        
        outcome = self.outcome_simulator.simulate(action_plan, world_state)
        
        # 7. Record outcome for learning
        if hasattr(core, 'record_outcome'):
            core.record_outcome(outcome.outcome_type, outcome.outcome_valence)
        
        # 8. Apply action effects to world
        self.world_builder.apply_action_effects(action_name, outcome.outcome_valence)
        
        # 9. Get emotion state
        # Get emotion state (Sprint 0A-Fix: standardized API)
        emotion = {"valence": 0.0, "arousal": 0.5, "label": "neutral"}
        if hasattr(core, 'current_emotion') and core.current_emotion:
            emotion = core.current_emotion.copy()
        # Validation with fallback (no assert)
        if "label" not in emotion:
            if hasattr(core, 'emotion_core'):
                emotion["label"] = core.emotion_core._classify_emotion()
            else:
                emotion["label"] = "neutral"
            print(f"[WARN] emotion missing 'label', using fallback")
        
        # 10. Update statistics
        self._update_stats(action_name, emotion, outcome.success)
        
        # 11. Format output
        if self.verbose:
            self._print_verbose_cycle(tick, core, world_state, event, emotion, action_plan, outcome)
        else:
            print(format_cycle_minimal(
                tick=tick,
                total=self.ticks,
                world_state=world_state,
                emotion=emotion,
                action_name=action_name,
                target=target,
                reasoning=reasoning if isinstance(reasoning, list) else [],
                outcome_type=outcome.outcome_type,
                outcome_valence=outcome.outcome_valence,
                success=outcome.success,
            ))
    
    def _print_verbose_cycle(
        self,
        tick: int,
        core: UnifiedUEMCore,
        world_state: WorldStateSnapshot,
        event: GeneratedEvent,
        emotion: Dict[str, Any],
        action_plan,
        outcome,
    ) -> None:
        """Print verbose cycle output with all phases."""
        from .formatting import format_tick_header, format_world_state
        
        print(format_tick_header(tick, self.ticks))
        print(format_world_state(world_state))
        
        # Phase details
        print(format_verbose_phase("Phase 1: PERCEPTION", {
            "event": event.name if event else "None",
            "symbols": world_state.symbols,
            "agents": len(world_state.agents),
            "objects": len(world_state.objects),
        }))
        
        print(format_verbose_phase("Phase 4: APPRAISAL", {
            "valence": emotion.get("valence", 0.0),
            "arousal": emotion.get("arousal", 0.5),
            "emotion": emotion.get("label", "neutral"),
        }))
        
        print(format_verbose_phase("Phase 6: PLANNING", {
            "action": action_plan.action,
            "target": action_plan.target,
            "reasoning": action_plan.reasoning[:2] if action_plan.reasoning else [],
        }))
        
        print(format_verbose_phase("Phase 8: EXECUTION", {
            "success": outcome.success,
            "outcome_type": outcome.outcome_type,
            "outcome_valence": outcome.outcome_valence,
        }))
        
        print(format_verbose_phase("Phase 9: LEARNING", {
            "somatic_update": outcome.success,
            "memory_stored": True,
        }))
    
    def _update_stats(self, action: str, emotion: Dict[str, Any], success: bool) -> None:
        """Update running statistics."""
        # Action counts
        self.action_counts[action] = self.action_counts.get(action, 0) + 1
        
        # Emotion history
        self.valence_history.append(emotion.get("valence", 0.0))
        self.arousal_history.append(emotion.get("arousal", 0.5))
        
        # Success count
        if success:
            self.success_count += 1
    
    def _print_summary(self) -> None:
        """Print end-of-demo summary."""
        total = len(self.valence_history) or 1
        avg_valence = sum(self.valence_history) / total
        avg_arousal = sum(self.arousal_history) / total
        success_rate = self.success_count / total
        
        print(format_summary(
            total_ticks=total,
            action_counts=self.action_counts,
            avg_valence=avg_valence,
            avg_arousal=avg_arousal,
            success_rate=success_rate,
        ))


# ============================================================================
# CLI
# ============================================================================

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="UEM Demo v0 - Cognitive Cycle Demonstration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m demo_v0.demo_v0 --scenario survival
  python -m demo_v0.demo_v0 --scenario exploration --ticks 30
  python -m demo_v0.demo_v0 --scenario social --verbose
  python -m demo_v0.demo_v0 --scenario survival --seed 42

Available scenarios:
  - survival:    Danger-heavy, tests flee/attack decisions
  - exploration: Resource-heavy, tests curiosity/exploration
  - social:      NPC-heavy, tests empathy/help decisions
        """,
    )
    
    parser.add_argument(
        "--scenario", "-s",
        type=str,
        choices=list_scenarios(),
        default="survival",
        help="Scenario to run (default: survival)",
    )
    
    parser.add_argument(
        "--ticks", "-t",
        type=int,
        default=20,
        help="Number of ticks to run (default: 20)",
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output with all 9 phases",
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )
    
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()
    
    runner = DemoRunner(
        scenario_name=args.scenario,
        ticks=args.ticks,
        verbose=args.verbose,
        seed=args.seed,
    )
    
    await runner.run()


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Handle Windows event loop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())
