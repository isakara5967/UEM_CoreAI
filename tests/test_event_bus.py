import pytest
import asyncio
import sys

# Windows için gerekli
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from core.event_bus import EventBus, Event, EventPriority


@pytest.fixture
async def event_bus():
    bus = EventBus('tcp://127.0.0.1:5556')
    await bus.start()
    yield bus
    await bus.stop()


@pytest.mark.asyncio
async def test_publish_subscribe(event_bus):
    received_events = []
    
    async def handler(event: Event):
        received_events.append(event)
    
    await event_bus.subscribe('test.event', handler)
    
    test_event = Event(
        type='test.event',
        source='test',
        data={'message': 'hello'}
    )
    
    await event_bus.publish(test_event)
    await asyncio.sleep(0.3)
    
    assert len(received_events) == 1
    assert received_events[0].data['message'] == 'hello'


@pytest.mark.asyncio
async def test_multiple_handlers(event_bus):
    results = []
    
    async def handler1(event: Event):
        results.append('handler1')
    
    async def handler2(event: Event):
        results.append('handler2')
    
    await event_bus.subscribe('multi.test', handler1)
    await event_bus.subscribe('multi.test', handler2)
    
    await event_bus.publish(Event(
        type='multi.test',
        source='test',
        data={}
    ))
    
    await asyncio.sleep(0.3)
    
    assert len(results) == 2
    assert 'handler1' in results
    assert 'handler2' in results
