"""
UEM Global Workspace System

LIDA tarzı conscious broadcast mekanizması.
Coalition competition → Conscious content → Broadcast to all modules

Author: UEM Project
"""

from __future__ import annotations
import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum, auto
from collections import deque


# =========================================================================
# ENUMS
# =========================================================================

class ContentType(Enum):
    """Workspace içerik türleri"""
    PERCEPT = "percept"
    MEMORY = "memory"
    GOAL = "goal"
    EMOTION = "emotion"
    PREDICTION = "prediction"
    CONFLICT = "conflict"
    NOVELTY = "novelty"
    URGENCY = "urgency"
    INSIGHT = "insight"


class BroadcastPriority(Enum):
    """Broadcast öncelik seviyeleri"""
    CRITICAL = 100
    HIGH = 75
    NORMAL = 50
    LOW = 25
    BACKGROUND = 10


# =========================================================================
# DATA STRUCTURES
# =========================================================================

@dataclass
class Coalition:
    """Workspace erişimi için yarışan bilgi birimi"""
    id: str
    content: Dict[str, Any]
    content_type: ContentType
    activation: float  # 0-1
    salience: float    # 0-1
    source: str
    timestamp: float = field(default_factory=time.time)
    supporting_codelets: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def competition_strength(self) -> float:
        """Yarışma gücü = activation * salience"""
        return self.activation * self.salience
    
    def decay(self, rate: float = 0.05) -> None:
        """Aktivasyon zamanla azalır"""
        self.activation = max(0.0, self.activation - rate)


@dataclass
class BroadcastMessage:
    """Tüm modüllere yayınlanan mesaj"""
    coalition: Coalition
    content_type: ContentType
    content: Dict[str, Any]
    timestamp: float
    cycle_number: int
    priority: BroadcastPriority = BroadcastPriority.NORMAL
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'coalition_id': self.coalition.id,
            'content_type': self.content_type.value,
            'content': self.content,
            'timestamp': self.timestamp,
            'cycle_number': self.cycle_number,
            'priority': self.priority.value,
        }


# =========================================================================
# CODELET BASE CLASS
# =========================================================================

class Codelet(ABC):
    """
    Coalition oluşturan küçük işlem birimi.
    Her codelet belirli bir pattern arar ve coalition üretir.
    """
    
    def __init__(
        self,
        name: str,
        priority: float = 0.5,
        logger: Optional[logging.Logger] = None,
    ):
        self.name = name
        self.priority = priority
        self.logger = logger or logging.getLogger(f"Codelet.{name}")
        self.run_count = 0
        self.coalition_count = 0
    
    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Optional[Coalition]:
        """Context'i analiz et, coalition oluştur veya None döndür"""
        pass
    
    def _create_coalition(
        self,
        content: Dict[str, Any],
        content_type: ContentType,
        activation: float,
        salience: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> Coalition:
        """Helper: Coalition oluştur"""
        self.coalition_count += 1
        return Coalition(
            id=f"{self.name}_{self.coalition_count}_{time.time():.0f}",
            content=content,
            content_type=content_type,
            activation=min(1.0, max(0.0, activation)),
            salience=min(1.0, max(0.0, salience)),
            source=self.name,
            supporting_codelets=[self.name],
            context=context or {},
        )


# =========================================================================
# DEFAULT CODELETS
# =========================================================================

class PerceptionCodelet(Codelet):
    """Tehlike algılama codelet'i"""
    
    def __init__(self, logger=None):
        super().__init__("perception_danger", priority=0.9, logger=logger)
    
    def run(self, context: Dict[str, Any]) -> Optional[Coalition]:
        self.run_count += 1
        perception = context.get('perception', {})
        danger = perception.get('danger_level', 0.0)
        
        if danger > 0.3:
            return self._create_coalition(
                content={'danger_level': danger, 'type': 'danger_detected'},
                content_type=ContentType.URGENCY,
                activation=0.5 + danger * 0.5,
                salience=danger,
                context={'source': 'perception'},
            )
        return None


class EmotionCodelet(Codelet):
    """Güçlü duygu codelet'i"""
    
    def __init__(self, logger=None):
        super().__init__("emotion_intense", priority=0.8, logger=logger)
    
    def run(self, context: Dict[str, Any]) -> Optional[Coalition]:
        self.run_count += 1
        emotion = context.get('emotion', {})
        arousal = emotion.get('arousal', 0.0)
        valence = emotion.get('valence', 0.0)
        
        intensity = (arousal + abs(valence)) / 2
        
        if intensity > 0.5:
            return self._create_coalition(
                content={
                    'arousal': arousal,
                    'valence': valence,
                    'emotion': emotion.get('current', 'unknown'),
                },
                content_type=ContentType.EMOTION,
                activation=intensity,
                salience=arousal,
                context={'intensity': intensity},
            )
        return None


class GoalCodelet(Codelet):
    """Aktif hedef codelet'i"""
    
    def __init__(self, logger=None):
        super().__init__("goal_active", priority=0.7, logger=logger)
    
    def run(self, context: Dict[str, Any]) -> Optional[Coalition]:
        self.run_count += 1
        goals = context.get('active_goals', [])
        
        if goals:
            top_goal = goals[0] if isinstance(goals[0], dict) else {'name': goals[0]}
            priority = top_goal.get('priority', 0.5)
            
            return self._create_coalition(
                content={'goal': top_goal, 'goal_count': len(goals)},
                content_type=ContentType.GOAL,
                activation=priority,
                salience=0.6,
                context={'goals': goals},
            )
        return None


class MemoryCodelet(Codelet):
    """İlgili hafıza codelet'i"""
    
    def __init__(self, logger=None):
        super().__init__("memory_relevant", priority=0.6, logger=logger)
    
    def run(self, context: Dict[str, Any]) -> Optional[Coalition]:
        self.run_count += 1
        memories = context.get('relevant_memories', [])
        
        if memories:
            top_memory = memories[0]
            relevance = top_memory.get('relevance', 0.5)
            
            return self._create_coalition(
                content={'memory': top_memory, 'memory_count': len(memories)},
                content_type=ContentType.MEMORY,
                activation=relevance,
                salience=0.5,
                context={'all_memories': memories},
            )
        return None


class NoveltyCodelet(Codelet):
    """Yenilik/beklenmedik durum codelet'i"""
    
    def __init__(self, logger=None):
        super().__init__("novelty_detector", priority=0.75, logger=logger)
        self.seen_patterns: set = set()
    
    def run(self, context: Dict[str, Any]) -> Optional[Coalition]:
        self.run_count += 1
        perception = context.get('perception', {})
        symbols = tuple(sorted(perception.get('symbols', [])))
        
        if symbols and symbols not in self.seen_patterns:
            self.seen_patterns.add(symbols)
            novelty_score = min(1.0, len(symbols) * 0.2)
            
            return self._create_coalition(
                content={'novel_symbols': list(symbols), 'novelty_score': novelty_score},
                content_type=ContentType.NOVELTY,
                activation=0.6 + novelty_score * 0.3,
                salience=novelty_score,
                context={'first_seen': True},
            )
        return None


class UrgencyCodelet(Codelet):
    """Düşük kaynak aciliyeti codelet'i"""
    
    def __init__(self, logger=None):
        super().__init__("urgency_resources", priority=0.85, logger=logger)
    
    def run(self, context: Dict[str, Any]) -> Optional[Coalition]:
        self.run_count += 1
        agent = context.get('agent_state', {})
        health = agent.get('health', 1.0)
        energy = agent.get('energy', 1.0)
        
        urgency = 0.0
        urgent_resource = None
        
        if health < 0.3:
            urgency = 1.0 - health
            urgent_resource = 'health'
        elif energy < 0.2:
            urgency = 0.8 - energy
            urgent_resource = 'energy'
        
        if urgency > 0.5:
            return self._create_coalition(
                content={
                    'urgency_type': 'low_resource',
                    'resource': urgent_resource,
                    'level': health if urgent_resource == 'health' else energy,
                },
                content_type=ContentType.URGENCY,
                activation=urgency,
                salience=urgency,
                context={'health': health, 'energy': energy},
            )
        return None


# =========================================================================
# WORKSPACE SUBSCRIBER
# =========================================================================

class WorkspaceSubscriber(ABC):
    """Broadcast alan modül interface'i"""
    
    @property
    @abstractmethod
    def subscriber_name(self) -> str:
        pass
    
    @abstractmethod
    async def receive_broadcast(self, message: BroadcastMessage) -> None:
        pass


# =========================================================================
# ATTENTION CONTROLLER
# =========================================================================

class AttentionController:
    """
    Top-down attention modülasyonu.
    Hedeflere göre coalition'ları boost eder.
    """
    
    def __init__(
        self,
        top_down_weight: float = 0.3,
        logger: Optional[logging.Logger] = None,
    ):
        self.logger = logger or logging.getLogger("Attention")
        self.top_down_weight = top_down_weight
        
        # Dikkat hedefleri
        self.attention_goals: List[Dict[str, Any]] = []
        
        # Dikkat durumu
        self.current_focus: Optional[str] = None
        self.focus_start_time: float = 0.0
        self.focus_duration: float = 0.0
        self.attention_shifts: List[Dict[str, Any]] = []
    
    def set_attention_goal(
        self,
        goal_type: str,
        target: str,
        priority: float,
    ) -> None:
        """Dikkat hedefi belirle"""
        self.attention_goals.append({
            'type': goal_type,
            'target': target,
            'priority': priority,
            'set_at': time.time(),
        })
        self.attention_goals.sort(key=lambda x: x['priority'], reverse=True)
        self.logger.debug(f"Attention goal set: {goal_type} → {target}")
    
    def modulate_coalition(self, coalition: Coalition) -> Coalition:
        """Coalition aktivasyonunu hedeflere göre modüle et"""
        if not self.attention_goals:
            return coalition
        
        top_goal = self.attention_goals[0]
        
        # Hedefle eşleşme kontrolü
        boost = 0.0
        if coalition.content_type.value == top_goal['target']:
            boost = top_goal['priority'] * self.top_down_weight * 0.3
        
        if boost > 0:
            coalition.activation = min(1.0, coalition.activation + boost)
            self.logger.debug(f"Attention boost: {coalition.content_type.value} +{boost:.3f}")
        
        return coalition
    
    def shift_attention(self, new_focus: str) -> None:
        """Dikkat kaydır"""
        if self.current_focus != new_focus:
            if self.current_focus:
                self.attention_shifts.append({
                    'from': self.current_focus,
                    'to': new_focus,
                    'duration': time.time() - self.focus_start_time,
                    'timestamp': time.time(),
                })
            
            self.current_focus = new_focus
            self.focus_start_time = time.time()
            self.focus_duration = 0.0
    
    def update(self, dt: float) -> None:
        """Dikkat durumunu güncelle"""
        if self.current_focus:
            self.focus_duration += dt
        
        # Eski hedefleri temizle (30 sn timeout)
        current_time = time.time()
        self.attention_goals = [
            g for g in self.attention_goals
            if current_time - g['set_at'] < 30.0
        ]


# =========================================================================
# GLOBAL WORKSPACE
# =========================================================================

class GlobalWorkspace:
    """
    LIDA tarzı Global Workspace.
    
    Cycle:
    1. Codelet'ler coalition üretir
    2. Coalition'lar yarışır
    3. Kazanan broadcast edilir
    """
    
    def __init__(
        self,
        competition_threshold: float = 0.4,
        max_coalitions: int = 10,
        decay_rate: float = 0.05,
        logger: Optional[logging.Logger] = None,
    ):
        self.logger = logger or logging.getLogger("GlobalWorkspace")
        
        # Parametreler
        self.competition_threshold = competition_threshold
        self.max_coalitions = max_coalitions
        self.decay_rate = decay_rate
        
        # Codelets
        self.codelets: List[Codelet] = []
        
        # Coalition queue
        self.coalition_queue: deque = deque(maxlen=max_coalitions)
        
        # Subscribers
        self.subscribers: List[WorkspaceSubscriber] = []
        
        # Current conscious content
        self.current_content: Optional[Coalition] = None
        
        # History
        self.broadcast_history: deque = deque(maxlen=100)
        self.cycle_count: int = 0
    
    def register_codelet(self, codelet: Codelet) -> None:
        """Codelet kaydet"""
        self.codelets.append(codelet)
        self.codelets.sort(key=lambda c: c.priority, reverse=True)
        self.logger.info(f"Codelet registered: {codelet.name}")
    
    def register_subscriber(self, subscriber: WorkspaceSubscriber) -> None:
        """Subscriber kaydet"""
        self.subscribers.append(subscriber)
        self.logger.info(f"Subscriber registered: {subscriber.subscriber_name}")
    
    async def cycle(self, context: Dict[str, Any]) -> Optional[BroadcastMessage]:
        """
        Tek workspace cycle'ı çalıştır.
        
        1. Coalition üretimi (codelets)
        2. Coalition yarışması
        3. Broadcast
        """
        self.cycle_count += 1
        
        # 1. Codelet'leri çalıştır → coalition üret
        new_coalitions = self._run_codelets(context)
        
        # Queue'ya ekle
        for coalition in new_coalitions:
            self.coalition_queue.append(coalition)
        
        # 2. Mevcut coalition'ları decay et
        for coalition in self.coalition_queue:
            coalition.decay(self.decay_rate)
        
        # 3. Yarışma
        winner = self._compete()
        
        if winner is None:
            return None
        
        # 4. Broadcast
        message = await self._broadcast(winner)
        
        return message
    
    def _run_codelets(self, context: Dict[str, Any]) -> List[Coalition]:
        """Tüm codelet'leri çalıştır"""
        coalitions = []
        
        for codelet in self.codelets:
            try:
                coalition = codelet.run(context)
                if coalition:
                    coalitions.append(coalition)
            except Exception as e:
                self.logger.error(f"Codelet {codelet.name} error: {e}")
        
        return coalitions
    
    def _compete(self) -> Optional[Coalition]:
        """Coalition'lar yarışır, en güçlü kazanır"""
        if not self.coalition_queue:
            return None
        
        # En yüksek competition_strength
        candidates = list(self.coalition_queue)
        candidates.sort(key=lambda c: c.competition_strength, reverse=True)
        
        winner = candidates[0]
        
        if winner.competition_strength < self.competition_threshold:
            self.logger.debug(f"No winner (strength {winner.competition_strength:.3f} < threshold)")
            return None
        
        self.current_content = winner
        
        # Kazananı queue'dan çıkar
        self.coalition_queue.remove(winner)
        
        self.logger.debug(
            f"Competition winner: {winner.content_type.value} "
            f"(strength={winner.competition_strength:.3f})"
        )
        
        return winner
    
    async def _broadcast(self, winner: Coalition) -> BroadcastMessage:
        """Kazanan içeriği tüm subscriber'lara yayınla"""
        
        # Priority belirleme
        priority = BroadcastPriority.NORMAL
        if winner.content_type == ContentType.URGENCY:
            priority = BroadcastPriority.CRITICAL
        elif winner.content_type == ContentType.EMOTION:
            priority = BroadcastPriority.HIGH
        
        message = BroadcastMessage(
            coalition=winner,
            content_type=winner.content_type,
            content=winner.content,
            timestamp=time.time(),
            cycle_number=self.cycle_count,
            priority=priority,
        )
        
        # Tüm subscriber'lara gönder
        broadcast_tasks = [
            subscriber.receive_broadcast(message)
            for subscriber in self.subscribers
        ]
        
        if broadcast_tasks:
            await asyncio.gather(*broadcast_tasks, return_exceptions=True)
        
        # History'ye ekle
        self.broadcast_history.append(message)
        
        self.logger.info(
            f"[BROADCAST] {winner.content_type.value} → "
            f"{len(self.subscribers)} subscribers"
        )
        
        return message
    
    def get_current_content(self) -> Optional[Coalition]:
        """Şu anki conscious content"""
        return self.current_content
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikler"""
        return {
            'cycle_count': self.cycle_count,
            'codelet_count': len(self.codelets),
            'subscriber_count': len(self.subscribers),
            'queue_size': len(self.coalition_queue),
            'broadcast_count': len(self.broadcast_history),
            'current_content_type': (
                self.current_content.content_type.value
                if self.current_content else None
            ),
        }


# =========================================================================
# WORKSPACE MANAGER (Unified Interface)
# =========================================================================

class WorkspaceManager:
    """
    Global Workspace + Attention Controller entegrasyonu.
    IntegratedUEMCore ile kullanım için.
    """
    
    def __init__(
        self,
        competition_threshold: float = 0.4,
        logger: Optional[logging.Logger] = None,
    ):
        self.logger = logger or logging.getLogger("WorkspaceManager")
        
        # Core components
        self.workspace = GlobalWorkspace(
            competition_threshold=competition_threshold,
            logger=self.logger.getChild("GW"),
        )
        self.attention = AttentionController(
            logger=self.logger.getChild("Attention"),
        )
        
        # Default codelets
        self._register_default_codelets()
        
        # Statistics
        self.cycle_count = 0
        self.broadcast_count = 0
    
    def _register_default_codelets(self) -> None:
        """Varsayılan codelet'leri kaydet"""
        self.workspace.register_codelet(PerceptionCodelet(self.logger))
        self.workspace.register_codelet(EmotionCodelet(self.logger))
        self.workspace.register_codelet(GoalCodelet(self.logger))
        self.workspace.register_codelet(MemoryCodelet(self.logger))
        self.workspace.register_codelet(NoveltyCodelet(self.logger))
        self.workspace.register_codelet(UrgencyCodelet(self.logger))
        
        self.logger.info("Default codelets registered (6)")
    
    def register_subscriber(self, subscriber: WorkspaceSubscriber) -> None:
        """Subscriber ekle"""
        self.workspace.register_subscriber(subscriber)
    
    def register_codelet(self, codelet: Codelet) -> None:
        """Özel codelet ekle"""
        self.workspace.register_codelet(codelet)
    
    def set_attention_goal(self, goal_type: str, target: str, priority: float) -> None:
        """Dikkat hedefi belirle"""
        self.attention.set_attention_goal(goal_type, target, priority)
    
    async def cycle(self, context: Dict[str, Any]) -> Optional[BroadcastMessage]:
        """
        Tam workspace + attention cycle.
        """
        self.cycle_count += 1
        
        # Attention update
        self.attention.update(context.get('dt', 0.1))
        
        # Coalition'ları modüle et (top-down attention)
        for coalition in self.workspace.coalition_queue:
            self.attention.modulate_coalition(coalition)
        
        # Workspace cycle
        message = await self.workspace.cycle(context)
        
        if message:
            self.broadcast_count += 1
            self.attention.shift_attention(message.content_type.value)
        
        return message
    
    def get_current_focus(self) -> Optional[str]:
        """Şu anki dikkat odağı"""
        return self.attention.current_focus
    
    def get_current_content(self) -> Optional[Coalition]:
        """Şu anki workspace içeriği"""
        return self.workspace.get_current_content()
    
    def get_stats(self) -> Dict[str, Any]:
        """Birleşik istatistikler"""
        return {
            'workspace': self.workspace.get_stats(),
            'attention': {
                'current_focus': self.attention.current_focus,
                'focus_duration': self.attention.focus_duration,
                'goals_count': len(self.attention.attention_goals),
                'shifts_count': len(self.attention.attention_shifts),
            },
            'manager': {
                'cycle_count': self.cycle_count,
                'broadcast_count': self.broadcast_count,
            },
        }


# =========================================================================
# FACTORY
# =========================================================================

def create_workspace_manager(
    config: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None,
) -> WorkspaceManager:
    """WorkspaceManager factory"""
    config = config or {}
    return WorkspaceManager(
        competition_threshold=config.get('competition_threshold', 0.4),
        logger=logger,
    )
