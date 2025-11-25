"""
Somatic System Event Handler for UEM

Event bus ile SomaticMarkerSystem arasında köprü.
Gerçek zamanlı event'leri işleyerek marker'ları otomatik günceller.

Event Subscriptions:
- planning.action_decided → Eylemi kaydet
- world.outcome_received → Sonucu kaydet, marker güncelle
- emotion.state_changed → Mevcut emotion context'i güncelle

Event Publications:
- somatic.marker_created → Yeni marker oluşturulduğunda
- somatic.marker_reinforced → Marker güçlendirildiğinde
- somatic.bias_applied → Karar vermeye bias uygulandığında
"""

from __future__ import annotations
import asyncio
import logging
import time
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class OutcomeMapping:
    """Outcome türlerini valence değerlerine eşle"""
    # Pozitif sonuçlar
    positive: Dict[str, float] = field(default_factory=lambda: {
        "found_reward": 0.6,
        "found_treasure": 0.8,
        "task_completed": 0.7,
        "goal_reached": 0.9,
        "item_collected": 0.5,
        "npc_friendly": 0.4,
        "safe_passage": 0.3,
        "discovered_secret": 0.7,
    })
    
    # Negatif sonuçlar
    negative: Dict[str, float] = field(default_factory=lambda: {
        "took_damage": -0.6,
        "ambushed": -0.8,
        "trapped": -0.7,
        "task_failed": -0.5,
        "lost_item": -0.4,
        "npc_hostile": -0.5,
        "blocked_path": -0.3,
        "died": -1.0,
    })
    
    def get_valence(self, outcome_type: str) -> float:
        """Outcome türünden valence değeri al"""
        if outcome_type in self.positive:
            return self.positive[outcome_type]
        if outcome_type in self.negative:
            return self.negative[outcome_type]
        # Bilinmeyen outcome - nötr
        return 0.0


class SomaticEventHandler:
    """
    Event bus ile Somatic Marker System arasında köprü.
    
    Kullanım:
        handler = SomaticEventHandler(somatic_system, event_bus)
        await handler.initialize()
        
        # Event bus üzerinden otomatik çalışır:
        # planning.action_decided → record_action
        # world.outcome_received → record_outcome
    """
    
    def __init__(
        self,
        somatic_system: Any,  # SomaticMarkerSystem
        event_bus: Any,  # EventBus
        outcome_mapping: Optional[OutcomeMapping] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.somatic = somatic_system
        self.event_bus = event_bus
        self.outcome_mapping = outcome_mapping or OutcomeMapping()
        self.logger = logger or logging.getLogger("core.emotion.SomaticEventHandler")
        
        # Current context
        self.current_emotion: Dict[str, float] = {
            'valence': 0.0,
            'arousal': 0.0,
            'dominance': 0.0,
        }
        self.current_world_state: Dict[str, Any] = {}
        
        # Statistics
        self.events_processed = 0
        self.actions_recorded = 0
        self.outcomes_recorded = 0
        self.markers_created = 0
        self.markers_reinforced = 0
        
        # Pending action timeout (saniye)
        self.action_timeout = 30.0
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Event subscriptions kur"""
        if self._initialized:
            return
        
        if self.event_bus is None:
            self.logger.warning("[SomaticHandler] No event bus provided")
            return
        
        # Subscribe to events
        await self.event_bus.subscribe(
            'planning.action_decided',
            self._on_action_decided
        )
        await self.event_bus.subscribe(
            'world.outcome_received',
            self._on_outcome_received
        )
        await self.event_bus.subscribe(
            'emotion.state_changed',
            self._on_emotion_changed
        )
        await self.event_bus.subscribe(
            'perception.new_data',
            self._on_perception_data
        )
        
        self._initialized = True
        self.logger.info("[SomaticHandler] Event subscriptions initialized")
    
    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================
    
    async def _on_action_decided(self, event) -> None:
        """
        Handle planning.action_decided events.
        
        Event data:
        - action_name: str
        - action_params: dict
        - confidence: float
        - emotional_influence: float
        - current_emotion: str
        """
        try:
            action_name = event.data.get('action_name')
            action_params = event.data.get('action_params', {})
            
            if not action_name:
                return
            
            # World state from params or current context
            world_state = self._build_world_state(action_params)
            
            # Record action
            situation_hash = self.somatic.record_action(
                action_name=action_name,
                action_params=action_params,
                world_state=world_state,
                emotion_state=self.current_emotion.copy(),
            )
            
            self.actions_recorded += 1
            self.events_processed += 1
            
            self.logger.debug(
                "[SomaticHandler] Action recorded: %s (situation=%s)",
                action_name, situation_hash[:8]
            )
            
        except Exception as e:
            self.logger.error("[SomaticHandler] Error recording action: %s", e)
    
    async def _on_outcome_received(self, event) -> None:
        """
        Handle world.outcome_received events.
        
        Event data:
        - outcome_type: str ("took_damage", "found_reward", etc.)
        - outcome_valence: float (optional, -1 to +1)
        - action_name: str (optional, for specific action)
        - details: dict (optional)
        """
        try:
            outcome_type = event.data.get('outcome_type', '')
            outcome_valence = event.data.get('outcome_valence')
            action_name = event.data.get('action_name')
            
            # Valence belirlenmemişse, mapping'den al
            if outcome_valence is None:
                outcome_valence = self.outcome_mapping.get_valence(outcome_type)
            
            # Marker güncelle
            marker = self.somatic.record_outcome(
                outcome_valence=outcome_valence,
                outcome_description=outcome_type,
                action_name=action_name,
            )
            
            self.outcomes_recorded += 1
            self.events_processed += 1
            
            if marker:
                # İstatistik güncelle
                if marker.activation_count == 1:
                    self.markers_created += 1
                    event_type = 'somatic.marker_created'
                else:
                    self.markers_reinforced += 1
                    event_type = 'somatic.marker_reinforced'
                
                # Publish marker event
                await self._publish_marker_event(marker, event_type)
                
                self.logger.info(
                    "[SomaticHandler] Outcome processed: %s → valence=%.2f, marker=%s",
                    outcome_type, outcome_valence, marker.action
                )
            
        except Exception as e:
            self.logger.error("[SomaticHandler] Error recording outcome: %s", e)
    
    async def _on_emotion_changed(self, event) -> None:
        """
        Handle emotion.state_changed events.
        Update current emotion context.
        """
        try:
            self.current_emotion = {
                'valence': event.data.get('valence', 0.0),
                'arousal': event.data.get('arousal', 0.0),
                'dominance': event.data.get('dominance', 0.0),
            }
            self.events_processed += 1
            
            self.logger.debug(
                "[SomaticHandler] Emotion context updated: v=%.2f, a=%.2f",
                self.current_emotion['valence'],
                self.current_emotion['arousal']
            )
            
        except Exception as e:
            self.logger.error("[SomaticHandler] Error updating emotion: %s", e)
    
    async def _on_perception_data(self, event) -> None:
        """
        Handle perception.new_data events.
        Update current world state context.
        """
        try:
            self.current_world_state = {
                'danger_level': event.data.get('danger_level', 0),
                'objects_count': event.data.get('objects_count', 0),
                'agents_count': event.data.get('agents_count', 0),
                'symbols': event.data.get('symbols', []),
                'nearest_target': event.data.get('nearest_target'),
                'nearest_danger': event.data.get('nearest_danger'),
                'tick': event.data.get('tick', 0),
            }
            
        except Exception as e:
            self.logger.error("[SomaticHandler] Error updating world state: %s", e)
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _build_world_state(self, action_params: Dict[str, Any]) -> Dict[str, Any]:
        """Action params ve current context'ten world state oluştur"""
        # Base: current world state
        world_state = self.current_world_state.copy()
        
        # Action params'tan ek bilgi
        if 'danger_level' in action_params:
            world_state['danger_level'] = action_params['danger_level']
        if 'target_id' in action_params:
            world_state['nearest_target'] = action_params['target_id']
        if 'symbols' in action_params:
            world_state['symbols'] = action_params['symbols']
        
        return world_state
    
    async def _publish_marker_event(self, marker, event_type: str) -> None:
        """Marker event'i publish et"""
        if self.event_bus is None:
            return
        
        try:
            from core.event_bus import Event, EventPriority
            
            event = Event(
                type=event_type,
                source='somatic_event_handler',
                data={
                    'situation_hash': marker.situation_hash,
                    'action': marker.action,
                    'valence': marker.valence,
                    'strength': marker.strength,
                    'activation_count': marker.activation_count,
                    'original_outcome': marker.original_outcome,
                },
                priority=EventPriority.LOW
            )
            
            await self.event_bus.publish(event)
            
        except Exception as e:
            self.logger.debug("[SomaticHandler] Failed to publish marker event: %s", e)
    
    # =========================================================================
    # MANUAL API (Event bus olmadan kullanım için)
    # =========================================================================
    
    def manual_record_outcome(
        self,
        outcome_type: str,
        outcome_valence: Optional[float] = None,
        action_name: Optional[str] = None,
    ) -> None:
        """
        Manuel outcome kaydı (event bus olmadan).
        
        Args:
            outcome_type: "took_damage", "found_reward", etc.
            outcome_valence: -1 to +1 (None = mapping'den al)
            action_name: Belirli bir eylem için
        """
        if outcome_valence is None:
            outcome_valence = self.outcome_mapping.get_valence(outcome_type)
        
        marker = self.somatic.record_outcome(
            outcome_valence=outcome_valence,
            outcome_description=outcome_type,
            action_name=action_name,
        )
        
        self.outcomes_recorded += 1
        
        if marker:
            if marker.activation_count == 1:
                self.markers_created += 1
            else:
                self.markers_reinforced += 1
            
            self.logger.info(
                "[SomaticHandler] Manual outcome: %s → valence=%.2f",
                outcome_type, outcome_valence
            )
    
    # =========================================================================
    # STATISTICS
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Handler istatistikleri"""
        somatic_stats = self.somatic.get_stats() if self.somatic else {}
        
        return {
            'handler': {
                'events_processed': self.events_processed,
                'actions_recorded': self.actions_recorded,
                'outcomes_recorded': self.outcomes_recorded,
                'markers_created': self.markers_created,
                'markers_reinforced': self.markers_reinforced,
                'initialized': self._initialized,
            },
            'somatic': somatic_stats,
            'current_emotion': self.current_emotion.copy(),
        }


# =========================================================================
# FACTORY FUNCTION
# =========================================================================

def create_somatic_handler(
    event_bus: Any,
    persistence_path: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> SomaticEventHandler:
    """
    Somatic handler oluştur (convenience function).
    
    Args:
        event_bus: EventBus instance
        persistence_path: Marker'ları kaydetmek için dosya yolu
        logger: Logger instance
    
    Returns:
        SomaticEventHandler (initialize() çağrılmalı)
    """
    from core.emotion.somatic_marker_system import SomaticMarkerSystem
    
    somatic = SomaticMarkerSystem(
        persistence_path=persistence_path,
        logger=logger.getChild("Somatic") if logger else None,
    )
    
    return SomaticEventHandler(
        somatic_system=somatic,
        event_bus=event_bus,
        logger=logger,
    )


# =========================================================================
# WORLD OUTCOME EVENT HELPER
# =========================================================================

class WorldOutcomePublisher:
    """
    World/Game sisteminden outcome event'leri publish etmek için helper.
    
    Kullanım (game loop içinde):
        publisher = WorldOutcomePublisher(event_bus)
        
        # Agent hasar aldığında:
        await publisher.damage_taken(amount=10)
        
        # Ödül bulunduğunda:
        await publisher.reward_found(reward_type="gold", amount=50)
    """
    
    def __init__(self, event_bus: Any, logger: Optional[logging.Logger] = None):
        self.event_bus = event_bus
        self.logger = logger or logging.getLogger("world.OutcomePublisher")
    
    async def _publish(
        self,
        outcome_type: str,
        valence: Optional[float] = None,
        action_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Base publish method"""
        if self.event_bus is None:
            return
        
        try:
            from core.event_bus import Event, EventPriority
            
            data = {
                'outcome_type': outcome_type,
                'details': details or {},
                'timestamp': time.time(),
            }
            
            if valence is not None:
                data['outcome_valence'] = valence
            if action_name:
                data['action_name'] = action_name
            
            # Priority: damage/death = HIGH, others = NORMAL
            priority = EventPriority.HIGH if valence and valence < -0.5 else EventPriority.NORMAL
            
            event = Event(
                type='world.outcome_received',
                source='world_outcome_publisher',
                data=data,
                priority=priority
            )
            
            await self.event_bus.publish(event)
            self.logger.debug("[OutcomePublisher] Published: %s", outcome_type)
            
        except Exception as e:
            self.logger.error("[OutcomePublisher] Failed to publish: %s", e)
    
    # Convenience methods
    async def damage_taken(
        self,
        amount: float = 0,
        source: str = "unknown",
        action_name: Optional[str] = None,
    ) -> None:
        """Agent hasar aldı"""
        # Valence: hasar miktarına göre -0.3 ile -1.0 arası
        valence = max(-1.0, -0.3 - (amount / 100) * 0.7)
        await self._publish(
            'took_damage',
            valence=valence,
            action_name=action_name,
            details={'amount': amount, 'source': source}
        )
    
    async def reward_found(
        self,
        reward_type: str = "generic",
        amount: float = 0,
        action_name: Optional[str] = None,
    ) -> None:
        """Ödül bulundu"""
        # Valence: ödül miktarına göre 0.3 ile 0.9 arası
        valence = min(0.9, 0.3 + (amount / 100) * 0.6)
        await self._publish(
            'found_reward',
            valence=valence,
            action_name=action_name,
            details={'type': reward_type, 'amount': amount}
        )
    
    async def task_completed(
        self,
        task_name: str = "",
        success_level: float = 1.0,
        action_name: Optional[str] = None,
    ) -> None:
        """Görev tamamlandı"""
        valence = 0.5 + (success_level * 0.4)
        await self._publish(
            'task_completed',
            valence=valence,
            action_name=action_name,
            details={'task': task_name, 'success': success_level}
        )
    
    async def task_failed(
        self,
        task_name: str = "",
        reason: str = "",
        action_name: Optional[str] = None,
    ) -> None:
        """Görev başarısız"""
        await self._publish(
            'task_failed',
            valence=-0.5,
            action_name=action_name,
            details={'task': task_name, 'reason': reason}
        )
    
    async def npc_interaction(
        self,
        npc_id: str,
        interaction_type: str,  # "friendly", "hostile", "neutral"
        action_name: Optional[str] = None,
    ) -> None:
        """NPC etkileşimi"""
        valence_map = {
            'friendly': 0.4,
            'hostile': -0.5,
            'neutral': 0.0,
        }
        valence = valence_map.get(interaction_type, 0.0)
        outcome_type = f"npc_{interaction_type}"
        
        await self._publish(
            outcome_type,
            valence=valence,
            action_name=action_name,
            details={'npc_id': npc_id}
        )
    
    async def death(self, cause: str = "unknown") -> None:
        """Agent öldü"""
        await self._publish(
            'died',
            valence=-1.0,
            details={'cause': cause}
        )
    
    async def custom_outcome(
        self,
        outcome_type: str,
        valence: float,
        action_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Özel outcome"""
        await self._publish(
            outcome_type,
            valence=valence,
            action_name=action_name,
            details=details
        )
