"""
pdf_service.py
--------------
İki farklı PDF kütüphanesini, iki farklı amaç için kullanır:

- ReportLab: Kategoriye göre gruplanmış, çok sayfalı, tablo düzenli
  "Formül Kılavuzu" (cheat-sheet) — zorluk sütunu, özet satırı ve
  sayfa numarası içeren altbilgi ile (daha zengin sayfa/tablo kontrolü).
- FPDF2: Tek bir formül için hızlı, çok bölümlü "Hızlı Referans Kartı":
  söz dizimi, açıklama, ne işe yarar, canlı örnek + beklenen sonuç,
  adım adım anlatım, alıştırma (soru/cevap/ipucu) ve etiketler. Her
  sayfada yeşil başlık bandı ve sayfa numarası içeren altbilgi vardır.

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
from app.utils.helpers import find_unicode_font, safe_filename
from app.utils.logger import app_logger

_EXCEL_GREEN = colors.HexColor("#107C41")
_LIGHT_GREEN = colors.HexColor("#E6F4EA")

# FPDF format="A5" yerine açık A5 boyutu (mm): fpdf2 >= 2.8.5 sürümünde
# format dizesi için gereksiz bir UserWarning üretiyor.
_A5_SIZE_MM = (148, 210)
_LEFT_MM = 8


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


class _QuickCardPDF(FPDF):
    """Hızlı referans kartı için A5 sayfa düzeni.

    Her sayfada yeşil başlık bandı (formül adı + kategori/zorluk) ve
    sayfa numarası içeren altbilgi otomatik çizilir.
    """

    def __init__(self, title: str, subtitle: str, footer_text: str, font_family: str):
        super().__init__(format=_A5_SIZE_MM)
        self._card_title = title
        self._card_subtitle = subtitle
        self._card_footer = footer_text
        self._card_font = font_family
        self.set_margins(_LEFT_MM, 26, _LEFT_MM)
        self.set_auto_page_break(auto=True, margin=15)

    def header(self) -> None:
        self.set_fill_color(16, 124, 65)  # Excel yeşili
        self.rect(0, 0, self.w, 22, style="F")
        self.set_text_color(255, 255, 255)
        self.set_font(self._card_font, size=15)
        self.set_xy(_LEFT_MM, 5)
        self.cell(0, 8, self._card_title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font(self._card_font, size=9)
        self.set_text_color(205, 235, 220)
        self.set_xy(_LEFT_MM, 14)
        self.cell(0, 6, self._card_subtitle, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(20, 20, 20)
        self.set_y(26)

    def footer(self) -> None:
        self.set_y(-13)
        self.set_draw_color(214, 214, 214)
        self.line(_LEFT_MM, self.get_y(), self.w - _LEFT_MM, self.get_y())
        self.set_font(self._card_font, size=7.5)
        self.set_text_color(130, 130, 130)
        self.set_xy(_LEFT_MM, self.get_y() + 1.5)
        self.cell(0, 5, self._card_footer, align="C")
        self.set_text_color(20, 20, 20)


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
        filename = f"formul_kilavuzu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        path = self.export_dir / filename

        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.8 * cm,
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

        by_category: dict[str, list[Formula]] = {}
        for formula in formulas:
            category_name = formula.category.name_tr if formula.category else "Diğer"
            by_category.setdefault(category_name, []).append(formula)

        prepared_at = datetime.now().strftime("%d.%m.%Y")
        summary = (
            f"{len(formulas)} formül • {len(by_category)} kategori • "
            f"Hazırlanma: {prepared_at}"
        )

        elements = [
            Paragraph(title, title_style),
            Paragraph(
                "Excel formüllerini ve fonksiyonlarını Türkçe öğrenmek için hazırlanmış başucu kılavuzu.",
                body_style,
            ),
            Paragraph(summary, body_style),
            Spacer(1, 10),
        ]

        if not formulas:
            elements.append(
                Paragraph("Bu kılavuzda gösterilecek formül bulunamadı.", body_style)
            )

        for idx, category_name in enumerate(sorted(by_category.keys())):
            items = sorted(by_category[category_name], key=lambda f: f.name_tr)
            if idx > 0:
                elements.append(PageBreak())
            elements.append(Paragraph(category_name, category_style))
            elements.append(
                Paragraph(f"{len(items)} fonksiyon", cell_style),
            )

            table_data = [[
                Paragraph("<b>Türkçe</b>", cell_style),
                Paragraph("<b>İngilizce</b>", cell_style),
                Paragraph("<b>Söz Dizimi</b>", cell_style),
                Paragraph("<b>Açıklama</b>", cell_style),
                Paragraph("<b>Zorluk</b>", cell_style),
            ]]
            for formula in items:
                table_data.append([
                    Paragraph(formula.name_tr, cell_style),
                    Paragraph(formula.name_en, cell_style),
                    Paragraph(formula.syntax_tr, cell_style),
                    Paragraph(formula.short_description_tr, cell_style),
                    Paragraph(formula.difficulty_label, cell_style),
                ])

            table = Table(
                table_data,
                colWidths=[2.3 * cm, 2.0 * cm, 4.6 * cm, 7.4 * cm, 1.5 * cm],
                repeatRows=1,
            )
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

        app_name = settings.app_name

        def _decorate_page(canvas, _doc) -> None:
            canvas.saveState()
            canvas.setFont(self._font_name, 7.5)
            canvas.setFillColor(colors.HexColor("#6B7670"))
            canvas.drawString(1.5 * cm, 1.0 * cm, f"{app_name} • Hazırlanma: {prepared_at}")
            canvas.drawRightString(A4[0] - 1.5 * cm, 1.0 * cm, f"Sayfa {canvas.getPageNumber()}")
            canvas.restoreState()

        doc.build(elements, onFirstPage=_decorate_page, onLaterPages=_decorate_page)
        app_logger.info(f"PDF kılavuz oluşturuldu ({len(formulas)} formül): {path}")
        return path

    # ------------------------------------------------------------------
    # FPDF2: Tek formül için hızlı referans kartı
    # ------------------------------------------------------------------
    def generate_quick_reference_card(self, formula: Formula) -> Path:
        """Tek bir formül için çok bölümlü, A5 boyutunda hızlı referans
        kartı üretir: söz dizimi, açıklama, detay, canlı örnek + beklenen
        sonuç, adım adım anlatım, alıştırma ve etiketler."""
        if self._unicode_font_path is not None:
            font_family = "TRFont"
        else:
            font_family = "Helvetica"
            app_logger.warning(
                "Hızlı referans kartı Türkçe karakter destekli yazı tipi olmadan üretiliyor."
            )

        category = getattr(formula, "category", None)
        category_name = category.name_tr if category is not None else "—"
        subtitle = f"Kategori: {category_name}   •   Zorluk: {formula.difficulty_label}"
        footer_text = (
            f"{settings.app_name}   •   {datetime.now().strftime('%d.%m.%Y')}   •   Sayfa {{nb}}"
        )

        pdf = _QuickCardPDF(
            title=f"{formula.name_tr}  ({formula.name_en})",
            subtitle=subtitle,
            footer_text=footer_text,
            font_family=font_family,
        )
        if self._unicode_font_path is not None:
            pdf.add_font("TRFont", "", str(self._unicode_font_path))
        pdf.add_page()

        # ---- Bölüm yardımcıları ----
        def heading(text: str) -> None:
            pdf.ln(3.5)
            pdf.set_x(_LEFT_MM)
            pdf.set_font(font_family, size=9)
            pdf.set_text_color(16, 124, 65)
            pdf.multi_cell(0, 5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(20, 20, 20)

        def paragraph(
            text: str,
            size: float = 9.5,
            line_height: float = 5.2,
            fill: Optional[tuple[int, int, int]] = None,
            text_color: tuple[int, int, int] = (20, 20, 20),
        ) -> None:
            pdf.ln(1)
            pdf.set_x(_LEFT_MM)
            pdf.set_font(font_family, size=size)
            pdf.set_text_color(*text_color)
            if fill is not None:
                pdf.set_fill_color(*fill)
            pdf.multi_cell(
                0, line_height, str(text), fill=fill is not None,
                new_x=XPos.LMARGIN, new_y=YPos.NEXT,
            )
            pdf.set_text_color(20, 20, 20)

        GREEN_FILL = (230, 244, 234)
        YELLOW_FILL = (255, 244, 214)

        # ---- İçerik ----
        heading("SÖZ DİZİMİ")
        paragraph(formula.syntax_tr, size=11, line_height=7, fill=GREEN_FILL)

        heading("AÇIKLAMA")
        paragraph(formula.short_description_tr or "—", size=10, line_height=5.6)

        if formula.detailed_explanation_tr:
            heading("NE İŞE YARAR?")
            paragraph(formula.detailed_explanation_tr, size=9.5, line_height=5.2)

        heading("CANLI ÖRNEK")
        paragraph(formula.example_formula, size=11, line_height=7, fill=(238, 242, 245))
        if formula.example_description_tr:
            paragraph(formula.example_description_tr, size=9.5, line_height=5.2)
        if formula.example_result:
            paragraph(
                f"Beklenen Sonuç: {formula.example_result}",
                size=10,
                line_height=6,
                fill=GREEN_FILL,
                text_color=(16, 124, 65),
            )

        steps = formula.steps or []
        if steps:
            heading("ADIM ADIM")
            for index, step in enumerate(steps, start=1):
                paragraph(f"{index}. {step}", size=9.5, line_height=5.2)

        if formula.exercise_question_tr:
            heading("ALIŞTIRMA")
            paragraph(formula.exercise_question_tr, size=10, line_height=5.6)
            if formula.exercise_answer:
                paragraph(
                    f"Cevap: {formula.exercise_answer}",
                    size=10,
                    line_height=6,
                    fill=GREEN_FILL,
                    text_color=(16, 124, 65),
                )
            if formula.exercise_hint_tr:
                paragraph(
                    f"İpucu: {formula.exercise_hint_tr}",
                    size=9,
                    line_height=5.2,
                    fill=YELLOW_FILL,
                    text_color=(120, 84, 0),
                )

        tags = formula.tags or []
        if tags:
            heading("ETİKETLER")
            paragraph(" • ".join(str(tag) for tag in tags), size=9, line_height=5.2,
                      text_color=(107, 118, 112))

        filename = f"{safe_filename(formula.name_tr)}_kart.pdf"
        path = self.export_dir / filename
        pdf.output(str(path))
        app_logger.info(f"Hızlı referans kartı oluşturuldu: {path}")
        return path


def create_pdf_service() -> PdfService:
    """DI container için fabrika fonksiyonu."""
    return PdfService(export_dir=settings.paths.pdf_exports_dir)
