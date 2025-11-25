import asyncio
import logging
from typing import Any, Optional

from core.memory.memory_core import MemoryCore
from core.memory.working.working_memory import WorkingMemoryState
from core.planning.action_selection.action_selector import (
    ActionCommand,
    ActionSelector,
)


class PlanningCore:
    '''UEM planlama / karar verme çekirdeği - Event-aware version'''

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        memory_core: Optional[MemoryCore] = None,
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

        self.action_selector: Optional[ActionSelector] = None
        self.last_action: Optional[ActionCommand] = None

    def start(self) -> None:
        '''Initialize planning system'''
        self.action_selector = ActionSelector(
            logger=self.logger.getChild('ActionSelector')
        )

        self.logger.info('[Planning] PlanningCore initialized.')

    def update(self, dt: float) -> None:
        '''Tek bir karar verme tick'i'''
        if self.action_selector is None:
            self.logger.error('[Planning] start() not called; action_selector is None.')
            return

        if self.memory is None:
            self.logger.warning('[Planning] MemoryCore is None; skipping planning.')
            return

        wm_state = self.memory.get_working_state()
        if wm_state is None:
            self.logger.debug('[Planning] No WorkingMemoryState available; skipping.')
            return

        # 1) Eylem seç
        action = self.action_selector.select_action(wm_state)
        self.last_action = action

        self.logger.debug('[Planning] Selected action: %r', action)

        # 2) Publish planning event
        if self.event_bus:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self._publish_action_event(action))
            except RuntimeError:
                self.logger.debug('[Planning] No event loop, skipping event publish')

        # 3) Dünya arayüzüne iletmeye çalış (varsa)
        self._send_action_to_world(action, wm_state)

    async def _publish_action_event(self, action: ActionCommand):
        '''Publish action decision to event bus'''
        from core.event_bus import Event, EventPriority
        
        # Priority based on action urgency
        priority = EventPriority.HIGH if action.name == 'ESCAPE' else EventPriority.NORMAL
        
        event = Event(
            type='planning.action_decided',
            source='planning_core',
            data={
                'action_name': action.name,
                'action_params': action.params,
            },
            priority=priority
        )
        
        await self.event_bus.publish(event)
        self.logger.debug('[Planning] Published action event: %s', action.name)

    def _send_action_to_world(
        self,
        action: ActionCommand,
        wm_state: WorkingMemoryState,
    ) -> None:
        '''Send action to world interface (legacy)'''
        if self.world is None:
            self.logger.debug('[Planning] No world interface; action not dispatched.')
            return

        try:
            if hasattr(self.world, 'enqueue_action'):
                self.world.enqueue_action(action)
                self.logger.debug('[Planning] Action enqueued to world: %r', action)
            elif hasattr(self.world, 'apply_action'):
                self.world.apply_action(action)
                self.logger.debug('[Planning] Action applied to world: %r', action)
            else:
                self.logger.debug(
                    '[Planning] World interface has no enqueue/apply; action not dispatched.'
                )
        except Exception as exc:
            self.logger.debug('[Planning] Failed to dispatch action to world: %s', exc)
