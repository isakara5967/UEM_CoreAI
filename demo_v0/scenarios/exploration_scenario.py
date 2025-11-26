# demo_v0/scenarios/exploration_scenario.py
"""
Exploration Scenario - Resource/discovery-heavy scenario for Demo v0.

Focus: Curiosity, resource gathering, low threat environment.

UPDATED: Planning rebalance - added planning_weights and softmax_temperature
"""

SCENARIO_CONFIG = {
    "name": "exploration",
    "description": "Keşif ve kaynak toplama ağırlıklı senaryo",
    
    # Event generation weights
    "event_weights": {
        "danger": 0.15,
        "resource": 0.50,
        "social": 0.15,
        "environmental": 0.20,
    },
    
    # =========================================================================
    # NEW: Planning Rebalance Parameters
    # =========================================================================
    "planning_weights": {
        "safety": 0.3,       # Lower - environment is safer
        "curiosity": 0.5,    # High - exploration focus
        "empathy": 0.2,      # Moderate
    },
    
    "softmax_temperature": 0.7,  # High T = more stochastic (exploration needs variety)
    
    # =========================================================================
    
    "initial_world": {
        "danger_level": 0.1,
        "player_health": 1.0,
        "player_energy": 0.9,
    },
    
    "tick_count": 20,
    
    # Scenario-specific events
    "events": {
        "FOUND_TREASURE": {
            "category": "resource",
            "danger_delta": 0.0,
            "symbols": ["TREASURE", "REWARD"],
            "objects": [{"type": "treasure", "id": "chest_1"}],
            "message": "You discover a hidden treasure chest!",
        },
        "FOUND_FOOD": {
            "category": "resource",
            "danger_delta": -0.05,
            "energy_delta": +0.2,
            "symbols": ["RESOURCE_NEARBY"],
            "objects": [{"type": "food", "id": "food_1"}],
            "message": "You discover edible berries.",
        },
        "FOUND_WATER": {
            "category": "resource",
            "danger_delta": -0.05,
            "energy_delta": +0.15,
            "symbols": ["RESOURCE_NEARBY"],
            "objects": [{"type": "water", "id": "water_1"}],
            "message": "A fresh water stream appears.",
        },
        "SAFE_ZONE": {
            "category": "resource",
            "danger_delta": -0.3,
            "symbols": ["SAFE"],
            "message": "You find a sheltered safe zone.",
        },
        "ENEMY_APPEARED": {
            "category": "danger",
            "danger_delta": +0.3,
            "symbols": ["DANGER_MEDIUM"],
            "agents": [{"type": "enemy", "id": "creature_1"}],
            "message": "A wild creature blocks your path.",
        },
        "WEATHER_RAIN": {
            "category": "environmental",
            "danger_delta": +0.05,
            "energy_delta": -0.05,
            "symbols": ["WEATHER_BAD"],
            "message": "Rain begins to fall.",
        },
        "NPC_FRIENDLY": {
            "category": "social",
            "danger_delta": -0.1,
            "symbols": ["FRIENDLY"],
            "agents": [{"type": "npc", "id": "trader_1", "state": "friendly"}],
            "message": "A friendly traveler waves at you.",
        },
    },
}


def get_config():
    """Return scenario configuration."""
    return SCENARIO_CONFIG
