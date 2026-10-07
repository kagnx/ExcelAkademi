"""
sidebar.py
----------
Sol kenar menüsü: marka başlığı, sayfa gezinme listesi, alt kısımdaki
ilerleme paneli (dairesel gösterge + 3 istatistik satırı) ve Başarılar
butonu.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config import settings
from app.services.progress_service import ProgressService
from app.ui.widgets import CircularProgress

NAV_ITEMS = [
    ("home", "🏠", "Ana Sayfa"),
    ("formulas", "𝑓x", "Formüller"),
    ("functions", "Σ", "Fonksiyonlar"),
    ("lessons", "📖", "Konu Anlatımları"),
    ("exercises", "📝", "Alıştırmalar"),
    ("quiz", "🎓", "Mini Sınavlar"),
    ("cards", "🎴", "Özet Kartlar"),
    ("tips", "💡", "Excel İpuçları"),
    ("settings", "⚙️", "Ayarlar"),
    ("about", "ℹ️", "Hakkında"),
]


class Sidebar(QWidget):
    navigate_requested = pyqtSignal(str)

    def __init__(self, progress_service: ProgressService, parent: QWidget | None = None):
        super().__init__(parent)
        self.progress_service = progress_service
        self.setObjectName("sidebar")
        self.setFixedWidth(232)
        self._build_ui()
        self.refresh_progress()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(12)

        layout.addWidget(self._build_brand())

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navList")
        self.nav_list.setFrameShape(QFrame.Shape.NoFrame)
        nav_font = QFont("Segoe UI", 15)
        nav_font.setBold(True)
        nav_pal = self.nav_list.palette()
        nav_pal.setColor(QPalette.ColorRole.WindowText, QColor("#E8D0FF"))
        nav_pal.setColor(QPalette.ColorRole.Text, QColor("#E8D0FF"))
        for _, icon, label in NAV_ITEMS:
            item = QListWidgetItem(f"   {icon}    {label}")
            item.setFont(nav_font)
            item.setForeground(QColor("#E8D0FF"))
            self.nav_list.addItem(item)
        self.nav_list.setFont(nav_font)
        self.nav_list.setPalette(nav_pal)
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._on_nav_row_changed)
        layout.addWidget(self.nav_list, 1)

        layout.addWidget(self._build_progress_panel())

        self.achievements_button = QPushButton("🏆   Başarılar   →")
        self.achievements_button.setObjectName("achievementsButton")
        self.achievements_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.achievements_button.clicked.connect(lambda: self.navigate_requested.emit("achievements"))
        margin_wrap = QWidget()
        wrap_layout = QHBoxLayout(margin_wrap)
        wrap_layout.setContentsMargins(16, 0, 16, 0)
        wrap_layout.addWidget(self.achievements_button)
        layout.addWidget(margin_wrap)

    def _build_brand(self) -> QWidget:
        brand_widget = QWidget()
        brand_layout = QHBoxLayout(brand_widget)
        brand_layout.setContentsMargins(18, 0, 14, 10)
        brand_layout.setSpacing(10)

        icon_label = QLabel("📗")
        icon_label.setObjectName("brandIcon")
        icon_label.setFixedSize(42, 42)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_layout.addWidget(icon_label)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        name_label = QLabel("Excel Formül ve\nFonksiyonları")
        name_label.setObjectName("brandTitle")
        name_label.setStyleSheet("color: #E8D0FF; font-size: 15px; font-weight: 800;")
        sub_label = QLabel("Türkçe Başucu Uygulaması")
        sub_label.setObjectName("brandSubtitle")
        sub_label.setStyleSheet("color: #E8D0FF; font-size: 12px; font-weight: 700;")
        version_label = QLabel(f"v{settings.app_version}")
        version_label.setObjectName("brandVersion")
        version_label.setStyleSheet("color: #E8D0FF; font-size: 10px; font-weight: 700;")
        text_col.addWidget(name_label)
        text_col.addWidget(sub_label)
        text_col.addWidget(version_label)
        brand_layout.addLayout(text_col, 1)

        return brand_widget

    def _build_progress_panel(self) -> QWidget:
        margin_wrap = QWidget()
        outer_layout = QVBoxLayout(margin_wrap)
        outer_layout.setContentsMargins(14, 0, 14, 0)

        frame = QFrame()
        frame.setObjectName("progressPanel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setSpacing(10)

        title = QLabel("İlerleme Durumu")
        title.setObjectName("progressPanelTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setStyleSheet("color: #E8D0FF; font-size: 14px; font-weight: 900;")
        layout.addWidget(title)

        self.circular_progress = CircularProgress(value=0, size=96, thickness=9)
        layout.addWidget(self.circular_progress, 0, Qt.AlignmentFlag.AlignHCenter)

        self.lessons_label = QLabel()
        self.exercises_label = QLabel()
        self.quiz_label = QLabel()
        for label_widget in (self.lessons_label, self.exercises_label, self.quiz_label):
            label_widget.setObjectName("progressStatLine")
            label_widget.setStyleSheet("color: #E8D0FF; font-size: 13px; font-weight: 800;")
            layout.addWidget(label_widget)

        outer_layout.addWidget(frame)
        return margin_wrap

    def _on_nav_row_changed(self, row: int) -> None:
        if 0 <= row < len(NAV_ITEMS):
            self.navigate_requested.emit(NAV_ITEMS[row][0])

    def select_page(self, key: str) -> None:
        for row, (item_key, _, _) in enumerate(NAV_ITEMS):
            if item_key == key:
                self.nav_list.blockSignals(True)
                self.nav_list.setCurrentRow(row)
                self.nav_list.blockSignals(False)
                return

    def refresh_progress(self) -> None:
        stats = self.progress_service.get_dashboard_stats()
        self.circular_progress.set_value(stats.overall_pct)
        self.lessons_label.setText(f"Konu Anlatımları      {stats.lessons_done}/{stats.lessons_total}")
        self.exercises_label.setText(f"Alıştırmalar      {stats.exercises_done}/{stats.exercises_total}")
        self.quiz_label.setText(f"Mini Sınavlar      {stats.quiz_categories_done}/{stats.quiz_categories_total}")
