"""
formula_detail.py
------------------
`FormulaDetailCard`: bir formülün söz dizimi, açıklaması, canlı mini
örneği ve adım adım anlatımını tek bir kart içinde gösteren, birden
fazla sayfada (Ana Sayfa önizlemesi, Konu Anlatımları, Formüller,
Fonksiyonlar) yeniden kullanılan ana widget.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.services.formula_service import FormulaService
from app.ui.widgets import MiniExampleWidget, make_difficulty_badge
from app.utils.logger import app_logger


class FormulaDetailCard(QFrame):
    """Tek bir formülün konu anlatımını gösteren kart. `favorite_toggled` ve
    `excel_requested` / `pdf_requested` sinyalleri, üst bileşenin gerçek
    servis çağrılarını yapmasını sağlar (bu widget servislere doğrudan
    bağımlı değildir, yalnızca formula_service salt-okunur sorgular için
    kullanılır)."""

    favorite_toggled = pyqtSignal(int)
    excel_requested = pyqtSignal(int)
    pdf_requested = pyqtSignal(int)

    def __init__(self, formula_service: FormulaService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.formula_service = formula_service
        self.current_formula = None
        self.setObjectName("lessonCard")
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setObjectName("lessonCardHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 12, 20, 12)
        header_label = QLabel("KONU ANLATIMI")
        header_label.setObjectName("lessonCardHeaderLabel")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        outer.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(12)

        title_row = QHBoxLayout()
        self.title_label = QLabel("Bir formül seçin")
        self.title_label.setObjectName("lessonTitle")
        title_row.addWidget(self.title_label)
        self.difficulty_badge = make_difficulty_badge("Başlangıç")
        title_row.addWidget(self.difficulty_badge)
        title_row.addStretch()
        self.favorite_button = QPushButton("☆ Favorilere Ekle")
        self.favorite_button.setObjectName("favoriteButton")
        self.favorite_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.favorite_button.clicked.connect(self._on_favorite_clicked)
        title_row.addWidget(self.favorite_button)
        layout.addLayout(title_row)

        self.description_label = QLabel()
        self.description_label.setObjectName("lessonDescription")
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)

        syntax_box = QFrame()
        syntax_box.setObjectName("syntaxBox")
        syntax_layout = QVBoxLayout(syntax_box)
        self.syntax_label = QLabel()
        self.syntax_label.setObjectName("syntaxLabel")
        self.syntax_label.setWordWrap(True)
        syntax_layout.addWidget(self.syntax_label)
        layout.addWidget(syntax_box)

        example_heading = QLabel("Canlı Örnek")
        example_heading.setObjectName("sectionHeading")
        layout.addWidget(example_heading)

        self.example_widget = MiniExampleWidget()
        layout.addWidget(self.example_widget)

        self.example_caption = QLabel()
        self.example_caption.setObjectName("captionText")
        self.example_caption.setWordWrap(True)
        layout.addWidget(self.example_caption)

        why_box = QFrame()
        why_box.setObjectName("whyBox")
        why_layout = QVBoxLayout(why_box)
        why_title = QLabel("📊  Ne İşe Yarar?")
        why_title.setObjectName("whyBoxTitle")
        why_layout.addWidget(why_title)
        self.why_label = QLabel()
        self.why_label.setObjectName("whyBoxText")
        self.why_label.setWordWrap(True)
        why_layout.addWidget(self.why_label)
        layout.addWidget(why_box)

        steps_heading = QLabel("Adım Adım")
        steps_heading.setObjectName("sectionHeading")
        steps_heading.setStyleSheet("color: #4A148C; font-size: 18px; font-weight: 800;")
        layout.addWidget(steps_heading)
        self.steps_list = QListWidget()
        self.steps_list.setObjectName("stepsList")
        self.steps_list.setFrameShape(QFrame.Shape.NoFrame)
        self.steps_list.setMaximumHeight(140)
        self.steps_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.steps_list.setStyleSheet(
            "QListWidget { background: transparent; border: none; color: #4A148C; font-size: 15px; font-weight: 800; }"
            "QListWidget::item { padding: 6px 4px; color: #4A148C; font-weight: 800; }"
        )
        self._step_font = QFont("Segoe UI", 15)
        self._step_font.setBold(True)
        self._step_color = QColor("#4A148C")
        layout.addWidget(self.steps_list)

        action_row = QHBoxLayout()
        self.show_excel_button = QPushButton("📊 Excel'de Göster")
        self.show_excel_button.setObjectName("secondaryButton")
        self.show_excel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.show_excel_button.clicked.connect(
            lambda: self.current_formula and self.excel_requested.emit(self.current_formula.id)
        )
        self.save_pdf_button = QPushButton("📄 Hızlı Kart (PDF)")
        self.save_pdf_button.setObjectName("secondaryButton")
        self.save_pdf_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_pdf_button.clicked.connect(
            lambda: self.current_formula and self.pdf_requested.emit(self.current_formula.id)
        )
        action_row.addWidget(self.show_excel_button)
        action_row.addWidget(self.save_pdf_button)
        action_row.addStretch()
        layout.addLayout(action_row)

        layout.addStretch()
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

    def show_formula(self, formula) -> None:
        self.current_formula = formula
        self.title_label.setText(f"{formula.name_tr}  ({formula.name_en})")

        new_badge = make_difficulty_badge(formula.difficulty_label)
        layout = self.difficulty_badge.parentWidget().layout()
        layout.replaceWidget(self.difficulty_badge, new_badge)
        self.difficulty_badge.deleteLater()
        self.difficulty_badge = new_badge

        self.description_label.setText(formula.short_description_tr)
        self.syntax_label.setText(formula.syntax_tr)
        self.example_widget.show_formula(formula)
        self.example_caption.setText(formula.example_description_tr)
        self.why_label.setText(formula.detailed_explanation_tr)

        self.steps_list.clear()
        for i, step in enumerate(formula.steps or [], start=1):
            item = QListWidgetItem(f"{i}.  {step}")
            item.setFont(self._step_font)
            item.setForeground(self._step_color)
            self.steps_list.addItem(item)

        self._update_favorite_button()

    def _update_favorite_button(self) -> None:
        if not self.current_formula:
            return
        is_favorite = self.formula_service.is_favorite(self.current_formula.id)
        self.favorite_button.setText("★ Favorilerden Çıkar" if is_favorite else "☆ Favorilere Ekle")

    def _on_favorite_clicked(self) -> None:
        if self.current_formula:
            self.favorite_toggled.emit(self.current_formula.id)
            self._update_favorite_button()

    def refresh_favorite_state(self) -> None:
        self._update_favorite_button()


# =========================================================================
# Paylaşılan Excel / PDF / Favori handler mixin'i
# =========================================================================
class FormulaExportMixin:
    """Birden fazla sayfada (Ana Sayfa, Konu Anlatımları, Formüller, Fonksiyonlar)
    tekrar eden Excel dışa aktarma, PDF oluşturma ve favori değiştirme
    handler'larını tek bir yerde toplar.

    Kullanım: MRO'da *solda* olmalı; örn. class Sayfa(FormulaExportMixin, QWidget).
    Bu mixin şu niteliklerin `self` üzerinde mevcut olmasını bekler:
        self.formula_service  -> FormulaService
        self.excel_service    -> ExcelService
        self.pdf_service      -> PdfService
    """

    def _on_favorite_toggled(self, formula_id: int) -> None:  # noqa: D102
        self.formula_service.toggle_favorite(formula_id)

    def _on_excel_requested(self, formula_id: int) -> None:  # noqa: D102
        formula = self.formula_service.get_formula(formula_id)
        if formula is None:
            QMessageBox.warning(self, "Bulunamadı", "Seçilen formül bulunamadı.")
            return
        try:
            path = self.excel_service.build_example_workbook(formula)
            QMessageBox.information(self, "Oluşturuldu", f"Örnek Excel dosyası oluşturuldu:\n{path}")
        except Exception as exc:  # noqa: BLE001
            app_logger.exception("Excel örneği oluşturulurken hata")
            QMessageBox.critical(self, "Hata", f"Excel dosyası oluşturulurken bir hata oluştu:\n{exc}")

    def _on_pdf_requested(self, formula_id: int) -> None:  # noqa: D102
        formula = self.formula_service.get_formula(formula_id)
        if formula is None:
            QMessageBox.warning(self, "Bulunamadı", "Seçilen formül bulunamadı.")
            return
        try:
            path = self.pdf_service.generate_quick_reference_card(formula)
            QMessageBox.information(self, "Kaydedildi", f"Hızlı referans kartı oluşturuldu:\n{path}")
        except Exception as exc:  # noqa: BLE001
            app_logger.exception("PDF kartı oluşturulurken hata")
            QMessageBox.critical(self, "Hata", f"PDF oluşturulurken bir hata oluştu:\n{exc}")
