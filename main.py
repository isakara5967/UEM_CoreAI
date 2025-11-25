import asyncio
import logging
import sys
import time
from typing import Any, Dict

import yaml

# Windows için gerekli
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from world.test_dummy_world import TestDummyWorld
from core.uem_core import UEMCore
from core.logging_utils import setup_logging


def load_core_config(path: str = 'config/core.yaml') -> Dict[str, Any]:
    logger = logging.getLogger(__name__)
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
            logger.info('Config loaded from %s', path)
            return data
    except FileNotFoundError:
        logger.warning('Config file %s not found, using defaults.', path)
        return {}
    except Exception as e:
        logger.exception('Failed to load config from %s: %s', path, e)
        return {}


async def async_main() -> None:
    '''Async main loop'''
    logger = setup_logging('config/logging.yaml')
    logger.info('Starting UEM Core...')
    
    config = load_core_config('config/core.yaml')
    world = TestDummyWorld()
    
    core = UEMCore(
        config=config,
        world_interface=world,
        logger=logger
    )
    
    try:
        # Async initialize
        await core.initialize()
        
        tick_seconds = config.get('loop', {}).get('tick_seconds', 0.1)
        logger.info('Entering async main loop (tick_seconds=%s)', tick_seconds)
        
        while True:
            await core.step()
            await asyncio.sleep(tick_seconds)
    
    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt received; shutting down UEMCore.')
    except Exception:
        logger.exception('Fatal error in main loop.')
    finally:
        try:
            await core.shutdown()
        except Exception:
            logger.exception('Error during UEMCore shutdown.')
        logger.info('UEM Core stopped.')


def main() -> None:
    asyncio.run(async_main())


if __name__ == '__main__':
    main()
