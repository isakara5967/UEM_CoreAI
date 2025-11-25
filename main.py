import logging
import time
from typing import Any, Dict

import yaml  # pyyaml gerektirir

from world.test_dummy_world import TestDummyWorld

from core.uem_core import UEMCore
from core.logging_utils import setup_logging  # C.4'te yazacağız


def load_core_config(path: str = "config/core.yaml") -> Dict[str, Any]:
    """
    Çekirdek konfigürasyon dosyasını yükler.
    Dosya yoksa veya hata olursa boş dict döner.
    """
    logger = logging.getLogger(__name__)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            logger.info("Config loaded from %s", path)
            return data
    except FileNotFoundError:
        logger.warning("Config file %s not found, using defaults.", path)
        return {}
    except Exception as e:
        logger.exception("Failed to load config from %s: %s", path, e)
        return {}


def main() -> None:
    """
    UEM çekirdeğinin giriş noktası.
    - Logging'i başlatır
    - Config'i yükler
    - UEMCore oluşturur
    - Ana döngüyü çalıştırır
    """
    # 1) Logging konfigürasyonunu yükle
    logger = setup_logging("config/logging.yaml")
    logger.info("Starting UEM Core...")

    # 2) Çekirdek config'i yükle
    config = load_core_config("config/core.yaml")

    # 3) Test amaçlı world interface oluştur
    world = TestDummyWorld()

    # 4) UEMCore örneğini world ile birlikte oluştur
    core = UEMCore(
        config=config,
        world_interface=world,
        logger=logger
    )



    try:
        # 4) Alt sistemleri başlat
        core.initialize()

        # 5) Tick süresini config'ten al (yoksa 0.1s)
        tick_seconds = config.get("loop", {}).get("tick_seconds", 0.1)
        logger.info("Entering main loop (tick_seconds=%s)", tick_seconds)

        # 6) Ana döngü
        while True:
            core.step()
            time.sleep(tick_seconds)

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received; shutting down UEMCore.")
    except Exception:
        logger.exception("Fatal error in main loop.")
    finally:
        try:
            core.shutdown()
        except Exception:
            logger.exception("Error during UEMCore shutdown.")
        logger.info("UEM Core stopped.")


if __name__ == "__main__":
    main()
