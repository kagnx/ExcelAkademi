"""
excel_service.py
-----------------
OpenPyXL kullanarak gerçek .xlsx dosyaları üretir:

1. `build_example_workbook`: Tek bir formülün gerçek Excel'de nasıl
   çalıştığını gösteren, kullanıcının kendi verisiyle deneyebileceği
   canlı bir örnek dosyası (formül hücreye GERÇEKTEN yazılır, statik bir
   değer değil).
2. `export_all_formulas`: Tüm formülleri kategoriye göre sekmelere
   ayırarak tek bir referans çalışma kitabına aktarır.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from app.config import settings
from app.models.formula import Formula
from app.utils.logger import app_logger

_HEADER_FILL = PatternFill(start_color="107C41", end_color="107C41", fill_type="solid")
_HEADER_FONT = Font(color="FFFFFF", bold=True, size=11)
_ACCENT_FONT = Font(italic=True, color="107C41")

# Sayısal toplama/istatistik formülleri için jenerik, tutarlı örnek veri seti.
_SAMPLE_NUMBERS = [12, 23, 35, 10, 8]


def _safe_sheet_name(name: str) -> str:
    """Excel sekme adları 31 karakteri geçemez ve bazı özel karakterleri kabul etmez."""
    forbidden = set('[]:*?/\\')
    cleaned = "".join(ch for ch in name if ch not in forbidden)
    return cleaned[:31] or "Sayfa1"


class ExcelService:
    def __init__(self, export_dir: Path):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    def build_example_workbook(self, formula: Formula) -> Path:
        """Formülün gerçek Excel'de nasıl çalıştığını gösteren, canlı formül
        içeren bir örnek dosya oluşturur ve dosya yolunu döner."""
        wb = Workbook()
        ws = wb.active
        ws.title = _safe_sheet_name(formula.name_tr)

        ws["A1"] = f"{formula.name_tr}  ({formula.name_en})"
        ws["A1"].font = Font(bold=True, size=14, color="107C41")
        ws.merge_cells("A1:D1")

        ws["A3"] = "Söz Dizimi:"
        ws["A3"].font = Font(bold=True)
        ws["B3"] = formula.syntax_tr

        ws["A4"] = "Açıklama:"
        ws["A4"].font = Font(bold=True)
        ws["B4"] = formula.short_description_tr
        ws["B4"].alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[4].height = 32

        ws["A6"] = "Canlı Örnek (aşağıdaki değerleri değiştirin, formül otomatik güncellenir)"
        ws["A6"].font = Font(bold=True, size=12, color="107C41")
        ws.merge_cells("A6:D6")

        ws["A8"] = "Değer"
        ws["A8"].font = _HEADER_FONT
        ws["A8"].fill = _HEADER_FILL
        for i, value in enumerate(_SAMPLE_NUMBERS, start=9):
            ws[f"A{i}"] = value

        result_row = 9 + len(_SAMPLE_NUMBERS)
        ws[f"A{result_row}"] = "Sonuç ->"
        ws[f"A{result_row}"].font = Font(bold=True)
        ws[f"B{result_row}"] = formula.example_formula
        ws[f"B{result_row}"].font = _ACCENT_FONT
        ws[f"B{result_row}"].fill = PatternFill(
            start_color="E6F4EA", end_color="E6F4EA", fill_type="solid"
        )

        for col in ("A", "B", "C", "D"):
            ws.column_dimensions[col].width = 30

        filename = f"{formula.name_tr}_ornek.xlsx".replace(" ", "_")
        path = self.export_dir / filename
        wb.save(path)
        app_logger.info(f"Örnek Excel dosyası oluşturuldu: {path}")
        return path

    # ------------------------------------------------------------------
    def export_all_formulas(self, formulas: List[Formula]) -> Path:
        """Tüm formülleri kategoriye göre gruplandırıp tek bir referans
        çalışma kitabına aktarır (her kategori ayrı bir sekmede)."""
        wb = Workbook()
        wb.remove(wb.active)

        by_category: dict[str, list[Formula]] = {}
        for formula in formulas:
            category_name = formula.category.name_tr if formula.category else "Diğer"
            by_category.setdefault(category_name, []).append(formula)

        headers = ["Türkçe Ad", "İngilizce Ad", "Söz Dizimi", "Açıklama", "Örnek", "Zorluk"]

        for category_name in sorted(by_category.keys()):
            items = by_category[category_name]
            ws = wb.create_sheet(title=_safe_sheet_name(category_name))

            for col_idx, header in enumerate(headers, start=1):
                cell = ws.cell(row=1, column=col_idx, value=header)
                cell.font = _HEADER_FONT
                cell.fill = _HEADER_FILL

            for row_idx, formula in enumerate(sorted(items, key=lambda f: f.name_tr), start=2):
                ws.cell(row=row_idx, column=1, value=formula.name_tr)
                ws.cell(row=row_idx, column=2, value=formula.name_en)
                ws.cell(row=row_idx, column=3, value=formula.syntax_tr)
                ws.cell(row=row_idx, column=4, value=formula.short_description_tr)
                ws.cell(row=row_idx, column=5, value=formula.example_formula)
                ws.cell(row=row_idx, column=6, value=formula.difficulty_label)

            for col_idx, header in enumerate(headers, start=1):
                ws.column_dimensions[get_column_letter(col_idx)].width = max(18, len(header) + 6)
            ws.freeze_panes = "A2"

        filename = f"excel_formulleri_referans_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        path = self.export_dir / filename
        wb.save(path)
        app_logger.info(f"{len(formulas)} formül Excel'e aktarıldı: {path}")
        return path


def create_excel_service() -> ExcelService:
    """DI container için fabrika fonksiyonu."""
    return ExcelService(export_dir=settings.paths.excel_exports_dir)
