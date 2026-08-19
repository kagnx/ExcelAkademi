"""
validation_service.py
----------------------
Pydantic ile giriş doğrulama. Şu an tek kullanım noktası, kullanıcının
arayüzden özel bir formül eklemesidir ("Yeni Formül Ekle"), ancak
`FormulaInputSchema` bağımsız da (örn. ileride JSON içe aktarma
özelliği eklenirse) kullanılabilir.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.models.formula import Difficulty
from app.utils.helpers import is_balanced_parentheses


class FormulaInputSchema(BaseModel):
    name_tr: str
    name_en: str
    category_id: int
    syntax_tr: str
    syntax_en: Optional[str] = None
    short_description_tr: str = Field(min_length=3, max_length=255)
    detailed_explanation_tr: str = Field(min_length=3)
    example_formula: str
    example_description_tr: str
    example_result: Optional[str] = None
    difficulty: Difficulty = Difficulty.BASLANGIC
    tags: List[str] = Field(default_factory=list)

    @field_validator("name_tr", "name_en")
    @classmethod
    def _name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Fonksiyon adı boş olamaz.")
        return v.strip().upper()

    @field_validator("syntax_tr", "example_formula")
    @classmethod
    def _formula_must_look_valid(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith("="):
            raise ValueError("Formül '=' işareti ile başlamalıdır.")
        if not is_balanced_parentheses(v):
            raise ValueError("Formüldeki parantezler dengeli değil.")
        return v


class ExerciseAnswerSchema(BaseModel):
    raw_answer: str

    @field_validator("raw_answer")
    @classmethod
    def _not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Lütfen bir formül girin.")
        return v


class ValidationService:
    """Statik yardımcı metotlar barındırır; durum (state) tutmaz."""

    @staticmethod
    def validate_formula_input(data: dict) -> Tuple[bool, Optional[FormulaInputSchema], List[str]]:
        try:
            model = FormulaInputSchema(**data)
            return True, model, []
        except ValidationError as exc:
            errors = [err["msg"] for err in exc.errors()]
            return False, None, errors

    @staticmethod
    def validate_exercise_answer(raw_answer: str) -> Tuple[bool, List[str]]:
        try:
            ExerciseAnswerSchema(raw_answer=raw_answer)
            return True, []
        except ValidationError as exc:
            return False, [err["msg"] for err in exc.errors()]

    @staticmethod
    def is_balanced_parentheses(formula: str) -> bool:
        return is_balanced_parentheses(formula)
