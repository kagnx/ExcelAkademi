"""
pages_dashboard.py
-------------------
Ana Sayfa: hoş geldin başlığı + günlük seri rozeti, 4'lü istatistik
kartları, o anki formülün konu anlatımı önizlemesi (ileri/geri gezinme
ile) ve alıştırma / mini sınav / özet kart önizleme kartları.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.dependency_injection import Container
from app.ui.formula_detail import FormulaDetailCard, FormulaExportMixin
from app.ui.quiz_dialog import QuizDialog
from app.ui.widgets import StatCard

MAX_DOTS = 5


class HomePage(FormulaExportMixin, QWidget):
    navigate_requested = pyqtSignal(str)
    progress_changed = pyqtSignal()

    def __init__(self, container: Container, parent=None):
        super().__init__(parent)
        self.container = container
        self.formula_service = container.formula_service()
        self.progress_service = container.progress_service()
        self.excel_service = container.excel_service()
        self.pdf_service = container.pdf_service()

        self.all_formulas = self.formula_service.list_formulas()
        self.current_index = self._find_starting_index()
        self.stat_card_widgets = []

        self._build_ui()
        self._show_current_formula()

    # ------------------------------------------------------------------
    def _find_starting_index(self) -> int:
        for i, formula in enumerate(self.all_formulas):
            if not self.progress_service.progress_repo.get_or_create(formula.id).lesson_viewed:
                return i
        return 0

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer_layout.addWidget(scroll)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        layout.addLayout(self._build_welcome_row())

        self.stats_row = QHBoxLayout()
        self.stats_row.setSpacing(14)
        layout.addLayout(self.stats_row)
        self._populate_stat_cards()

        self.lesson_card = FormulaDetailCard(self.formula_service)
        self.lesson_card.favorite_toggled.connect(self._on_favorite_toggled)
        self.lesson_card.excel_requested.connect(self._on_excel_requested)
        self.lesson_card.pdf_requested.connect(self._on_pdf_requested)
        self.lesson_card.setMinimumHeight(420)
        layout.addWidget(self.lesson_card)

        layout.addWidget(self._build_lesson_nav())
        layout.addLayout(self._build_preview_row())
        layout.addStretch()

        scroll.setWidget(content)

    def showEvent(self, event) -> None:  # noqa: N802
        """Sayfa her görünür olduğunda favori durumunu tazeler."""
        super().showEvent(event)
        self.lesson_card.refresh_favorite_state()

    def _build_welcome_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        text_col = QVBoxLayout()
        title = QLabel("Hoş geldiniz!")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Excel formüllerini ve fonksiyonlarını birlikte öğrenelim.")
        subtitle.setObjectName("pageSubtitle")
        text_col.addWidget(title)
        text_col.addWidget(subtitle)
        row.addLayout(text_col)
        row.addStretch()

        current_streak, _ = self.progress_service.get_streak()
        streak_badge = QFrame()
        streak_badge.setObjectName("streakBadge")
        streak_layout = QHBoxLayout(streak_badge)
        streak_layout.setContentsMargins(14, 8, 14, 8)
        fire = QLabel("🔥")
        count_col = QVBoxLayout()
        count_col.setSpacing(0)
        count_label = QLabel(str(current_streak))
        count_label.setObjectName("streakCount")
        day_label = QLabel("Günlük Seri")
        day_label.setObjectName("streakLabel")
        count_col.addWidget(count_label)
        count_col.addWidget(day_label)
        streak_layout.addWidget(fire)
        streak_layout.addLayout(count_col)
        row.addWidget(streak_badge)

        continue_button = QPushButton("Planıma Devam Et")
        continue_button.setObjectName("primaryButton")
        continue_button.setCursor(Qt.CursorShape.PointingHandCursor)
        continue_button.clicked.connect(lambda: self.navigate_requested.emit("lessons"))
        row.addWidget(continue_button)
        return row

    def _populate_stat_cards(self) -> None:
        while self.stats_row.count():
            item = self.stats_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.stat_card_widgets = []

        stats = self.progress_service.get_dashboard_stats()
        data = [
            ("📘", "Konu Anlatımları", stats.lessons_done, stats.lessons_total, "#107C41"),
            ("📝", "Alıştırmalar", stats.exercises_done, stats.exercises_total, "#2B7DE9"),
            ("🎓", "Mini Sınavlar", stats.quiz_categories_done, stats.quiz_categories_total, "#8B5CF6"),
            ("🎴", "Özet Kartlar", stats.cards_done, stats.cards_total, "#F59E0B"),
        ]
        for icon, title, done, total, color in data:
            card = StatCard(icon, title, done, total, color)
            self.stat_card_widgets.append(card)
            self.stats_row.addWidget(card)

    def _build_lesson_nav(self) -> QWidget:
        wrap = QWidget()
        row = QHBoxLayout(wrap)
        row.setContentsMargins(0, 0, 0, 0)

        self.prev_button = QPushButton("←  Önceki")
        self.prev_button.setObjectName("navButton")
        self.prev_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_button.clicked.connect(self._show_previous)
        row.addWidget(self.prev_button)

        row.addStretch()
        self.dots_layout = QHBoxLayout()
        self.dots_layout.setSpacing(6)
        row.addLayout(self.dots_layout)
        row.addStretch()

        self.next_button = QPushButton("Sonraki  →")
        self.next_button.setObjectName("primaryButton")
        self.next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_button.clicked.connect(self._show_next)
        row.addWidget(self.next_button)
        return wrap

    def _build_preview_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(14)
        row.addWidget(self._build_exercise_preview())
        row.addWidget(self._build_quiz_preview())
        row.addWidget(self._build_card_preview())
        return row

    def _build_exercise_preview(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("previewCard")
        layout = QVBoxLayout(frame)
        header = QLabel("📝  Alıştırma")
        header.setObjectName("previewCardHeader")
        layout.addWidget(header)

        self.exercise_question_label = QLabel()
        self.exercise_question_label.setWordWrap(True)
        layout.addWidget(self.exercise_question_label)

        input_row = QHBoxLayout()
        self.exercise_input = QLineEdit()
        self.exercise_input.setPlaceholderText("Sonucu yazın...")
        input_row.addWidget(self.exercise_input)
        layout.addLayout(input_row)

        self.exercise_check_button = QPushButton("Kontrol Et")
        self.exercise_check_button.setObjectName("primaryButton")
        self.exercise_check_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.exercise_check_button.clicked.connect(self._check_exercise)
        layout.addWidget(self.exercise_check_button)

        self.exercise_feedback_label = QLabel()
        self.exercise_feedback_label.setWordWrap(True)
        layout.addWidget(self.exercise_feedback_label)
        layout.addStretch()
        return frame

    def _build_quiz_preview(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("previewCard")
        layout = QVBoxLayout(frame)
        header = QLabel("🎓  Mini Sınav")
        header.setObjectName("previewCardHeader")
        layout.addWidget(header)

        text = QLabel(
            "Öğrendiğiniz formülleri 10 soruluk hızlı bir sınavla test edin. "
            "Sorular otomatik olarak formül veritabanınızdan üretilir."
        )
        text.setWordWrap(True)
        layout.addWidget(text)
        layout.addStretch()

        start_button = QPushButton("Sınavı Başlat")
        start_button.setObjectName("primaryButton")
        start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        start_button.clicked.connect(self._start_quick_quiz)
        layout.addWidget(start_button)
        return frame

    def _build_card_preview(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("previewCard")
        layout = QVBoxLayout(frame)
        header = QLabel("🗂️  Özet Kart")
        header.setObjectName("previewCardHeader")
        layout.addWidget(header)

        self.card_name_label = QLabel()
        self.card_name_label.setObjectName("previewCardName")
        layout.addWidget(self.card_name_label)

        self.card_description_label = QLabel()
        self.card_description_label.setWordWrap(True)
        layout.addWidget(self.card_description_label)

        self.card_syntax_label = QLabel()
        self.card_syntax_label.setObjectName("syntaxLabel")
        self.card_syntax_label.setWordWrap(True)
        layout.addWidget(self.card_syntax_label)
        layout.addStretch()

        view_all_button = QPushButton("Tüm Kartları Gör  →")
        view_all_button.setObjectName("linkButton")
        view_all_button.setCursor(Qt.CursorShape.PointingHandCursor)
        view_all_button.clicked.connect(lambda: self.navigate_requested.emit("cards"))
        layout.addWidget(view_all_button)
        return frame

    # ------------------------------------------------------------------
    def _show_current_formula(self) -> None:
        if not self.all_formulas:
            return
        formula = self.all_formulas[self.current_index]
        self.lesson_card.show_formula(formula)
        self.formula_service.mark_lesson_viewed(formula.id)

        self.exercise_question_label.setText(formula.exercise_question_tr or "Bu formül için alıştırma bulunmuyor.")
        self.exercise_input.clear()
        self.exercise_feedback_label.clear()

        self.card_name_label.setText(formula.name_tr)
        self.card_description_label.setText(formula.short_description_tr)
        self.card_syntax_label.setText(formula.syntax_tr)

        self._render_dots()
        self._populate_stat_cards()
        self.progress_changed.emit()

    def _render_dots(self) -> None:
        while self.dots_layout.count():
            item = self.dots_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        total_dots = min(MAX_DOTS, len(self.all_formulas)) or 1
        active_dot = self.current_index % total_dots
        for i in range(total_dots):
            dot = QLabel()
            dot.setFixedSize(8, 8)
            color = "#107C41" if i == active_dot else "#D7DEDB"
            dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
            self.dots_layout.addWidget(dot)

    def _show_previous(self) -> None:
        if self.all_formulas:
            self.current_index = (self.current_index - 1) % len(self.all_formulas)
            self._show_current_formula()

    def _show_next(self) -> None:
        if self.all_formulas:
            self.current_index = (self.current_index + 1) % len(self.all_formulas)
            self._show_current_formula()

    def _check_exercise(self) -> None:
        formula = self.all_formulas[self.current_index]
        answer = self.exercise_input.text()
        if not answer.strip():
            self.exercise_feedback_label.setText("Lütfen bir formül girin.")
            return
        is_correct = self.formula_service.check_exercise_answer(formula.id, answer)
        if is_correct:
            self.exercise_feedback_label.setText("✅ Doğru! Harika iş çıkardınız.")
        else:
            self.exercise_feedback_label.setText("❌ Doğru değil, tekrar deneyin.")
        self._populate_stat_cards()
        self.progress_changed.emit()

    def _start_quick_quiz(self) -> None:
        try:
            questions = self.formula_service.generate_quiz(question_count=10)
        except ValueError as exc:
            QMessageBox.warning(self, "Sınav Oluşturulamadı", str(exc))
            return
        dialog = QuizDialog(questions, self.formula_service, category_id=None, parent=self)
        dialog.exec()
        self._populate_stat_cards()
        self.progress_changed.emit()

    def refresh(self) -> None:
        """Sayfa tekrar görünür olduğunda istatistikleri tazeler."""
        self._populate_stat_cards()
