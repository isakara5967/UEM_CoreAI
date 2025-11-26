# demo_v0/outcome_simulator.py
"""
Outcome Simulator for Demo v0.

Simulates action outcomes when no real world interface exists.
Returns ActionResult compatible with UnifiedUEMCore learning phase.
"""

from typing import Optional
import random

# Import real UEM Core types
from core.planning.types import ActionPlan, StateDelta
from core.unified_types import ActionResult

# Import demo types
from .world_state_builder import WorldStateSnapshot


# ============================================================================
# OUTCOME MAPPINGS
# ============================================================================

# Base success rates for actions
ACTION_SUCCESS_RATES = {
    "flee": 0.85,       # Usually successful
    "attack": 0.60,     # Risky
    "help": 0.90,       # Usually works
    "explore": 0.95,    # Safe action
    "approach": 0.80,   # Moderate risk
    "wait": 1.0,        # Always succeeds
}

# Outcome types and valences for success/failure
OUTCOME_TEMPLATES = {
    "flee": {
        "success": ("escaped", +0.3, (-0.0, -0.3, +0.1)),
        "failure": ("caught", -0.4, (0.0, +0.1, -0.2)),
    },
    "attack": {
        "success": ("defeated_threat", +0.4, (0.0, -0.4, +0.1)),
        "failure": ("attack_failed", -0.3, (0.0, +0.1, -0.2)),
    },
    "help": {
        "success": ("helped_successfully", +0.5, (-0.1, 0.0, +0.3)),
        "failure": ("help_rejected", -0.1, (0.0, 0.0, -0.1)),
    },
    "explore": {
        "success": ("discovered_something", +0.2, (+0.1, +0.05, +0.1)),
        "failure": ("nothing_found", 0.0, (0.0, 0.0, 0.0)),
    },
    "approach": {
        "success": ("approached_safely", +0.2, (+0.1, 0.0, +0.1)),
        "failure": ("approach_dangerous", -0.2, (0.0, +0.2, -0.1)),
    },
    "wait": {
        "success": ("observed", +0.05, (0.0, -0.05, 0.0)),
        "failure": ("observed", 0.0, (0.0, 0.0, 0.0)),
    },
}


# ============================================================================
# SIMULATOR
# ============================================================================

class OutcomeSimulator:
    """
    Simulates action outcomes for Demo v0.
    
    Takes ActionPlan + WorldState and produces ActionResult.
    Uses probabilistic outcomes influenced by world state.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize simulator with optional random seed."""
        if seed is not None:
            random.seed(seed)
    
    def simulate(
        self,
        action_plan: ActionPlan,
        world_state: WorldStateSnapshot,
    ) -> ActionResult:
        """
        Simulate outcome of an action.
        
        Args:
            action_plan: The planned action from UnifiedUEMCore
            world_state: Current world state
        
        Returns:
            ActionResult with outcome details
        """
        action = action_plan.action
        target = action_plan.target
        
        # Calculate success probability (modified by world state)
        base_rate = ACTION_SUCCESS_RATES.get(action, 0.7)
        modified_rate = self._modify_success_rate(base_rate, action, world_state)
        
        # Determine success/failure
        success = random.random() < modified_rate
        
        # Get outcome template
        template = OUTCOME_TEMPLATES.get(action, {
            "success": ("action_completed", +0.1, (0.0, 0.0, 0.0)),
            "failure": ("action_failed", -0.1, (0.0, 0.0, 0.0)),
        })
        
        outcome_key = "success" if success else "failure"
        outcome_type, base_valence, effect_tuple = template[outcome_key]
        
        # Modify valence based on context
        outcome_valence = self._modify_valence(base_valence, action, world_state, success)
        
        # Build StateDelta
        actual_effect: StateDelta = effect_tuple
        
        return ActionResult(
            action_name=action,
            target=target,
            success=success,
            outcome_type=outcome_type,
            outcome_valence=outcome_valence,
            actual_effect=actual_effect,
        )
    
    def _modify_success_rate(
        self,
        base_rate: float,
        action: str,
        world_state: WorldStateSnapshot,
    ) -> float:
        """Modify success rate based on world state."""
        rate = base_rate
        
        # High danger reduces success for risky actions
        if action in ("attack", "approach") and world_state.danger_level > 0.6:
            rate -= 0.15
        
        # Low energy reduces success
        if world_state.player_energy < 0.3:
            rate -= 0.1
        
        # Low health makes fleeing more desperate (higher success)
        if action == "flee" and world_state.player_health < 0.4:
            rate += 0.1
        
        # Clamp to valid range
        return max(0.1, min(0.95, rate))
    
    def _modify_valence(
        self,
        base_valence: float,
        action: str,
        world_state: WorldStateSnapshot,
        success: bool,
    ) -> float:
        """Modify outcome valence based on context."""
        valence = base_valence
        
        # Successful escape from high danger = more relief
        if action == "flee" and success and world_state.danger_level > 0.5:
            valence += 0.1
        
        # Helping when already low energy = more costly feeling
        if action == "help" and world_state.player_energy < 0.4:
            valence -= 0.1
        
        # Attack success in high danger = greater triumph
        if action == "attack" and success and world_state.danger_level > 0.6:
            valence += 0.15
        
        # Clamp to valid range
        return max(-1.0, min(1.0, valence))


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def simulate_outcome(
    action_plan: ActionPlan,
    world_state: WorldStateSnapshot,
) -> ActionResult:
    """
    Convenience function to simulate outcome.
    
    Creates a temporary simulator and runs once.
    For repeated use, instantiate OutcomeSimulator directly.
    """
    simulator = OutcomeSimulator()
    return simulator.simulate(action_plan, world_state)
