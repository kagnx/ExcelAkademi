"""
logger.py
---------
Loguru tabanlı merkezi loglama yapılandırması. Uygulamanın her yerinde
`from app.utils.logger import app_logger` ile aynı, önceden yapılandırılmış
logger nesnesi kullanılır.

- Konsola renkli, özet log satırları basılır (INFO ve üzeri, .env'den ayarlanabilir).
- `logs/app.log` dosyasına daha ayrıntılı (DEBUG) loglar, otomatik
  döndürme (rotation) ve saklama (retention) politikasıyla yazılır.
"""
from __future__ import annotations

import sys

from loguru import logger

from app.config import settings

_LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def _configure() -> "logger":
    logger.remove()  # Varsayılan handler'ı kaldır (çift log basmayı önler)

    # PyInstaller console=False modunda sys.stderr None olur,
    # bu yüzden kontrol edip ekliyoruz.
    if sys.stderr is not None:
        logger.add(
            sys.stderr,
            level=settings.log_level,
            format=_LOG_FORMAT,
            colorize=True,
            backtrace=False,
            diagnose=settings.debug,
        )

    log_file = settings.paths.logs_dir / "app.log"
    logger.add(
        log_file,
        level="DEBUG",
        format=_LOG_FORMAT,
        rotation="5 MB",
        retention=5,
        encoding="utf-8",
        enqueue=True,  # Thread-safe yazım (PyQt sinyal/slot çağrılarında güvenli)
        backtrace=True,
        diagnose=settings.debug,
    )

    logger.info(f"{settings.app_name} v{settings.app_version} başlatılıyor...")
    logger.debug(f"Log dosyası: {log_file}")
    return logger


app_logger = _configure()
