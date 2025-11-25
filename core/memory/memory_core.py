import asyncio
import logging
from typing import Any, Optional

from core.perception.types import PerceptionResult
from core.memory.short_term.short_term_memory import ShortTermMemory
from core.memory.working.working_memory import WorkingMemory, WorkingMemoryState


class MemoryCore:
    '''UEM hafıza çekirdeği - Event-aware version'''

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        logger: Optional[logging.Logger] = None,
        event_bus: Any | None = None,
    ) -> None:
        self.config = config or {}
        base_logger = logger or logging.getLogger('core.memory')
        self.logger = base_logger
        self.event_bus = event_bus

        self.short_term: Optional[ShortTermMemory] = None
        self.working: Optional[WorkingMemory] = None

    def start(self) -> None:
        '''Initialize memory systems'''
        stm_capacity = int(self.config.get('short_term_capacity', 10))

        self.short_term = ShortTermMemory(
            capacity=stm_capacity,
            logger=self.logger.getChild('ShortTermMemory'),
        )
        self.working = WorkingMemory(
            logger=self.logger.getChild('WorkingMemory'),
        )

        self.logger.info(
            '[Memory] MemoryCore initialized (short_term_capacity=%d).',
            stm_capacity,
        )

    def update(self, dt: float) -> None:
        '''Per-tick update'''
        return

    # Event handlers
    async def on_perception_data(self, event) -> None:
        '''Handle perception events from event bus'''
        from core.event_bus import Event, EventPriority
        
        self.logger.debug(
            '[Memory] Received perception event: tick=%s, danger=%.2f, symbols=%s',
            event.data.get('tick'),
            event.data.get('danger_level', 0),
            event.data.get('symbols', [])
        )
        
        # Check for high-priority situations
        danger_level = event.data.get('danger_level', 0)
        if danger_level > 0.7:
            # Emergency recall - publish memory retrieval event
            await self._emergency_recall(event)

    async def _emergency_recall(self, trigger_event) -> None:
        '''High-priority memory search triggered by danger'''
        from core.event_bus import Event, EventPriority
        
        self.logger.info('[Memory] Emergency recall triggered by danger!')
        
        # In future: search episodic memory for similar threats
        # For now: just publish event
        if self.event_bus:
            recall_event = Event(
                type='memory.retrieved',
                source='memory_core',
                data={
                    'query_type': 'danger_response',
                    'trigger_danger': trigger_event.data.get('danger_level'),
                    'results': [],  # Placeholder
                    'emergency': True
                },
                priority=EventPriority.CRITICAL
            )
            await self.event_bus.publish(recall_event)

    # Legacy API
    def store_perception(self, perception: PerceptionResult) -> None:
        '''Legacy method - still used by sync code'''
        if self.short_term is None or self.working is None:
            self.logger.warning(
                '[Memory] store_perception called before start(); ignoring.'
            )
            return

        self.short_term.store_perception(perception)
        self.working.update_from_perception(perception)

    def get_last_perception(self) -> Optional[PerceptionResult]:
        if self.short_term is None:
            return None
        return self.short_term.get_last()

    def get_recent_perceptions(self):
        if self.short_term is None:
            return []
        return self.short_term.get_all()

    def get_working_state(self) -> Optional[WorkingMemoryState]:
        if self.working is None:
            return None
        return self.working.get_state()
