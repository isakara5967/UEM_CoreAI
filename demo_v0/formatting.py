# demo_v0/formatting.py
"""
Console Formatting for Demo v0.

Provides styled output for demo visualization.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Import demo types
from .world_state_builder import WorldStateSnapshot


# ============================================================================
# ANSI COLOR CODES
# ============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Foreground
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    
    # Background
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"


def colored(text: str, color: str) -> str:
    """Wrap text with color code."""
    return f"{color}{text}{Colors.RESET}"


# ============================================================================
# FORMATTERS
# ============================================================================

def format_header(scenario_name: str, total_ticks: int) -> str:
    """Format demo header."""
    width = 66
    border = "═" * width
    
    lines = [
        "",
        colored(f"╔{border}╗", Colors.CYAN),
        colored(f"║{'UEM Demo v0':^{width}}║", Colors.CYAN + Colors.BOLD),
        colored(f"║{f'Scenario: {scenario_name} | Ticks: {total_ticks}':^{width}}║", Colors.CYAN),
        colored(f"╚{border}╝", Colors.CYAN),
        "",
    ]
    return "\n".join(lines)


def format_tick_header(tick: int, total: int) -> str:
    """Format tick header."""
    progress = f"[{tick}/{total}]"
    bar_width = 20
    filled = int((tick / total) * bar_width)
    bar = "█" * filled + "░" * (bar_width - filled)
    
    return colored(f"\n{'─' * 66}\n  TICK {tick:02d} {bar} {progress}", Colors.BOLD)


def format_world_state(state: WorldStateSnapshot) -> str:
    """Format world state display."""
    # Color code danger level
    danger = state.danger_level
    if danger >= 0.7:
        danger_str = colored(f"{danger:.2f}", Colors.RED + Colors.BOLD)
    elif danger >= 0.4:
        danger_str = colored(f"{danger:.2f}", Colors.YELLOW)
    else:
        danger_str = colored(f"{danger:.2f}", Colors.GREEN)
    
    # Color code health
    health = state.player_health
    if health <= 0.3:
        health_str = colored(f"{health:.2f}", Colors.RED + Colors.BOLD)
    elif health <= 0.6:
        health_str = colored(f"{health:.2f}", Colors.YELLOW)
    else:
        health_str = colored(f"{health:.2f}", Colors.GREEN)
    
    # Color code energy
    energy = state.player_energy
    if energy <= 0.3:
        energy_str = colored(f"{energy:.2f}", Colors.YELLOW)
    else:
        energy_str = colored(f"{energy:.2f}", Colors.BLUE)
    
    lines = [
        f"  ┌─ World State {'─' * 49}",
        f"  │ Danger: {danger_str}  Health: {health_str}  Energy: {energy_str}",
    ]
    
    # Event info
    if state.current_event:
        event_color = Colors.RED if "ENEMY" in state.current_event or "TRAP" in state.current_event else Colors.YELLOW
        lines.append(f"  │ Event: {colored(state.current_event, event_color)}")
        lines.append(f"  │ {Colors.DIM}\"{state.event_message}\"{Colors.RESET}")
    else:
        lines.append(f"  │ Event: {colored('None', Colors.GRAY)}")
    
    lines.append(f"  └{'─' * 65}")
    
    return "\n".join(lines)


def format_emotion(emotion_data: Dict[str, Any]) -> str:
    """Format emotion display."""
    valence = emotion_data.get("valence", 0.0)
    arousal = emotion_data.get("arousal", 0.5)
    label = emotion_data.get("emotion_label", "neutral")
    
    # Color code valence
    if valence >= 0.3:
        valence_str = colored(f"{valence:+.2f}", Colors.GREEN)
    elif valence <= -0.3:
        valence_str = colored(f"{valence:+.2f}", Colors.RED)
    else:
        valence_str = colored(f"{valence:+.2f}", Colors.GRAY)
    
    # Color code arousal
    if arousal >= 0.7:
        arousal_str = colored(f"{arousal:.2f}", Colors.MAGENTA + Colors.BOLD)
    else:
        arousal_str = colored(f"{arousal:.2f}", Colors.MAGENTA)
    
    # Emotion label color
    emotion_colors = {
        "fear": Colors.RED,
        "anger": Colors.RED + Colors.BOLD,
        "joy": Colors.GREEN,
        "excitement": Colors.GREEN + Colors.BOLD,
        "sadness": Colors.BLUE,
        "neutral": Colors.GRAY,
        "calm": Colors.CYAN,
    }
    label_color = emotion_colors.get(label, Colors.WHITE)
    
    return f"  │ Emotion: {colored(label, label_color)} (v={valence_str}, a={arousal_str})"


def format_action(action_name: str, target: Optional[str], reasoning: List[str]) -> str:
    """Format action display."""
    # Action colors
    action_colors = {
        "flee": Colors.YELLOW,
        "attack": Colors.RED,
        "help": Colors.GREEN,
        "explore": Colors.CYAN,
        "approach": Colors.BLUE,
        "wait": Colors.GRAY,
    }
    action_color = action_colors.get(action_name, Colors.WHITE)
    
    target_str = f" → {target}" if target else ""
    action_str = colored(f"{action_name}{target_str}", action_color + Colors.BOLD)
    
    lines = [f"  │ Action: {action_str}"]
    
    # Reasoning (abbreviated)
    if reasoning:
        reason_str = "; ".join(reasoning[:2])  # Max 2 reasons
        if len(reasoning) > 2:
            reason_str += "..."
        lines.append(f"  │ {Colors.DIM}Reasoning: {reason_str}{Colors.RESET}")
    
    return "\n".join(lines)


def format_outcome(outcome_type: str, valence: float, success: bool) -> str:
    """Format outcome display."""
    if success:
        status = colored("✓", Colors.GREEN)
    else:
        status = colored("✗", Colors.RED)
    
    if valence >= 0.2:
        valence_str = colored(f"{valence:+.2f}", Colors.GREEN)
    elif valence <= -0.2:
        valence_str = colored(f"{valence:+.2f}", Colors.RED)
    else:
        valence_str = colored(f"{valence:+.2f}", Colors.GRAY)
    
    return f"  │ Outcome: {status} {outcome_type} (valence={valence_str})"


def format_cycle_minimal(
    tick: int,
    total: int,
    world_state: WorldStateSnapshot,
    emotion: Dict[str, Any],
    action_name: str,
    target: Optional[str],
    reasoning: List[str],
    outcome_type: str,
    outcome_valence: float,
    success: bool,
) -> str:
    """Format minimal cycle output (default mode)."""
    lines = [
        format_tick_header(tick, total),
        format_world_state(world_state),
        f"  ┌─ Agent Response {'─' * 47}",
        format_emotion(emotion),
        format_action(action_name, target, reasoning),
        format_outcome(outcome_type, outcome_valence, success),
        f"  └{'─' * 65}",
    ]
    return "\n".join(lines)


def format_verbose_phase(phase_name: str, data: Dict[str, Any]) -> str:
    """Format verbose phase output."""
    lines = [
        colored(f"    ┌─ {phase_name} ", Colors.DIM) + "─" * (60 - len(phase_name)),
    ]
    
    for key, value in data.items():
        if isinstance(value, float):
            lines.append(f"    │ {key}: {value:.4f}")
        elif isinstance(value, list) and len(value) > 3:
            lines.append(f"    │ {key}: [{len(value)} items]")
        else:
            lines.append(f"    │ {key}: {value}")
    
    lines.append(colored(f"    └{'─' * 62}", Colors.DIM))
    return "\n".join(lines)


def format_summary(
    total_ticks: int,
    action_counts: Dict[str, int],
    avg_valence: float,
    avg_arousal: float,
    success_rate: float,
) -> str:
    """Format end-of-demo summary."""
    width = 66
    border = "═" * width
    
    lines = [
        "",
        colored(f"╔{border}╗", Colors.GREEN),
        colored(f"║{'DEMO COMPLETE':^{width}}║", Colors.GREEN + Colors.BOLD),
        colored(f"╠{border}╣", Colors.GREEN),
    ]
    
    # Stats
    lines.append(colored(f"║  Total Ticks: {total_ticks:<51}║", Colors.GREEN))
    lines.append(colored(f"║  Success Rate: {success_rate*100:.1f}%{' ' * 49}║", Colors.GREEN))
    lines.append(colored(f"║  Avg Valence: {avg_valence:+.3f}{' ' * 49}║", Colors.GREEN))
    lines.append(colored(f"║  Avg Arousal: {avg_arousal:.3f}{' ' * 50}║", Colors.GREEN))
    
    # Action distribution
    lines.append(colored(f"╠{border}╣", Colors.GREEN))
    lines.append(colored(f"║  {'Action Distribution:':<63}║", Colors.GREEN))
    
    for action, count in sorted(action_counts.items(), key=lambda x: -x[1]):
        pct = (count / total_ticks) * 100
        bar = "█" * int(pct / 5)
        lines.append(colored(f"║    {action:10s}: {count:3d} ({pct:5.1f}%) {bar:<20}║", Colors.GREEN))
    
    lines.append(colored(f"╚{border}╝", Colors.GREEN))
    lines.append("")
    
    return "\n".join(lines)


def format_error(message: str) -> str:
    """Format error message."""
    return colored(f"\n  ✗ ERROR: {message}\n", Colors.RED + Colors.BOLD)
