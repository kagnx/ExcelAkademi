"""
pdf_service.py
--------------
İki farklı PDF kütüphanesini, iki farklı amaç için kullanır:

- ReportLab: Kategoriye göre gruplanmış, çok sayfalı, tablo düzenli
  "Formül Kılavuzu" (cheat-sheet) için (daha zengin sayfa/tablo kontrolü).
- FPDF2: Tek bir formül için hızlı, tek sayfalık "Hızlı Referans Kartı"
  için (daha hafif, hızlı üretim).

TÜRKÇE KARAKTER NOTU:
    ReportLab ve FPDF2'nin çekirdek yazı tipleri (Helvetica vb.) Latin-1
    tabanlıdır ve "ğ", "ş", "İ" gibi Türkçe'ye özgü karakterleri İÇERMEZ.
    Bu yüzden `find_unicode_font()` ile sistemde Unicode destekli bir TTF
    yazı tipi aranır ve bulunursa PDF'e gömülür; bulunamazsa çekirdek
    yazı tipine düşülür ve bir uyarı loglanır (ASCII içerik yine de
    doğru görünür, yalnızca Türkçe'ye özgü harfler bozulabilir).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.config import settings
from app.models.formula import Formula
from app.utils.helpers import find_unicode_font
from app.utils.logger import app_logger

_EXCEL_GREEN = colors.HexColor("#107C41")
_LIGHT_GREEN = colors.HexColor("#E6F4EA")


def _register_reportlab_font() -> str:
    """Türkçe karakter destekli bir TTF yazı tipini ReportLab'a kaydeder.
    Bulunamazsa 'Helvetica' döner (Türkçe'ye özgü harfler eksik görünebilir)."""
    font_path = find_unicode_font()
    if font_path is None:
        app_logger.warning(
            "Türkçe karakter destekli TTF yazı tipi bulunamadı; PDF'lerde "
            "Helvetica kullanılacak (ğ/ş/İ gibi karakterler eksik görünebilir)."
        )
        return "Helvetica"
    try:
        pdfmetrics.registerFont(TTFont("TRFont", str(font_path)))
        pdfmetrics.registerFont(TTFont("TRFont-Bold", str(font_path)))
        return "TRFont"
    except Exception:
        app_logger.exception("TTF yazı tipi ReportLab'a kaydedilirken hata oluştu")
        return "Helvetica"


class PdfService:
    def __init__(self, export_dir: Path):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self._font_name = _register_reportlab_font()
        self._unicode_font_path = find_unicode_font()

    # ------------------------------------------------------------------
    # ReportLab: Çok sayfalı formül kılavuzu
    # ------------------------------------------------------------------
    def generate_cheatsheet_pdf(self, formulas: List[Formula], title: str = "Excel Formül Kılavuzu") -> Path:
        filename = f"formul_kilavuzu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        path = self.export_dir / filename

        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
            title=title,
        )

        title_style = ParagraphStyle(
            "Baslik", fontName=self._font_name, fontSize=20, textColor=_EXCEL_GREEN, spaceAfter=6
        )
        category_style = ParagraphStyle(
            "Kategori", fontName=self._font_name, fontSize=15, textColor=_EXCEL_GREEN, spaceBefore=14, spaceAfter=8
        )
        body_style = ParagraphStyle("Govde", fontName=self._font_name, fontSize=9, leading=12)
        cell_style = ParagraphStyle("Hucre", fontName=self._font_name, fontSize=8.5, leading=11)

        elements = [
            Paragraph(title, title_style),
            Paragraph(
                "Excel formüllerini ve fonksiyonlarını Türkçe öğrenmek için hazırlanmış başucu kılavuzu.",
                body_style,
            ),
            Spacer(1, 10),
        ]

        by_category: dict[str, list[Formula]] = {}
        for formula in formulas:
            category_name = formula.category.name_tr if formula.category else "Diğer"
            by_category.setdefault(category_name, []).append(formula)

        for idx, category_name in enumerate(sorted(by_category.keys())):
            items = sorted(by_category[category_name], key=lambda f: f.name_tr)
            if idx > 0:
                elements.append(PageBreak())
            elements.append(Paragraph(category_name, category_style))

            table_data = [[
                Paragraph("<b>Türkçe</b>", cell_style),
                Paragraph("<b>İngilizce</b>", cell_style),
                Paragraph("<b>Söz Dizimi</b>", cell_style),
                Paragraph("<b>Açıklama</b>", cell_style),
            ]]
            for formula in items:
                table_data.append([
                    Paragraph(formula.name_tr, cell_style),
                    Paragraph(formula.name_en, cell_style),
                    Paragraph(formula.syntax_tr, cell_style),
                    Paragraph(formula.short_description_tr, cell_style),
                ])

            table = Table(table_data, colWidths=[2.6 * cm, 2.4 * cm, 5.2 * cm, 7.3 * cm], repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), _EXCEL_GREEN),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D7DEDB")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _LIGHT_GREEN]),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            elements.append(table)

        doc.build(elements)
        app_logger.info(f"PDF kılavuz oluşturuldu ({len(formulas)} formül): {path}")
        return path

    # ------------------------------------------------------------------
    # FPDF2: Tek formül için hızlı referans kartı
    # ------------------------------------------------------------------
    def generate_quick_reference_card(self, formula: Formula) -> Path:
        pdf = FPDF(format="A5")
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=12)

        if self._unicode_font_path is not None:
            pdf.add_font("TRFont", "", str(self._unicode_font_path))
            font_family = "TRFont"
        else:
            font_family = "Helvetica"
            app_logger.warning(
                "Hızlı referans kartı Türkçe karakter destekli yazı tipi olmadan üretiliyor."
            )

        pdf.set_fill_color(16, 124, 65)  # Excel yeşili
        pdf.rect(0, 0, pdf.w, 22, style="F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(font_family, size=16)
        pdf.set_xy(8, 6)
        pdf.cell(0, 10, f"{formula.name_tr}  ({formula.name_en})", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_text_color(20, 20, 20)
        pdf.set_xy(8, 28)
        pdf.set_x(8)

        pdf.set_font(font_family, size=10)
        pdf.multi_cell(0, 6, "Söz Dizimi:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_x(8)
        pdf.set_fill_color(230, 244, 234)
        pdf.set_font(font_family, size=11)
        pdf.multi_cell(0, 8, formula.syntax_tr, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(2)
        pdf.set_x(8)
        pdf.set_font(font_family, size=10)
        pdf.multi_cell(0, 6, "Açıklama:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_x(8)
        pdf.multi_cell(0, 6, formula.short_description_tr, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(2)
        pdf.set_x(8)
        pdf.multi_cell(0, 6, "Örnek:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_x(8)
        pdf.set_font(font_family, size=11)
        pdf.multi_cell(0, 6, formula.example_formula, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_x(8)
        pdf.set_font(font_family, size=9)
        pdf.multi_cell(0, 6, formula.example_description_tr, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        if formula.exercise_hint_tr:
            pdf.ln(3)
            pdf.set_x(8)
            pdf.set_fill_color(255, 244, 214)
            pdf.set_font(font_family, size=9)
            pdf.multi_cell(0, 6, f"İpucu: {formula.exercise_hint_tr}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        filename = f"{formula.name_tr}_kart.pdf".replace(" ", "_")
        path = self.export_dir / filename
        pdf.output(str(path))
        app_logger.info(f"Hızlı referans kartı oluşturuldu: {path}")
        return path


def create_pdf_service() -> PdfService:
    """DI container için fabrika fonksiyonu."""
    return PdfService(export_dir=settings.paths.pdf_exports_dir)
