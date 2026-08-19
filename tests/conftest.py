"""
conftest.py
-----------
Tüm testler için ortak pytest fixture'ları: bellek içi (in-memory) SQLite
veritabanı oturumu ve örnek kategori/formül nesneleri.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.models.category import Category
from app.models.formula import Difficulty, Formula


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    db_session = session_factory()
    yield db_session
    db_session.close()


@pytest.fixture()
def sample_category(session):
    category = Category(
        slug="matematik",
        name_tr="Matematik",
        description_tr="Test kategorisi",
        icon="➕",
        sort_order=1,
    )
    session.add(category)
    session.commit()
    return category


@pytest.fixture()
def sample_formula(session, sample_category):
    formula = Formula(
        category_id=sample_category.id,
        name_tr="TOPLA",
        name_en="SUM",
        syntax_tr="=TOPLA(sayı1; [sayı2]; ...)",
        syntax_en="=SUM(number1, [number2], ...)",
        short_description_tr="Sayıları toplar.",
        detailed_explanation_tr="TOPLA fonksiyonu belirtilen aralıktaki tüm sayıları toplar.",
        example_formula="=TOPLA(A1:A5)",
        example_description_tr="A1:A5 aralığındaki sayıları toplar.",
        example_result="88",
        steps=["Hücre aralığını seçin.", "=TOPLA( yazın.", "Aralığı belirtin.", "Enter'a basın."],
        tags=["matematik", "toplama"],
        exercise_question_tr="A1:A5 aralığındaki sayıları toplayan formülü yazın.",
        exercise_answer="=TOPLA(A1:A5)",
        exercise_hint_tr="TOPLA fonksiyonunu kullanın.",
        difficulty=Difficulty.BASLANGIC,
    )
    session.add(formula)
    session.commit()
    return formula
