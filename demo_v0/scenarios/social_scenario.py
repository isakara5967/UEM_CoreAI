# demo_v0/scenarios/social_scenario.py
"""
Social Scenario - Empathy/interaction-heavy scenario for Demo v0.

Focus: NPC interactions, help decisions, empathy system testing.

UPDATED: Planning rebalance - added planning_weights and softmax_temperature
"""

SCENARIO_CONFIG = {
    "name": "social",
    "description": "Empati ve sosyal etkileşim ağırlıklı senaryo",
    
    # Event generation weights
    "event_weights": {
        "danger": 0.10,
        "resource": 0.20,
        "social": 0.55,
        "environmental": 0.15,
    },
    
    # =========================================================================
    # NEW: Planning Rebalance Parameters
    # =========================================================================
    "planning_weights": {
        "safety": 0.25,      # Lower - focus is social
        "curiosity": 0.25,   # Moderate
        "empathy": 0.5,      # High - social focus
    },
    
    "softmax_temperature": 0.5,  # Medium T = balanced (social needs some predictability)
    
    # =========================================================================
    
    "initial_world": {
        "danger_level": 0.15,
        "player_health": 1.0,
        "player_energy": 0.85,
    },
    
    "tick_count": 20,
    
    "events": {
        # Social events (dominant)
        "NPC_DISTRESSED": {
            "category": "social",
            "danger_delta": +0.1,
            "symbols": ["OTHER_DISTRESS", "EMPATHY_TRIGGER"],
            "agents": [{"type": "npc", "id": "victim_1", "state": "distressed"}],
            "message": "A distressed traveler calls for help.",
        },
        "NPC_REQUEST_HELP": {
            "category": "social",
            "danger_delta": 0.0,
            "symbols": ["SOCIAL_REQUEST"],
            "agents": [{"type": "npc", "id": "requester_1", "state": "needy"}],
            "message": "Someone approaches asking for assistance.",
        },
        "NPC_INJURED": {
            "category": "social",
            "danger_delta": +0.05,
            "symbols": ["OTHER_INJURED", "EMPATHY_TRIGGER"],
            "agents": [{"type": "npc", "id": "injured_1", "state": "injured"}],
            "message": "An injured person lies on the ground.",
        },
        "NPC_GRATEFUL": {
            "category": "social",
            "danger_delta": -0.1,
            "symbols": ["POSITIVE_SOCIAL"],
            "agents": [{"type": "npc", "id": "grateful_1", "state": "grateful"}],
            "message": "Someone thanks you warmly for past help.",
        },
        "NPC_CONFLICT": {
            "category": "social",
            "danger_delta": +0.2,
            "symbols": ["SOCIAL_CONFLICT"],
            "agents": [
                {"type": "npc", "id": "person_a", "state": "angry"},
                {"type": "npc", "id": "person_b", "state": "scared"},
            ],
            "message": "Two people are in a heated argument.",
        },
        
        # Light danger
        "THREAT_TO_NPC": {
            "category": "danger",
            "danger_delta": +0.25,
            "symbols": ["OTHER_THREATENED", "EMPATHY_TRIGGER"],
            "agents": [
                {"type": "npc", "id": "threatened_1", "state": "threatened"},
                {"type": "enemy", "id": "aggressor_1"},
            ],
            "message": "A hostile creature threatens a helpless traveler!",
        },
        
        # Resources
        "FOUND_FOOD": {
            "category": "resource",
            "danger_delta": -0.05,
            "energy_delta": +0.2,
            "symbols": ["RESOURCE_NEARBY"],
            "objects": [{"type": "food", "id": "food_1"}],
            "message": "You find some food to share.",
        },
        
        # Environmental
        "WEATHER_CALM": {
            "category": "environmental",
            "danger_delta": -0.05,
            "symbols": ["PEACEFUL"],
            "message": "The weather is calm and pleasant.",
        },
    },
}


def get_config():
    """Return scenario configuration."""
    return SCENARIO_CONFIG
