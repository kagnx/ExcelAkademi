"""FormulaRepository testleri."""
from __future__ import annotations

from app.repositories.formula_repository import FormulaRepository


def test_get_by_name_tr(session, sample_formula):
    repo = FormulaRepository(session)
    result = repo.get_by_name("topla")
    assert result is not None
    assert result.id == sample_formula.id


def test_get_by_name_en(session, sample_formula):
    repo = FormulaRepository(session)
    result = repo.get_by_name("SUM")
    assert result is not None
    assert result.id == sample_formula.id


def test_get_by_name_not_found(session, sample_formula):
    repo = FormulaRepository(session)
    assert repo.get_by_name("OLMAYANFORMUL") is None


def test_search_matches_description(session, sample_formula):
    repo = FormulaRepository(session)
    results = repo.search("toplar")
    assert any(f.id == sample_formula.id for f in results)


def test_search_matches_tags(session, sample_formula):
    repo = FormulaRepository(session)
    results = repo.search("toplama")
    assert any(f.id == sample_formula.id for f in results)


def test_search_empty_query_returns_all(session, sample_formula):
    repo = FormulaRepository(session)
    results = repo.search("")
    assert len(results) == 1


def test_search_turkish_case_insensitive_i(session, sample_formula):
    """Türkçe İ/I - ı/i büyük-küçük harf kuralı doğru çalışmalı."""
    repo = FormulaRepository(session)
    # 'sayıları' kelimesi açıklamada geçiyor; büyük harfle aratıldığında da bulunmalı
    results = repo.search("SAYILARI")
    assert any(f.id == sample_formula.id for f in results)


def test_by_category(session, sample_formula, sample_category):
    repo = FormulaRepository(session)
    results = repo.by_category(sample_category.id)
    assert len(results) == 1
    assert results[0].name_tr == "TOPLA"


def test_by_category_empty_for_unknown_id(session, sample_formula):
    repo = FormulaRepository(session)
    assert repo.by_category(9999) == []


def test_favorites_initially_empty(session, sample_formula):
    repo = FormulaRepository(session)
    assert repo.favorites() == []
