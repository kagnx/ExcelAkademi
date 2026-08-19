"""
config.py
---------
Uygulama genelinde kullanılan ayarları, ortam değişkenlerini (.env) ve
dosya yollarını tek bir merkezden yönetir. Diğer tüm modüller ayar
bilgisine ihtiyaç duyduğunda bu modüldeki `settings` nesnesini kullanır.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Proje kök dizini: PyInstaller frozen modda _MEIPASS kullanılır
if getattr(sys, "frozen", False):
    # PyInstaller ile derlenmiş exe: veriler _MEIPASS içinde
    BASE_DIR: Path = Path(sys._MEIPASS)
else:
    # Normal Python çalıştırma: excel_master_academy_py/
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

# .env dosyasını (varsa) yükle. Dosya yoksa sessizce devam eder,
# bu durumda aşağıdaki varsayılan değerler kullanılır.
load_dotenv(BASE_DIR / ".env")


def _get_bool(name: str, default: bool) -> bool:
    """Ortam değişkenini boolean olarak okur (1/true/evet/on -> True)."""
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "evet", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass
class Paths:
    """Uygulamanın kullandığı tüm dosya/klasör yollarını tutar."""

    base_dir: Path = BASE_DIR
    app_dir: Path = BASE_DIR / "app"
    data_dir: Path = BASE_DIR / "app" / "data"
    db_path: Path = BASE_DIR / "app" / "data" / "academy.db"
    resources_dir: Path = BASE_DIR / "app" / "ui" / "resources"
    stylesheet_path: Path = BASE_DIR / "app" / "ui" / "resources" / "styles.qss"
    logs_dir: Path = BASE_DIR / "logs"
    exports_dir: Path = BASE_DIR / "exports"
    excel_exports_dir: Path = BASE_DIR / "exports" / "excel"
    pdf_exports_dir: Path = BASE_DIR / "exports" / "pdf"
    backups_dir: Path = BASE_DIR / "exports" / "backups"

    def ensure_exist(self) -> None:
        """Uygulamanın çalışması için gerekli klasörleri oluşturur."""
        for directory in (
            self.data_dir,
            self.logs_dir,
            self.exports_dir,
            self.excel_exports_dir,
            self.pdf_exports_dir,
            self.backups_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


@dataclass
class Settings:
    """Merkezi ayar nesnesi. `.env` dosyasındaki değerlerle doldurulur."""

    app_name: str = os.getenv("APP_NAME", "Excel Master Academy")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    debug: bool = field(default_factory=lambda: _get_bool("DEBUG", False))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    default_language: str = os.getenv("DEFAULT_LANGUAGE", "tr")
    quiz_default_question_count: int = field(
        default_factory=lambda: _get_int("QUIZ_QUESTION_COUNT", 10)
    )
    exercise_pass_threshold: int = field(
        default_factory=lambda: _get_int("EXERCISE_PASS_THRESHOLD", 70)
    )
    paths: Paths = field(default_factory=Paths)
    database_url: str = ""

    def __post_init__(self) -> None:
        env_url = os.getenv("DATABASE_URL", "").strip()
        if env_url:
            self.database_url = env_url
        else:
            # SQLite mutlak yol -> sqlite:////mutlak/yol/academy.db
            self.database_url = f"sqlite:///{self.paths.db_path}"


settings = Settings()
settings.paths.ensure_exist()
