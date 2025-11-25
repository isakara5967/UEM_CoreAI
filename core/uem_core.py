import asyncio
import logging
from typing import Any, Dict, Optional

from .memory import MemoryCore
from .cognition import CognitionCore
from .perception import PerceptionCore
from .emotion import EmotionCore
from .planning import PlanningCore
from .self import SelfCore
from .metamind import MetaMindCore
from .ethmor.ethmor_system import EthmorSynthSystem
from .event_bus import EventBus, Event, EventPriority


class UEMCore:
    '''UEM ana orkestratörü - Event-driven async version'''

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None,
        world_interface: Any | None = None,
    ) -> None:
        self.config: Dict[str, Any] = config or {}
        self.logger: logging.Logger = logger or logging.getLogger('uem_core')
        self.world_interface: Any | None = world_interface
        
        self.started: bool = False
        
        # Event Bus
        event_bus_address = self.config.get('event_bus', {}).get(
            'address', 'tcp://127.0.0.1:5555'
        )
        self.event_bus = EventBus(event_bus_address)
        
        # Alt sistemler
        self.memory = MemoryCore()
        self.cognition = CognitionCore()
        
        self.perception = PerceptionCore(
            config=self.config.get('perception', {}),
            world_interface=self.world_interface,
            memory_core=self.memory,
            logger=self.logger.getChild('perception'),
        )
        
        self.emotion = EmotionCore()
        self.planning = PlanningCore(
            config=self.config.get('planning', {}),
            memory_core=self.memory,
            world_interface=self.world_interface,
            logger=self.logger.getChild('planning'),
        )
        
        self.metamind = MetaMindCore()
        self.ethmor_system = EthmorSynthSystem()
        
        self.self_system = SelfCore(
            memory_system=self.memory,
            emotion_system=self.emotion,
            cognition_system=self.cognition,
            planning_system=self.planning,
            metamind_system=self.metamind,
            ethmor_system=self.ethmor_system,
            logger=self.logger,
            config=self.config.get('self', None),
        )

    async def initialize(self) -> None:
        '''Async initialization - start event bus and subscribe modules'''
        if self.started:
            self.logger.warning('UEMCore.initialize() called but already started.')
            return
        
        self.started = True
        
        # Start event bus
        await self.event_bus.start()
        self.logger.info('[UEM] Event bus started')
        
        # Setup event subscriptions
        await self._setup_event_subscriptions()
        
        # Start subsystems (sync initialization)
        self.logger.info('[UEM] Core initialized.')
        
        self.logger.info('[UEM] Memory system loading...')
        if hasattr(self.memory, 'start'):
            self.memory.start()
        
        self.logger.info('[UEM] Cognition system loading...')
        if hasattr(self.cognition, 'start'):
            self.cognition.start()
        
        self.logger.info('[UEM] Perception system loading...')
        if hasattr(self.perception, 'start'):
            self.perception.start()
        
        self.logger.info('[UEM] Emotion system loading...')
        if hasattr(self.emotion, 'start'):
            self.emotion.start()
        
        self.logger.info('[UEM] Planning system loading...')
        if hasattr(self.planning, 'start'):
            self.planning.start()
        
        self.logger.info('[UEM] EthmorSynth system loading...')
        if hasattr(self.ethmor_system, 'start'):
            self.ethmor_system.start()
        
        self.logger.info('[UEM] Self system loading...')
        if hasattr(self.self_system, 'start'):
            self.self_system.start()
        
        self.logger.info('[UEM] MetaMind system loading...')
        if hasattr(self.metamind, 'start'):
            self.metamind.start()
        
        self.logger.info('[UEM] All subsystems started.')

    async def _setup_event_subscriptions(self) -> None:
        '''Wire up event handlers between modules'''
        
        # Perception events
        await self.event_bus.subscribe('perception.new_data', self._on_perception_data)
        
        # Memory events  
        await self.event_bus.subscribe('memory.retrieved', self._on_memory_retrieved)
        
        # Planning events
        await self.event_bus.subscribe('planning.action_decided', self._on_action_decided)
        
        # Emotion events
        await self.event_bus.subscribe('emotion.state_changed', self._on_emotion_changed)
        
        self.logger.info('[UEM] Event subscriptions configured')

    # Event handlers
    async def _on_perception_data(self, event: Event):
        '''Handle new perception data'''
        self.logger.debug(f'Perception event received: {event.type}')

    async def _on_memory_retrieved(self, event: Event):
        '''Handle memory retrieval results'''
        self.logger.debug(f'Memory retrieval event: {event.type}')

    async def _on_action_decided(self, event: Event):
        '''Handle planning decisions'''
        action = event.data.get('action', 'unknown')
        self.logger.debug(f'Action decided: {action}')

    async def _on_emotion_changed(self, event: Event):
        '''Handle emotion state changes'''
        self.logger.debug(f'Emotion changed: {event.data}')

    async def step(
        self,
        world_state: Optional[Dict[str, Any]] = None,
        dt: Optional[float] = None,
    ) -> None:
        '''Async cognitive cycle step'''
        if dt is None:
            dt = (
                self.config.get('loop', {}).get('tick_seconds', 0.1)
                if self.config is not None
                else 0.1
            )
        
        # Publish tick event
        await self.event_bus.publish(Event(
            type='core.tick',
            source='uem_core',
            data={'dt': dt, 'world_state': world_state},
            priority=EventPriority.HIGH
        ))
        
        # Run sync update
        self.update(dt=dt, world_snapshot=world_state)

    def update(
        self,
        dt: float = 0.1,
        world_snapshot: Optional[Dict[str, Any]] = None,
    ) -> None:
        '''Synchronous update (legacy)'''
        if not self.started:
            return
        
        self.logger.debug('UEMCore.update() tick started (dt=%s)', dt)
        
        # Subsystem updates
        if hasattr(self.perception, 'update'):
            self.perception.update(dt)
        
        if hasattr(self.memory, 'update'):
            self.memory.update(dt)
        
        if hasattr(self.cognition, 'update'):
            self.cognition.update(dt)
        
        if hasattr(self.emotion, 'update'):
            self.emotion.update(dt)
        
        if hasattr(self.planning, 'update'):
            self.planning.update(dt)
        
        if hasattr(self.ethmor_system, 'update'):
            self.ethmor_system.update(dt)
        
        if hasattr(self.self_system, 'update'):
            self.self_system.update(dt)
        
        if hasattr(self.metamind, 'update'):
            self.metamind.update(dt)
        
        self.logger.debug('UEMCore.update() tick finished.')

    def notify_event(self, event: Dict[str, Any]) -> None:
        '''Legacy sync event notification'''
        if not isinstance(event, dict):
            self.logger.warning('notify_event called with non-dict event: %r', event)
            return
        
        self.logger.debug('UEMCore.notify_event() event=%r', event)
        
        if hasattr(self.emotion, 'notify_event'):
            self.emotion.notify_event(event)
        
        if hasattr(self.memory, 'notify_event'):
            self.memory.notify_event(event)
        
        if hasattr(self.self_system, 'notify_event'):
            self.self_system.notify_event(event)
        
        if hasattr(self.ethmor_system, 'notify_event'):
            self.ethmor_system.notify_event(event)
        
        if hasattr(self.metamind, 'notify_event'):
            self.metamind.notify_event(event)

    async def shutdown(self) -> None:
        '''Gracefully stop UEM Core'''
        self.logger.info('[UEM] Shutting down...')
        
        # Stop event bus
        await self.event_bus.stop()
        
        # Subsystem cleanup logs
        if getattr(self, 'memory', None) is not None:
            self.logger.info(' - Memory system shutdown')
        if getattr(self, 'cognition', None) is not None:
            self.logger.info(' - Cognition system shutdown')
        if getattr(self, 'perception', None) is not None:
            self.logger.info(' - Perception system shutdown')
        if getattr(self, 'emotion', None) is not None:
            self.logger.info(' - Emotion system shutdown')
        if getattr(self, 'planning', None) is not None:
            self.logger.info(' - Planning system shutdown')
        if getattr(self, 'ethmor_system', None) is not None:
            self.logger.info(' - EthmorSynth system shutdown')
        if getattr(self, 'self_system', None) is not None:
            self.logger.info(' - Self system shutdown')
        if getattr(self, 'metamind', None) is not None:
            self.logger.info(' - MetaMind system shutdown')
        
        self.logger.info('[UEM] Shutdown complete')

    # Legacy sync API
    def start(self) -> None:
        '''Legacy sync start - deprecated, use initialize() instead'''
        self.logger.warning('Sync start() called - use async initialize() instead')
