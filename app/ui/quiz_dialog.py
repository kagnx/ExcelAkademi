"""
quiz_dialog.py
--------------
Otomatik üretilen mini sınav sorularını sırayla gösteren, kullanıcının
cevaplarını toplayan ve sonunda skoru bildiren modal diyalog.
"""
from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from app.services.formula_service import FormulaService, QuizQuestion


class QuizDialog(QDialog):
    def __init__(
        self,
        questions: List[QuizQuestion],
        formula_service: FormulaService,
        category_id: Optional[int] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.questions = questions
        self.formula_service = formula_service
        self.category_id = category_id
        self.current_index = 0
        self.answers: List[int] = []
        self.choice_buttons: List[QRadioButton] = []

        self.setObjectName("quizDialog")
        self.setWindowTitle("Mini Sınav")
        self.setMinimumSize(560, 420)

        self._build_ui()
        self._show_question()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        self.progress_label = QLabel()
        self.progress_label.setObjectName("quizProgressLabel")
        layout.addWidget(self.progress_label)

        self.question_label = QLabel()
        self.question_label.setObjectName("quizQuestionLabel")
        self.question_label.setWordWrap(True)
        layout.addWidget(self.question_label)

        self.button_group = QButtonGroup(self)
        for _ in range(4):
            radio = QRadioButton()
            radio.setObjectName("quizChoice")
            self.choice_buttons.append(radio)
            self.button_group.addButton(radio)
            layout.addWidget(radio)

        layout.addStretch()

        self.next_button = QPushButton("Sonraki  →")
        self.next_button.setObjectName("primaryButton")
        self.next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_button.clicked.connect(self._on_next_clicked)
        layout.addWidget(self.next_button)

    def _show_question(self) -> None:
        question = self.questions[self.current_index]
        self.progress_label.setText(f"Soru {self.current_index + 1} / {len(self.questions)}")
        self.question_label.setText(question.question_tr)

        self.button_group.setExclusive(False)
        for radio in self.choice_buttons:
            radio.setChecked(False)
        self.button_group.setExclusive(True)

        for radio, choice in zip(self.choice_buttons, question.choices):
            radio.setText(choice)
            radio.setVisible(True)
        for radio in self.choice_buttons[len(question.choices):]:
            radio.setVisible(False)

        is_last = self.current_index == len(self.questions) - 1
        self.next_button.setText("Sınavı Bitir  ✓" if is_last else "Sonraki  →")

    def _on_next_clicked(self) -> None:
        selected_index = -1
        for i, radio in enumerate(self.choice_buttons):
            if radio.isVisible() and radio.isChecked():
                selected_index = i
                break

        if selected_index == -1:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen devam etmeden önce bir seçenek işaretleyin.")
            return

        self.answers.append(selected_index)
        self.current_index += 1

        if self.current_index < len(self.questions):
            self._show_question()
        else:
            self._finish_quiz()

    def _finish_quiz(self) -> None:
        result = self.formula_service.finalize_quiz(self.questions, self.answers, self.category_id)
        emoji = "🏆" if result.percentage >= 80 else ("👍" if result.percentage >= 50 else "💪")
        QMessageBox.information(
            self,
            "Sınav Sonucu",
            f"{emoji}  Skorunuz: {result.score} / {result.total}   (%{result.percentage})\n\n"
            "Yanlış cevapladığınız formülleri Konu Anlatımları bölümünden tekrar gözden geçirebilirsiniz.",
        )
        self.accept()
