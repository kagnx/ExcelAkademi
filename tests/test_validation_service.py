"""ValidationService testleri."""
from __future__ import annotations

from app.services.validation_service import ValidationService


def _valid_data() -> dict:
    return {
        "name_tr": "topla",
        "name_en": "sum",
        "category_id": 1,
        "syntax_tr": "=TOPLA(sayı1; sayı2)",
        "short_description_tr": "Sayıları toplar.",
        "detailed_explanation_tr": "Açıklama metni buraya gelir.",
        "example_formula": "=TOPLA(A1:A2)",
        "example_description_tr": "Örnek açıklaması.",
    }


def test_valid_formula_input_uppercases_names():
    ok, model, errors = ValidationService.validate_formula_input(_valid_data())
    assert ok is True
    assert model.name_tr == "TOPLA"
    assert model.name_en == "SUM"
    assert errors == []


def test_invalid_formula_missing_equals_sign():
    data = _valid_data()
    data["example_formula"] = "TOPLA(A1:A2)"  # eksik '='
    ok, model, errors = ValidationService.validate_formula_input(data)
    assert ok is False
    assert model is None
    assert len(errors) > 0


def test_invalid_formula_unbalanced_parentheses():
    data = _valid_data()
    data["example_formula"] = "=TOPLA(A1:A2"
    ok, _model, errors = ValidationService.validate_formula_input(data)
    assert ok is False
    assert len(errors) > 0


def test_invalid_formula_empty_name():
    data = _valid_data()
    data["name_tr"] = "   "
    ok, _model, errors = ValidationService.validate_formula_input(data)
    assert ok is False
    assert len(errors) > 0


def test_exercise_answer_validation():
    ok, errors = ValidationService.validate_exercise_answer("=TOPLA(A1:A5)")
    assert ok is True
    assert errors == []


def test_exercise_answer_validation_empty():
    ok, errors = ValidationService.validate_exercise_answer("   ")
    assert ok is False
    assert len(errors) > 0


def test_is_balanced_parentheses():
    assert ValidationService.is_balanced_parentheses("=TOPLA(A1:A2)") is True
    assert ValidationService.is_balanced_parentheses("=TOPLA(A1:A2") is False
    assert ValidationService.is_balanced_parentheses("=İNDİS(A1:C10;5;2)") is True
    assert ValidationService.is_balanced_parentheses("=İNDİS(A1:C10;5;2))") is False
