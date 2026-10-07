"""
title_bar.py
------------
Çerçevesiz (frameless) ana pencere için özel başlık çubuğu. Pencereyi
sürükleyerek taşımak ve büyütmek/geri yüklemek için Qt6'nın yerel
`startSystemMove` / `showMaximized` mekanizmalarını kullanır; bu sayede
platforma özgü piksel matematiği yazmaya gerek kalmaz.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMouseEvent, QPixmap
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.config import settings


class TitleBar(QWidget):
    def __init__(self, parent_window: QWidget):
        super().__init__(parent_window)
        self._window = parent_window
        self.setObjectName("titleBar")
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 8, 0)
        layout.setSpacing(10)

        # İkon (gerçek .ico dosyasından)
        icon_label = QLabel()
        icon_label.setObjectName("titleBarIcon")
        pixmap = QPixmap(str(settings.paths.base_dir / "app" / "ui" / "resources" / "app_icon.ico"))
        if not pixmap.isNull():
            icon_label.setPixmap(pixmap.scaled(22, 22, Qt.AspectRatioMode.KeepAspectRatio,
                                               Qt.TransformationMode.SmoothTransformation))
        else:
            icon_label.setText("📗")
        icon_label.setFixedSize(26, 26)
        layout.addWidget(icon_label)

        # Başlık + alt başlık (dikey)
        title_text_layout = QVBoxLayout()
        title_text_layout.setSpacing(0)
        title_text_layout.setContentsMargins(0, 2, 0, 2)

        title_label = QLabel(settings.app_name)
        title_label.setObjectName("titleBarText")
        title_text_layout.addWidget(title_label)

        version_label = QLabel(f"v{settings.app_version}  •  {len(self._window.formula_service.list_formulas())} formül")
        version_label.setObjectName("titleBarVersion")
        title_text_layout.addWidget(version_label)

        layout.addLayout(title_text_layout)

        layout.addStretch()

        self.minimize_button = self._make_button("_", "Tepsiye Kucult")
        self.minimize_button.clicked.connect(self._window.minimize_to_tray)
        layout.addWidget(self.minimize_button)

        self.fullscreen_button = self._make_button("[]", "Tam Ekran (F11)")
        self.fullscreen_button.clicked.connect(self._window.toggle_fullscreen)
        layout.addWidget(self.fullscreen_button)

        self.maximize_button = self._make_button("[ ]", "Buyut/Geri Yukle")
        self.maximize_button.clicked.connect(self._toggle_maximize)
        layout.addWidget(self.maximize_button)

        self.close_button = self._make_button("X", "Kapat")
        self.close_button.setObjectName("closeButton")
        self.close_button.clicked.connect(self._window.close)
        layout.addWidget(self.close_button)

    def _make_button(self, text: str, tooltip: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("titleBarButton")
        button.setToolTip(tooltip)
        button.setFixedSize(42, 34)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_font = QFont("Segoe UI", 14)
        btn_font.setBold(True)
        button.setFont(btn_font)
        button.setStyleSheet(
            "QPushButton { background-color: #BA68C8; color: #FFFFFF; border: 2px solid #CE93D8; border-radius: 6px; font-size: 17px; font-weight: 900; }"
            "QPushButton:hover { background-color: #CE93D8; }"
        )
        return button

    def _toggle_maximize(self) -> None:
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()

    # ---- Sürükleyerek taşıma ----
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._window.windowHandle():
            self._window.windowHandle().startSystemMove()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
        super().mouseDoubleClickEvent(event)
