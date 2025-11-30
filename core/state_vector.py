# core/state_vector.py
"""
StateVector 16D Tanımları ve Sabitler

UEM CoreAI'de tüm modüller arasında paylaşılan durum vektörü.
16 boyutlu yapı, hem türetilmiş hem de ham değerleri içerir.

Yapı:
    [0-2]   Derived (türetilmiş) değerler
    [3-7]   Raw (ham) değerler  
    [8-15]  Reserved (gelecek kullanım için)

Versiyon: 2.0
Tarih: 1 Aralık 2025
Yazarlar: Claude (Opus 4.5) + Alice (GPT-5.1) + İsa Kara
"""

from typing import Tuple, NamedTuple, Any, Optional

# ============================================================================
# CONSTANTS - State Vector Index Tanımları
# ============================================================================

# Derived (Türetilmiş) Değerler [0-2]
SV_RESOURCE = 0      # (health + energy) / 2
SV_THREAT = 1        # clamp(danger, 0, 1)
SV_WELLBEING = 2     # (valence + 1) / 2

# Raw (Ham) Değerler [3-7]
SV_HEALTH = 3        # player_health
SV_ENERGY = 4        # player_energy
SV_VALENCE = 5       # emotion.valence
SV_AROUSAL = 6       # emotion.arousal
SV_DOMINANCE = 7     # emotion.dominance

# Reserved (Gelecek Kullanım) [8-15]
SV_RESERVED_8 = 8
SV_RESERVED_9 = 9
SV_RESERVED_10 = 10
SV_RESERVED_11 = 11
SV_RESERVED_12 = 12
SV_RESERVED_13 = 13
SV_RESERVED_14 = 14
SV_RESERVED_15 = 15

# Boyut sabiti
STATE_VECTOR_SIZE = 16

# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

# Temel tip (backward compatible)
StateVector = Tuple[float, ...]

# 16D sabit boyutlu tip
StateVector16 = Tuple[
    float, float, float, float,
    float, float, float, float,
    float, float, float, float,
    float, float, float, float,
]

# Legacy 3D tip (backward compatibility)
StateVector3 = Tuple[float, float, float]


# ============================================================================
# BUILDER FUNCTIONS
# ============================================================================

def build_state_vector_16d(
    world: Any,
    emotion: Any,
) -> StateVector16:
    """
    16D state vector oluştur.
    
    Args:
        world: WorldState veya dict (player_health, player_energy, danger_level)
        emotion: EmotionCore veya dict (valence, arousal, dominance)
    
    Returns:
        16D tuple
    """
    # Raw değerleri al
    if hasattr(world, 'player_health'):
        health = getattr(world, 'player_health', 0.5)
        energy = getattr(world, 'player_energy', 0.5)
        danger = getattr(world, 'danger_level', 0.0)
    elif isinstance(world, dict):
        health = world.get('player_health', 0.5)
        energy = world.get('player_energy', 0.5)
        danger = world.get('danger_level', 0.0)
    else:
        health, energy, danger = 0.5, 0.5, 0.0
    
    if hasattr(emotion, 'valence'):
        valence = getattr(emotion, 'valence', 0.0)
        arousal = getattr(emotion, 'arousal', 0.0)
        dominance = getattr(emotion, 'dominance', 0.0)
    elif isinstance(emotion, dict):
        valence = emotion.get('valence', 0.0)
        arousal = emotion.get('arousal', 0.0)
        dominance = emotion.get('dominance', 0.0)
    else:
        valence, arousal, dominance = 0.0, 0.0, 0.0
    
    # Derived değerleri hesapla
    resource = max(0.0, min(1.0, (health + energy) / 2.0))
    threat = max(0.0, min(1.0, danger))
    wellbeing = max(0.0, min(1.0, (valence + 1.0) / 2.0))
    
    return (
        resource,       # [0] derived
        threat,         # [1] derived
        wellbeing,      # [2] derived
        health,         # [3] raw
        energy,         # [4] raw
        valence,        # [5] raw
        arousal,        # [6] raw
        dominance,      # [7] raw
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,  # [8-15] reserved
    )


def ensure_vector_16d(vec: tuple) -> StateVector16:
    """
    Herhangi bir vektörü 16D'ye dönüştür.
    """
    if vec is None:
        vec = ()
    if len(vec) >= STATE_VECTOR_SIZE:
        return tuple(vec[:STATE_VECTOR_SIZE])
    return tuple(vec) + (0.0,) * (STATE_VECTOR_SIZE - len(vec))


def extract_legacy_3d(vec: tuple) -> StateVector3:
    """16D vektörden legacy 3D vektör çıkar."""
    if vec is None or len(vec) < 3:
        return (0.5, 0.0, 0.5)
    return (vec[0], vec[1], vec[2])


def get_health_from_vector(vec: tuple) -> float:
    """State vector'den health değerini al."""
    if vec is None:
        return 0.5
    if len(vec) > SV_HEALTH:
        return vec[SV_HEALTH]
    if len(vec) > 0:
        return vec[0]  # Legacy fallback
    return 0.5


def get_energy_from_vector(vec: tuple) -> float:
    """State vector'den energy değerini al."""
    if vec is None:
        return 0.5
    if len(vec) > SV_ENERGY:
        return vec[SV_ENERGY]
    return 0.5


def get_valence_from_vector(vec: tuple) -> float:
    """State vector'den valence değerini al."""
    if vec is None:
        return 0.0
    if len(vec) > SV_VALENCE:
        return vec[SV_VALENCE]
    return 0.0


def get_arousal_from_vector(vec: tuple) -> float:
    """State vector'den arousal değerini al."""
    if vec is None:
        return 0.0
    if len(vec) > SV_AROUSAL:
        return vec[SV_AROUSAL]
    return 0.0


def get_dominance_from_vector(vec: tuple) -> float:
    """State vector'den dominance değerini al."""
    if vec is None:
        return 0.0
    if len(vec) > SV_DOMINANCE:
        return vec[SV_DOMINANCE]
    return 0.0


__all__ = [
    'SV_RESOURCE', 'SV_THREAT', 'SV_WELLBEING',
    'SV_HEALTH', 'SV_ENERGY', 'SV_VALENCE', 'SV_AROUSAL', 'SV_DOMINANCE',
    'SV_RESERVED_8', 'SV_RESERVED_9', 'SV_RESERVED_10', 'SV_RESERVED_11',
    'SV_RESERVED_12', 'SV_RESERVED_13', 'SV_RESERVED_14', 'SV_RESERVED_15',
    'STATE_VECTOR_SIZE',
    'StateVector', 'StateVector16', 'StateVector3',
    'build_state_vector_16d', 'ensure_vector_16d', 'extract_legacy_3d',
    'get_health_from_vector', 'get_energy_from_vector', 'get_valence_from_vector',
    'get_arousal_from_vector', 'get_dominance_from_vector',
]
