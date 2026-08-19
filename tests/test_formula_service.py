"""FormulaService testleri."""
from __future__ import annotations

import pytest

from app.models.formula import Difficulty, Formula
from app.repositories.category_repository import CategoryRepository
from app.repositories.formula_repository import FormulaRepository
from app.repositories.user_progress_repository import UserProgressRepository
from app.services.formula_service import FormulaService


@pytest.fixture()
def formula_service(session):
    return FormulaService(
        FormulaRepository(session),
        CategoryRepository(session),
        UserProgressRepository(session),
    )


def _add_second_formula(session, category):
    formula = Formula(
        category_id=category.id,
        name_tr="ORTALAMA",
        name_en="AVERAGE",
        syntax_tr="=ORTALAMA(sayı1; [sayı2]; ...)",
        short_description_tr="Sayıların ortalamasını alır.",
        detailed_explanation_tr="ORTALAMA fonksiyonu sayıların aritmetik ortalamasını hesaplar.",
        example_formula="=ORTALAMA(A1:A5)",
        example_description_tr="A1:A5 aralığının ortalamasını bulur.",
        difficulty=Difficulty.BASLANGIC,
    )
    session.add(formula)
    session.commit()
    return formula


# ---- Favoriler ----
def test_is_favorite_initially_false(formula_service, sample_formula):
    assert formula_service.is_favorite(sample_formula.id) is False


def test_toggle_favorite(formula_service, sample_formula):
    result = formula_service.toggle_favorite(sample_formula.id)
    assert result is True
    assert formula_service.is_favorite(sample_formula.id) is True

    result_again = formula_service.toggle_favorite(sample_formula.id)
    assert result_again is False
    assert formula_service.is_favorite(sample_formula.id) is False


def test_list_favorites(formula_service, sample_formula):
    formula_service.toggle_favorite(sample_formula.id)
    favorites = formula_service.list_favorites()
    assert len(favorites) == 1
    assert favorites[0].id == sample_formula.id


# ---- Görüntülenme takibi ----
def test_mark_lesson_viewed(formula_service, sample_formula, session):
    formula_service.mark_lesson_viewed(sample_formula.id)
    progress = formula_service.progress_repo.get_by_formula_id(sample_formula.id)
    assert progress.lesson_viewed is True
    assert progress.view_count == 1


# ---- Alıştırmalar ----
def test_check_exercise_answer_correct(formula_service, sample_formula):
    assert formula_service.check_exercise_answer(sample_formula.id, "=TOPLA(A1:A5)") is True


def test_check_exercise_answer_normalizes_comma_separator(formula_service, sample_formula):
    """Kullanıcı İngilizce alışkanlığıyla virgül kullansa bile doğru kabul edilmeli."""
    assert formula_service.check_exercise_answer(sample_formula.id, "=topla(a1:a5)") is True


def test_check_exercise_answer_wrong(formula_service, sample_formula):
    assert formula_service.check_exercise_answer(sample_formula.id, "=ORTALAMA(A1:A5)") is False


def test_check_exercise_answer_tracks_attempts(formula_service, sample_formula):
    formula_service.check_exercise_answer(sample_formula.id, "=YANLIŞ()")
    progress = formula_service.progress_repo.get_by_formula_id(sample_formula.id)
    assert progress.exercise_attempts == 1
    assert progress.exercise_solved is False


# ---- Mini Sınavlar ----
def test_generate_quiz_requires_minimum_formulas(formula_service, sample_category):
    with pytest.raises(ValueError):
        formula_service.generate_quiz()


def test_generate_quiz_with_enough_formulas(formula_service, session, sample_category, sample_formula):
    _add_second_formula(session, sample_category)
    questions = formula_service.generate_quiz(question_count=2)
    assert len(questions) == 2
    for question in questions:
        assert 0 <= question.correct_index < len(question.choices)


def test_finalize_quiz_records_score(formula_service, session, sample_category, sample_formula):
    _add_second_formula(session, sample_category)
    questions = formula_service.generate_quiz(question_count=2)
    correct_answers = [q.correct_index for q in questions]
    result = formula_service.finalize_quiz(questions, correct_answers)
    assert result.score == 2
    assert result.total == 2
    assert result.percentage == 100.0
