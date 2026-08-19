"""
main_window.py
---------------
Uygulamanın ana penceresi. Çerçevesiz (frameless) pencere + özel başlık
çubuğu + kenar menüsü + sayfalar arası geçişi yöneten QStackedWidget'ı
bir araya getirir. Kenarlardan sürükleyerek yeniden boyutlandırma,
Qt6'nın yerel `startSystemResize` mekanizmasıyla, ince (5px) bir kenar
boşluğu üzerinden desteklenir.
"""
from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QIcon, QMouseEvent, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QStackedWidget,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from app.config import settings
from app.dependency_injection import Container
from app.models.formula import Formula
from app.ui.pages_dashboard import HomePage
from app.ui.pages_learning import (
    CardsPage,
    ExercisesPage,
    FormulasPage,
    FunctionsPage,
    LessonsPage,
    QuizPage,
)
from app.ui.pages_misc import AboutPage, AchievementsPage, SettingsPage, TipsPage
from app.ui.sidebar import Sidebar
from app.ui.title_bar import TitleBar
from app.utils.logger import app_logger

RESIZE_MARGIN = 5


class _ResizableRoot(QWidget):
    """Ana pencerenin merkez widget'ı. Kenarlarındaki ince şerit üzerinden
    fare ile sürüklenerek pencere boyutunun değiştirilmesini sağlar."""

    def __init__(self, window: QWidget):
        super().__init__()
        self._window = window
        self.setObjectName("appRoot")
        self.setMouseTracking(True)

    def _edge_at(self, pos: QPoint):
        if self._window.isMaximized():
            return None
        x, y, w, h = pos.x(), pos.y(), self.width(), self.height()
        margin = RESIZE_MARGIN + 2
        edge = Qt.Edge(0)
        if y <= margin:
            edge |= Qt.Edge.TopEdge
        if y >= h - margin:
            edge |= Qt.Edge.BottomEdge
        if x <= margin:
            edge |= Qt.Edge.LeftEdge
        if x >= w - margin:
            edge |= Qt.Edge.RightEdge
        return edge if edge != Qt.Edge(0) else None

    def _cursor_for_edge(self, edge) -> Qt.CursorShape:
        has_top = bool(edge & Qt.Edge.TopEdge)
        has_bottom = bool(edge & Qt.Edge.BottomEdge)
        has_left = bool(edge & Qt.Edge.LeftEdge)
        has_right = bool(edge & Qt.Edge.RightEdge)
        if (has_top and has_left) or (has_bottom and has_right):
            return Qt.CursorShape.SizeFDiagCursor
        if (has_top and has_right) or (has_bottom and has_left):
            return Qt.CursorShape.SizeBDiagCursor
        if has_top or has_bottom:
            return Qt.CursorShape.SizeVerCursor
        return Qt.CursorShape.SizeHorCursor

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        edge = self._edge_at(event.position().toPoint())
        self.setCursor(self._cursor_for_edge(edge)) if edge else self.unsetCursor()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._edge_at(event.position().toPoint())
            window_handle = self._window.windowHandle()
            if edge and window_handle:
                window_handle.startSystemResize(edge)
                event.accept()
                return
        super().mousePressEvent(event)


class MainWindow(QWidget):
    def __init__(self, container: Container):
        super().__init__()
        self.container = container
        self.formula_service = container.formula_service()
        self.progress_service = container.progress_service()
        self.validation_service = container.validation_service()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle(settings.app_name)
        self.setMinimumSize(1180, 720)
        self.resize(1360, 840)
        self._is_fullscreen = False

        self._load_stylesheet()
        self._build_ui()
        self._setup_system_tray()

    # ------------------------------------------------------------------
    # Sistem Tepsisi (System Tray)
    # ------------------------------------------------------------------
    def _setup_system_tray(self) -> None:
        """Sistem tepsisi ikonu oluşturur. Küçültme düğmesi tepsine küçültür."""
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = str(settings.paths.base_dir / "app" / "ui" / "resources" / "app_icon.ico")
        self.tray_icon.setIcon(QIcon(icon_path))
        self.tray_icon.setToolTip(settings.app_name)

        # Tepsi menüsü
        tray_menu = self.tray_icon.activated.connect(self._on_tray_activated)

        self.tray_icon.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Tepsi ikonuna çift tıklandığında pencereyi göster."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()
            self.activateWindow()

    def minimize_to_tray(self) -> None:
        """Pencereyi sistem tepsisine küçült."""
        self.hide()
        self.tray_icon.showMessage(
            settings.app_name,
            "Uygulama arka planda çalışıyor.",
            QSystemTrayIcon.MessageIcon.Information,
            1500,
        )

    # ------------------------------------------------------------------
    # Tam Ekran
    # ------------------------------------------------------------------
    def toggle_fullscreen(self) -> None:
        """Tam ekran modunu aç/kapat."""
        if self._is_fullscreen:
            self.showNormal()
            self._is_fullscreen = False
        else:
            self.showFullScreen()
            self._is_fullscreen = True

    def keyPressEvent(self, event) -> None:  # noqa: N802
        """Klavye kısayollarını yönetir."""
        if event.key() == Qt.Key.Key_F11:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key.Key_Escape and self._is_fullscreen:
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)

    def _load_stylesheet(self) -> None:
        qss_path = settings.paths.stylesheet_path
        if qss_path.exists():
            self.setStyleSheet(qss_path.read_text(encoding="utf-8"))
        else:
            app_logger.warning(f"Stil dosyası bulunamadı: {qss_path}")

    def _build_ui(self) -> None:
        root = _ResizableRoot(self)
        margin_layout = QVBoxLayout(self)
        margin_layout.setContentsMargins(RESIZE_MARGIN, RESIZE_MARGIN, RESIZE_MARGIN, RESIZE_MARGIN)
        margin_layout.setSpacing(0)
        margin_layout.addWidget(root)

        outer_layout = QVBoxLayout(root)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.title_bar = TitleBar(self)
        outer_layout.addWidget(self.title_bar)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = Sidebar(self.progress_service)
        self.sidebar.navigate_requested.connect(self.navigate_to)
        body_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        body_layout.addWidget(self.stack, 1)

        outer_layout.addWidget(body, 1)

        self._build_pages()
        self.navigate_to("home")

    def _build_pages(self) -> None:
        self.pages: dict[str, QWidget] = {}

        self.home_page = HomePage(self.container)
        self.home_page.navigate_requested.connect(self.navigate_to)
        self.home_page.progress_changed.connect(self._on_progress_changed)
        self._register_page("home", self.home_page)

        self.formulas_page = FormulasPage(self.container)
        self.formulas_page.navigate_requested.connect(self.navigate_to)
        self._register_page("formulas", self.formulas_page)

        self._register_page("functions", FunctionsPage(self.container))
        self._register_page("lessons", LessonsPage(self.container))
        self._register_page("exercises", ExercisesPage(self.container))
        self._register_page("quiz", QuizPage(self.container))
        self._register_page("cards", CardsPage(self.container))
        self._register_page("tips", TipsPage(self.container))
        self._register_page("settings", SettingsPage(self.container))
        self._register_page("about", AboutPage(self.container))
        self._register_page("achievements", AchievementsPage(self.container))

    def _register_page(self, key: str, widget: QWidget) -> None:
        self.pages[key] = widget
        self.stack.addWidget(widget)

    def navigate_to(self, key: str) -> None:
        if key == "add_formula":
            self._open_add_formula_dialog()
            return
        if key in self.pages:
            self.stack.setCurrentWidget(self.pages[key])
            self.sidebar.select_page(key)

    def _on_progress_changed(self) -> None:
        self.sidebar.refresh_progress()

    def _refresh_after_formula_change(self) -> None:
        """Formül eklendikten/silindikten sonra Visible tüm sayfaları ve
        Sidebar'ı tazeler. Yeni formülün Sidebar istatistiklerinde, Ana Sayfa
        kartlarında ve Formüller listesinde hemen görünmesini sağlar."""
        self.sidebar.refresh_progress()
        self.home_page.refresh()
        self.formulas_page.refresh_list()

    # ------------------------------------------------------------------
    # Yeni Formül Ekle (ValidationService kullanan basit CRUD diyaloğu)
    # ------------------------------------------------------------------
    def _open_add_formula_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Yeni Formül Ekle")
        dialog.resize(460, 480)
        layout = QFormLayout(dialog)

        name_tr_input = QLineEdit()
        name_en_input = QLineEdit()
        category_combo = QComboBox()
        for category in self.formula_service.list_categories():
            category_combo.addItem(f"{category.icon}  {category.name_tr}", category.id)
        syntax_input = QLineEdit()
        short_desc_input = QLineEdit()
        detailed_input = QTextEdit()
        detailed_input.setFixedHeight(80)
        example_formula_input = QLineEdit()
        example_desc_input = QLineEdit()

        layout.addRow("Türkçe Ad:", name_tr_input)
        layout.addRow("İngilizce Ad:", name_en_input)
        layout.addRow("Kategori:", category_combo)
        layout.addRow("Söz Dizimi:", syntax_input)
        layout.addRow("Kısa Açıklama:", short_desc_input)
        layout.addRow("Detaylı Açıklama:", detailed_input)
        layout.addRow("Örnek Formül:", example_formula_input)
        layout.addRow("Örnek Açıklaması:", example_desc_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addRow(buttons)

        def on_save() -> None:
            data = {
                "name_tr": name_tr_input.text(),
                "name_en": name_en_input.text(),
                "category_id": category_combo.currentData(),
                "syntax_tr": syntax_input.text(),
                "short_description_tr": short_desc_input.text(),
                "detailed_explanation_tr": detailed_input.toPlainText(),
                "example_formula": example_formula_input.text(),
                "example_description_tr": example_desc_input.text(),
            }
            is_valid, model, errors = self.validation_service.validate_formula_input(data)
            if not is_valid:
                QMessageBox.warning(dialog, "Geçersiz Veri", "\n".join(errors))
                return

            self.formula_service.add_custom_formula(model.model_dump())
            QMessageBox.information(dialog, "Eklendi", f"'{model.name_tr}' formülü eklendi.")
            dialog.accept()
            self._refresh_after_formula_change()

        buttons.accepted.connect(on_save)
        buttons.rejected.connect(dialog.reject)
        dialog.exec()
