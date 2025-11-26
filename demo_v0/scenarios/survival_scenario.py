# demo_v0/scenarios/survival_scenario.py
"""
Survival Scenario - Danger-heavy scenario for Demo v0.

Focus: High threat environment, flee/attack decisions, somatic learning.
"""

SCENARIO_CONFIG = {
    "name": "survival",
    "description": "Tehlike ağırlıklı hayatta kalma senaryosu",
    
    "event_weights": {
        "danger": 0.50,
        "resource": 0.20,
        "social": 0.10,
        "environmental": 0.20,
    },
    
    "initial_world": {
        "danger_level": 0.3,
        "player_health": 1.0,
        "player_energy": 0.8,
    },
    
    "tick_count": 20,
    
    # Scenario-specific events with deltas
    "events": {
        # Danger events
        "ENEMY_APPEARED": {
            "category": "danger",
            "danger_delta": +0.4,
            "symbols": ["DANGER_HIGH", "ENEMY_NEARBY"],
            "agents": [{"type": "enemy", "id": "monster_1"}],
            "message": "A hostile creature emerges from the shadows!",
        },
        "TRAP_DETECTED": {
            "category": "danger",
            "danger_delta": +0.2,
            "symbols": ["DANGER_MEDIUM", "TRAP"],
            "message": "You notice a hidden trap ahead.",
        },
        "LOUD_NOISE": {
            "category": "danger",
            "danger_delta": +0.15,
            "symbols": ["ALERT"],
            "message": "A loud noise echoes through the area.",
        },
        
        # Resource events
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
        
        # Social events
        "NPC_DISTRESSED": {
            "category": "social",
            "danger_delta": +0.1,
            "symbols": ["OTHER_DISTRESS"],
            "agents": [{"type": "npc", "id": "npc_1", "state": "distressed"}],
            "message": "A distressed traveler calls for help.",
        },
        "NPC_REQUEST_HELP": {
            "category": "social",
            "danger_delta": 0.0,
            "symbols": ["SOCIAL_REQUEST"],
            "agents": [{"type": "npc", "id": "npc_2", "state": "needy"}],
            "message": "Someone approaches asking for assistance.",
        },
        
        # Environmental events
        "WEATHER_RAIN": {
            "category": "environmental",
            "danger_delta": +0.05,
            "energy_delta": -0.05,
            "symbols": ["WEATHER_BAD"],
            "message": "Rain begins to fall.",
        },
        "WEATHER_STORM": {
            "category": "environmental",
            "danger_delta": +0.2,
            "energy_delta": -0.1,
            "symbols": ["WEATHER_SEVERE", "DANGER_MEDIUM"],
            "message": "A violent storm approaches!",
        },
    },
}


def get_config():
    """Return scenario configuration."""
    return SCENARIO_CONFIG
