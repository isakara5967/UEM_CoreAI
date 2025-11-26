# demo_v0/world_state_builder.py
"""
World State Builder for Demo v0.

Applies events to WorldState, producing updated state.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import copy

# Import from world_generator
from .world_generator import GeneratedEvent


@dataclass
class WorldStateSnapshot:
    """
    Demo v0 WorldState representation.
    
    Compatible with UnifiedUEMCore.WorldState interface.
    """
    tick: int = 0
    danger_level: float = 0.0
    player_health: float = 1.0
    player_energy: float = 1.0
    objects: List[Dict[str, Any]] = field(default_factory=list)
    agents: List[Dict[str, Any]] = field(default_factory=list)
    symbols: List[str] = field(default_factory=list)
    
    # Demo v0 extras
    current_event: Optional[str] = None
    event_message: str = ""
    
    def to_core_worldstate(self):
        """
        Convert to UnifiedUEMCore.WorldState format.
        
        Returns dict that can be unpacked to WorldState constructor.
        """
        return {
            "tick": self.tick,
            "danger_level": self.danger_level,
            "player_health": self.player_health,
            "player_energy": self.player_energy,
            "objects": self.objects,
            "agents": self.agents,
            "symbols": self.symbols,
        }


class WorldStateBuilder:
    """
    Builds and updates WorldState based on events.
    
    Responsibilities:
    - Initialize world from scenario config
    - Apply event deltas to world state
    - Clamp values to valid ranges
    - Track state history (optional)
    """
    
    def __init__(self, initial_config: Dict[str, Any]):
        """
        Initialize builder with scenario's initial_world config.
        
        Args:
            initial_config: Dict with danger_level, player_health, player_energy
        """
        self.initial_config = initial_config
        self.current_state: Optional[WorldStateSnapshot] = None
        self.history: List[WorldStateSnapshot] = []
    
    def create_initial_state(self) -> WorldStateSnapshot:
        """Create initial world state from config."""
        self.current_state = WorldStateSnapshot(
            tick=0,
            danger_level=self.initial_config.get("danger_level", 0.2),
            player_health=self.initial_config.get("player_health", 1.0),
            player_energy=self.initial_config.get("player_energy", 0.8),
            objects=[],
            agents=[],
            symbols=[],
            current_event=None,
            event_message="Simulation started.",
        )
        return self.current_state
    
    def apply_event(
        self,
        tick: int,
        event: Optional[GeneratedEvent],
        previous_state: Optional[WorldStateSnapshot] = None,
    ) -> WorldStateSnapshot:
        """
        Apply event to world state, producing new state.
        
        Args:
            tick: Current simulation tick
            event: GeneratedEvent or None (no event this tick)
            previous_state: Previous WorldStateSnapshot (uses current_state if None)
        
        Returns:
            Updated WorldStateSnapshot
        """
        # Use provided state or current state
        if previous_state is not None:
            base_state = previous_state
        elif self.current_state is not None:
            base_state = self.current_state
        else:
            base_state = self.create_initial_state()
        
        # Start with copy of base values
        new_danger = base_state.danger_level
        new_health = base_state.player_health
        new_energy = base_state.player_energy
        new_objects = []  # Reset per-tick (transient)
        new_agents = []   # Reset per-tick (transient)
        new_symbols = []  # Reset per-tick (transient)
        
        current_event_name = None
        event_message = "Nothing notable happens."
        
        # Apply event deltas if event exists
        if event is not None:
            new_danger += event.danger_delta
            new_health += event.health_delta
            new_energy += event.energy_delta
            new_objects = copy.deepcopy(event.objects)
            new_agents = copy.deepcopy(event.agents)
            new_symbols = list(event.symbols)
            current_event_name = event.name
            event_message = event.message
        
        # Natural decay/recovery (subtle)
        new_danger = max(0.0, new_danger - 0.02)  # Danger slowly decreases
        new_energy = max(0.0, new_energy - 0.01)  # Energy slowly depletes
        
        # Clamp all values to valid ranges
        new_danger = self._clamp(new_danger, 0.0, 1.0)
        new_health = self._clamp(new_health, 0.0, 1.0)
        new_energy = self._clamp(new_energy, 0.0, 1.0)
        
        # Create new state
        new_state = WorldStateSnapshot(
            tick=tick,
            danger_level=new_danger,
            player_health=new_health,
            player_energy=new_energy,
            objects=new_objects,
            agents=new_agents,
            symbols=new_symbols,
            current_event=current_event_name,
            event_message=event_message,
        )
        
        # Update tracking
        self.history.append(new_state)
        self.current_state = new_state
        
        return new_state
    
    def apply_action_effects(
        self,
        action_name: str,
        outcome_valence: float,
    ) -> None:
        """
        Apply action outcome effects to current state.
        
        Called after UnifiedUEMCore returns ActionResult.
        Modifies current_state in place.
        """
        if self.current_state is None:
            return
        
        # Simple effect mapping
        if action_name == "flee" and outcome_valence > 0:
            self.current_state.danger_level = max(0.0, self.current_state.danger_level - 0.2)
        elif action_name == "attack" and outcome_valence > 0:
            self.current_state.danger_level = max(0.0, self.current_state.danger_level - 0.3)
        elif action_name == "help" and outcome_valence > 0:
            self.current_state.player_energy = max(0.0, self.current_state.player_energy - 0.1)
        elif action_name == "explore":
            self.current_state.player_energy = max(0.0, self.current_state.player_energy - 0.05)
    
    @staticmethod
    def _clamp(value: float, min_val: float, max_val: float) -> float:
        """Clamp value to range."""
        return max(min_val, min(max_val, value))
    
    def get_history(self) -> List[WorldStateSnapshot]:
        """Get state history."""
        return self.history
