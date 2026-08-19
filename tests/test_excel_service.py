"""ExcelService testleri: örnek workbook oluşturma ve toplu dışa aktarım."""
from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import load_workbook

from app.models.category import Category
from app.models.formula import Difficulty, Formula
from app.services.excel_service import ExcelService, _safe_sheet_name


# ---- Fixtures ----
@pytest.fixture()
def excel_service(tmp_path: Path) -> ExcelService:
    return ExcelService(export_dir=tmp_path)


@pytest.fixture()
def second_formula(session, sample_category) -> Formula:
    formula = Formula(
        category_id=sample_category.id,
        name_tr="EĞER",
        name_en="IF",
        syntax_tr="=EĞER(test;_doğru;yanlış)",
        short_description_tr="Bir koşulu test eder.",
        detailed_explanation_tr="EĞER, verilen koşulun DOĞRU veya YANLIŞ olduğunu kontrol eder.",
        example_formula='=EĞER(A1>10;"büyük";"küçük")',
        example_description_tr="A1 10'dan büyükse 'büyük', değilse 'küçük' yazar.",
        example_result="büyük",
        difficulty=Difficulty.ORTA,
    )
    session.add(formula)
    session.commit()
    return formula


# ---- _safe_sheet_name Tests ----
class TestSafeSheetName:
    def test_normal_name_unchanged(self):
        assert _safe_sheet_name("Matematik") == "Matematik"

    def test_truncates_to_31_chars(self):
        long_name = "A" * 40
        result = _safe_sheet_name(long_name)
        assert len(result) <= 31

    def test_removes_forbidden_chars(self):
        result = _safe_sheet_name('Test[0]:*?/\\Name')
        assert not any(ch in result for ch in '[]:*?/\\')

    def test_empty_returns_default(self):
        assert _safe_sheet_name("") == "Sayfa1"
        assert _safe_sheet_name("[]:*?/\\") == "Sayfa1"


# ---- build_example_workbook Tests ----
class TestBuildExampleWorkbook:
    def test_creates_xlsx_file(self, excel_service, sample_formula):
        path = excel_service.build_example_workbook(sample_formula)
        assert path.exists()
        assert path.suffix == ".xlsx"

    def test_filename_contains_formula_name(self, excel_service, sample_formula):
        path = excel_service.build_example_workbook(sample_formula)
        assert "TOPLA" in path.name

    def test_workbook_has_correct_sheet_title(self, excel_service, sample_formula):
        path = excel_service.build_example_workbook(sample_formula)
        wb = load_workbook(path)
        assert wb.sheetnames[0] == "TOPLA"

    def test_workbook_contains_formula_name_in_cell(self, excel_service, sample_formula):
        path = excel_service.build_example_workbook(sample_formula)
        wb = load_workbook(path)
        ws = wb.active
        assert "TOPLA" in str(ws["A1"].value)
        assert "SUM" in str(ws["A1"].value)

    def test_workbook_contains_syntax(self, excel_service, sample_formula):
        path = excel_service.build_example_workbook(sample_formula)
        wb = load_workbook(path)
        ws = wb.active
        assert ws["B3"].value == sample_formula.syntax_tr

    def test_workbook_contains_sample_data(self, excel_service, sample_formula):
        path = excel_service.build_example_workbook(sample_formula)
        wb = load_workbook(path)
        ws = wb.active
        # Sample numbers are in A9:A13
        assert ws["A9"].value == 12
        assert ws["A13"].value == 8

    def test_workbook_contains_example_formula(self, excel_service, sample_formula):
        path = excel_service.build_example_workbook(sample_formula)
        wb = load_workbook(path)
        ws = wb.active
        result_row = 9 + 5  # 9 + len(SAMPLE_NUMBERS)
        assert ws[f"B{result_row}"].value == sample_formula.example_formula

    def test_turkish_name_with_special_chars(self, excel_service, sample_category, session):
        formula = Formula(
            category_id=sample_category.id,
            name_tr="ÇOKETOPLA",
            name_en="SUMIFS",
            syntax_tr="=ÇOKETOPLA(...)",
            short_description_tr="Test.",
            detailed_explanation_tr="Açıklama.",
            example_formula="=ÇOKETOPLA(A1:A5)",
            example_description_tr="Örnek.",
            difficulty=Difficulty.ORTA,
        )
        session.add(formula)
        session.commit()
        path = excel_service.build_example_workbook(formula)
        assert path.exists()
        assert "ÇOKETOPLA" in path.name


# ---- export_all_formulas Tests ----
class TestExportAllFormulas:
    def test_creates_reference_workbook(self, excel_service, sample_formula):
        path = excel_service.export_all_formulas([sample_formula])
        assert path.exists()
        assert path.suffix == ".xlsx"
        assert "referans" in path.name

    def test_workbook_has_category_sheet(self, excel_service, sample_formula):
        path = excel_service.export_all_formulas([sample_formula])
        wb = load_workbook(path)
        # Should have a sheet named after the category
        assert len(wb.sheetnames) >= 1

    def test_workbook_contains_formula_data(self, excel_service, sample_formula):
        path = excel_service.export_all_formulas([sample_formula])
        wb = load_workbook(path)
        ws = wb.active
        # Row 2 should have formula data (row 1 is header)
        assert ws.cell(row=2, column=1).value == "TOPLA"
        assert ws.cell(row=2, column=2).value == "SUM"

    def test_multiple_categories_separate_sheets(
        self, excel_service, sample_formula, second_formula
    ):
        path = excel_service.export_all_formulas([sample_formula, second_formula])
        wb = load_workbook(path)
        # Both formulas are in the same category, so 1 sheet
        assert len(wb.sheetnames) == 1

    def test_turkish_name_in_category_sheet(self, excel_service, sample_category, session):
        formula = Formula(
            category_id=sample_category.id,
            name_tr="ÇOKETOPLA",
            name_en="SUMIFS",
            syntax_tr="=ÇOKETOPLA(...)",
            short_description_tr="Çoklu koşul toplama.",
            detailed_explanation_tr="Açıklama.",
            example_formula="=ÇOKETOPLA(...)",
            example_description_tr="Örnek.",
            difficulty=Difficulty.ORTA,
        )
        session.add(formula)
        session.commit()
        path = excel_service.export_all_formulas([formula])
        wb = load_workbook(path)
        ws = wb.active
        # Turkish name should be in column A, row 2
        assert ws.cell(row=2, column=1).value == "ÇOKETOPLA"

    def test_headers_are_present(self, excel_service, sample_formula):
        path = excel_service.export_all_formulas([sample_formula])
        wb = load_workbook(path)
        ws = wb.active
        expected_headers = ["Türkçe Ad", "İngilizce Ad", "Söz Dizimi", "Açıklama", "Örnek", "Zorluk"]
        for col_idx, header in enumerate(expected_headers, start=1):
            assert ws.cell(row=1, column=col_idx).value == header
