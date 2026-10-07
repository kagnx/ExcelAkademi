"""PdfService testleri: kılavuz PDF ve hızlı referans kartı oluşturma."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.models.category import Category
from app.models.formula import Difficulty, Formula
from app.services.pdf_service import PdfService


# ---- Fixtures ----
@pytest.fixture()
def pdf_service(tmp_path: Path) -> PdfService:
    return PdfService(export_dir=tmp_path)


@pytest.fixture()
def second_category(session) -> Category:
    category = Category(
        slug="metin",
        name_tr="Metin Fonksiyonları",
        description_tr="Metin işlemleri.",
        icon="🔤",
        sort_order=2,
    )
    session.add(category)
    session.commit()
    return category


@pytest.fixture()
def second_formula(session, second_category) -> Formula:
    formula = Formula(
        category_id=second_category.id,
        name_tr="SOLDAN",
        name_en="LEFT",
        syntax_tr="=SOLDAN(metin; [sayı_karakter])",
        short_description_tr="Metnin soldan karakterlerini alır.",
        detailed_explanation_tr="SOLDAN, verilen metnin başından karakter döndürür.",
        example_formula="=SOLDAN(A1;3)",
        example_description_tr="A1'deki ilk 3 karakteri alır.",
        difficulty=Difficulty.BASLANGIC,
    )
    session.add(formula)
    session.commit()
    return formula


# ---- generate_cheatsheet_pdf Tests ----
class TestGenerateCheatsheetPdf:
    def test_creates_pdf_file(self, pdf_service, sample_formula):
        path = pdf_service.generate_cheatsheet_pdf([sample_formula])
        assert path.exists()
        assert path.suffix == ".pdf"

    def test_filename_contains_kilavuz(self, pdf_service, sample_formula):
        path = pdf_service.generate_cheatsheet_pdf([sample_formula])
        assert "kilavuz" in path.name

    def test_pdf_file_size_nonzero(self, pdf_service, sample_formula):
        path = pdf_service.generate_cheatsheet_pdf([sample_formula])
        assert path.stat().st_size > 0

    def test_custom_title(self, pdf_service, sample_formula):
        path = pdf_service.generate_cheatsheet_pdf(
            [sample_formula], title="Özel Başlık"
        )
        assert path.exists()

    def test_multiple_formulas_different_categories(
        self, pdf_service, sample_formula, second_formula
    ):
        path = pdf_service.generate_cheatsheet_pdf([sample_formula, second_formula])
        assert path.exists()
        assert path.stat().st_size > 0

    def test_empty_list_creates_valid_pdf(self, pdf_service):
        path = pdf_service.generate_cheatsheet_pdf([])
        assert path.exists()


# ---- generate_quick_reference_card Tests ----
class TestGenerateQuickReferenceCard:
    def test_creates_pdf_file(self, pdf_service, sample_formula):
        path = pdf_service.generate_quick_reference_card(sample_formula)
        assert path.exists()
        assert path.suffix == ".pdf"

    def test_filename_contains_formula_name(self, pdf_service, sample_formula):
        path = pdf_service.generate_quick_reference_card(sample_formula)
        assert "TOPLA" in path.name

    def test_filename_contains_kart(self, pdf_service, sample_formula):
        path = pdf_service.generate_quick_reference_card(sample_formula)
        assert "kart" in path.name

    def test_pdf_file_size_nonzero(self, pdf_service, sample_formula):
        path = pdf_service.generate_quick_reference_card(sample_formula)
        assert path.stat().st_size > 0

    def test_turkish_name_in_filename(self, pdf_service, sample_category, session):
        formula = Formula(
            category_id=sample_category.id,
            name_tr="ÇOKETOPLA",
            name_en="SUMIFS",
            syntax_tr="=ÇOKETOPLA(...)",
            short_description_tr="Test.",
            detailed_explanation_tr="Açıklama.",
            example_formula="=ÇOKETOPLA(A1:A5)",
            example_description_tr="Örnek.",
            exercise_hint_tr="İpucu metni.",
            difficulty=Difficulty.ORTA,
        )
        session.add(formula)
        session.commit()
        path = pdf_service.generate_quick_reference_card(formula)
        assert path.exists()
        assert "ÇOKETOPLA" in path.name

    def test_rich_card_is_larger_than_basic_card(self, pdf_service, sample_category, session):
        """Adım/ipucu/etiket içeren formül, sade formülden daha kapsamlı kart üretmeli."""
        minimal = Formula(
            category_id=sample_category.id,
            name_tr="PİKSEL",
            name_en="PX",
            syntax_tr="=PİKSEL()",
            short_description_tr="Sade açıklama.",
            detailed_explanation_tr="Sade detay.",
            example_formula="=PİKSEL()",
            example_description_tr="Sade örnek.",
            steps=None,
            tags=None,
            exercise_question_tr=None,
            exercise_answer=None,
            exercise_hint_tr=None,
            difficulty=Difficulty.BASLANGIC,
        )
        rich = Formula(
            category_id=sample_category.id,
            name_tr="DÜŞEYARA",
            name_en="VLOOKUP",
            syntax_tr="=DÜŞEYARA(aranan_değer; tablo_aralığı; sütun_no; [yaklaşık])",
            short_description_tr="Bir değer arar ve ilgili sütunu döndürür.",
            detailed_explanation_tr="DÜŞEYARA, tablonun ilk sütununda arama yapar.",
            example_formula="=DÜŞEYARA(\"Ali\";A1:C10;3;YANLIŞ)",
            example_description_tr="A1:C10 aralığında Ali arar, 3. sütunu döndürür.",
            example_result="Yılmaz",
            steps=["Aralığı seçin.", "Sütun numarasını belirleyin.", "Tam eşleşme için YANLIŞ yazın."],
            tags=["arama", "başvuru"],
            exercise_question_tr="DÜŞEYARA ile tam eşleşme nasıl sağlanır?",
            exercise_answer="=DÜŞEYARA(...;YANLIŞ)",
            exercise_hint_tr="Son parametre YANLIŞ olmalı.",
            difficulty=Difficulty.ORTA,
        )
        session.add_all([minimal, rich])
        session.commit()

        minimal_path = pdf_service.generate_quick_reference_card(minimal)
        rich_path = pdf_service.generate_quick_reference_card(rich)
        assert minimal_path.exists() and rich_path.exists()
        assert minimal_path.stat().st_size > 0
        # Kapsamlı içerik (detay + adımlar + alıştırma + etiketler) daha büyük kart üretir:
        assert rich_path.stat().st_size > minimal_path.stat().st_size
        assert "DÜŞEYARA" in rich_path.name

    def test_card_filename_is_sanitized(self, pdf_service, sample_category, session):
        formula = Formula(
            category_id=sample_category.id,
            name_tr='TE/ST<FORMÜL',
            name_en="TEST",
            syntax_tr="=TEST()",
            short_description_tr="Test.",
            detailed_explanation_tr="Açıklama.",
            example_formula="=TEST(A1:A5)",
            example_description_tr="Örnek.",
            difficulty=Difficulty.BASLANGIC,
        )
        session.add(formula)
        session.commit()
        path = pdf_service.generate_quick_reference_card(formula)
        assert path.exists()
        assert not any(ch in path.name for ch in '<>:"/\\|?*')

    def test_formula_without_hint(self, pdf_service, sample_category, session):
        formula = Formula(
            category_id=sample_category.id,
            name_tr="Pİ",
            name_en="PI",
            syntax_tr="=Pİ()",
            short_description_tr="Pi sayısını verir.",
            detailed_explanation_tr="Pi sabiti.",
            example_formula="=Pİ()",
            example_description_tr="Pi değerini döndürür.",
            exercise_hint_tr=None,
            difficulty=Difficulty.ORTA,
        )
        session.add(formula)
        session.commit()
        path = pdf_service.generate_quick_reference_card(formula)
        assert path.exists()
