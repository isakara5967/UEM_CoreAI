"""
Event-Aware Planning Core for UEM

Emotion → Planning feedback loop:
1. emotion.state_changed event'ini dinler
2. EmotionalActionSelector'a emotion state'i iletir
3. Karar verirken duygusal durumu dikkate alır
"""

from __future__ import annotations
import asyncio
import logging
from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class WorkingMemoryState:
    """Karar verme için özet zihin durumu"""
    tick: int = 0
    danger_level: float = 0.0
    nearest_target: Any = None
    visible_objects: int = 0
    visible_agents: int = 0
    symbols: list = None
    notes: str = ""
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = []


class EmotionAwarePlanningCore:
    """
    UEM planlama çekirdeği - Emotion feedback loop entegrasyonlu.
    
    Event subscriptions:
    - emotion.state_changed → ActionSelector'ı güncelle
    
    Event publications:
    - planning.action_decided → Karar alındığında
    - planning.emotion_influenced → Duygunun karara etkisi
    """

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        memory_core: Any | None = None,
        world_interface: Any | None = None,
        logger: Optional[logging.Logger] = None,
        event_bus: Any | None = None,
    ) -> None:
        self.config = config or {}
        self.memory = memory_core
        self.world = world_interface
        self.event_bus = event_bus
        
        base_logger = logger or logging.getLogger('core.planning')
        self.logger = base_logger
        
        # Import here to avoid circular
        from core.planning.action_selection.emotional_action_selector import (
            EmotionalActionSelector,
            ActionCommand,
        )
        
        self.action_selector: Optional[EmotionalActionSelector] = None
        self.last_action: Optional[ActionCommand] = None
        self.last_emotion_state: dict = {}
        
        # Emotion feedback metrics
        self.emotion_influence_history: list = []
        self.decisions_with_emotion: int = 0
        self.total_decisions: int = 0

    async def initialize(self) -> None:
        """Async initialization - subscribe to emotion events"""
        if self.event_bus is not None:
            await self.event_bus.subscribe(
                'emotion.state_changed', 
                self._on_emotion_changed
            )
            self.logger.info('[Planning] Subscribed to emotion.state_changed events')

    def start(self) -> None:
        """Sync initialization"""
        from core.planning.action_selection.emotional_action_selector import (
            EmotionalActionSelector
        )
        
        self.action_selector = EmotionalActionSelector(
            logger=self.logger.getChild('ActionSelector')
        )
        
        self.logger.info('[Planning] EmotionAwarePlanningCore initialized.')

    async def _on_emotion_changed(self, event) -> None:
        """
        Handle emotion.state_changed events.
        
        Event data:
        - valence: float
        - arousal: float
        - dominance: float
        - emotion: str (label)
        - trigger_action: str (hangi eylem tetikledi)
        """
        emotion_data = event.data
        self.last_emotion_state = emotion_data
        
        if self.action_selector is not None:
            self.action_selector.update_emotional_state(emotion_data)
            
        self.logger.debug(
            '[Planning] Emotion state updated: %s (v=%.2f, a=%.2f)',
            emotion_data.get('emotion', 'unknown'),
            emotion_data.get('valence', 0),
            emotion_data.get('arousal', 0)
        )

    def update(self, dt: float) -> None:
        """Tek bir karar verme tick'i"""
        if self.action_selector is None:
            self.logger.error('[Planning] start() not called; action_selector is None.')
            return
        
        # Memory'den working state al
        wm_state = self._get_working_state()
        if wm_state is None:
            self.logger.debug('[Planning] No WorkingMemoryState available; skipping.')
            return
        
        # Eylem seç (emotion-aware)
        action = self.action_selector.select_action(wm_state)
        self.last_action = action
        self.total_decisions += 1
        
        # Emotion influence tracking
        if action.emotional_influence > 0.3:
            self.decisions_with_emotion += 1
            self.emotion_influence_history.append({
                'tick': wm_state.tick,
                'action': action.name,
                'influence': action.emotional_influence,
                'emotion': self.last_emotion_state.get('emotion', 'unknown')
            })
        
        self.logger.info(
            '[Planning] Action: %s (conf=%.2f, emotion_inf=%.2f, emotion=%s)',
            action.name,
            action.confidence,
            action.emotional_influence,
            self.last_emotion_state.get('emotion', 'neutral')
        )
        
        # Event publish
        if self.event_bus:
            self._schedule_action_event(action, wm_state)
        
        # World'e gönder (legacy)
        self._send_action_to_world(action, wm_state)

    def _get_working_state(self) -> Optional[WorkingMemoryState]:
        """Memory'den working state al veya mock oluştur"""
        if self.memory is not None and hasattr(self.memory, 'get_working_state'):
            state = self.memory.get_working_state()
            if state is not None:
                return state
        
        # Test için mock state
        return None

    def _schedule_action_event(self, action, wm_state: WorkingMemoryState) -> None:
        """Async event publish'i schedule et"""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._publish_action_event(action, wm_state))
        except RuntimeError:
            self.logger.debug('[Planning] No event loop, skipping event publish')

    async def _publish_action_event(self, action, wm_state: WorkingMemoryState) -> None:
        """Action event'ini publish et"""
        # Event import (avoid circular)
        try:
            from core.event_bus import Event, EventPriority
        except ImportError:
            return
        
        # Priority: ESCAPE/PANIC için CRITICAL
        if 'ESCAPE' in action.name or 'PANIC' in action.name:
            priority = EventPriority.CRITICAL
        elif 'CONFRONT' in action.name:
            priority = EventPriority.HIGH
        else:
            priority = EventPriority.NORMAL
        
        # Main action event
        event = Event(
            type='planning.action_decided',
            source='planning_core',
            data={
                'action_name': action.name,
                'action_params': action.params,
                'confidence': action.confidence,
                'emotional_influence': action.emotional_influence,
                'current_emotion': self.last_emotion_state.get('emotion', 'neutral'),
            },
            priority=priority
        )
        await self.event_bus.publish(event)
        
        # Emotion influence event (eğer yüksekse)
        if action.emotional_influence > 0.5:
            influence_event = Event(
                type='planning.emotion_influenced',
                source='planning_core',
                data={
                    'action_name': action.name,
                    'influence_level': action.emotional_influence,
                    'emotion': self.last_emotion_state.get('emotion', 'neutral'),
                    'valence': self.last_emotion_state.get('valence', 0),
                    'arousal': self.last_emotion_state.get('arousal', 0),
                },
                priority=EventPriority.NORMAL
            )
            await self.event_bus.publish(influence_event)
            self.logger.debug(
                '[Planning] Published emotion_influenced event (influence=%.2f)',
                action.emotional_influence
            )

    def _send_action_to_world(self, action, wm_state: WorkingMemoryState) -> None:
        """World interface'e eylem gönder (legacy)"""
        if self.world is None:
            return
        
        try:
            if hasattr(self.world, 'enqueue_action'):
                self.world.enqueue_action(action)
            elif hasattr(self.world, 'apply_action'):
                self.world.apply_action(action)
        except Exception as exc:
            self.logger.debug('[Planning] Failed to dispatch action: %s', exc)

    def get_emotion_influence_stats(self) -> dict:
        """Emotion influence istatistiklerini döndür"""
        if self.total_decisions == 0:
            return {'ratio': 0, 'count': 0, 'total': 0}
        
        return {
            'ratio': self.decisions_with_emotion / self.total_decisions,
            'count': self.decisions_with_emotion,
            'total': self.total_decisions,
            'recent_influences': self.emotion_influence_history[-10:]
        }


# Geriye uyumluluk
PlanningCore = EmotionAwarePlanningCore
