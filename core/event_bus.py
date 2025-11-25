"""
Event Bus for UEM - ZeroMQ-based async message passing

Provides pub/sub communication between UEM modules.
"""

import asyncio
import json
import logging
import time
from typing import Callable, Dict, Set, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class EventPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    type: str
    source: str
    data: dict
    priority: EventPriority = EventPriority.NORMAL
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_json(self) -> str:
        d = asdict(self)
        d['priority'] = self.priority.value
        return json.dumps(d)
    
    @classmethod
    def from_json(cls, json_str: str):
        d = json.loads(json_str)
        d['priority'] = EventPriority(d['priority'])
        return cls(**d)


class EventBus:
    """ZeroMQ-based event bus for UEM modules"""
    
    def __init__(self, pub_address: str = 'tcp://127.0.0.1:5555'):
        self.pub_address = pub_address
        self.ctx = None
        self.pub_socket = None
        self.sub_socket = None
        self.handlers: Dict[str, Set[Callable]] = {}
        self.logger = logging.getLogger('uem.eventbus')
        self._running = False
        self._listener_task = None
        self._use_zmq = True
        
        # Try to import zmq
        try:
            import zmq
            import zmq.asyncio
            self._zmq = zmq
            self._zmq_asyncio = zmq.asyncio
        except ImportError:
            self.logger.warning("ZeroMQ not available, using in-memory event bus")
            self._use_zmq = False
    
    async def start(self):
        if self._use_zmq:
            await self._start_zmq()
        else:
            await self._start_memory()
    
    async def _start_zmq(self):
        self.ctx = self._zmq_asyncio.Context()
        
        # Publisher socket
        self.pub_socket = self.ctx.socket(self._zmq.PUB)
        self.pub_socket.bind(self.pub_address)
        
        # Subscriber socket
        self.sub_socket = self.ctx.socket(self._zmq.SUB)
        self.sub_socket.connect(self.pub_address)
        
        self._running = True
        self._listener_task = asyncio.create_task(self._listen_zmq())
        
        # ZMQ needs time to establish connection
        await asyncio.sleep(0.1)
        
        self.logger.info(f'EventBus started on {self.pub_address}')
    
    async def _start_memory(self):
        """Start in-memory event bus (no ZMQ)"""
        self._running = True
        self.logger.info('EventBus started (in-memory mode)')
    
    async def stop(self):
        self._running = False
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        
        if self._use_zmq:
            if self.pub_socket:
                self.pub_socket.close()
            if self.sub_socket:
                self.sub_socket.close()
            if self.ctx:
                self.ctx.term()
        
        self.logger.info('EventBus stopped')
    
    async def publish(self, event: Event):
        if self._use_zmq:
            await self._publish_zmq(event)
        else:
            await self._publish_memory(event)
    
    async def _publish_zmq(self, event: Event):
        topic = f'uem.{event.type}'
        message = event.to_json()
        await self.pub_socket.send_multipart([
            topic.encode('utf-8'),
            message.encode('utf-8')
        ])
        self.logger.debug(f'Published {event.type} from {event.source}')
    
    async def _publish_memory(self, event: Event):
        """Publish directly to handlers (no ZMQ)"""
        handlers = self.handlers.get(event.type, set())
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                self.logger.error(f'Handler error: {e}')
        self.logger.debug(f'Published {event.type} from {event.source}')
    
    async def subscribe(self, event_type: str, handler: Callable):
        if self._use_zmq:
            topic = f'uem.{event_type}'
            
            if event_type not in self.handlers:
                self.handlers[event_type] = set()
                self.sub_socket.setsockopt_string(self._zmq.SUBSCRIBE, topic)
                self.logger.info(f'Subscribed to {topic}')
            
            self.handlers[event_type].add(handler)
        else:
            # In-memory mode
            if event_type not in self.handlers:
                self.handlers[event_type] = set()
            self.handlers[event_type].add(handler)
            self.logger.info(f'Subscribed to {event_type}')
    
    async def _listen_zmq(self):
        try:
            while self._running:
                try:
                    topic_bytes, message_bytes = await asyncio.wait_for(
                        self.sub_socket.recv_multipart(),
                        timeout=0.1
                    )
                    topic = topic_bytes.decode('utf-8')
                    message = message_bytes.decode('utf-8')
                    await self._handle_message(topic, message)
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f'Listener error: {e}')
    
    async def _handle_message(self, topic: str, message: str):
        try:
            event = Event.from_json(message)
            handlers = self.handlers.get(event.type, set())
            
            tasks = []
            for handler in handlers:
                task = asyncio.create_task(handler(event))
                tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            self.logger.error(f'Handler error: {e}')
