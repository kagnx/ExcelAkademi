"""
excel_service.py
----------------
OpenPyXL kullanarak gerçek .xlsx dosyaları üretir:

1. `build_example_workbook`: Tek bir formülün gerçek Excel'de nasıl
   çalıştığını gösteren, kullanıcının kendi verisiyle deneyebileceği
   canlı örnek dosya.

   Örnek veriler, örnek formülün referans verdiği HÜCRELERE (ör. A1:A5)
   yazılır; başlık/söz dizimi/açıklama gibi bilgi metinleri ise veri
   bloğunun SAĞINDA tutulur. Böylece dosya Excel'de açıldığında formül
   gerçekten hesaplanır ve kitapta gösterilen "Beklenen Sonuç" ile
   eşleşir (eski düzende bilgi metinleri A1:A5 içinde olduğu için formül
   metin hücrelerini toplayıp 0 / hata döndürüyordu).

2. `export_all_formulas`: Tüm formülleri kategoriye göre gruplayıp
   zengin sütunlarla (detaylı açıklama, örnek açıklaması, beklenen sonuç,
   alıştırma sorusu/cevabı, ipucu, etiketler) tek bir referans çalışma
   kitabına aktarır; sayfalar üstte başlık kilidi ve otomatik filtre içerir.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import List, Sequence, Tuple

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import column_index_from_string, get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from app.config import settings
from app.models.formula import Formula
from app.utils.helpers import is_balanced_parentheses, safe_filename
from app.utils.logger import app_logger

# OOXML (xlsx) dosya biçimi, formülleri YERELLEŞTİRİLMEMİŞ evrensel gramerle
# saklar: kanonik (İngilizce) fonksiyon adları, ',' argüman ayıracı, '.'
# ondalık ayracı. Türkçe Excel açılışta bunları kendi diline çeviri gösterir
# (=SUM -> =TOPLA, ',' -> ';'). Dosyaya Türkçe ad/' ';' yazılırsa Excel ya
# tüm kitabı reddeder (ayraç) ya da #NAME? döner (ad) — bu yüzden canlı
# formül hücrelerine yazmadan önce `to_universal_formula()` ile çevrilir.
try:  # Tohum verideki tüm Türkçe/İngilizce fonksiyon adı eşleştirmeleri
    from app.data.seed_data import FORMULAS as _SEED_FORMULAS

    _TR_EN_NAME_MAP: dict[str, str] = {
        f["name_tr"]: f["name_en"] for f in _SEED_FORMULAS if f.get("name_tr") and f.get("name_en")
    }
except Exception:  # pragma: no cover - tohum veri yoksa bile çalışır (kendi eşlemesi kalır)
    _TR_EN_NAME_MAP = {}

_STRING_LITERAL_RE = re.compile(r'"[^"]*"')
_FUNC_CALL_RE = re.compile(r"\w+(?:\.\w+)*(?=\s*\()")
# Mantıksal sabitler dosya biçiminde İngilizce yazılır: DOĞRU->TRUE, YANLIŞ->FALSE
_BOOLEAN_LITERAL_MAP = {"DOĞRU": "TRUE", "YANLIŞ": "FALSE"}
_BOOLEAN_LITERAL_RE = re.compile(r"(?<![A-Za-z0-9_])(DOĞRU|YANLIŞ)(?![A-Za-z0-9_])")

# OOXML dosya gramerinde 2007 sonrası eklenen fonksiyonlar "_xlfn." önekiyle
# saklanır. Öneksiz yazılan ad Excel dosya yüklenirken ad (name) olarak çözülür
# ve #NAME? üretir; Excel arayüzünde önek gizlenir, Türkçe ad görünür:
#   dosyada: =_xlfn.IFS(...)   ->   ekranda: =ÇOKEĞER(...)
# (2007 ve öncesi: SUM, IF, VLOOKUP, SUMIFS, INDIRECT... önek GEREKTİRMEZ.)
_XLFN_FUNCTIONS = {
    "IFS", "MAXIFS", "MINIFS", "TEXTJOIN", "IFNA", "CONCAT", "SWITCH",
    "XLOOKUP", "XMATCH", "FILTER", "SEQUENCE", "UNIQUE", "SORTBY", "LET",
}
_TIME_RESULT_RE = re.compile(r"\d{1,2}:\d{2}(:\d{2})?")
_DATE_RESULT_RE = re.compile(r"\d{1,2}\.\d{1,2}\.\d{4}")

_HEADER_FILL = PatternFill(start_color="107C41", end_color="107C41", fill_type="solid")
_HEADER_FONT = Font(color="FFFFFF", bold=True, size=11)
_ACCENT_FONT = Font(italic=True, color="107C41")
_LABEL_FONT = Font(bold=True, color="107C41")
_TITLE_FONT = Font(bold=True, size=14, color="107C41")
_RESULT_FONT = Font(bold=True, color="107C41")
_RESULT_FILL = PatternFill(start_color="E6F4EA", end_color="E6F4EA", fill_type="solid")

# Sayısal toplama/istatistik formülleri için jenerik, tutarlı örnek veri seti.
# Tohum verideki beklenen sonuçlar bu değerlerle uyumludur:
#   12+23+35+10+8 = 88, 20'den büyüklerin toplamı = 58, ortalaması = 17,6 ...
_SAMPLE_NUMBERS = [12, 23, 35, 10, 8]

# Excel hücre referansları: A1, $A$1, A1:A5, B3:B10 gibi biçimler.
_CELL_REF_RE = re.compile(
    r"\$?([A-Z]{1,3})\$?([0-9]{1,7})(?::\$?([A-Z]{1,3})\$?([0-9]{1,7}))?"
)

_MAX_EXCEL_COL = 16384      # XFD
_MAX_EXCEL_ROW = 1_048_576

_EXPORT_HEADERS = [
    "Türkçe Ad",
    "İngilizce Ad",
    "Söz Dizimi",
    "Açıklama",
    "Örnek",
    "Zorluk",
    "Detaylı Açıklama",
    "Örnek Açıklama",
    "Beklenen Sonuç",
    "Alıştırma Sorusu",
    "Alıştırma Cevabı",
    "İpucu",
    "Etiketler",
]
_EXPORT_WIDTHS = [18, 16, 34, 42, 30, 12, 50, 42, 18, 44, 30, 40, 28]


def _safe_sheet_name(name: str) -> str:
    """Excel sekme adları 31 karakteri geçemez ve bazı özel karakterleri kabul etmez."""
    forbidden = set('[]:*?/\\')
    cleaned = "".join(ch for ch in name if ch not in forbidden)
    return cleaned[:31] or "Sayfa1"


def _set_text(cell, value) -> None:
    """Hücreye değer yazar; `=` ile başlayan metinleri ise formül değil DÜZ
    METİN olarak saklar.

    openpyxl `=` ile başlayan her dizeyi formül olarak yazar. Söz dizimi
    metinleri (ör. ``=TOPLA(sayı1; [sayı2]; ...)``) geçersiz formül
    sözdizimi olduğu için Excel, dosyanın AÇILIŞINDA hata verir ve tüm
    çalışma kitabını reddeder (0x800A03EC). Bu yüzden yer tutuculu
    metinler her zaman düz metin olarak yazılır.
    """
    cell.value = value
    if isinstance(value, str) and value.startswith("="):
        cell.data_type = "s"


def _is_live_formula(text: str) -> bool:
    """Metnin Excel'in dosya açarken ayrıştırabileceği geçerli bir formül
    olup olmadığı. Yer tutucu '...' ve köşeli parantezler Excel'de
    ayıklama (parse) hatası verip dosyanın açılmasını engeller."""
    if not text or not text.startswith("="):
        return False
    if "..." in text or "[" in text or "]" in text or "\n" in text:
        return False
    return is_balanced_parentheses(text)


def _convert_segment(segment: str, name_map: dict[str, str]) -> str:
    """Tırnak DİŞİ kalan bir formül parçasında: fonksiyon adlarını kanonik
    (İngilizce) adıyla değiştirir, mantıksal sabitleri TRUE/FALSE'e çevirir,
    ';' argüman ayıracını ','ye ve rakamlar arasındaki ondalık virgülü '.'ye
    çevirir. Dizi sabitlerinin ({...}) içindeki virgül ayıraçtır, noktaya
    çevrilmez. (Tırnak içi metinler çağrılmadan önce ayrılır.)"""

    def _replace(match: "re.Match[str]") -> str:
        name = match.group(0)
        english = name_map.get(name) or name_map.get(name.upper()) or name
        if english.upper() in _XLFN_FUNCTIONS:
            return "_xlfn." + english        # dosya biçimi öneki (bkz. modül üstü not)
        return english

    segment = _FUNC_CALL_RE.sub(_replace, segment)
    segment = _BOOLEAN_LITERAL_RE.sub(
        lambda match: name_map.get(match.group(1), match.group(1)), segment
    )

    chars: list[str] = []
    brace_depth = 0
    for index, ch in enumerate(segment):
        if ch == "{":
            brace_depth += 1
        elif ch == "}":
            brace_depth = max(0, brace_depth - 1)

        if ch == ";":                       # TR argüman ayıracı -> evrensel ','
            chars.append(",")
        elif ch == ",":
            prev = segment[index - 1] if index > 0 else ""
            nxt = segment[index + 1] if index + 1 < len(segment) else ""
            # Rakamlar arasındaki virgül ONDALIK ayıracıdır ('17,6456' -> '17.6456');
            # dizi sabiti içinde ({1,2}) ise virgül ayırıcıdır, aynen kalır.
            if brace_depth == 0 and prev.isdigit() and nxt.isdigit():
                chars.append(".")
            else:
                chars.append(",")
        else:
            chars.append(ch)
    return "".join(chars)


def to_universal_formula(example_formula: str, own_names: dict[str, str] | None = None) -> str:
    """Türkçe Excel formülünü dosya biçiminin beklediği evrensel (kanonik)
    gramerine çevirir.

        =TOPLA(A1:A5)                      ->  =SUM(A1:A5)
        =EĞER(A1>10;"küçük";"büyük")     ->  =IF(A1>10,"küçük","büyük")
        =YUVARLA(17,6456;2)                ->  =ROUND(17.6456,2)
        =ÇOKEĞER(...;DOĞRU;"FF")          ->  =IFS(...,TRUE,"FF")
        =İÇ_VERİM_ORANI({-1000;300})       ->  =IRR({-1000,300})

    Tırnak içindeki metinlere dokunmaz. `own_names`, dosyayı üreten servisin
    elindeki ek Türkçe/İngilizce eşleştirmelerdir (tohum verideki tüm
    fonksiyon adları ayrıca dahildir).
    """
    if not example_formula:
        return example_formula
    name_map = dict(_BOOLEAN_LITERAL_MAP)
    name_map.update(_TR_EN_NAME_MAP)
    if own_names:
        name_map.update({k: v for k, v in own_names.items() if k and v})

    parts: list[str] = []
    pos = 0
    for literal in _STRING_LITERAL_RE.finditer(example_formula):
        parts.append(_convert_segment(example_formula[pos : literal.start()], name_map))
        parts.append(literal.group(0))          # tırnak içi metin aynen kalır
        pos = literal.end()
    parts.append(_convert_segment(example_formula[pos:], name_map))
    return "".join(parts)


def _write_result_cell(ws: Worksheet, row: int, col: int, formula: Formula) -> None:
    """Sonuç hücresini yazar: Excel'in açabileceği geçerli bir formülse
    CANLI olarak (evrensel gramerle), değilse (yer tutucu vb.) düz metin olarak."""
    cell = ws.cell(row=row, column=col)
    universal = to_universal_formula(
        formula.example_formula, {formula.name_tr: formula.name_en}
    )
    if _is_live_formula(universal):
        cell.value = universal
    else:
        _set_text(cell, formula.example_formula)   # kullanıcının gördüğü Türkçe metin
    cell.font = _ACCENT_FONT
    cell.fill = _RESULT_FILL

    # Beklenen sonuç tarih/saat ise hücre de o biçimde gösterilsin
    # (aksi hâlde Excel saat sonucunu ham ondalık sayı olarak gösterir).
    expected = str(formula.example_result or "").strip()
    if _TIME_RESULT_RE.fullmatch(expected):
        cell.number_format = "hh:mm:ss"
    elif _DATE_RESULT_RE.fullmatch(expected):
        cell.number_format = "dd.mm.yyyy"


# ---------------------------------------------------------------------------\
# Örnek workbook için hücre referansı yardımcıları
# ---------------------------------------------------------------------------\
def _extract_cell_refs(example_formula: str) -> List[Tuple[int, int, int, int]]:
    """Örnek formüldeki hücre referanslarını (min_sütun, min_satır, max_sütun,
    max_satır) olarak çıkarır. Tırnak içindeki metin sabitleri ("büyük" gibi)
    çıkarılır; yalnızca A1 / A1:A5 gibi gerçek referanslar alınır.
    """
    if not example_formula:
        return []
    cleaned = re.sub(r'"[^"]*"', " ", example_formula)   # metin sabitleri
    cleaned = re.sub(r"'[^']*'", " ", cleaned)            # sayfa adları: 'Sayfa 1'!A1
    refs: List[Tuple[int, int, int, int]] = []
    for match in _CELL_REF_RE.finditer(cleaned.upper()):
        col1 = column_index_from_string(match.group(1))
        row1 = int(match.group(2))
        if match.group(3):
            col2 = column_index_from_string(match.group(3))
            row2 = int(match.group(4))
        else:
            col2, row2 = col1, row1
        if col1 > _MAX_EXCEL_COL or col2 > _MAX_EXCEL_COL:
            continue
        if row1 > _MAX_EXCEL_ROW or row2 > _MAX_EXCEL_ROW:
            continue
        refs.append((min(col1, col2), min(row1, row2), max(col1, col2), max(row1, row2)))
    return refs


def _format_range(ref: Tuple[int, int, int, int]) -> str:
    """(1, 1, 1, 5) -> 'A1:A5'; tek hücrede 'A1'."""
    col1, row1, col2, row2 = ref
    start = f"{get_column_letter(col1)}{row1}"
    end = f"{get_column_letter(col2)}{row2}"
    return start if start == end else f"{start}:{end}"


def _fill_sample_data(ws: Worksheet, refs: Sequence[Tuple[int, int, int, int]]) -> Tuple[int, int, int, int]:
    """Referans verilen tüm hücrelere örnek sayısal veri yazar ve veri bloğunun
    sınırlarını (min_sütun, min_satır, max_sütun, max_satır) döner.

    B sütunu özel durum: ilk hücresi A1 ile aynıdır (arama anahtarları
    DÜŞEYARA/YATAYARA için eşleşme sağlar), diğer hücreleri +60 eklenir;
    böylece koşullu toplama örnekleri (ör. \">50\" kriteri) en az bir eşleşme
    bulur ve #BÖLME0! gibi hata üretmez.
    """
    min_col = min(r[0] for r in refs)
    min_row = min(r[1] for r in refs)
    max_col = max(r[2] for r in refs)
    max_row = max(r[3] for r in refs)

    for col1, row1, col2, row2 in refs:
        index = 0
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                value = _SAMPLE_NUMBERS[index % len(_SAMPLE_NUMBERS)]
                if col == 2 and index > 0:      # B sütunu: bkz. docstring
                    value += 60
                ws.cell(row=row, column=col, value=value)
                index += 1
    return min_col, min_row, max_col, max_row


def _write_info_block(ws: Worksheet, label_col: int, formula: Formula, note: str) -> int:
    """Formül bilgilerini veri bloğunun SAĞINDA bilgi bloğu olarak yazar
    (başlık, söz dizimi, kategori, zorluk, açıklamalar, beklenen sonuç, not).
    Kullanılan son satır numarasını döner."""
    value_col = label_col + 1
    last_col = label_col + 3

    title_cell = ws.cell(row=1, column=label_col, value=f"{formula.name_tr}  ({formula.name_en})")
    title_cell.font = _TITLE_FONT
    ws.merge_cells(start_row=1, start_column=label_col, end_row=1, end_column=last_col)
    title_cell.alignment = Alignment(vertical="center")

    def kv(row: int, label: str, value, *, wrap: bool = False, height: int | None = None,
           fill: PatternFill | None = None, font: Font | None = None) -> None:
        label_cell = ws.cell(row=row, column=label_col, value=label)
        label_cell.font = _LABEL_FONT
        label_cell.alignment = Alignment(vertical="top")
        value_cell = ws.cell(row=row, column=value_col)
        _set_text(value_cell, value)
        ws.merge_cells(start_row=row, start_column=value_col, end_row=row, end_column=last_col)
        value_cell.alignment = Alignment(wrap_text=wrap, vertical="top")
        if fill is not None:
            value_cell.fill = fill
        if font is not None:
            value_cell.font = font
        if height is not None:
            ws.row_dimensions[row].height = height

    kv(3, "Söz Dizimi:", formula.syntax_tr, wrap=True, height=30)
    kv(4, "Kategori:", formula.category.name_tr if formula.category else "—")
    kv(5, "Zorluk:", formula.difficulty_label)
    kv(7, "Açıklama:", formula.short_description_tr, wrap=True, height=32)
    kv(9, "Detaylı Açıklama:", formula.detailed_explanation_tr or "—", wrap=True, height=72)
    kv(11, "Beklenen Sonuç:", formula.example_result or "—", fill=_RESULT_FILL, font=_RESULT_FONT)
    kv(13, "Örnek Açıklama:", formula.example_description_tr or "—", wrap=True, height=44)
    kv(15, "Not:", note, wrap=True, height=34)
    return 15


def _export_row(formula: Formula) -> List[object]:
    """Toplu aktarım satırının 13 değerini üretir (başlıklarla sıralı)."""
    tags = formula.tags or []
    if not isinstance(tags, (list, tuple)):
        tags = [tags]
    return [
        formula.name_tr,
        formula.name_en,
        formula.syntax_tr,
        formula.short_description_tr,
        formula.example_formula,
        formula.difficulty_label,
        formula.detailed_explanation_tr or "",
        formula.example_description_tr or "",
        formula.example_result or "",
        formula.exercise_question_tr or "",
        formula.exercise_answer or "",
        formula.exercise_hint_tr or "",
        ", ".join(str(tag) for tag in tags),
    ]


class ExcelService:
    def __init__(self, export_dir: Path):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------\
    def build_example_workbook(self, formula: Formula) -> Path:
        """Formülün gerçek Excel'de nasıl çalıştığını gösteren, canlı formül
        içeren bir örnek dosya oluşturur ve dosya yolunu döner.

        Örnek veriler formülün referans ettiği hücrelere yazılır; bilgi
        metinleri veri bloğunun sağına yerleşir (çakışma olmaz), böylece
        formül Excel'de açılır açılmaz doğru sonucu üretir.
        """
        wb = Workbook()
        ws = wb.active
        ws.title = _safe_sheet_name(formula.name_tr)

        refs = _extract_cell_refs(formula.example_formula or "")

        if refs:
            min_col, _min_row, max_col, max_row = _fill_sample_data(ws, refs)
            for col in range(min_col, max_col + 2):       # +2: "Sonuç" formülü sütunu
                ws.column_dimensions[get_column_letter(col)].width = 13
            meta_col = max_col + 2
            result_row = max_row + 2

            ws.cell(row=result_row, column=min_col, value="Sonuç →").font = Font(bold=True)
            _write_result_cell(ws, result_row, min_col + 1, formula)

            ranges_text = ", ".join(_format_range(ref) for ref in refs)
            note = (
                f"Örnek veriler {ranges_text} aralığına yazıldı. Hücreleri "
                "değiştirdiğinizde formülün sonucu otomatik olarak güncellenir."
            )
        else:
            meta_col = 1
            result_row = 0
            note = (
                "Bu örnek sabit değerlerle çalışır; formülü bir hücreye "
                "kopyalayıp kendi verinizle deneyebilirsiniz."
            )

        last_info_row = _write_info_block(ws, meta_col, formula, note)

        if not refs:
            result_row = last_info_row + 2
            ws.cell(row=result_row, column=1, value="Formül →").font = Font(bold=True)
            _write_result_cell(ws, result_row, 2, formula)
            ws.column_dimensions[get_column_letter(2)].width = 34

        ws.column_dimensions[get_column_letter(meta_col)].width = 22
        for offset in (1, 2, 3):
            ws.column_dimensions[get_column_letter(meta_col + offset)].width = 20

        filename = f"{safe_filename(formula.name_tr)}_ornek.xlsx"
        path = self.export_dir / filename
        wb.save(path)
        app_logger.info(f"Örnek Excel dosyası oluşturuldu: {path}")
        return path

    # ------------------------------------------------------------------\
    def export_all_formulas(self, formulas: List[Formula]) -> Path:
        """Tüm formülleri kategoriye göre gruplandırıp tek bir referans
        çalışma kitabına aktarır (her kategori ayrı bir sekmede; başlık
        kilidi, otomatik filtre ve zengin sütunlarla)."""
        wb = Workbook()
        wb.remove(wb.active)

        by_category: dict[str, list[Formula]] = {}
        for formula in formulas:
            category_name = formula.category.name_tr if formula.category else "Diğer"
            by_category.setdefault(category_name, []).append(formula)

        if not by_category:
            # En az bir sayfa olmadan kaydedilen workbook Excel tarafından
            # açılamaz; bu yüzden bilgi sayfası oluştur.
            ws = wb.create_sheet(title="Formüller")
            ws["A1"] = "Dışa aktarılacak formül bulunamadı."
            ws["A1"].font = Font(bold=True, size=12, color="107C41")
            ws.column_dimensions["A"].width = 44
        else:
            for category_name in sorted(by_category.keys()):
                items = sorted(by_category[category_name], key=lambda f: f.name_tr)
                ws = wb.create_sheet(title=_safe_sheet_name(category_name))

                for col_idx, header in enumerate(_EXPORT_HEADERS, start=1):
                    cell = ws.cell(row=1, column=col_idx, value=header)
                    cell.font = _HEADER_FONT
                    cell.fill = _HEADER_FILL
                    cell.alignment = Alignment(
                        horizontal="center", vertical="center", wrap_text=True
                    )

                for row_idx, formula in enumerate(items, start=2):
                    for col_idx, value in enumerate(_export_row(formula), start=1):
                        cell = ws.cell(row=row_idx, column=col_idx)
                        # Söz Dizimi / Örnek / Cevap sütunları `=` ile başlar;
                        # bunlar metin olarak saklanmalı (bkz. _set_text). Excel'de
                        # canlı hesaplanan referans satırı, kitabın kendisi değil,
                        # yalnızca "Örnek Workbook" dosyasıdır.
                        _set_text(cell, value)
                        cell.alignment = Alignment(wrap_text=True, vertical="top")

                for col_idx, width in enumerate(_EXPORT_WIDTHS, start=1):
                    ws.column_dimensions[get_column_letter(col_idx)].width = width

                last_row = len(items) + 1
                ws.auto_filter.ref = f"A1:{get_column_letter(len(_EXPORT_HEADERS))}{last_row}"
                ws.freeze_panes = "A2"

        filename = f"excel_formulleri_referans_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        path = self.export_dir / filename
        wb.save(path)
        app_logger.info(f"{len(formulas)} formül Excel'e aktarıldı: {path}")
        return path


def create_excel_service() -> ExcelService:
    """DI container için fabrika fonksiyonu."""
    return ExcelService(export_dir=settings.paths.excel_exports_dir)
