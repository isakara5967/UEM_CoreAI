import logging
import logging.config
from pathlib import Path
from typing import Optional

import yaml


def setup_logging(config_path: str = "config/logging.yaml") -> logging.Logger:
    """
    logging.yaml dosyasını yükler ve logging'i konfigüre eder.
    Dosya bulunamaz veya hata olursa basicConfig ile devam eder.

    Returns:
        'core' isimli logger (yoksa root logger).
    """
    config_file = Path(config_path)

    if config_file.is_file():
        try:
            with config_file.open("r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logging.config.dictConfig(config)
        except Exception as e:
            # Konfigürasyon başarısız; basicConfig'e düş
            logging.basicConfig(
                level=logging.INFO,
                format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            )
            logging.getLogger(__name__).exception(
                "Failed to load logging config from %s: %s",
                config_path,
                e,
            )
    else:
        # Dosya yoksa basicConfig
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        )
        logging.getLogger(__name__).warning(
            "Logging config file %s not found, using basicConfig.", config_path
        )

    logger = logging.getLogger("core")
    return logger if logger.handlers else logging.getLogger()
