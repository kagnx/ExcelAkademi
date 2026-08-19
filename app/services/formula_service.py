"""
formula_service.py
-------------------
Formüllerle ilgili tüm iş mantığını barındırır: listeleme, arama,
favoriler, görüntülenme takibi, alıştırma kontrolü ve -en önemlisi-
mevcut formül veritabanından TAMAMEN OTOMATİK mini sınav üretimi.

Sınavlar formül tablosundan dinamik olarak türetildiği için, veritabanına
yeni formül eklendikçe (elle ya da `seed_data.py` üzerinden) sınav havuzu
otomatik olarak büyür; sorular elle yazılmaz.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from app.models.formula import Formula, Difficulty
from app.repositories.category_repository import CategoryRepository
from app.repositories.formula_repository import FormulaRepository
from app.repositories.user_progress_repository import UserProgressRepository
from app.utils.helpers import normalize_formula_answer
from app.utils.logger import app_logger


@dataclass
class QuizQuestion:
    formula_id: int
    question_tr: str
    choices: List[str]
    correct_index: int
    explanation_tr: str = ""


@dataclass
class QuizResultSummary:
    score: int
    total: int
    wrong_formula_ids: List[int] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        return round((self.score / self.total) * 100, 1) if self.total else 0.0


class FormulaService:
    MIN_FORMULAS_FOR_QUIZ = 2

    def __init__(
        self,
        formula_repo: FormulaRepository,
        category_repo: CategoryRepository,
        progress_repo: UserProgressRepository,
    ):
        self.formula_repo = formula_repo
        self.category_repo = category_repo
        self.progress_repo = progress_repo

    # ------------------------------------------------------------------
    # Listeleme / Arama
    # ------------------------------------------------------------------
    def list_categories(self):
        return self.category_repo.get_all_sorted()

    def get_category(self, category_id: int):
        return self.category_repo.get_by_id(category_id)

    def list_formulas(self, category_id: Optional[int] = None) -> List[Formula]:
        if category_id is not None:
            return self.formula_repo.by_category(category_id)
        return self.formula_repo.get_all_sorted()

    def search_formulas(self, query: str) -> List[Formula]:
        return self.formula_repo.search(query)

    def get_formula(self, formula_id: int) -> Optional[Formula]:
        return self.formula_repo.get_by_id(formula_id)

    def total_formula_count(self) -> int:
        return self.formula_repo.count()

    # ------------------------------------------------------------------
    # İlerleme / Favoriler / Görüntülenme
    # ------------------------------------------------------------------
    def is_favorite(self, formula_id: int) -> bool:
        return self.progress_repo.get_or_create(formula_id).is_favorite

    def toggle_favorite(self, formula_id: int) -> bool:
        progress = self.progress_repo.get_or_create(formula_id)
        progress.is_favorite = not progress.is_favorite
        self.progress_repo.update(progress)
        app_logger.info(f"Favori güncellendi: formula_id={formula_id} -> {progress.is_favorite}")
        return progress.is_favorite

    def list_favorites(self) -> List[Formula]:
        return self.formula_repo.favorites()

    def mark_lesson_viewed(self, formula_id: int) -> None:
        progress = self.progress_repo.get_or_create(formula_id)
        progress.lesson_viewed = True
        progress.lesson_viewed_at = datetime.now(timezone.utc)
        progress.view_count += 1
        self.progress_repo.update(progress)

    def mark_card_viewed(self, formula_id: int) -> None:
        progress = self.progress_repo.get_or_create(formula_id)
        if not progress.card_viewed:
            progress.card_viewed = True
            self.progress_repo.update(progress)

    def toggle_mastered(self, formula_id: int) -> bool:
        progress = self.progress_repo.get_or_create(formula_id)
        progress.is_mastered = not progress.is_mastered
        self.progress_repo.update(progress)
        return progress.is_mastered

    def is_mastered(self, formula_id: int) -> bool:
        return self.progress_repo.get_or_create(formula_id).is_mastered

    # ------------------------------------------------------------------
    # Alıştırmalar
    # ------------------------------------------------------------------
    def check_exercise_answer(self, formula_id: int, user_answer: str) -> bool:
        formula = self.get_formula(formula_id)
        if not formula or not formula.exercise_answer:
            return False

        progress = self.progress_repo.get_or_create(formula_id)
        progress.exercise_attempts += 1

        is_correct = normalize_formula_answer(user_answer) == normalize_formula_answer(
            formula.exercise_answer
        )
        if is_correct:
            progress.exercise_correct_count += 1
            progress.exercise_solved = True

        self.progress_repo.update(progress)
        return is_correct

    def formulas_with_exercise(self) -> List[Formula]:
        return [f for f in self.formula_repo.get_all_sorted() if f.exercise_question_tr]

    # ------------------------------------------------------------------
    # Mini Sınavlar (otomatik üretim)
    # ------------------------------------------------------------------
    def generate_quiz(
        self, category_id: Optional[int] = None, question_count: int = 10
    ) -> List[QuizQuestion]:
        pool = self.list_formulas(category_id)
        if len(pool) < self.MIN_FORMULAS_FOR_QUIZ:
            raise ValueError(
                "Sınav oluşturmak için yeterli formül bulunamadı "
                f"(en az {self.MIN_FORMULAS_FOR_QUIZ} formül gerekir)."
            )

        question_count = min(question_count, len(pool))
        chosen = random.sample(pool, question_count)

        question_types = ["ne_yapar", "ingilizce_karsilik", "hangi_formul"]
        questions: List[QuizQuestion] = []

        for formula in chosen:
            q_type = random.choice(question_types)
            distractor_pool = [f for f in pool if f.id != formula.id]
            distractor_count = min(3, len(distractor_pool))
            distractors = random.sample(distractor_pool, k=distractor_count) if distractor_count else []

            if q_type == "ne_yapar" or not distractors:
                question_tr = f"'{formula.name_tr}' fonksiyonu ne işe yarar?"
                correct_choice = formula.short_description_tr
                choices = [correct_choice] + [d.short_description_tr for d in distractors]
                explanation = formula.detailed_explanation_tr

            elif q_type == "ingilizce_karsilik":
                question_tr = f"'{formula.name_tr}' fonksiyonunun İngilizce karşılığı nedir?"
                correct_choice = formula.name_en
                choices = [correct_choice] + [d.name_en for d in distractors]
                explanation = f"{formula.name_tr} fonksiyonu, İngilizce Excel'de {formula.name_en} olarak bilinir."

            else:  # hangi_formul
                question_tr = (
                    f"Aşağıdaki formüllerden hangisi şu işi yapar: "
                    f"\"{formula.short_description_tr}\""
                )
                correct_choice = formula.example_formula
                choices = [correct_choice] + [d.example_formula for d in distractors]
                explanation = formula.example_description_tr

            random.shuffle(choices)
            correct_index = choices.index(correct_choice)
            questions.append(
                QuizQuestion(
                    formula_id=formula.id,
                    question_tr=question_tr,
                    choices=choices,
                    correct_index=correct_index,
                    explanation_tr=explanation,
                )
            )

        return questions

    def finalize_quiz(
        self,
        questions: List[QuizQuestion],
        answers: List[int],
        category_id: Optional[int] = None,
    ) -> QuizResultSummary:
        score = 0
        wrong_ids: List[int] = []
        for question, answer in zip(questions, answers):
            if answer == question.correct_index:
                score += 1
            else:
                wrong_ids.append(question.formula_id)

        self.progress_repo.record_quiz_result(
            score=score, total=len(questions), category_id=category_id
        )
        app_logger.info(f"Sınav tamamlandı: {score}/{len(questions)}")
        return QuizResultSummary(score=score, total=len(questions), wrong_formula_ids=wrong_ids)

    # ------------------------------------------------------------------
    # Özel Formül Ekleme (Doğrulanmış Girdi)
    # ------------------------------------------------------------------
    def add_custom_formula(self, validated_data: dict) -> Formula:
        """`ValidationService` ile doğrulanmış veriden yeni bir formül oluşturur."""
        formula = Formula(
            category_id=validated_data["category_id"],
            name_tr=validated_data["name_tr"],
            name_en=validated_data["name_en"],
            syntax_tr=validated_data["syntax_tr"],
            syntax_en=validated_data.get("syntax_en"),
            short_description_tr=validated_data["short_description_tr"],
            detailed_explanation_tr=validated_data["detailed_explanation_tr"],
            example_formula=validated_data["example_formula"],
            example_description_tr=validated_data["example_description_tr"],
            example_result=validated_data.get("example_result"),
            tags=validated_data.get("tags", []),
            difficulty=validated_data.get("difficulty", Difficulty.BASLANGIC),
        )
        return self.formula_repo.add(formula)
