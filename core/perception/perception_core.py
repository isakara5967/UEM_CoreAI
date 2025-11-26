import logging
from typing import Any, Optional

from core.perception.types import (
    PerceivedObject,
    PerceivedAgent,
    EnvironmentState,
    PerceptionResult,
    WorldSnapshot,
)
from core.perception.noise_filter.noise_filter import NoiseFilter
from core.perception.feature_extraction.feature_extractor import FeatureExtractor
from core.perception.state.state_perception import StatePerception
from core.perception.symbolic.symbolic_perception import SymbolicPerception


class PerceptionCore:
    '''UEM algı pipeline - Event-aware version'''

    def __init__(
        self,
        config: dict[str, Any] | None,
        world_interface: Any,
        memory_core: Any | None = None,
        logger: Optional[logging.Logger] = None,
        event_bus: Any | None = None,
    ) -> None:
        self.config = config or {}
        self.world = world_interface
        self.memory = memory_core
        self.event_bus = event_bus

        base_logger = logger or logging.getLogger('core.perception')
        self.logger = base_logger

        self.noise_filter: Optional[NoiseFilter] = None
        self.feature_extractor: Optional[FeatureExtractor] = None
        self.state_perception: Optional[StatePerception] = None
        self.symbolic_perception: Optional[SymbolicPerception] = None

        self.last_result: Optional[PerceptionResult] = None

    def start(self) -> None:
        '''Initialize perception pipeline'''
        max_distance = float(self.config.get('max_distance', 100.0))

        self.noise_filter = NoiseFilter(
            max_distance=max_distance,
            logger=self.logger.getChild('NoiseFilter'),
        )
        self.feature_extractor = FeatureExtractor(
            logger=self.logger.getChild('FeatureExtractor')
        )
        self.state_perception = StatePerception(
            logger=self.logger.getChild('StatePerception')
        )
        self.symbolic_perception = SymbolicPerception(
            logger=self.logger.getChild('SymbolicPerception')
        )

        self.logger.info(
            '[Perception] PerceptionCore initialized '
            '(max_distance=%.1f).',
            max_distance,
        )

    def update(self, dt: float) -> None:
        '''Sync update - processes perception and publishes events'''
        if self.world is None:
            self.logger.warning('[Perception] World interface is None; skipping update.')
            return

        if self.noise_filter is None:
            self.logger.error('[Perception] start() not called; noise_filter is None.')
            return

        if (
            self.feature_extractor is None
            or self.state_perception is None
            or self.symbolic_perception is None
        ):
            self.logger.error('[Perception] start() not fully initialized.')
            return

        # Process perception
        raw_snapshot = self._get_world_snapshot()
        if raw_snapshot is None:
            return

        filtered_snapshot = self.noise_filter.process(raw_snapshot)
        objects, agents = self.feature_extractor.process(filtered_snapshot)
        env_state = self.state_perception.infer_state(
            filtered_snapshot, objects, agents
        )
        symbols = self.symbolic_perception.infer_symbols(
            env_state, objects, agents
        )

        result = PerceptionResult(
            snapshot=filtered_snapshot,
            objects=objects,
            agents=agents,
            environment_state=env_state,
            symbols=symbols,
        )

        self.last_result = result

        # Store in memory (legacy)
        if self.memory is not None and hasattr(self.memory, 'store_perception'):
            try:
                self.memory.store_perception(result)
            except Exception as exc:
                self.logger.debug(
                    '[Perception] memory.store_perception failed: %s', exc
                )

        # Publish event (new)
        if self.event_bus is not None:
            import asyncio
            from core.event_bus import Event, EventPriority
            
            # Determine priority based on danger
            priority = EventPriority.CRITICAL if env_state.danger_level > 0.7 else EventPriority.HIGH
            
            event = Event(
                type='perception.new_data',
                source='perception_core',
                data={
                    'tick': filtered_snapshot.tick,
                    'danger_level': env_state.danger_level,
                    'objects_count': len(objects),
                    'agents_count': len(agents),
                    'symbols': symbols,
                    'nearest_danger': env_state.nearest_danger.id if env_state.nearest_danger else None,
                    'nearest_target': env_state.nearest_target.id if env_state.nearest_target else None,
                },
                priority=priority
            )
            
            # Schedule async publish
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.event_bus.publish(event))
            except RuntimeError:
                self.logger.debug('[Perception] No event loop running, skipping event publish')

        self.logger.debug(
            '[Perception] tick processed: objects=%d, agents=%d, symbols=%s',
            len(result.objects),
            len(result.agents),
            result.symbols,
        )

    def _get_world_snapshot(self) -> Optional[WorldSnapshot]:
        '''Get snapshot from world interface'''
        if not hasattr(self.world, 'get_snapshot'):
            self.logger.warning(
                '[Perception] World interface has no get_snapshot(); skipping.'
            )
            return None

        raw = self.world.get_snapshot()
        if raw is None:
            return None

        if isinstance(raw, WorldSnapshot):
            return raw

        if isinstance(raw, dict):
            try:
                tick = int(raw.get('tick', 0))
                timestamp = float(raw.get('timestamp', 0.0))
                agent_position = tuple(raw.get('agent_position', (0.0, 0.0, 0.0)))
                objects = list(raw.get('objects', []))
                agents = list(raw.get('agents', []))
                environment = dict(raw.get('environment', {}))

                snapshot = WorldSnapshot(
                    tick=tick,
                    timestamp=timestamp,
                    agent_position=agent_position,
                    objects=objects,
                    agents=agents,
                    environment=environment,
                )
                return snapshot
            except Exception as exc:
                self.logger.error(
                    '[Perception] Failed to adapt raw snapshot dict -> WorldSnapshot: %s',
                    exc,
                )
                return None

        self.logger.warning(
            '[Perception] Unsupported snapshot type from world: %r', type(raw)
        )
        return None

    def process(self, world_state: Any) -> 'PerceptionResult':
        '''
        UnifiedUEMCore uyumlu API.
        
        WorldState alır, PerceptionResult döndürür.
        Bu metod update() yerine doğrudan çağrılabilir.
        
        Args:
            world_state: WorldState veya dict benzeri obje
            
        Returns:
            PerceptionResult veya world_state (fallback)
        '''
        # Ensure pipeline is initialized
        if self.noise_filter is None:
            self.start()
        
        # Extract data from world_state
        tick = getattr(world_state, 'tick', 0)
        danger_level = getattr(world_state, 'danger_level', 0.0)
        objects = getattr(world_state, 'objects', [])
        agents = getattr(world_state, 'agents', [])
        symbols = getattr(world_state, 'symbols', [])
        player_health = getattr(world_state, 'player_health', 1.0)
        player_energy = getattr(world_state, 'player_energy', 1.0)
        
        # Build minimal WorldSnapshot
        snapshot = WorldSnapshot(
            tick=tick,
            timestamp=float(tick),
            agent_position=(0.0, 0.0, 0.0),
            objects=objects,
            agents=agents,
            environment={
                'danger_level': danger_level,
                'player_health': player_health,
                'player_energy': player_energy,
            },
        )
        
        # Process through pipeline (simplified)
        processed_objects = []
        for obj in objects:
            obj_id = obj.get('id', f'obj_{len(processed_objects)}')
            obj_type = obj.get('type', 'unknown')
            processed_objects.append(PerceivedObject(
                id=obj_id,
                obj_type=obj_type,
                position=(0.0, 0.0, 0.0),
                distance=1.0,
                is_dangerous=obj_type in ('enemy', 'trap', 'hazard'),
                is_interactable=obj_type in ('food', 'water', 'item', 'treasure'),
                raw=obj,
            ))
        
        processed_agents = []
        for agent in agents:
            agent_id = agent.get('id', f'agent_{len(processed_agents)}')
            agent_type = agent.get('type', 'unknown')
            relation = 'hostile' if agent_type == 'enemy' else 'neutral'
            processed_agents.append(PerceivedAgent(
                id=agent_id,
                agent_type=agent_type,
                position=(0.0, 0.0, 0.0),
                relation=relation,
                raw=agent,
            ))
        
        # Find nearest danger
        nearest_danger = None
        for obj in processed_objects:
            if obj.is_dangerous:
                nearest_danger = obj
                break
        
        # Build environment state
        env_state = EnvironmentState(
            danger_level=danger_level,
            nearest_danger=nearest_danger,
            nearest_target=None,
            notes=f"tick={tick}, symbols={symbols}",
        )
        
        # Build result
        result = PerceptionResult(
            snapshot=snapshot,
            objects=processed_objects,
            agents=processed_agents,
            environment_state=env_state,
            symbols=list(symbols),
        )
        
        self.last_result = result
        
        self.logger.debug(
            '[Perception] process(): tick=%d, objects=%d, agents=%d, danger=%.2f',
            tick, len(processed_objects), len(processed_agents), danger_level,
        )
        
        return result
