"""
main.py
-------
Excel Usta Akademisi uygulamasının giriş noktası.

Kullanım:
    python -m app.main                # Normal başlatma
    python -m app.main --reset-db     # Veritabanını silip sıfırdan oluşturur
"""
from __future__ import annotations

import argparse
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from app.config import settings
from app.dependency_injection import Container, initialize_database
from app.ui.main_window import MainWindow
from app.utils.logger import app_logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=settings.app_name)
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Mevcut veritabanını siler ve tohum verisiyle sıfırdan oluşturur.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.reset_db and settings.paths.db_path.exists():
        settings.paths.db_path.unlink()
        app_logger.info("Veritabanı silindi; yeniden oluşturulacak.")

    container = Container()
    initialize_database(container)

    progress_service = container.progress_service()
    progress_service.update_streak_on_launch()

    app = QApplication(sys.argv)
    app.setApplicationName(settings.app_name)
    app.setApplicationVersion(settings.app_version)
    app.setStyle("Fusion")

    # Uygulama ikonunu ayarla
    icon_path = str(settings.paths.base_dir / "app" / "ui" / "resources" / "app_icon.ico")
    app.setWindowIcon(QIcon(icon_path))

    window = MainWindow(container)
    window.show()

    app_logger.info(f"{settings.app_name} penceresi açıldı.")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
