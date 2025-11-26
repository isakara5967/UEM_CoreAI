# demo_v0/scenarios/__init__.py
"""
Scenario loader for Demo v0.
"""

from typing import Dict, Any

def get_scenario(name: str) -> Dict[str, Any]:
    """Load scenario config by name."""
    if name == "survival":
        from .survival_scenario import SCENARIO_CONFIG
    elif name == "exploration":
        from .exploration_scenario import SCENARIO_CONFIG
    elif name == "social":
        from .social_scenario import SCENARIO_CONFIG
    else:
        raise ValueError(f"Unknown scenario: {name}. Available: survival, exploration, social")
    
    return SCENARIO_CONFIG


def list_scenarios() -> list:
    """List available scenario names."""
    return ["survival", "exploration", "social"]
