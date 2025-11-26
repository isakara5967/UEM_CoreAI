# demo_v0/world_generator.py
"""
World Generator for Demo v0.

Generates random events based on scenario configuration.
"""

import random
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


# Default event probability per tick
EVENT_PROBABILITY = 0.5


@dataclass
class GeneratedEvent:
    """Represents a generated world event."""
    name: str
    category: str
    danger_delta: float = 0.0
    energy_delta: float = 0.0
    health_delta: float = 0.0
    symbols: List[str] = field(default_factory=list)
    objects: List[Dict[str, Any]] = field(default_factory=list)
    agents: List[Dict[str, Any]] = field(default_factory=list)
    message: str = ""


class WorldGenerator:
    """
    Generates events based on scenario configuration.
    
    Usage:
        generator = WorldGenerator(scenario_config)
        event = generator.generate_event()  # May return None
    """
    
    def __init__(
        self,
        scenario_config: Dict[str, Any],
        event_probability: float = EVENT_PROBABILITY,
        seed: Optional[int] = None,
    ):
        self.config = scenario_config
        self.event_probability = event_probability
        self.events = scenario_config.get("events", {})
        self.weights = scenario_config.get("event_weights", {})
        
        # Build category -> event_names mapping
        self._category_events: Dict[str, List[str]] = {}
        for event_name, event_data in self.events.items():
            category = event_data.get("category", "unknown")
            if category not in self._category_events:
                self._category_events[category] = []
            self._category_events[category].append(event_name)
        
        # Set random seed if provided
        if seed is not None:
            random.seed(seed)
    
    def generate_event(self) -> Optional[GeneratedEvent]:
        """
        Generate a random event based on scenario weights.
        
        Returns:
            GeneratedEvent or None (if no event this tick)
        """
        # Check if event occurs this tick
        if random.random() > self.event_probability:
            return None
        
        # Select category based on weights
        category = self._select_category()
        if category is None:
            return None
        
        # Select random event from category
        event_name = self._select_event(category)
        if event_name is None:
            return None
        
        # Build event object
        event_data = self.events[event_name]
        return GeneratedEvent(
            name=event_name,
            category=category,
            danger_delta=event_data.get("danger_delta", 0.0),
            energy_delta=event_data.get("energy_delta", 0.0),
            health_delta=event_data.get("health_delta", 0.0),
            symbols=event_data.get("symbols", []),
            objects=event_data.get("objects", []),
            agents=event_data.get("agents", []),
            message=event_data.get("message", ""),
        )
    
    def _select_category(self) -> Optional[str]:
        """Select event category based on weights."""
        if not self.weights:
            return None
        
        categories = list(self.weights.keys())
        weights = list(self.weights.values())
        
        # Normalize weights
        total = sum(weights)
        if total == 0:
            return None
        
        normalized = [w / total for w in weights]
        
        # Random selection
        return random.choices(categories, weights=normalized, k=1)[0]
    
    def _select_event(self, category: str) -> Optional[str]:
        """Select random event from category."""
        events = self._category_events.get(category, [])
        if not events:
            return None
        return random.choice(events)
    
    def get_initial_world(self) -> Dict[str, Any]:
        """Get initial world state from scenario config."""
        return self.config.get("initial_world", {
            "danger_level": 0.2,
            "player_health": 1.0,
            "player_energy": 0.8,
        })
