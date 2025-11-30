from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

Vec3 = Tuple[float, float, float]


@dataclass
class PerceivedObject:
    """
    Perception pipeline'ının çıkardığı, normalize edilmiş nesne temsili.
    WorldSnapshot içindeki ham dict'lerden türetilir.
    """
    id: str
    obj_type: str
    position: Vec3
    distance: float
    is_dangerous: bool = False
    is_interactable: bool = False
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerceivedAgent:
    """
    Görüş alanındaki NPC / oyuncu / başka ajanların temsili.
    """
    id: str
    agent_type: str  # "NPC", "PLAYER", "AGENT" vs.
    position: Vec3
    relation: Optional[str] = None  # "friendly", "hostile", "neutral" vs.
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorldSnapshot:
    """
    World interface'den gelen ham verinin normalize edilmiş hali.
    Burada hala "ham" sayılır, perception alt modülleri bunu işler.
    """
    tick: int
    timestamp: float
    agent_position: Vec3
    objects: List[Dict[str, Any]]
    agents: List[Dict[str, Any]]
    environment: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnvironmentState:
    """
    StatePerception çıktısı: UEM'in o anki çevresine dair özet zihinsel sahne.
    """
    danger_level: float
    nearest_danger: Optional[PerceivedObject]
    nearest_target: Optional[PerceivedObject]
    notes: str = ""


@dataclass
class PerceptionResult:
    """
    PerceptionCore'un diğer sistemlere vereceği ana çıktı paketi.
    Memory, Planning, Emotion vs. bu yapıyı kullanabilir.
    """
    snapshot: WorldSnapshot
    objects: List[PerceivedObject]
    agents: List[PerceivedAgent]
    environment_state: EnvironmentState
    symbols: List[str] = field(default_factory=list)
