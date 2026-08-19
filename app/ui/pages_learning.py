"""
pages_learning.py
------------------
Öğrenme ile doğrudan ilgili sayfalar: Formüller (ara/gözat), Fonksiyonlar
(kategoriye göre gözat), Konu Anlatımları (adım adım gezinme), Alıştırmalar,
Mini Sınavlar (başlatma ekranı + geçmiş) ve Özet Kartlar (kart tarayıcı).
"""
from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.dependency_injection import Container
from app.models.formula import Formula
from app.ui.formula_detail import FormulaDetailCard, FormulaExportMixin
from app.ui.quiz_dialog import QuizDialog


# =========================================================================
# Ortak temel sınıf: liste + detay kartı düzeni (Formüller ve Fonksiyonlar)
# =========================================================================
class _BaseListDetailPage(FormulaExportMixin, QWidget):
    navigate_requested = pyqtSignal(str)

    def __init__(self, container: Container, parent=None):
        super().__init__(parent)
        self.container = container
        self.formula_service = container.formula_service()
        self.excel_service = container.excel_service()
        self.pdf_service = container.pdf_service()
        self._current_formulas: List[Formula] = []
        self._build_base_ui()

    def _build_base_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        layout.addLayout(self._build_header())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.formula_list = QListWidget()
        self.formula_list.setObjectName("formulaListWidget")
        self.formula_list.currentRowChanged.connect(self._on_row_changed)
        splitter.addWidget(self.formula_list)

        self.detail_card = FormulaDetailCard(self.formula_service)
        self.detail_card.favorite_toggled.connect(self._on_favorite_toggled)
        self.detail_card.excel_requested.connect(self._on_excel_requested)
        self.detail_card.pdf_requested.connect(self._on_pdf_requested)
        splitter.addWidget(self.detail_card)
        splitter.setSizes([320, 700])
        layout.addWidget(splitter, 1)

    def _build_header(self):  # pragma: no cover - alt sınıflar doldurur
        raise NotImplementedError

    def _populate_list(self, formulas: List[Formula]) -> None:
        self._current_formulas = formulas
        self.formula_list.blockSignals(True)
        self.formula_list.clear()
        for formula in formulas:
            self.formula_list.addItem(f"{formula.name_tr}   —   {formula.name_en}")
        self.formula_list.blockSignals(False)
        if formulas:
            self.formula_list.setCurrentRow(0)
            self.detail_card.show_formula(formulas[0])
            self.formula_service.mark_lesson_viewed(formulas[0].id)

    def _on_row_changed(self, row: int) -> None:
        if 0 <= row < len(self._current_formulas):
            formula = self._current_formulas[row]
            self.detail_card.show_formula(formula)
            self.formula_service.mark_lesson_viewed(formula.id)


# =========================================================================
# Formüller: serbest metin arama + favoriler filtresi
# =========================================================================
class FormulasPage(_BaseListDetailPage):
    def _build_header(self):
        row = QHBoxLayout()
        title = QLabel("Formüller")
        title.setObjectName("pageTitle")
        row.addWidget(title)
        row.addStretch()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Formül ara... (örn. TOPLA, EĞER, DÜŞEYARA)")
        self.search_box.setMinimumWidth(260)
        self.search_box.textChanged.connect(self._on_search_changed)
        row.addWidget(self.search_box)

        self.favorites_toggle = QPushButton("⭐ Yalnızca Favoriler")
        self.favorites_toggle.setCheckable(True)
        self.favorites_toggle.setObjectName("toggleButton")
        self.favorites_toggle.toggled.connect(lambda _checked: self.refresh_list())
        row.addWidget(self.favorites_toggle)

        add_button = QPushButton("＋ Formül Ekle")
        add_button.setObjectName("secondaryButton")
        add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_button.clicked.connect(lambda: self.navigate_requested.emit("add_formula"))
        row.addWidget(add_button)
        return row

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.refresh_list()

    def _on_search_changed(self, _text: str) -> None:
        if self.favorites_toggle.isChecked():
            self.favorites_toggle.blockSignals(True)
            self.favorites_toggle.setChecked(False)
            self.favorites_toggle.blockSignals(False)
        self.refresh_list()

    def refresh_list(self) -> None:
        if self.favorites_toggle.isChecked():
            self._populate_list(self.formula_service.list_favorites())
            return
        query = self.search_box.text().strip()
        if query:
            self._populate_list(self.formula_service.search_formulas(query))
        else:
            self._populate_list(self.formula_service.list_formulas())


# =========================================================================
# Fonksiyonlar: kategoriye göre gözatma
# =========================================================================
class FunctionsPage(_BaseListDetailPage):
    def _build_header(self):
        row = QHBoxLayout()
        title = QLabel("Fonksiyonlar")
        title.setObjectName("pageTitle")
        row.addWidget(title)
        row.addStretch()

        row.addWidget(QLabel("Kategori:"))
        self.category_combo = QComboBox()
        self.category_combo.setMinimumWidth(240)
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        row.addWidget(self.category_combo)
        return row

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if self.category_combo.count() == 0:
            self.category_combo.blockSignals(True)
            self.category_combo.addItem("📚  Tüm Kategoriler", None)
            for category in self.formula_service.list_categories():
                self.category_combo.addItem(f"{category.icon}  {category.name_tr}", category.id)
            self.category_combo.blockSignals(False)
            self._on_category_changed(0)

    def _on_category_changed(self, _index: int) -> None:
        category_id = self.category_combo.currentData()
        self._populate_list(self.formula_service.list_formulas(category_id))


# =========================================================================
# Konu Anlatımları: tüm formüller arasında adım adım gezinme
# =========================================================================
class LessonsPage(FormulaExportMixin, QWidget):
    def __init__(self, container: Container, parent=None):
        super().__init__(parent)
        self.container = container
        self.formula_service = container.formula_service()
        self.excel_service = container.excel_service()
        self.pdf_service = container.pdf_service()
        self.all_formulas = self.formula_service.list_formulas()
        self.current_index = 0
        self._build_ui()
        if self.all_formulas:
            self._show_current()

    def showEvent(self, event) -> None:  # noqa: N802
        """Sayfa her görünür olduğunda favori durumunu tazeler."""
        super().showEvent(event)
        self.detail_card.refresh_favorite_state()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Konu Anlatımları")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()

        self.category_combo = QComboBox()
        self.category_combo.addItem("📚  Tüm Kategoriler", None)
        for category in self.formula_service.list_categories():
            self.category_combo.addItem(f"{category.icon}  {category.name_tr}", category.id)
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        header.addWidget(self.category_combo)
        layout.addLayout(header)

        self.detail_card = FormulaDetailCard(self.formula_service)
        self.detail_card.favorite_toggled.connect(lambda fid: self.formula_service.toggle_favorite(fid))
        self.detail_card.excel_requested.connect(self._on_excel_requested)
        self.detail_card.pdf_requested.connect(self._on_pdf_requested)
        layout.addWidget(self.detail_card, 1)

        nav_row = QHBoxLayout()
        self.position_label = QLabel()
        self.position_label.setObjectName("captionText")
        nav_row.addWidget(self.position_label)
        nav_row.addStretch()

        prev_button = QPushButton("←  Önceki")
        prev_button.setObjectName("navButton")
        prev_button.setCursor(Qt.CursorShape.PointingHandCursor)
        prev_button.clicked.connect(self._show_previous)
        nav_row.addWidget(prev_button)

        next_button = QPushButton("Sonraki  →")
        next_button.setObjectName("primaryButton")
        next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        next_button.clicked.connect(self._show_next)
        nav_row.addWidget(next_button)
        layout.addLayout(nav_row)

    def _on_category_changed(self, _index: int) -> None:
        category_id = self.category_combo.currentData()
        self.all_formulas = self.formula_service.list_formulas(category_id)
        self.current_index = 0
        if self.all_formulas:
            self._show_current()

    def _show_current(self) -> None:
        formula = self.all_formulas[self.current_index]
        self.detail_card.show_formula(formula)
        self.formula_service.mark_lesson_viewed(formula.id)
        self.position_label.setText(f"{self.current_index + 1} / {len(self.all_formulas)}")

    def _show_previous(self) -> None:
        if self.all_formulas:
            self.current_index = (self.current_index - 1) % len(self.all_formulas)
            self._show_current()

    def _show_next(self) -> None:
        if self.all_formulas:
            self.current_index = (self.current_index + 1) % len(self.all_formulas)
            self._show_current()


# =========================================================================
# Alıştırmalar
# =========================================================================
class ExercisesPage(QWidget):
    def __init__(self, container: Container, parent=None):
        super().__init__(parent)
        self.formula_service = container.formula_service()
        self.formulas = self.formula_service.formulas_with_exercise()
        self.current_index = 0
        self._build_ui()
        if self.formulas:
            self._show_current()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Alıştırmalar")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.list_widget = QListWidget()
        for formula in self.formulas:
            self.list_widget.addItem(f"{formula.name_tr}   —   {formula.name_en}")
        self.list_widget.currentRowChanged.connect(self._on_row_changed)
        splitter.addWidget(self.list_widget)

        right_panel = QFrame()
        right_panel.setObjectName("previewCard")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(12)

        self.formula_name_label = QLabel()
        self.formula_name_label.setObjectName("lessonTitle")
        right_layout.addWidget(self.formula_name_label)

        self.question_label = QLabel()
        self.question_label.setWordWrap(True)
        right_layout.addWidget(self.question_label)

        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("Formülünüzü buraya yazın... (örn. =TOPLA(A1:A10))")
        right_layout.addWidget(self.answer_input)

        button_row = QHBoxLayout()
        self.check_button = QPushButton("Kontrol Et")
        self.check_button.setObjectName("primaryButton")
        self.check_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.check_button.clicked.connect(self._check_answer)
        self.hint_button = QPushButton("💡 İpucu Göster")
        self.hint_button.setObjectName("secondaryButton")
        self.hint_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hint_button.clicked.connect(self._show_hint)
        button_row.addWidget(self.check_button)
        button_row.addWidget(self.hint_button)
        right_layout.addLayout(button_row)

        self.feedback_label = QLabel()
        self.feedback_label.setWordWrap(True)
        right_layout.addWidget(self.feedback_label)
        right_layout.addStretch()

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 640])
        layout.addWidget(splitter, 1)

    def _on_row_changed(self, row: int) -> None:
        if 0 <= row < len(self.formulas):
            self.current_index = row
            self._show_current()

    def _show_current(self) -> None:
        formula = self.formulas[self.current_index]
        self.formula_name_label.setText(f"{formula.name_tr}  ({formula.name_en})")
        self.question_label.setText(formula.exercise_question_tr or "")
        self.answer_input.clear()
        self.feedback_label.clear()

    def _check_answer(self) -> None:
        if not self.formulas:
            return
        formula = self.formulas[self.current_index]
        answer = self.answer_input.text()
        if not answer.strip():
            self.feedback_label.setText("Lütfen bir formül girin.")
            return
        is_correct = self.formula_service.check_exercise_answer(formula.id, answer)
        self.feedback_label.setText(
            "✅ Doğru! Harika iş çıkardınız." if is_correct else "❌ Doğru değil. Tekrar deneyin veya ipucuna bakın."
        )

    def _show_hint(self) -> None:
        if not self.formulas:
            return
        formula = self.formulas[self.current_index]
        QMessageBox.information(self, "İpucu", formula.exercise_hint_tr or "Bu alıştırma için ipucu bulunmuyor.")


# =========================================================================
# Mini Sınavlar: başlatma ekranı + geçmiş
# =========================================================================
class QuizPage(QWidget):
    def __init__(self, container: Container, parent=None):
        super().__init__(parent)
        self.container = container
        self.formula_service = container.formula_service()
        self.progress_service = container.progress_service()
        self._build_ui()
        self._refresh_history()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Mini Sınavlar")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        subtitle = QLabel("Sorular seçtiğiniz kategoriye göre formül veritabanınızdan otomatik olarak üretilir.")
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        form_frame = QFrame()
        form_frame.setObjectName("previewCard")
        form_layout = QVBoxLayout(form_frame)

        category_row = QHBoxLayout()
        category_row.addWidget(QLabel("Kategori:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("🔀  Karma (Tüm Kategoriler)", None)
        for category in self.formula_service.list_categories():
            self.category_combo.addItem(f"{category.icon}  {category.name_tr}", category.id)
        category_row.addWidget(self.category_combo, 1)
        form_layout.addLayout(category_row)

        count_row = QHBoxLayout()
        count_row.addWidget(QLabel("Soru Sayısı:"))
        self.count_spin = QSpinBox()
        self.count_spin.setRange(3, 30)
        self.count_spin.setValue(10)
        count_row.addWidget(self.count_spin)
        count_row.addStretch()
        form_layout.addLayout(count_row)

        start_button = QPushButton("Sınavı Başlat  🚀")
        start_button.setObjectName("primaryButton")
        start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        start_button.clicked.connect(self._start_quiz)
        form_layout.addWidget(start_button)
        layout.addWidget(form_frame)

        history_label = QLabel("Son Sınavlarınız")
        history_label.setObjectName("sectionHeading")
        layout.addWidget(history_label)

        self.history_list = QListWidget()
        layout.addWidget(self.history_list, 1)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._refresh_history()

    def _start_quiz(self) -> None:
        category_id = self.category_combo.currentData()
        count = self.count_spin.value()
        try:
            questions = self.formula_service.generate_quiz(category_id=category_id, question_count=count)
        except ValueError as exc:
            QMessageBox.warning(self, "Sınav Oluşturulamadı", str(exc))
            return
        dialog = QuizDialog(questions, self.formula_service, category_id, parent=self)
        dialog.exec()
        self._refresh_history()

    def _refresh_history(self) -> None:
        self.history_list.clear()
        results = self.progress_service.progress_repo.recent_quiz_results(10)
        if not results:
            self.history_list.addItem("Henüz bir sınav geçmişiniz yok, hemen başlayın!")
            return
        for result in results:
            category_name = result.category.name_tr if result.category else "Karma"
            when = result.taken_at.strftime("%d.%m.%Y %H:%M")
            self.history_list.addItem(
                f"{when}   —   {category_name}   —   {result.score}/{result.total_questions}   (%{result.percentage})"
            )


# =========================================================================
# Özet Kartlar: flashcard tarayıcı
# =========================================================================
class CardsPage(QWidget):
    def __init__(self, container: Container, parent=None):
        super().__init__(parent)
        self.formula_service = container.formula_service()
        self.formulas = self.formula_service.list_formulas()
        self.current_index = 0
        self._build_ui()
        if self.formulas:
            self._show_current()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Özet Kartlar")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()
        self.category_combo = QComboBox()
        self.category_combo.addItem("📚  Tüm Kategoriler", None)
        for category in self.formula_service.list_categories():
            self.category_combo.addItem(f"{category.icon}  {category.name_tr}", category.id)
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        header.addWidget(self.category_combo)
        layout.addLayout(header)

        self.card_frame = QFrame()
        self.card_frame.setObjectName("summaryCard")
        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(28, 26, 28, 26)
        card_layout.setSpacing(14)

        self.name_label = QLabel()
        self.name_label.setObjectName("lessonTitle")
        card_layout.addWidget(self.name_label)

        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        card_layout.addWidget(self.description_label)

        syntax_box = QFrame()
        syntax_box.setObjectName("syntaxBox")
        syntax_box_layout = QVBoxLayout(syntax_box)
        self.syntax_label = QLabel()
        self.syntax_label.setWordWrap(True)
        syntax_box_layout.addWidget(self.syntax_label)
        card_layout.addWidget(syntax_box)

        self.tip_label = QLabel()
        self.tip_label.setObjectName("whyBoxText")
        self.tip_label.setWordWrap(True)
        card_layout.addWidget(self.tip_label)
        card_layout.addStretch()

        layout.addWidget(self.card_frame, 1)

        nav_row = QHBoxLayout()
        self.position_label = QLabel()
        self.position_label.setObjectName("captionText")
        nav_row.addWidget(self.position_label)
        nav_row.addStretch()

        prev_button = QPushButton("←  Önceki")
        prev_button.setObjectName("navButton")
        prev_button.setCursor(Qt.CursorShape.PointingHandCursor)
        prev_button.clicked.connect(self._show_previous)
        nav_row.addWidget(prev_button)

        next_button = QPushButton("Sonraki  →")
        next_button.setObjectName("primaryButton")
        next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        next_button.clicked.connect(self._show_next)
        nav_row.addWidget(next_button)
        layout.addLayout(nav_row)

    def _on_category_changed(self, _index: int) -> None:
        category_id = self.category_combo.currentData()
        self.formulas = self.formula_service.list_formulas(category_id)
        self.current_index = 0
        if self.formulas:
            self._show_current()

    def _show_current(self) -> None:
        formula = self.formulas[self.current_index]
        self.name_label.setText(f"{formula.name_tr}  ({formula.name_en})")
        self.description_label.setText(formula.short_description_tr)
        self.syntax_label.setText(formula.syntax_tr)
        tip = formula.exercise_hint_tr or formula.example_description_tr
        self.tip_label.setText(f"⭐  İpucu: {tip}")
        self.position_label.setText(f"{self.current_index + 1} / {len(self.formulas)}")
        self.formula_service.mark_card_viewed(formula.id)

    def _show_previous(self) -> None:
        if self.formulas:
            self.current_index = (self.current_index - 1) % len(self.formulas)
            self._show_current()

    def _show_next(self) -> None:
        if self.formulas:
            self.current_index = (self.current_index + 1) % len(self.formulas)
            self._show_current()
