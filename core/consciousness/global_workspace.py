"""
UEM Global Workspace System

LIDA (Learning Intelligent Distribution Agent) mimarisinden esinlenilmiş
conscious broadcast mekanizması.

Temel Kavramlar:
- Coalition: Birlikte yarışan bilgi birimleri grubu
- Codelet: Özel görevler yapan küçük işlem birimleri
- Competition: Coalition'lar workspace erişimi için yarışır
- Broadcast: Kazanan içerik tüm modüllere yayınlanır
- Attention: Sınırlı kaynak, en önemli içerik seçilir

LIDA Cognitive Cycle:
1. Perception → Sensory data → Perceptual memory
2. Understanding → Coalition formation
3. Attention → Competition for workspace access
4. Action Selection → Broadcast influences behavior
5. Learning → All modules learn from broadcast

References:
- Franklin, S., et al. (2013). LIDA: A Systems-level Architecture for Cognition
- Baars, B. (1988). A Cognitive Theory of Consciousness

Author: UEM Project
"""

from __future__ import annotations
import asyncio
import logging
import time
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Callable, Tuple
from enum import Enum, auto
from collections import deque


# =========================================================================
# ENUMS AND CONSTANTS
# =========================================================================

class ContentType(Enum):
    """Global Workspace'e girebilecek içerik türleri"""
    PERCEPT = "percept"              # Algısal veri
    MEMORY = "memory"                # Hatırlanan bilgi
    GOAL = "goal"                    # Aktif hedef
    EMOTION = "emotion"              # Duygusal durum
    PREDICTION = "prediction"        # Beklenti/tahmin
    CONFLICT = "conflict"            # Çatışan bilgi
    NOVELTY = "novelty"              # Yeni/beklenmedik
    URGENCY = "urgency"              # Acil durum
    INSIGHT = "insight"              # İçgörü


class BroadcastPriority(Enum):
    """Broadcast öncelik seviyeleri"""
    CRITICAL = 100      # Hayati (tehlike, acil)
    HIGH = 75           # Yüksek öncelik
    NORMAL = 50         # Normal
    LOW = 25            # Düşük öncelik
    BACKGROUND = 10     # Arka plan


# =========================================================================
# DATA STRUCTURES
# =========================================================================

@dataclass
class Coalition:
    """
    Workspace erişimi için yarışan bilgi birimi.
    
    Coalition, birden fazla "codelet" veya bilgi parçasının
    birleşerek oluşturduğu bir yapıdır.
    """
    coalition_id: str
    content: Any
    content_type: ContentType
    activation: float                   # 0-1 arası, yarışma gücü
    salience: float                     # 0-1 arası, içeriğin önemi
    urgency: float = 0.0                # 0-1 arası, aciliyet
    emotional_charge: float = 0.0       # -1 to +1, duygusal yük
    novelty: float = 0.0                # 0-1 arası, yenilik derecesi
    source_module: str = ""             # Kaynak modül
    context: Dict[str, Any] = field(default_factory=dict)
    supporting_codelets: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    
    @property
    def total_activation(self) -> float:
        """
        Toplam aktivasyon skoru.
        
        Faktörler:
        - Base activation
        - Salience boost
        - Urgency boost
        - Emotional intensity boost
        - Novelty boost
        - Recency bonus (yeni oluşturulanlar biraz avantajlı)
        """
        recency_bonus = max(0, 0.1 - (time.time() - self.created_at) * 0.01)
        emotional_boost = abs(self.emotional_charge) * 0.2
        
        total = (
            self.activation * 0.4 +
            self.salience * 0.25 +
            self.urgency * 0.2 +
            emotional_boost +
            self.novelty * 0.1 +
            recency_bonus
        )
        return min(1.0, total)
    
    def __lt__(self, other: Coalition) -> bool:
        """Heap comparison için"""
        return self.total_activation > other.total_activation  # Max-heap
    
    def __repr__(self) -> str:
        return f"Coalition({self.content_type.value}, act={self.total_activation:.3f})"


@dataclass
class BroadcastMessage:
    """Global workspace'ten yayınlanan mesaj"""
    message_id: str
    content: Any
    content_type: ContentType
    source_coalition: Coalition
    activation: float
    timestamp: float = field(default_factory=time.time)
    priority: BroadcastPriority = BroadcastPriority.NORMAL
    context: Dict[str, Any] = field(default_factory=dict)
    recipients: List[str] = field(default_factory=list)


@dataclass
class WorkspaceState:
    """Global Workspace'in anlık durumu"""
    current_content: Optional[Coalition] = None
    competition_in_progress: bool = False
    last_broadcast_time: float = 0.0
    broadcasts_count: int = 0
    total_coalitions_evaluated: int = 0
    attention_focus: Optional[str] = None


# =========================================================================
# CODELET BASE CLASS
# =========================================================================

class Codelet(ABC):
    """
    Temel codelet sınıfı.
    
    Codelet, belirli bir görevi yerine getiren küçük işlem birimidir.
    Coalition'ları oluşturur ve workspace'e aday olarak sunar.
    """
    
    def __init__(
        self,
        name: str,
        priority: float = 0.5,
        logger: Optional[logging.Logger] = None,
    ):
        self.name = name
        self.priority = priority
        self.logger = logger or logging.getLogger(f"codelet.{name}")
        self.activation = 0.0
        self.last_run = 0.0
        self.run_count = 0
    
    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Optional[Coalition]:
        """
        Codelet'i çalıştır.
        
        Returns:
            Coalition if something worth broadcasting, None otherwise
        """
        pass
    
    def _create_coalition(
        self,
        content: Any,
        content_type: ContentType,
        activation: float,
        salience: float,
        **kwargs,
    ) -> Coalition:
        """Helper: Coalition oluştur"""
        coalition_id = hashlib.md5(
            f"{self.name}:{time.time()}:{id(content)}".encode()
        ).hexdigest()[:12]
        
        return Coalition(
            coalition_id=coalition_id,
            content=content,
            content_type=content_type,
            activation=activation,
            salience=salience,
            source_module=self.name,
            supporting_codelets=[self.name],
            **kwargs,
        )


# =========================================================================
# BUILT-IN CODELETS
# =========================================================================

class PerceptionCodelet(Codelet):
    """Algısal veriyi coalition'a dönüştürür"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__("perception_codelet", priority=0.7, logger=logger)
    
    def run(self, context: Dict[str, Any]) -> Optional[Coalition]:
        perception_data = context.get('perception', {})
        if not perception_data:
            return None
        
        # Tehlike algısı yüksek salience
        danger = perception_data.get('danger_level', 0)
        salience = max(0.3, danger)
        
        # Yeni/beklenmedik algı yüksek novelty
        novelty = perception_data.get('novelty', 0.2)
        
        self.run_count += 1
        self.last_run = time.time()
        
        return self._create_coalition(
            content=perception_data,
            content_type=ContentType.PERCEPT,
            activation=0.5 + danger * 0.3,
            salience=salience,
            urgency=danger,
            novelty=novelty,
            context={'source': 'perception'},
        )


class MemoryCodelet(Codelet):
    """Tetiklenen anıları coalition'a dönüştürür"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__("memory_codelet", priority=0.5, logger=logger)
    
    def run(self, context: Dict[str, Any]) -> Optional[Coalition]:
        memories = context.get('retrieved_memories', [])
        if not memories:
            return None
        
        # En yüksek aktivasyonlu anı
        if isinstance(memories, list) and len(memories) > 0:
            top_memory = memories[0]
            activation = getattr(top_memory, 'activation', 0.5)
            
            return self._create_coalition(
                content=top_memory,
                content_type=ContentType.MEMORY,
                activation=activation,
                salience=0.4,
                context={'memory_count': len(memories)},
            )
        
        return None


class EmotionCodelet(Codelet):
    """Güçlü duygusal durumları coalition'a dönüştürür"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__("emotion_codelet", priority=0.6, logger=logger)
    
    def run(self, context: Dict[str, Any]) -> Optional[Coalition]:
        emotion_state = context.get('emotion', {})
        if not emotion_state:
            return None
        
        valence = emotion_state.get('valence', 0)
        arousal = emotion_state.get('arousal', 0)
        emotion_label = emotion_state.get('emotion', 'neutral')
        
        # Güçlü duygular (yüksek arousal veya ekstrem valence)
        intensity = abs(valence) * max(0.5, arousal)
        
        if intensity < 0.3:
            return None  # Zayıf duygu, broadcast gereksiz
        
        return self._create_coalition(
            content=emotion_state,
            content_type=ContentType.EMOTION,
            activation=0.4 + intensity * 0.4,
            salience=intensity,
            emotional_charge=valence,
            urgency=arousal * 0.5 if valence < 0 else 0,
            context={'emotion_label': emotion_label},
        )


class GoalCodelet(Codelet):
    """Aktif hedefleri coalition'a dönüştürür"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__("goal_codelet", priority=0.6, logger=logger)
    
    def run(self, context: Dict[str, Any]) -> Optional[Coalition]:
        goals = context.get('active_goals', [])
        current_goal = context.get('current_goal')
        
        if not current_goal and not goals:
            return None
        
        goal = current_goal or (goals[0] if goals else None)
        if not goal:
            return None
        
        importance = goal.get('importance', 0.5) if isinstance(goal, dict) else 0.5
        
        return self._create_coalition(
            content=goal,
            content_type=ContentType.GOAL,
            activation=0.5 + importance * 0.3,
            salience=importance,
            context={'goal_type': 'current'},
        )


class UrgencyCodelet(Codelet):
    """Acil durumları tespit eder ve coalition oluşturur"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__("urgency_codelet", priority=0.9, logger=logger)
    
    def run(self, context: Dict[str, Any]) -> Optional[Coalition]:
        # Çeşitli acil durum sinyalleri
        danger = context.get('perception', {}).get('danger_level', 0)
        health = context.get('agent_state', {}).get('health', 1.0)
        
        # Acil durum: yüksek tehlike veya düşük sağlık
        urgency_score = 0.0
        urgency_reason = []
        
        if danger > 0.7:
            urgency_score = max(urgency_score, danger)
            urgency_reason.append(f"high_danger:{danger:.2f}")
        
        if health < 0.3:
            urgency_score = max(urgency_score, 1 - health)
            urgency_reason.append(f"low_health:{health:.2f}")
        
        if urgency_score < 0.5:
            return None
        
        return self._create_coalition(
            content={'urgency_reasons': urgency_reason, 'score': urgency_score},
            content_type=ContentType.URGENCY,
            activation=0.8 + urgency_score * 0.2,
            salience=urgency_score,
            urgency=urgency_score,
            emotional_charge=-0.5,  # Acil durumlar negatif
            context={'priority': 'critical'},
        )


class NoveltyCodelet(Codelet):
    """Yeni/beklenmedik durumları tespit eder"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__("novelty_codelet", priority=0.5, logger=logger)
        self.seen_patterns: Set[str] = set()
    
    def run(self, context: Dict[str, Any]) -> Optional[Coalition]:
        perception = context.get('perception', {})
        
        # Pattern hash oluştur
        pattern_key = str(sorted(perception.get('symbols', [])))
        
        if pattern_key in self.seen_patterns:
            return None  # Bilinen durum
        
        # Yeni pattern
        self.seen_patterns.add(pattern_key)
        
        # Hafıza sınırlı tut
        if len(self.seen_patterns) > 100:
            self.seen_patterns = set(list(self.seen_patterns)[-50:])
        
        return self._create_coalition(
            content={'novel_pattern': pattern_key, 'perception': perception},
            content_type=ContentType.NOVELTY,
            activation=0.6,
            salience=0.5,
            novelty=0.8,
            context={'first_encounter': True},
        )


# =========================================================================
# WORKSPACE SUBSCRIBER INTERFACE
# =========================================================================

class WorkspaceSubscriber(ABC):
    """Global Workspace broadcast'lerini dinleyen modül arayüzü"""
    
    @abstractmethod
    async def receive_broadcast(self, message: BroadcastMessage) -> None:
        """Broadcast mesajını işle"""
        pass
    
    @property
    @abstractmethod
    def subscriber_name(self) -> str:
        """Subscriber adı"""
        pass


# =========================================================================
# GLOBAL WORKSPACE
# =========================================================================

class GlobalWorkspace:
    """
    LIDA tarzı Global Workspace implementasyonu.
    
    Temel işlevler:
    1. Coalition'ları topla (perception, memory, emotion, etc.)
    2. Yarışma düzenle (activation tabanlı)
    3. Kazananı broadcast et
    4. Subscriber'ları bilgilendir
    
    Parametreler:
    - competition_threshold: Minimum aktivasyon eşiği
    - broadcast_decay: Her cycle'da broadcast içeriğinin zayıflaması
    - max_coalitions: Aynı anda yarışabilecek maksimum coalition
    """
    
    def __init__(
        self,
        competition_threshold: float = 0.4,
        broadcast_decay: float = 0.1,
        max_coalitions: int = 10,
        logger: Optional[logging.Logger] = None,
    ):
        self.competition_threshold = competition_threshold
        self.broadcast_decay = broadcast_decay
        self.max_coalitions = max_coalitions
        self.logger = logger or logging.getLogger("GlobalWorkspace")
        
        # State
        self.state = WorkspaceState()
        self.coalition_queue: List[Coalition] = []
        self.subscribers: List[WorkspaceSubscriber] = []
        self.codelets: List[Codelet] = []
        
        # History
        self.broadcast_history: deque = deque(maxlen=50)
        self.competition_history: deque = deque(maxlen=100)
        
        # Statistics
        self.stats = {
            'total_broadcasts': 0,
            'total_competitions': 0,
            'coalitions_by_type': {},
            'winners_by_type': {},
            'avg_winning_activation': 0.0,
        }
    
    def register_subscriber(self, subscriber: WorkspaceSubscriber) -> None:
        """Broadcast dinleyicisi ekle"""
        self.subscribers.append(subscriber)
        self.logger.info(f"Subscriber registered: {subscriber.subscriber_name}")
    
    def unregister_subscriber(self, subscriber: WorkspaceSubscriber) -> None:
        """Broadcast dinleyicisini kaldır"""
        if subscriber in self.subscribers:
            self.subscribers.remove(subscriber)
    
    def register_codelet(self, codelet: Codelet) -> None:
        """Codelet ekle"""
        self.codelets.append(codelet)
        self.logger.info(f"Codelet registered: {codelet.name}")
    
    def submit_coalition(self, coalition: Coalition) -> None:
        """Coalition'ı yarışmaya ekle"""
        if len(self.coalition_queue) >= self.max_coalitions:
            # En düşük aktivasyonluyu çıkar
            min_idx = min(range(len(self.coalition_queue)), 
                         key=lambda i: self.coalition_queue[i].total_activation)
            if coalition.total_activation > self.coalition_queue[min_idx].total_activation:
                self.coalition_queue.pop(min_idx)
                self.coalition_queue.append(coalition)
        else:
            self.coalition_queue.append(coalition)
        
        # İstatistik güncelle
        ctype = coalition.content_type.value
        self.stats['coalitions_by_type'][ctype] = self.stats['coalitions_by_type'].get(ctype, 0) + 1
    
    async def run_codelets(self, context: Dict[str, Any]) -> List[Coalition]:
        """Tüm codelet'leri çalıştır ve coalition'ları topla"""
        coalitions = []
        
        for codelet in self.codelets:
            try:
                result = codelet.run(context)
                if result is not None:
                    coalitions.append(result)
                    self.submit_coalition(result)
            except Exception as e:
                self.logger.warning(f"Codelet {codelet.name} error: {e}")
        
        return coalitions
    
    def compete(self) -> Optional[Coalition]:
        """
        Coalition'lar arasında yarışma düzenle.
        
        En yüksek total_activation'a sahip coalition kazanır.
        Eşik altındaki coalition'lar elemine edilir.
        """
        if not self.coalition_queue:
            return None
        
        self.state.competition_in_progress = True
        self.stats['total_competitions'] += 1
        
        # Eşik üstü coalition'ları filtrele
        candidates = [c for c in self.coalition_queue 
                     if c.total_activation >= self.competition_threshold]
        
        if not candidates:
            self.state.competition_in_progress = False
            self.coalition_queue.clear()
            return None
        
        # En yüksek aktivasyonlu kazanır
        winner = max(candidates, key=lambda c: c.total_activation)
        
        # Geçmişe ekle
        self.competition_history.append({
            'timestamp': time.time(),
            'candidates_count': len(candidates),
            'winner_type': winner.content_type.value,
            'winner_activation': winner.total_activation,
        })
        
        # İstatistik güncelle
        wtype = winner.content_type.value
        self.stats['winners_by_type'][wtype] = self.stats['winners_by_type'].get(wtype, 0) + 1
        
        # Running average of winning activation
        n = self.stats['total_competitions']
        old_avg = self.stats['avg_winning_activation']
        self.stats['avg_winning_activation'] = old_avg + (winner.total_activation - old_avg) / n
        
        # Temizle
        self.coalition_queue.clear()
        self.state.competition_in_progress = False
        self.state.current_content = winner
        self.state.total_coalitions_evaluated += len(candidates)
        
        self.logger.debug(
            f"Competition: {len(candidates)} candidates, winner={winner.content_type.value}, "
            f"activation={winner.total_activation:.3f}"
        )
        
        return winner
    
    async def broadcast(self, coalition: Coalition) -> BroadcastMessage:
        """
        Kazanan coalition'ı tüm subscriber'lara yayınla.
        """
        # Mesaj oluştur
        message_id = hashlib.md5(
            f"{coalition.coalition_id}:{time.time()}".encode()
        ).hexdigest()[:12]
        
        # Öncelik belirle
        if coalition.urgency > 0.7:
            priority = BroadcastPriority.CRITICAL
        elif coalition.urgency > 0.4 or coalition.salience > 0.7:
            priority = BroadcastPriority.HIGH
        elif coalition.salience < 0.3:
            priority = BroadcastPriority.LOW
        else:
            priority = BroadcastPriority.NORMAL
        
        message = BroadcastMessage(
            message_id=message_id,
            content=coalition.content,
            content_type=coalition.content_type,
            source_coalition=coalition,
            activation=coalition.total_activation,
            priority=priority,
            context=coalition.context,
            recipients=[s.subscriber_name for s in self.subscribers],
        )
        
        # Broadcast history
        self.broadcast_history.append({
            'message_id': message_id,
            'content_type': coalition.content_type.value,
            'activation': coalition.total_activation,
            'timestamp': time.time(),
            'recipients_count': len(self.subscribers),
        })
        
        # State güncelle
        self.state.last_broadcast_time = time.time()
        self.state.broadcasts_count += 1
        self.stats['total_broadcasts'] += 1
        
        # Tüm subscriber'lara gönder
        tasks = []
        for subscriber in self.subscribers:
            tasks.append(subscriber.receive_broadcast(message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.logger.info(
            f"Broadcast: type={coalition.content_type.value}, "
            f"priority={priority.name}, recipients={len(self.subscribers)}"
        )
        
        return message
    
    async def cycle(self, context: Dict[str, Any]) -> Optional[BroadcastMessage]:
        """
        Tam bir workspace cycle:
        1. Codelet'leri çalıştır → coalition'lar
        2. Yarışma düzenle
        3. Kazananı broadcast et
        
        Returns:
            BroadcastMessage if broadcast occurred, None otherwise
        """
        # 1. Codelet'leri çalıştır
        await self.run_codelets(context)
        
        # 2. Yarışma
        winner = self.compete()
        
        if winner is None:
            return None
        
        # 3. Broadcast
        message = await self.broadcast(winner)
        
        return message
    
    def get_current_content(self) -> Optional[Coalition]:
        """Şu anki workspace içeriği"""
        return self.state.current_content
    
    def get_attention_focus(self) -> Optional[str]:
        """Dikkat odağı (en son broadcast edilen içerik türü)"""
        if self.state.current_content:
            return self.state.current_content.content_type.value
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikler"""
        return {
            **self.stats,
            'current_queue_size': len(self.coalition_queue),
            'subscribers_count': len(self.subscribers),
            'codelets_count': len(self.codelets),
            'state': {
                'broadcasts_count': self.state.broadcasts_count,
                'total_evaluated': self.state.total_coalitions_evaluated,
                'attention_focus': self.get_attention_focus(),
            },
        }


# =========================================================================
# ATTENTION CONTROLLER
# =========================================================================

class AttentionController:
    """
    Dikkat yönetimi.
    
    Top-down (goal-driven) ve bottom-up (stimulus-driven) 
    dikkat arasında denge kurar.
    """
    
    def __init__(
        self,
        top_down_weight: float = 0.4,
        bottom_up_weight: float = 0.6,
        logger: Optional[logging.Logger] = None,
    ):
        self.top_down_weight = top_down_weight
        self.bottom_up_weight = bottom_up_weight
        self.logger = logger or logging.getLogger("AttentionController")
        
        # Current attention state
        self.current_focus: Optional[str] = None
        self.focus_duration: float = 0.0
        self.focus_start_time: float = 0.0
        
        # Attention history
        self.attention_shifts: List[Dict[str, Any]] = []
        
        # Goals affecting attention
        self.attention_goals: List[Dict[str, Any]] = []
    
    def set_attention_goal(self, goal_type: str, target: str, priority: float) -> None:
        """Top-down dikkat hedefi belirle"""
        self.attention_goals.append({
            'goal_type': goal_type,
            'target': target,
            'priority': priority,
            'set_at': time.time(),
        })
        # En yüksek öncelikli hedefe göre sırala
        self.attention_goals.sort(key=lambda x: -x['priority'])
    
    def modulate_coalition(self, coalition: Coalition) -> Coalition:
        """
        Top-down attention ile coalition aktivasyonunu modüle et.
        
        Hedefle uyumlu içerikler boost alır.
        """
        if not self.attention_goals:
            return coalition
        
        top_goal = self.attention_goals[0]
        
        # Hedefle eşleşme kontrolü
        boost = 0.0
        if coalition.content_type.value == top_goal['target']:
            boost = top_goal['priority'] * self.top_down_weight * 0.3
        
        if boost > 0:
            # Aktivasyonu boost et
            new_activation = min(1.0, coalition.activation + boost)
            coalition.activation = new_activation
            self.logger.debug(
                f"Attention boost: {coalition.content_type.value} +{boost:.3f}"
            )
        
        return coalition
    
    def shift_attention(self, new_focus: str) -> None:
        """Dikkat kaydır"""
        if self.current_focus != new_focus:
            # Eski odağı kaydet
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
        
        # Eski hedefleri temizle
        current_time = time.time()
        self.attention_goals = [
            g for g in self.attention_goals 
            if current_time - g['set_at'] < 30.0  # 30 saniye timeout
        ]


# =========================================================================
# WORKSPACE MANAGER (INTEGRATED)
# =========================================================================

class WorkspaceManager:
    """
    Global Workspace + Attention Controller entegrasyonu.
    
    IntegratedUEMCore ile kullanım için hazır.
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
        self.workspace.register_codelet(MemoryCodelet(self.logger))
        self.workspace.register_codelet(EmotionCodelet(self.logger))
        self.workspace.register_codelet(GoalCodelet(self.logger))
        self.workspace.register_codelet(UrgencyCodelet(self.logger))
        self.workspace.register_codelet(NoveltyCodelet(self.logger))
        
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
            # Dikkat kaydır
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
# FACTORY FUNCTION
# =========================================================================

def create_workspace_manager(
    config: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None,
) -> WorkspaceManager:
    """WorkspaceManager oluştur"""
    config = config or {}
    return WorkspaceManager(
        competition_threshold=config.get('competition_threshold', 0.4),
        logger=logger,
    )
