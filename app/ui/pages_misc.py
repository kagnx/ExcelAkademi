"""
pages_misc.py
-------------
Diğer destekleyici sayfalar: Excel İpuçları (genel ipuçları listesi),
Ayarlar (dışa aktarma / yedekleme / uygulama bilgisi), Hakkında ve
Başarılar (rozetler + günlük seri özeti).
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.config import settings
from app.dependency_injection import Container
from app.utils.logger import app_logger


# =========================================================================
# Excel İpuçları
# =========================================================================
class TipsPage(QWidget):
    def __init__(self, container: Container, parent=None):
        super().__init__(parent)
        self.tip_repository = container.tip_repository()
        self._build_ui()
        self._load_tips()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Excel İpuçları")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        subtitle = QLabel("Klavye kısayolları ve verimliliğinizi artıracak pratik ipuçları.")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self.scroll_area, 1)

    def _load_tips(self) -> None:
        tips = self.tip_repository.get_all_sorted()
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(12)

        groups: dict[str, list] = {}
        for tip in tips:
            groups.setdefault(tip.group_tr or "Genel", []).append(tip)

        for group_name, group_tips in groups.items():
            group_label = QLabel(group_name)
            group_label.setObjectName("sectionHeading")
            content_layout.addWidget(group_label)
            for tip in group_tips:
                content_layout.addWidget(self._build_tip_card(tip))

        content_layout.addStretch()
        self.scroll_area.setWidget(content)

    def _build_tip_card(self, tip) -> QFrame:
        frame = QFrame()
        frame.setObjectName("previewCard")
        layout = QHBoxLayout(frame)
        layout.setSpacing(14)

        icon_label = QLabel(tip.icon or "💡")
        icon_label.setStyleSheet("font-size: 24px;")
        icon_label.setFixedWidth(36)
        layout.addWidget(icon_label)

        text_col = QVBoxLayout()
        title_label = QLabel(tip.title_tr)
        title_label.setObjectName("previewCardName")
        text_col.addWidget(title_label)
        content_label = QLabel(tip.content_tr)
        content_label.setWordWrap(True)
        text_col.addWidget(content_label)
        layout.addLayout(text_col, 1)
        return frame


# =========================================================================
# Ayarlar
# =========================================================================
class SettingsPage(QWidget):
    def __init__(self, container: Container, parent=None):
        super().__init__(parent)
        self.container = container
        self.formula_service = container.formula_service()
        self.progress_service = container.progress_service()
        self.excel_service = container.excel_service()
        self.pdf_service = container.pdf_service()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Ayarlar")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        layout.addWidget(self._build_export_section())
        layout.addWidget(self._build_database_section())
        layout.addWidget(self._build_info_section())
        layout.addStretch()

    def _build_export_section(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("previewCard")
        layout = QVBoxLayout(frame)
        layout.setSpacing(10)

        heading = QLabel("Dışa Aktarma")
        heading.setObjectName("sectionHeading")
        layout.addWidget(heading)

        export_excel_button = QPushButton("📊  Tüm Formülleri Excel'e Aktar")
        export_excel_button.setObjectName("secondaryButton")
        export_excel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        export_excel_button.clicked.connect(self._export_excel)
        layout.addWidget(export_excel_button)

        export_pdf_button = QPushButton("📄  Formül Kılavuzunu PDF Olarak Kaydet")
        export_pdf_button.setObjectName("secondaryButton")
        export_pdf_button.setCursor(Qt.CursorShape.PointingHandCursor)
        export_pdf_button.clicked.connect(self._export_pdf)
        layout.addWidget(export_pdf_button)
        return frame

    def _build_database_section(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("previewCard")
        layout = QVBoxLayout(frame)
        layout.setSpacing(10)

        heading = QLabel("Veritabanı")
        heading.setObjectName("sectionHeading")
        layout.addWidget(heading)

        backup_button = QPushButton("💾  Veritabanını Yedekle")
        backup_button.setObjectName("secondaryButton")
        backup_button.setCursor(Qt.CursorShape.PointingHandCursor)
        backup_button.clicked.connect(self._backup_database)
        layout.addWidget(backup_button)

        note = QLabel(
            "Yedekler, uygulama klasörünüzdeki 'backups' dizinine zaman damgasıyla kaydedilir. "
            "Veritabanını sıfırlamak isterseniz, uygulamayı terminalden --reset-db seçeneğiyle çalıştırabilirsiniz."
        )
        note.setObjectName("captionText")
        note.setWordWrap(True)
        layout.addWidget(note)
        return frame

    def _build_info_section(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("previewCard")
        layout = QVBoxLayout(frame)
        layout.setSpacing(6)

        heading = QLabel("Uygulama Bilgisi")
        heading.setObjectName("sectionHeading")
        layout.addWidget(heading)

        layout.addWidget(QLabel(f"Sürüm: {settings.app_version}"))
        layout.addWidget(QLabel(f"Toplam formül sayısı: {self.formula_service.total_formula_count()}"))
        layout.addWidget(QLabel(f"Kategori sayısı: {len(self.formula_service.list_categories())}"))

        db_path_label = QLabel(f"Veritabanı konumu: {settings.paths.db_path}")
        db_path_label.setObjectName("captionText")
        db_path_label.setWordWrap(True)
        layout.addWidget(db_path_label)
        return frame

    def _export_excel(self) -> None:
        try:
            formulas = self.formula_service.list_formulas()
            path = self.excel_service.export_all_formulas(formulas)
            QMessageBox.information(self, "Aktarıldı", f"Tüm formüller şu dosyaya aktarıldı:\n{path}")
        except Exception as exc:  # noqa: BLE001
            app_logger.exception("Excel'e toplu aktarım sırasında hata")
            QMessageBox.critical(self, "Hata", f"Excel'e aktarma sırasında bir hata oluştu:\n{exc}")

    def _export_pdf(self) -> None:
        try:
            formulas = self.formula_service.list_formulas()
            path = self.pdf_service.generate_cheatsheet_pdf(formulas, title=settings.app_name)
            QMessageBox.information(self, "Kaydedildi", f"PDF kılavuz oluşturuldu:\n{path}")
        except Exception as exc:  # noqa: BLE001
            app_logger.exception("PDF kılavuzu oluşturulurken hata")
            QMessageBox.critical(self, "Hata", f"PDF oluşturulurken bir hata oluştu:\n{exc}")

    def _backup_database(self) -> None:
        try:
            path = self.progress_service.backup_database()
            QMessageBox.information(self, "Yedeklendi", f"Veritabanı şu konuma yedeklendi:\n{path}")
        except Exception as exc:  # noqa: BLE001
            app_logger.exception("Veritabanı yedekleme sırasında hata")
            QMessageBox.critical(self, "Hata", f"Yedekleme sırasında bir hata oluştu:\n{exc}")


# =========================================================================
# Hakkında
# =========================================================================
class AboutPage(QWidget):
    def __init__(self, container: Container, parent=None):
        super().__init__(parent)
        self.formula_service = container.formula_service()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 40, 24, 24)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        icon = QLabel("📗")
        icon.setStyleSheet("font-size: 52px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        title = QLabel(settings.app_name)
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        version = QLabel(f"Sürüm {settings.app_version}")
        version.setObjectName("captionText")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        description = QLabel(
            "Excel formüllerini ve fonksiyonlarını Türkçe öğrenmek için hazırlanmış, "
            "internet bağlantısı gerektirmeyen bir başucu uygulamasıdır."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setMaximumWidth(480)
        layout.addWidget(description, 0, Qt.AlignmentFlag.AlignHCenter)

        stats_row = QHBoxLayout()
        stats_row.addStretch()
        stats_row.addWidget(QLabel(f"📚 {self.formula_service.total_formula_count()} formül"))
        stats_row.addWidget(QLabel(f"🗂️ {len(self.formula_service.list_categories())} kategori"))
        stats_row.addStretch()
        layout.addLayout(stats_row)

        tech_label = QLabel(
            "Python, PyQt6, SQLAlchemy, Pydantic, OpenPyXL, ReportLab, FPDF2, Loguru ve "
            "Dependency Injector ile geliştirilmiştir."
        )
        tech_label.setObjectName("captionText")
        tech_label.setWordWrap(True)
        tech_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tech_label.setMaximumWidth(480)
        layout.addWidget(tech_label, 0, Qt.AlignmentFlag.AlignHCenter)

        layout.addStretch()


# =========================================================================
# Başarılar
# =========================================================================
class AchievementsPage(QWidget):
    def __init__(self, container: Container, parent=None):
        super().__init__(parent)
        self.progress_service = container.progress_service()
        self._build_ui()
        self._load_achievements()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(12)

        title = QLabel("🏆  Başarılar")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self.summary_label = QLabel()
        self.summary_label.setObjectName("pageSubtitle")
        layout.addWidget(self.summary_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self.scroll_area, 1)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._load_achievements()

    def _load_achievements(self) -> None:
        achievements = self.progress_service.get_achievements()
        unlocked_count = sum(1 for a in achievements if a.unlocked)
        current_streak, longest_streak = self.progress_service.get_streak()
        self.summary_label.setText(
            f"{unlocked_count} / {len(achievements)} rozet kazanıldı   •   "
            f"🔥 Güncel seri: {current_streak} gün   •   En uzun seri: {longest_streak} gün"
        )

        content = QWidget()
        grid = QGridLayout(content)
        grid.setSpacing(14)
        columns = 3
        for index, achievement in enumerate(achievements):
            card = self._build_achievement_card(achievement)
            grid.addWidget(card, index // columns, index % columns)
        self.scroll_area.setWidget(content)

    def _build_achievement_card(self, achievement) -> QFrame:
        frame = QFrame()
        frame.setObjectName("achievementCard" if achievement.unlocked else "achievementCardLocked")
        layout = QVBoxLayout(frame)
        layout.setSpacing(6)

        icon_label = QLabel(achievement.icon if achievement.unlocked else "🔒")
        icon_label.setStyleSheet("font-size: 30px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        title_label = QLabel(achievement.title)
        title_label.setObjectName("previewCardName")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        desc_label = QLabel(achievement.description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        return frame
